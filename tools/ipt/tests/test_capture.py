"""test_capture.py — armed buffer, dedup, and TCP XYZ/SENSOR pairing."""

import numpy as np
import pytest

from tools.ipt.capture import IptCapture
from tools.position_checker.parser import ParsedFrame


def _frame(x, y, z, valid=1):
    return ParsedFrame(x_mm=x, y_mm=y, z_mm=z, r_mm=0.0, theta_deg=0.0,
                       phi_deg=0.0, is_valid=valid, frame_count=0, ts_ms=0)


def test_ignores_frames_until_armed():
    cap = IptCapture()
    assert cap.ingest_frame(_frame(0, 0, 0)) is False
    cap.arm()
    assert cap.ingest_frame(_frame(0, 0, 0)) is True
    assert cap.count() == 1


def test_dedup_rejects_near_identical_points():
    cap = IptCapture(min_disp_mm=1.0)
    cap.arm()
    cap.ingest_frame(_frame(0, 0, 0))
    assert cap.ingest_frame(_frame(0.4, 0, 0)) is False   # < 1 mm move
    assert cap.ingest_frame(_frame(2.0, 0, 0)) is True     # > 1 mm move
    assert cap.count() == 2


def test_drops_invalid_frames():
    cap = IptCapture()
    cap.arm()
    assert cap.ingest_frame(_frame(5, 5, 5, valid=0)) is False
    assert cap.count() == 0


def test_tcp_pairs_xyz_with_following_valid_sensor():
    cap = IptCapture()
    cap.arm()
    # XYZ alone does not commit; the paired SENSOR line does.
    assert cap.ingest_line("X10.00,Y20.00,Z30.00") is False
    assert cap.ingest_line("SENSOR,100.00,0.000,0.000,1,1") is True
    assert cap.count() == 1
    # Invalid sensor discards the pending point.
    cap.ingest_line("X40.00,Y50.00,Z60.00")
    assert cap.ingest_line("SENSOR,100.00,0.000,0.000,0,2") is False
    assert cap.count() == 1
    np.testing.assert_allclose(cap.points()[0], [10, 20, 30])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
