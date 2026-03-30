"""tcp_client.py — newline-delimited TCP client for ESP32 CMD protocol."""

from __future__ import annotations

import socket
import threading
from typing import Callable, Optional


LineCallback = Callable[[str], None]
DisconnectCallback = Callable[[str], None]


class TcpClient:
    """Small threaded TCP client with line-based receive loop."""

    def __init__(self) -> None:
        self._sock: Optional[socket.socket] = None
        self._reader = None
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
            return self._sock is not None and self._running

    def connect(self, host: str, port: int, timeout_s: float = 5.0) -> tuple[bool, str]:
        self.close(emit_disconnect=False)
        try:
            sock = socket.create_connection((host, port), timeout=timeout_s)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            reader = sock.makefile("r", encoding="ascii", newline="\n")
        except Exception as exc:
            return False, str(exc)

        with self._lock:
            self._sock = sock
            self._reader = reader
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
        return True, "connected"

    def send_command(self, command: str) -> tuple[bool, str]:
        payload = (command.strip() + "\n").encode("ascii", errors="ignore")
        with self._lock:
            sock = self._sock
            running = self._running

        if not running or sock is None:
            return False, "not connected"

        try:
            sock.sendall(payload)
            return True, "sent"
        except Exception as exc:
            return False, str(exc)

    def close(self, emit_disconnect: bool = True, reason: str = "Disconnected") -> None:
        thread = None
        with self._lock:
            if not self._running and self._sock is None and self._reader is None:
                return
            self._running = False
            thread = self._thread
            self._thread = None
            sock = self._sock
            reader = self._reader
            self._sock = None
            self._reader = None

        try:
            if reader is not None:
                reader.close()
        except Exception:
            pass

        try:
            if sock is not None:
                sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass

        try:
            if sock is not None:
                sock.close()
        except Exception:
            pass

        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=0.2)

        if emit_disconnect and self._on_disconnect is not None:
            self._on_disconnect(reason)

    def _read_loop(self) -> None:
        reason = "Connection closed"
        try:
            while True:
                with self._lock:
                    running = self._running
                    reader = self._reader
                if not running or reader is None:
                    return

                line = reader.readline()
                if line == "":
                    reason = "Connection closed by remote host"
                    break
                line = line.strip()
                if line and self._on_line is not None:
                    self._on_line(line)
        except Exception as exc:
            reason = f"Receive error: {exc}"
        finally:
            self.close(emit_disconnect=False)
            if self._on_disconnect is not None:
                self._on_disconnect(reason)
