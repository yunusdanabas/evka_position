#!/usr/bin/env python3
"""cmd_main.py — canonical visualizer conventions + CMD GUI entry point.

This module is the single source of truth for cross-visualizer protocol and
display conventions used in Python visualizer tools.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from typing import Dict, Tuple

# -----------------------------------------------------------------------------
# Firmware stream contract (authoritative)
# -----------------------------------------------------------------------------

DATA_PREFIX = "DATA,"
SENSOR_PREFIX = "SENSOR,"
XYZ_PREFIX = "X"
STA_IP_PREFIX = "STA_IP:"
SYSINFO_PREFIX = "SYSINFO,"
ACK_PREFIX = "ACK:"
ERR_PREFIX = "ERR:"

DATA_FIELDS: Tuple[str, ...] = (
    "x_mm",
    "y_mm",
    "z_mm",
    "r_mm",
    "theta_deg",
    "phi_deg",
    "is_valid",
    "frame_count",
    "ts_ms",
)
SENSOR_FIELDS: Tuple[str, ...] = ("r_mm", "theta_deg", "phi_deg", "is_valid", "frame_count")

FIRMWARE_PHI_AUTHORITATIVE = True

# Firmware pin map metadata for visualizer labels/help text consistency.
PIN_MAP: Dict[str, int] = {
    "theta_a": 14,
    "theta_b": 12,
    "phi_a": 32,
    "phi_b": 35,
    "wire_a": 16,
    "wire_b": 17,
}

# CMD/TCP defaults
CMD_DEFAULT_STA_IP = "192.168.1.84"
CMD_AP_FALLBACK_IP = "192.168.1.50"
CMD_DEFAULT_PORT = 8080


@dataclass(frozen=True)
class VisualizerConventions:
    """Shared conventions consumed by Python visualizers."""

    data_prefix: str = DATA_PREFIX
    sensor_prefix: str = SENSOR_PREFIX
    xyz_prefix: str = XYZ_PREFIX
    data_fields: Tuple[str, ...] = DATA_FIELDS
    sensor_fields: Tuple[str, ...] = SENSOR_FIELDS
    firmware_phi_authoritative: bool = FIRMWARE_PHI_AUTHORITATIVE
    pin_map: Dict[str, int] = field(default_factory=lambda: dict(PIN_MAP))


def get_visualizer_conventions() -> VisualizerConventions:
    return VisualizerConventions()


def main() -> None:
    from .cmd_gui import run_cmd_gui  # Local import avoids circular dependency.

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    code = run_cmd_gui()
    if code:
        sys.exit(code)


if __name__ == "__main__":
    main()
