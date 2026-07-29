"""remote_window.py — secondary window for ESP32-C3 ButtonRemoteTest firmware."""

from __future__ import annotations

from PyQt5 import QtWidgets

from tools.remote_tester.remote_test_gui import RemoteTestWindow


class RemoteTesterWindow(RemoteTestWindow):
    """ButtonRemoteTest dev tool — separate TCP session from main EVKA GUI."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Remote Button Tester (ButtonRemoteTest firmware)")
        # Dev-note banner adds ~40 px; keep log stretch usable without clipping.
        self.setMinimumSize(480, 560)
        self.resize(520, 680)

    def _header_widget(self) -> QtWidgets.QWidget | None:
        note = QtWidgets.QLabel(
            "Dev tool only — connects to ESP32-C3 ButtonRemoteTest AP (REMOTE_TEST), "
            "not production EVKA position firmware."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#888; font-size:10px;")
        note.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Maximum,
        )
        return note
