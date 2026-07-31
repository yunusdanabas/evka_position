"""ipt_panel.py — inline Quick IPT controls for the main evka_gui panel."""

from __future__ import annotations

import csv
from typing import Optional

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from tools.ipt.capture import IptCapture
from tools.ipt.solver import COND_BLOCK, COND_WARN, MIN_POINTS, solve_ipt
from tools.position_checker.parser import parse_line

from .session_utils import default_export_path

_STATUS_COLOR = {
    "ok": "#00ff88",
    "warn": "#ffd700",
    "reject": "#ff4444",
    "block": "#ff4444",
}


def _btn_style(fg: str) -> str:
    return (
        f"QPushButton {{ color: {fg}; border: 1px solid {fg}; padding: 4px 8px;"
        f" background: transparent; border-radius: 3px; }}"
        f"QPushButton:hover {{ background: {fg}22; }}"
        f"QPushButton:disabled {{ color: #555; border-color: #444; background: transparent; }}"
    )


def feed_protocol_line(capture: IptCapture, line: str) -> None:
    """Feed one raw protocol line into an IPT capture buffer (GUI-thread only)."""
    capture.ingest_line(line)
    stripped = line.strip()
    if stripped.startswith("DATA,"):
        frame = parse_line(stripped)
        if frame is not None:
            capture.ingest_frame(frame)


