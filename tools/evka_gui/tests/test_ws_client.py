"""Tests for WebSocket transport helpers."""

from tools.evka_gui.ws_client import parse_ws_url


def test_parse_ws_url_default_host():
    assert parse_ws_url("192.168.1.50").toString() == "ws://192.168.1.50:80/ws"


def test_parse_ws_url_host_with_path_and_port():
    assert parse_ws_url("evka.local/custom", port=81).toString() == "ws://evka.local:81/custom"


def test_parse_ws_url_preserves_explicit_url():
    assert parse_ws_url("wss://example.test/ws2").toString() == "wss://example.test/ws2"
