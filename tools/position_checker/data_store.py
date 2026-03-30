"""data_store.py — thread-safe ring buffer for parsed frames."""

import csv
from collections import deque
from threading import Lock
from typing import Dict, Optional, TextIO, Tuple

import numpy as np
import serial  # type: ignore

from .parser import ParsedFrame
from .transform import apply_transform, cartesian_to_spherical


class DataStore:
    """Stores up to *maxpoints* most recent ParsedFrame objects.

    Thread-safe: the serial reader thread appends, the GUI thread reads.
    """

    def __init__(
        self,
        maxpoints: int = 500,
        ser: Optional[serial.Serial] = None,
        csv_log_path: Optional[str] = None,
    ):
        self._buf: deque = deque(maxlen=maxpoints)
        self._lock = Lock()
        self._ser = ser
        self._connected = False
        self._connection_info = "Not connected"
        self._last_error = ""
        self._last_info = ""
        self._last_command_status = ""
        self._csv_file: Optional[TextIO] = None
        self._csv_writer: Optional[csv.writer] = None

        self._transform: Optional[Tuple[np.ndarray, np.ndarray]] = None

        if csv_log_path:
            self._csv_file = open(csv_log_path, "a", newline="", encoding="utf-8")
            self._csv_writer = csv.writer(self._csv_file)
            if self._csv_file.tell() == 0:
                self._csv_writer.writerow([
                    "x_mm", "y_mm", "z_mm", "r_mm", "theta_deg", "phi_deg",
                    "is_valid", "frame_count", "ts_ms",
                ])
                self._csv_file.flush()

    # ------------------------------------------------------------------
    # Calibration transform
    # ------------------------------------------------------------------

    def set_transform(self, R: np.ndarray, t: np.ndarray) -> None:
        """Set the sensor→world rigid body transform (applied in push())."""
        with self._lock:
            self._transform = (R, t)

    # ------------------------------------------------------------------
    # Called from serial reader thread
    # ------------------------------------------------------------------

    def push(self, frame: ParsedFrame) -> None:
        with self._lock:
            if self._transform is not None:
                R, t = self._transform
                wx, wy, wz = apply_transform(frame.x_mm, frame.y_mm, frame.z_mm, R, t)
                wr, wtheta, wphi = cartesian_to_spherical(wx, wy, wz)
                frame = frame._replace(
                    x_mm=wx, y_mm=wy, z_mm=wz,
                    r_mm=wr, theta_deg=wtheta, phi_deg=wphi,
                )
            self._buf.append(frame)
            if self._csv_writer is not None:
                self._csv_writer.writerow(list(frame))
                self._csv_file.flush()

    def set_serial(self, ser: Optional[serial.Serial]) -> None:
        with self._lock:
            self._ser = ser

    def set_connection(self, connected: bool, info: str) -> None:
        with self._lock:
            self._connected = connected
            self._connection_info = info

    def set_error(self, error: str) -> None:
        with self._lock:
            self._last_error = error

    def set_info(self, info: str) -> None:
        with self._lock:
            self._last_info = info

    def set_command_status(self, status: str) -> None:
        with self._lock:
            self._last_command_status = status

    # ------------------------------------------------------------------
    # Called from GUI thread
    # ------------------------------------------------------------------

    def snapshot(self) -> list:
        """Return a shallow copy of all stored frames (list of ParsedFrame)."""
        with self._lock:
            return list(self._buf)

    def latest(self) -> Optional[ParsedFrame]:
        """Return the most recent frame, or None if the buffer is empty."""
        with self._lock:
            return self._buf[-1] if self._buf else None

    def get_runtime_status(self) -> Dict[str, object]:
        """Return connection and command/status metadata for UI rendering."""
        with self._lock:
            return {
                "connected": self._connected,
                "connection_info": self._connection_info,
                "last_error": self._last_error,
                "last_info": self._last_info,
                "last_command_status": self._last_command_status,
            }

    def clear(self) -> None:
        """Clear all stored frames from the buffer."""
        with self._lock:
            self._buf.clear()

    def send_zero(self) -> bool:
        """Write 'ZERO\\n' to the serial port; returns True on success."""
        with self._lock:
            ser = self._ser

        if ser is None or not ser.is_open:
            self.set_command_status("ZERO failed: serial not connected")
            return False
        try:
            ser.write(b"ZERO\n")
            self.set_command_status("ZERO sent")
            return True
        except serial.SerialException as exc:
            self.set_command_status(f"ZERO failed: {exc}")
            return False

    def send_ping(self) -> bool:
        """Write 'PING\\n' to serial; returns True on success."""
        with self._lock:
            ser = self._ser

        if ser is None or not ser.is_open:
            self.set_command_status("PING failed: serial not connected")
            return False
        try:
            ser.write(b"PING\n")
            self.set_command_status("PING sent")
            return True
        except serial.SerialException as exc:
            self.set_command_status(f"PING failed: {exc}")
            return False

    def close(self) -> None:
        """Release optional file handles used by the logger."""
        with self._lock:
            if self._csv_file is not None:
                self._csv_file.close()
                self._csv_file = None
                self._csv_writer = None
