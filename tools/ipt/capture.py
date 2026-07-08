"""capture.py — armed point-cloud buffer for IPT sweeps.

Accumulates Cartesian (x, y, z) attachment points while a sweep is active. All
state is intended to live on the GUI thread: transports run on daemon threads, so
the GUI must hand raw lines / frames to this buffer from inside its QTimer drain
(never call these methods from a transport callback directly).

Transport wrinkle (firmware-specific): over the raw TCP CMD server the firmware
sends position and validity as SEPARATE lines — "X..,Y..,Z.." then "SENSOR,..."
each cycle (CmdTcpServer.cpp). So `ingest_line` pairs each XYZ line with the
following SENSOR line to recover validity. Over serial the firmware sends one full
"DATA,..." line per cycle, parsed to a ParsedFrame that already carries is_valid;
feed those via `ingest_frame`.
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

import numpy as np

from tools.position_checker.parser import (
    ParsedFrame,
    parse_sensor_line,
    parse_xyz_line,
)

# 20 Hz emits many near-identical frames when the handle is momentarily still;
# accept a new point only after it has moved at least this far (dedup).
DEFAULT_MIN_DISP_MM = 1.0


class IptCapture:
    def __init__(self, min_disp_mm: float = DEFAULT_MIN_DISP_MM) -> None:
        self._armed = False
        self._pts: List[Tuple[float, float, float]] = []
        self._last: Optional[Tuple[float, float, float]] = None
        self._min_disp_sq = float(min_disp_mm) ** 2
        # TCP correlation state: stash the latest XYZ until its SENSOR line arrives.
        self._pending_xyz: Optional[Tuple[float, float, float]] = None

    # ---- control ----
    def arm(self) -> None:
        self._armed = True

    def disarm(self) -> None:
        self._armed = False
        self._pending_xyz = None

    def is_armed(self) -> bool:
        return self._armed

    def clear(self) -> None:
        self._pts.clear()
        self._last = None
        self._pending_xyz = None

    # ---- readout ----
    def count(self) -> int:
        return len(self._pts)

    def points(self) -> np.ndarray:
        return np.asarray(self._pts, dtype=float).reshape(-1, 3)

    # ---- ingest ----
    def _accept(self, x: float, y: float, z: float) -> bool:
        """Add a point if armed and it has moved far enough from the last one."""
        if not self._armed:
            return False
        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
            return False
        if self._last is not None:
            dx = x - self._last[0]
            dy = y - self._last[1]
            dz = z - self._last[2]
            if dx * dx + dy * dy + dz * dz < self._min_disp_sq:
                return False
        p = (x, y, z)
        self._pts.append(p)
        self._last = p
        return True

    def ingest_frame(self, frame: ParsedFrame) -> bool:
        """Serial path: a parsed DATA frame (already validated/finite). DataStore
        drops is_valid==0, but check defensively in case the caller bypasses it."""
        if not frame.is_valid:
            return False
        return self._accept(frame.x_mm, frame.y_mm, frame.z_mm)

    def ingest_line(self, line: str) -> bool:
        """TCP path: one raw protocol line. XYZ lines are stashed; the recovered
        point is committed when the matching (valid) SENSOR line follows."""
        xyz = parse_xyz_line(line)
        if xyz is not None:
            self._pending_xyz = (xyz.x_mm, xyz.y_mm, xyz.z_mm)
            return False
        sensor = parse_sensor_line(line)
        if sensor is not None:
            pending = self._pending_xyz
            self._pending_xyz = None
            if sensor.is_valid and pending is not None:
                return self._accept(*pending)
        return False
