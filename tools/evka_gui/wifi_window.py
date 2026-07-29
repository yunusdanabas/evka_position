"""wifi_window.py — WiFi credential settings secondary window for evka_gui."""

from __future__ import annotations

from typing import Callable, Optional

from PyQt5 import QtCore, QtWidgets

SaveFn = Callable[[], None]
ForgetFn = Callable[[], None]


class WifiSettingsWindow(QtWidgets.QMainWindow):
    """Secondary window for STA WiFi credentials (TCP mode only)."""

    def __init__(
        self,
        save_fn: SaveFn,
        forget_fn: ForgetFn,
        ssid: str = "",
        password: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._save = save_fn
        self._forget = forget_fn
        self.setWindowTitle("EVKA WiFi Settings")
        self.resize(480, 220)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        router = QtWidgets.QGroupBox("STA / Router")
        rl = QtWidgets.QVBoxLayout(router)
        self._lbl_router_ip = QtWidgets.QLabel("Router IP: —")
        rl.addWidget(self._lbl_router_ip)
        layout.addWidget(router)

        cred = QtWidgets.QGroupBox("Credentials")
        cl = QtWidgets.QGridLayout(cred)
        self.txt_ssid = QtWidgets.QLineEdit(ssid)
        self.txt_pass = QtWidgets.QLineEdit(password)
        self.txt_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.btn_save = QtWidgets.QPushButton("Save && Reboot")
        self.btn_forget = QtWidgets.QPushButton("Forget")
        self.btn_save.clicked.connect(self._save)
        self.btn_forget.clicked.connect(self._forget)
        cl.addWidget(QtWidgets.QLabel("SSID"), 0, 0)
        cl.addWidget(self.txt_ssid, 0, 1)
        cl.addWidget(QtWidgets.QLabel("Password"), 1, 0)
        cl.addWidget(self.txt_pass, 1, 1)
        cl.addWidget(self.btn_save, 2, 0)
        cl.addWidget(self.btn_forget, 2, 1)
        layout.addWidget(cred)

        self._status = QtWidgets.QLabel(
            "Saving credentials reboots the device. AP stays at 192.168.1.50."
        )
        self._status.setWordWrap(True)
        self._status.setStyleSheet("color:#888; font-size:10px;")
        layout.addWidget(self._status)

    def ssid(self) -> str:
        return self.txt_ssid.text().strip()

    def password(self) -> str:
        return self.txt_pass.text()

    def set_router_ip(self, text: str) -> None:
        self._lbl_router_ip.setText(text)

    def set_controls_enabled(self, enabled: bool) -> None:
        self.btn_save.setEnabled(enabled)
        self.btn_forget.setEnabled(enabled)

    def set_status(self, text: str, color: Optional[str] = None) -> None:
        self._status.setText(text)
        if color:
            self._status.setStyleSheet(f"color:{color}; font-size:10px;")
