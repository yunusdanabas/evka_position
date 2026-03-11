"""parser.py — parse DATA CSV lines from the firmware serial stream."""

from collections import namedtuple
from typing import Optional

ParsedFrame = namedtuple(
    "ParsedFrame",
    ["x_mm", "y_mm", "z_mm", "r_mm", "theta_deg", "phi_deg",
     "is_valid", "frame_count", "ts_ms"],
)

_PREFIX = "DATA,"
_FIELD_COUNT = 9


def parse_line(line: str) -> Optional[ParsedFrame]:
    """Return a ParsedFrame if *line* is a valid DATA CSV line, else None.

    Expected format (emitted by SphericalSensor.printPosition()):
        DATA,<x>,<y>,<z>,<r>,<theta>,<phi>,<is_valid>,<frame_count>,<ts_ms>
    """
    line = line.strip()
    if not line.startswith(_PREFIX):
        return None
    parts = line[len(_PREFIX):].split(",")
    if len(parts) != _FIELD_COUNT:
        return None
    try:
        return ParsedFrame(
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

    info_prefixes = ("ACK:", "STATUS,", "BATT,", "ERR:", "!")
    if clean.startswith(info_prefixes):
        return clean
    return None
