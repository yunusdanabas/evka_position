"""test_calibration_report.py — Endpoint tab session I/O, report verdict, gated deploy."""

import csv
import json
import sys

import pytest
from PyQt5 import QtWidgets

from tools.calibration.report import CALIBRATION_CSV, POINT_FIELDS, VALIDATION_CSV
from tools.evka_gui import calibration as cal_mod
from tools.evka_gui.model import CalRotary, CalWire
from tools.evka_gui.calibration import (
    ROLE_CALIBRATION,
    ROLE_VALIDATION,
    CalibrationWindow,
    WireTrial,
)


@pytest.fixture(scope="module")
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    return app


@pytest.fixture
def window(qapp, tmp_path):
    w = CalibrationWindow(lambda cmd: None, session_dir=tmp_path)
    yield w
    w.close()


def _add(window, label, world, sensor, role):
    window._ep_label.setText(label)
    for widget, value in zip(
        (window._ep_wx, window._ep_wy, window._ep_wz), world
    ):
        widget.setText(str(value))
    for widget, value in zip(
        (window._ep_sx, window._ep_sy, window._ep_sz), sensor
    ):
        widget.setText(str(value))
    window._ep_role.setCurrentIndex(0 if role == ROLE_CALIBRATION else 1)
    window._add_endpoint()


def _read_rows(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _identity_session(window):
    """4 calibration + 1 validation point, sensor frame == world frame."""
    for label, xyz in [
        ("P0", (0, 0, 0)), ("PX", (100, 0, 0)), ("PY", (0, 100, 0)), ("PZ", (0, 0, 100)),
    ]:
        _add(window, label, xyz, xyz, ROLE_CALIBRATION)
    _add(window, "V1", (10, 20, 30), (10, 20, 30), ROLE_VALIDATION)


def test_add_writes_points_to_the_right_session_csv(window, tmp_path):
    _add(window, "P0", (1, 2, 3), (4, 5, 6), ROLE_CALIBRATION)
    _add(window, "V1", (7, 8, 9), (10, 11, 12), ROLE_VALIDATION)

    cal_rows = _read_rows(tmp_path / CALIBRATION_CSV)
    val_rows = _read_rows(tmp_path / VALIDATION_CSV)
    assert [r["label"] for r in cal_rows] == ["P0"]
    assert [r["label"] for r in val_rows] == ["V1"]
    assert list(cal_rows[0]) == POINT_FIELDS
    assert float(cal_rows[0]["world_x"]) == 1.0
    assert float(cal_rows[0]["sensor_z"]) == 6.0


def test_session_round_trips_on_reopen(qapp, tmp_path):
    first = CalibrationWindow(lambda cmd: None, session_dir=tmp_path)
    _add(first, "P0", (1, 2, 3), (4, 5, 6), ROLE_CALIBRATION)
    _add(first, "V1", (7, 8, 9), (10, 11, 12), ROLE_VALIDATION)
    first.close()

    reopened = CalibrationWindow(lambda cmd: None, session_dir=tmp_path)
    try:
        pairs = reopened._state.endpoint_pairs
        assert [(p.label, p.role) for p in pairs] == [
            ("P0", ROLE_CALIBRATION),
            ("V1", ROLE_VALIDATION),
        ]
        assert reopened._ep_table.rowCount() == 2
    finally:
        reopened.close()


def test_role_change_moves_row_between_csvs(window, tmp_path):
    _add(window, "P0", (1, 2, 3), (4, 5, 6), ROLE_CALIBRATION)
    window._change_role(0, ROLE_VALIDATION)

    assert _read_rows(tmp_path / CALIBRATION_CSV) == []
    assert [r["label"] for r in _read_rows(tmp_path / VALIDATION_CSV)] == ["P0"]


def test_delete_rewrites_csv(window, tmp_path):
    _add(window, "P0", (1, 2, 3), (4, 5, 6), ROLE_CALIBRATION)
    _add(window, "P1", (7, 8, 9), (10, 11, 12), ROLE_CALIBRATION)
    window._ep_table.selectRow(0)
    window._delete_selected()

    assert [r["label"] for r in _read_rows(tmp_path / CALIBRATION_CSV)] == ["P1"]


def test_passing_report_enables_deploy_and_shows_residuals(window):
    _identity_session(window)
    window._generate_report()

    assert window._verdict.text() == "PASS"
    assert window._btn_deploy.isEnabled()
    text = window._results.toPlainText()
    assert "Calibration  n=4" in text
    assert "Validation   n=1" in text
    assert "V1" in text


def test_failing_report_leaves_deploy_disabled(window, tmp_path, monkeypatch):
    deploy = tmp_path / "deployed" / "calibration.json"
    monkeypatch.setattr(cal_mod, "DEPLOY_JSON", deploy)

    for label, xyz in [
        ("P0", (0, 0, 0)), ("PX", (100, 0, 0)), ("PY", (0, 100, 0)), ("PZ", (0, 0, 100)),
    ]:
        _add(window, label, xyz, xyz, ROLE_CALIBRATION)
    # Validation point 100 mm off — max error blows past the 15 mm limit.
    _add(window, "V1", (0, 0, 0), (100, 0, 0), ROLE_VALIDATION)
    window._generate_report()

    assert window._verdict.text() == "FAIL"
    assert not window._btn_deploy.isEnabled()

    # The gate must hold even if the slot is invoked directly.
    window._deploy_calibration()
    assert not deploy.exists()


def test_deploy_copies_session_json_after_pass(window, tmp_path, monkeypatch):
    deploy = tmp_path / "deployed" / "calibration.json"
    monkeypatch.setattr(cal_mod, "DEPLOY_JSON", deploy)
    monkeypatch.setattr(
        QtWidgets.QMessageBox, "question",
        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.Yes),
    )

    _identity_session(window)
    window._generate_report()
    window._deploy_calibration()

    assert json.loads(deploy.read_text(encoding="utf-8"))["n_points"] == 4


