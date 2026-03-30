"""transform.py — Load and apply a sensor-to-world calibration transform."""

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
