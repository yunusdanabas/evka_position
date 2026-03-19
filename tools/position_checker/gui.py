"""gui.py — Software-rendered 3D + 2D multi-projection position viewer."""

import math
import sys

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from .data_store import DataStore


class _View3D(QtWidgets.QWidget):
    """Software-rendered 3D trail view — no OpenGL required.

    Z-axis-up perspective projection. Left-click + drag rotates the view.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rot_x = -30.0   # elevation tilt (degrees)
        self._rot_y = 45.0    # azimuth spin   (degrees)
        self._drag_start = None
        self._pts: list[tuple[float, float, float]] = []
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: #0f0f23;")

    def set_data(self, xs, ys, zs):
        self._pts = list(zip(xs.tolist(), ys.tolist(), zs.tolist()))
        self.update()

    def clear(self):
        self._pts = []
        self.update()

    # ------------------------------------------------------------------
    def _project(self, x: float, y: float, z: float) -> tuple[float, float]:
        W, H = self.width(), self.height()
        rz = math.radians(self._rot_y)   # azimuth: spin around Z
        rx = math.radians(self._rot_x)   # elevation: tilt around X
        cz, sz = math.cos(rz), math.sin(rz)
        cx, sx = math.cos(rx), math.sin(rx)
        x1 = x * cz - y * sz             # rotate around Z
        y1 = x * sz + y * cz
        y2 = y1 * cx - z * sx            # tilt around X  (y2 = depth)
        z1 = y1 * sx + z * cx            #                (z1 = screen-up)
        s = W * 0.6 / (y2 + 800)
        return W / 2 + x1 * s, H / 2 - z1 * s

    def paintEvent(self, _event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        W, H = self.width(), self.height()

        painter.fillRect(0, 0, W, H, QtGui.QColor("#0f0f23"))

        # Grid (XY plane, Z=0)
        grid_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 18))
        grid_pen.setWidthF(0.5)
        painter.setPen(grid_pen)
        for i in range(-600, 601, 200):
            a = self._project(i, -600, 0)
            b = self._project(i,  600, 0)
            painter.drawLine(QtCore.QLineF(*a, *b))
            c = self._project(-600, i, 0)
            d = self._project( 600, i, 0)
            painter.drawLine(QtCore.QLineF(*c, *d))

        # Axes
        ox, oy = self._project(0, 0, 0)
        al = 400
        for (ax, ay, az), color in [
            ((al, 0,  0),  "#ff4444"),
            ((0,  al, 0),  "#44ff44"),
            ((0,  0,  al), "#4488ff"),
        ]:
            px, py = self._project(ax, ay, az)
            pen = QtGui.QPen(QtGui.QColor(color))
            pen.setWidthF(1.5)
            painter.setPen(pen)
            painter.drawLine(QtCore.QLineF(ox, oy, px, py))

        pts = self._pts
        n = len(pts)

        # Trail
        if n > 1:
            for i in range(1, n):
                alpha = int(51 + 204 * (i / n))
                pen = QtGui.QPen(QtGui.QColor(30, 200, 120, alpha))
                pen.setWidthF(2)
                painter.setPen(pen)
                x0, y0 = self._project(*pts[i - 1])
                x1, y1 = self._project(*pts[i])
                painter.drawLine(QtCore.QLineF(x0, y0, x1, y1))

        # Head dot
        if n > 0:
            hx, hy = self._project(*pts[-1])
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QBrush(QtGui.QColor("#ff3333")))
            painter.drawEllipse(QtCore.QPointF(hx, hy), 14, 14)
            painter.setBrush(QtGui.QBrush(QtGui.QColor("#ff8888")))
            painter.drawEllipse(QtCore.QPointF(hx, hy),  7,  7)

        painter.end()

    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_start = event.pos()

    def mouseMoveEvent(self, event):
        if self._drag_start is not None and (event.buttons() & QtCore.Qt.LeftButton):
            dx = event.x() - self._drag_start.x()
            dy = event.y() - self._drag_start.y()
            self._rot_y += dx * 0.4
            self._rot_x += dy * 0.4
            self._drag_start = event.pos()
            self.update()

    def mouseReleaseEvent(self, _event):
        self._drag_start = None


# ==============================================================================

def run_gui(store: DataStore, fps: float = 10.0) -> None:
    """Open the position checker window.  Blocks until the window is closed."""

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    import pyqtgraph as pg  # noqa: PLC0415 — intentional late import

    pg.setConfigOption("background", "#1a1a2e")
    pg.setConfigOption("foreground", "#e0e0e0")

    win = QtWidgets.QWidget()
    win.setWindowTitle("Spherical 3D Position Checker")
    win.resize(1600, 720)
    win.setStyleSheet("background-color: #1a1a2e; color: #e0e0e0;")

    main_layout = QtWidgets.QHBoxLayout(win)
    main_layout.setSpacing(8)
    main_layout.setContentsMargins(8, 8, 8, 8)

    # --- Software 3D view (left column) ---
    view3d = _View3D()
    main_layout.addWidget(view3d, stretch=2)

    # --- 2D plots column (centre) ---
    plots_col_widget = QtWidgets.QWidget()
    plots_col_layout = QtWidgets.QVBoxLayout(plots_col_widget)
    plots_col_layout.setSpacing(4)
    plots_col_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(plots_col_widget, stretch=2)

    def _make_plot(title, xlabel, ylabel):
        pw = pg.PlotWidget(title=title)
        pw.setLabel("bottom", xlabel)
        pw.setLabel("left", ylabel)
        pw.showGrid(x=True, y=True, alpha=0.2)
        pw.setAspectLocked(True)
        return pw

    plot_xy = _make_plot("Top View  XY", "X (mm)", "Y (mm)")
    plot_xz = _make_plot("Side View  XZ", "X (mm)", "Z (mm)")
    plot_yz = _make_plot("Front View  YZ", "Y (mm)", "Z (mm)")

    plots_col_layout.addWidget(plot_xy)
    plots_col_layout.addWidget(plot_xz)
    plots_col_layout.addWidget(plot_yz)

    trail_pen = pg.mkPen(color="#1e78b4", width=1.5)
    head_brush = pg.mkBrush("#ff3333")
    head_pen = pg.mkPen(None)

    trail_xy = plot_xy.plot([], [], pen=trail_pen)
    head_xy  = plot_xy.plot([], [], pen=head_pen, symbol="o",
                            symbolBrush=head_brush, symbolSize=10)
    trail_xz = plot_xz.plot([], [], pen=trail_pen)
    head_xz  = plot_xz.plot([], [], pen=head_pen, symbol="o",
                            symbolBrush=head_brush, symbolSize=10)
    trail_yz = plot_yz.plot([], [], pen=trail_pen)
    head_yz  = plot_yz.plot([], [], pen=head_pen, symbol="o",
                            symbolBrush=head_brush, symbolSize=10)

    # --- Right panel ---
    right_panel = QtWidgets.QVBoxLayout()
    right_panel.setSpacing(10)
    main_layout.addLayout(right_panel, stretch=1)

    title_label = QtWidgets.QLabel("Spherical 3D\nPosition Checker")
    title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #e0e0e0;")
    right_panel.addWidget(title_label)

    sensor_header = QtWidgets.QLabel("SENSOR READINGS")
    sensor_header.setStyleSheet(
        "font-size: 12px; font-weight: bold; color: #ffd700;"
        "border-bottom: 1px solid #ffd700; padding-bottom: 3px;"
    )
    right_panel.addWidget(sensor_header)

    readings_label = QtWidgets.QLabel(
        "Draw-wire  R =   \u2014\u2014 mm\n"
        "Rotary-1   \u03b8 =  \u2014\u2014.\u2014\u00b0\n"
        "Rotary-2   \u03c6 =  \u2014\u2014.\u2014\u00b0"
    )
    readings_label.setStyleSheet(
        "font-family: monospace; font-size: 13px; color: #7fffd4; padding: 4px 0px;"
    )
    right_panel.addWidget(readings_label)

    info_label = QtWidgets.QLabel("Waiting for data...")
    info_label.setStyleSheet("font-family: monospace; font-size: 11px; color: #e0e0e0;")
    info_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
    info_label.setWordWrap(True)
    right_panel.addWidget(info_label, stretch=1)

    btn_layout = QtWidgets.QHBoxLayout()
    btn_style = (
        "QPushButton { color: #00ffff; border: 1px solid #00ffff;"
        "  padding: 4px 10px; background: transparent; }"
        "QPushButton:hover { background: #003333; }"
    )
    btn_zero = QtWidgets.QPushButton("Zero")
    btn_ping = QtWidgets.QPushButton("Ping")
    btn_clear = QtWidgets.QPushButton("Clear")
    btn_zero.setStyleSheet(btn_style)
    btn_ping.setStyleSheet(btn_style)
    btn_clear.setStyleSheet(btn_style)
    btn_zero.clicked.connect(lambda: store.send_zero())
    btn_ping.clicked.connect(lambda: store.send_ping())
    btn_clear.clicked.connect(lambda: store.clear())
    btn_layout.addWidget(btn_zero)
    btn_layout.addWidget(btn_ping)
    btn_layout.addWidget(btn_clear)
    right_panel.addLayout(btn_layout)

    # --- Update timer ---
    def update():
        frames = store.snapshot()
        status = store.get_runtime_status()
        latest = frames[-1] if frames else None

        if frames:
            xs = np.array([f.x_mm for f in frames], dtype=np.float64)
            ys = np.array([f.y_mm for f in frames], dtype=np.float64)
            zs = np.array([f.z_mm for f in frames], dtype=np.float64)

            view3d.set_data(xs, ys, zs)

            trail_xy.setData(xs, ys)
            head_xy.setData([xs[-1]], [ys[-1]])

            trail_xz.setData(xs, zs)
            head_xz.setData([xs[-1]], [zs[-1]])

            trail_yz.setData(ys, zs)
            head_yz.setData([ys[-1]], [zs[-1]])
        else:
            view3d.clear()
            for t, h in [(trail_xy, head_xy), (trail_xz, head_xz), (trail_yz, head_yz)]:
                t.setData([], [])
                h.setData([], [])

        if latest is not None:
            readings_label.setText(
                f"Draw-wire  R = {latest.r_mm:8.1f} mm\n"
                f"Rotary-1   \u03b8 = {latest.theta_deg:+8.2f}\u00b0\n"
                f"Rotary-2   \u03c6 = {latest.phi_deg:8.2f}\u00b0"
            )
            info_text = (
                "Cartesian\n"
                "------------------------\n"
                f"  X = {latest.x_mm:+10.1f} mm\n"
                f"  Y = {latest.y_mm:+10.1f} mm\n"
                f"  Z = {latest.z_mm:+10.1f} mm\n"
                "------------------------\n"
                f"  Valid  = {'YES' if latest.is_valid else 'NO':>6}\n"
                f"  Frame  = {latest.frame_count:>6}\n"
                f"  t      = {latest.ts_ms:>6} ms\n"
                f"  Points = {len(frames):>6}\n"
                "------------------------\n"
                f"  Connected = {'YES' if status['connected'] else 'NO'}\n"
                f"  Link      = {status['connection_info']}\n"
                f"  Last info = {status['last_info']}\n"
                f"  Last cmd  = {status['last_command_status']}\n"
                f"  Last err  = {status['last_error']}"
            )
        else:
            readings_label.setText(
                "Draw-wire  R =   \u2014\u2014 mm\n"
                "Rotary-1   \u03b8 =  \u2014\u2014.\u2014\u00b0\n"
                "Rotary-2   \u03c6 =  \u2014\u2014.\u2014\u00b0"
            )
            info_text = (
                "Cartesian\n"
                "------------------------\n"
                "  waiting for DATA frames\n"
                "------------------------\n"
                f"  Connected = {'YES' if status['connected'] else 'NO'}\n"
                f"  Link      = {status['connection_info']}\n"
                f"  Last info = {status['last_info']}\n"
                f"  Last cmd  = {status['last_command_status']}\n"
                f"  Last err  = {status['last_error']}"
            )
        info_label.setText(info_text)

    interval_ms = int(max(16, 1000.0 / max(1.0, fps)))
    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(interval_ms)

    win.show()
    app.exec_()
