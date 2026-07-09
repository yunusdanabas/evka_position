"""gui.py — EvkaWindow: unified dual-transport control panel + 3D view."""

from __future__ import annotations

import csv
import math
import queue
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from PyQt5 import QtCore, QtGui, QtWidgets
from serial.tools import list_ports

from tools.position_checker.cmd_display import (
    AXIS_COLORS,
    AXIS_INVALID_COLOR,
    CmdDisplayState,
    process_sensor_line,
    process_xyz_frame,
    sta_ip_display,
    sta_ip_is_connected,
)
from tools.position_checker.cmd_main import (
    CMD_AP_FALLBACK_IP,
    CMD_DEFAULT_PORT,
    CMD_DEFAULT_STA_IP,
    DEL_POINT_PREFIX,
    POINT_PREFIX,
)
from tools.position_checker.gui import _View3D
from tools.position_checker.replay_reader import load_replay_frames

from .calibration import CalibrationWindow
from .model import SysInfo, TrailBuffer, UiState, ingest_line
from .transport import SerialLineReader, TcpClient

TRAIL_MAX = 800
HB_STALE_S = 5.0
CMD_RESPONSE_TIMEOUT_S = 2.0
SYSINFO_POLL_MS = 5000

_LED_SIZE = " border-radius:12px; min-width:24px; max-width:24px; min-height:24px; max-height:24px;"
_LED_IDLE = [
    "background:#1e1e1e; border:2px solid #1a5c38;" + _LED_SIZE,
    "background:#1e1e1e; border:2px solid #5c1a1a;" + _LED_SIZE,
]
_LED_FLASH = [
    "background:#00ff88; border:2px solid #66ffbb;" + _LED_SIZE,
    "background:#ff3333; border:2px solid #ff6666;" + _LED_SIZE,
]
_LED_LABELS = ["BTN0\nSAVE_POINT", "BTN1\nDEL_POINT"]

_COMMANDS = ["ZERO", "ZERO_T", "ZERO_P", "ZERO_W", "PING", "STATUS", "SAVE_POINT", "DEL_POINT", "SYSINFO"]


