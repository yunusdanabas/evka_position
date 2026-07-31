"""Disconnect must stick.

The reader threads used to emit an unconditional disconnect event from their
``finally`` blocks — even on a requested stop. Harmless before auto-reconnect
existed; with it, the stray event told the window the link had *dropped* right
after the user clicked Disconnect, and the GUI reconnected against their wish.
These tests pin both the GUI behaviour and the transport root cause.
"""

import socket
import sys
import threading
import time

import pytest
from PyQt5 import QtWidgets

from tools.position_checker.tcp_client import TcpClient

# This module builds pyqtgraph plot widgets, which register in a process-global
# ViewBox registry that every later plot construction walks. Sharing one process
# across these modules segfaults intermittently, so run this one forked.
# See docs/CI_PYTEST_SEGFAULT_LOG.md.
pytestmark = pytest.mark.forked


@pytest.fixture(scope="module")
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    return app


@pytest.fixture
def window(qapp):
    from tools.evka_gui.gui import EvkaWindow
    w = EvkaWindow()
    yield w
    w.close()


class FakeTransport:
    def __init__(self):
        self.closed = False

    def close(self, emit_disconnect=True, reason="Disconnected"):
        self.closed = True

    def send_command(self, cmd):
        return True, "sent"


def test_disconnect_button_closes_and_sticks(window):
    tr = FakeTransport()
    window._transport = tr
    window._set_connected(True)
    assert window.btn_disconnect.isEnabled()

    window.btn_disconnect.click()          # the real button, not the method

    assert tr.closed, "Disconnect must close the transport"
    assert window._transport is None
    assert not window._reconnect_timer.isActive(), "user disconnect must not schedule a retry"

    # The reader thread's dying gasp: a stray disconnect event landing after the
    # user already disconnected. It must be dropped, not treated as a lost link.
    window._queue.put(("disconnect", "Connection closed"))
    window._drain()
    assert not window._reconnect_timer.isActive(), (
        "a stray disconnect event after an explicit Disconnect must not auto-reconnect"
    )
    assert window._transport is None


def test_real_link_loss_still_reconnects(window):
    tr = FakeTransport()
    window._transport = tr
    window._set_connected(True)

    window._queue.put(("disconnect", "Receive error"))   # transport still present → real drop
    window._drain()
    assert window._reconnect_timer.isActive(), "a genuine drop must schedule a retry"
    assert window.btn_disconnect.text() == "Cancel"
    window.btn_disconnect.click()                        # Cancel stops the retry
    assert not window._reconnect_timer.isActive()
    assert window.btn_disconnect.text() == "Disconnect"


def test_tcp_client_requested_stop_does_not_emit_disconnect():
    """Root cause, against a real socket: close() is a requested stop, not a lost link."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    accepted = {}

    def accept():
        conn, _ = server.accept()
        accepted["conn"] = conn

    threading.Thread(target=accept, daemon=True).start()

    events = []
    client = TcpClient()
    client.set_callbacks(on_line=lambda l: None, on_disconnect=lambda r: events.append(r))
    ok, info = client.connect("127.0.0.1", port, timeout_s=2.0, io_timeout_s=2.0)
    assert ok, info

    client.close(emit_disconnect=False)     # what the GUI does on user Disconnect
    time.sleep(0.5)                          # let the reader thread run its finally block
    assert events == [], f"requested stop must not emit disconnect, got {events}"

    server.close()
    if "conn" in accepted:
        accepted["conn"].close()


def test_tcp_client_lost_link_does_emit_disconnect():
    """The other half: a genuine drop must still be reported."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    accepted = {}

    def accept():
        conn, _ = server.accept()
        accepted["conn"] = conn

    threading.Thread(target=accept, daemon=True).start()

    events = []
    client = TcpClient()
    client.set_callbacks(on_line=lambda l: None, on_disconnect=lambda r: events.append(r))
    ok, info = client.connect("127.0.0.1", port, timeout_s=2.0, io_timeout_s=2.0)
    assert ok, info

    deadline = time.time() + 2.0
    while "conn" not in accepted and time.time() < deadline:
        time.sleep(0.02)
    accepted["conn"].close()                # the device side dies
    server.close()

    deadline = time.time() + 2.0
    while not events and time.time() < deadline:
        time.sleep(0.02)
    assert events, "a lost link must emit disconnect"
