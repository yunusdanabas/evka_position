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

from .ws_client import WsClient  # noqa: F401  (re-exported)

LineCallback = Callable[[str], None]
DisconnectCallback = Callable[[str], None]

RECONNECT_MIN_S = 1.0
RECONNECT_MAX_S = 30.0


def next_backoff(
    prev_s: float,
    *,
    min_s: float = RECONNECT_MIN_S,
    max_s: float = RECONNECT_MAX_S,
) -> float:
    """Exponential reconnect backoff: 1, 2, 4, 8, 16, 30, 30, … seconds.

    ``prev_s`` is 0.0 for the first retry. Mirrors the web dashboard's
    WebSocket backoff so both UIs behave the same on a dropped link.
    """
    return min(max(prev_s * 2.0, min_s), max_s)


class SerialLineReader:
    """Threaded newline serial reader shaped exactly like ``TcpClient``.

    No reconnect logic lives here: a dropped port fires ``on_disconnect`` and
    ``EvkaWindow`` drives the retry with ``next_backoff`` above, so all three
    transports reconnect through one code path.
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
            # Only report a *lost* link. On a requested stop (close() flipped
            # _running before we got here) emitting would push a stray disconnect
            # event after the user already disconnected — which the window would
            # read as a dropped link and try to auto-reconnect.
            with self._lock:
                requested_stop = not self._running
            self.close(emit_disconnect=False)
            if not requested_stop and self._on_disconnect is not None:
                self._on_disconnect(reason)