class EvkaWindow(QtWidgets.QMainWindow):
    def __init__(self, initial: Optional[dict] = None):
        super().__init__()
        self.setWindowTitle("EVKA Position — Control")
        self.resize(1500, 860)
        self.showMaximized()

        self._transport = None
        self._is_serial = False
        self._is_replay = False
        self._replay_frames: list = []
        self._replay_idx = 0
        self._queue: queue.Queue = queue.Queue()
        self._trail = TrailBuffer(TRAIL_MAX)
        self._display = CmdDisplayState()
        self._state = UiState(self._trail)
        self._settings = QtCore.QSettings("evka_position", "evka_gui")
        self._pending_cmd: Optional[str] = None
        self._pending_cmd_at: Optional[float] = None
        self._wifi_pending: Optional[str] = None
        self._has_xyz = False
        self._saved_point_rows: List[Tuple[str, float, float, float]] = []
        self._origin: Optional[Tuple[float, float, float]] = None
        self._cal_window: Optional[CalibrationWindow] = None
        self._connected_at: Optional[float] = None

        self._build_ui()
        self._load_settings()
        if initial:
            self._apply_initial(initial)

        self._drain_timer = QtCore.QTimer(self, interval=25, timeout=self._drain)
        self._view_timer = QtCore.QTimer(self, interval=50, timeout=self._refresh_views)
        self._batt_timer = QtCore.QTimer(self, interval=4000, timeout=self._poll_battery)
        self._hb_timer = QtCore.QTimer(self, interval=1000, timeout=self._check_hb_stale)
        self._cmd_timer = QtCore.QTimer(self, interval=200, timeout=self._check_cmd_timeout)
        self._sysinfo_timer = QtCore.QTimer(self, interval=SYSINFO_POLL_MS, timeout=self._poll_sysinfo)
        for t in (self._drain_timer, self._view_timer, self._batt_timer, self._hb_timer, self._cmd_timer):
            t.start()

        if initial and initial.get("autoconnect"):
            QtCore.QTimer.singleShot(0, self._connect)

    def _build_ui(self) -> None:
        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        left = QtWidgets.QScrollArea()
        left.setWidgetResizable(True)
        left.setWidget(self._build_control_panel())
        split.addWidget(left)
        split.addWidget(self._build_view_panel())
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 1)
        split.setSizes([960, 960])
        self.setCentralWidget(split)

        toolbar = self.addToolBar("Main")
        act_cal = toolbar.addAction("Calibration…")
        act_cal.triggered.connect(self._open_calibration)
        act_export = toolbar.addAction("Export Session CSV")
        act_export.triggered.connect(self._export_session)

    def _build_control_panel(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        col = QtWidgets.QVBoxLayout(w)
        col.addWidget(self._grp_connection())
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self._grp_position(), 2)
        rightcol = QtWidgets.QVBoxLayout()
        rightcol.addWidget(self._grp_battery())
        rightcol.addWidget(self._grp_remote())
        row.addLayout(rightcol, 1)
        col.addLayout(row)
        col.addWidget(self._grp_wifi())
        col.addWidget(self._grp_sysinfo())
        col.addWidget(self._grp_commands())
        col.addWidget(self._grp_points(), 1)
        self._lbl_status = QtWidgets.QLabel("Disconnected.")
        self._lbl_status.setStyleSheet("color:#c0392b; font-weight:bold;")
        self._lbl_sw_zero = QtWidgets.QLabel("")
        self._lbl_sw_zero.setStyleSheet(
            "color:#2980b9; background:#ebf5fb; padding:2px 8px; border-radius:4px;"
        )
        self._lbl_sw_zero.hide()
        col.addWidget(self._lbl_sw_zero)
        col.addWidget(self._lbl_status)
        credit = QtWidgets.QLabel("Yunus Emre Danabaş")
        credit.setStyleSheet("color:#555; font-size:9px; font-style:italic;")
        credit.setAlignment(QtCore.Qt.AlignRight)
        col.addWidget(credit)
        return w

    def _grp_connection(self) -> QtWidgets.QGroupBox:
        g = QtWidgets.QGroupBox("Connection")
        lay = QtWidgets.QGridLayout(g)
        self.rb_serial = QtWidgets.QRadioButton("Serial")
        self.rb_tcp = QtWidgets.QRadioButton("WiFi / TCP")
        self.rb_replay = QtWidgets.QRadioButton("Replay CSV")
        self.rb_serial.setChecked(True)
        self.rb_serial.toggled.connect(self._sync_conn_fields)
        self.rb_tcp.toggled.connect(self._sync_conn_fields)
        self.rb_replay.toggled.connect(self._sync_conn_fields)

        self.cmb_port = QtWidgets.QComboBox()
        self.cmb_port.setEditable(True)
        self._refresh_ports()
        btn_rescan = QtWidgets.QPushButton("↻")
        btn_rescan.setFixedWidth(30)
        btn_rescan.clicked.connect(self._refresh_ports)
        self.txt_baud = QtWidgets.QLineEdit("115200")

        self.txt_ip = QtWidgets.QLineEdit(CMD_DEFAULT_STA_IP)
        self.txt_ip.setToolTip(f"STA {CMD_DEFAULT_STA_IP} · AP {CMD_AP_FALLBACK_IP}")
        self.txt_tcp_port = QtWidgets.QLineEdit(str(CMD_DEFAULT_PORT))
        btn_ap = QtWidgets.QPushButton(f"AP ({CMD_AP_FALLBACK_IP})")
        btn_ap.clicked.connect(lambda: self.txt_ip.setText(CMD_AP_FALLBACK_IP))
        btn_sta = QtWidgets.QPushButton(f"STA ({CMD_DEFAULT_STA_IP})")
        btn_sta.clicked.connect(lambda: self.txt_ip.setText(CMD_DEFAULT_STA_IP))

        self.txt_replay = QtWidgets.QLineEdit()
        self.txt_replay.setPlaceholderText("Path to DATA, CSV replay file")
        btn_replay_browse = QtWidgets.QPushButton("…")
        btn_replay_browse.clicked.connect(self._browse_replay)

        self.btn_connect = QtWidgets.QPushButton("Connect")
        self.btn_connect.clicked.connect(self._connect)
        self.btn_disconnect = QtWidgets.QPushButton("Disconnect")
        self.btn_disconnect.clicked.connect(self._disconnect)
        self.btn_disconnect.setEnabled(False)

        self.btn_blink = QtWidgets.QPushButton("Blink LED")
        self.btn_blink.setToolTip("Send BLINK — status LED flashes if link is alive")
        self.btn_blink.clicked.connect(lambda: self._send("BLINK"))
        self.btn_blink.setEnabled(False)

        lay.addWidget(self.rb_serial, 0, 0)
        lay.addWidget(QtWidgets.QLabel("Port"), 0, 1)
        lay.addWidget(self.cmb_port, 0, 2)
        lay.addWidget(btn_rescan, 0, 3)
        lay.addWidget(QtWidgets.QLabel("Baud"), 0, 4)
        lay.addWidget(self.txt_baud, 0, 5)
        lay.addWidget(self.rb_tcp, 1, 0)
        lay.addWidget(QtWidgets.QLabel("IP"), 1, 1)
        lay.addWidget(self.txt_ip, 1, 2)
        lay.addWidget(btn_ap, 1, 3)
        lay.addWidget(btn_sta, 1, 4)
        lay.addWidget(QtWidgets.QLabel("Port"), 1, 5)
        lay.addWidget(self.txt_tcp_port, 1, 6)
        lay.addWidget(self.rb_replay, 2, 0)
        lay.addWidget(self.txt_replay, 2, 1, 1, 4)
        lay.addWidget(btn_replay_browse, 2, 5)
        lay.addWidget(self.btn_connect, 0, 6)
        lay.addWidget(self.btn_disconnect, 1, 7)
        lay.addWidget(self.btn_blink, 3, 0, 1, 2)
        self._sync_conn_fields()
        return g

    def _grp_position(self) -> QtWidgets.QGroupBox:
        g = QtWidgets.QGroupBox("Live Position")
        lay = QtWidgets.QGridLayout(g)
        big = "font-size:20px; font-weight:bold;"
        self._axis_labels = {}
        self._min_labels = {}
        self._max_labels = {}
        for i, axis in enumerate(("x", "y", "z")):
            cap = QtWidgets.QLabel(axis.upper())
            cap.setStyleSheet(f"color:{AXIS_COLORS[axis]}; font-weight:bold;")
            lbl = QtWidgets.QLabel("—")
            lbl.setStyleSheet(big)
            self._axis_labels[axis] = lbl
            min_l = QtWidgets.QLabel("Min: —")
            max_l = QtWidgets.QLabel("Max: —")
            min_l.setStyleSheet("color:#888; font-size:10px;")
            max_l.setStyleSheet("color:#888; font-size:10px;")
            self._min_labels[axis] = min_l
            self._max_labels[axis] = max_l
            btn = QtWidgets.QPushButton(f"{axis.upper()}=0")
            btn.clicked.connect(lambda _=False, a=axis: self._software_zero_axis(a))
            lay.addWidget(cap, 0, i * 3)
            lay.addWidget(lbl, 1, i * 3)
            lay.addWidget(min_l, 2, i * 3)
            lay.addWidget(max_l, 3, i * 3)
            lay.addWidget(btn, 1, i * 3 + 1, 2, 1)

        self._lbl_r = QtWidgets.QLabel("R —")
        self._lbl_theta = QtWidgets.QLabel("θ —")
        self._lbl_phi = QtWidgets.QLabel("φ —")
        lay.addWidget(self._lbl_r, 4, 0)
        lay.addWidget(self._lbl_theta, 4, 3)
        lay.addWidget(self._lbl_phi, 4, 6)
        self._lbl_valid = QtWidgets.QLabel("valid: —")
        self._lbl_frame = QtWidgets.QLabel("frame: —")
        self._lbl_ts = QtWidgets.QLabel("ts: —")
        lay.addWidget(self._lbl_valid, 5, 0)
        lay.addWidget(self._lbl_frame, 5, 3)
        lay.addWidget(self._lbl_ts, 5, 6)

        zero_row = QtWidgets.QHBoxLayout()
        self.btn_swzero = QtWidgets.QPushButton("Software Zero (All)")
        self.btn_swzero.clicked.connect(self._software_zero_all)
        self.btn_swclear = QtWidgets.QPushButton("Clear SW Zero")
        self.btn_swclear.clicked.connect(self._software_zero_clear)
        self.btn_hwzero = QtWidgets.QPushButton("Hardware ZERO")
        self.btn_hwzero.clicked.connect(self._hardware_zero)
        self.btn_reset_mm = QtWidgets.QPushButton("Reset Min/Max")
        self.btn_reset_mm.clicked.connect(self._reset_minmax)
        for b in (self.btn_swzero, self.btn_swclear, self.btn_hwzero, self.btn_reset_mm):
            zero_row.addWidget(b)
        lay.addLayout(zero_row, 6, 0, 1, 9)
        return g

    def _grp_battery(self) -> QtWidgets.QGroupBox:
        self._grp_batt = QtWidgets.QGroupBox("Battery")
        lay = QtWidgets.QVBoxLayout(self._grp_batt)
        self._lbl_batt_v = QtWidgets.QLabel("Voltage: N/A")
        self._lbl_batt_pct = QtWidgets.QLabel("Charge: N/A")
        self._lbl_batt_low = QtWidgets.QLabel("")
        for lbl in (self._lbl_batt_v, self._lbl_batt_pct, self._lbl_batt_low):
            lay.addWidget(lbl)
        return self._grp_batt

    def _grp_remote(self) -> QtWidgets.QGroupBox:
        g = QtWidgets.QGroupBox("ESP-NOW Remote (TCP)")
        self._remote_group = g
        lay = QtWidgets.QGridLayout(g)
        self._leds = []
        for i, text in enumerate(_LED_LABELS):
            led = QtWidgets.QLabel()
            led.setStyleSheet(_LED_IDLE[i])
            led.setAlignment(QtCore.Qt.AlignCenter)
            self._leds.append(led)
            cap = QtWidgets.QLabel(text)
            cap.setAlignment(QtCore.Qt.AlignCenter)
            lay.addWidget(led, 0, i, alignment=QtCore.Qt.AlignCenter)
            lay.addWidget(cap, 1, i)
        self._lbl_hb = QtWidgets.QLabel("Last HB: never")
        self._lbl_hb.setStyleSheet("color:#888;")
        lay.addWidget(self._lbl_hb, 2, 0, 1, 2)
        return g

    def _grp_wifi(self) -> QtWidgets.QGroupBox:
        g = QtWidgets.QGroupBox("WiFi Settings (TCP / WebSocket)")
        self._wifi_group = g
        lay = QtWidgets.QGridLayout(g)
        self.txt_ssid = QtWidgets.QLineEdit()
        self.txt_pass = QtWidgets.QLineEdit()
        self.txt_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self._lbl_router_ip = QtWidgets.QLabel("Router IP: —")
        self.btn_wifi_save = QtWidgets.QPushButton("Save & Reboot")
        self.btn_wifi_save.clicked.connect(self._save_wifi)
        self.btn_wifi_forget = QtWidgets.QPushButton("Forget")
        self.btn_wifi_forget.clicked.connect(self._forget_wifi)
        lay.addWidget(QtWidgets.QLabel("SSID"), 0, 0)
        lay.addWidget(self.txt_ssid, 0, 1)
        lay.addWidget(QtWidgets.QLabel("Password"), 0, 2)
        lay.addWidget(self.txt_pass, 0, 3)
        lay.addWidget(self.btn_wifi_save, 0, 4)
        lay.addWidget(self.btn_wifi_forget, 1, 4)
        lay.addWidget(self._lbl_router_ip, 1, 0, 1, 4)
        return g

    def _grp_sysinfo(self) -> QtWidgets.QGroupBox:
        g = QtWidgets.QGroupBox("System Info")
        lay = QtWidgets.QHBoxLayout(g)
        self._lbl_rssi = QtWidgets.QLabel("RSSI: —")
        self._lbl_heap = QtWidgets.QLabel("Heap: —")
        self._lbl_uptime = QtWidgets.QLabel("Uptime: —")
        self._lbl_tcp_clients = QtWidgets.QLabel("TCP: —")
        for lbl in (self._lbl_rssi, self._lbl_heap, self._lbl_uptime, self._lbl_tcp_clients):
            lbl.setStyleSheet("color:#666;")
            lay.addWidget(lbl)
        return g

    def _grp_commands(self) -> QtWidgets.QGroupBox:
        g = QtWidgets.QGroupBox("Quick Commands")
        lay = QtWidgets.QHBoxLayout(g)
        self._cmd_buttons = []
        for cmd in _COMMANDS:
            b = QtWidgets.QPushButton(cmd)
            b.clicked.connect(lambda _=False, c=cmd: self._send(c))
            b.setEnabled(False)
            self._cmd_buttons.append(b)
            lay.addWidget(b)
        return g

    def _grp_points(self) -> QtWidgets.QGroupBox:
        g = QtWidgets.QGroupBox("Saved Points")
        lay = QtWidgets.QVBoxLayout(g)
        row = QtWidgets.QHBoxLayout()
        self.btn_save_pt = QtWidgets.QPushButton("SAVE_POINT")
        self.btn_save_pt.clicked.connect(lambda: self._send("SAVE_POINT"))
        self.btn_del_pt = QtWidgets.QPushButton("DEL_POINT")
        self.btn_del_pt.clicked.connect(lambda: self._send("DEL_POINT"))
        row.addWidget(self.btn_save_pt)
        row.addWidget(self.btn_del_pt)
        lay.addLayout(row)
        origin_row = QtWidgets.QHBoxLayout()
        self.btn_origin = QtWidgets.QPushButton("Set Origin")
        self.btn_origin.clicked.connect(self._set_origin)
        self.btn_clear_origin = QtWidgets.QPushButton("Clear Origin")
        self.btn_clear_origin.clicked.connect(self._clear_origin)
        origin_row.addWidget(self.btn_origin)
        origin_row.addWidget(self.btn_clear_origin)
        lay.addLayout(origin_row)
        self._lbl_origin = QtWidgets.QLabel("Origin: not set")
        self._lbl_dist_origin = QtWidgets.QLabel("Distance from origin: —")
        self._lbl_dist_last = QtWidgets.QLabel("Distance last 2 points: —")
        for lbl in (self._lbl_origin, self._lbl_dist_origin, self._lbl_dist_last):
            lbl.setStyleSheet("color:#888; font-size:10px;")
            lay.addWidget(lbl)
        self._pts_list = QtWidgets.QListWidget()
        lay.addWidget(self._pts_list)
        return g

    def _build_view_panel(self) -> QtWidgets.QWidget:
        import pyqtgraph as pg
        pg.setConfigOption("background", "#1a1a2e")
        pg.setConfigOption("foreground", "#e0e0e0")
        self._pg = pg
        w = QtWidgets.QWidget()
        col = QtWidgets.QVBoxLayout(w)
        grid = QtWidgets.QGridLayout()
        self._view3d = _View3D()
        self._xy = self._make_plot("XY", "X (mm)", "Y (mm)")
        self._xz = self._make_plot("XZ", "X (mm)", "Z (mm)")
        self._yz = self._make_plot("YZ", "Y (mm)", "Z (mm)")
        grid.addWidget(self._view3d, 0, 0)
        grid.addWidget(self._xy[0], 0, 1)
        grid.addWidget(self._xz[0], 1, 0)
        grid.addWidget(self._yz[0], 1, 1)
        col.addLayout(grid)
        bar = QtWidgets.QHBoxLayout()
        btn_clear = QtWidgets.QPushButton("Clear Trail")
        btn_clear.clicked.connect(self._clear_trail)
        self._lbl_ptcount = QtWidgets.QLabel("points: 0")
        bar.addWidget(btn_clear)
        bar.addWidget(self._lbl_ptcount)
        bar.addStretch(1)
        col.addLayout(bar)
        return w

    def _make_plot(self, title, xlabel, ylabel):
        pg = self._pg
        pw = pg.PlotWidget(title=title)
        pw.setLabel("bottom", xlabel)
        pw.setLabel("left", ylabel)
        pw.showGrid(x=True, y=True, alpha=0.2)
        pw.setAspectLocked(True)
        trail = pw.plot([], [], pen=pg.mkPen("#1e78b4", width=1.5))
        head = pw.plot([], [], pen=None, symbol="o", symbolBrush=pg.mkBrush("#ff3333"), symbolSize=10)
        return pw, trail, head

    # ------------------------------------------------------------- settings
    def _refresh_ports(self) -> None:
        cur = self.cmb_port.currentText()
        self.cmb_port.clear()
        self.cmb_port.addItems([p.device for p in list_ports.comports()])
        if cur:
            self.cmb_port.setCurrentText(cur)

    def _browse_replay(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open replay CSV", "", "CSV (*.csv);;All (*)"
        )
        if path:
            self.txt_replay.setText(path)
            self.rb_replay.setChecked(True)

    def _load_settings(self) -> None:
        s = self._settings
        if s.value("serial/port"):
            self.cmb_port.setCurrentText(s.value("serial/port"))
        self.txt_baud.setText(s.value("serial/baud", "115200"))
        self.txt_ip.setText(s.value("tcp/ip", CMD_DEFAULT_STA_IP))
        self.txt_tcp_port.setText(s.value("tcp/port", str(CMD_DEFAULT_PORT)))
        self.txt_ssid.setText(s.value("wifi/ssid", ""))
        self.txt_pass.setText(s.value("wifi/pass", ""))
        mode = s.value("mode", "serial")
        if mode == "tcp":
            self.rb_tcp.setChecked(True)
        elif mode == "replay":
            self.rb_replay.setChecked(True)
        if s.value("replay/path"):
            self.txt_replay.setText(s.value("replay/path"))
        self._sync_conn_fields()

    def _save_settings(self) -> None:
        s = self._settings
        s.setValue("serial/port", self.cmb_port.currentText())
        s.setValue("serial/baud", self.txt_baud.text())
        s.setValue("tcp/ip", self.txt_ip.text())
        s.setValue("tcp/port", self.txt_tcp_port.text())
        s.setValue("wifi/ssid", self.txt_ssid.text())
        s.setValue("wifi/pass", self.txt_pass.text())
        s.setValue("replay/path", self.txt_replay.text())
        if self.rb_replay.isChecked():
            s.setValue("mode", "replay")
        elif self.rb_tcp.isChecked():
            s.setValue("mode", "tcp")
        else:
            s.setValue("mode", "serial")

    def _apply_initial(self, initial: dict) -> None:
        if initial.get("mode") == "serial":
            self.rb_serial.setChecked(True)
            if initial.get("port"):
                self.cmb_port.setCurrentText(initial["port"])
            if initial.get("baud"):
                self.txt_baud.setText(str(initial["baud"]))
        elif initial.get("mode") == "tcp":
            self.rb_tcp.setChecked(True)
            if initial.get("host"):
                self.txt_ip.setText(initial["host"])
            if initial.get("port"):
                self.txt_tcp_port.setText(str(initial["port"]))
        elif initial.get("mode") == "replay":
            self.rb_replay.setChecked(True)
            if initial.get("replay_file"):
                self.txt_replay.setText(initial["replay_file"])
        self._sync_conn_fields()

    def _sync_conn_fields(self) -> None:
        serial_mode = self.rb_serial.isChecked()
        tcp_mode = self.rb_tcp.isChecked()
        replay_mode = self.rb_replay.isChecked()
        self.cmb_port.setEnabled(serial_mode)
        self.txt_baud.setEnabled(serial_mode)
        self.txt_ip.setEnabled(tcp_mode)
        self.txt_tcp_port.setEnabled(tcp_mode)
        self.txt_replay.setEnabled(replay_mode)
        wifi_group = getattr(self, "_wifi_group", None)
        if wifi_group is not None:
            wifi_group.setEnabled(tcp_mode)
        remote_group = getattr(self, "_remote_group", None)
        if remote_group is not None:
            remote_group.setEnabled(tcp_mode or serial_mode)

    # ------------------------------------------------------------ transport
    def _connect(self) -> None:
        if self._transport is not None or getattr(self, "_is_replay", False):
            return

        if self.rb_replay.isChecked():
            path = self.txt_replay.text().strip()
            if not path:
                self._warn("Select a replay CSV file.")
                return
            frames = load_replay_frames(path)
            if not frames:
                self._warn(f"No frames in: {path}")
                return
            self._replay_frames = frames
            self._replay_idx = 0
            self._is_replay = True
            self._is_serial = False
            self._replay_timer = QtCore.QTimer(self, interval=50)
            self._replay_timer.timeout.connect(self._replay_tick)
            self._replay_timer.start()
            self._save_settings()
            self._set_connected(True)
            self._set_status(f"Replay: {Path(path).name}", "#27ae60")
            return

        if self.rb_serial.isChecked():
            port = self.cmb_port.currentText().strip()
            if not port:
                self._warn("No serial port selected.")
                return
            try:
                baud = int(self.txt_baud.text())
            except ValueError:
                self._warn("Invalid baud rate.")
                return
            tr = SerialLineReader()
            tr.set_callbacks(on_line=self._push_line, on_disconnect=self._push_disconnect)
            ok, info = tr.connect(port, baud)
            self._is_serial = True
            self._is_replay = False
        else:
            try:
                port = int(self.txt_tcp_port.text())
            except ValueError:
                self._warn("Invalid TCP port.")
                return
            tr = TcpClient()
            tr.set_callbacks(on_line=self._push_line, on_disconnect=self._push_disconnect)
            ok, info = tr.connect(self.txt_ip.text().strip(), port)
            self._is_serial = False
            self._is_replay = False

        if not ok:
            self._warn(f"Connection failed: {info}")
            return
        self._transport = tr
        self._save_settings()
        self._set_connected(True)
        self._set_status("Connected.", "#27ae60")
        self._connected_at = time.monotonic()
        if not self._is_serial:
            self._send("GET_IP")
            self._send("SYSINFO")
            self._send("STATUS")
            self._sysinfo_timer.start()

    @staticmethod
    def _format_data_line(frame) -> str:
        return (
            f"DATA,{frame.x_mm:.2f},{frame.y_mm:.2f},{frame.z_mm:.2f},"
            f"{frame.r_mm:.2f},{frame.theta_deg:.3f},{frame.phi_deg:.3f},"
            f"{1 if frame.is_valid else 0},{frame.frame_count},{frame.ts_ms}"
        )

    def _replay_tick(self) -> None:
        if self._replay_idx >= len(self._replay_frames):
            self._replay_timer.stop()
            self._set_status("Replay finished.", "#888")
            return
        frame = self._replay_frames[self._replay_idx]
        self._push_line(self._format_data_line(frame))
        self._replay_idx += 1

    def _disconnect(self) -> None:
        if hasattr(self, "_replay_timer") and self._replay_timer.isActive():
            self._replay_timer.stop()
        self._replay_frames = []
        self._replay_idx = 0
        self._is_replay = False
        self._sysinfo_timer.stop()
        self._connected_at = None
        if self._transport is not None:
            self._transport.close(emit_disconnect=False)
            self._transport = None
        self._reset_ui()
        self._set_connected(False)
        self._set_status("Disconnected.", "#c0392b")

    def _reset_ui(self) -> None:
        self._clear_pending_cmd()
        self._state.reset()
        self._display.reset_session_state()
        self._has_xyz = False
        self._saved_point_rows.clear()
        for axis, lbl in self._axis_labels.items():
            lbl.setText("—")
        for lbl in self._min_labels.values():
            lbl.setText("Min: —")
        for lbl in self._max_labels.values():
            lbl.setText("Max: —")
        self._lbl_r.setText("R —")
        self._lbl_theta.setText("θ —")
        self._lbl_phi.setText("φ —")
        self._lbl_valid.setText("valid: —")
        self._lbl_frame.setText("frame: —")
        self._lbl_ts.setText("ts: —")
        self._lbl_batt_v.setText("Voltage: N/A")
        self._lbl_batt_pct.setText("Charge: N/A")
        self._lbl_batt_low.setText("")
        self._grp_batt.setStyleSheet("")
        self._lbl_hb.setText("Last HB: never")
        self._lbl_hb.setStyleSheet("color:#888;")
        for i, led in enumerate(self._leds):
            led.setStyleSheet(_LED_IDLE[i])
        self._pts_list.clear()
        self._origin = None
        self._lbl_origin.setText("Origin: not set")
        self._lbl_dist_origin.setText("Distance from origin: —")
        self._lbl_dist_last.setText("Distance last 2 points: —")
        self._lbl_router_ip.setText("Router IP: —")
        self._lbl_rssi.setText("RSSI: —")
        self._lbl_heap.setText("Heap: —")
        self._lbl_uptime.setText("Uptime: —")
        self._lbl_tcp_clients.setText("TCP: —")
        self._update_sw_zero_badge()

    def _set_connected(self, connected: bool) -> None:
        self.btn_connect.setEnabled(not connected)
        self.btn_disconnect.setEnabled(connected)
        self.btn_blink.setEnabled(connected and not self._is_replay)
        self.rb_serial.setEnabled(not connected)
        self.rb_tcp.setEnabled(not connected)
        self.rb_replay.setEnabled(not connected)
        for b in self._cmd_buttons:
            b.setEnabled(connected and not self._is_replay)
        for b in (self.btn_swzero, self.btn_swclear, self.btn_reset_mm, self.btn_origin, self.btn_clear_origin):
            b.setEnabled(connected)
        for b in (self.btn_save_pt, self.btn_del_pt, self.btn_hwzero):
            b.setEnabled(connected and not self._is_replay)
        self.btn_wifi_save.setEnabled(connected and not self._is_replay and not self._is_serial)
        self.btn_wifi_forget.setEnabled(connected and not self._is_replay and not self._is_serial)

    def _push_line(self, line: str) -> None:
        self._queue.put(("line", line))

    def _push_disconnect(self, reason: str) -> None:
        self._queue.put(("disconnect", reason))

    def _send(self, cmd: str) -> None:
        if self._transport is None:
            self._warn("Not connected.")
            return
        ok, info = self._transport.send_command(cmd)
        if not ok:
            self._warn(f"Send failed: {info}")
            return
        self._pending_cmd = cmd.strip().upper()
        self._pending_cmd_at = time.monotonic()
        self._set_status(f"Sent {self._pending_cmd}, waiting…", "#888888")

    def _clear_pending_cmd(self) -> None:
        self._pending_cmd = None
        self._pending_cmd_at = None

    def _check_cmd_timeout(self) -> None:
        if self._pending_cmd is None or self._pending_cmd_at is None:
            return
        if time.monotonic() - self._pending_cmd_at >= CMD_RESPONSE_TIMEOUT_S:
            cmd = self._pending_cmd
            self._clear_pending_cmd()
            self._set_status(f"No response to {cmd} (timeout)", "#c0392b")

    def _poll_battery(self) -> None:
        if self._transport is not None:
            self._transport.send_command("STATUS")

    def _poll_sysinfo(self) -> None:
        if self._transport is not None and not self._is_serial:
            self._transport.send_command("SYSINFO")
            self._transport.send_command("GET_IP")

    def _check_hb_stale(self) -> None:
        if self._state.last_hb is not None and time.monotonic() - self._state.last_hb > HB_STALE_S:
            self._lbl_hb.setStyleSheet("color:#c0392b;")
        if (self._transport is not None and not self._state.battery_seen
                and self._connected_at is not None
                and time.monotonic() - self._connected_at > 10):
            self._lbl_batt_v.setText("Voltage: N/A (no data)")
            self._lbl_batt_pct.setText("Reflash firmware for BATT support")

    # -------------------------------------------------------------- drain
    def _drain(self) -> None:
        while True:
            try:
                kind, payload = self._queue.get_nowait()
            except queue.Empty:
                break
            if kind == "disconnect":
                self._set_status(f"Disconnected: {payload}", "#c0392b")
                self._disconnect()
                return
            for up in ingest_line(payload):
                self._apply(up)

    def _apply(self, up) -> None:
        k, d = up.kind, up.data
        if k == "position":
            self._on_position(*d)
        elif k == "sensor":
            self._on_sensor(*d)
        elif k == "ts":
            self._lbl_ts.setText(f"ts: {d} ms")
        elif k == "batt":
            self._on_batt(d)
        elif k == "remote_btn":
            self._on_remote_btn(d)
        elif k == "remote_hb":
            self._on_remote_hb()
        elif k == "point":
            self._on_point(d)
        elif k == "del_point":
            self._on_del_point(d)
        elif k == "ack":
            self._on_ack(d)
        elif k == "err":
            self._on_err(d)
        elif k == "sysinfo":
            self._on_sysinfo(d)
        elif k == "sta_ip":
            self._on_sta_ip(d)
        elif k == "cal":
            if self._cal_window is not None:
                self._cal_window.handle_cal(d)
        elif k == "constants":
            if self._cal_window is not None:
                self._cal_window.handle_constants(d)

    def _on_position(self, x, y, z) -> None:
        self._has_xyz = True
        pos = process_xyz_frame(self._display, x, y, z, track_minmax=True)
        self._trail.add(pos.x, pos.y, pos.z)
        self._axis_labels["x"].setText(f"{pos.x:.2f}")
        self._axis_labels["y"].setText(f"{pos.y:.2f}")
        self._axis_labels["z"].setText(f"{pos.z:.2f}")
        self._update_minmax_labels()
        self._update_axis_styles()
        if pos.update_spherical and pos.r is not None:
            self._lbl_r.setText(f"R {pos.r:.2f}")
            self._lbl_theta.setText(f"θ {pos.theta:.2f}")
            self._lbl_phi.setText(f"φ {pos.phi:.2f}")
        self._update_distance_labels()
        if self._cal_window is not None:
            self._cal_window.handle_position(pos.x, pos.y, pos.z)

    def _on_sensor(self, r, theta, phi, valid, frame) -> None:
        self._state.is_valid = bool(valid)
        if not self._display.relative_zero_active:
            self._lbl_r.setText(f"R {r:.2f}")
            self._lbl_theta.setText(f"θ {theta:.2f}")
            self._lbl_phi.setText(f"φ {phi:.2f}")
        process_sensor_line(self._display, r, theta, phi, valid, frame)
        self._lbl_valid.setText(f"valid: {'YES' if valid else 'NO'}")
        self._lbl_valid.setStyleSheet("color:#27ae60;" if valid else "color:#c0392b;")
        self._lbl_frame.setText(f"frame: {frame}")
        self._update_axis_styles()

    def _on_batt(self, batt) -> None:
        self._state.battery_seen = True
        self._lbl_batt_v.setText(f"Voltage: {batt.voltage:.3f} V")
        self._lbl_batt_pct.setText(f"Charge: {batt.pct} %")
        if batt.is_low:
            self._lbl_batt_low.setText("LOW BATTERY")
            self._grp_batt.setStyleSheet("QGroupBox { border:1px solid #c0392b; }")
        else:
            self._lbl_batt_low.setText("OK")
            self._grp_batt.setStyleSheet("")

    def _on_remote_btn(self, idx) -> None:
        self._mark_hb()
        if 0 <= idx < len(self._leds):
            self._leds[idx].setStyleSheet(_LED_FLASH[idx])
            QtCore.QTimer.singleShot(400, lambda i=idx: self._leds[i].setStyleSheet(_LED_IDLE[i]))

    def _on_remote_hb(self) -> None:
        self._mark_hb()

    def _mark_hb(self) -> None:
        self._state.last_hb = time.monotonic()
        self._lbl_hb.setText(f"Last HB: {datetime.now().strftime('%H:%M:%S')}")
        self._lbl_hb.setStyleSheet("color:#27ae60;")

    def _on_point(self, line: str) -> None:
        parts = line[len(POINT_PREFIX):].split(",")
        if len(parts) >= 4:
            idx, wx, wy, wz = parts[0], float(parts[1]), float(parts[2]), float(parts[3])
            self._saved_point_rows.append((idx, wx, wy, wz))
            self._pts_list.addItem(self._display.format_point_entry(idx, wx, wy, wz))
            self._state.saved_points += 1
            self._update_distance_labels()

    def _on_del_point(self, line: str) -> None:
        if self._pts_list.count():
            self._pts_list.takeItem(self._pts_list.count() - 1)
        if self._saved_point_rows:
            self._saved_point_rows.pop()
        self._state.saved_points = max(0, self._state.saved_points - 1)
        self._update_distance_labels()

    def _on_ack(self, line: str) -> None:
        self._clear_pending_cmd()
        self._set_status(line, "#27ae60")
        if "WIFI_SAVED" in line and self._wifi_pending:
            action = self._wifi_pending
            self._wifi_pending = None
            msg = (
                "WiFi credentials sent. Device will reboot."
                if action == "save"
                else "Credentials cleared. Device rebooting."
            )
            QtWidgets.QMessageBox.information(self, "WiFi", msg)
            self._disconnect()

    def _on_err(self, line: str) -> None:
        pending = self._pending_cmd
        self._clear_pending_cmd()
        if pending == "BLINK" and line == "ERR:UNKNOWN_CMD":
            self._set_status("ERR:UNKNOWN_CMD — reflash firmware for BLINK support", "#c0392b")
        elif line == "ERR:NO_POINTS":
            QtWidgets.QMessageBox.information(self, "Delete Point", "No saved points on device.")
        elif "WIFI" in line and self._wifi_pending:
            self._wifi_pending = None
            QtWidgets.QMessageBox.critical(self, "WiFi Error", line)
        else:
            self._set_status(line, "#c0392b")

    def _on_sysinfo(self, si: SysInfo) -> None:
        self._lbl_rssi.setText(
            f"RSSI: {si.rssi} dBm" if si.rssi != 0 else "RSSI: n/a"
        )
        self._lbl_heap.setText(f"Heap: {si.heap // 1024} KB")
        h, m, s = si.uptime_s // 3600, (si.uptime_s % 3600) // 60, si.uptime_s % 60
        self._lbl_uptime.setText(f"Uptime: {h:02d}:{m:02d}:{s:02d}")
        self._lbl_tcp_clients.setText(f"TCP: {si.tcp_clients}")

    def _on_sta_ip(self, ip: str) -> None:
        self._lbl_router_ip.setText(f"Router IP: {sta_ip_display(ip)}")
        if sta_ip_is_connected(ip):
            self.txt_ip.setText(ip)

    def _update_minmax_labels(self) -> None:
        for axis in ("x", "y", "z"):
            mn, mx = self._display.min_vals[axis], self._display.max_vals[axis]
            self._min_labels[axis].setText(
                f"Min: {mn:.1f}" if mn != math.inf else "Min: —"
            )
            self._max_labels[axis].setText(
                f"Max: {mx:.1f}" if mx != -math.inf else "Max: —"
            )

    def _update_axis_styles(self) -> None:
        invalid = self._state.is_valid is False
        for axis, lbl in self._axis_labels.items():
            color = AXIS_INVALID_COLOR if invalid else AXIS_COLORS[axis]
            lbl.setStyleSheet(f"font-size:20px; font-weight:bold; color:{color};")

    def _update_sw_zero_badge(self) -> None:
        if self._display.relative_zero_active:
            self._lbl_sw_zero.setText("SW ZERO active")
            self._lbl_sw_zero.show()
        else:
            self._lbl_sw_zero.hide()

    # ------------------------------------------------------------- actions
    def _refresh_display_from_raw(self, *, track_minmax: bool = False) -> None:
        if not self._has_xyz:
            return
        pos = process_xyz_frame(
            self._display,
            self._display.last_raw_x,
            self._display.last_raw_y,
            self._display.last_raw_z,
            track_minmax=track_minmax,
        )
        self._trail.add(pos.x, pos.y, pos.z)
        self._axis_labels["x"].setText(f"{pos.x:.2f}")
        self._axis_labels["y"].setText(f"{pos.y:.2f}")
        self._axis_labels["z"].setText(f"{pos.z:.2f}")
        if track_minmax:
            self._update_minmax_labels()
        self._update_axis_styles()
        if pos.update_spherical and pos.r is not None:
            self._lbl_r.setText(f"R {pos.r:.2f}")
            self._lbl_theta.setText(f"θ {pos.theta:.2f}")
            self._lbl_phi.setText(f"φ {pos.phi:.2f}")

    def _activate_sw_zero(self, *, ox=None, oy=None, oz=None, reset_mm=True) -> None:
        if not self._has_xyz:
            self._warn("No position data yet.")
            return
        if ox is not None:
            self._display.offset_x = ox
        if oy is not None:
            self._display.offset_y = oy
        if oz is not None:
            self._display.offset_z = oz
        self._display.relative_zero_active = True
        if reset_mm:
            self._reset_minmax()
        self._trail.clear()
        self._update_sw_zero_badge()
        self._refresh_display_from_raw()

    def _software_zero_axis(self, axis: str) -> None:
        raw = getattr(self._display, f"last_raw_{axis}")
        kw = {"ox": raw} if axis == "x" else {"oy": raw} if axis == "y" else {"oz": raw}
        self._activate_sw_zero(**kw)

    def _software_zero_all(self) -> None:
        self._activate_sw_zero(
            ox=self._display.last_raw_x,
            oy=self._display.last_raw_y,
            oz=self._display.last_raw_z,
        )
        self._set_status("Software zero applied.", "#27ae60")

    def _software_zero_clear(self) -> None:
        self._display.clear_software_zero()
        self._trail.clear()
        self._update_sw_zero_badge()
        self._refresh_display_from_raw()
        self._set_status("Software zero cleared.", "#e0e0e0")

    def _hardware_zero(self) -> None:
        if QtWidgets.QMessageBox.question(
            self, "Hardware Zero",
            "Reset encoder offsets at mechanical home?\nSend ZERO only when at home.",
        ) != QtWidgets.QMessageBox.Yes:
            return
        self._display.clear_software_zero()
        self._reset_minmax()
        self._update_sw_zero_badge()
        self._send("ZERO")

    def _reset_minmax(self) -> None:
        self._display.reset_minmax()
        self._update_minmax_labels()

    def _raw_position(self) -> Tuple[float, float, float]:
        return (self._display.last_raw_x, self._display.last_raw_y, self._display.last_raw_z)

    def _set_origin(self) -> None:
        if not self._has_xyz:
            self._warn("No position data yet.")
            return
        self._origin = self._raw_position()
        self._lbl_origin.setText(
            f"Origin: {self._origin[0]:.1f}, {self._origin[1]:.1f}, {self._origin[2]:.1f} mm"
        )
        self._update_distance_labels()

    def _clear_origin(self) -> None:
        self._origin = None
        self._lbl_origin.setText("Origin: not set")
        self._lbl_dist_origin.setText("Distance from origin: —")

    def _update_distance_labels(self) -> None:
        if self._origin is not None and self._has_xyz:
            x, y, z = self._raw_position()
            ox, oy, oz = self._origin
            d = math.sqrt((x - ox) ** 2 + (y - oy) ** 2 + (z - oz) ** 2)
            self._lbl_dist_origin.setText(f"Distance from origin: {d:.1f} mm")
        if len(self._saved_point_rows) >= 2:
            _, ax, ay, az = self._saved_point_rows[-2]
            _, bx, by, bz = self._saved_point_rows[-1]
            d = math.sqrt((bx - ax) ** 2 + (by - ay) ** 2 + (bz - az) ** 2)
            self._lbl_dist_last.setText(f"Distance last 2 points: {d:.1f} mm")
        else:
            self._lbl_dist_last.setText("Distance last 2 points: —")

    def _save_wifi(self) -> None:
        ssid = self.txt_ssid.text().strip()
        password = self.txt_pass.text()
        if not ssid:
            self._warn("SSID required.")
            return
        if password and len(password) < 8:
            self._warn("Password must be empty or ≥8 characters.")
            return
        self._wifi_pending = "save"
        self._send(f"WIFI_SET:{ssid},{password}")

    def _forget_wifi(self) -> None:
        if QtWidgets.QMessageBox.question(
            self, "Forget WiFi", "Erase stored credentials and reboot?"
        ) != QtWidgets.QMessageBox.Yes:
            return
        self._wifi_pending = "forget"
        self._send("WIFI_SET:,")

    def _open_calibration(self) -> None:
        if self._cal_window is None:
            self._cal_window = CalibrationWindow(self._send_for_cal, self)
            self._cal_window.destroyed.connect(lambda: setattr(self, "_cal_window", None))
        self._cal_window.show()
        self._cal_window.raise_()

    def _send_for_cal(self, cmd: str) -> None:
        if self._transport is None:
            QtWidgets.QMessageBox.warning(self, "Calibration", "Connect to device first.")
            return
        self._transport.send_command(cmd)

    def _export_session(self) -> None:
        if not self._saved_point_rows:
            self._warn("No saved points to export.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export session", f"evka_session_{int(time.time())}.csv", "CSV (*.csv)"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["label", "x_mm", "y_mm", "z_mm", "rel_x_mm", "rel_y_mm", "rel_z_mm"])
            ox, oy, oz = self._origin or (0.0, 0.0, 0.0)
            if self._origin is not None:
                w.writerow(["ORIGIN", f"{ox:.3f}", f"{oy:.3f}", f"{oz:.3f}", "0.000", "0.000", "0.000"])
            for idx, x, y, z in self._saved_point_rows:
                w.writerow([
                    f"P{idx}", f"{x:.3f}", f"{y:.3f}", f"{z:.3f}",
                    f"{x - ox:.3f}", f"{y - oy:.3f}", f"{z - oz:.3f}",
                ])
        self._set_status(f"Exported {len(self._saved_point_rows)} points.", "#27ae60")

    def _clear_trail(self) -> None:
        self._trail.clear()

    def _refresh_views(self) -> None:
        xs, ys, zs = self._trail.xs(), self._trail.ys(), self._trail.zs()
        self._view3d.set_data(xs, ys, zs)
        n = len(xs)
        for (_, trail, head), (a, b) in (
            (self._xy, (xs, ys)),
            (self._xz, (xs, zs)),
            (self._yz, (ys, zs)),
        ):
            trail.setData(a, b)
            if n:
                head.setData([a[-1]], [b[-1]])
            else:
                head.setData([], [])
        self._lbl_ptcount.setText(f"points: {n}")

    def _set_status(self, text: str, color: str) -> None:
        self._lbl_status.setText(text)
        self._lbl_status.setStyleSheet(f"color:{color}; font-weight:bold;")

    def _warn(self, text: str) -> None:
        QtWidgets.QMessageBox.warning(self, "EVKA Position", text)

    def closeEvent(self, event) -> None:
        for t in (self._drain_timer, self._view_timer, self._batt_timer, self._hb_timer,
                  self._cmd_timer, self._sysinfo_timer):
            t.stop()
        if hasattr(self, "_replay_timer"):
            self._replay_timer.stop()
        if self._transport is not None:
            self._transport.close(emit_disconnect=False)
            self._transport = None
        if self._cal_window is not None:
            self._cal_window.close()
        self._save_settings()
        super().closeEvent(event)


def run(initial: Optional[dict] = None) -> int:
    app = QtWidgets.QApplication.instance()
    created = app is None
    if created:
        app = QtWidgets.QApplication(sys.argv)
    win = EvkaWindow(initial)
    win.show()
    return app.exec_() if created else 0
