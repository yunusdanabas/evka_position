"""gui.py — 3-D scatter plot + text panel + Zero button, updated at 10 Hz."""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button

from .data_store import DataStore


def run_gui(store: DataStore) -> None:
    """Open the position checker window.  Blocks until the window is closed."""

    fig = plt.figure(figsize=(10, 7))
    fig.suptitle("Spherical 3D Position Checker", fontsize=13)

    # 3-D scatter axes
    ax3d = fig.add_subplot(121, projection="3d")
    ax3d.set_xlabel("X (mm)")
    ax3d.set_ylabel("Y (mm)")
    ax3d.set_zlabel("Z (mm)")
    ax3d.set_title("Trajectory")

    scatter = [None]  # mutable reference so inner functions can replace it

    # Text panel (right side)
    ax_text = fig.add_subplot(122)
    ax_text.axis("off")
    info_text = ax_text.text(
        0.05, 0.95, "Waiting for data…",
        transform=ax_text.transAxes,
        verticalalignment="top",
        fontfamily="monospace",
        fontsize=10,
    )

    # Zero button
    ax_btn = fig.add_axes([0.45, 0.02, 0.12, 0.05])
    btn_zero = Button(ax_btn, "Zero")

    def on_zero(_event):
        ok = store.send_zero()
        status = "ZERO sent" if ok else "Serial not connected"
        print(f"[GUI] {status}")

    btn_zero.on_clicked(on_zero)

    # Animation callback — runs at ~10 Hz
    def update(_frame):
        frames = store.snapshot()
        if not frames:
            return

        xs = [f.x_mm for f in frames]
        ys = [f.y_mm for f in frames]
        zs = [f.z_mm for f in frames]

        # Rebuild scatter (simplest approach; adequate at 10 Hz)
        ax3d.cla()
        ax3d.set_xlabel("X (mm)")
        ax3d.set_ylabel("Y (mm)")
        ax3d.set_zlabel("Z (mm)")
        ax3d.set_title("Trajectory")
        ax3d.scatter(xs, ys, zs, c=range(len(xs)), cmap="viridis", s=10)
        ax3d.scatter([xs[-1]], [ys[-1]], [zs[-1]], c="red", s=60, zorder=5)

        # Update text panel with latest frame
        latest = frames[-1]
        text = (
            f"Latest reading\n"
            f"{'─'*24}\n"
            f"  X    = {latest.x_mm:+10.1f} mm\n"
            f"  Y    = {latest.y_mm:+10.1f} mm\n"
            f"  Z    = {latest.z_mm:+10.1f} mm\n"
            f"{'─'*24}\n"
            f"  R    = {latest.r_mm:10.1f} mm\n"
            f"  θ    = {latest.theta_deg:+10.2f}°\n"
            f"  φ    = {latest.phi_deg:10.2f}°\n"
            f"{'─'*24}\n"
            f"  Valid  = {'YES' if latest.is_valid else 'NO':>8}\n"
            f"  Frame  = {latest.frame_count:>8}\n"
            f"  t      = {latest.ts_ms:>8} ms\n"
            f"  Points = {len(frames):>8}\n"
        )
        info_text.set_text(text)

    ani = animation.FuncAnimation(fig, update, interval=100, cache_frame_data=False)

    plt.tight_layout()
    plt.show()

    # Keep reference so GC doesn't collect the animation
    _ = ani
