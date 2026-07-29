"""model.py — pure (Qt-free) parsing/dispatch + trail buffer for evka_gui."""

from __future__ import annotations

import math
from collections import deque, namedtuple
from dataclasses import dataclass
from ipaddress import ip_address
from typing import List, Optional

import numpy as np

from tools.position_checker.cmd_main import (
    ACK_PREFIX,
    DATA_PREFIX,
    DEL_POINT_PREFIX,
    ERR_PREFIX,
    POINT_PREFIX,
    REMOTE_BTN_PREFIX,
    REMOTE_HB_PREFIX,
    SENSOR_PREFIX,
    STA_IP_PREFIX,
    SYSINFO_PREFIX,
    XYZ_PREFIX,
)
from tools.position_checker.parser import (
    parse_line,
    parse_sensor_line,
    parse_xyz_line,
)

BATT_PREFIX = "BATT,"
CAL_PREFIX = "CAL:"
CONSTANTS_PREFIX = "CONSTANTS,"
RAW_PREFIX = "RAW,"
STATUS_PREFIX = "STATUS,"

def is_frame_line(line: str) -> bool:
    """True for the 20 Hz position-stream lines (``DATA,`` / ``X..,Y..,Z..`` / ``SENSOR,``).

    These are the only lines FREEZE suppresses — command replies (ACK/ERR/POINT/…)
    must keep flowing while frozen, matching the web dashboard, which gates
    ``frozen`` inside the ``DATA,`` branch alone.
    """
    return line.startswith((DATA_PREFIX, XYZ_PREFIX, SENSOR_PREFIX))


Update = namedtuple("Update", ["kind", "data"])
Batt = namedtuple("Batt", ["voltage", "pct", "is_low"])
SysInfo = namedtuple("SysInfo", ["rssi", "heap", "uptime_s", "tcp_clients"])
CalWire = namedtuple("CalWire", ["factor", "mm_per_pulse", "ppr_wire"])
CalRotary = namedtuple("CalRotary", ["counts", "ppr", "axis"])
Status = namedtuple(
    "Status", ["valid", "frame", "ts_ms", "r", "theta", "phi", "x", "y", "z"]
)


def command_response_matches(command: str, response: str) -> bool:
    """Return whether a protocol line completes a specific command."""
    cmd = command.strip().upper()
    line = response.strip().upper()
    op = cmd.split(maxsplit=1)[0] if cmd else ""

    if line.startswith(ERR_PREFIX):
        if line == "ERR:UNKNOWN_CMD":
            return op == "BLINK"
        expected_error = {
            "CAL_W": "ERR:CAL_W",
            "CAL_T": "ERR:CAL_T",
            "CAL_P": "ERR:CAL_P",
            "SET_PPR_ROTARY": "ERR:SET_PPR_ROTARY",
            "SET_PPR_WIRE": "ERR:SET_PPR_WIRE",
            "SAVE_PPR": "ERR:SAVE_PPR_FAILED",
            "DEL_POINT": "ERR:NO_POINTS",
        }.get(op)
        if expected_error is not None:
            return line.startswith(expected_error)
        if cmd.startswith("WIFI_SET:"):
            return line.startswith((
                "ERR:WIFI_CFG_", "ERR:WIFI_INVALID", "ERR:WIFI_SAVE_",
                "ERR:SSID_", "ERR:PASS_",
            ))
        return False

    ppr_prefix = {
        "SET_PPR_ROTARY": "ACK:PPR_ROTARY,",
        "SET_PPR_WIRE": "ACK:PPR_WIRE,",
    }.get(op)
    if ppr_prefix:
        if not line.startswith(ppr_prefix) or " " not in cmd:
            return False
        try:
            requested = float(cmd.split(maxsplit=1)[1])
            applied = float(line[len(ppr_prefix):])
        except ValueError:
            return False
        return math.isclose(requested, applied, abs_tol=0.011)

    if cmd.startswith("WIFI_SET:"):
        return line == "ACK:WIFI_SAVED"

    if op == "STATUS":
        return parse_status_line(line) is not None
    if op == "SYSINFO":
        return parse_sysinfo_line(line) is not None
    if op == "GET_IP":
        return parse_sta_ip_line(line) is not None
    if op == "CONSTANTS":
        return parse_constants_line(line) is not None
    if op == "RAW_COUNTS":
        return parse_raw_line(line) is not None
    if op in ("CAL_W", "CAL_T", "CAL_P"):
        cal = parse_cal_line(line)
        return (
            (op == "CAL_W" and isinstance(cal, CalWire))
            or (op == "CAL_T" and isinstance(cal, CalRotary) and cal.axis == "theta")
            or (op == "CAL_P" and isinstance(cal, CalRotary) and cal.axis == "phi")
        )
    if op == "SAVE_POINT":
        return parse_point_line(line) is not None
    if op == "DEL_POINT":
        return parse_del_point_line(line) is not None
    expected = {
        "PING": "ACK:PONG",
        "SAVE_PPR": "ACK:SAVE_PPR",
    }.get(op)
    if expected is not None:
        return line == expected
    return bool(op) and line == f"ACK:{op}"


