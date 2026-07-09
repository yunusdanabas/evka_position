"""transport.py — serial line transport mirroring TcpClient's interface.

Both transports expose ``set_callbacks`` / ``connect`` / ``send_command`` / ``close``
so the GUI drives them identically (one queue, one drain, clean join on switch).
``TcpClient`` is re-exported so the window imports both from here.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

import serial  # pyserial

from tools.position_checker.tcp_client import TcpClient  # noqa: F401  (re-exported)

LineCallback = Callable[[str], None]
DisconnectCallback = Callable[[str], None]


class SerialLineReader:
    """Threaded newline serial reader shaped exactly like ``TcpClient``.

    ponytail: no auto-reconnect — matches TcpClient; a dropped port fires
    ``on_disconnect`` and the GUI reconnects. Add a backoff-reopen loop only if
    USB re-enumeration mid-session becomes a real annoyance.
    """

    def __init__(self) -> None:
        self._ser: Optional[serial.Serial] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._running = False
        self._on_line: Optional[LineCallback] = None
        self._on_disconnect: Optional[DisconnectCallback] = None

    def set_callbacks(
        self,
        on_line: Optional[LineCallback] = None,
        on_disconnect: Optional[DisconnectCallback] = None,
    ) -> None:
        self._on_line = on_line
        self._on_disconnect = on_disconnect

    def is_connected(self) -> bool:
        with self._lock:
            return self._ser is not None and self._running

    def connect(self, port: str, baud: int = 115200, timeout_s: float = 0.2) -> tuple[bool, str]:
        self.close(emit_disconnect=False)
        try:
            ser = serial.Serial(port, baud, timeout=timeout_s)
        except Exception as exc:  # serial.SerialException, ValueError, OSError…
            return False, str(exc)

        with self._lock:
            self._ser = ser
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
        return True, "connected"

    def send_command(self, command: str) -> tuple[bool, str]:
        payload = (command.strip() + "\n").encode("ascii", errors="ignore")
        with self._lock:
            ser = self._ser
            running = self._running

        if not running or ser is None:
            return False, "not connected"

        try:
            ser.write(payload)
            return True, "sent"
        except Exception as exc:
            return False, str(exc)

    def close(self, emit_disconnect: bool = True, reason: str = "Disconnected") -> None:
        thread = None
        with self._lock:
            if not self._running and self._ser is None:
                return
            self._running = False
            thread = self._thread
            self._thread = None
            ser = self._ser
            self._ser = None

        try:
            if ser is not None:
                ser.close()
        except Exception:
            pass

        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.0)

        if emit_disconnect and self._on_disconnect is not None:
            self._on_disconnect(reason)

    def _read_loop(self) -> None:
        reason = "Connection closed"
        try:
            while True:
                with self._lock:
                    running = self._running
                    ser = self._ser
                if not running or ser is None:
                    return

                try:
                    raw = ser.readline()
                except Exception as exc:
                    reason = f"Serial error: {exc}"
                    break
                if not raw:
                    continue  # read timeout → loop re-checks running flag

                line = raw.decode("ascii", errors="ignore").strip()
                if line and self._on_line is not None:
                    self._on_line(line)
        finally:
            self.close(emit_disconnect=False)
            if self._on_disconnect is not None:
                self._on_disconnect(reason)
