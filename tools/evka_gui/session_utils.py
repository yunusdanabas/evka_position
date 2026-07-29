"""session_utils.py — pure helpers for snapshots, saved points, and connection profiles."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

SnapshotRow = Tuple[int, float, float, float, str]
SavedPointRow = Tuple[str, float, float, float]


def format_data_line(
    x: float, y: float, z: float,
    r: float, theta: float, phi: float,
    is_valid: bool, frame_count: int, ts_ms: int,
) -> str:
    """Serialise one frame as a firmware ``DATA,`` line.

    This is the recording format, and it is deliberately not a new one:
    ``load_replay_frames`` (tools/position_checker/replay_reader.py) already reads a
    dump of raw ``DATA,`` lines. So a recording made on any transport — or in the web
    dashboard on a phone — replays on the desktop with no conversion.

    Field order is fixed by the firmware (``EvkaPosition.cpp``); do not reorder.
    """
    return (
        f"DATA,{x:.2f},{y:.2f},{z:.2f},"
        f"{r:.2f},{theta:.3f},{phi:.3f},"
        f"{1 if is_valid else 0},{frame_count},{ts_ms}"
    )


def format_snapshot_row(index: int, x: float, y: float, z: float) -> SnapshotRow:
    ts = datetime.now().strftime("%H:%M:%S")
    return (index, x, y, z, ts)


def snapshots_to_csv_rows(snapshots: Sequence[SnapshotRow]) -> List[List[str]]:
    rows = [["#", "X_mm", "Y_mm", "Z_mm", "Time"]]
    for idx, x, y, z, ts in snapshots:
        rows.append([str(idx), f"{x:.3f}", f"{y:.3f}", f"{z:.3f}", ts])
    return rows


def write_snapshots_csv(path: str, snapshots: Sequence[SnapshotRow]) -> int:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerows(snapshots_to_csv_rows(snapshots))
    return len(snapshots)


def saved_points_to_csv_rows(
    points: Sequence[SavedPointRow],
    origin: Optional[Tuple[float, float, float]] = None,
) -> List[List[str]]:
    rows = [["label", "x_mm", "y_mm", "z_mm", "rel_x_mm", "rel_y_mm", "rel_z_mm"]]
    ox, oy, oz = origin or (0.0, 0.0, 0.0)
    if origin is not None:
        rows.append(["ORIGIN", f"{ox:.3f}", f"{oy:.3f}", f"{oz:.3f}", "0.000", "0.000", "0.000"])
    for idx, x, y, z in points:
        rows.append([
            f"P{idx}", f"{x:.3f}", f"{y:.3f}", f"{z:.3f}",
            f"{x - ox:.3f}", f"{y - oy:.3f}", f"{z - oz:.3f}",
        ])
    return rows


def write_saved_points_csv(
    path: str,
    points: Sequence[SavedPointRow],
    origin: Optional[Tuple[float, float, float]] = None,
) -> int:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerows(saved_points_to_csv_rows(points, origin))
    return len(points)


def format_constants_strip(line: str) -> str:
    parts = [p.strip() for p in line.split(",") if p.strip()]
    if len(parts) >= 4:
        return f"PPR_rot={parts[0]} · PPR_wire={parts[1]} · mm/pulse={parts[2]} · deg/pulse={parts[3]}"
    return line


def format_raw_counts_line(line: str) -> str:
    parts = [p.strip() for p in line.split(",") if p.strip()]
    if len(parts) >= 3:
        return f"θ={parts[0]} · φ={parts[1]} · wire={parts[2]}"
    return line


def profile_key(name: str) -> str:
    return f"profiles/{name}"


def save_profile(settings, name: str, data: Dict[str, Any]) -> None:
    settings.setValue(profile_key(name), json.dumps(data))


def load_profile(settings, name: str) -> Optional[Dict[str, Any]]:
    raw = settings.value(profile_key(name))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def list_profiles(settings) -> List[str]:
    settings.beginGroup("profiles")
    names = settings.childKeys()
    settings.endGroup()
    return sorted(names)


def delete_profile(settings, name: str) -> None:
    settings.remove(profile_key(name))


def replay_seek_indices(total: int, target: int) -> int:
    """Clamp replay index to [0, total]."""
    return max(0, min(target, total))
