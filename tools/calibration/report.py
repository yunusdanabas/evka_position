"""Generate the default EVKA calibration report.

Run from the repo root:
    python -m tools.calibration.report

Default inputs/outputs live in docs/calibration/sessions/current/.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from tools.calibration.calibrate import kabsch


def _project_root() -> Path:
    """Repo root when running from source; a writable user dir when frozen.

    A PyInstaller bundle has no repo root — ``__file__`` points inside the
    (read-only, and on onefile temporary) bundle directory, so calibration
    sessions and the deployed calibration.json would be written somewhere the
    user can neither find nor keep. Redirect those to the platform's per-user
    data directory instead.
    """
    if getattr(sys, "frozen", False):
        base = (
            os.environ.get("LOCALAPPDATA")              # Windows, always set
            or os.environ.get("XDG_DATA_HOME")          # Linux, if configured
            or Path.home() / ".local" / "share"         # Linux default
        )
        # Not bare ~/evka_position: on a dev box where the repo is checked out
        # under $HOME that path is the repo itself, and a frozen build would
        # write user data straight into the working tree.
        return Path(base) / "evka_position"
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _project_root()
DEFAULT_SESSION_DIR = PROJECT_ROOT / "docs" / "calibration" / "sessions" / "current"
CALIBRATION_CSV = "calibration_points.csv"
VALIDATION_CSV = "validation_points.csv"
GENERATED_FILES = (
    "report.md",
    "calibration.json",
    "calibration_errors.csv",
    "validation_errors.csv",
)
POINT_FIELDS = [
    "label",
    "world_x",
    "world_y",
    "world_z",
    "sensor_x",
    "sensor_y",
    "sensor_z",
    "notes",
]
# Only the coordinate columns are required; label/notes are optional so CSVs
# exported by the web dashboard (no notes) and evka_gui (coords only) load as-is.
COORD_FIELDS = POINT_FIELDS[1:-1]
CALIBRATION_RMSE_LIMIT_MM = 10.0
VALIDATION_MAX_LIMIT_MM = 15.0


@dataclass(frozen=True)
class PointPair:
    label: str
    world: np.ndarray
    sensor: np.ndarray
    notes: str = ""


@dataclass(frozen=True)
class PointError:
    label: str
    world: np.ndarray
    sensor: np.ndarray
    computed: np.ndarray
    delta: np.ndarray
    error_mm: float
    notes: str = ""


@dataclass(frozen=True)
class ErrorStats:
    n: int
    rmse_mm: float
    mean_mm: float
    max_mm: float
    max_label: str


def calibration_passed(stats: ErrorStats) -> bool:
    return stats.rmse_mm <= CALIBRATION_RMSE_LIMIT_MM


def validation_passed(stats: ErrorStats) -> bool:
    return stats.max_mm <= VALIDATION_MAX_LIMIT_MM


@dataclass(frozen=True)
class GeneratedReport:
    session_dir: Path
    report_md: Path
    calibration_json: Path
    calibration_errors_csv: Path
    validation_errors_csv: Path
    calibration_stats: ErrorStats
    validation_stats: ErrorStats
    calibration_errors: Tuple[PointError, ...]
    validation_errors: Tuple[PointError, ...]

    @property
    def passed(self) -> bool:
        return calibration_passed(self.calibration_stats) and validation_passed(self.validation_stats)


def ensure_templates(session_dir: Path = DEFAULT_SESSION_DIR) -> List[Path]:
    """Create missing default input CSV templates."""
    session_dir.mkdir(parents=True, exist_ok=True)
    created: List[Path] = []
    for name in (CALIBRATION_CSV, VALIDATION_CSV):
        path = session_dir / name
        if path.exists():
            continue
        with path.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(POINT_FIELDS)
        created.append(path)
    return created


def remove_generated_artifacts(session_dir: Path) -> None:
    for name in GENERATED_FILES:
        (session_dir / name).unlink(missing_ok=True)


def load_point_pairs(path: Path) -> List[PointPair]:
    """Load sensor/world point pairs from the standard report CSV format."""
    rows: List[PointPair] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [field for field in COORD_FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(missing)}")

        for row in reader:
            row_number = reader.line_num
            if not any((row.get(field) or "").strip() for field in POINT_FIELDS):
                continue
            try:
                world = np.array([
                    float(row["world_x"]),
                    float(row["world_y"]),
                    float(row["world_z"]),
                ], dtype=float)
                sensor = np.array([
                    float(row["sensor_x"]),
                    float(row["sensor_y"]),
                    float(row["sensor_z"]),
                ], dtype=float)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{path}: row {row_number} has non-numeric coordinates") from exc
            if not np.isfinite(world).all() or not np.isfinite(sensor).all():
                raise ValueError(f"{path}: row {row_number} has non-finite coordinates")
            label = (row.get("label") or f"row{row_number}").strip() or f"row{row_number}"
            rows.append(PointPair(label, world, sensor, (row.get("notes") or "").strip()))
    return rows


def save_point_pairs(path: Path, points: Sequence[PointPair]) -> None:
    """Write point pairs in the standard report CSV format (inverse of load_point_pairs)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(POINT_FIELDS)
        for p in points:
            writer.writerow([
                p.label,
                *(f"{v:.3f}" for v in p.world),
                *(f"{v:.3f}" for v in p.sensor),
                p.notes,
            ])


