import csv
import json
from datetime import datetime

import pytest

from tools.calibration import report as report_mod
from tools.calibration.report import (
    CALIBRATION_CSV,
    GENERATED_FILES,
    POINT_FIELDS,
    VALIDATION_CSV,
    PointPair,
    generate_report,
    load_point_pairs,
    save_point_pairs,
)


def _write_points(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(POINT_FIELDS)
        writer.writerows(rows)


def _seed_generated_files(session_dir):
    for name in GENERATED_FILES:
        (session_dir / name).write_text("stale PASS", encoding="utf-8")


def test_save_point_pairs_round_trips(tmp_path):
    import numpy as np

    path = tmp_path / CALIBRATION_CSV
    save_point_pairs(path, [
        PointPair("P0", np.array([1.0, 2.0, 3.0]), np.array([4.0, 5.0, 6.0]), "origin"),
        PointPair("PX", np.array([100.0, 0.0, 0.0]), np.array([100.5, 0.0, 0.0]), ""),
    ])
    assert path.read_text(encoding="utf-8").startswith(",".join(POINT_FIELDS))

    loaded = load_point_pairs(path)
    assert [p.label for p in loaded] == ["P0", "PX"]
    assert [p.notes for p in loaded] == ["origin", ""]
    assert loaded[0].world.tolist() == [1.0, 2.0, 3.0]
    assert loaded[1].sensor.tolist() == [100.5, 0.0, 0.0]


def test_missing_inputs_create_templates(tmp_path):
    assert generate_report(tmp_path) is None
    assert (tmp_path / CALIBRATION_CSV).read_text(encoding="utf-8").startswith("label,")
    assert (tmp_path / VALIDATION_CSV).read_text(encoding="utf-8").startswith("label,")
    assert generate_report(tmp_path) is None


def test_generate_report_identity_transform(tmp_path):
    _write_points(tmp_path / CALIBRATION_CSV, [
        ["P0", 0, 0, 0, 0, 0, 0, "origin"],
        ["PX", 100, 0, 0, 100, 0, 0, ""],
        ["PY", 0, 100, 0, 0, 100, 0, ""],
        ["PZ", 0, 0, 100, 0, 0, 100, ""],
    ])
    _write_points(tmp_path / VALIDATION_CSV, [
        ["V1", 10, 20, 30, 10, 20, 30, "exact"],
        ["V1", 10, 20, 30, 10, 20, 30, "repeat"],
    ])

    report = generate_report(tmp_path, generated_at=datetime(2026, 7, 16, 12, 0, 0))
    assert report is not None
    text = report.report_md.read_text(encoding="utf-8")
    assert "| Calibration | 4 | 0.00" in text
    assert "| Validation | 2 | 0.00" in text
    assert "| V1 | 2 |" in text

    data = json.loads(report.calibration_json.read_text(encoding="utf-8"))
    assert data["n_points"] == 4
    assert data["rmse_mm"] == 0.0
    assert data["verdict"] == "PASS"
    assert data["generated_at"] == "2026-07-16T12:00:00"
    assert data["session"] == str(tmp_path.resolve())
    assert data["calibration"]["point_count"] == 4
    assert data["calibration"]["verdict"] == "PASS"
    assert data["validation"]["point_count"] == 2
    assert data["validation"]["max_mm"] == 0.0
    assert report.validation_errors_csv.exists()

    assert report.passed is True
    assert report.calibration_stats.n == 4
    assert report.validation_stats.max_mm == pytest.approx(0.0)
    assert [e.label for e in report.calibration_errors] == ["P0", "PX", "PY", "PZ"]


def test_load_point_pairs_rejects_bad_numbers(tmp_path):
    path = tmp_path / CALIBRATION_CSV
    _write_points(path, [["P0", "bad", 0, 0, 0, 0, 0, ""]])

    with pytest.raises(ValueError, match="non-numeric"):
        load_point_pairs(path)


def test_load_point_pairs_accepts_exported_headers(tmp_path):
    # Web dashboard endpoint export: label + coords, no notes column.
    dash = tmp_path / "dash.csv"
    dash.write_text(
        "label,world_x,world_y,world_z,sensor_x,sensor_y,sensor_z\r\nP1,0,0,0,1,2,3\r\n",
        encoding="utf-8",
    )
    pairs = load_point_pairs(dash)
    assert len(pairs) == 1
    assert pairs[0].label == "P1"
    assert pairs[0].notes == ""

    # evka_gui endpoint export: coordinate columns only.
    gui = tmp_path / "gui.csv"
    gui.write_text(
        "world_x,world_y,world_z,sensor_x,sensor_y,sensor_z\n0,0,0,1,2,3\n",
        encoding="utf-8",
    )
    pairs = load_point_pairs(gui)
    assert len(pairs) == 1
    assert pairs[0].label == "row2"


def test_collinear_calibration_rejected(tmp_path):
    _write_points(tmp_path / CALIBRATION_CSV, [
        ["A", 0, 0, 0, 0, 0, 0, ""],
        ["B", 100, 0, 0, 100, 0, 0, ""],
        ["C", 200, 0, 0, 200, 0, 0, ""],
    ])
    _write_points(tmp_path / VALIDATION_CSV, [["V", 0, 10, 0, 0, 10, 0, ""]])

    with pytest.raises(ValueError, match="collinear"):
        generate_report(tmp_path)


def test_fail_rendering_out_of_tolerance(tmp_path):
    _write_points(tmp_path / CALIBRATION_CSV, [
        ["P0", 0, 0, 0, 0, 0, 0, ""],
        ["PX", 100, 0, 0, 100, 0, 0, ""],
        ["PY", 0, 100, 0, 0, 100, 0, ""],
        ["PZ", 0, 0, 100, 0, 0, 100, ""],
    ])
    _write_points(tmp_path / VALIDATION_CSV, [["V1", 0, 0, 0, 100, 0, 0, "way off"]])

    report = generate_report(tmp_path)
    text = report.report_md.read_text(encoding="utf-8")
    assert "| PASS |" in text  # calibration
    assert "| FAIL |" in text  # validation max error 100 mm > 15 mm

    # A failing validation set must fail the whole report — this gates the GUI deploy button.
    assert report.passed is False
    data = json.loads(report.calibration_json.read_text(encoding="utf-8"))
    assert data["verdict"] == "FAIL"
    assert data["validation"]["verdict"] == "FAIL"


def test_cli_failure_returns_nonzero_without_deploy_instruction(tmp_path, monkeypatch, capsys):
    _write_points(tmp_path / CALIBRATION_CSV, [
        ["P0", 0, 0, 0, 0, 0, 0, ""],
        ["PX", 100, 0, 0, 100, 0, 0, ""],
        ["PY", 0, 100, 0, 0, 100, 0, ""],
        ["PZ", 0, 0, 100, 0, 0, 100, ""],
    ])
    _write_points(tmp_path / VALIDATION_CSV, [
        ["V1", 0, 0, 0, 100, 0, 0, "way off"],
    ])
    generated = generate_report(tmp_path)
    monkeypatch.setattr(report_mod, "generate_report", lambda: generated)

    assert report_mod.main() == 1
    output = capsys.readouterr().out
    assert "Verdict: FAIL" in output
    assert "To deploy" not in output


def test_cli_pass_prints_explicit_legacy_visualizer_instruction(tmp_path, monkeypatch, capsys):
    _write_points(tmp_path / CALIBRATION_CSV, [
        ["P0", 0, 0, 0, 0, 0, 0, ""],
        ["PX", 100, 0, 0, 100, 0, 0, ""],
        ["PY", 0, 100, 0, 0, 100, 0, ""],
        ["PZ", 0, 0, 100, 0, 0, 100, ""],
    ])
    _write_points(tmp_path / VALIDATION_CSV, [["V1", 10, 20, 30, 10, 20, 30, ""]])
    generated = generate_report(tmp_path)
    monkeypatch.setattr(report_mod, "generate_report", lambda: generated)

    assert report_mod.main() == 0
    output = capsys.readouterr().out
    assert "Verdict: PASS" in output
    assert "Optional legacy visualizer input" in output
    assert "--legacy-visualizer --calibration" in output


def test_error_row_number_survives_blank_lines(tmp_path):
    path = tmp_path / CALIBRATION_CSV
    path.write_text(
        "label,world_x,world_y,world_z,sensor_x,sensor_y,sensor_z,notes\n"
        "P0,0,0,0,0,0,0,\n"
        "\n"
        "P1,bad,0,0,0,0,0,\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="row 4"):
        load_point_pairs(path)


def test_repeatability_skips_label_reused_for_different_points(tmp_path):
    _write_points(tmp_path / CALIBRATION_CSV, [
        ["P0", 0, 0, 0, 0, 0, 0, ""],
        ["PX", 100, 0, 0, 100, 0, 0, ""],
        ["PY", 0, 100, 0, 0, 100, 0, ""],
        ["PZ", 0, 0, 100, 0, 0, 100, ""],
    ])
    _write_points(tmp_path / VALIDATION_CSV, [
        ["V1", 10, 20, 30, 10, 20, 30, ""],
        ["V1", 500, 0, 0, 500, 0, 0, "different point, same label"],
    ])

    report = generate_report(tmp_path)
    text = report.report_md.read_text(encoding="utf-8")
    assert "| V1 | 2 |" not in text
    assert "reused for different world points" in text


def test_exact_pair_cannot_be_in_both_calibration_and_validation(tmp_path):
    _write_points(tmp_path / CALIBRATION_CSV, [
        ["P0", 0, 0, 0, 0, 0, 0, ""],
        ["PX", 100, 0, 0, 100, 0, 0, ""],
        ["PY", 0, 100, 0, 0, 100, 0, ""],
        ["PZ", 0, 0, 100, 0, 0, 100, ""],
    ])
    _write_points(tmp_path / VALIDATION_CSV, [
        ["COPY", 100, 0, 0, 100, 0, 0, ""],
    ])

    with pytest.raises(ValueError, match="reused across calibration and validation"):
        generate_report(tmp_path)


def test_empty_inputs_remove_stale_generated_artifacts(tmp_path):
    _write_points(tmp_path / CALIBRATION_CSV, [])
    _write_points(tmp_path / VALIDATION_CSV, [])
    _seed_generated_files(tmp_path)

    assert generate_report(tmp_path) is None
    assert all(not (tmp_path / name).exists() for name in GENERATED_FILES)


def test_invalid_inputs_remove_stale_generated_artifacts(tmp_path):
    _write_points(tmp_path / CALIBRATION_CSV, [
        ["P0", 0, 0, 0, 0, 0, 0, ""],
    ])
    _write_points(tmp_path / VALIDATION_CSV, [
        ["V1", 10, 0, 0, 10, 0, 0, ""],
    ])
    _seed_generated_files(tmp_path)

    with pytest.raises(ValueError, match="at least 3"):
        generate_report(tmp_path)
    assert all(not (tmp_path / name).exists() for name in GENERATED_FILES)


def test_cli_catches_output_oserror(monkeypatch, capsys):
    monkeypatch.setattr(
        report_mod, "generate_report", lambda: (_ for _ in ()).throw(OSError("read-only")),
    )
    assert report_mod.main() == 2
    assert "ERROR: read-only" in capsys.readouterr().out
