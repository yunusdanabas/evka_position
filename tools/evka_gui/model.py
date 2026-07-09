"""model.py — pure (Qt-free) parsing/dispatch + trail buffer for evka_gui."""

from __future__ import annotations

import math
from collections import deque, namedtuple
from dataclasses import dataclass
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

Update = namedtuple("Update", ["kind", "data"])
Batt = namedtuple("Batt", ["voltage", "pct", "is_low"])
SysInfo = namedtuple("SysInfo", ["rssi", "heap", "uptime_s", "tcp_clients"])
CalWire = namedtuple("CalWire", ["factor", "mm_per_pulse", "ppr_wire"])
CalRotary = namedtuple("CalRotary", ["counts", "ppr", "axis"])


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
            return CalWire(float(parts[0]), float(parts[1]), float(parts[2]))
        except ValueError:
            return None
    if body.startswith("THETA,"):
        parts = body[6:].split(",")
        if len(parts) != 2:
            return None
        try:
            return CalRotary(int(parts[0]), float(parts[1]), "theta")
        except ValueError:
            return None
    if body.startswith("PHI,"):
        parts = body[4:].split(",")
        if len(parts) != 2:
            return None
        try:
            return CalRotary(int(parts[0]), float(parts[1]), "phi")
        except ValueError:
            return None
    return None


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
        return [Update("constants", line[len(CONSTANTS_PREFIX):])]

    if line.startswith(REMOTE_BTN_PREFIX):
        try:
            idx = int(line[len(REMOTE_BTN_PREFIX):])
        except ValueError:
            return []
        return [Update("remote_btn", idx)]

    if line == REMOTE_HB_PREFIX:
        return [Update("remote_hb", None)]

    if line.startswith(POINT_PREFIX):
        return [Update("point", line)]

    if line.startswith(DEL_POINT_PREFIX):
        return [Update("del_point", line)]

    if line.startswith(ACK_PREFIX):
        return [Update("ack", line)]

    if line.startswith(ERR_PREFIX):
        return [Update("err", line)]

    if line.startswith(STA_IP_PREFIX):
        return [Update("sta_ip", line[len(STA_IP_PREFIX):])]

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
