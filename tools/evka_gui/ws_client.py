"""ws_client.py — WebSocket transport mirroring TcpClient's interface."""

from __future__ import annotations

from typing import Callable, Optional
from urllib.parse import urlparse

from PyQt5.QtCore import QUrl, QEventLoop, QTimer
from PyQt5.QtNetwork import QAbstractSocket

# Distro PyQt5 (Debian/Ubuntu python3-pyqt5) ships QtWebSockets as a separate
# package, unlike the PyPI wheel. Defer the failure to WsClient() so the serial
# and TCP transports — which need none of this — still import and work.
try:
    from PyQt5.QtWebSockets import QWebSocket
except ImportError as _exc:  # pragma: no cover - environment dependent
    QWebSocket = None
    _WS_IMPORT_ERROR = (
        "PyQt5.QtWebSockets is unavailable "
        f"({_exc}). Install PyQt5 from PyPI (pip install -e .) or the distro "
        "package python3-pyqt5.qtwebsockets. Serial and TCP transports still work."
    )
else:
    _WS_IMPORT_ERROR = None

LineCallback = Callable[[str], None]
DisconnectCallback = Callable[[str], None]

DEFAULT_WS_PATH = "/ws"
DEFAULT_WS_PORT = 80


def parse_ws_url(host_or_url: str, port: Optional[int] = None) -> QUrl:
    """Build ws:// URL from host, optional port, and path."""
    text = host_or_url.strip()
    if text.startswith("ws://") or text.startswith("wss://"):
        return QUrl(text)
    p = port if port is not None else DEFAULT_WS_PORT
    if "/" in text:
        host, _, path = text.partition("/")
        path = "/" + path.lstrip("/")
    else:
        host = text
        path = DEFAULT_WS_PATH
    return QUrl(f"ws://{host}:{p}{path}")


class WsClient:
    """QWebSocket client with the same surface as TcpClient."""

    def __init__(self) -> None:
        if QWebSocket is None:
            raise RuntimeError(_WS_IMPORT_ERROR)
        self._ws: Optional[QWebSocket] = None
        self._on_line: Optional[LineCallback] = None
        self._on_disconnect: Optional[DisconnectCallback] = None
        self._connected = False
        self._closing = False

    def set_callbacks(
        self,
        on_line: Optional[LineCallback] = None,
        on_disconnect: Optional[DisconnectCallback] = None,
    ) -> None:
        self._on_line = on_line
        self._on_disconnect = on_disconnect

    def is_connected(self) -> bool:
        return (
            self._connected
            and self._ws is not None
            and self._ws.state() == QAbstractSocket.ConnectedState
        )

    def connect(
        self,
        host: str,
        port: int = DEFAULT_WS_PORT,
        timeout_s: float = 5.0,
        io_timeout_s: float = 30.0,
    ) -> tuple[bool, str]:
        del io_timeout_s  # QWebSocket has no I/O timeout param
        self.close(emit_disconnect=False)
        url = parse_ws_url(host, port)
        ws = QWebSocket()
        self._closing = False
        ws.textMessageReceived.connect(self._on_text)
        ws.disconnected.connect(self._on_disconnected)
        ws.open(url)
        self._ws = ws
        loop = QEventLoop()
        ok = {"v": False}

        def _done(success: bool = True) -> None:
            ok["v"] = success
            loop.quit()

        ws.connected.connect(lambda: _done(True))
        QTimer.singleShot(int(timeout_s * 1000), lambda: _done(False))
        loop.exec_()
        if not ok["v"] or ws.state() != QAbstractSocket.ConnectedState:
            err = ws.errorString() or "WebSocket connect failed"
            self._closing = True
            ws.deleteLater()
            self._ws = None
            self._connected = False
            self._closing = False
            return False, err
        self._connected = True
        parsed = urlparse(url.toString())
        return True, f"connected {parsed.hostname}:{parsed.port or DEFAULT_WS_PORT}{parsed.path}"

    def send_command(self, command: str) -> tuple[bool, str]:
        if not self.is_connected() or self._ws is None:
            return False, "not connected"
        self._ws.sendTextMessage(command.strip())
        return True, "sent"

    def close(self, emit_disconnect: bool = True, reason: str = "Disconnected") -> None:
        ws = self._ws
        self._ws = None
        was = self._connected
        self._connected = False
        self._closing = True
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
            ws.deleteLater()
        self._closing = False
        if emit_disconnect and was and self._on_disconnect is not None:
            self._on_disconnect(reason)

    def _on_text(self, message: str) -> None:
        for line in message.splitlines():
            s = line.strip()
            if s and self._on_line is not None:
                self._on_line(s)

    def _on_disconnected(self) -> None:
        if self._ws is None or self._closing:
            return
        ws = self._ws
        self._ws = None
        was = self._connected
        self._connected = False
        ws.deleteLater()
        if was and self._on_disconnect is not None:
            self._on_disconnect("WebSocket closed")
