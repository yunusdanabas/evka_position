"""transform.py — Load and apply a sensor-to-world calibration transform.

When firmware-authoritative spherical display is enabled, only XYZ values are
transformed during visualization; firmware R/theta/phi are preserved.
"""

import json
import logging
import math
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def load_calibration(path: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """Load R (3x3) and t (3,) from a calibration JSON file.

    Returns (R, t) on success, or None if the file is missing/invalid.
    """
    try:
        with open(path) as f:
            data = json.load(f)
        R = np.array(data["R"], dtype=float)
        t = np.array(data["t"], dtype=float)
        if R.shape != (3, 3) or t.shape != (3,):
            raise ValueError("Unexpected shape in calibration JSON")
        return R, t
    except (FileNotFoundError, KeyError, ValueError) as exc:
        logger.warning("Could not load calibration from %s: %s", path, exc)
        return None


def apply_transform(
    x: float, y: float, z: float,
    R: np.ndarray, t: np.ndarray,
) -> Tuple[float, float, float]:
    """Apply world_pos = R @ sensor_pos + t.

    Returns (x_world, y_world, z_world).
    """
    p = R @ np.array([x, y, z], dtype=float) + t
    return float(p[0]), float(p[1]), float(p[2])


def cartesian_to_spherical(x: float, y: float, z: float):
    """Convert (x, y, z) mm → (r_mm, theta_deg, phi_deg).

    Uses the same elevation-azimuth convention as the firmware.
    """
    r = math.sqrt(x**2 + y**2 + z**2)
    if r < 1e-6:
        return 0.0, 0.0, 0.0
    theta = math.degrees(math.atan2(y, x))
    phi = math.degrees(math.asin(max(-1.0, min(1.0, z / r))))
    return r, theta, phi


def spherical_to_cartesian(r: float, theta_deg: float, phi_deg: float):
    """Convert (r_mm, theta_deg, phi_deg) → (x_mm, y_mm, z_mm).

    Uses the same elevation-azimuth convention as the firmware:
      x = r * cos(phi) * cos(theta)
      y = r * cos(phi) * sin(theta)
      z = r * sin(phi)
    phi = -90° arm down, 0° horizontal, +90° arm up.
    theta = azimuth from +X in XY-plane.
    """
    theta_rad = math.radians(theta_deg)
    phi_rad = math.radians(phi_deg)
    x = r * math.cos(phi_rad) * math.cos(theta_rad)
    y = r * math.cos(phi_rad) * math.sin(theta_rad)
    z = r * math.sin(phi_rad)
    return x, y, z