def parse_batt_line(line: str) -> Optional[Batt]:
    line = line.strip()
    if not line.startswith(BATT_PREFIX):
        return None
    parts = line[len(BATT_PREFIX):].split(",")
    if len(parts) != 3:
        return None
    try:
        voltage = float(parts[0])
        pct = int(parts[1])
        is_low = bool(int(parts[2]))
    except ValueError:
        return None
    if not math.isfinite(voltage):
        return None
    return Batt(voltage, pct, is_low)


def parse_sysinfo_line(line: str) -> Optional[SysInfo]:
    line = line.strip()
    if not line.startswith(SYSINFO_PREFIX):
        return None
    parts = line[len(SYSINFO_PREFIX):].split(",")
    if len(parts) < 3:
        return None
    try:
        rssi = int(parts[0])
        heap = int(parts[1])
        uptime = int(parts[2])
        tcp = int(parts[3]) if len(parts) >= 4 else 0
    except ValueError:
        return None
    return SysInfo(rssi, heap, uptime, tcp)


def parse_status_line(line: str) -> Optional[Status]:
    line = line.strip()
    if not line.startswith(STATUS_PREFIX):
        return None
    parts = line[len(STATUS_PREFIX):].split(",")
    if len(parts) < 9:
        return None
    try:
        valid = int(parts[0])
        frame = int(parts[1])
        ts_ms = int(parts[2])
        r, theta, phi, x, y, z = (float(value) for value in parts[3:9])
    except ValueError:
        return None
    if valid not in (0, 1) or not all(math.isfinite(v) for v in (r, theta, phi, x, y, z)):
        return None
    return Status(bool(valid), frame, ts_ms, r, theta, phi, x, y, z)


def parse_cal_line(line: str):
    line = line.strip()
    if not line.startswith(CAL_PREFIX):
        return None
    body = line[len(CAL_PREFIX):]
    if body.startswith("WIRE,"):
        parts = body[5:].split(",")
        if len(parts) != 3:
            return None
        try:
            values = tuple(float(value) for value in parts)
        except ValueError:
            return None
        if not all(math.isfinite(value) and value > 0 for value in values):
            return None
        return CalWire(*values)
    if body.startswith("THETA,"):
        parts = body[6:].split(",")
        if len(parts) != 2:
            return None
        try:
            counts, ppr = int(parts[0]), float(parts[1])
        except ValueError:
            return None
        return CalRotary(counts, ppr, "theta") if math.isfinite(ppr) and ppr > 0 else None
    if body.startswith("PHI,"):
        parts = body[4:].split(",")
        if len(parts) != 2:
            return None
        try:
            counts, ppr = int(parts[0]), float(parts[1])
        except ValueError:
            return None
        return CalRotary(counts, ppr, "phi") if math.isfinite(ppr) and ppr > 0 else None
    return None


def parse_constants_line(line: str) -> Optional[str]:
    line = line.strip()
    if not line.startswith(CONSTANTS_PREFIX):
        return None
    body = line[len(CONSTANTS_PREFIX):]
    parts = body.split(",")
    try:
        values = [float(value) for value in parts]
    except ValueError:
        return None
    if len(values) != 4 or not all(math.isfinite(value) and value > 0 for value in values):
        return None
    return body


def parse_raw_line(line: str) -> Optional[str]:
    line = line.strip()
    if not line.startswith(RAW_PREFIX):
        return None
    body = line[len(RAW_PREFIX):]
    parts = body.split(",")
    if len(parts) != 3:
        return None
    try:
        [int(value) for value in parts]
    except ValueError:
        return None
    return body


def parse_sta_ip_line(line: str) -> Optional[str]:
    line = line.strip()
    if not line.startswith(STA_IP_PREFIX):
        return None
    value = line[len(STA_IP_PREFIX):].strip()
    if value in ("NOT_CONNECTED", "BAGLI_DEGIL"):
        return value
    try:
        address = ip_address(value)
    except ValueError:
        return None
    return value if address.version == 4 else None


