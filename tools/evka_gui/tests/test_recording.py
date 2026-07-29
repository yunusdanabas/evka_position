"""Recording round-trip: what we write must be what replay reads back.

The whole point of the recording format is that it isn't a new one — it's the
firmware's own ``DATA,`` line, which ``load_replay_frames`` already parses. These
tests hold that claim honest on every transport, including the awkward one (TCP,
which sends ``X,Y,Z`` + ``SENSOR,`` and has to be re-serialised).
"""

import sys

import pytest
from PyQt5 import QtWidgets

from tools.evka_gui.session_utils import format_data_line
from tools.position_checker.replay_reader import load_replay_frames


@pytest.fixture(scope="module")
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    return app


@pytest.fixture
def window(qapp):
    from tools.evka_gui.gui import EvkaWindow
    w = EvkaWindow()
    yield w
    if w._rec_file is not None:
        w._rec_file.close()
        w._rec_file = None
    w.close()


def _record(window, path, lines):
    window._rec_file = open(path, "w", encoding="utf-8", newline="\n")
    window._rec_count = 0
    window._rec_xyz = None
    window._rec_t0 = 0.0
    for line in lines:
        window._record_line(line)
    window._rec_file.close()
    window._rec_file = None


def test_format_data_line_round_trips_through_replay(tmp_path):
    path = tmp_path / "rec.csv"
    path.write_text(
        format_data_line(1.0, 2.0, 3.0, 900.0, 25.0, 10.0, True, 42, 12345) + "\n"
        + format_data_line(-4.5, 5.25, -6.75, 901.5, -25.5, -10.5, False, 43, 12395) + "\n",
        encoding="utf-8",
    )
    frames = load_replay_frames(str(path))
    assert len(frames) == 2
    f = frames[0]
    assert (f.x_mm, f.y_mm, f.z_mm) == (1.0, 2.0, 3.0)
    assert (f.r_mm, f.theta_deg, f.phi_deg) == (900.0, 25.0, 10.0)
    assert f.is_valid == 1 and f.frame_count == 42 and f.ts_ms == 12345
    assert frames[1].is_valid == 0 and frames[1].x_mm == -4.5


def test_serial_and_ws_data_lines_pass_through_verbatim(window, tmp_path):
    path = tmp_path / "serial.csv"
    lines = [
        "DATA,1.00,2.00,3.00,900.00,25.000,10.000,1,1,100",
        "ACK:PONG",                                    # replies must not be recorded
        "DATA,4.00,5.00,6.00,901.00,26.000,11.000,1,2,150",
    ]
    _record(window, path, lines)

    frames = load_replay_frames(str(path))
    assert len(frames) == 2, "command replies must not land in the recording"
    assert (frames[0].x_mm, frames[1].x_mm) == (1.0, 4.0)
    assert frames[1].frame_count == 2


def test_tcp_xyz_plus_sensor_is_reserialised_into_replayable_data(window, tmp_path):
    path = tmp_path / "tcp.csv"
    # TCP never sends DATA — it sends the position line, then the sensor line.
    lines = [
        "X1.00,Y2.00,Z3.00",
        "SENSOR,900.00,25.000,10.000,1,7",
        "X4.00,Y5.00,Z6.00",
        "SENSOR,901.00,26.000,11.000,0,8",
    ]
    _record(window, path, lines)

    frames = load_replay_frames(str(path))
    assert len(frames) == 2, "a TCP recording must still replay"
    assert (frames[0].x_mm, frames[0].y_mm, frames[0].z_mm) == (1.0, 2.0, 3.0)
    assert frames[0].r_mm == 900.0 and frames[0].frame_count == 7
    assert frames[0].is_valid == 1
    assert (frames[1].x_mm, frames[1].is_valid) == (4.0, 0)


def test_tcp_sensor_without_a_preceding_position_is_dropped(window, tmp_path):
    # A half-frame would otherwise be written with stale coordinates.
    path = tmp_path / "partial.csv"
    _record(window, path, ["SENSOR,900.00,25.000,10.000,1,7"])
    assert load_replay_frames(str(path)) == []


def test_recording_is_raw_sensor_frame_not_software_zeroed(window, tmp_path):
    """A software zero is a display offset. Baking it into a recording would make the
    file disagree with what the device actually measured.

    The offsets below are large and non-zero on purpose: if recording ever moved
    downstream of ``process_xyz_frame``, the recorded X would be 1.0 - 1000.0.
    """
    window._display.relative_zero_active = True
    window._display.offset_x = 1000.0
    window._display.offset_y = 2000.0
    window._display.offset_z = 3000.0
    # Guard against this test rotting into a no-op if the field names ever change.
    assert window._display.apply_offsets(1.0, 2.0, 3.0) == (-999.0, -1998.0, -2997.0)

    path = tmp_path / "raw.csv"
    _record(window, path, ["DATA,1.00,2.00,3.00,900.00,25.000,10.000,1,1,100"])

    frames = load_replay_frames(str(path))
    assert (frames[0].x_mm, frames[0].y_mm, frames[0].z_mm) == (1.0, 2.0, 3.0)


def test_manual_snapshot_is_always_raw_sensor_frame(window):
    window._on_position(100.0, 200.0, 300.0)
    window._display.relative_zero_active = True
    window._display.offset_x = 10.0
    window._display.offset_y = 20.0
    window._display.offset_z = 30.0

    window._capture_snapshot()

    assert window._snapshots[0][1:4] == (100.0, 200.0, 300.0)


def test_recording_write_error_stops_and_closes_recording(window):
    class BrokenFile:
        closed = False

        def write(self, _text):
            raise OSError("disk full")

        def close(self):
            self.closed = True

    broken = BrokenFile()
    window._rec_file = broken
    window._act_record.blockSignals(True)
    window._act_record.setChecked(True)
    window._act_record.blockSignals(False)

    window._record_line("DATA,1,2,3,4,5,6,1,7,8")

    assert window._rec_file is None
    assert broken.closed
    assert not window._act_record.isChecked()
    assert window._rec_count == 0
    assert window._lbl_status.text() == "Recording stopped: disk full"
