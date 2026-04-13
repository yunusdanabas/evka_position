"""parser.py — parse DATA CSV lines from the firmware serial stream."""

import math
from collections import namedtuple
from typing import Optional

from .cmd_main import (
    ACK_PREFIX,
    DATA_FIELDS,
    DATA_PREFIX,
    DEL_POINT_PREFIX,
    ERR_PREFIX,
    POINT_PREFIX,
    SENSOR_PREFIX,
    STA_IP_PREFIX,
    SYSINFO_PREFIX,
    XYZ_PREFIX,
)

ParsedFrame = namedtuple(
    "ParsedFrame",
    ["x_mm", "y_mm", "z_mm", "r_mm", "theta_deg", "phi_deg",
     "is_valid", "frame_count", "ts_ms"],
)

SensorFrame = namedtuple(
    "SensorFrame",
    ["r_mm", "theta_deg", "phi_deg", "is_valid", "frame_count"],
)
XYZFrame = namedtuple("XYZFrame", ["x_mm", "y_mm", "z_mm"])

_FIELD_COUNT = len(DATA_FIELDS)


def parse_line(line: str) -> Optional[ParsedFrame]:
    """Return a ParsedFrame if *line* is a valid DATA CSV line, else None.

    Expected format (emitted by SphericalSensor.printPosition()):
        DATA,<x>,<y>,<z>,<r>,<theta>,<phi>,<is_valid>,<frame_count>,<ts_ms>
    """
    line = line.strip()
    if not line.startswith(DATA_PREFIX):
        return None
    parts = line[len(DATA_PREFIX):].split(",")
    if len(parts) != _FIELD_COUNT:
        return None
    try:
        frame = ParsedFrame(
            x_mm=float(parts[0]),
            y_mm=float(parts[1]),
            z_mm=float(parts[2]),
            r_mm=float(parts[3]),
            theta_deg=float(parts[4]),
            phi_deg=float(parts[5]),
            is_valid=int(parts[6]),
            frame_count=int(parts[7]),
            ts_ms=int(parts[8]),
        )
        if not all(math.isfinite(v) for v in (frame.x_mm, frame.y_mm, frame.z_mm,
                                               frame.r_mm, frame.theta_deg, frame.phi_deg)):
            return None
        return frame
    except ValueError:
        return None


def parse_sensor_line(line: str) -> Optional[SensorFrame]:
    """Return parsed SENSOR telemetry frame if valid."""
    line = line.strip()
    if not line.startswith(SENSOR_PREFIX):
        return None

    parts = line[len(SENSOR_PREFIX):].split(",")
    if len(parts) < 5:
        return None
    try:
        return SensorFrame(
            r_mm=float(parts[0]),
            theta_deg=float(parts[1]),
            phi_deg=float(parts[2]),
            is_valid=int(parts[3]),
            frame_count=int(parts[4]),
        )
    except ValueError:
        return None


def parse_xyz_line(line: str) -> Optional[XYZFrame]:
    """Return parsed X/Y/Z telemetry line if valid."""
    line = line.strip()
    if not line.startswith(XYZ_PREFIX):
        return None

    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 3:
        return None

    try:
        if not (parts[0].startswith('X') and parts[1].startswith('Y') and parts[2].startswith('Z')):
            return None
        return XYZFrame(
            x_mm=float(parts[0][1:]),
            y_mm=float(parts[1][1:]),
            z_mm=float(parts[2][1:]),
        )
    except ValueError:
        return None


def parse_info_line(line: str) -> Optional[str]:
    """Return human-readable non-DATA status lines, or None.

    Informational lines are routed to GUI/status panels without affecting the
    DATA parser contract.
    """
    clean = line.strip()
    if not clean:
        return None

    info_prefixes = (ACK_PREFIX, "STATUS,", "BATT,", ERR_PREFIX, "!", STA_IP_PREFIX, SYSINFO_PREFIX,
                     POINT_PREFIX, DEL_POINT_PREFIX)
    if clean.startswith(info_prefixes):
        return clean
    return None
