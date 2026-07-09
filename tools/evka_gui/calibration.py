"""calibration.py — non-modal calibration window for evka_gui."""

from __future__ import annotations

import csv
import io
import statistics
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from PyQt5 import QtCore, QtWidgets

from .model import CalRotary, CalWire


SendFn = Callable[[str], None]


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


@dataclass
class CalibrationState:
    wire_trials: List[WireTrial] = field(default_factory=list)
    pending_wire_mm: float = 0.0
    last_theta: Optional[CalRotary] = None
    last_phi: Optional[CalRotary] = None
    endpoint_pairs: List[EndpointPair] = field(default_factory=list)
    constants_line: str = ""


class CalibrationWindow(QtWidgets.QMainWindow):
    """Secondary window for encoder PPR and endpoint calibration."""

    def __init__(self, send_fn: SendFn, parent=None):
        super().__init__(parent)
        self._send = send_fn
        self._state = CalibrationState()
        self._last_sensor = (0.0, 0.0, 0.0)
        self._has_sensor = False
        self.setWindowTitle("EVKA Calibration")
        self.resize(720, 560)

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

        QtCore.QTimer.singleShot(0, lambda: self._send("CONSTANTS"))

    def handle_cal(self, cal) -> None:
        if isinstance(cal, CalWire):
            trial = WireTrial(self._state.pending_wire_mm, cal.factor, cal.ppr_wire)
            self._state.wire_trials.append(trial)
            self._wire_result.setText(
                f"Trial: factor={cal.factor:.4f}, PPR={cal.ppr_wire:.1f}"
            )
            self._refresh_wire_table()
        elif isinstance(cal, CalRotary):
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
        btn_zero_w.clicked.connect(lambda: self._send("ZERO_W"))
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
        lay.addLayout(btns)
        return w

    def _record_wire(self) -> None:
        try:
            mm = float(self._wire_dist.text())
        except ValueError:
            self._status.setText("Enter a valid distance in mm.")
            return
        if mm <= 0:
            self._status.setText("Distance must be > 0.")
            return
        self._state.pending_wire_mm = mm
        self._send(f"CAL_W {mm}")

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
        self._send(f"SET_PPR_WIRE {mean:.2f}")
        if save:
            self._send("SAVE_PPR")
        self._status.setText(
            f"{'Saved' if save else 'Applied'} PPR_WIRE={mean:.2f}"
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
        zero_btn.clicked.connect(lambda: self._send(f"ZERO_{axis[0].upper()}"))
        row.addWidget(zero_btn)
        btn = QtWidgets.QPushButton(f"CAL_{axis[0].upper()}")
        result = QtWidgets.QLabel("—")
        btn.clicked.connect(lambda: self._send(f"CAL_{axis[0].upper()} {turns.value()}"))
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
            self._send(f"SET_PPR_ROTARY {cal.ppr:.2f}")
            if save:
                self._send("SAVE_PPR")
            self._status.setText(f"{'Saved' if save else 'Applied'} PPR for {axis}.")

        btn_apply.clicked.connect(lambda: apply_ppr(False))
        btn_save.clicked.connect(lambda: apply_ppr(True))
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
            "Record world-coordinate and sensor-coordinate point pairs for offline fit."
        ))
        form = QtWidgets.QGridLayout()
        self._ep_wx = QtWidgets.QLineEdit()
        self._ep_wy = QtWidgets.QLineEdit()
        self._ep_wz = QtWidgets.QLineEdit()
        self._ep_sx = QtWidgets.QLineEdit()
        self._ep_sy = QtWidgets.QLineEdit()
        self._ep_sz = QtWidgets.QLineEdit()
        labels = [
            ("World X", self._ep_wx), ("World Y", self._ep_wy), ("World Z", self._ep_wz),
            ("Sensor X", self._ep_sx), ("Sensor Y", self._ep_sy), ("Sensor Z", self._ep_sz),
        ]
        for i, (name, field) in enumerate(labels):
            form.addWidget(QtWidgets.QLabel(name), i // 3, (i % 3) * 2)
            form.addWidget(field, i // 3, (i % 3) * 2 + 1)
        lay.addLayout(form)

        btn_row = QtWidgets.QHBoxLayout()
        btn_sensor = QtWidgets.QPushButton("Use Current Sensor XYZ")
        btn_sensor.clicked.connect(self._use_current_sensor)
        btn_add = QtWidgets.QPushButton("Add pair")
        btn_add.clicked.connect(self._add_endpoint)
        btn_export = QtWidgets.QPushButton("Export CSV")
        btn_export.clicked.connect(self._export_endpoint)
        btn_clear = QtWidgets.QPushButton("Clear")
        btn_clear.clicked.connect(self._clear_endpoint)
        btn_row.addWidget(btn_sensor)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_export)
        btn_row.addWidget(btn_clear)
        lay.addLayout(btn_row)

        self._ep_list = QtWidgets.QListWidget()
        lay.addWidget(self._ep_list)
        return w

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
            )
        except ValueError:
            self._status.setText("All six coordinates must be numeric.")
            return
        self._state.endpoint_pairs.append(pair)
        n = len(self._state.endpoint_pairs)
        self._ep_list.addItem(
            f"#{n}: world=({pair.world_x:.1f},{pair.world_y:.1f},{pair.world_z:.1f}) "
            f"sensor=({pair.sensor_x:.1f},{pair.sensor_y:.1f},{pair.sensor_z:.1f})"
        )

    def _export_endpoint(self) -> None:
        if not self._state.endpoint_pairs:
            return
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["world_x", "world_y", "world_z", "sensor_x", "sensor_y", "sensor_z"])
        for p in self._state.endpoint_pairs:
            w.writerow([
                f"{p.world_x:.3f}", f"{p.world_y:.3f}", f"{p.world_z:.3f}",
                f"{p.sensor_x:.3f}", f"{p.sensor_y:.3f}", f"{p.sensor_z:.3f}",
            ])
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export endpoint pairs", "endpoint_pairs.csv", "CSV (*.csv)"
        )
        if path:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(buf.getvalue())
            self._status.setText(f"Exported {len(self._state.endpoint_pairs)} pairs.")

    def _clear_endpoint(self) -> None:
        self._state.endpoint_pairs.clear()
        self._ep_list.clear()
