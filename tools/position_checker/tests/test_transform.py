import json

from tools.calibration import calibrate
from tools.position_checker import main as main_mod
from tools.position_checker.transform import load_calibration


class _Worker:
    def start(self):
        pass

    def stop(self):
        pass

    def join(self, timeout=None):
        pass


def test_legacy_visualizer_defaults_to_sensor_frame(monkeypatch):
    loaded = []
    monkeypatch.setattr(main_mod, "load_calibration", lambda path: loaded.append(path))
    monkeypatch.setattr(main_mod, "load_replay_frames", lambda path: [object()])
    monkeypatch.setattr(main_mod, "ReplayReader", lambda **kwargs: _Worker())
    monkeypatch.setattr(main_mod, "run_gui", lambda *args, **kwargs: None)

    main_mod.main(["--legacy-visualizer", "--replay-file", "unused.csv"])
    assert loaded == []


def test_failed_calibration_verdict_is_rejected(tmp_path):
    path = tmp_path / "calibration.json"
    path.write_text(json.dumps({
        "R": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "t": [0, 0, 0],
        "verdict": "FAIL",
    }), encoding="utf-8")
    assert load_calibration(str(path)) is None


def test_missing_verdict_is_rejected_and_explicit_pass_is_loaded(tmp_path):
    path = tmp_path / "calibration.json"
    data = {
        "R": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "t": [1, 2, 3],
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    assert load_calibration(str(path)) is None

    data["verdict"] = "PASS"
    path.write_text(json.dumps(data), encoding="utf-8")
    R, t = load_calibration(str(path))
    assert R.tolist() == data["R"]
    assert t.tolist() == data["t"]


def test_legacy_calibrate_output_is_an_explicit_candidate(tmp_path):
    path = tmp_path / "candidate.json"
    calibrate.main(["--out", str(path)])
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["verdict"] == "CANDIDATE"
    assert data["generated_at"]
    assert data["session"]
    assert load_calibration(str(path)) is None


def test_transform_rejects_non_finite_and_non_rotation_matrices(tmp_path):
    cases = [
        ([[None, 0, 0], [0, 1, 0], [0, 0, 1]], [0, 0, 0]),
        ([[float("nan"), 0, 0], [0, 1, 0], [0, 0, 1]], [0, 0, 0]),
        ([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0, float("inf"), 0]),
        ([[2, 0, 0], [0, 1, 0], [0, 0, 1]], [0, 0, 0]),
        ([[-1, 0, 0], [0, 1, 0], [0, 0, 1]], [0, 0, 0]),
    ]
    for index, (rotation, translation) in enumerate(cases):
        path = tmp_path / f"bad-{index}.json"
        path.write_text(json.dumps({
            "R": rotation,
            "t": translation,
            "verdict": "PASS",
        }), encoding="utf-8")
        assert load_calibration(str(path)) is None
