"""test_gui.py — standalone calibration app: session I/O, verdict, gated deploy, raw frame."""

import csv
import json
import sys
import time

import pytest
from PyQt5 import QtWidgets

from tools.calibration import gui as gui_mod
from tools.calibration.gui import ROLE_CALIBRATION, ROLE_VALIDATION, CalibrationApp
from tools.calibration.report import CALIBRATION_CSV, POINT_FIELDS, VALIDATION_CSV


@pytest.fixture(scope="module")
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    return app


@pytest.fixture
def app(qapp, tmp_path):
    w = CalibrationApp(session_dir=tmp_path)
    yield w
    w.close()


def _add(app, label, world, sensor, role, notes=""):
    app._ep_label.setText(label)
    app._ep_notes.setText(notes)
    for widget, value in zip((app._ep_wx, app._ep_wy, app._ep_wz), world):
        widget.setText(str(value))
    for widget, value in zip((app._ep_sx, app._ep_sy, app._ep_sz), sensor):
        widget.setText(str(value))
    app._ep_role.setCurrentIndex(0 if role == ROLE_CALIBRATION else 1)
    app._add_endpoint()


def _read_rows(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _identity_session(app):
    """4 calibration + 1 validation point, sensor frame == world frame."""
    for label, xyz in [
        ("P0", (0, 0, 0)), ("PX", (100, 0, 0)), ("PY", (0, 100, 0)), ("PZ", (0, 0, 100)),
    ]:
        _add(app, label, xyz, xyz, ROLE_CALIBRATION)
    _add(app, "V1", (10, 20, 30), (10, 20, 30), ROLE_VALIDATION)


def _failing_session(app):
    for label, xyz in [
        ("P0", (0, 0, 0)), ("PX", (100, 0, 0)), ("PY", (0, 100, 0)), ("PZ", (0, 0, 100)),
    ]:
        _add(app, label, xyz, xyz, ROLE_CALIBRATION)
    # Validation point 100 mm off — blows past the 15 mm max limit.
    _add(app, "V1", (0, 0, 0), (100, 0, 0), ROLE_VALIDATION)


def test_add_writes_points_to_the_right_session_csv(app, tmp_path):
    _add(app, "P0", (1, 2, 3), (4, 5, 6), ROLE_CALIBRATION, notes="origin")
    _add(app, "V1", (7, 8, 9), (10, 11, 12), ROLE_VALIDATION)

    cal_rows = _read_rows(tmp_path / CALIBRATION_CSV)
    val_rows = _read_rows(tmp_path / VALIDATION_CSV)
    assert [r["label"] for r in cal_rows] == ["P0"]
    assert [r["label"] for r in val_rows] == ["V1"]
    assert list(cal_rows[0]) == POINT_FIELDS
    assert cal_rows[0]["notes"] == "origin"
    assert float(cal_rows[0]["world_x"]) == 1.0
    assert float(cal_rows[0]["sensor_z"]) == 6.0


def test_session_round_trips_on_reopen(qapp, tmp_path):
    first = CalibrationApp(session_dir=tmp_path)
    _add(first, "P0", (1, 2, 3), (4, 5, 6), ROLE_CALIBRATION)
    _add(first, "V1", (7, 8, 9), (10, 11, 12), ROLE_VALIDATION)
    first.close()

    reopened = CalibrationApp(session_dir=tmp_path)
    try:
        assert [(r, p.label) for r, p in reopened._points] == [
            (ROLE_CALIBRATION, "P0"),
            (ROLE_VALIDATION, "V1"),
        ]
        assert reopened._ep_table.rowCount() == 2
    finally:
        reopened.close()


def test_role_change_moves_row_between_csvs(app, tmp_path):
    _add(app, "P0", (1, 2, 3), (4, 5, 6), ROLE_CALIBRATION)
    app._change_role(0, ROLE_VALIDATION)

    assert _read_rows(tmp_path / CALIBRATION_CSV) == []
    assert [r["label"] for r in _read_rows(tmp_path / VALIDATION_CSV)] == ["P0"]


def test_delete_rewrites_csv(app, tmp_path):
    _add(app, "P0", (1, 2, 3), (4, 5, 6), ROLE_CALIBRATION)
    _add(app, "P1", (7, 8, 9), (10, 11, 12), ROLE_CALIBRATION)
    app._ep_table.selectRow(0)
    app._delete_selected()

    assert [r["label"] for r in _read_rows(tmp_path / CALIBRATION_CSV)] == ["P1"]


def test_passing_report_enables_deploy_and_shows_residuals(app):
    _identity_session(app)
    app._generate_report()

    assert app._verdict.text() == "PASS"
    assert app._btn_deploy.isEnabled()
    text = app._results.toPlainText()
    assert "Calibration  n=4" in text
    assert "Validation   n=1" in text
    assert "V1" in text


def test_failing_report_leaves_deploy_disabled(app, tmp_path, monkeypatch):
    deploy = tmp_path / "deployed" / "calibration.json"
    monkeypatch.setattr(gui_mod, "DEPLOY_JSON", deploy)

    _failing_session(app)
    app._generate_report()

    assert app._verdict.text() == "FAIL"
    assert not app._btn_deploy.isEnabled()

    # The gate must hold even if the slot is invoked directly.
    app._deploy_calibration()
    assert not deploy.exists()


def test_deploy_copies_session_json_after_pass(app, tmp_path, monkeypatch):
    deploy = tmp_path / "deployed" / "calibration.json"
    monkeypatch.setattr(gui_mod, "DEPLOY_JSON", deploy)
    monkeypatch.setattr(
        QtWidgets.QMessageBox, "question",
        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.Yes),
    )

    _identity_session(app)
    app._generate_report()
    app._deploy_calibration()

    assert json.loads(deploy.read_text(encoding="utf-8"))["n_points"] == 4


