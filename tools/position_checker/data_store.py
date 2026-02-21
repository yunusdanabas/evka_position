"""data_store.py — thread-safe ring buffer for parsed frames."""

from collections import deque
from threading import Lock
from typing import Optional

import serial  # type: ignore

from .parser import ParsedFrame


class DataStore:
    """Stores up to *maxpoints* most recent ParsedFrame objects.

    Thread-safe: the serial reader thread appends, the GUI thread reads.
    """

    def __init__(self, maxpoints: int = 500, ser: Optional[serial.Serial] = None):
        self._buf: deque = deque(maxlen=maxpoints)
        self._lock = Lock()
        self._ser = ser

    # ------------------------------------------------------------------
    # Called from serial reader thread
    # ------------------------------------------------------------------

    def push(self, frame: ParsedFrame) -> None:
        with self._lock:
            self._buf.append(frame)

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

    def send_zero(self) -> bool:
        """Write 'ZERO\\n' to the serial port; returns True on success."""
        if self._ser is None or not self._ser.is_open:
            return False
        try:
            self._ser.write(b"ZERO\n")
            return True
        except serial.SerialException:
            return False
