"""gui.py — 3-D scatter plot + status panel with non-destructive updates."""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
import numpy as np

from .data_store import DataStore


def run_gui(store: DataStore, fps: float = 10.0) -> None:
    """Open the position checker window.  Blocks until the window is closed."""

    fig = plt.figure(figsize=(11, 7))
    fig.suptitle("Spherical 3D Position Checker", fontsize=13)

    # 3-D scatter axes
    ax3d = fig.add_subplot(121, projection="3d")
    ax3d.set_xlabel("X (mm)")
    ax3d.set_ylabel("Y (mm)")
    ax3d.set_zlabel("Z (mm)")
    ax3d.set_title("Trajectory")

    ax3d.grid(True, alpha=0.3)
    ax3d.set_xlim(-1000, 1000)
    ax3d.set_ylim(-1000, 1000)
    ax3d.set_zlim(-1000, 1000)

    trajectory, = ax3d.plot([], [], [], color="#1f77b4", lw=1.6, alpha=0.85)
    points = ax3d.scatter([], [], [], c=[], cmap="viridis", s=10, depthshade=False)
    latest_point = ax3d.scatter([], [], [], c="red", s=60, zorder=5, depthshade=False)

    # Text panel (right side)
    ax_text = fig.add_subplot(122)
    ax_text.axis("off")
    info_text = ax_text.text(
        0.05, 0.95, "Waiting for data...",
        transform=ax_text.transAxes,
        verticalalignment="top",
        fontfamily="monospace",
        fontsize=10,
    )

    # Command buttons
    ax_btn_zero = fig.add_axes([0.41, 0.02, 0.12, 0.05])
    btn_zero = Button(ax_btn_zero, "Zero")

    ax_btn_ping = fig.add_axes([0.55, 0.02, 0.12, 0.05])
    btn_ping = Button(ax_btn_ping, "Ping")

    def on_zero(_event):
        store.send_zero()

    def on_ping(_event):
        store.send_ping()

    btn_zero.on_clicked(on_zero)
    btn_ping.on_clicked(on_ping)

    # Animation callback — runs at ~10 Hz
    def update(_frame):
        frames = store.snapshot()

        if frames:
            xs = np.asarray([f.x_mm for f in frames], dtype=float)
            ys = np.asarray([f.y_mm for f in frames], dtype=float)
            zs = np.asarray([f.z_mm for f in frames], dtype=float)

            trajectory.set_data(xs, ys)
            trajectory.set_3d_properties(zs)
            points._offsets3d = (xs, ys, zs)
            points.set_array(np.arange(len(xs), dtype=float))
            latest_point._offsets3d = ([xs[-1]], [ys[-1]], [zs[-1]])

            span = max(float(np.ptp(xs)), float(np.ptp(ys)), float(np.ptp(zs)), 200.0)
            half = span * 0.6
            ax3d.set_xlim(xs[-1] - half, xs[-1] + half)
            ax3d.set_ylim(ys[-1] - half, ys[-1] + half)
            ax3d.set_zlim(zs[-1] - half, zs[-1] + half)
        else:
            trajectory.set_data([], [])
            trajectory.set_3d_properties([])
            points._offsets3d = ([], [], [])
            latest_point._offsets3d = ([], [], [])

        status = store.get_runtime_status()
        latest = frames[-1] if frames else None
        if latest is None:
            text = (
                "Latest reading\n"
                "------------------------\n"
                "  waiting for DATA frames\n"
                "------------------------\n"
                f"  Connected = {'YES' if status['connected'] else 'NO'}\n"
                f"  Link      = {status['connection_info']}\n"
                f"  Last info = {status['last_info']}\n"
                f"  Last cmd  = {status['last_command_status']}\n"
                f"  Last err  = {status['last_error']}\n"
            )
        else:
            text = (
                "Latest reading\n"
                "------------------------\n"
                f"  X      = {latest.x_mm:+10.1f} mm\n"
                f"  Y      = {latest.y_mm:+10.1f} mm\n"
                f"  Z      = {latest.z_mm:+10.1f} mm\n"
                "------------------------\n"
                f"  R      = {latest.r_mm:10.1f} mm\n"
                f"  Theta  = {latest.theta_deg:+10.2f} deg\n"
                f"  Phi    = {latest.phi_deg:10.2f} deg\n"
                "------------------------\n"
                f"  Valid  = {'YES' if latest.is_valid else 'NO':>8}\n"
                f"  Frame  = {latest.frame_count:>8}\n"
                f"  t      = {latest.ts_ms:>8} ms\n"
                f"  Points = {len(frames):>8}\n"
                "------------------------\n"
                f"  Connected = {'YES' if status['connected'] else 'NO'}\n"
                f"  Link      = {status['connection_info']}\n"
                f"  Last info = {status['last_info']}\n"
                f"  Last cmd  = {status['last_command_status']}\n"
                f"  Last err  = {status['last_error']}\n"
            )
        info_text.set_text(text)

    interval_ms = int(max(1.0, 1000.0 / max(1.0, fps)))
    ani = animation.FuncAnimation(fig, update, interval=interval_ms, cache_frame_data=False)

    plt.tight_layout()
    plt.show()

    # Keep reference so GC doesn't collect the animation
    _ = ani