def parse_point_line(line: str) -> Optional[str]:
    line = line.strip()
    if not line.startswith(POINT_PREFIX):
        return None
    parts = line[len(POINT_PREFIX):].split(",")
    if len(parts) < 4:
        return None
    try:
        int(parts[0])
        values = [float(value) for value in parts[1:]]
    except ValueError:
        return None
    return line if all(math.isfinite(value) for value in values) else None


def parse_del_point_line(line: str) -> Optional[str]:
    line = line.strip()
    if not line.startswith(DEL_POINT_PREFIX):
        return None
    try:
        int(line[len(DEL_POINT_PREFIX):])
    except ValueError:
        return None
    return line


def ingest_line(line: str) -> List[Update]:
    line = line.strip()
    if not line:
        return []

    if line.startswith(DATA_PREFIX):
        f = parse_line(line)
        if f is None:
            return []
        return [
            Update("position", (f.x_mm, f.y_mm, f.z_mm)),
            Update("sensor", (f.r_mm, f.theta_deg, f.phi_deg, f.is_valid, f.frame_count)),
            Update("ts", f.ts_ms),
        ]

    if line.startswith(STATUS_PREFIX):
        status = parse_status_line(line)
        if status is None:
            return []
        return [
            Update("position", (status.x, status.y, status.z)),
            Update("sensor", (
                status.r, status.theta, status.phi, status.valid, status.frame,
            )),
            Update("ts", status.ts_ms),
        ]

    if line.startswith(SENSOR_PREFIX):
        s = parse_sensor_line(line)
        if s is None:
            return []
        return [Update("sensor", (s.r_mm, s.theta_deg, s.phi_deg, s.is_valid, s.frame_count))]

    if line.startswith(BATT_PREFIX):
        b = parse_batt_line(line)
        return [Update("batt", b)] if b is not None else []

    if line.startswith(SYSINFO_PREFIX):
        si = parse_sysinfo_line(line)
        return [Update("sysinfo", si)] if si is not None else []

    if line.startswith(CAL_PREFIX):
        cal = parse_cal_line(line)
        return [Update("cal", cal)] if cal is not None else []

    if line.startswith(CONSTANTS_PREFIX):
        constants = parse_constants_line(line)
        return [Update("constants", constants)] if constants is not None else []

    if line.startswith(RAW_PREFIX):
        raw = parse_raw_line(line)
        return [Update("raw_counts", raw)] if raw is not None else []

    if line.startswith(REMOTE_BTN_PREFIX):
        try:
            idx = int(line[len(REMOTE_BTN_PREFIX):])
        except ValueError:
            return []
        return [Update("remote_btn", idx)]

    if line == REMOTE_HB_PREFIX:
        return [Update("remote_hb", None)]

    if line.startswith(POINT_PREFIX):
        point = parse_point_line(line)
        return [Update("point", point)] if point is not None else []

    if line.startswith(DEL_POINT_PREFIX):
        deleted = parse_del_point_line(line)
        return [Update("del_point", deleted)] if deleted is not None else []

    if line.startswith(ACK_PREFIX):
        return [Update("ack", line)]

    if line.startswith(ERR_PREFIX):
        return [Update("err", line)]

    if line.startswith(STA_IP_PREFIX):
        ip = parse_sta_ip_line(line)
        return [Update("sta_ip", ip)] if ip is not None else []

    if line.startswith(XYZ_PREFIX):
        xyz = parse_xyz_line(line)
        if xyz is None:
            return []
        return [Update("position", (xyz.x_mm, xyz.y_mm, xyz.z_mm))]

    return []


class TrailBuffer:
    def __init__(self, maxlen: int = 800):
        self._pts: deque = deque(maxlen=maxlen)

    def add(self, x: float, y: float, z: float) -> None:
        self._pts.append((x, y, z))

    def clear(self) -> None:
        self._pts.clear()

    def __len__(self) -> int:
        return len(self._pts)

    def xs(self) -> np.ndarray:
        return np.array([p[0] for p in self._pts], dtype=float)

    def ys(self) -> np.ndarray:
        return np.array([p[1] for p in self._pts], dtype=float)

    def zs(self) -> np.ndarray:
        return np.array([p[2] for p in self._pts], dtype=float)

    def points(self) -> list:
        return list(self._pts)


@dataclass
class UiState:
    trail: TrailBuffer
    last_hb: Optional[float] = None
    battery_seen: bool = False
    saved_points: int = 0
    is_valid: Optional[bool] = None

    def reset(self) -> None:
        self.trail.clear()
        self.last_hb = None
        self.battery_seen = False
        self.saved_points = 0
        self.is_valid = None
