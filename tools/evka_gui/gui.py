"""gui.py — EvkaWindow: unified dual-transport control panel + 3D view."""

from __future__ import annotations

import csv
import math
import queue
import sys
import time
import webbrowser
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
    DATA_PREFIX,
    DEL_POINT_PREFIX,
    POINT_PREFIX,
)
from tools.position_checker.gui import _View3D
from tools.position_checker.parser import parse_sensor_line, parse_xyz_line
from tools.position_checker.replay_reader import load_replay_frames

from .calibration import CalibrationWindow
from .ipt_panel import IptPanel, ipt_marker_coords, ipt_projections, ipt_sphere_circle
from .ipt_window import IptPlotsWindow
from .model import (
    SysInfo,
    TrailBuffer,
    UiState,
    command_response_matches,
    ingest_line,
    is_frame_line,
)
from .protocol_log import ProtocolLogPane
from .remote_window import RemoteTesterWindow
from .replay_utils import interval_for_speed
from .session_utils import (
    default_export_path,
    delete_profile,
    format_constants_strip,
    format_data_line,
    format_raw_counts_line,
    format_snapshot_row,
    list_profiles,
    load_profile,
    save_profile,
    write_saved_points_csv,
    write_snapshots_csv,
)
from .transport import SerialLineReader, TcpClient, WsClient, next_backoff
from .wifi_window import WifiSettingsWindow

TRAIL_MAX = 800
CMD_DEFAULT_WS_PORT = 80
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
_LED_LABELS = ["BTN0\nSAVE POINT", "BTN1\nDEL LAST POINT"]

_COMMANDS = [
    "ZERO", "ZERO_T", "ZERO_P", "ZERO_W", "PING", "STATUS", "RAW_COUNTS",
    "SAVE_POINT", "DEL_POINT", "SYSINFO",
]

_CMD_COLORS = {
    "ZERO": "#ffd700", "ZERO_T": "#ffd700", "ZERO_P": "#ffd700", "ZERO_W": "#ffd700",
    "PING": "#00ffff", "STATUS": "#00ffff", "RAW_COUNTS": "#00ffff", "SYSINFO": "#00ffff",
    "SAVE_POINT": "#00ff88", "DEL_POINT": "#ff4444",
}


def _btn_style(fg: str) -> str:
    return (
        f"QPushButton {{ color: {fg}; border: 1px solid {fg}; padding: 4px 8px;"
        f" background: transparent; border-radius: 3px; }}"
        f"QPushButton:hover {{ background: {fg}22; }}"
        f"QPushButton:disabled {{ color: #555; border-color: #444; background: transparent; }}"
    )


class _SplitPane(QtWidgets.QWidget):
    """Splitter child with a modest size hint so 50/50 layout can shrink plots."""

    def minimumSizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(320, 300)