def save_session_sets(
    session_dir: Path,
    calibration_points: Sequence[PointPair],
    validation_points: Sequence[PointPair],
) -> None:
    """Replace both session CSVs together and restore their prior bytes on failure."""
    session_dir.mkdir(parents=True, exist_ok=True)
    targets = [session_dir / CALIBRATION_CSV, session_dir / VALIDATION_CSV]
    temps = [path.with_name(path.name + ".tmp") for path in targets]
    previous = [path.read_bytes() if path.exists() else None for path in targets]
    try:
        save_point_pairs(temps[0], calibration_points)
        save_point_pairs(temps[1], validation_points)
        for temp, target in zip(temps, targets):
            temp.replace(target)
    except OSError:
        for target, data in zip(targets, previous):
            try:
                if data is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(data)
            except OSError:
                pass
        raise
    finally:
        for temp in temps:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass


def calculate_errors(points: Sequence[PointPair], R: np.ndarray, t: np.ndarray) -> List[PointError]:
    """Apply the transform; delta = computed - world (positive = sensor overshoots)."""
    errors: List[PointError] = []
    for point in points:
        computed = R @ point.sensor + t
        delta = computed - point.world
        errors.append(PointError(
            point.label,
            point.world,
            point.sensor,
            computed,
            delta,
            float(np.linalg.norm(delta)),
            point.notes,
        ))
    return errors


def summarize_errors(errors: Sequence[PointError]) -> ErrorStats:
    if not errors:
        return ErrorStats(0, math.nan, math.nan, math.nan, "")
    vals = np.array([e.error_mm for e in errors], dtype=float)
    max_idx = int(np.argmax(vals))
    return ErrorStats(
        len(errors),
        float(math.sqrt(np.mean(vals * vals))),
        float(np.mean(vals)),
        float(vals[max_idx]),
        errors[max_idx].label,
    )


def repeatability_rows(
    errors: Sequence[PointError],
) -> Tuple[List[Tuple[str, int, float, float, float, float]], List[str]]:
    """Group repeated labels; labels reused for different world points are skipped."""
    groups: Dict[str, List[PointError]] = {}
    for error in errors:
        groups.setdefault(error.label, []).append(error)

    rows: List[Tuple[str, int, float, float, float, float]] = []
    mismatched: List[str] = []
    for label, group in sorted(groups.items()):
        if len(group) < 2:
            continue
        if not all(np.allclose(e.world, group[0].world) for e in group[1:]):
            mismatched.append(label)
            continue
        arr = np.vstack([e.computed for e in group])
        std = np.std(arr, axis=0, ddof=1)
        centroid = np.mean(arr, axis=0)
        spread = float(max(np.linalg.norm(p - centroid) for p in arr))
        rows.append((label, len(group), float(std[0]), float(std[1]), float(std[2]), spread))
    return rows, mismatched


def write_errors_csv(path: Path, errors: Sequence[PointError]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            POINT_FIELDS[:-1]
            + ["computed_x", "computed_y", "computed_z", "err_x", "err_y", "err_z", "error_mm"]
            + POINT_FIELDS[-1:]
        )
        for e in errors:
            writer.writerow([
                e.label,
                f"{e.world[0]:.3f}",
                f"{e.world[1]:.3f}",
                f"{e.world[2]:.3f}",
                f"{e.sensor[0]:.3f}",
                f"{e.sensor[1]:.3f}",
                f"{e.sensor[2]:.3f}",
                f"{e.computed[0]:.3f}",
                f"{e.computed[1]:.3f}",
                f"{e.computed[2]:.3f}",
                f"{e.delta[0]:.3f}",
                f"{e.delta[1]:.3f}",
                f"{e.delta[2]:.3f}",
                f"{e.error_mm:.3f}",
                e.notes,
            ])


def _fmt(value: float) -> str:
    return "n/a" if math.isnan(value) else f"{value:.2f}"


