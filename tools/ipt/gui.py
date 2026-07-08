"""gui.py — pyqtgraph GUI for Quick IPT hidden-point measurement.

Live 2D projection views (XY, XZ, YZ) of the captured attachment-point cloud,
the fitted sphere outline, and the recovered hidden point. Connect over TCP
(raw CMD server, port 8080) or serial, Arm a sweep, sweep the handle in a wide
spiral, Stop, then Solve.

Uses 2D PlotWidget projections instead of GLViewWidget for portability — no
OpenGL context required, works on Wayland, X11, headless, and VMs.

Threading: transports run on daemon threads. The TCP client pushes raw lines
onto a queue.Queue; a QTimer on the GUI thread drains it and feeds the capture
buffer. The serial reader fills a DataStore; the same QTimer polls it.
(Pattern mirrors cmd_gui.py.)
"""
from __future__ import annotations

import queue
from typing import Optional

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from tools.position_checker.cmd_main import (
    CMD_AP_FALLBACK_IP,
    CMD_DEFAULT_PORT,
)
from tools.position_checker.data_store import DataStore
from tools.position_checker.serial_reader import SerialReader
from tools.position_checker.tcp_client import TcpClient

from .capture import IptCapture
from .solver import MIN_POINTS, solve_ipt

_STATUS_COLOR = {"ok": "#27ae60", "warn": "#f39c12", "reject": "#c0392b",
                 "block": "#c0392b"}

pg.setConfigOption("background", "#1a1a2e")
pg.setConfigOption("foreground", "#e0e0e0")

_CLOUD_COLOR = pg.mkPen("#00ff88", width=1, symbol="o", symbolSize=5)
_CLOUD_BRUSH = pg.mkBrush("#00ff88")
_MARKER_PEN = pg.mkPen("#ff6600", width=2, symbol="o", symbolSize=12)
_MARKER_BRUSH = pg.mkBrush("#ff6600")
_SPHERE_PEN = pg.mkPen("#2980b9", width=1.5, style=QtCore.Qt.DashLine)


