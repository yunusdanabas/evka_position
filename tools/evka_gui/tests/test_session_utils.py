"""Tests for session_utils helpers."""

from tools.evka_gui.session_utils import (
    delete_profile,
    format_constants_strip,
    format_raw_counts_line,
    format_snapshot_row,
    list_profiles,
    load_profile,
    replay_seek_indices,
    saved_points_to_csv_rows,
    save_profile,
    snapshots_to_csv_rows,
    write_saved_points_csv,
    write_snapshots_csv,
)


class FakeSettings:
    def __init__(self):
        self.data = {}
        self.group = ""

    def setValue(self, key, value):  # noqa: N802 - Qt-compatible fake
        self.data[key] = value

    def value(self, key, default=None):
        return self.data.get(key, default)

    def beginGroup(self, group):  # noqa: N802 - Qt-compatible fake
        self.group = group

    def childKeys(self):  # noqa: N802 - Qt-compatible fake
        prefix = f"{self.group}/"
        return [key[len(prefix):] for key in self.data if key.startswith(prefix)]

    def endGroup(self):  # noqa: N802 - Qt-compatible fake
        self.group = ""

    def remove(self, key):
        self.data.pop(key, None)


def test_format_snapshot_row():
    row = format_snapshot_row(1, 10.0, 20.0, 30.0)
    assert row[0] == 1
    assert row[1:4] == (10.0, 20.0, 30.0)
    assert row[4]
    assert row[5] is None


def test_format_snapshot_row_keeps_sensor():
    row = format_snapshot_row(1, 10.0, 20.0, 30.0, (412.3, 15.24, -3.11))
    assert row[5] == (412.3, 15.24, -3.11)


def test_snapshots_csv_rows():
    rows = snapshots_to_csv_rows([(1, 1.0, 2.0, 3.0, "12:00:00", None)])
    assert rows[0] == ["#", "X_mm", "Y_mm", "Z_mm", "Time", "wire_mm", "theta_deg", "phi_deg"]
    assert rows[1][0] == "1"
    # Missing reading is blank, never 0.0 — a real 0.0 must stay distinguishable.
    assert rows[1][5:] == ["", "", ""]


def test_snapshots_csv_rows_with_sensor():
    rows = snapshots_to_csv_rows([(1, 1.0, 2.0, 3.0, "12:00:00", (412.3, 15.24, -3.11))])
    assert rows[1][5:] == ["412.30", "15.240", "-3.110"]


def test_saved_points_with_origin():
    rows = saved_points_to_csv_rows([("0", 1.0, 2.0, 3.0, None)], origin=(0.0, 0.0, 0.0))
    assert rows[0][0] == "label"
    assert rows[0][-3:] == ["wire_mm", "theta_deg", "phi_deg"]
    assert rows[1][0] == "ORIGIN"
    assert rows[1][-3:] == ["", "", ""]
    assert rows[2][-3:] == ["", "", ""]


def test_saved_points_with_sensor():
    rows = saved_points_to_csv_rows([("0", 1.0, 2.0, 3.0, (412.3, 15.24, -3.11))])
    assert rows[1][-3:] == ["412.30", "15.240", "-3.110"]


def test_format_constants_strip():
    text = format_constants_strip("20000,8000,0.025,0.018")
    assert "PPR_rot=20000" in text
    assert "PPR_wire=8000" in text


def test_format_raw_counts_line():
    text = format_raw_counts_line("100,200,300")
    assert "θ=100" in text
    assert "wire=300" in text


def test_replay_seek_indices():
    assert replay_seek_indices(100, 150) == 100
    assert replay_seek_indices(100, -5) == 0


def test_write_snapshots_csv(tmp_path):
    path = tmp_path / "snap.csv"
    n = write_snapshots_csv(str(path), [(1, 1.0, 2.0, 3.0, "t", (5.0, 6.0, 7.0))])
    assert n == 1
    text = path.read_text(encoding="utf-8")
    assert text.startswith("#,X_mm,Y_mm,Z_mm,Time,wire_mm,theta_deg,phi_deg")
    assert "1,1.000,2.000,3.000,t,5.00,6.000,7.000" in text


def test_write_saved_points_csv(tmp_path):
    path = tmp_path / "points.csv"
    n = write_saved_points_csv(
        str(path), [("0", 2.0, 3.0, 4.0, (5.0, 6.0, 7.0))], origin=(1.0, 1.0, 1.0)
    )
    text = path.read_text(encoding="utf-8")
    assert n == 1
    assert "ORIGIN" in text
    assert "P0,2.000,3.000,4.000,1.000,2.000,3.000,5.00,6.000,7.000" in text


def test_profiles_round_trip_and_bad_json():
    settings = FakeSettings()
    save_profile(settings, "bench", {"mode": "tcp", "tcp_ip": "192.168.1.50"})
    assert list_profiles(settings) == ["bench"]
    assert load_profile(settings, "bench")["mode"] == "tcp"

    settings.setValue("profiles/bad", "{")
    assert load_profile(settings, "bad") is None

    delete_profile(settings, "bench")
    assert list_profiles(settings) == ["bad"]