def _md(text: str) -> str:
    """Escape a CSV field for use inside a markdown table cell."""
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _pass_fail(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def write_report_md(
    path: Path,
    session_dir: Path,
    R: np.ndarray,
    t: np.ndarray,
    calibration_stats: ErrorStats,
    validation_stats: ErrorStats,
    calibration_errors: Sequence[PointError],
    validation_errors: Sequence[PointError],
    repeat_rows: Sequence[Tuple[str, int, float, float, float, float]] = (),
    repeat_mismatched: Sequence[str] = (),
    generated_at: Optional[datetime] = None,
) -> None:
    generated_at = generated_at or datetime.now()
    cal_status = _pass_fail(calibration_passed(calibration_stats))
    val_status = _pass_fail(validation_passed(validation_stats))
    try:
        shown_dir = session_dir.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        shown_dir = session_dir

    lines = [
        "# EVKA Calibration Report",
        "",
        f"Generated: {generated_at.isoformat(timespec='seconds')}",
        f"Session folder: `{shown_dir}`",
        "",
        "## Inputs",
        "",
        "| File | Rows |",
        "|---|---:|",
        f"| `{CALIBRATION_CSV}` | {calibration_stats.n} |",
        f"| `{VALIDATION_CSV}` | {validation_stats.n} |",
        "",
        "## Thresholds",
        "",
        "| Check | Limit |",
        "|---|---:|",
        f"| Calibration RMSE | <= {CALIBRATION_RMSE_LIMIT_MM:.1f} mm |",
        f"| Validation max error | <= {VALIDATION_MAX_LIMIT_MM:.1f} mm |",
        "",
        "## Transform",
        "",
        "Sensor to world transform: `world = R @ sensor + t`.",
        "",
        "```text",
        "R =",
    ]
    for row in R:
        lines.append(f"  [{row[0]:+.8f} {row[1]:+.8f} {row[2]:+.8f}]")
    lines.extend([
        f"t = [{t[0]:+.3f}, {t[1]:+.3f}, {t[2]:+.3f}] mm",
        "```",
        "",
        "## Summary",
        "",
        "| Dataset | Points | RMSE mm | Mean mm | Max mm | Max label | Status |",
        "|---|---:|---:|---:|---:|---|---|",
        f"| Calibration | {calibration_stats.n} | {_fmt(calibration_stats.rmse_mm)} | {_fmt(calibration_stats.mean_mm)} | {_fmt(calibration_stats.max_mm)} | {_md(calibration_stats.max_label)} | {cal_status} |",
        f"| Validation | {validation_stats.n} | {_fmt(validation_stats.rmse_mm)} | {_fmt(validation_stats.mean_mm)} | {_fmt(validation_stats.max_mm)} | {_md(validation_stats.max_label)} | {val_status} |",
        "",
    ])

    if calibration_stats.n < 8:
        lines.extend([
            "> Warning: calibration uses fewer than 8 points. Use 8+ well-spread points for the final report.",
            "",
        ])

    lines.extend(_point_table("Calibration Point Errors", calibration_errors))
    lines.extend(_point_table("Validation Point Errors", validation_errors))

    lines.extend([
        "## Repeatability",
        "",
    ])
    if repeat_mismatched:
        lines.extend([
            "> Warning: label(s) reused for different world points (skipped): "
            + ", ".join(_md(label) for label in repeat_mismatched),
            "",
        ])
    if repeat_rows:
        lines.extend([
            "Computed from repeated validation labels.",
            "",
            "| Label | N | Std X mm | Std Y mm | Std Z mm | Max distance from mean mm |",
            "|---|---:|---:|---:|---:|---:|",
        ])
        for label, n, sx, sy, sz, spread in repeat_rows:
            lines.append(f"| {_md(label)} | {n} | {sx:.3f} | {sy:.3f} | {sz:.3f} | {spread:.3f} |")
        lines.append("")
    else:
        lines.extend([
            "No repeated validation labels found. Repeat one or more validation points to measure repeatability.",
            "",
        ])

    lines.extend([
        "## Output Files",
        "",
        "| File | Purpose |",
        "|---|---|",
        "| `report.md` | Human-readable calibration and validation report |",
        "| `calibration.json` | Candidate transform (`world = R @ sensor + t`); canonical `evka_gui` remains sensor-frame-only |",
        "| `calibration_errors.csv` | Per-point calibration residuals |",
        "| `validation_errors.csv` | Per-point validation residuals |",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def _point_table(title: str, errors: Sequence[PointError]) -> List[str]:
    lines = [
        f"## {title}",
        "",
        "dX/dY/dZ = computed - world (positive = sensor overshoots).",
        "",
        "| Label | World XYZ mm | Computed XYZ mm | dX | dY | dZ | Error mm | Notes |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for e in errors:
        lines.append(
            f"| {_md(e.label)} | "
            f"({e.world[0]:.1f}, {e.world[1]:.1f}, {e.world[2]:.1f}) | "
            f"({e.computed[0]:.1f}, {e.computed[1]:.1f}, {e.computed[2]:.1f}) | "
            f"{e.delta[0]:.2f} | {e.delta[1]:.2f} | {e.delta[2]:.2f} | "
            f"{e.error_mm:.2f} | {_md(e.notes)} |"
        )
    lines.append("")
    return lines


def generate_report(
    session_dir: Path = DEFAULT_SESSION_DIR,
    generated_at: Optional[datetime] = None,
) -> Optional[GeneratedReport]:
    generated_at = generated_at or datetime.now()
    created = ensure_templates(session_dir)
    remove_generated_artifacts(session_dir)
    cal_path = session_dir / CALIBRATION_CSV
    val_path = session_dir / VALIDATION_CSV
    if created:
        return None

    calibration_points = load_point_pairs(cal_path)
    validation_points = load_point_pairs(val_path)
    if not calibration_points and not validation_points:
        return None
    calibration_pairs = {
        tuple(point.sensor.tolist()) + tuple(point.world.tolist())
        for point in calibration_points
    }
    reused = [
        point.label for point in validation_points
        if tuple(point.sensor.tolist()) + tuple(point.world.tolist()) in calibration_pairs
    ]
    if reused:
        raise ValueError(
            "exact sensor/world point pair reused across calibration and validation: "
            + ", ".join(reused)
        )
    if len(calibration_points) < 3:
        raise ValueError(f"{cal_path}: need at least 3 calibration points")
    if not validation_points:
        raise ValueError(f"{val_path}: need at least 1 validation point")

    sensor = np.vstack([p.sensor for p in calibration_points])
    world = np.vstack([p.world for p in calibration_points])
    # Collinear/coincident sets leave a free rotation axis (coplanar rank-2 is fine).
    if np.linalg.matrix_rank(sensor - sensor.mean(axis=0)) < 2:
        raise ValueError(
            f"{cal_path}: calibration points are collinear or coincident — "
            "spread them in at least two directions"
        )
    R, t = kabsch(sensor, world)

    calibration_errors = calculate_errors(calibration_points, R, t)
    validation_errors = calculate_errors(validation_points, R, t)
    calibration_stats = summarize_errors(calibration_errors)
    validation_stats = summarize_errors(validation_errors)
    repeat_rows, repeat_mismatched = repeatability_rows(validation_errors)

    report = GeneratedReport(
        session_dir=session_dir,
        report_md=session_dir / "report.md",
        calibration_json=session_dir / "calibration.json",
        calibration_errors_csv=session_dir / "calibration_errors.csv",
        validation_errors_csv=session_dir / "validation_errors.csv",
        calibration_stats=calibration_stats,
        validation_stats=validation_stats,
        calibration_errors=tuple(calibration_errors),
        validation_errors=tuple(validation_errors),
    )

    try:
        shown_session = str(session_dir.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        shown_session = str(session_dir.resolve())

    def stats_json(stats: ErrorStats, passed: bool) -> dict:
        return {
            "point_count": stats.n,
            "rmse_mm": round(stats.rmse_mm, 3),
            "mean_mm": round(stats.mean_mm, 3),
            "max_mm": round(stats.max_mm, 3),
            "max_label": stats.max_label,
            "verdict": _pass_fail(passed),
        }

    try:
        with report.calibration_json.open("w", encoding="utf-8") as f:
            json.dump({
                "R": R.tolist(),
                "t": t.tolist(),
                "verdict": _pass_fail(report.passed),
                "generated_at": generated_at.isoformat(timespec="seconds"),
                "session": shown_session,
                "calibration": stats_json(
                    calibration_stats, calibration_passed(calibration_stats),
                ),
                "validation": stats_json(
                    validation_stats, validation_passed(validation_stats),
                ),
                "rmse_mm": round(calibration_stats.rmse_mm, 3),
                "n_points": calibration_stats.n,
            }, f, indent=2)
        write_errors_csv(report.calibration_errors_csv, calibration_errors)
        write_errors_csv(report.validation_errors_csv, validation_errors)
        write_report_md(
            report.report_md,
            session_dir,
            R,
            t,
            calibration_stats,
            validation_stats,
            calibration_errors,
            validation_errors,
            repeat_rows,
            repeat_mismatched,
            generated_at,
        )
    except OSError:
        remove_generated_artifacts(session_dir)
        raise
    return report


def main() -> int:
    try:
        report = generate_report()
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    if report is None:
        print(f"Input templates are ready in: {DEFAULT_SESSION_DIR}")
        print(f"Fill `{CALIBRATION_CSV}` and `{VALIDATION_CSV}`, then run:")
        print("python -m tools.calibration.report")
        return 0

    print(f"Report written: {report.report_md}")
    print(f"Calibration JSON written: {report.calibration_json}")
    print(f"Verdict: {_pass_fail(report.passed)}")
    if not report.passed:
        return 1
    print(
        "Optional legacy visualizer input: "
        f"--legacy-visualizer --calibration {report.calibration_json}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