def test_deploy_declined_leaves_target_untouched(window, tmp_path, monkeypatch):
    deploy = tmp_path / "deployed" / "calibration.json"
    monkeypatch.setattr(cal_mod, "DEPLOY_JSON", deploy)
    monkeypatch.setattr(
        QtWidgets.QMessageBox, "question",
        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.No),
    )

    _identity_session(window)
    window._generate_report()
    window._deploy_calibration()

    assert not deploy.exists()


def test_editing_points_invalidates_a_passing_verdict(window):
    _identity_session(window)
    window._generate_report()
    assert window._btn_deploy.isEnabled()

    _add(window, "P4", (5, 5, 5), (5, 5, 5), ROLE_CALIBRATION)
    assert not window._btn_deploy.isEnabled()
    assert window._verdict.text() == "No report yet."


def test_too_few_points_reports_shortfall(window):
    _add(window, "P0", (0, 0, 0), (0, 0, 0), ROLE_CALIBRATION)
    _add(window, "V1", (10, 20, 30), (10, 20, 30), ROLE_VALIDATION)
    window._generate_report()

    assert window._verdict.text() == "No report yet."
    assert not window._btn_deploy.isEnabled()
    assert "at least 3 calibration points" in window._status.text()


def test_capture_uses_raw_sensor_frame_despite_software_zero(qapp, tmp_path):
    """A software zero must not leak into captured points.

    Kabsch absorbs a constant offset into t, so a shifted frame yields a fit that looks
    fine but is only valid while that same zero is active.
    """
    from tools.evka_gui.gui import EvkaWindow

    main = EvkaWindow()
    try:
        main._cal_window = CalibrationWindow(lambda cmd: None, session_dir=tmp_path)
        main._display.relative_zero_active = True
        main._display.offset_x = 10.0
        main._display.offset_y = 20.0
        main._display.offset_z = 30.0

        main._on_position(100.0, 200.0, 300.0)

        assert main._cal_window._last_sensor == (100.0, 200.0, 300.0)
    finally:
        if main._cal_window is not None:
            main._cal_window.close()
        main.close()


def test_constants_only_sent_when_connected(qapp, tmp_path):
    sent = []
    w = CalibrationWindow(sent.append, session_dir=tmp_path)
    try:
        assert sent == []          # offline open must not command the device
        w.set_connected(False)
        assert sent == []
        w.set_connected(True)
        assert sent == ["CONSTANTS"]
    finally:
        w.close()


def test_device_controls_disabled_offline_and_ppr_save_waits_for_matching_acks(qapp, tmp_path):
    sent = []
    w = CalibrationWindow(lambda command: sent.append(command) or True, session_dir=tmp_path)
    try:
        assert all(not button.isEnabled() for button in w._device_buttons)
        w.set_connected(True, refresh=False)
        assert all(button.isEnabled() for button in w._device_buttons)

        w._state.wire_trials = [WireTrial(500.0, 1.0, 8000.0)]
        w._apply_wire(True)
        assert sent == ["SET_PPR_WIRE 8000.00"]
        assert "Saved" not in w._status.text()

        w.handle_reply("ACK:PPR_WIRE,7999.00", "SET_PPR_WIRE 8000.00")
        assert sent == ["SET_PPR_WIRE 8000.00"]
        w.handle_reply("ACK:PPR_WIRE,8000.00", "SET_PPR_WIRE 8000.00")
        assert sent[-1] == "SAVE_PPR"
        assert "waiting" in w._status.text()
        w.handle_reply("ACK:SAVE_PPR", "SAVE_PPR")
        assert w._status.text() == "Saved PPR_WIRE=8000.00"

        w.set_connected(False, refresh=False)
        assert all(not button.isEnabled() for button in w._device_buttons)
    finally:
        w.close()


