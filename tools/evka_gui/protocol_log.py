"""protocol_log.py — scrollable raw protocol log with category filters."""

from __future__ import annotations

from collections import deque
from typing import Deque, Optional

from PyQt5 import QtCore, QtGui, QtWidgets

_MAX_LINES = 2000


def _classify_line(line: str) -> str:
    s = line.strip()
    if (
        s.startswith("DATA,")
        or s.startswith("SENSOR,")
        or (s.startswith("X") and ",Y" in s and ",Z" in s)
    ):
        return "data"
    if s.startswith("ACK:"):
        return "ack"
    if s.startswith("ERR:"):
        return "err"
    return "other"


class ProtocolLogPane(QtWidgets.QWidget):
    """Compact raw protocol log with filters."""

    def __init__(self, parent=None, *, compact: bool = False) -> None:
        super().__init__(parent)
        self._compact = compact
        self._lines: Deque[tuple[str, str]] = deque(maxlen=_MAX_LINES)
        self._paused = False
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)

        bar = QtWidgets.QHBoxLayout()
        self._chk_data = QtWidgets.QCheckBox("DATA")
        self._chk_ack = QtWidgets.QCheckBox("ACK")
        self._chk_err = QtWidgets.QCheckBox("ERR")
        self._chk_other = QtWidgets.QCheckBox("Other")
        for chk in (self._chk_data, self._chk_ack, self._chk_err, self._chk_other):
            chk.setChecked(True)
            chk.toggled.connect(self._refresh_view)
            bar.addWidget(chk)
        self._chk_pause = QtWidgets.QCheckBox("Pause")
        self._chk_pause.toggled.connect(lambda v: setattr(self, "_paused", v))
        bar.addWidget(self._chk_pause)
        btn_clear = QtWidgets.QPushButton("Clear")
        btn_clear.clicked.connect(self.clear)
        bar.addWidget(btn_clear)
        bar.addStretch(1)
        lay.addLayout(bar)

        self._view = QtWidgets.QPlainTextEdit()
        self._view.setReadOnly(True)
        self._view.setFont(QtGui.QFont("Consolas", 9))
        self._view.setMaximumBlockCount(_MAX_LINES)
        if self._compact:
            self._view.setMaximumHeight(72)
            self._view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self._view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        lay.addWidget(self._view)

    def append_line(self, line: str) -> None:
        if self._paused or not line.strip():
            return
        cat = _classify_line(line)
        self._lines.append((cat, line.strip()))
        if self._visible(cat):
            self._view.appendPlainText(line.strip())

    def clear(self) -> None:
        self._lines.clear()
        self._view.clear()

    def _visible(self, cat: str) -> bool:
        return {
            "data": self._chk_data.isChecked(),
            "ack": self._chk_ack.isChecked(),
            "err": self._chk_err.isChecked(),
            "other": self._chk_other.isChecked(),
        }.get(cat, True)

    def _refresh_view(self) -> None:
        self._view.clear()
        for cat, line in self._lines:
            if self._visible(cat):
                self._view.appendPlainText(line)
