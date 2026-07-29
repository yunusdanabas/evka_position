"""calibration.py — non-modal calibration window for evka_gui."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from PyQt5 import QtWidgets

from tools.calibration import report

from .model import CalRotary, CalWire, command_response_matches


SendFn = Callable[[str], bool]

ROLE_CALIBRATION = "calibration"
ROLE_VALIDATION = "validation"
ROLE_LABELS = {ROLE_CALIBRATION: "Calibration", ROLE_VALIDATION: "Validation"}

# Where a passing fit gets deployed for position_checker/GUI to consume.
DEPLOY_JSON = report.PROJECT_ROOT / "tools" / "calibration" / "calibration.json"


@dataclass
class WireTrial:
    actual_mm: float
    factor: float
    ppr: float


@dataclass
class EndpointPair:
    world_x: float
    world_y: float
    world_z: float
    sensor_x: float
    sensor_y: float
    sensor_z: float
    label: str = ""
    notes: str = ""
    role: str = ROLE_CALIBRATION


@dataclass
class CalibrationState:
    wire_trials: List[WireTrial] = field(default_factory=list)
    last_theta: Optional[CalRotary] = None
    last_phi: Optional[CalRotary] = None
    endpoint_pairs: List[EndpointPair] = field(default_factory=list)
    constants_line: str = ""


class CalibrationWindow(QtWidgets.QMainWindow):
    """Secondary window for encoder PPR and endpoint calibration."""

    def __init__(self, send_fn: SendFn, parent=None, session_dir: Optional[Path] = None):
        super().__init__(parent)
        self._send = send_fn
        self._state = CalibrationState()
        self._device_buttons: List[QtWidgets.QPushButton] = []
        self._ppr_pending: Optional[Tuple[str, bool, str]] = None
        self._wire_pending: Optional[Tuple[str, float]] = None
        self._last_sensor = (0.0, 0.0, 0.0)
        self._has_sensor = False
        self._session_dir = Path(session_dir) if session_dir else report.DEFAULT_SESSION_DIR
        self._report: Optional[report.GeneratedReport] = None
        self._report_json_bytes: Optional[bytes] = None
        self.setWindowTitle("EVKA Calibration")
        self.resize(820, 640)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        self._tabs = QtWidgets.QTabWidget()
        self._tabs.addTab(self._build_wire_tab(), "Wire")
        self._tabs.addTab(self._build_theta_tab(), "Theta")
        self._tabs.addTab(self._build_phi_tab(), "Phi")
        self._tabs.addTab(self._build_endpoint_tab(), "Endpoint")
        layout.addWidget(self._tabs)

        self._status = QtWidgets.QLabel("Send CONSTANTS on open to refresh firmware values.")
        self._status.setStyleSheet("color:#888;")
        layout.addWidget(self._status)

        self._constants_lbl = QtWidgets.QLabel("CONSTANTS: —")
        self._constants_lbl.setWordWrap(True)
        layout.addWidget(self._constants_lbl)

        self._load_session()
        self.set_connected(False, refresh=False)

    def set_connected(self, connected: bool, *, refresh: bool = True) -> None:
        """Refresh firmware constants when a device is live.

        The endpoint report flow works offline, so CONSTANTS is only sent when there is
        something to answer it — otherwise opening the window pops a 'connect first' warning.
        """
        for button in self._device_buttons:
            button.setEnabled(connected)
        if not connected:
            self._ppr_pending = None
            self._wire_pending = None
            self._has_sensor = False
            self._last_sensor = (0.0, 0.0, 0.0)
            for label in (self._live_x, self._live_y, self._live_z):
                label.setText("—")
        elif refresh:
            self._send_device("CONSTANTS")

    def _send_device(self, command: str) -> bool:
        if self._send(command) is False:
            self._status.setText(f"Send failed: {command}")
            return False
        return True

    def _start_ppr_apply(self, command: str, save: bool, label: str) -> None:
        if self._ppr_pending is not None:
            self._status.setText("Wait for the current PPR command reply.")
            return
        self._ppr_pending = (command, save, label)
        if not self._send_device(command):
            self._ppr_pending = None
            return
        self._status.setText(f"Waiting for {command.split()[0]} reply…")

    def handle_reply(self, line: str, replied_command: Optional[str] = None) -> None:
        if (line.startswith("ERR:") and self._wire_pending is not None
                and replied_command == self._wire_pending[0]):
            self._wire_pending = None
            self._status.setText(f"Wire calibration failed: {line}")
            return
        pending = self._ppr_pending
        if pending is None:
            return
        command, save, label = pending
        if line.startswith("ERR:"):
            if replied_command != command:
                return
            self._ppr_pending = None
            self._status.setText(f"{label} failed: {line}")
            return
        if not command_response_matches(command, line):
            return
        if save and command != "SAVE_PPR":
            self._ppr_pending = ("SAVE_PPR", False, label)
            if not self._send_device("SAVE_PPR"):
                self._ppr_pending = None
                return
            self._status.setText(f"{label} applied; waiting for SAVE_PPR reply…")
            return
        self._ppr_pending = None
        self._status.setText(f"{'Saved' if command == 'SAVE_PPR' else 'Applied'} {label}")

    def handle_timeout(self, command: str) -> None:
        if self._wire_pending is not None and self._wire_pending[0] == command:
            self._wire_pending = None
        if self._ppr_pending is not None and self._ppr_pending[0] == command:
            self._ppr_pending = None
        self._status.setText(f"No response to {command} (timeout)")

    def handle_cal(self, cal, replied_command: Optional[str] = None) -> None:
        if isinstance(cal, CalWire):
            if self._wire_pending is None or replied_command != self._wire_pending[0]:
                return
            _, actual_mm = self._wire_pending
            self._wire_pending = None
            trial = WireTrial(actual_mm, cal.factor, cal.ppr_wire)
            self._state.wire_trials.append(trial)
            self._wire_result.setText(
                f"Trial: factor={cal.factor:.4f}, PPR={cal.ppr_wire:.1f}"
            )
            self._refresh_wire_table()
        elif isinstance(cal, CalRotary):
            expected = "CAL_T " if cal.axis == "theta" else "CAL_P "
            if replied_command is None or not replied_command.startswith(expected):
                return
            if cal.axis == "theta":
                self._state.last_theta = cal
                self._theta_result.setText(f"Counts={cal.counts}, PPR={cal.ppr:.1f}")
            else:
                self._state.last_phi = cal
                self._phi_result.setText(f"Counts={cal.counts}, PPR={cal.ppr:.1f}")

    def handle_constants(self, line: str) -> None:
        self._state.constants_line = line
        self._constants_lbl.setText(f"CONSTANTS: {line}")

    def handle_position(self, x: float, y: float, z: float) -> None:
        self._last_sensor = (x, y, z)
        self._has_sensor = True
        self._live_x.setText(f"{x:.2f}")
        self._live_y.setText(f"{y:.2f}")
        self._live_z.setText(f"{z:.2f}")

    # ------------------------------------------------------------------ wire
    def _build_wire_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        live = QtWidgets.QHBoxLayout()
        self._live_x = QtWidgets.QLabel("X —")
        self._live_y = QtWidgets.QLabel("Y —")
        self._live_z = QtWidgets.QLabel("Z —")
        for lbl in (self._live_x, self._live_y, self._live_z):
            live.addWidget(lbl)
        lay.addLayout(live)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Pull distance (mm):"))
        self._wire_dist = QtWidgets.QLineEdit()
        self._wire_dist.setPlaceholderText("e.g. 500")
        row.addWidget(self._wire_dist)
        btn_zero_w = QtWidgets.QPushButton("ZERO WIRE")
        btn_zero_w.clicked.connect(lambda: self._send_device("ZERO_W"))
        btn_record = QtWidgets.QPushButton("RECORD")
        btn_record.clicked.connect(self._record_wire)
        row.addWidget(btn_zero_w)
        row.addWidget(btn_record)
        lay.addLayout(row)

        self._wire_result = QtWidgets.QLabel("—")
        lay.addWidget(self._wire_result)

        self._wire_table = QtWidgets.QTableWidget(0, 4)
        self._wire_table.setHorizontalHeaderLabels(["#", "Actual mm", "Factor", "PPR"])
        self._wire_table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self._wire_table)

        stats = QtWidgets.QHBoxLayout()
        self._wire_mean = QtWidgets.QLabel("Mean PPR: —")
        self._wire_spread = QtWidgets.QLabel("Spread: —")
        stats.addWidget(self._wire_mean)
        stats.addWidget(self._wire_spread)
        lay.addLayout(stats)

        btns = QtWidgets.QHBoxLayout()
        btn_apply = QtWidgets.QPushButton("APPLY (RAM)")
        btn_apply.clicked.connect(lambda: self._apply_wire(False))
        btn_save = QtWidgets.QPushButton("APPLY + SAVE (NVS)")
        btn_save.clicked.connect(lambda: self._apply_wire(True))
        btn_clear = QtWidgets.QPushButton("Clear trials")
        btn_clear.clicked.connect(self._clear_wire)
        btns.addWidget(btn_apply)
        btns.addWidget(btn_save)
        btns.addWidget(btn_clear)
        self._device_buttons += [btn_zero_w, btn_record, btn_apply, btn_save]
        lay.addLayout(btns)
        return w

    def _record_wire(self) -> None:
        if self._wire_pending is not None:
            self._status.setText("Wait for the current CAL_W reply.")
            return
        try:
            mm = float(self._wire_dist.text())
        except ValueError:
            self._status.setText("Enter a valid distance in mm.")
            return
        if mm <= 0:
            self._status.setText("Distance must be > 0.")
            return
        command = f"CAL_W {mm}".upper()
        self._wire_pending = (command, mm)
        if not self._send_device(command):
            self._wire_pending = None

    def _refresh_wire_table(self) -> None:
        trials = self._state.wire_trials
        self._wire_table.setRowCount(len(trials))
        for i, t in enumerate(trials):
            self._wire_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(i + 1)))
            self._wire_table.setItem(i, 1, QtWidgets.QTableWidgetItem(f"{t.actual_mm:.1f}"))
            self._wire_table.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{t.factor:.4f}"))
            self._wire_table.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{t.ppr:.1f}"))
        if trials:
            pprs = [t.ppr for t in trials]
            mean = statistics.mean(pprs)
            self._wire_mean.setText(f"Mean PPR: {mean:.1f}")
            if len(pprs) > 1:
                spread = (max(pprs) - min(pprs)) / mean * 100
                self._wire_spread.setText(f"Spread: {spread:.2f}%")
            else:
                self._wire_spread.setText("Spread: —")

    def _apply_wire(self, save: bool) -> None:
        if not self._state.wire_trials:
            return
        mean = statistics.mean(t.ppr for t in self._state.wire_trials)
        self._start_ppr_apply(
            f"SET_PPR_WIRE {mean:.2f}", save, f"PPR_WIRE={mean:.2f}",
        )

    def _clear_wire(self) -> None:
        self._state.wire_trials.clear()
        self._wire_table.setRowCount(0)
        self._wire_mean.setText("Mean PPR: —")
        self._wire_spread.setText("Spread: —")
        self._wire_result.setText("—")

    # --------------------------------------------------------------- theta/phi
    def _build_rotary_tab(self, axis: str) -> tuple:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        lay.addWidget(QtWidgets.QLabel(
            f"Rotate {axis} encoder N full turns, then compute PPR."
        ))
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Turns:"))
        turns = QtWidgets.QSpinBox()
        turns.setRange(1, 20)
        turns.setValue(5)
        row.addWidget(turns)
        zero_btn = QtWidgets.QPushButton(f"ZERO_{axis[0].upper()}")
        zero_btn.clicked.connect(lambda: self._send_device(f"ZERO_{axis[0].upper()}"))
        row.addWidget(zero_btn)
        btn = QtWidgets.QPushButton(f"CAL_{axis[0].upper()}")
        result = QtWidgets.QLabel("—")
        btn.clicked.connect(
            lambda: self._send_device(f"CAL_{axis[0].upper()} {turns.value()}")
        )
        row.addWidget(btn)
        lay.addLayout(row)
        lay.addWidget(result)
        apply_row = QtWidgets.QHBoxLayout()
        btn_apply = QtWidgets.QPushButton("APPLY (RAM)")
        btn_save = QtWidgets.QPushButton("APPLY + SAVE (NVS)")
        apply_row.addWidget(btn_apply)
        apply_row.addWidget(btn_save)
        lay.addLayout(apply_row)

        def apply_ppr(save: bool) -> None:
            cal = self._state.last_theta if axis == "theta" else self._state.last_phi
            if cal is None:
                self._status.setText(f"Run CAL_{axis[0].upper()} first.")
                return
            self._start_ppr_apply(
                f"SET_PPR_ROTARY {cal.ppr:.2f}", save, f"PPR for {axis}",
            )

        btn_apply.clicked.connect(lambda: apply_ppr(False))
        btn_save.clicked.connect(lambda: apply_ppr(True))
        self._device_buttons += [zero_btn, btn, btn_apply, btn_save]
        return w, result

    def _build_theta_tab(self) -> QtWidgets.QWidget:
        w, self._theta_result = self._build_rotary_tab("theta")
        return w

    def _build_phi_tab(self) -> QtWidgets.QWidget:
        w, self._phi_result = self._build_rotary_tab("phi")
        return w

    # ------------------------------------------------------------- endpoint
    def _build_endpoint_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        lay.addWidget(QtWidgets.QLabel(
            "Collect world/sensor pairs, assign each to the calibration or validation set, "
            "then generate the report. Points are stored in the session folder."
        ))

        form = QtWidgets.QGridLayout()
        self._ep_label = QtWidgets.QLineEdit()
        self._ep_wx = QtWidgets.QLineEdit()
        self._ep_wy = QtWidgets.QLineEdit()
        self._ep_wz = QtWidgets.QLineEdit()
        self._ep_sx = QtWidgets.QLineEdit()
        self._ep_sy = QtWidgets.QLineEdit()
        self._ep_sz = QtWidgets.QLineEdit()
        self._ep_notes = QtWidgets.QLineEdit()
        coords = [
            ("World X", self._ep_wx), ("World Y", self._ep_wy), ("World Z", self._ep_wz),
            ("Sensor X", self._ep_sx), ("Sensor Y", self._ep_sy), ("Sensor Z", self._ep_sz),
        ]
        for i, (name, widget) in enumerate(coords):
            form.addWidget(QtWidgets.QLabel(name), i // 3, (i % 3) * 2)
            form.addWidget(widget, i // 3, (i % 3) * 2 + 1)
        form.addWidget(QtWidgets.QLabel("Label"), 2, 0)
        form.addWidget(self._ep_label, 2, 1)
        form.addWidget(QtWidgets.QLabel("Notes"), 2, 2)
        form.addWidget(self._ep_notes, 2, 3)
        form.addWidget(QtWidgets.QLabel("Add to"), 2, 4)
        self._ep_role = QtWidgets.QComboBox()
        for role in (ROLE_CALIBRATION, ROLE_VALIDATION):
            self._ep_role.addItem(ROLE_LABELS[role], role)
        form.addWidget(self._ep_role, 2, 5)
        lay.addLayout(form)

        btn_row = QtWidgets.QHBoxLayout()
        btn_sensor = QtWidgets.QPushButton("Use Current Sensor XYZ")
        btn_sensor.clicked.connect(self._use_current_sensor)
        btn_add = QtWidgets.QPushButton("Add pair")
        btn_add.clicked.connect(self._add_endpoint)
        btn_import = QtWidgets.QPushButton("Import CSV")
        btn_import.clicked.connect(self._import_endpoint)
        self._btn_delete = QtWidgets.QPushButton("Delete selected")
        self._btn_delete.clicked.connect(self._delete_selected)
        btn_clear = QtWidgets.QPushButton("Clear")
        btn_clear.clicked.connect(self._clear_endpoint)
        for b in (btn_sensor, btn_add, btn_import, self._btn_delete, btn_clear):
            btn_row.addWidget(b)
        self._device_buttons.append(btn_sensor)
        lay.addLayout(btn_row)

        self._ep_table = QtWidgets.QTableWidget(0, 9)
        self._ep_table.setHorizontalHeaderLabels([
            "Label", "World X", "World Y", "World Z",
            "Sensor X", "Sensor Y", "Sensor Z", "Set", "Notes",
        ])
        self._ep_table.horizontalHeader().setStretchLastSection(True)
        self._ep_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._ep_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        lay.addWidget(self._ep_table)

        run_row = QtWidgets.QHBoxLayout()
        btn_report = QtWidgets.QPushButton("Generate report")
        btn_report.clicked.connect(self._generate_report)
        self._btn_deploy = QtWidgets.QPushButton("Deploy calibration.json")
        self._btn_deploy.clicked.connect(self._deploy_calibration)
        self._btn_deploy.setEnabled(False)
        self._verdict = QtWidgets.QLabel("No report yet.")
        run_row.addWidget(btn_report)
        run_row.addWidget(self._btn_deploy)
        run_row.addWidget(self._verdict, 1)
        lay.addLayout(run_row)

        self._results = QtWidgets.QTextEdit()
        self._results.setReadOnly(True)
        self._results.setFontFamily("monospace")
        lay.addWidget(self._results)
        return w

    # --------------------------------------------------------- session files
    def _load_session(self) -> None:
        """Populate the table from the session CSVs — they are the source of truth."""
        try:
            report.ensure_templates(self._session_dir)
            pairs: List[EndpointPair] = []
            for role, name in (
                (ROLE_CALIBRATION, report.CALIBRATION_CSV),
                (ROLE_VALIDATION, report.VALIDATION_CSV),
            ):
                for p in report.load_point_pairs(self._session_dir / name):
                    pairs.append(EndpointPair(
                        float(p.world[0]), float(p.world[1]), float(p.world[2]),
                        float(p.sensor[0]), float(p.sensor[1]), float(p.sensor[2]),
                        p.label, p.notes, role,
                    ))
        except (OSError, ValueError) as exc:
            self._status.setText(f"Could not load session: {exc}")
            return
        self._state.endpoint_pairs = pairs
        self._refresh_endpoint_table()
        if pairs:
            self._status.setText(f"Loaded {len(pairs)} points from {self._session_dir}.")

    def _save_session(self) -> bool:
        """Rewrite both CSVs from current state.

        Whole-file rewrite keeps add/delete/role-change on one code path — no dirty tracking.
        """
        points = {
            role: [
                report.PointPair(
                    p.label,
                    (p.world_x, p.world_y, p.world_z),
                    (p.sensor_x, p.sensor_y, p.sensor_z),
                    p.notes,
                )
                for p in self._state.endpoint_pairs if p.role == role
            ]
            for role in (ROLE_CALIBRATION, ROLE_VALIDATION)
        }
        try:
            report.save_session_sets(
                self._session_dir,
                points[ROLE_CALIBRATION],
                points[ROLE_VALIDATION],
            )
        except OSError as exc:
            message = f"Could not save session: {exc}"
            self._load_session()
            self._status.setText(message)
            return False
        return True

    def _refresh_endpoint_table(self) -> None:
        self._ep_table.setRowCount(len(self._state.endpoint_pairs))
        for row, p in enumerate(self._state.endpoint_pairs):
            values = [
                p.label,
                f"{p.world_x:.2f}", f"{p.world_y:.2f}", f"{p.world_z:.2f}",
                f"{p.sensor_x:.2f}", f"{p.sensor_y:.2f}", f"{p.sensor_z:.2f}",
            ]
            for col, text in enumerate(values):
                self._ep_table.setItem(row, col, QtWidgets.QTableWidgetItem(text))
            combo = QtWidgets.QComboBox()
            for role in (ROLE_CALIBRATION, ROLE_VALIDATION):
                combo.addItem(ROLE_LABELS[role], role)
            combo.setCurrentIndex(0 if p.role == ROLE_CALIBRATION else 1)
            combo.currentIndexChanged.connect(
                lambda _idx, r=row, c=combo: self._change_role(r, c.currentData())
            )
            self._ep_table.setCellWidget(row, 7, combo)
            self._ep_table.setItem(row, 8, QtWidgets.QTableWidgetItem(p.notes))

    def _change_role(self, row: int, role: str) -> None:
        if not 0 <= row < len(self._state.endpoint_pairs):
            return
        if self._state.endpoint_pairs[row].role == role:
            return
        self._state.endpoint_pairs[row].role = role
        if not self._save_session():
            return
        self._invalidate_report(f"Moved point to {ROLE_LABELS[role]} set — regenerate the report.")

    # ---------------------------------------------------------- point entry
    def _use_current_sensor(self) -> None:
        if not self._has_sensor:
            self._status.setText("No live position yet.")
            return
        x, y, z = self._last_sensor
        self._ep_sx.setText(f"{x:.3f}")
        self._ep_sy.setText(f"{y:.3f}")
        self._ep_sz.setText(f"{z:.3f}")

    def _add_endpoint(self) -> None:
        try:
            pair = EndpointPair(
                float(self._ep_wx.text()), float(self._ep_wy.text()), float(self._ep_wz.text()),
                float(self._ep_sx.text()), float(self._ep_sy.text()), float(self._ep_sz.text()),
                self._ep_label.text().strip(),
                self._ep_notes.text().strip(),
                self._ep_role.currentData(),
            )
        except ValueError:
            self._status.setText("All six coordinates must be numeric.")
            return
        if not pair.label:
            pair.label = f"P{len(self._state.endpoint_pairs) + 1}"
        self._state.endpoint_pairs.append(pair)
        if not self._save_session():
            return
        self._refresh_endpoint_table()
        self._invalidate_report(
            f"Added {pair.label} to {ROLE_LABELS[pair.role]} set "
            f"({len(self._state.endpoint_pairs)} points)."
        )

    def _delete_selected(self) -> None:
        rows = sorted({i.row() for i in self._ep_table.selectedIndexes()}, reverse=True)
        if not rows:
            self._status.setText("Select a row to delete.")
            return
        for row in rows:
            del self._state.endpoint_pairs[row]
        if not self._save_session():
            return
        self._refresh_endpoint_table()
        self._invalidate_report(f"Deleted {len(rows)} point(s).")

    def _import_endpoint(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import endpoint pairs", "", "CSV (*.csv);;All (*)"
        )
        if not path:
            return
        role = self._ep_role.currentData()
        try:
            # Shares the report parser: BOM-tolerant, and it reports bad rows by line number
            # instead of skipping them silently.
            loaded = report.load_point_pairs(Path(path))
        except (OSError, ValueError) as exc:
            self._status.setText(f"Import failed: {exc}")
            return
        if not loaded:
            self._status.setText("No rows in CSV.")
            return
        for p in loaded:
            self._state.endpoint_pairs.append(EndpointPair(
                float(p.world[0]), float(p.world[1]), float(p.world[2]),
                float(p.sensor[0]), float(p.sensor[1]), float(p.sensor[2]),
                p.label, p.notes, role,
            ))
        if not self._save_session():
            return
        self._refresh_endpoint_table()
        self._invalidate_report(f"Imported {len(loaded)} points into {ROLE_LABELS[role]} set.")

    def _clear_endpoint(self) -> None:
        self._state.endpoint_pairs.clear()
        if not self._save_session():
            return
        self._refresh_endpoint_table()
        self._invalidate_report("Cleared all points.")

    # --------------------------------------------------------------- report
    def _invalidate_report(self, message: str) -> None:
        """Any point change makes the last verdict stale — never leave deploy armed."""
        self._report = None
        self._report_json_bytes = None
        self._btn_deploy.setEnabled(False)
        self._verdict.setText("No report yet.")
        self._verdict.setStyleSheet("")
        self._status.setText(message)

    def _generate_report(self) -> None:
        self._invalidate_report("Generating report…")
        try:
            generated = report.generate_report(self._session_dir)
        except ValueError as exc:
            self._status.setText(str(exc))
            self._results.setPlainText(str(exc))
            return
        except OSError as exc:
            self._status.setText(f"Report failed: {exc}")
            return
        if generated is None:
            self._status.setText("Add at least 3 calibration points and 1 validation point.")
            return

        try:
            report_json_bytes = generated.calibration_json.read_bytes()
        except OSError as exc:
            self._status.setText(f"Report failed: {exc}")
            return
        self._report = generated
        self._report_json_bytes = report_json_bytes
        passed = generated.passed
        self._verdict.setText("PASS" if passed else "FAIL")
        self._verdict.setStyleSheet(
            "color:#2e7d32; font-weight:bold;" if passed else "color:#c62828; font-weight:bold;"
        )
        self._btn_deploy.setEnabled(passed)
        self._results.setPlainText(self._format_results(generated))
        self._status.setText(f"Report written to {generated.report_md}.")

    def _format_results(self, generated: report.GeneratedReport) -> str:
        cal, val = generated.calibration_stats, generated.validation_stats
        lines = [
            f"Calibration  n={cal.n}  RMSE {cal.rmse_mm:.2f} mm  max {cal.max_mm:.2f} mm "
            f"({cal.max_label})  limit RMSE <= {report.CALIBRATION_RMSE_LIMIT_MM:.1f} mm  "
            f"[{'PASS' if report.calibration_passed(cal) else 'FAIL'}]",
            f"Validation   n={val.n}  RMSE {val.rmse_mm:.2f} mm  max {val.max_mm:.2f} mm "
            f"({val.max_label})  limit max <= {report.VALIDATION_MAX_LIMIT_MM:.1f} mm  "
            f"[{'PASS' if report.validation_passed(val) else 'FAIL'}]",
        ]
        for title, errors in (
            ("Calibration points", generated.calibration_errors),
            ("Validation points", generated.validation_errors),
        ):
            lines += ["", title, f"{'label':<12}{'error mm':>10}{'dx':>9}{'dy':>9}{'dz':>9}"]
            for e in errors:
                lines.append(
                    f"{e.label:<12}{e.error_mm:>10.2f}"
                    f"{e.delta[0]:>9.2f}{e.delta[1]:>9.2f}{e.delta[2]:>9.2f}"
                )
        return "\n".join(lines)

    def _deploy_calibration(self) -> None:
        if self._report is None or not self._report.passed:
            self._status.setText("Deploy requires a passing report.")
            return
        reply = QtWidgets.QMessageBox.question(
            self, "Deploy calibration.json",
            f"Overwrite {DEPLOY_JSON} with this passing fit?\n\n"
            f"Calibration RMSE {self._report.calibration_stats.rmse_mm:.2f} mm, "
            f"validation max {self._report.validation_stats.max_mm:.2f} mm.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return
        try:
            if (self._report_json_bytes is None
                    or self._report.calibration_json.read_bytes() != self._report_json_bytes):
                self._invalidate_report("Session calibration.json changed; regenerate the report.")
                return
            DEPLOY_JSON.parent.mkdir(parents=True, exist_ok=True)
            DEPLOY_JSON.write_bytes(self._report_json_bytes)
        except OSError as exc:
            self._status.setText(f"Deploy failed: {exc}")
            return
        self._status.setText(f"Deployed to {DEPLOY_JSON}.")