class EvkaWindow(QtWidgets.QMainWindow):
    def __init__(self, initial: Optional[dict] = None):
        super().__init__()
        self.setWindowTitle("EVKA Position — Control")
        self.resize(1500, 860)
        self.setMinimumSize(1050, 700)
        self.showMaximized()

        self._transport = None
        self._is_serial = False
        self._is_ws = False
        self._is_replay = False
        self._replay_frames: list = []
        self._replay_idx = 0
        self._replay_paused = False
        self._replay_speed = 1.0
        self._queue: queue.Queue = queue.Queue()
        self._trail_max = TRAIL_MAX
        self._trail = TrailBuffer(self._trail_max)
        self._display = CmdDisplayState()
        self._state = UiState(self._trail)
        self._settings = QtCore.QSettings("evka_position", "evka_gui")
        self._pending_commands: List[Tuple[str, float]] = []
        self._wifi_pending: Optional[str] = None
        self._wifi_ssid_cached = ""
        self._wifi_pass_cached = ""
        self._has_xyz = False
        self._saved_point_rows: List[Tuple[str, float, float, float]] = []
        self._snapshots: List[Tuple[int, float, float, float, str]] = []
        self._snapshot_idx = 0
        self._origin: Optional[Tuple[float, float, float]] = None
        self._sta_ip_cached = ""
        self._constants_line = ""
        self._raw_counts_line = ""
        self._show_trail = True
        self._show_ipt = True
        self._show_origin = True
        self._show_saved_pts = True
        self._cal_window: Optional[CalibrationWindow] = None
        self._wifi_window: Optional[WifiSettingsWindow] = None
        self._ipt_plots_window: Optional[IptPlotsWindow] = None
        self._remote_window: Optional[RemoteTesterWindow] = None
        self._protocol_log: Optional[ProtocolLogPane] = None
        self._connected_at: Optional[float] = None
        self._frozen = False
        self._reconnect_delay = 0.0
        self._reconnect_attempts = 0
        self._rec_file = None
        self._rec_xyz: Optional[Tuple[float, float, float]] = None
        self._rec_count = 0
        self._rec_t0 = 0.0

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
        self._reconnect_timer = QtCore.QTimer(self, singleShot=True, timeout=self._reconnect_attempt)
        for t in (self._drain_timer, self._view_timer, self._batt_timer, self._hb_timer, self._cmd_timer):
            t.start()

        if initial and initial.get("autoconnect"):
            QtCore.QTimer.singleShot(0, self._connect)

        self._setup_shortcuts()

    def _setup_shortcuts(self) -> None:
        QtWidgets.QShortcut(QtGui.QKeySequence("Z"), self, activated=self._hardware_zero)
        QtWidgets.QShortcut(QtGui.QKeySequence("S"), self, activated=lambda: self._send("SAVE_POINT"))
        QtWidgets.QShortcut(QtGui.QKeySequence("A"), self, activated=self._ipt_panel.btn_arm.click)
        QtWidgets.QShortcut(QtGui.QKeySequence("Escape"), self, activated=self._ipt_panel._stop)

    def _build_ui(self) -> None:
        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        split.setChildrenCollapsible(False)
        split.setHandleWidth(6)

        left = self._build_control_panel()
        left.setMinimumWidth(0)
        left.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
        )
        split.addWidget(left)

        views = self._build_view_panel()
        views.setMinimumWidth(0)
        views.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
        )
        split.addWidget(views)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 1)
        split.splitterMoved.connect(self._on_split_moved)
        self._split = split
        self._split_user_moved = False
        self._balancing_split = False
        self._left_panel = left
        self.setCentralWidget(split)

        toolbar = self.addToolBar("Main")
        self._act_record = toolbar.addAction("Record")
        self._act_record.setCheckable(True)
        self._act_record.setToolTip("Write the live stream to a replayable DATA-line file")
        self._act_record.toggled.connect(self._toggle_record)
        self._act_freeze = toolbar.addAction("Freeze")
        self._act_freeze.setCheckable(True)
        self._act_freeze.setToolTip("Pause the live position stream (the link stays up)")
        self._act_freeze.toggled.connect(self._set_frozen)
        toolbar.addSeparator()
        act_cal = toolbar.addAction("Calibration…")
        act_cal.triggered.connect(self._open_calibration)
        self._act_wifi = toolbar.addAction("WiFi Settings…")
        self._act_wifi.triggered.connect(self._open_wifi)
        self._act_ipt_plots = toolbar.addAction("IPT plots…")
        self._act_ipt_plots.triggered.connect(self._open_ipt_plots)
        act_remote = toolbar.addAction("Remote Tester…")
        act_remote.triggered.connect(self._open_remote_tester)
        act_snap = toolbar.addAction("Capture Snapshot")
        act_snap.triggered.connect(self._capture_snapshot)
        act_snap_clear = toolbar.addAction("Clear Snapshots")
        act_snap_clear.triggered.connect(self._clear_snapshots)
        act_snap_export = toolbar.addAction("Export Snapshots CSV")
        act_snap_export.triggered.connect(self._export_snapshots)
        act_pts_export = toolbar.addAction("Export Saved Points CSV")
        act_pts_export.triggered.connect(self._export_saved_points)
        act_dashboard = toolbar.addAction("Open Dashboard")
        act_dashboard.triggered.connect(self._open_dashboard)
        act_export = toolbar.addAction("Export Session CSV")
        act_export.triggered.connect(self._export_session)

    def _build_control_panel(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        w.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred,
        )
        col = QtWidgets.QVBoxLayout(w)
        col.setSpacing(4)
        col.setContentsMargins(4, 4, 4, 4)
        col.addWidget(self._grp_connection())
        col.addWidget(self._grp_position())

        tabs = QtWidgets.QTabWidget()
        tabs.setDocumentMode(True)
        self._ipt_panel = IptPanel()
        self._ipt_panel.state_changed.connect(self._refresh_views)
        self._ipt_panel.add_p_to_snapshots.connect(self._add_ipt_snapshot)
        # Arming while frozen would capture zero points and look broken.
        self._ipt_panel.btn_arm.clicked.connect(lambda: self._set_frozen(False))
        tabs.addTab(self._ipt_panel, "IPT")
        tabs.addTab(self._grp_points(), "Points")
        tabs.addTab(self._grp_diagnostics(), "Diagnostics")
        tabs.addTab(self._grp_commands(), "Commands")
        col.addWidget(tabs, 1)

        log_box = QtWidgets.QGroupBox("Protocol Log")
        log_lay = QtWidgets.QVBoxLayout(log_box)
        log_lay.setContentsMargins(4, 4, 4, 4)
        self._protocol_log = ProtocolLogPane(compact=True)
        log_lay.addWidget(self._protocol_log)
        log_box.setMaximumHeight(118)
        col.addWidget(log_box)

        footer = QtWidgets.QHBoxLayout()
        self._lbl_sw_zero = QtWidgets.QLabel("")
        self._lbl_sw_zero.setStyleSheet(
            "color:#4488ff; background:#ebf5fb; padding:2px 6px; border-radius:4px; font-size:10px;"
        )
        self._lbl_sw_zero.hide()
        self._lbl_status = QtWidgets.QLabel("Disconnected.")
        self._lbl_status.setStyleSheet("color:#ff4444; font-weight:bold; font-size:10px;")
        footer.addWidget(self._lbl_sw_zero)
        footer.addWidget(self._lbl_status, 1)
        col.addLayout(footer)
        return w

    def _grp_connection(self) -> QtWidgets.QGroupBox:
        g = QtWidgets.QGroupBox("Connection")
        lay = QtWidgets.QGridLayout(g)
        lay.setHorizontalSpacing(4)
        lay.setVerticalSpacing(3)
        self.rb_serial = QtWidgets.QRadioButton("Serial")
        self.rb_tcp = QtWidgets.QRadioButton("WiFi / TCP")
        self.rb_ws = QtWidgets.QRadioButton("WebSocket")
        self.rb_replay = QtWidgets.QRadioButton("Replay CSV")
        self.rb_serial.setChecked(True)
        self.rb_serial.toggled.connect(self._sync_conn_fields)
        self.rb_tcp.toggled.connect(self._sync_conn_fields)
        self.rb_ws.toggled.connect(self._sync_conn_fields)
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
        self.txt_ws_host = QtWidgets.QLineEdit(CMD_AP_FALLBACK_IP)
        self.txt_ws_host.setToolTip(f"HTTP/WebSocket host (port {CMD_DEFAULT_WS_PORT}, path /ws)")
        btn_ap = QtWidgets.QPushButton("AP")
        btn_ap.setToolTip(f"Use AP fallback {CMD_AP_FALLBACK_IP}")
        btn_ap.clicked.connect(lambda: self.txt_ip.setText(CMD_AP_FALLBACK_IP))
        btn_sta = QtWidgets.QPushButton("STA")
        btn_sta.setToolTip(f"Use STA {CMD_DEFAULT_STA_IP}")
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

        self.btn_blink = QtWidgets.QPushButton("BLINK LED")
        self.btn_blink.setToolTip("Send BLINK — status LED flashes if link is alive")
        self.btn_blink.clicked.connect(lambda: self._send("BLINK"))
        self.btn_blink.setEnabled(False)

        self.btn_connect.setStyleSheet(_btn_style("#00ff88"))
        self.btn_disconnect.setStyleSheet(_btn_style("#ff4444"))
        self.btn_blink.setStyleSheet(_btn_style("#00ffff"))
        btn_ap.setStyleSheet(_btn_style("#4488ff"))
        btn_sta.setStyleSheet(_btn_style("#4488ff"))

        mode_row = QtWidgets.QHBoxLayout()
        mode_row.setContentsMargins(0, 0, 0, 0)
        for rb in (self.rb_serial, self.rb_tcp, self.rb_ws, self.rb_replay):
            mode_row.addWidget(rb)
        mode_row.addStretch(1)
        mode_w = QtWidgets.QWidget()
        mode_w.setLayout(mode_row)
        lay.addWidget(mode_w, 0, 0, 1, 4)

        serial_row = QtWidgets.QHBoxLayout()
        serial_row.setContentsMargins(0, 0, 0, 0)
        serial_row.addWidget(self.cmb_port, 1)
        serial_row.addWidget(btn_rescan)
        serial_row.addWidget(QtWidgets.QLabel("Baud"))
        serial_row.addWidget(self.txt_baud)
        serial_w = QtWidgets.QWidget()
        serial_w.setLayout(serial_row)
        lay.addWidget(QtWidgets.QLabel("Serial"), 1, 0)
        lay.addWidget(serial_w, 1, 1, 1, 3)

        tcp_row = QtWidgets.QHBoxLayout()
        tcp_row.setContentsMargins(0, 0, 0, 0)
        tcp_row.addWidget(self.txt_ip, 1)
        tcp_row.addWidget(btn_ap)
        tcp_row.addWidget(btn_sta)
        tcp_row.addWidget(QtWidgets.QLabel("Port"))
        tcp_row.addWidget(self.txt_tcp_port)
        tcp_w = QtWidgets.QWidget()
        tcp_w.setLayout(tcp_row)
        lay.addWidget(QtWidgets.QLabel("TCP"), 2, 0)
        lay.addWidget(tcp_w, 2, 1, 1, 3)

        lay.addWidget(QtWidgets.QLabel("WS"), 3, 0)
        lay.addWidget(self.txt_ws_host, 3, 1, 1, 3)

        replay_row = QtWidgets.QHBoxLayout()
        replay_row.setContentsMargins(0, 0, 0, 0)
        replay_row.addWidget(self.txt_replay, 1)
        replay_row.addWidget(btn_replay_browse)
        replay_w = QtWidgets.QWidget()
        replay_w.setLayout(replay_row)
        lay.addWidget(QtWidgets.QLabel("Replay"), 4, 0)
        lay.addWidget(replay_w, 4, 1, 1, 3)

        conn_row = QtWidgets.QHBoxLayout()
        conn_row.setContentsMargins(0, 0, 0, 0)
        for btn in (self.btn_connect, self.btn_disconnect, self.btn_blink):
            conn_row.addWidget(btn)
        conn_w = QtWidgets.QWidget()
        conn_w.setLayout(conn_row)
        lay.addWidget(conn_w, 5, 0, 1, 4)

        prof_row = QtWidgets.QHBoxLayout()
        self.cmb_profile = QtWidgets.QComboBox()
        self.cmb_profile.addItem("(none)")
        self._refresh_profile_combo()
        btn_prof_load = QtWidgets.QPushButton("Load")
        btn_prof_load.clicked.connect(self._load_connection_profile)
        btn_prof_save = QtWidgets.QPushButton("Save…")
        btn_prof_save.clicked.connect(self._save_connection_profile)
        btn_prof_del = QtWidgets.QPushButton("Delete")
        btn_prof_del.clicked.connect(self._delete_connection_profile)
        prof_row.addWidget(QtWidgets.QLabel("Profile:"))
        prof_row.addWidget(self.cmb_profile, 1)
        prof_row.addWidget(btn_prof_load)
        prof_row.addWidget(btn_prof_save)
        prof_row.addWidget(btn_prof_del)
        prof_w = QtWidgets.QWidget()
        prof_w.setLayout(prof_row)
        lay.addWidget(prof_w, 6, 0, 1, 4)
        lay.setColumnStretch(1, 1)
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
            btn.setStyleSheet(_btn_style(AXIS_COLORS[axis]))
            btn.clicked.connect(lambda _=False, a=axis: self._software_zero_axis(a))
            btn_copy = QtWidgets.QPushButton("Copy")
            btn_copy.setFixedWidth(48)
            btn_copy.setStyleSheet(_btn_style("#8899aa"))
            btn_copy.clicked.connect(lambda _=False, a=axis: self._copy_axis(a))
            lay.addWidget(cap, 0, i * 4)
            lay.addWidget(lbl, 1, i * 4)
            lay.addWidget(min_l, 2, i * 4)
            lay.addWidget(max_l, 3, i * 4)
            lay.addWidget(btn, 1, i * 4 + 1, 2, 1)
            lay.addWidget(btn_copy, 1, i * 4 + 2, 2, 1)

        self._lbl_r = QtWidgets.QLabel("R —")
        self._lbl_theta = QtWidgets.QLabel("θ —")
        self._lbl_phi = QtWidgets.QLabel("φ —")
        lay.addWidget(self._lbl_r, 4, 0)
        lay.addWidget(self._lbl_theta, 4, 4)
        lay.addWidget(self._lbl_phi, 4, 8)
        self._lbl_valid = QtWidgets.QLabel("valid: —")
        self._lbl_frame = QtWidgets.QLabel("frame: —")
        self._lbl_ts = QtWidgets.QLabel("ts: —")
        lay.addWidget(self._lbl_valid, 5, 0)
        lay.addWidget(self._lbl_frame, 5, 4)
        lay.addWidget(self._lbl_ts, 5, 8)
        btn_copy_r = QtWidgets.QPushButton("Copy Rθφ")
        btn_copy_r.setStyleSheet(_btn_style("#8899aa"))
        btn_copy_r.clicked.connect(self._copy_spherical)
        lay.addWidget(btn_copy_r, 6, 0, 1, 3)

        zero_row = QtWidgets.QHBoxLayout()
        self.btn_swzero = QtWidgets.QPushButton("ZERO (SW)")
        self.btn_swzero.setStyleSheet(_btn_style("#4488ff"))
        self.btn_swzero.clicked.connect(self._software_zero_all)
        self.btn_swclear = QtWidgets.QPushButton("CLEAR SW ZERO")
        self.btn_swclear.setStyleSheet(_btn_style("#8899aa"))
        self.btn_swclear.clicked.connect(self._software_zero_clear)
        self.btn_hwzero = QtWidgets.QPushButton("ZERO (HW)")
        self.btn_hwzero.setStyleSheet(_btn_style("#ffd700"))
        self.btn_hwzero.clicked.connect(self._hardware_zero)
        self.btn_reset_mm = QtWidgets.QPushButton("RESET MIN/MAX")
        self.btn_reset_mm.setStyleSheet(_btn_style("#8e44ad"))
        self.btn_reset_mm.clicked.connect(self._reset_minmax)
        for b in (self.btn_swzero, self.btn_swclear, self.btn_hwzero, self.btn_reset_mm):
            zero_row.addWidget(b)
        lay.addLayout(zero_row, 7, 0, 1, 12)
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

    def _grp_diagnostics(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)
        status_row = QtWidgets.QHBoxLayout()
        status_row.setSpacing(4)
        status_row.addWidget(self._grp_battery(), 1)
        status_row.addWidget(self._grp_remote(), 1)
        lay.addLayout(status_row)
        self._lbl_sysinfo = QtWidgets.QLabel("RSSI — · Heap — · Uptime — · TCP —")
        self._lbl_sysinfo.setStyleSheet("color:#666; font-size:10px; font-family:Consolas;")
        self._lbl_sysinfo.setWordWrap(True)
        self._lbl_constants = QtWidgets.QLabel("PPR —")
        self._lbl_constants.setStyleSheet("color:#666; font-size:10px; font-family:Consolas;")
        self._lbl_constants.setWordWrap(True)
        self._lbl_raw_counts = QtWidgets.QLabel("Raw counts —")
        self._lbl_raw_counts.setStyleSheet("color:#666; font-size:10px; font-family:Consolas;")
        self._lbl_raw_counts.setWordWrap(True)
        for lbl in (self._lbl_sysinfo, self._lbl_constants, self._lbl_raw_counts):
            lay.addWidget(lbl)
        lay.addStretch(1)
        return w

    def _grp_commands(self) -> QtWidgets.QGroupBox:
        g = QtWidgets.QGroupBox("Quick Commands")
        lay = QtWidgets.QGridLayout(g)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setHorizontalSpacing(4)
        lay.setVerticalSpacing(4)
        self._cmd_buttons = []
        cols = 5
        for i, cmd in enumerate(_COMMANDS):
            b = QtWidgets.QPushButton(cmd)
            b.setStyleSheet(_btn_style(_CMD_COLORS.get(cmd, "#8899aa")))
            b.clicked.connect(lambda _=False, c=cmd: self._send(c))
            b.setEnabled(False)
            self._cmd_buttons.append(b)
            lay.addWidget(b, i // cols, i % cols)
        return g

    def _grp_points(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)
        row = QtWidgets.QHBoxLayout()
        self.btn_save_pt = QtWidgets.QPushButton("SAVE POINT")
        self.btn_save_pt.setStyleSheet(_btn_style("#00ff88"))
        self.btn_save_pt.clicked.connect(lambda: self._send("SAVE_POINT"))
        self.btn_del_pt = QtWidgets.QPushButton("DEL LAST POINT")
        self.btn_del_pt.setStyleSheet(_btn_style("#ff4444"))
        self.btn_del_pt.clicked.connect(lambda: self._send("DEL_POINT"))
        row.addWidget(self.btn_save_pt)
        row.addWidget(self.btn_del_pt)
        lay.addLayout(row)
        origin_row = QtWidgets.QHBoxLayout()
        self.btn_origin = QtWidgets.QPushButton("SET ORIGIN")
        self.btn_origin.setStyleSheet(_btn_style("#ffd700"))
        self.btn_origin.clicked.connect(self._set_origin)
        self.btn_clear_origin = QtWidgets.QPushButton("CLEAR ORIGIN")
        self.btn_clear_origin.setStyleSheet(_btn_style("#8899aa"))
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
        self._pts_list.setMinimumHeight(160)
        self._pts_list.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        lay.addWidget(self._pts_list, 1)
        return w

    def _build_view_panel(self) -> QtWidgets.QWidget:
        import pyqtgraph as pg
        pg.setConfigOption("background", "#1a1a2e")
        pg.setConfigOption("foreground", "#eeeeff")
        self._pg = pg
        w = _SplitPane()
        col = QtWidgets.QVBoxLayout(w)
        col.setContentsMargins(4, 4, 4, 4)
        col.setSpacing(4)
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(4)
        self._view3d = _View3D(rot_x=30.0, rot_y=45.0)
        self._view3d.setMinimumSize(160, 160)
        self._xy = self._make_plot("XY", "X (mm)", "Y (mm)")
        self._xz = self._make_plot("XZ", "X (mm)", "Z (mm)")
        self._yz = self._make_plot("YZ", "Y (mm)", "Z (mm)")
        for plot_tuple in (self._xy, self._xz, self._yz):
            plot_tuple[0].setMinimumSize(160, 120)
        self._ipt_cloud: dict = {}
        self._ipt_marker: dict = {}
        self._ipt_sphere: dict = {"xy": [], "xz": [], "yz": []}
        self._origin_marker: dict = {}
        self._saved_markers: dict = {}
        for key, plot_tuple in (("xy", self._xy), ("xz", self._xz), ("yz", self._yz)):
            pw = plot_tuple[0]
            self._ipt_cloud[key] = pw.plot(
                [], [], pen=None, symbol="o", symbolSize=5,
                symbolBrush=pg.mkBrush("#00ff88"), symbolPen=None)
            self._ipt_marker[key] = pw.plot(
                [], [], pen=None, symbol="o", symbolSize=12,
                symbolBrush=pg.mkBrush("#ff8c00"), symbolPen=None)
            self._origin_marker[key] = pw.plot(
                [], [], pen=None, symbol="+", symbolSize=16,
                symbolPen=pg.mkPen("#ffd700", width=2), symbolBrush=None)
            self._saved_markers[key] = pw.plot(
                [], [], pen=None, symbol="o", symbolSize=7,
                symbolBrush=pg.mkBrush("#f1c40f"), symbolPen=pg.mkPen("#222222"))
        grid.addWidget(self._view3d, 0, 0)
        grid.addWidget(self._xy[0], 0, 1)
        grid.addWidget(self._xz[0], 1, 0)
        grid.addWidget(self._yz[0], 1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        layer_row = QtWidgets.QHBoxLayout()
        self._chk_trail = QtWidgets.QCheckBox("Trail")
        self._chk_trail.setChecked(True)
        self._chk_trail.toggled.connect(self._on_layer_toggle)
        self._chk_ipt = QtWidgets.QCheckBox("IPT")
        self._chk_ipt.setChecked(True)
        self._chk_ipt.toggled.connect(self._on_layer_toggle)
        self._chk_origin = QtWidgets.QCheckBox("Origin")
        self._chk_origin.setChecked(True)
        self._chk_origin.toggled.connect(self._on_layer_toggle)
        self._chk_saved = QtWidgets.QCheckBox("Saved pts")
        self._chk_saved.setChecked(True)
        self._chk_saved.toggled.connect(self._on_layer_toggle)
        layer_row.addWidget(QtWidgets.QLabel("Layers:"))
        for chk in (self._chk_trail, self._chk_ipt, self._chk_origin, self._chk_saved):
            layer_row.addWidget(chk)
        layer_row.addWidget(QtWidgets.QLabel("Trail max:"))
        self._spin_trail = QtWidgets.QSpinBox()
        self._spin_trail.setRange(50, 5000)
        self._spin_trail.setValue(self._trail_max)
        self._spin_trail.valueChanged.connect(self._on_trail_max_changed)
        layer_row.addWidget(self._spin_trail)
        layer_row.addStretch(1)
        col.addLayout(layer_row)

        self._replay_bar = QtWidgets.QWidget()
        replay_lay = QtWidgets.QHBoxLayout(self._replay_bar)
        replay_lay.setContentsMargins(0, 0, 0, 0)
        self._btn_replay_play = QtWidgets.QPushButton("Pause")
        self._btn_replay_play.clicked.connect(self._toggle_replay_pause)
        self._btn_replay_step_back = QtWidgets.QPushButton("◀")
        self._btn_replay_step_back.clicked.connect(lambda: self._replay_step(-1))
        self._btn_replay_step_fwd = QtWidgets.QPushButton("▶")
        self._btn_replay_step_fwd.clicked.connect(lambda: self._replay_step(1))
        self._cmb_replay_speed = QtWidgets.QComboBox()
        for s in ("0.25×", "0.5×", "1×", "2×", "4×"):
            self._cmb_replay_speed.addItem(s)
        self._cmb_replay_speed.setCurrentText("1×")
        self._cmb_replay_speed.currentTextChanged.connect(self._on_replay_speed_changed)
        self._replay_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._replay_slider.setMinimum(0)
        self._replay_slider.setMaximum(0)
        self._replay_slider.valueChanged.connect(self._on_replay_seek)
        self._lbl_replay_pos = QtWidgets.QLabel("0/0")
        replay_lay.addWidget(self._btn_replay_play)
        replay_lay.addWidget(self._btn_replay_step_back)
        replay_lay.addWidget(self._btn_replay_step_fwd)
        replay_lay.addWidget(QtWidgets.QLabel("Speed:"))
        replay_lay.addWidget(self._cmb_replay_speed)
        replay_lay.addWidget(self._replay_slider, 1)
        replay_lay.addWidget(self._lbl_replay_pos)
        self._replay_bar.hide()
        col.addWidget(self._replay_bar)

        bar = QtWidgets.QHBoxLayout()
        btn_clear = QtWidgets.QPushButton("CLEAR TRAIL")
        btn_clear.clicked.connect(self._clear_trail)
        self._lbl_ptcount = QtWidgets.QLabel("points: 0")
        bar.addWidget(btn_clear)
        bar.addWidget(self._lbl_ptcount)
        bar.addStretch(1)
        col.addLayout(bar)
        col.addLayout(grid, 1)
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
        self.txt_ws_host.setText(s.value("ws/host", CMD_AP_FALLBACK_IP))
        self._wifi_ssid_cached = s.value("wifi/ssid", "")
        self._wifi_pass_cached = s.value("wifi/pass", "")
        mode = s.value("mode", "serial")
        if mode == "tcp":
            self.rb_tcp.setChecked(True)
        elif mode == "ws":
            self.rb_ws.setChecked(True)
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
        s.setValue("ws/host", self.txt_ws_host.text())
        if self._wifi_window is not None:
            s.setValue("wifi/ssid", self._wifi_window.ssid())
            s.setValue("wifi/pass", self._wifi_window.password())
        else:
            s.setValue("wifi/ssid", self._wifi_ssid_cached)
            s.setValue("wifi/pass", self._wifi_pass_cached)
        s.setValue("replay/path", self.txt_replay.text())
        if self.rb_replay.isChecked():
            s.setValue("mode", "replay")
        elif self.rb_ws.isChecked():
            s.setValue("mode", "ws")
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
        elif initial.get("mode") == "ws":
            self.rb_ws.setChecked(True)
            if initial.get("host"):
                self.txt_ws_host.setText(initial["host"])
        elif initial.get("mode") == "replay":
            self.rb_replay.setChecked(True)
            if initial.get("replay_file"):
                self.txt_replay.setText(initial["replay_file"])
        self._sync_conn_fields()

    def _sync_conn_fields(self) -> None:
        serial_mode = self.rb_serial.isChecked()
        tcp_mode = self.rb_tcp.isChecked()
        ws_mode = self.rb_ws.isChecked()
        replay_mode = self.rb_replay.isChecked()
        self.cmb_port.setEnabled(serial_mode)
        self.txt_baud.setEnabled(serial_mode)
        self.txt_ip.setEnabled(tcp_mode)
        self.txt_tcp_port.setEnabled(tcp_mode)
        self.txt_ws_host.setEnabled(ws_mode)
        self.txt_replay.setEnabled(replay_mode)
        remote_group = getattr(self, "_remote_group", None)
        if remote_group is not None:
            remote_group.setEnabled(tcp_mode or ws_mode or serial_mode)
        if hasattr(self, "_act_wifi"):
            self._act_wifi.setEnabled(tcp_mode or ws_mode)

    # ------------------------------------------------------------ transport
    def _connect(self, *, silent: bool = False) -> None:
        """Connect using the current panel settings.

        ``silent`` is set by the auto-reconnect timer: failures then feed the
        backoff instead of popping a modal dialog in the operator's face.
        """
        if self._transport is not None or getattr(self, "_is_replay", False):
            return

        def fail(msg: str) -> None:
            if silent:
                self._schedule_reconnect(msg)
            else:
                self._warn(msg)

        if self.rb_replay.isChecked():
            path = self.txt_replay.text().strip()
            if not path:
                fail("Select a replay CSV file.")
                return
            frames = load_replay_frames(path)
            if not frames:
                fail(f"No frames in: {path}")
                return
            self._replay_frames = frames
            self._replay_idx = 0
            self._is_replay = True
            self._is_serial = False
            self._is_ws = False
            self._replay_paused = False
            self._replay_timer = QtCore.QTimer(self, interval=interval_for_speed(self._replay_speed))
            self._replay_timer.timeout.connect(self._replay_tick)
            self._replay_timer.start()
            self._replay_slider.setMaximum(max(0, len(frames) - 1))
            self._replay_slider.setValue(0)
            self._lbl_replay_pos.setText(f"0/{len(frames)}")
            self._replay_bar.show()
            self._btn_replay_play.setText("Pause")
            self._save_settings()
            self._set_connected(True)
            self._set_status(f"Replay: {Path(path).name}", "#00ff88")
            return

        if self.rb_serial.isChecked():
            port = self.cmb_port.currentText().strip()
            if not port:
                fail("No serial port selected.")
                return
            try:
                baud = int(self.txt_baud.text())
            except ValueError:
                fail("Invalid baud rate.")
                return
            tr = SerialLineReader()
            tr.set_callbacks(on_line=self._push_line, on_disconnect=self._push_disconnect)
            ok, info = tr.connect(port, baud)
            self._is_serial = True
            self._is_replay = False
            self._is_ws = False
        elif self.rb_ws.isChecked():
            tr = WsClient()
            tr.set_callbacks(on_line=self._push_line, on_disconnect=self._push_disconnect)
            ok, info = tr.connect(self.txt_ws_host.text().strip(), CMD_DEFAULT_WS_PORT)
            self._is_serial = False
            self._is_replay = False
            self._is_ws = True
        else:
            try:
                port = int(self.txt_tcp_port.text())
            except ValueError:
                fail("Invalid TCP port.")
                return
            tr = TcpClient()
            tr.set_callbacks(on_line=self._push_line, on_disconnect=self._push_disconnect)
            ok, info = tr.connect(self.txt_ip.text().strip(), port)
            self._is_serial = False
            self._is_replay = False
            self._is_ws = False

        if not ok:
            fail(f"Connection failed: {info}")
            return
        self._transport = tr
        self._cancel_reconnect()
        self._save_settings()
        self._set_connected(True)
        self._set_status("Connected.", "#00ff88")
        self._connected_at = time.monotonic()
        if not self._is_replay:
            self._send("CONSTANTS")
            if not self._is_serial:
                self._send("GET_IP")
                self._send("SYSINFO")
                self._send("STATUS")
                self._sysinfo_timer.start()

    @staticmethod
    def _format_data_line(frame) -> str:
        return format_data_line(
            frame.x_mm, frame.y_mm, frame.z_mm,
            frame.r_mm, frame.theta_deg, frame.phi_deg,
            frame.is_valid, frame.frame_count, frame.ts_ms,
        )

    def _replay_tick(self) -> None:
        if self._replay_paused:
            return
        if self._replay_idx >= len(self._replay_frames):
            self._replay_timer.stop()
            self._set_status("Replay finished.", "#888")
            return
        frame = self._replay_frames[self._replay_idx]
        self._push_line(self._format_data_line(frame))
        self._replay_idx += 1
        self._replay_slider.blockSignals(True)
        self._replay_slider.setValue(self._replay_idx)
        self._replay_slider.blockSignals(False)
        self._lbl_replay_pos.setText(f"{self._replay_idx}/{len(self._replay_frames)}")

    def _toggle_replay_pause(self) -> None:
        if not self._is_replay:
            return
        self._replay_paused = not self._replay_paused
        self._btn_replay_play.setText("Play" if self._replay_paused else "Pause")
        if not self._replay_paused and hasattr(self, "_replay_timer"):
            self._replay_timer.start()

    def _on_replay_speed_changed(self, text: str) -> None:
        mult = float(text.replace("×", ""))
        self._replay_speed = mult
        if hasattr(self, "_replay_timer") and self._replay_timer.isActive():
            self._replay_timer.setInterval(interval_for_speed(mult))

    def _replay_step(self, delta: int) -> None:
        if not self._is_replay:
            return
        was_paused = self._replay_paused
        self._replay_paused = True
        target = max(0, min(self._replay_idx + delta, len(self._replay_frames)))
        self._replay_seek(target)
        self._replay_paused = was_paused

    def _on_replay_seek(self, idx: int) -> None:
        if not self._is_replay:
            return
        self._replay_seek(idx)

    def _replay_seek(self, target_idx: int) -> None:
        if not self._replay_frames:
            return
        target_idx = max(0, min(target_idx, len(self._replay_frames)))
        self._replay_idx = 0
        self._trail.clear()
        self._display.reset_minmax()
        self._has_xyz = False
        for i in range(target_idx):
            frame = self._replay_frames[i]
            self._push_line(self._format_data_line(frame))
            self._drain()
        self._replay_idx = target_idx
        self._replay_slider.blockSignals(True)
        self._replay_slider.setValue(target_idx)
        self._replay_slider.blockSignals(False)
        self._lbl_replay_pos.setText(f"{target_idx}/{len(self._replay_frames)}")

    # -------------------------------------------------------- auto-reconnect
    def _cancel_reconnect(self) -> None:
        """Stop any pending retry and reset the backoff to its first step."""
        self._reconnect_timer.stop()
        self._reconnect_delay = 0.0
        self._reconnect_attempts = 0
        self.btn_disconnect.setText("Disconnect")

    def _schedule_reconnect(self, reason: str) -> None:
        self._reconnect_delay = next_backoff(self._reconnect_delay)
        self._reconnect_attempts += 1
        self._reconnect_timer.start(int(self._reconnect_delay * 1000))
        # The Disconnect button doubles as the escape hatch while we retry.
        self.btn_disconnect.setEnabled(True)
        self.btn_disconnect.setText("Cancel")
        self._set_status(
            f"{reason} — reconnecting in {self._reconnect_delay:.0f}s "
            f"(attempt {self._reconnect_attempts})",
            "#ffd700",
        )

    def _reconnect_attempt(self) -> None:
        self._set_status(f"Reconnecting (attempt {self._reconnect_attempts})…", "#ffd700")
        self._connect(silent=True)

    def _on_link_lost(self, reason: str) -> None:
        """Unexpected drop: tear down, then retry with backoff.

        Replay is not a link, so it just stops.
        """
        was_replay = self._is_replay
        self._teardown(reset_backoff=False)
        if was_replay:
            self._set_status(f"Disconnected: {reason}", "#ff4444")
            self._cancel_reconnect()
            return
        self._schedule_reconnect(f"Lost link ({reason})")

    def _disconnect(self) -> None:
        """User-initiated disconnect — also cancels any retry in flight."""
        self._teardown(reset_backoff=True)
        self._set_status("Disconnected.", "#ff4444")

    def _teardown(self, *, reset_backoff: bool) -> None:
        if reset_backoff:
            self._cancel_reconnect()
        if hasattr(self, "_replay_timer") and self._replay_timer.isActive():
            self._replay_timer.stop()
        self._replay_frames = []
        self._replay_idx = 0
        self._is_replay = False
        self._is_ws = False
        self._replay_bar.hide()
        self._sysinfo_timer.stop()
        self._connected_at = None
        if self._transport is not None:
            self._transport.close(emit_disconnect=False)
            self._transport = None
        self._reset_ui()
        self._set_connected(False)
        # Caller sets the status line: _disconnect says "Disconnected",
        # _on_link_lost says "reconnecting in Ns".

    def _reset_ui(self) -> None:
        self._clear_pending_cmd()
        self._state.reset()
        self._display.reset_session_state()
        self._has_xyz = False
        self._saved_point_rows.clear()
        self._snapshots.clear()
        self._snapshot_idx = 0
        self._constants_line = ""
        self._raw_counts_line = ""
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
        self._lbl_sysinfo.setText("RSSI — · Heap — · Uptime — · TCP —")
        self._lbl_constants.setText("PPR —")
        self._lbl_raw_counts.setText("Raw counts —")
        if self._wifi_window is not None:
            self._wifi_window.set_router_ip("Router IP: —")
        self._update_sw_zero_badge()

    def _set_connected(self, connected: bool) -> None:
        self.btn_connect.setEnabled(not connected)
        self.btn_disconnect.setEnabled(connected)
        self.btn_blink.setEnabled(connected and not self._is_replay)
        self.rb_serial.setEnabled(not connected)
        self.rb_tcp.setEnabled(not connected)
        self.rb_ws.setEnabled(not connected)
        self.rb_replay.setEnabled(not connected)
        for b in self._cmd_buttons:
            b.setEnabled(connected and not self._is_replay)
        for b in (self.btn_swzero, self.btn_swclear, self.btn_reset_mm, self.btn_origin, self.btn_clear_origin):
            b.setEnabled(connected)
        for b in (self.btn_save_pt, self.btn_del_pt, self.btn_hwzero):
            b.setEnabled(connected and not self._is_replay)
        if self._cal_window is not None:
            self._cal_window.set_connected(
                connected and not self._is_replay, refresh=False,
            )
        self._ipt_panel.set_connected(connected)
        if self._wifi_window is not None:
            self._wifi_window.set_controls_enabled(
                connected and not self._is_replay and not self._is_serial)
        if hasattr(self, "_act_wifi"):
            self._act_wifi.setEnabled(self.rb_tcp.isChecked() or self.rb_ws.isChecked())

    def _push_line(self, line: str) -> None:
        self._queue.put(("line", line))

    def _push_disconnect(self, reason: str) -> None:
        self._queue.put(("disconnect", reason))

    def _send(self, cmd: str) -> bool:
        if self._transport is None:
            self._warn("Not connected.")
            return False
        command = cmd.strip().upper()
        if command.startswith("CAL_W ") and any(
            pending.startswith("CAL_W ") for pending, _ in self._pending_commands
        ):
            self._set_status("CAL_W already waiting for a reply.", "#ffd700")
            return False
        ok, info = self._transport.send_command(cmd)
        if not ok:
            self._warn(f"Send failed: {info}")
            return False
        self._pending_commands.append((command, time.monotonic()))
        self._set_status(f"Sent {command}, waiting…", "#888888")
        return True

    def _clear_pending_cmd(self) -> None:
        self._pending_commands.clear()

    def _complete_pending_response(self, line: str) -> Optional[str]:
        if not self._pending_commands:
            return None
        index = None
        for i, (command, _) in enumerate(self._pending_commands):
            if command_response_matches(command, line):
                index = i
                break
        if index is None:
            return None
        command, _ = self._pending_commands.pop(index)
        return command

    def _check_cmd_timeout(self) -> None:
        if not self._pending_commands:
            return
        now = time.monotonic()
        expired = [
            command for command, sent_at in self._pending_commands
            if now - sent_at >= CMD_RESPONSE_TIMEOUT_S
        ]
        if not expired:
            return
        self._pending_commands = [
            item for item in self._pending_commands
            if now - item[1] < CMD_RESPONSE_TIMEOUT_S
        ]
        if self._cal_window is not None:
            for command in expired:
                self._cal_window.handle_timeout(command)
        self._set_status(
            f"No response to {', '.join(expired)} (timeout)", "#ff4444",
        )

    def _poll_battery(self) -> None:
        if self._transport is not None:
            self._transport.send_command("STATUS")

    def _poll_sysinfo(self) -> None:
        if self._transport is not None and not self._is_serial:
            self._transport.send_command("SYSINFO")
            self._transport.send_command("GET_IP")

    def _check_hb_stale(self) -> None:
        if self._state.last_hb is not None and time.monotonic() - self._state.last_hb > HB_STALE_S:
            self._lbl_hb.setStyleSheet("color:#ff4444;")
        if (self._transport is not None and not self._state.battery_seen
                and self._connected_at is not None
                and time.monotonic() - self._connected_at > 10):
            self._lbl_batt_v.setText("Voltage: N/A (no data)")
            self._lbl_batt_pct.setText("Reflash firmware for BATT support")

    # -------------------------------------------------------------- record
    def _toggle_record(self, on: bool) -> None:
        if on:
            default = default_export_path(f"evka_session_{datetime.now():%Y%m%d_%H%M%S}.csv")
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Record session to…", default, "CSV / DATA dump (*.csv)"
            )
            if not path:
                self._act_record.setChecked(False)   # user cancelled the dialog
                return
            try:
                self._rec_file = open(path, "w", encoding="utf-8", newline="\n")
            except OSError as exc:
                self._act_record.setChecked(False)
                self._warn(f"Cannot record to {path}: {exc}")
                return
            self._rec_count = 0
            self._rec_xyz = None
            self._rec_t0 = time.monotonic()
            self._set_status(f"REC → {Path(path).name}", "#ff4444")
        else:
            if self._rec_file is None:
                return
            try:
                self._rec_file.close()
            except OSError as exc:
                self._rec_file = None
                self._rec_xyz = None
                self._set_status(f"Recording stopped: {exc}", "#ff4444")
                return
            self._rec_file = None
            self._rec_xyz = None
            self._set_status(f"Recording stopped — {self._rec_count} frames.", "#00ff88")

    def _record_line(self, line: str) -> None:
        """Tap the wire and write it as replayable ``DATA,`` lines.

        Serial and WebSocket already send ``DATA,`` — pass it through untouched. TCP
        sends ``X..,Y..,Z..`` followed by ``SENSOR,`` instead, so pair the two and
        re-serialise. Either way the file is raw sensor-frame (never software-zeroed)
        and ``load_replay_frames`` reads it back directly.
        """
        if line.startswith(DATA_PREFIX):
            self._rec_write(line)
            return
        xyz = parse_xyz_line(line)
        if xyz is not None:
            self._rec_xyz = (xyz.x_mm, xyz.y_mm, xyz.z_mm)
            return
        sensor = parse_sensor_line(line)
        if sensor is not None and self._rec_xyz is not None:
            x, y, z = self._rec_xyz
            self._rec_write(format_data_line(
                x, y, z,
                sensor.r_mm, sensor.theta_deg, sensor.phi_deg,
                sensor.is_valid, sensor.frame_count,
                int((time.monotonic() - self._rec_t0) * 1000),
            ))
            self._rec_xyz = None

    def _rec_write(self, line: str) -> None:
        try:
            self._rec_file.write(line + "\n")
        except OSError as exc:
            rec_file = self._rec_file
            self._rec_file = None
            self._rec_xyz = None
            try:
                rec_file.close()
            except OSError:
                pass
            self._act_record.blockSignals(True)
            self._act_record.setChecked(False)
            self._act_record.blockSignals(False)
            self._set_status(f"Recording stopped: {exc}", "#ff4444")
            return
        self._rec_count += 1
        if self._rec_count % 100 == 0:
            self._set_status(f"REC — {self._rec_count} frames", "#ff4444")

    # -------------------------------------------------------------- freeze
    def _set_frozen(self, frozen: bool) -> None:
        """Pause/resume ingestion of the position stream. The link stays up."""
        frozen = bool(frozen)
        if frozen == self._frozen:
            return
        self._frozen = frozen
        if self._act_freeze.isChecked() != frozen:
            self._act_freeze.setChecked(frozen)   # keep the toolbar in sync
        if frozen:
            self._set_status("FROZEN — stream paused, link still up.", "#ffd700")
        else:
            self._set_status("Live.", "#00ff88")

    # -------------------------------------------------------------- drain
    def _drain(self) -> None:
        while True:
            try:
                kind, payload = self._queue.get_nowait()
            except queue.Empty:
                break
            if kind == "disconnect":
                # A disconnect event with no transport is an echo of a close that
                # already happened (e.g. the reader thread winding down after the
                # user hit Disconnect). Acting on it would auto-reconnect against
                # the user's explicit wish.
                if self._transport is not None or self._is_replay:
                    self._on_link_lost(str(payload))
                    return
                continue
            # The raw log always sees the wire, frozen or not — it has its own Pause.
            if self._protocol_log is not None:
                self._protocol_log.append_line(payload)
            # Recording taps the wire; FREEZE only pauses the view. Freezing must
            # never punch a silent hole in a recording.
            if self._rec_file is not None:
                self._record_line(payload)
            if self._frozen and is_frame_line(payload):
                continue          # FREEZE stops the stream, not command replies
            if self._ipt_panel is not None:
                self._ipt_panel.feed_line(payload)
            replied_cmd = self._complete_pending_response(payload)
            for up in ingest_line(payload):
                self._apply(up, replied_cmd)

    def _apply(self, up, replied_cmd: Optional[str] = None) -> None:
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
            self._on_ack(d, replied_cmd)
        elif k == "err":
            self._on_err(d, replied_cmd)
        elif k == "sysinfo":
            self._on_sysinfo(d)
        elif k == "sta_ip":
            self._on_sta_ip(d)
        elif k == "cal":
            if self._cal_window is not None:
                self._cal_window.handle_cal(d, replied_cmd)
        elif k == "constants":
            self._on_constants(d)
            if self._cal_window is not None:
                self._cal_window.handle_constants(d)
        elif k == "raw_counts":
            self._on_raw_counts(d)

    def _on_constants(self, line: str) -> None:
        self._constants_line = line
        self._lbl_constants.setText(format_constants_strip(line))

    def _on_raw_counts(self, line: str) -> None:
        self._raw_counts_line = line
        self._lbl_raw_counts.setText(format_raw_counts_line(line))

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
            # Raw sensor frame, never pos.* — a software zero would otherwise bake its
            # offset into the calibration fit (Kabsch hides it in t) and the deployed
            # transform would only be valid while that same zero is active.
            self._cal_window.handle_position(x, y, z)

    def _on_sensor(self, r, theta, phi, valid, frame) -> None:
        self._state.is_valid = bool(valid)
        if not self._display.relative_zero_active:
            self._lbl_r.setText(f"R {r:.2f}")
            self._lbl_theta.setText(f"θ {theta:.2f}")
            self._lbl_phi.setText(f"φ {phi:.2f}")
        process_sensor_line(self._display, r, theta, phi, valid, frame)
        self._lbl_valid.setText(f"valid: {'YES' if valid else 'NO'}")
        style = "color:#00ff88;" if valid else "color:#ff4444;"
        self._lbl_valid.setStyleSheet(style)
        if not valid:
            self._set_status("Invalid position", "#ff4444")
        self._lbl_frame.setText(f"frame: {frame}")
        self._update_axis_styles()

    def _on_batt(self, batt) -> None:
        self._state.battery_seen = True
        self._lbl_batt_v.setText(f"Voltage: {batt.voltage:.3f} V")
        self._lbl_batt_pct.setText(f"Charge: {batt.pct} %")
        if batt.is_low:
            self._lbl_batt_low.setText("LOW BATTERY")
            self._grp_batt.setStyleSheet("QGroupBox { border:1px solid #ff4444; }")
            self._set_status("Low battery", "#ff4444")
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
        self._lbl_hb.setStyleSheet("color:#00ff88;")

    def _on_point(self, line: str) -> None:
        parts = line[len(POINT_PREFIX):].split(",")
        if len(parts) >= 4:
            try:
                idx, wx, wy, wz = parts[0], float(parts[1]), float(parts[2]), float(parts[3])
            except ValueError:
                return
            self._saved_point_rows.append((idx, wx, wy, wz))
            item = QtWidgets.QListWidgetItem(self._display.format_point_entry(idx, wx, wy, wz))
            item.setData(QtCore.Qt.UserRole, (idx, wx, wy, wz))
            self._pts_list.addItem(item)
            self._state.saved_points += 1
            self._update_distance_labels()

    def _on_del_point(self, line: str) -> None:
        if self._pts_list.count():
            self._pts_list.takeItem(self._pts_list.count() - 1)
        if self._saved_point_rows:
            self._saved_point_rows.pop()
        self._state.saved_points = max(0, self._state.saved_points - 1)
        self._update_distance_labels()

    def _on_ack(self, line: str, replied_cmd: Optional[str] = None) -> None:
        if line.startswith(("ACK:PPR_", "ACK:SAVE_PPR")) and replied_cmd is None:
            self._set_status(f"Unexpected reply: {line}", "#ffd700")
        else:
            self._set_status(line, "#00ff88")
        if self._cal_window is not None:
            self._cal_window.handle_reply(line, replied_cmd)
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

    def _on_err(self, line: str, replied_cmd: Optional[str] = None) -> None:
        if self._cal_window is not None:
            self._cal_window.handle_reply(line, replied_cmd)
        if replied_cmd == "BLINK" and line == "ERR:UNKNOWN_CMD":
            self._set_status("ERR:UNKNOWN_CMD — reflash firmware for BLINK support", "#ff4444")
        elif line == "ERR:NO_POINTS":
            QtWidgets.QMessageBox.information(self, "Delete Point", "No saved points on device.")
        elif "WIFI" in line and self._wifi_pending:
            self._wifi_pending = None
            QtWidgets.QMessageBox.critical(self, "WiFi Error", line)
        else:
            self._set_status(line, "#ff4444")

    def _on_sysinfo(self, si: SysInfo) -> None:
        rssi = f"{si.rssi} dBm" if si.rssi != 0 else "n/a"
        h, m, s = si.uptime_s // 3600, (si.uptime_s % 3600) // 60, si.uptime_s % 60
        heap_kb = si.heap // 1024
        self._lbl_sysinfo.setText(
            f"RSSI {rssi} · Heap {heap_kb} KB · "
            f"Up {h:02d}:{m:02d}:{s:02d} · TCP {si.tcp_clients}"
        )
        if heap_kb < 40:
            self._lbl_sysinfo.setStyleSheet("color:#ff4444; font-size:10px; font-family:Consolas;")
        else:
            self._lbl_sysinfo.setStyleSheet("color:#666; font-size:10px; font-family:Consolas;")

    def _on_sta_ip(self, ip: str) -> None:
        self._sta_ip_cached = ip.strip()
        text = f"Router IP: {sta_ip_display(ip)}"
        if self._wifi_window is not None:
            self._wifi_window.set_router_ip(text)
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
        self._refresh_saved_point_labels()

    def _software_zero_all(self) -> None:
        self._activate_sw_zero(
            ox=self._display.last_raw_x,
            oy=self._display.last_raw_y,
            oz=self._display.last_raw_z,
        )
        self._refresh_saved_point_labels()
        self._set_status("Software zero applied.", "#00ff88")

    def _software_zero_clear(self) -> None:
        self._display.clear_software_zero()
        self._trail.clear()
        self._update_sw_zero_badge()
        self._refresh_display_from_raw()
        self._refresh_saved_point_labels()
        self._set_status("Software zero cleared.", "#eeeeff")

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

    def _refresh_saved_point_labels(self) -> None:
        for i in range(self._pts_list.count()):
            item = self._pts_list.item(i)
            data = item.data(QtCore.Qt.UserRole)
            if data is None:
                continue
            idx, wx, wy, wz = data
            item.setText(self._display.format_point_entry(str(idx), wx, wy, wz))

    def _copy_axis(self, axis: str) -> None:
        if not self._has_xyz:
            return
        val = getattr(self._display, f"last_raw_{axis}")
        off = getattr(self._display, f"offset_{axis}")
        disp = val - off if self._display.relative_zero_active else val
        QtWidgets.QApplication.clipboard().setText(f"{disp:.3f}")

    def _copy_spherical(self) -> None:
        text = f"{self._lbl_r.text()}, {self._lbl_theta.text()}, {self._lbl_phi.text()}"
        QtWidgets.QApplication.clipboard().setText(text)

    def _on_layer_toggle(self) -> None:
        self._show_trail = self._chk_trail.isChecked()
        self._show_ipt = self._chk_ipt.isChecked()
        self._show_origin = self._chk_origin.isChecked()
        self._show_saved_pts = self._chk_saved.isChecked()
        self._refresh_views()

    def _on_trail_max_changed(self, value: int) -> None:
        self._trail_max = value
        pts = self._trail.points()
        self._trail = TrailBuffer(value)
        self._state.trail = self._trail
        for x, y, z in pts[-value:]:
            self._trail.add(x, y, z)

    def _capture_snapshot(self) -> None:
        if not self._has_xyz:
            self._warn("No position data yet.")
            return
        x, y, z = self._raw_position()
        self._snapshot_idx += 1
        self._snapshots.append(format_snapshot_row(self._snapshot_idx, x, y, z))
        self._set_status(f"Snapshot #{self._snapshot_idx} captured.", "#00ff88")

    def _add_ipt_snapshot(self, x: float, y: float, z: float) -> None:
        self._snapshot_idx += 1
        self._snapshots.append(format_snapshot_row(self._snapshot_idx, x, y, z))

    def _clear_snapshots(self) -> None:
        self._snapshots.clear()
        self._snapshot_idx = 0
        self._set_status("Snapshots cleared.", "#888")

    def _export_snapshots(self) -> None:
        if not self._snapshots:
            self._warn("No snapshots to export.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export snapshots",
            default_export_path(f"evka_snapshots_{int(time.time())}.csv"), "CSV (*.csv)"
        )
        if not path:
            return
        n = write_snapshots_csv(path, self._snapshots)
        self._set_status(f"Exported {n} snapshots.", "#00ff88")

    def _export_saved_points(self) -> None:
        if not self._saved_point_rows:
            self._warn("No saved points to export.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export saved points",
            default_export_path(f"evka_points_{int(time.time())}.csv"), "CSV (*.csv)"
        )
        if not path:
            return
        n = write_saved_points_csv(path, self._saved_point_rows, self._origin)
        self._set_status(f"Exported {n} saved points.", "#00ff88")

    def _open_dashboard(self) -> None:
        if self._sta_ip_cached and sta_ip_is_connected(self._sta_ip_cached):
            host = self._sta_ip_cached
        elif self.rb_ws.isChecked():
            host = self.txt_ws_host.text().strip()
        elif self.rb_tcp.isChecked():
            host = self.txt_ip.text().strip()
        else:
            host = CMD_AP_FALLBACK_IP
        webbrowser.open(f"http://{host}")

    def _open_remote_tester(self) -> None:
        if self._remote_window is None:
            self._remote_window = RemoteTesterWindow(parent=self)
            self._remote_window.destroyed.connect(
                lambda: setattr(self, "_remote_window", None))
        self._remote_window.show()
        self._remote_window.raise_()

    def _refresh_profile_combo(self) -> None:
        cur = self.cmb_profile.currentText()
        self.cmb_profile.clear()
        self.cmb_profile.addItem("(none)")
        for name in list_profiles(self._settings):
            self.cmb_profile.addItem(name)
        idx = self.cmb_profile.findText(cur)
        if idx >= 0:
            self.cmb_profile.setCurrentIndex(idx)

    def _connection_profile_data(self) -> dict:
        mode = "serial"
        if self.rb_tcp.isChecked():
            mode = "tcp"
        elif self.rb_ws.isChecked():
            mode = "ws"
        elif self.rb_replay.isChecked():
            mode = "replay"
        return {
            "mode": mode,
            "serial_port": self.cmb_port.currentText(),
            "serial_baud": self.txt_baud.text(),
            "tcp_ip": self.txt_ip.text(),
            "tcp_port": self.txt_tcp_port.text(),
            "ws_host": self.txt_ws_host.text(),
            "replay_path": self.txt_replay.text(),
        }

    def _save_connection_profile(self) -> None:
        name, ok = QtWidgets.QInputDialog.getText(self, "Save profile", "Profile name:")
        if not ok or not name.strip():
            return
        save_profile(self._settings, name.strip(), self._connection_profile_data())
        self._refresh_profile_combo()
        self.cmb_profile.setCurrentText(name.strip())

    def _load_connection_profile(self) -> None:
        name = self.cmb_profile.currentText()
        if name == "(none)":
            return
        data = load_profile(self._settings, name)
        if not data:
            self._warn(f"Profile '{name}' not found.")
            return
        mode = data.get("mode", "serial")
        if mode == "tcp":
            self.rb_tcp.setChecked(True)
        elif mode == "ws":
            self.rb_ws.setChecked(True)
        elif mode == "replay":
            self.rb_replay.setChecked(True)
        else:
            self.rb_serial.setChecked(True)
        if data.get("serial_port"):
            self.cmb_port.setCurrentText(data["serial_port"])
        if data.get("serial_baud"):
            self.txt_baud.setText(data["serial_baud"])
        if data.get("tcp_ip"):
            self.txt_ip.setText(data["tcp_ip"])
        if data.get("tcp_port"):
            self.txt_tcp_port.setText(data["tcp_port"])
        if data.get("ws_host"):
            self.txt_ws_host.setText(data["ws_host"])
        if data.get("replay_path"):
            self.txt_replay.setText(data["replay_path"])
        self._sync_conn_fields()

    def _delete_connection_profile(self) -> None:
        name = self.cmb_profile.currentText()
        if name == "(none)":
            return
        delete_profile(self._settings, name)
        self._refresh_profile_combo()

    def _save_wifi(self) -> None:
        w = self._wifi_window
        if w is None:
            return
        ssid = w.ssid()
        password = w.password()
        if not ssid:
            self._warn("SSID required.")
            return
        if password and len(password) < 8:
            self._warn("Password must be empty or ≥8 characters.")
            return
        self._wifi_ssid_cached = ssid
        self._wifi_pass_cached = password
        self._wifi_pending = "save"
        self._send(f"WIFI_SET:{ssid},{password}")

    def _forget_wifi(self) -> None:
        if QtWidgets.QMessageBox.question(
            self, "Forget WiFi", "Erase stored credentials and reboot?"
        ) != QtWidgets.QMessageBox.Yes:
            return
        self._wifi_pending = "forget"
        self._send("WIFI_SET:,")

    def _open_wifi(self) -> None:
        if not (self.rb_tcp.isChecked() or self.rb_ws.isChecked()):
            QtWidgets.QMessageBox.information(
                self, "WiFi Settings", "WiFi credentials apply in TCP or WebSocket mode only.")
            return
        if self._wifi_window is None:
            self._wifi_window = WifiSettingsWindow(
                self._save_wifi,
                self._forget_wifi,
                ssid=self._wifi_ssid_cached,
                password=self._wifi_pass_cached,
                parent=self,
            )
            self._wifi_window.destroyed.connect(
                lambda: setattr(self, "_wifi_window", None))
        self._wifi_window.set_controls_enabled(
            self._transport is not None and not self._is_replay and not self._is_serial)
        self._wifi_window.show()
        self._wifi_window.raise_()

    def _open_calibration(self) -> None:
        if self._cal_window is None:
            self._cal_window = CalibrationWindow(self._send_for_cal, self)
            self._cal_window.destroyed.connect(lambda: setattr(self, "_cal_window", None))
        self._cal_window.set_connected(self._transport is not None and not self._is_replay)
        self._cal_window.show()
        self._cal_window.raise_()

    def _open_ipt_plots(self) -> None:
        if self._transport is None and not self._is_replay:
            QtWidgets.QMessageBox.warning(
                self, "IPT plots", "Connect to device first.")
            return
        if self._ipt_plots_window is None:
            self._ipt_plots_window = IptPlotsWindow(self._ipt_panel, self)
            self._ipt_plots_window.destroyed.connect(
                lambda: setattr(self, "_ipt_plots_window", None))
        self._ipt_plots_window.show()
        self._ipt_plots_window.raise_()

    def _send_for_cal(self, cmd: str) -> bool:
        if self._transport is None or self._is_replay:
            QtWidgets.QMessageBox.warning(self, "Calibration", "Connect to device first.")
            return False
        return self._send(cmd)

    def _export_session(self) -> None:
        if not self._saved_point_rows:
            self._warn("No saved points to export.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export session",
            default_export_path(f"evka_session_{int(time.time())}.csv"), "CSV (*.csv)"
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
        self._set_status(f"Exported {len(self._saved_point_rows)} points.", "#00ff88")

    def _clear_trail(self) -> None:
        self._trail.clear()

    def _refresh_views(self) -> None:
        xs, ys, zs = self._trail.xs(), self._trail.ys(), self._trail.zs()
        if self._show_trail:
            self._view3d.set_show_trail(True)
            self._view3d.set_data(xs, ys, zs)
        else:
            self._view3d.set_show_trail(False)
            self._view3d.set_data([], [], [])
        n = len(xs) if self._show_trail else 0
        for (_, trail, head), (a, b) in (
            (self._xy, (xs, ys)),
            (self._xz, (xs, zs)),
            (self._yz, (ys, zs)),
        ):
            if self._show_trail:
                trail.setData(a, b)
                if n:
                    head.setData([a[-1]], [b[-1]])
                else:
                    head.setData([], [])
            else:
                trail.setData([], [])
                head.setData([], [])
        self._lbl_ptcount.setText(f"points: {n}")
        self._refresh_reference_overlays()
        self._refresh_ipt_overlays()
        self._refresh_3d_ipt()

    def _display_xyz(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        if self._display.relative_zero_active:
            return self._display.apply_offsets(x, y, z)
        return x, y, z

    def _refresh_reference_overlays(self) -> None:
        origin = self._display_xyz(*self._origin) if self._origin is not None else None
        saved = [self._display_xyz(x, y, z) for _, x, y, z in self._saved_point_rows]
        plot_values = {
            "xy": ((origin[0], origin[1]) if origin else None,
                   ([p[0] for p in saved], [p[1] for p in saved])),
            "xz": ((origin[0], origin[2]) if origin else None,
                   ([p[0] for p in saved], [p[2] for p in saved])),
            "yz": ((origin[1], origin[2]) if origin else None,
                   ([p[1] for p in saved], [p[2] for p in saved])),
        }
        for key, (origin_xy, saved_xy) in plot_values.items():
            if self._show_origin and origin_xy:
                self._origin_marker[key].setData(x=[origin_xy[0]], y=[origin_xy[1]])
            else:
                self._origin_marker[key].setData(x=[], y=[])
            if self._show_saved_pts and saved:
                self._saved_markers[key].setData(x=saved_xy[0], y=saved_xy[1])
            else:
                self._saved_markers[key].setData(x=[], y=[])

    def _refresh_3d_ipt(self) -> None:
        panel = self._ipt_panel
        if not self._show_ipt or not panel.show_overlay():
            self._view3d.set_ipt_overlay(None, None, None, 0.0, False)
            return
        sol = panel.last_solution
        marker = sol["P"] if sol and sol.get("ok") else None
        center = sol["P"] if sol and sol.get("ok") else None
        radius = sol.get("L_hat", 0.0) if sol and sol.get("ok") else 0.0
        self._view3d.set_ipt_overlay(
            panel.points(), marker, center, radius, True)

    def _refresh_ipt_overlays(self) -> None:
        panel = self._ipt_panel
        plot_map = {"xy": self._xy, "xz": self._xz, "yz": self._yz}

        if not self._show_ipt or not panel.show_overlay():
            for key in self._ipt_cloud:
                self._ipt_cloud[key].setData(x=[], y=[])
                self._ipt_marker[key].setData(x=[], y=[])
            for key, items in self._ipt_sphere.items():
                pw = plot_map[key][0]
                for item in items:
                    pw.removeItem(item)
                items.clear()
            return

        projections = ipt_projections(panel.points())
        for key, (pxs, pys) in projections.items():
            self._ipt_cloud[key].setData(
                x=pxs, y=pys, symbol="o", symbolSize=5,
                symbolBrush=self._pg.mkBrush("#00ff88"), symbolPen=None)

        for key, items in self._ipt_sphere.items():
            pw = plot_map[key][0]
            for item in items:
                pw.removeItem(item)
            items.clear()

        sol = panel.last_solution
        if sol and sol.get("ok"):
            p = sol["P"]
            for key, (mx, my) in ipt_marker_coords(p).items():
                self._ipt_marker[key].setData(
                    x=[mx], y=[my], symbol="o", symbolSize=12,
                    symbolBrush=self._pg.mkBrush("#ff8c00"), symbolPen=None)
            r = sol["L_hat"]
            sphere_pen = self._pg.mkPen("#4488ff", width=1.5, style=QtCore.Qt.DashLine)
            for key, (cx, cy) in (
                ("xy", (p[0], p[1])), ("xz", (p[0], p[2])), ("yz", (p[1], p[2]))):
                sx, sy = ipt_sphere_circle(cx, cy, r)
                pw = plot_map[key][0]
                item = pw.plot(sx, sy, pen=sphere_pen)
                self._ipt_sphere[key].append(item)
        else:
            for key in self._ipt_marker:
                self._ipt_marker[key].setData(x=[], y=[])

    def _set_status(self, text: str, color: str) -> None:
        self._lbl_status.setText(text)
        self._lbl_status.setStyleSheet(f"color:{color}; font-weight:bold;")

    def _warn(self, text: str) -> None:
        QtWidgets.QMessageBox.warning(self, "EVKA Position", text)

    def _on_split_moved(self, _pos: int, _index: int) -> None:
        if self._balancing_split:
            return
        self._split_user_moved = True

    def _balance_split(self) -> None:
        if not hasattr(self, "_split") or self._split_user_moved:
            return
        w = self._split.width()
        if w < 200:
            return
        half = w // 2
        self._balancing_split = True
        self._split.setSizes([half, w - half])
        self._balancing_split = False

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QtCore.QTimer.singleShot(0, self._balance_split)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        QtCore.QTimer.singleShot(0, self._balance_split)

    def closeEvent(self, event) -> None:
        for t in (self._drain_timer, self._view_timer, self._batt_timer, self._hb_timer,
                  self._cmd_timer, self._sysinfo_timer, self._reconnect_timer):
            t.stop()
        if hasattr(self, "_replay_timer"):
            self._replay_timer.stop()
        if self._rec_file is not None:
            self._rec_file.close()      # don't truncate a recording on exit
            self._rec_file = None
        if self._transport is not None:
            self._transport.close(emit_disconnect=False)
            self._transport = None
        if self._cal_window is not None:
            self._cal_window.close()
        if self._wifi_window is not None:
            self._wifi_window.close()
        if self._ipt_plots_window is not None:
            self._ipt_plots_window.close()
        if self._remote_window is not None:
            self._remote_window.close()
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
