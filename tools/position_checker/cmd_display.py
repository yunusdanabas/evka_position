"""cmd_display.py — testable display-offset logic for the CMD TCP GUI."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Tuple

from .transform import cartesian_to_spherical

# Default axis colors for valid positions (match cmd_gui).
AXIS_COLORS = {"x": "#ff4444", "y": "#44ff44", "z": "#4488ff"}
AXIS_INVALID_COLOR = "#666666"

STA_NOT_CONNECTED = frozenset({"NOT_CONNECTED", "BAGLI_DEGIL"})


@dataclass
class CmdDisplayState:
    """Client-side display frame: offsets, min/max, validity."""

    offset_x: float = 0.0
    offset_y: float = 0.0
    offset_z: float = 0.0
    relative_zero_active: bool = False
    last_raw_x: float = 0.0
    last_raw_y: float = 0.0
    last_raw_z: float = 0.0
    is_valid: Optional[bool] = None
    min_vals: dict[str, float] = field(
        default_factory=lambda: {"x": math.inf, "y": math.inf, "z": math.inf}
    )
    max_vals: dict[str, float] = field(
        default_factory=lambda: {"x": -math.inf, "y": -math.inf, "z": -math.inf}
    )

    def apply_offsets(self, raw_x: float, raw_y: float, raw_z: float) -> Tuple[float, float, float]:
        if self.relative_zero_active:
            return (
                raw_x - self.offset_x,
                raw_y - self.offset_y,
                raw_z - self.offset_z,
            )
        return raw_x, raw_y, raw_z

    def update_minmax(self, x: float, y: float, z: float) -> None:
        for axis, val in [("x", x), ("y", y), ("z", z)]:
            if val < self.min_vals[axis]:
                self.min_vals[axis] = val
            if val > self.max_vals[axis]:
                self.max_vals[axis] = val

    def reset_minmax(self) -> None:
        self.min_vals = {"x": math.inf, "y": math.inf, "z": math.inf}
        self.max_vals = {"x": -math.inf, "y": -math.inf, "z": -math.inf}

    def clear_software_zero(self) -> None:
        self.relative_zero_active = False
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.offset_z = 0.0

    def reset_session_state(self) -> None:
        """Clear software zero and min/max (used on disconnect)."""
        self.clear_software_zero()
        self.reset_minmax()
        self.is_valid = None

    def spherical_for_display(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        return cartesian_to_spherical(x, y, z)

    def format_point_entry(
        self,
        idx: str,
        world_x: float,
        world_y: float,
        world_z: float,
    ) -> str:
        """Format saved point for list; show display frame when SW zero active."""
        if self.relative_zero_active:
            dx, dy, dz = self.apply_offsets(world_x, world_y, world_z)
            return f"#{idx}: {dx:.2f}, {dy:.2f}, {dz:.2f} mm (display)"
        return f"#{idx}: {world_x}, {world_y}, {world_z} mm (world)"


@dataclass(frozen=True)
class PositionDisplay:
    """Computed labels after processing one XYZ frame."""

    x: float
    y: float
    z: float
    r: Optional[float]
    theta: Optional[float]
    phi: Optional[float]
    update_spherical: bool


def process_xyz_frame(
    state: CmdDisplayState,
    raw_x: float,
    raw_y: float,
    raw_z: float,
    *,
    track_minmax: bool = True,
) -> PositionDisplay:
    """Apply offsets, optionally track min/max, return display values."""
    state.last_raw_x = raw_x
    state.last_raw_y = raw_y
    state.last_raw_z = raw_z

    x, y, z = state.apply_offsets(raw_x, raw_y, raw_z)
    if track_minmax:
        state.update_minmax(x, y, z)

    if state.relative_zero_active:
        r, theta, phi = state.spherical_for_display(x, y, z)
        return PositionDisplay(
            x=x, y=y, z=z,
            r=r, theta=theta, phi=phi,
            update_spherical=True,
        )

    return PositionDisplay(
        x=x, y=y, z=z,
        r=None, theta=None, phi=None,
        update_spherical=False,
    )


def process_sensor_line(
    state: CmdDisplayState,
    r_mm: float,
    theta_deg: float,
    phi_deg: float,
    is_valid: int,
    frame_count: int,
) -> Tuple[Optional[Tuple[float, float, float]], bool, int]:
    """Return (r_theta_phi or None, is_valid, frame_count).

    When software zero is active, spherical values from SENSOR are suppressed;
    caller should keep R/θ/φ from the last XYZ-derived display update.
    """
    state.is_valid = bool(is_valid)
    if state.relative_zero_active:
        return None, bool(is_valid), frame_count
    return (r_mm, theta_deg, phi_deg), bool(is_valid), frame_count


def sta_ip_display(ip: str) -> str:
    return "Not Connected" if ip in STA_NOT_CONNECTED else ip


def sta_ip_is_connected(ip: str) -> bool:
    return bool(ip) and ip not in STA_NOT_CONNECTED