class IptWindow(QtWidgets.QWidget):
    def __init__(self, tcp: Optional[tuple] = None,
                 serial: Optional[tuple] = None) -> None:
        super().__init__()
        self._capture = IptCapture()
        self._client: Optional[TcpClient] = None
        self._serial: Optional[SerialReader] = None
        self._store: Optional[DataStore] = None
        self._serial_seen = 0
        self._event_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self._last_solution: Optional[dict] = None
        self._sphere_items: dict[str, list] = {"xy": [], "xz": [], "yz": []}

        self._build_ui(tcp, serial)

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    # ------------------------------------------------------------------ UI
    def _build_ui(self, tcp, serial) -> None:
        self.setWindowTitle("EVKA Quick IPT — hidden-point measurement")
        self.resize(1040, 720)
        root = QtWidgets.QHBoxLayout(self)

        # --- 2D projection plots (XY, XZ, YZ) ---
        plots_widget = QtWidgets.QWidget()
        pl = QtWidgets.QVBoxLayout(plots_widget)
        pl.setContentsMargins(0, 0, 0, 0)

        self._plots: dict[str, pg.PlotWidget] = {}
        self._cloud_scatters: dict[str, pg.ScatterPlotItem] = {}
        self._marker_scatters: dict[str, pg.ScatterPlotItem] = {}

        titles = {"xy": "XY (top)", "xz": "XZ (front)", "yz": "YZ (side)"}
        for key, title in titles.items():
            pw = pg.PlotWidget(title=title)
            pw.setLabel("bottom", "mm")
            pw.setLabel("left", "mm")
            pw.showGrid(x=True, y=True, alpha=0.15)
            pw.setAspectLocked(True)
            self._plots[key] = pw
            pl.addWidget(pw)

            empty = np.zeros((1, 2))
            self._cloud_scatters[key] = pw.plot(
                [], [], pen=None, symbol="o", symbolSize=5,
                symbolBrush=_CLOUD_BRUSH, symbolPen=None)
            self._marker_scatters[key] = pw.plot(
                [], [], pen=None, symbol="o", symbolSize=12,
                symbolBrush=_MARKER_BRUSH, symbolPen=None)

        root.addWidget(plots_widget, stretch=3)

        # --- side panel ---
        side = QtWidgets.QVBoxLayout()
        root.addLayout(side, stretch=1)

        conn = QtWidgets.QGroupBox("Connection")
        cl = QtWidgets.QGridLayout(conn)
        self.rb_tcp = QtWidgets.QRadioButton("TCP")
        self.rb_serial = QtWidgets.QRadioButton("Serial")
        self.txt_host = QtWidgets.QLineEdit(tcp[0] if tcp else CMD_AP_FALLBACK_IP)
        self.txt_port = QtWidgets.QLineEdit(str(tcp[1] if tcp else CMD_DEFAULT_PORT))
        self.txt_serial = QtWidgets.QLineEdit(serial[0] if serial else "/dev/ttyUSB0")
        self.txt_baud = QtWidgets.QLineEdit(str(serial[1] if serial else 115200))
        self.btn_conn = QtWidgets.QPushButton("CONNECT")
        self.btn_disc = QtWidgets.QPushButton("DISCONNECT")
        self.btn_disc.setEnabled(False)
        self.rb_serial.setChecked(bool(serial and not tcp))
        self.rb_tcp.setChecked(not (serial and not tcp))
        cl.addWidget(self.rb_tcp, 0, 0); cl.addWidget(self.txt_host, 0, 1)
        cl.addWidget(self.txt_port, 0, 2)
        cl.addWidget(self.rb_serial, 1, 0); cl.addWidget(self.txt_serial, 1, 1)
        cl.addWidget(self.txt_baud, 1, 2)
        cl.addWidget(self.btn_conn, 2, 0, 1, 2); cl.addWidget(self.btn_disc, 2, 2)
        side.addWidget(conn)

        cap = QtWidgets.QGroupBox("Capture")
        capl = QtWidgets.QGridLayout(cap)
        self.btn_arm = QtWidgets.QPushButton("ARM / START SWEEP")
        self.btn_stop = QtWidgets.QPushButton("STOP")
        self.btn_solve = QtWidgets.QPushButton("SOLVE")
        self.btn_clear = QtWidgets.QPushButton("CLEAR")
        capl.addWidget(QtWidgets.QLabel("Known pen length L (mm, blank=auto):"), 0, 0, 1, 2)
        self.txt_L = QtWidgets.QLineEdit()
        capl.addWidget(self.txt_L, 1, 0, 1, 2)
        capl.addWidget(self.btn_arm, 2, 0); capl.addWidget(self.btn_stop, 2, 1)
        capl.addWidget(self.btn_solve, 3, 0); capl.addWidget(self.btn_clear, 3, 1)
        for b in (self.btn_arm, self.btn_stop, self.btn_solve, self.btn_clear):
            b.setEnabled(False)
        side.addWidget(cap)

        res = QtWidgets.QGroupBox("Result (sensor frame, mm)")
        rl = QtWidgets.QVBoxLayout(res)
        self.lbl_pts = QtWidgets.QLabel("Points: 0")
        self.lbl_p = QtWidgets.QLabel("P:  --")
        self.lbl_l = QtWidgets.QLabel("L_hat:  --")
        self.lbl_rms = QtWidgets.QLabel("RMS residual:  --")
        self.lbl_cond = QtWidgets.QLabel("Geometry cond:  --")
        self.lbl_p.setFont(QtGui.QFont("Consolas", 13, QtGui.QFont.Bold))
        for lbl in (self.lbl_pts, self.lbl_l, self.lbl_rms, self.lbl_cond):
            lbl.setFont(QtGui.QFont("Consolas", 10))
        rl.addWidget(self.lbl_pts); rl.addWidget(self.lbl_p); rl.addWidget(self.lbl_l)
        rl.addWidget(self.lbl_rms); rl.addWidget(self.lbl_cond)
        side.addWidget(res)

        self.lbl_status = QtWidgets.QLabel("Disconnected.")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("font-weight: bold; color: #c0392b;")
        side.addWidget(self.lbl_status)
        side.addStretch(1)

        self.btn_conn.clicked.connect(self._connect)
        self.btn_disc.clicked.connect(self._disconnect)
        self.btn_arm.clicked.connect(self._arm)
        self.btn_stop.clicked.connect(self._stop)
        self.btn_solve.clicked.connect(self._solve)
        self.btn_clear.clicked.connect(self._clear)

    # ------------------------------------------------------------- helpers
    def _set_status(self, text: str, color: str) -> None:
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"font-weight: bold; color: {color};")

    def _set_capture_enabled(self, on: bool) -> None:
        for b in (self.btn_arm, self.btn_stop, self.btn_solve, self.btn_clear):
            b.setEnabled(on)
        self.btn_conn.setEnabled(not on)
        self.btn_disc.setEnabled(on)

    def _clear_sphere_overlays(self) -> None:
        for key, items in self._sphere_items.items():
            for item in items:
                self._plots[key].removeItem(item)
            items.clear()

    def _add_sphere_overlay(self, key: str, cx: float, cy: float, r: float) -> None:
        """Draw a circle of radius r centred at (cx, cy) on the given projection."""
        angles = np.linspace(0, 2 * np.pi, 80)
        x = cx + r * np.cos(angles)
        y = cy + r * np.sin(angles)
        item = self._plots[key].plot(x, y, pen=_SPHERE_PEN)
        self._sphere_items[key].append(item)

    def _update_marker(self, P: np.ndarray, visible: bool) -> None:
        coords = {"xy": (P[0], P[1]), "xz": (P[0], P[2]), "yz": (P[1], P[2])}
        for key, (px, py) in coords.items():
            if visible:
                self._marker_scatters[key].setData(
                    x=[px], y=[py], symbol="o", symbolSize=12,
                    symbolBrush=_MARKER_BRUSH, symbolPen=None)
            else:
                self._marker_scatters[key].setData(x=[], y=[])

    def _update_cloud(self, pts: np.ndarray) -> None:
        if len(pts) == 0:
            for key in self._cloud_scatters:
                self._cloud_scatters[key].setData(x=[], y=[])
            return
        projections = {"xy": (pts[:, 0], pts[:, 1]),
                       "xz": (pts[:, 0], pts[:, 2]),
                       "yz": (pts[:, 1], pts[:, 2])}
        for key, (xs, ys) in projections.items():
            self._cloud_scatters[key].setData(
                x=xs, y=ys, symbol="o", symbolSize=5,
                symbolBrush=_CLOUD_BRUSH, symbolPen=None)

    # ------------------------------------------------------- connect/disc
    def _connect(self) -> None:
        if self.rb_tcp.isChecked():
            try:
                port = int(self.txt_port.text().strip())
            except ValueError:
                QtWidgets.QMessageBox.critical(self, "Error", "Port must be a number.")
                return
            self._client = TcpClient()
            self._client.set_callbacks(
                on_line=lambda ln: self._event_queue.put(("line", ln)),
                on_disconnect=lambda r: self._event_queue.put(("disconnect", r)))
            ok, info = self._client.connect(self.txt_host.text().strip(), port)
            if not ok:
                QtWidgets.QMessageBox.critical(self, "Connection Error", info)
                self._client = None
                return
        else:
            try:
                baud = int(self.txt_baud.text().strip())
            except ValueError:
                QtWidgets.QMessageBox.critical(self, "Error", "Baud must be a number.")
                return
            self._store = DataStore()
            self._serial_seen = 0
            self._serial = SerialReader(self.txt_serial.text().strip(), baud,
                                        self._store)
            self._serial.start()
        self._set_capture_enabled(True)
        self._set_status("Connected. Place the tip on the target, then ARM.", "#27ae60")

    def _disconnect(self) -> None:
        if self._client is not None:
            self._client.close(emit_disconnect=False)
            self._client = None
        if self._serial is not None:
            self._serial.stop()
            self._serial = None
            self._store = None
        self._capture.disarm()
        self._set_capture_enabled(False)
        self._set_status("Disconnected.", "#c0392b")

    # ------------------------------------------------------------- capture
    def _arm(self) -> None:
        self._capture.clear()
        self._capture.arm()
        self._clear_sphere_overlays()
        self._update_marker(np.zeros(3), visible=False)
        self._set_status("CAPTURING — sweep the handle in a wide spiral.", "#f39c12")

    def _stop(self) -> None:
        self._capture.disarm()
        self._set_status(f"Stopped. {self._capture.count()} points. Press SOLVE.",
                         "#27ae60")

    def _clear(self) -> None:
        self._capture.clear()
        self._clear_sphere_overlays()
        self._update_marker(np.zeros(3), visible=False)
        self._last_solution = None
        self._set_status("Cleared.", "#27ae60")

    def _solve(self) -> None:
        M = self._capture.points()
        L_txt = self.txt_L.text().strip()
        try:
            L = float(L_txt) if L_txt else None
        except ValueError:
            self._set_status("Known pen length L must be a number (or blank).", "#c0392b")
            return
        if L is not None and L <= 0:
            self._set_status("Known pen length L must be positive.", "#c0392b")
            return
        out = solve_ipt(M, L=L)
        self._last_solution = out
        if not out["ok"]:
            self._set_status(out["error"], "#c0392b")
            return
        P = out["P"]
        self.lbl_p.setText("P:  %.2f, %.2f, %.2f" % (P[0], P[1], P[2]))
        if L is not None:
            self.lbl_l.setText("L used:  %.2f mm  (fit: %.2f mm)" % (out["L_hat"], out["L_fit"]))
        else:
            self.lbl_l.setText("L_hat:  %.2f mm" % out["L_hat"])
        self.lbl_rms.setText("RMS residual:  %.3f mm  [%s]"
                             % (out["rms_resid"], out["slip_warning"]))
        self.lbl_cond.setText("Geometry cond:  %.0f  [%s]"
                              % (out["cond"], out["geom_warning"]))
        # draw sphere outline + marker on each projection
        self._clear_sphere_overlays()
        r = out["L_hat"]
        self._add_sphere_overlay("xy", P[0], P[1], r)
        self._add_sphere_overlay("xz", P[0], P[2], r)
        self._add_sphere_overlay("yz", P[1], P[2], r)
        self._update_marker(P, visible=True)
        worst = "reject" if out["slip_warning"] == "reject" or out["geom_warning"] == "block" \
            else ("warn" if "warn" in (out["slip_warning"], out["geom_warning"]) else "ok")
        msgs = {"ok": "Good fit.",
                "warn": "Usable, but quality is marginal — sweep wider / re-measure.",
                "reject": "Rejected — tip slipped or sweep too small. Re-measure."}
        self._set_status(msgs[worst], _STATUS_COLOR[worst])

    # --------------------------------------------------------------- tick
    def _tick(self) -> None:
        # TCP: drain queued raw lines
        while True:
            try:
                kind, payload = self._event_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "disconnect":
                self._set_status(f"Disconnected: {payload}", "#c0392b")
                self._disconnect()
                return
            self._capture.ingest_line(payload)
        # Serial: poll the DataStore for frames newer than the high-water mark.
        if self._store is not None:
            for frame in self._store.snapshot():
                if frame.frame_count < self._serial_seen:
                    self._serial_seen = 0
                if frame.frame_count > self._serial_seen:
                    self._serial_seen = frame.frame_count
                    self._capture.ingest_frame(frame)
        # refresh live cloud + count
        pts = self._capture.points()
        self.lbl_pts.setText("Points: %d%s" % (
            len(pts), "" if len(pts) >= MIN_POINTS else f"  (need {MIN_POINTS})"))
        self._update_cloud(pts)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        self._timer.stop()
        self._disconnect()
        super().closeEvent(event)


def run_ipt_gui(tcp=None, serial=None) -> int:
    app = QtWidgets.QApplication.instance()
    owns = app is None
    if owns:
        app = QtWidgets.QApplication([])
    win = IptWindow(tcp=tcp, serial=serial)
    win.show()
    return app.exec_() if owns else 0