def ipt_projections(pts: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Map 3D points to XY/XZ/YZ plot coordinates."""
    if len(pts) == 0:
        return {k: (np.array([]), np.array([])) for k in ("xy", "xz", "yz")}
    return {
        "xy": (pts[:, 0], pts[:, 1]),
        "xz": (pts[:, 0], pts[:, 2]),
        "yz": (pts[:, 1], pts[:, 2]),
    }


def ipt_marker_coords(p: np.ndarray) -> dict[str, tuple[float, float]]:
    return {"xy": (p[0], p[1]), "xz": (p[0], p[2]), "yz": (p[1], p[2])}


def ipt_sphere_circle(cx: float, cy: float, r: float) -> tuple[np.ndarray, np.ndarray]:
    angles = np.linspace(0, 2 * np.pi, 80)
    return cx + r * np.cos(angles), cy + r * np.sin(angles)


class IptPanel(QtWidgets.QGroupBox):
    """Quick IPT capture controls and solver results (sensor frame, mm)."""

    state_changed = QtCore.pyqtSignal()
    add_p_to_snapshots = QtCore.pyqtSignal(float, float, float)

    def __init__(self, parent=None) -> None:
        super().__init__("Quick IPT", parent)
        self._capture = IptCapture()
        self._last_solution: Optional[dict] = None
        self._solution_usable = False
        self._connected = False
        self._build_ui()

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._refresh_count)
        self._timer.start(40)

    @property
    def capture(self) -> IptCapture:
        return self._capture

    @property
    def last_solution(self) -> Optional[dict]:
        return self._last_solution

    def is_armed(self) -> bool:
        return self._capture.is_armed()

    def has_solution(self) -> bool:
        return self._last_solution is not None and self._last_solution.get("ok")

    def show_overlay(self) -> bool:
        return self.is_armed() or self.has_solution()

    def points(self) -> np.ndarray:
        return self._capture.points()

    def count(self) -> int:
        return self._capture.count()

    def feed_line(self, line: str) -> None:
        feed_protocol_line(self._capture, line)

    def set_connected(self, connected: bool) -> None:
        self._connected = connected
        for btn in (self.btn_arm, self.btn_stop, self.btn_solve, self.btn_clear):
            btn.setEnabled(connected)
        for btn in (self.btn_copy_p, self.btn_add_snap):
            btn.setEnabled(connected and self._solution_usable)
        self.btn_export_csv.setEnabled(connected and self.has_solution())
        if connected:
            self._set_status("Place tip on target, then ARM.", "#00ff88")
        else:
            self._capture.disarm()
            self._solution_usable = False
            for btn in (self.btn_arm, self.btn_stop, self.btn_solve, self.btn_clear):
                btn.setEnabled(False)
            for btn in (self.btn_copy_p, self.btn_export_csv, self.btn_add_snap):
                btn.setEnabled(False)
            self._set_status("Disconnected.", "#ff4444")
            self.state_changed.emit()

    def _build_ui(self) -> None:
        lay = QtWidgets.QGridLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setHorizontalSpacing(4)
        lay.setVerticalSpacing(3)
        lay.addWidget(QtWidgets.QLabel("L (mm):"), 0, 0)
        self.txt_L = QtWidgets.QLineEdit()
        self.txt_L.setPlaceholderText("blank = auto")
        lay.addWidget(self.txt_L, 0, 1, 1, 3)
        self.btn_arm = QtWidgets.QPushButton("ARM")
        self.btn_stop = QtWidgets.QPushButton("STOP")
        self.btn_solve = QtWidgets.QPushButton("SOLVE")
        self.btn_clear = QtWidgets.QPushButton("CLEAR")
        self.btn_arm.setStyleSheet(_btn_style("#00ff88"))
        self.btn_stop.setStyleSheet(_btn_style("#ff4444"))
        self.btn_solve.setStyleSheet(_btn_style("#4488ff"))
        self.btn_clear.setStyleSheet(_btn_style("#8899aa"))
        for col, btn in enumerate((self.btn_arm, self.btn_stop, self.btn_solve, self.btn_clear)):
            btn.setEnabled(False)
            lay.addWidget(btn, 1, col)
        self.lbl_pts = QtWidgets.QLabel("Pts: 0")
        self.lbl_p = QtWidgets.QLabel("P: —")
        self.lbl_l = QtWidgets.QLabel("L: —")
        self.lbl_rms = QtWidgets.QLabel("RMS: —")
        self.lbl_cond = QtWidgets.QLabel("Cond: —")
        self.lbl_p.setFont(QtGui.QFont("Consolas", 10, QtGui.QFont.Bold))
        for lbl in (self.lbl_pts, self.lbl_l, self.lbl_rms, self.lbl_cond):
            lbl.setFont(QtGui.QFont("Consolas", 9))
        lay.addWidget(self.lbl_pts, 2, 0)
        lay.addWidget(self.lbl_p, 2, 1, 1, 3)
        lay.addWidget(self.lbl_l, 3, 0, 1, 2)
        lay.addWidget(self.lbl_rms, 3, 2)
        lay.addWidget(self.lbl_cond, 3, 3)
        self.lbl_status = QtWidgets.QLabel("Disconnected.")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("font-weight: bold; color: #ff4444; font-size: 9px;")
        lay.addWidget(self.lbl_status, 4, 0, 1, 4)

        export_row = QtWidgets.QHBoxLayout()
        export_row.setSpacing(4)
        self.btn_copy_p = QtWidgets.QPushButton("Copy P")
        self.btn_export_csv = QtWidgets.QPushButton("Export CSV")
        self.btn_add_snap = QtWidgets.QPushButton("Add to Snapshots")
        self.btn_copy_p.setStyleSheet(_btn_style("#00ffff"))
        self.btn_export_csv.setStyleSheet(_btn_style("#ffd700"))
        self.btn_add_snap.setStyleSheet(_btn_style("#00ff88"))
        for btn in (self.btn_copy_p, self.btn_export_csv, self.btn_add_snap):
            btn.setEnabled(False)
            export_row.addWidget(btn)
        lay.addLayout(export_row, 5, 0, 1, 4)

        self.btn_arm.clicked.connect(self._arm)
        self.btn_stop.clicked.connect(self._stop)
        self.btn_solve.clicked.connect(self._solve)
        self.btn_clear.clicked.connect(self._clear)
        self.btn_copy_p.clicked.connect(self._copy_p)
        self.btn_export_csv.clicked.connect(self._export_capture)
        self.btn_add_snap.clicked.connect(self._add_p_snapshot)

    def _set_status(self, text: str, color: str) -> None:
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 10px;")

    def _arm(self) -> None:
        self._capture.clear()
        self._capture.arm()
        self._last_solution = None
        self._solution_usable = False
        for btn in (self.btn_copy_p, self.btn_export_csv, self.btn_add_snap):
            btn.setEnabled(False)
        self._set_status("CAPTURING — sweep handle in a wide spiral.", "#ffd700")
        self.state_changed.emit()

    def _stop(self) -> None:
        self._capture.disarm()
        self._set_status(
            f"Stopped. {self._capture.count()} points. Press SOLVE.",
            "#00ff88",
        )
        self.state_changed.emit()

    def _clear(self) -> None:
        self._capture.clear()
        self._last_solution = None
        self._solution_usable = False
        for btn in (self.btn_copy_p, self.btn_export_csv, self.btn_add_snap):
            btn.setEnabled(False)
        self.lbl_p.setText("P: —")
        self.lbl_l.setText("L_hat: —")
        self.lbl_rms.setText("RMS: —")
        self.lbl_cond.setText("Cond: —")
        self._set_status("Cleared.", "#00ff88")
        self.state_changed.emit()

    def _solve(self) -> None:
        m = self._capture.points()
        l_txt = self.txt_L.text().strip()
        try:
            l_val = float(l_txt) if l_txt else None
        except ValueError:
            self._set_status("L must be a number (or blank).", "#ff4444")
            return
        if l_val is not None and l_val <= 0:
            self._set_status("L must be positive.", "#ff4444")
            return
        out = solve_ipt(m, L=l_val)
        self._last_solution = out
        if not out["ok"]:
            self._solution_usable = False
            for btn in (self.btn_copy_p, self.btn_export_csv, self.btn_add_snap):
                btn.setEnabled(False)
            self._set_status(out["error"], "#ff4444")
            self.state_changed.emit()
            return
        p = out["P"]
        self.lbl_p.setText("P: %.2f, %.2f, %.2f" % (p[0], p[1], p[2]))
        if l_val is not None:
            self.lbl_l.setText("L: %.1f mm (fit %.1f)" % (out["L_hat"], out["L_fit"]))
        else:
            self.lbl_l.setText("L_hat: %.1f mm" % out["L_hat"])
        self.lbl_rms.setText("RMS: %.3f [%s]" % (out["rms_resid"], out["slip_warning"]))
        self.lbl_cond.setText("Cond: %.0f [%s]" % (out["cond"], out["geom_warning"]))
        worst = (
            "reject"
            if out["slip_warning"] == "reject" or out["geom_warning"] == "block"
            else ("warn" if "warn" in (out["slip_warning"], out["geom_warning"]) else "ok")
        )
        msgs = {
            "ok": "Good fit.",
            "warn": "Marginal — sweep wider / re-measure.",
            "reject": "Rejected — tip slipped or sweep too small.",
        }
        self._set_status(msgs[worst], _STATUS_COLOR[worst])
        self._solution_usable = worst != "reject"
        for btn in (self.btn_copy_p, self.btn_add_snap):
            btn.setEnabled(self._solution_usable)
        self.btn_export_csv.setEnabled(True)
        self.state_changed.emit()

    def _copy_p(self) -> None:
        if not self._solution_usable:
            return
        p = self._last_solution["P"]
        QtWidgets.QApplication.clipboard().setText(
            f"{p[0]:.3f},{p[1]:.3f},{p[2]:.3f}"
        )
        self._set_status("P copied to clipboard.", "#00ff88")

    def _export_capture(self) -> None:
        pts = self._capture.points()
        if len(pts) == 0:
            self._set_status("No capture points to export.", "#ff4444")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export IPT capture", default_export_path("ipt_capture.csv"), "CSV (*.csv)"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["x_mm", "y_mm", "z_mm"])
            for row in pts:
                w.writerow([f"{row[0]:.3f}", f"{row[1]:.3f}", f"{row[2]:.3f}"])
        self._set_status(f"Exported {len(pts)} capture points.", "#00ff88")

    def _add_p_snapshot(self) -> None:
        if not self._solution_usable:
            return
        p = self._last_solution["P"]
        self.add_p_to_snapshots.emit(float(p[0]), float(p[1]), float(p[2]))
        self._set_status("P added to snapshots.", "#00ff88")

    def _refresh_count(self) -> None:
        n = self._capture.count()
        self.lbl_pts.setText(
            "Pts: %d%s"
            % (n, "" if n >= MIN_POINTS else f" /{MIN_POINTS}")
        )
        if self.is_armed() and n < MIN_POINTS:
            self._set_status(
                f"Capturing — need ≥{MIN_POINTS} points; sweep handle in a wide spiral.",
                "#ffd700",
            )
        elif self.is_armed() and n >= MIN_POINTS:
            self._set_status(
                "Good point count — keep sweeping or press STOP then SOLVE.",
                "#00ff88",
            )
        if self.has_solution() and self._last_solution:
            cond = self._last_solution.get("cond", 0)
            if cond >= COND_BLOCK:
                hint = "Geometry poor — repeat with a wider sweep."
            elif cond >= COND_WARN:
                hint = "Marginal geometry — consider a wider sweep."
            else:
                hint = None
            if hint and not self.is_armed():
                self._set_status(hint, "#ffd700")