def test_deploy_declined_leaves_target_untouched(app, tmp_path, monkeypatch):
    deploy = tmp_path / "deployed" / "calibration.json"
    monkeypatch.setattr(gui_mod, "DEPLOY_JSON", deploy)
    monkeypatch.setattr(
        QtWidgets.QMessageBox, "question",
        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.No),
    )

    _identity_session(app)
    app._generate_report()
    app._deploy_calibration()

    assert not deploy.exists()


def test_editing_points_invalidates_a_passing_verdict(app):
    _identity_session(app)
    app._generate_report()
    assert app._btn_deploy.isEnabled()

    _add(app, "P4", (5, 5, 5), (5, 5, 5), ROLE_CALIBRATION)
    assert not app._btn_deploy.isEnabled()
    assert app._verdict.text() == "No report yet."


def test_too_few_points_reports_shortfall(app):
    _add(app, "P0", (0, 0, 0), (0, 0, 0), ROLE_CALIBRATION)
    _add(app, "V1", (10, 20, 30), (10, 20, 30), ROLE_VALIDATION)
    app._generate_report()

    assert app._verdict.text() == "No report yet."
    assert not app._btn_deploy.isEnabled()
    assert "at least 3 calibration points" in app._lbl_status.text()


def test_data_line_feeds_raw_xyz_through_the_drain(app):
    """No software-zero path exists here, so captured XYZ is the raw wire value."""
    app._queue.put(("line", "DATA,12.5,-30.25,400.75,401.5,10.0,20.0,1,812,40600"))
    app._drain()

    assert app._last_sensor == (12.5, -30.25, 400.75)
    assert app._axis_labels["x"].text() == "12.50"
    assert app._axis_labels["z"].text() == "400.75"

    app._use_current_sensor()
    assert app._ep_sx.text() == "12.500"
    assert app._ep_sy.text() == "-30.250"


def test_no_software_zero_surface(app):
    """The offset machinery must not exist — that bug class is designed out, not patched."""
    assert not hasattr(app, "_display")
    assert not hasattr(app, "btn_swzero")


def test_device_buttons_disabled_until_connected(app):
    for btn in (app.btn_blink, app.btn_hwzero, app.btn_record_wire, app.btn_save_pt):
        assert not btn.isEnabled()
    app._set_connected(True)
    for btn in (app.btn_blink, app.btn_hwzero, app.btn_record_wire, app.btn_save_pt):
        assert btn.isEnabled()
    app._set_connected(False)
    assert not app.btn_blink.isEnabled()


def test_offline_open_sends_nothing(app):
    """The endpoint report flow is offline-capable; opening must not command a device."""
    assert app._transport is None
    assert app._pending_commands == []


class _FakeTransport:
    def __init__(self, ok=True):
        self.ok = ok
        self.sent = []

    def send_command(self, command):
        self.sent.append(command)
        return self.ok, "sent" if self.ok else "send failed"

    def close(self, emit_disconnect=True, reason="Disconnected"):
        pass