def test_ppr_apply_reports_send_failure(qapp, tmp_path):
    w = CalibrationWindow(lambda command: False, session_dir=tmp_path)
    try:
        w.set_connected(True, refresh=False)
        w._state.wire_trials = [WireTrial(500.0, 1.0, 8000.0)]
        w._apply_wire(False)
        assert w._status.text() == "Send failed: SET_PPR_WIRE 8000.00"
        assert w._ppr_pending is None
    finally:
        w.close()


def test_wire_trial_allows_one_request_and_uses_its_distance(qapp, tmp_path):
    sent = []
    w = CalibrationWindow(lambda command: sent.append(command) or True, session_dir=tmp_path)
    try:
        w.set_connected(True, refresh=False)
        w._wire_dist.setText("100")
        w._record_wire()
        w._wire_dist.setText("200")
        w._record_wire()
        assert sent == ["CAL_W 100.0"]
        assert "Wait" in w._status.text()

        cal = CalWire(1.0, 0.025, 8000.0)
        w.handle_cal(cal, "CAL_W 200.0")
        assert w._state.wire_trials == []
        w.handle_cal(cal, "CAL_W 100.0")
        assert [trial.actual_mm for trial in w._state.wire_trials] == [100.0]
        assert w._wire_pending is None

        w._wire_dist.setText("300")
        w._record_wire()
        assert w._wire_pending is not None
        w.handle_timeout("CAL_W 300.0")
        assert w._wire_pending is None

        w._wire_dist.setText("400")
        w._record_wire()
        assert w._wire_pending is not None
        w.set_connected(False, refresh=False)
        assert w._wire_pending is None
    finally:
        w.close()


def test_save_failure_reloads_embedded_session_without_overwriting_error(window, tmp_path, monkeypatch):
    _add(window, "P0", (1, 2, 3), (4, 5, 6), ROLE_CALIBRATION)
    monkeypatch.setattr(
        cal_mod.report, "save_session_sets",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )

    _add(window, "P1", (7, 8, 9), (10, 11, 12), ROLE_CALIBRATION)

    assert [pair.label for pair in window._state.endpoint_pairs] == ["P0"]
    assert [row["label"] for row in _read_rows(tmp_path / CALIBRATION_CSV)] == ["P0"]
    assert window._status.text() == "Could not save session: disk full"


def test_unsolicited_rotary_calibration_is_ignored(window):
    theta = CalRotary(20000, 20000.0, "theta")
    phi = CalRotary(20000, 20000.0, "phi")
    window.handle_cal(theta, None)
    window.handle_cal(phi, "CAL_T 1")
    assert window._state.last_theta is None
    assert window._state.last_phi is None

    window.handle_cal(theta, "CAL_T 1")
    window.handle_cal(phi, "CAL_P 1")
    assert window._state.last_theta == theta
    assert window._state.last_phi == phi


def test_replaced_session_json_cannot_be_deployed(window, tmp_path, monkeypatch):
    deploy = tmp_path / "deployed" / "calibration.json"
    monkeypatch.setattr(cal_mod, "DEPLOY_JSON", deploy)
    monkeypatch.setattr(
        QtWidgets.QMessageBox, "question",
        staticmethod(lambda *args, **kwargs: QtWidgets.QMessageBox.Yes),
    )
    _identity_session(window)
    window._generate_report()
    window._report.calibration_json.write_text("{}", encoding="utf-8")

    window._deploy_calibration()

    assert not deploy.exists()
    assert window._report is None
    assert "changed" in window._status.text()


def test_disconnect_clears_embedded_live_sensor_state(window):
    window.handle_position(10.0, 20.0, 30.0)
    assert window._has_sensor
    window.set_connected(False, refresh=False)
    assert not window._has_sensor
    assert window._last_sensor == (0.0, 0.0, 0.0)
    assert [label.text() for label in (window._live_x, window._live_y, window._live_z)] == ["—"] * 3

    window._use_current_sensor()
    assert window._ep_sx.text() == ""
    assert window._status.text() == "No live position yet."
