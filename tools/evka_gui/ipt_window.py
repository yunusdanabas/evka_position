"""ipt_window.py — optional full-height IPT projection plots for evka_gui."""

from __future__ import annotations

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from .ipt_panel import (
    IptPanel,
    ipt_marker_coords,
    ipt_projections,
    ipt_sphere_circle,
)

_CLOUD_BRUSH = pg.mkBrush("#00ff88")
_MARKER_BRUSH = pg.mkBrush("#ff8c00")
_SPHERE_PEN = pg.mkPen("#4488ff", width=1.5, style=QtCore.Qt.DashLine)


class IptPlotsWindow(QtWidgets.QMainWindow):
    """Plots-only pop-out mirroring the shared IptPanel capture state."""

    def __init__(self, panel: IptPanel, parent=None) -> None:
        super().__init__(parent)
        self._panel = panel
        self._sphere_items: dict[str, list] = {"xy": [], "xz": [], "yz": []}
        self.setWindowTitle("EVKA Quick IPT — projection plots")
        self.resize(1040, 720)
        self._build_ui()
        self._panel.state_changed.connect(self._refresh_plots)
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._refresh_plots)
        self._timer.start(40)

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        pl = QtWidgets.QVBoxLayout(central)
        pl.setContentsMargins(0, 0, 0, 0)

        self._plots: dict[str, pg.PlotWidget] = {}
        self._cloud_scatters: dict[str, pg.PlotDataItem] = {}
        self._marker_scatters: dict[str, pg.PlotDataItem] = {}

        titles = {"xy": "XY (top)", "xz": "XZ (front)", "yz": "YZ (side)"}
        for key, title in titles.items():
            pw = pg.PlotWidget(title=title)
            pw.setLabel("bottom", "mm")
            pw.setLabel("left", "mm")
            pw.showGrid(x=True, y=True, alpha=0.15)
            pw.setAspectLocked(True)
            self._plots[key] = pw
            pl.addWidget(pw)
            self._cloud_scatters[key] = pw.plot(
                [], [], pen=None, symbol="o", symbolSize=5,
                symbolBrush=_CLOUD_BRUSH, symbolPen=None)
            self._marker_scatters[key] = pw.plot(
                [], [], pen=None, symbol="o", symbolSize=12,
                symbolBrush=_MARKER_BRUSH, symbolPen=None)

    def _clear_sphere_overlays(self) -> None:
        for key, items in self._sphere_items.items():
            for item in items:
                self._plots[key].removeItem(item)
            items.clear()

    def _add_sphere_overlay(self, key: str, cx: float, cy: float, r: float) -> None:
        x, y = ipt_sphere_circle(cx, cy, r)
        item = self._plots[key].plot(x, y, pen=_SPHERE_PEN)
        self._sphere_items[key].append(item)

    def _refresh_plots(self) -> None:
        pts = self._panel.points()
        projections = ipt_projections(pts)
        for key, (xs, ys) in projections.items():
            self._cloud_scatters[key].setData(
                x=xs, y=ys, symbol="o", symbolSize=5,
                symbolBrush=_CLOUD_BRUSH, symbolPen=None)

        sol = self._panel.last_solution
        self._clear_sphere_overlays()
        if sol and sol.get("ok"):
            p = sol["P"]
            coords = ipt_marker_coords(p)
            for key, (px, py) in coords.items():
                self._marker_scatters[key].setData(
                    x=[px], y=[py], symbol="o", symbolSize=12,
                    symbolBrush=_MARKER_BRUSH, symbolPen=None)
            r = sol["L_hat"]
            self._add_sphere_overlay("xy", p[0], p[1], r)
            self._add_sphere_overlay("xz", p[0], p[2], r)
            self._add_sphere_overlay("yz", p[1], p[2], r)
        else:
            for key in self._marker_scatters:
                self._marker_scatters[key].setData(x=[], y=[])

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        self._timer.stop()
        try:
            self._panel.state_changed.disconnect(self._refresh_plots)
        except TypeError:
            pass
        super().closeEvent(event)


# Backward-compatible alias
IptWindow = IptPlotsWindow
