"""cmd_gui.py — Linux PyQt GUI for ESP32 TCP CMD protocol."""

from __future__ import annotations

import math
import queue
from pathlib import Path
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from .cmd_main import (
    ACK_PREFIX,
    CMD_AP_FALLBACK_IP,
    CMD_DEFAULT_PORT,
    CMD_DEFAULT_STA_IP,
    ERR_PREFIX,
    REMOTE_BTN_PREFIX,
    REMOTE_HB_PREFIX,
    SENSOR_PREFIX,
    STA_IP_PREFIX,
    SYSINFO_PREFIX,
    XYZ_PREFIX,
)
from .parser import parse_sensor_line, parse_xyz_line
from .tcp_client import TcpClient
from .transform import cartesian_to_spherical


class CmdControlWindow(QtWidgets.QWidget):
    """TCP control panel compatible with EvkaPosition CMD TCP protocol."""

    def __init__(self) -> None:
        super().__init__()
        self._client = TcpClient()
        self._event_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._drain_events)
        self._timer.start(25)

        # Sysinfo polling timer
        self._sysinfo_timer = QtCore.QTimer(self)
        self._sysinfo_timer.timeout.connect(self._poll_sysinfo)
        self._sysinfo_timer.setInterval(5000)

        self._last_raw_x = 0.0
        self._last_raw_y = 0.0
        self._last_raw_z = 0.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._offset_z = 0.0
        self._relative_zero_active = False
        self._wifi_pending_action: Optional[str] = None  # "save" | "forget" | None
        self._remote_last_ms: float = 0.0  # epoch ms of last REMOTE_HB or REMOTE_BTN

        # Periodic remote link status updater
        self._link_timer = QtCore.QTimer(self)
        self._link_timer.timeout.connect(self._update_remote_link)
        self._link_timer.start(2000)

        # Min/Max
        self._min = {"x": math.inf, "y": math.inf, "z": math.inf}
        self._max = {"x": -math.inf, "y": -math.inf, "z": -math.inf}

        self._settings_path = Path.cwd() / "settings.txt"

        self._build_ui()
        self._load_settings()
        self._set_controls_connected(False)

    def _build_ui(self) -> None:
        self.setWindowTitle("CMDScanner - Industrial Control Panel (Linux)")
        self.resize(780, 760)
        self.setMinimumSize(760, 740)
        self.setFont(QtGui.QFont("Segoe UI", 10))

        main = QtWidgets.QVBoxLayout(self)
        main.setSpacing(8)

        # --- Connection ---
        conn_box = QtWidgets.QGroupBox("Device Connection")
        conn_layout = QtWidgets.QGridLayout(conn_box)
        # Default to latest confirmed STA IP (ASMETAL example).
        # AP fallback remains 192.168.1.50 when STA is unavailable.
        self.txt_ip = QtWidgets.QLineEdit(CMD_DEFAULT_STA_IP)
        self.txt_port = QtWidgets.QLineEdit(str(CMD_DEFAULT_PORT))
        self.btn_connect = QtWidgets.QPushButton("CONNECT")
        self.btn_disconnect = QtWidgets.QPushButton("DISCONNECT")
        conn_layout.addWidget(QtWidgets.QLabel("IP:"), 0, 0)
        conn_layout.addWidget(self.txt_ip, 0, 1)
        conn_layout.addWidget(QtWidgets.QLabel("Port:"), 0, 2)
        conn_layout.addWidget(self.txt_port, 0, 3)
        conn_layout.addWidget(self.btn_connect, 0, 4)
        conn_layout.addWidget(self.btn_disconnect, 0, 5)
        main.addWidget(conn_box)

        self.lbl_status = QtWidgets.QLabel("Status: Waiting...")
        self.lbl_status.setStyleSheet("font-weight: bold; color: #c0392b;")
        main.addWidget(self.lbl_status)

        # --- Position with min/max ---
        xyz_box = QtWidgets.QGroupBox("Position")
        xyz_layout = QtWidgets.QGridLayout(xyz_box)
        self.lbl_x = QtWidgets.QLabel("X:    0.00 mm")
        self.lbl_y = QtWidgets.QLabel("Y:    0.00 mm")
        self.lbl_z = QtWidgets.QLabel("Z:    0.00 mm")

        self.lbl_min_x = QtWidgets.QLabel("Min: --")
        self.lbl_max_x = QtWidgets.QLabel("Max: --")
        self.lbl_min_y = QtWidgets.QLabel("Min: --")
        self.lbl_max_y = QtWidgets.QLabel("Max: --")
        self.lbl_min_z = QtWidgets.QLabel("Min: --")
        self.lbl_max_z = QtWidgets.QLabel("Max: --")

        for lbl, color in [
            (self.lbl_x, "#ff4444"),
            (self.lbl_y, "#44ff44"),
            (self.lbl_z, "#4488ff"),
        ]:
            lbl.setFont(QtGui.QFont("Consolas", 22, QtGui.QFont.Bold))
            lbl.setStyleSheet(f"color: {color};")

        mm_font = QtGui.QFont("Consolas", 9)
        mm_style = "color: #888;"
        for lbl in [
            self.lbl_min_x, self.lbl_max_x,
            self.lbl_min_y, self.lbl_max_y,
            self.lbl_min_z, self.lbl_max_z,
        ]:
            lbl.setFont(mm_font)
            lbl.setStyleSheet(mm_style)

        self.btn_zero_x = QtWidgets.QPushButton("X=0")
        self.btn_zero_y = QtWidgets.QPushButton("Y=0")
        self.btn_zero_z = QtWidgets.QPushButton("Z=0")

        xyz_layout.addWidget(self.lbl_x, 0, 0, 1, 2)
        xyz_layout.addWidget(self.lbl_min_x, 1, 0)
        xyz_layout.addWidget(self.lbl_max_x, 1, 1)
        xyz_layout.addWidget(self.btn_zero_x, 0, 2, 2, 1)

        xyz_layout.addWidget(self.lbl_y, 2, 0, 1, 2)
        xyz_layout.addWidget(self.lbl_min_y, 3, 0)
        xyz_layout.addWidget(self.lbl_max_y, 3, 1)
        xyz_layout.addWidget(self.btn_zero_y, 2, 2, 2, 1)

        xyz_layout.addWidget(self.lbl_z, 4, 0, 1, 2)
        xyz_layout.addWidget(self.lbl_min_z, 5, 0)
        xyz_layout.addWidget(self.lbl_max_z, 5, 1)
        xyz_layout.addWidget(self.btn_zero_z, 4, 2, 2, 1)

        main.addWidget(xyz_box)

        # --- Sensor Readings ---
        sensor_box = QtWidgets.QGroupBox("Sensor Readings")
        sensor_layout = QtWidgets.QGridLayout(sensor_box)
        self.lbl_r = QtWidgets.QLabel("R: --")
        self.lbl_theta = QtWidgets.QLabel("\u03B8: --")
        self.lbl_phi = QtWidgets.QLabel("\u03C6: --")
        self.lbl_valid = QtWidgets.QLabel("Valid: --")
        self.lbl_frame = QtWidgets.QLabel("Frame: --")

        for lbl in [self.lbl_r, self.lbl_theta, self.lbl_phi]:
            lbl.setFont(QtGui.QFont("Consolas", 13, QtGui.QFont.Bold))

        for lbl in [self.lbl_valid, self.lbl_frame]:
            lbl.setFont(QtGui.QFont("Consolas", 10))
            lbl.setStyleSheet("color: #666;")

        sensor_layout.addWidget(self.lbl_r, 0, 0)
        sensor_layout.addWidget(self.lbl_valid, 0, 1)
        sensor_layout.addWidget(self.lbl_frame, 0, 2)
        sensor_layout.addWidget(self.lbl_theta, 1, 0)
        sensor_layout.addWidget(self.lbl_phi, 1, 1)
        main.addWidget(sensor_box)

        # --- Zero buttons ---
        zero_row = QtWidgets.QHBoxLayout()
        self.btn_work_zero_all = QtWidgets.QPushButton("Software Zero (All)")
        self.btn_machine_zero = QtWidgets.QPushButton("Hardware Zero (Encoder)")
        self.btn_reset_minmax = QtWidgets.QPushButton("Reset Min/Max")
        zero_row.addWidget(self.btn_work_zero_all)
        zero_row.addWidget(self.btn_machine_zero)
        zero_row.addWidget(self.btn_reset_minmax)
        main.addLayout(zero_row)

        # --- WiFi Settings ---
        wifi_box = QtWidgets.QGroupBox("WiFi Settings (ESP32 STA)")
        wifi_layout = QtWidgets.QGridLayout(wifi_box)
        self.txt_ssid = QtWidgets.QLineEdit()
        self.txt_pass = QtWidgets.QLineEdit()
        self.txt_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.btn_wifi_save = QtWidgets.QPushButton("SAVE & REBOOT")
        self.btn_wifi_forget = QtWidgets.QPushButton("FORGET")
        self.lbl_router_ip = QtWidgets.QLabel("Router IP: --")
        wifi_layout.addWidget(QtWidgets.QLabel("SSID:"), 0, 0)
        wifi_layout.addWidget(self.txt_ssid, 0, 1)
        wifi_layout.addWidget(QtWidgets.QLabel("Password:"), 0, 2)
        wifi_layout.addWidget(self.txt_pass, 0, 3)
        wifi_layout.addWidget(self.btn_wifi_save, 0, 4)
        wifi_layout.addWidget(self.btn_wifi_forget, 1, 4)
        wifi_layout.addWidget(self.lbl_router_ip, 1, 0, 1, 4)
        main.addWidget(wifi_box)

        # --- System Info ---
        sys_box = QtWidgets.QGroupBox("System Info")
        sys_layout = QtWidgets.QHBoxLayout(sys_box)
        self.lbl_rssi = QtWidgets.QLabel("RSSI: --")
        self.lbl_heap = QtWidgets.QLabel("Heap: --")
        self.lbl_uptime = QtWidgets.QLabel("Uptime: --")
        for lbl in [self.lbl_rssi, self.lbl_heap, self.lbl_uptime]:
            lbl.setFont(QtGui.QFont("Consolas", 9))
            lbl.setStyleSheet("color: #666;")
        sys_layout.addWidget(self.lbl_rssi)
        sys_layout.addWidget(self.lbl_heap)
        sys_layout.addWidget(self.lbl_uptime)
        main.addWidget(sys_box)

        # --- Remote Buttons ---
        remote_box = QtWidgets.QGroupBox("Remote Buttons")
        remote_layout = QtWidgets.QHBoxLayout(remote_box)
        remote_layout.setSpacing(16)

        # BTN0 — Red — ZERO
        btn0_col = QtWidgets.QVBoxLayout()
        btn0_col.setAlignment(QtCore.Qt.AlignHCenter)
        self.rled0 = QtWidgets.QLabel()
        self.rled0.setFixedSize(24, 24)
        self._set_rled(0, False)
        btn0_col.addWidget(self.rled0, alignment=QtCore.Qt.AlignHCenter)
        btn0_col.addWidget(QtWidgets.QLabel("BTN0  ZERO"), alignment=QtCore.Qt.AlignHCenter)
        remote_layout.addLayout(btn0_col)

        # BTN1 — Green — SAVE POINT
        btn1_col = QtWidgets.QVBoxLayout()
        btn1_col.setAlignment(QtCore.Qt.AlignHCenter)
        self.rled1 = QtWidgets.QLabel()
        self.rled1.setFixedSize(24, 24)
        self._set_rled(1, False)
        btn1_col.addWidget(self.rled1, alignment=QtCore.Qt.AlignHCenter)
        btn1_col.addWidget(QtWidgets.QLabel("BTN1  SAVE"), alignment=QtCore.Qt.AlignHCenter)
        remote_layout.addLayout(btn1_col)

        remote_layout.addStretch(1)
        self.lbl_rbtn_status = QtWidgets.QLabel("No signal")
        self.lbl_rbtn_status.setFont(QtGui.QFont("Consolas", 9))
        self.lbl_rbtn_status.setStyleSheet("color: #888;")
        remote_layout.addWidget(self.lbl_rbtn_status)
        main.addWidget(remote_box)

        main.addStretch(1)

        # Connections
        self.btn_connect.clicked.connect(self._on_connect_clicked)
        self.btn_disconnect.clicked.connect(self._disconnect)
        self.btn_zero_x.clicked.connect(self._zero_x)
        self.btn_zero_y.clicked.connect(self._zero_y)
        self.btn_zero_z.clicked.connect(self._zero_z)
        self.btn_work_zero_all.clicked.connect(self._zero_all_soft)
        self.btn_machine_zero.clicked.connect(self._zero_machine)
        self.btn_reset_minmax.clicked.connect(self._reset_minmax)
        self.btn_wifi_save.clicked.connect(self._save_wifi)
        self.btn_wifi_forget.clicked.connect(self._forget_wifi)

    def _load_settings(self) -> None:
        if not self._settings_path.exists():
            return
        try:
            lines = self._settings_path.read_text(encoding="utf-8").splitlines()
            if len(lines) >= 4:
                self.txt_ip.setText(lines[0].strip())
                self.txt_port.setText(lines[1].strip())
                self.txt_ssid.setText(lines[2].strip())
                self.txt_pass.setText(lines[3].strip())
        except Exception:
            pass

    def _save_settings(self) -> None:
        lines = [
            self.txt_ip.text().strip(),
            self.txt_port.text().strip(),
            self.txt_ssid.text().strip(),
            self.txt_pass.text().strip(),
        ]
        self._settings_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _set_controls_connected(self, connected: bool) -> None:
        self.btn_connect.setEnabled(not connected)
        self.btn_disconnect.setEnabled(connected)
        self.btn_zero_x.setEnabled(connected)
        self.btn_zero_y.setEnabled(connected)
        self.btn_zero_z.setEnabled(connected)
        self.btn_work_zero_all.setEnabled(connected)
        self.btn_machine_zero.setEnabled(connected)
        self.btn_reset_minmax.setEnabled(connected)
        self.btn_wifi_save.setEnabled(connected)
        self.btn_wifi_forget.setEnabled(connected)

    # ---- Remote LED helpers ----
    _RLED_IDLE = [
        "border-radius:12px;border:2px solid #662222;background:#1a1a1a;",
        "border-radius:12px;border:2px solid #226622;background:#1a1a1a;",
    ]
    _RLED_ON = [
        "border-radius:12px;border:2px solid #ff6666;background:#ff3333;",
        "border-radius:12px;border:2px solid #66ff66;background:#33cc33;",
    ]

    def _set_rled(self, idx: int, active: bool) -> None:
        lbl = self.rled0 if idx == 0 else self.rled1
        lbl.setStyleSheet(self._RLED_ON[idx] if active else self._RLED_IDLE[idx])

    def _flash_rled(self, idx: int) -> None:
        names = ["ZERO", "SAVE POINT"]
        self._set_rled(idx, True)
        QtCore.QTimer.singleShot(400, lambda i=idx: self._set_rled(i, False))

    def _update_remote_link(self) -> None:
        import time
        if self._remote_last_ms == 0.0:
            self.lbl_rbtn_status.setText("LINK: NO SIGNAL")
            self.lbl_rbtn_status.setStyleSheet("color: #888;")
            return
        age = int(time.time() * 1000 - self._remote_last_ms) // 1000
        if age < 15:
            self.lbl_rbtn_status.setText(f"LINK: OK ({age}s ago)")
            self.lbl_rbtn_status.setStyleSheet("color: #00cc66;")
        else:
            self.lbl_rbtn_status.setText(f"LINK: TIMEOUT ({age}s ago)")
            self.lbl_rbtn_status.setStyleSheet("color: #ff4444;")

    def _set_status(self, text: str, color: str) -> None:
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"font-weight: bold; color: {color};")

    def _on_connect_clicked(self) -> None:
        ip = self.txt_ip.text().strip()
        port_txt = self.txt_port.text().strip()
        try:
            port = int(port_txt)
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Error", "Port must be a number.")
            return

        self._set_status("Status: Connecting...", "#f39c12")
        self._client.set_callbacks(
            on_line=lambda line: self._event_queue.put(("line", line)),
            on_disconnect=lambda reason: self._event_queue.put(("disconnect", reason)),
        )
        ok, info = self._client.connect(ip, port)
        if not ok:
            self._set_status("Status: Connection failed.", "#c0392b")
            QtWidgets.QMessageBox.critical(self, "Connection Error", info)
            self._client.close(emit_disconnect=False)
            return

        self._set_status("Status: Connected! Data streaming.", "#27ae60")
        self._set_controls_connected(True)
        self._send_command("GET_IP")
        self._send_command("SYSINFO")
        self._sysinfo_timer.start()

    def _send_command(self, command: str) -> bool:
        ok, info = self._client.send_command(command)
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Warning", f"Command failed: {info}")
            return False
        return True

    def _poll_sysinfo(self) -> None:
        if self._client.is_connected():
            self._client.send_command("SYSINFO")
            self._client.send_command("GET_IP")

    def _disconnect(self) -> None:
        self._sysinfo_timer.stop()
        self._client.close(emit_disconnect=False)
        self._set_status("Status: Disconnected.", "#c0392b")
        self._set_controls_connected(False)
        self.lbl_router_ip.setText("Router IP: --")

    def _update_xyz_labels(self, x: float, y: float, z: float) -> None:
        self.lbl_x.setText(f"X: {x:8.2f} mm")
        self.lbl_y.setText(f"Y: {y:8.2f} mm")
        self.lbl_z.setText(f"Z: {z:8.2f} mm")

    def _zero_x(self) -> None:
        self._offset_x = self._last_raw_x
        self._relative_zero_active = True
        self._reset_minmax()

    def _zero_y(self) -> None:
        self._offset_y = self._last_raw_y
        self._relative_zero_active = True
        self._reset_minmax()

    def _zero_z(self) -> None:
        self._offset_z = self._last_raw_z
        self._relative_zero_active = True
        self._reset_minmax()

    def _zero_all_soft(self) -> None:
        self._offset_x = self._last_raw_x
        self._offset_y = self._last_raw_y
        self._offset_z = self._last_raw_z
        self._relative_zero_active = True
        self._reset_minmax()

    def _zero_machine(self) -> None:
        answer = QtWidgets.QMessageBox.question(
            self,
            "Hardware Zero",
            "WARNING: This will reset encoder calibration.\n"
            "Is the probe at the mechanical home position?",
        )
        if answer != QtWidgets.QMessageBox.Yes:
            return
        self._relative_zero_active = False
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._offset_z = 0.0
        self._reset_minmax()
        self._send_command("ZERO")

    def _reset_minmax(self) -> None:
        self._min = {"x": math.inf, "y": math.inf, "z": math.inf}
        self._max = {"x": -math.inf, "y": -math.inf, "z": -math.inf}
        for a in ("x", "y", "z"):
            getattr(self, f"lbl_min_{a}").setText("Min: --")
            getattr(self, f"lbl_max_{a}").setText("Max: --")

    def _save_wifi(self) -> None:
        ssid = self.txt_ssid.text().strip()
        password = self.txt_pass.text()
        if not ssid or len(password) < 8:
            QtWidgets.QMessageBox.critical(
                self, "Error",
                "SSID is required and password must be at least 8 characters.",
            )
            return
        if self._send_command(f"WIFI_SET:{ssid},{password}"):
            self._wifi_pending_action = "save"  # dialog shown on ACK:WIFI_SAVED receipt

    def _forget_wifi(self) -> None:
        answer = QtWidgets.QMessageBox.question(
            self, "Forget Network",
            "This will erase stored WiFi credentials.\n"
            "Device will return to AP-only mode. Continue?",
        )
        if answer != QtWidgets.QMessageBox.Yes:
            return
        if self._send_command("WIFI_SET:,"):
            self._wifi_pending_action = "forget"  # dialog shown on ACK:WIFI_SAVED receipt

    def _drain_events(self) -> None:
        while True:
            try:
                evt_type, payload = self._event_queue.get_nowait()
            except queue.Empty:
                break

            if evt_type == "disconnect":
                self._sysinfo_timer.stop()
                self._set_status(f"Status: {payload}", "#c0392b")
                self._set_controls_connected(False)
                self.lbl_router_ip.setText("Router IP: --")
                continue

            line = payload

            # Router IP response
            if line.startswith(STA_IP_PREFIX):
                ip = line[len(STA_IP_PREFIX):].strip()
                display = "Not Connected" if ip == "NOT_CONNECTED" else ip
                self.lbl_router_ip.setText(f"Router IP: {display}")
                if ip != "NOT_CONNECTED" and ip:
                    # Keep connect target in sync with latest router-assigned STA IP.
                    self.txt_ip.setText(ip)
                elif not self.txt_ip.text().strip():
                    self.txt_ip.setText(CMD_AP_FALLBACK_IP)
                continue

            # Sensor data
            if line.startswith(SENSOR_PREFIX):
                sensor = parse_sensor_line(line)
                if sensor is not None:
                    # When software zero is active, R/theta/phi are re-derived
                    # from display XYZ in the XYZ branch to stay in the same
                    # reference frame. Only update from raw firmware SENSOR data
                    # when zero is inactive.
                    if not self._relative_zero_active:
                        self.lbl_r.setText(f"R: {sensor.r_mm:8.2f} mm")
                        self.lbl_theta.setText(f"\u03B8: {sensor.theta_deg:8.3f}\u00B0")
                        self.lbl_phi.setText(f"\u03C6: {sensor.phi_deg:8.3f}\u00B0")
                    self.lbl_valid.setText(f"Valid: {'YES' if sensor.is_valid else 'NO'}")
                    self.lbl_frame.setText(f"Frame: {sensor.frame_count}")
                continue

            # System info
            if line.startswith(SYSINFO_PREFIX):
                parts = line[len(SYSINFO_PREFIX):].split(",")
                if len(parts) >= 4:
                    try:
                        rssi = int(parts[0])
                        heap = int(parts[1])
                        up = int(parts[2])
                        h, m, s = up // 3600, (up % 3600) // 60, up % 60
                        self.lbl_rssi.setText(f"RSSI: {rssi} dBm")
                        self.lbl_heap.setText(f"Heap: {heap // 1024} KB")
                        self.lbl_uptime.setText(f"Uptime: {h:02d}:{m:02d}:{s:02d}")
                    except ValueError:
                        pass
                continue

            # Remote heartbeat — update link status without flashing LEDs
            if line.startswith(REMOTE_HB_PREFIX):
                import time
                self._remote_last_ms = time.time() * 1000
                continue

            # Remote button indicator
            if line.startswith(REMOTE_BTN_PREFIX):
                import time
                self._remote_last_ms = time.time() * 1000
                try:
                    idx = int(line[len(REMOTE_BTN_PREFIX):].strip())
                    if idx in (0, 1):
                        self._flash_rled(idx)
                except ValueError:
                    pass
                continue

            # ACK responses
            if line.startswith(ACK_PREFIX):
                self._set_status(f"Status: {line}", "#27ae60")
                if "WIFI_SAVED" in line and self._wifi_pending_action is not None:
                    action = self._wifi_pending_action
                    self._wifi_pending_action = None
                    if action == "save":
                        QtWidgets.QMessageBox.information(
                            self, "Success",
                            "WiFi credentials sent to ESP32. Device will reboot.",
                        )
                    else:
                        QtWidgets.QMessageBox.information(
                            self, "Success",
                            "Credentials cleared. Device rebooting.\nConnect to CMDCNC WiFi.",
                        )
                    self._disconnect()
                continue

            # ERR responses
            if line.startswith(ERR_PREFIX):
                self._set_status(f"Status: {line}", "#c0392b")
                if "WIFI" in line and self._wifi_pending_action is not None:
                    self._wifi_pending_action = None
                    QtWidgets.QMessageBox.critical(
                        self, "WiFi Error", f"Command rejected: {line}"
                    )
                continue

            # Position data (X,Y,Z)
            if not line.startswith(XYZ_PREFIX):
                continue

            xyz = parse_xyz_line(line)
            if xyz is None:
                continue

            raw_x = xyz.x_mm
            raw_y = xyz.y_mm
            raw_z = xyz.z_mm

            self._last_raw_x = raw_x
            self._last_raw_y = raw_y
            self._last_raw_z = raw_z

            x = raw_x - self._offset_x if self._relative_zero_active else raw_x
            y = raw_y - self._offset_y if self._relative_zero_active else raw_y
            z = raw_z - self._offset_z if self._relative_zero_active else raw_z

            # Min/Max
            for axis, val in [("x", x), ("y", y), ("z", z)]:
                if val < self._min[axis]:
                    self._min[axis] = val
                if val > self._max[axis]:
                    self._max[axis] = val
                mn = self._min[axis]
                mx = self._max[axis]
                getattr(self, f"lbl_min_{axis}").setText(
                    f"Min: {mn:.1f}" if mn != math.inf else "Min: --"
                )
                getattr(self, f"lbl_max_{axis}").setText(
                    f"Max: {mx:.1f}" if mx != -math.inf else "Max: --"
                )

            self._update_xyz_labels(x, y, z)

            # Recompute R/θ/φ from zeroed Cartesian so both panels stay in
            # the same reference frame when software zero is active.
            if self._relative_zero_active:
                disp_r, disp_theta, disp_phi = cartesian_to_spherical(x, y, z)
                self.lbl_r.setText(f"R: {disp_r:8.2f} mm")
                self.lbl_theta.setText(f"\u03B8: {disp_theta:8.3f}\u00B0")
                self.lbl_phi.setText(f"\u03C6: {disp_phi:8.3f}\u00B0")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        self._save_settings()
        self._timer.stop()
        self._sysinfo_timer.stop()
        self._client.close(emit_disconnect=False)
        super().closeEvent(event)


def run_cmd_gui() -> int:
    """Run the Linux CMD GUI and return process exit code."""
    app = QtWidgets.QApplication.instance()
    owns_app = False
    if app is None:
        app = QtWidgets.QApplication([])
        owns_app = True

    win = CmdControlWindow()
    win.show()

    if owns_app:
        return app.exec_()
    return 0