def test_ppr_save_is_sequential_and_ack_driven(app):
    transport = _FakeTransport()
    app._transport = transport
    app._set_connected(True)
    app._state.wire_trials = [gui_mod.WireTrial(500.0, 1.0, 8000.0)]

    app._apply_wire(True)
    assert transport.sent == ["SET_PPR_WIRE 8000.00"]
    assert "Saved" not in app._lbl_status.text()

    app._queue.put(("line", "ACK:PPR_WIRE,8000.00"))
    app._drain()
    assert transport.sent == ["SET_PPR_WIRE 8000.00", "SAVE_PPR"]
    assert "waiting" in app._lbl_status.text()

    app._queue.put(("line", "ACK:SAVE_PPR"))
    app._drain()
    assert app._lbl_status.text() == "Saved PPR_WIRE=8000.00"


def test_ppr_send_failure_is_reported(app, monkeypatch):
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", staticmethod(lambda *args, **kwargs: None))
    app._transport = _FakeTransport(ok=False)
    app._set_connected(True)
    app._state.wire_trials = [gui_mod.WireTrial(500.0, 1.0, 8000.0)]

    app._apply_wire(False)
    assert "Send failed" in app._lbl_status.text()
    assert app._ppr_pending is None


def test_ppr_timeout_clears_pending_workflow(app):
    app._transport = _FakeTransport()
    app._set_connected(True)
    app._state.wire_trials = [gui_mod.WireTrial(500.0, 1.0, 8000.0)]
    app._apply_wire(False)
    app._pending_commands = [
        (command, time.monotonic() - 10.0)
        for command, _ in app._pending_commands
    ]

    app._check_cmd_timeout()

    assert app._ppr_pending is None
    assert app._pending_commands == []
    assert "timeout" in app._lbl_status.text()


def test_wire_trial_allows_one_request_and_keeps_its_distance(app):
    transport = _FakeTransport()
    app._transport = transport
    app._set_connected(True)
    app._wire_mm.setText("100")
    app._record_wire()
    app._wire_mm.setText("200")
    app._record_wire()
    assert transport.sent == ["CAL_W 100.0"]

    app._queue.put(("line", "CAL:WIRE,1.0,0.025,8000"))
    app._drain()
    assert [trial.actual_mm for trial in app._state.wire_trials] == [100.0]
    assert app._wire_pending is None

    app._wire_mm.setText("300")
    app._record_wire()
    app._pending_commands = [
        (command, time.monotonic() - 10.0)
        for command, _ in app._pending_commands
    ]
    app._check_cmd_timeout()
    assert app._wire_pending is None


def test_rotary_turns_must_be_integer(app):
    transport = _FakeTransport()
    app._transport = transport
    app._set_connected(True)
    turns = QtWidgets.QLineEdit("1.5")
    app._compute_rotary("T", turns)
    assert transport.sent == []
    assert "whole integer" in app._lbl_status.text()

    turns.setText("2")
    app._compute_rotary("T", turns)
    assert transport.sent == ["CAL_T 2"]


def test_save_failure_reloads_standalone_session_without_overwriting_error(app, tmp_path, monkeypatch):
    _add(app, "P0", (1, 2, 3), (4, 5, 6), ROLE_CALIBRATION)
    monkeypatch.setattr(
        gui_mod.report, "save_session_sets",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )

    _add(app, "P1", (7, 8, 9), (10, 11, 12), ROLE_CALIBRATION)

    assert [pair.label for _, pair in app._points] == ["P0"]
    assert [row["label"] for row in _read_rows(tmp_path / CALIBRATION_CSV)] == ["P0"]
    assert app._lbl_status.text() == "Could not save session: disk full"


def test_standalone_rotary_reply_requires_matching_local_command(app):
    transport = _FakeTransport()
    app._transport = transport
    app._set_connected(True)
    app._queue.put(("line", "CAL:THETA,20000,20000"))
    app._drain()
    assert app._state.last_theta is None

    turns = QtWidgets.QLineEdit("1")
    app._compute_rotary("T", turns)
    app._queue.put(("line", "CAL:THETA,20000,20000"))
    app._drain()
    assert app._state.last_theta.ppr == 20000.0


def test_standalone_replaced_session_json_cannot_be_deployed(app, tmp_path, monkeypatch):
    deploy = tmp_path / "deployed" / "calibration.json"
    monkeypatch.setattr(gui_mod, "DEPLOY_JSON", deploy)
    monkeypatch.setattr(
        QtWidgets.QMessageBox, "question",
        staticmethod(lambda *args, **kwargs: QtWidgets.QMessageBox.Yes),
    )
    _identity_session(app)
    app._generate_report()
    app._report.calibration_json.write_text("{}", encoding="utf-8")

    app._deploy_calibration()

    assert not deploy.exists()
    assert app._report is None
    assert "changed" in app._lbl_status.text()
