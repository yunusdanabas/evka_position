"""The QtWebSockets guard: missing module must not break serial/TCP imports."""

import pytest

from tools.evka_gui import ws_client


def test_ws_client_raises_clear_error_when_qtwebsockets_missing(monkeypatch):
    monkeypatch.setattr(ws_client, "QWebSocket", None)
    monkeypatch.setattr(ws_client, "_WS_IMPORT_ERROR", "QtWebSockets is unavailable (test)")

    with pytest.raises(RuntimeError, match="QtWebSockets is unavailable"):
        ws_client.WsClient()


def test_parse_ws_url_works_without_qtwebsockets(monkeypatch):
    """URL parsing only needs QtCore, so it must survive a missing QtWebSockets."""
    monkeypatch.setattr(ws_client, "QWebSocket", None)
    assert ws_client.parse_ws_url("192.168.1.50").toString() == "ws://192.168.1.50:80/ws"
