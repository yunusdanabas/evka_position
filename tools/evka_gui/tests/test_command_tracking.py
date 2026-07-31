import sys
import time

import pytest
from PyQt5 import QtWidgets

from tools.evka_gui.gui import EvkaWindow

# This module builds pyqtgraph plot widgets, which register in a process-global
# ViewBox registry that every later plot construction walks. Sharing one process
# across these modules segfaults intermittently, so run this one forked.
# See docs/CI_PYTEST_SEGFAULT_LOG.md.
pytestmark = pytest.mark.forked


@pytest.fixture(scope="module")
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)


class FakeTransport:
    def __init__(self):
        self.sent = []

    def send_command(self, command):
        self.sent.append(command)
        return True, "sent"

    def close(self, emit_disconnect=True, reason="Disconnected"):
        pass


def test_startup_and_prefix_replies_clear_only_their_commands(qapp):
    window = EvkaWindow()
    try:
        window._transport = FakeTransport()
        commands = ["CONSTANTS", "GET_IP", "SYSINFO", "STATUS", "RAW_COUNTS", "CAL_T 1", "PING"]
        for command in commands:
            assert window._send(command)
        assert [command for command, _ in window._pending_commands] == commands

        replies = [
            "ACK:PONG",
            "STATUS,1,42,1234,500.0,10.0,-20.0,100.0,200.0,300.0",
            "CONSTANTS,20000,8000,0.025,0.018",
            "SYSINFO,-50,120000,300,1",
            "STA_IP:192.168.1.84",
            "RAW,1,2,3",
            "CAL:THETA,20000,20000.00",
        ]
        for reply in replies:
            window._queue.put(("line", reply))
        window._drain()

        assert window._pending_commands == []
        assert window._axis_labels["x"].text() == "100.00"
        assert window._lbl_r.text() == "R 500.00"
        assert window._lbl_ts.text() == "ts: 1234 ms"
        window._check_cmd_timeout()
        assert "timeout" not in window._lbl_status.text().lower()
    finally:
        window.close()


def test_replay_keeps_calibration_device_controls_disabled(qapp, tmp_path):
    from tools.evka_gui.calibration import CalibrationWindow

    window = EvkaWindow()
    try:
        window._cal_window = CalibrationWindow(lambda command: True, session_dir=tmp_path)
        window._is_replay = True
        window._set_connected(True)
        assert all(not button.isEnabled() for button in window._cal_window._device_buttons)
    finally:
        window.close()


def test_broadcast_error_and_malformed_reply_do_not_consume_commands(qapp):
    window = EvkaWindow()
    try:
        window._transport = FakeTransport()
        window._send("STATUS")
        window._send("PING")

        window._queue.put(("line", "ERR:CAL_W zero counts"))
        window._queue.put(("line", "STATUS,malformed"))
        window._drain()
        assert [command for command, _ in window._pending_commands] == ["STATUS", "PING"]

        window._queue.put(("line", "ACK:PONG"))
        window._queue.put(("line", "STATUS,1,1,1,1,2,3,4,5,6"))
        window._drain()
        assert window._pending_commands == []
    finally:
        window.close()


def test_second_cal_w_command_is_rejected_while_first_is_pending(qapp):
    window = EvkaWindow()
    try:
        transport = FakeTransport()
        window._transport = transport
        assert window._send("CAL_W 100")
        assert not window._send("CAL_W 200")
        assert transport.sent == ["CAL_W 100"]
    finally:
        window.close()


def test_unknown_command_reply_completes_blink_compatibility_path(qapp):
    window = EvkaWindow()
    try:
        window._transport = FakeTransport()
        window._send("BLINK")
        window._queue.put(("line", "ERR:UNKNOWN_CMD"))
        window._drain()
        assert window._pending_commands == []
        assert "reflash firmware for BLINK support" in window._lbl_status.text()
    finally:
        window.close()


def test_expired_ppr_command_notifies_calibration_and_unwedges_it(qapp, tmp_path):
    from tools.evka_gui.calibration import CalibrationWindow, WireTrial

    window = EvkaWindow()
    try:
        window._transport = FakeTransport()
        window._cal_window = CalibrationWindow(window._send_for_cal, session_dir=tmp_path)
        window._cal_window.set_connected(True, refresh=False)
        window._cal_window._state.wire_trials = [WireTrial(500.0, 1.0, 8000.0)]
        window._cal_window._apply_wire(False)
        window._pending_commands = [
            (command, time.monotonic() - 10.0)
            for command, _ in window._pending_commands
        ]

        window._check_cmd_timeout()

        assert window._pending_commands == []
        assert window._cal_window._ppr_pending is None
        assert "SET_PPR_WIRE 8000.00" in window._cal_window._status.text()
        assert "timeout" in window._cal_window._status.text()
    finally:
        window.close()


def test_ipt_a_shortcut_uses_connected_button_path_and_unfreezes(qapp):
    window = EvkaWindow()
    try:
        shortcut = next(
            item for item in window.findChildren(QtWidgets.QShortcut)
            if item.key().toString() == "A"
        )
        shortcut.activated.emit()
        assert not window._ipt_panel.is_armed()

        window._set_connected(True)
        window._set_frozen(True)
        shortcut.activated.emit()
        assert window._ipt_panel.is_armed()
        assert not window._frozen
    finally:
        window.close()


def test_websocket_wifi_controls_match_before_and_after_connect(qapp):
    before = EvkaWindow()
    after = EvkaWindow()
    try:
        before.rb_ws.setChecked(True)
        before._open_wifi()
        assert not before._wifi_window.btn_save.isEnabled()
        before._transport = FakeTransport()
        before._is_ws = True
        before._set_connected(True)
        assert before._wifi_window.btn_save.isEnabled()

        after.rb_ws.setChecked(True)
        after._transport = FakeTransport()
        after._is_ws = True
        after._set_connected(True)
        after._open_wifi()
        assert after._wifi_window.btn_save.isEnabled()
    finally:
        before.close()
        after.close()
