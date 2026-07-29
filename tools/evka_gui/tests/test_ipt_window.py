"""test_ipt_window.py — feed_protocol_line integration for embedded IPT."""

import numpy as np
import pytest

from tools.evka_gui.ipt_panel import feed_protocol_line
from tools.ipt.capture import IptCapture


def test_feed_ignores_until_armed():
    cap = IptCapture()
    feed_protocol_line(cap, "X10.00,Y20.00,Z30.00")
    feed_protocol_line(cap, "SENSOR,100.00,0.000,0.000,1,1")
    assert cap.count() == 0


def test_feed_tcp_xyz_sensor_pair_when_armed():
    cap = IptCapture()
    cap.arm()
    feed_protocol_line(cap, "X10.00,Y20.00,Z30.00")
    feed_protocol_line(cap, "SENSOR,100.00,0.000,0.000,1,1")
    assert cap.count() == 1
    np.testing.assert_allclose(cap.points()[0], [10, 20, 30])


def test_feed_tcp_invalid_sensor_discards_point():
    cap = IptCapture()
    cap.arm()
    feed_protocol_line(cap, "X40.00,Y50.00,Z60.00")
    feed_protocol_line(cap, "SENSOR,100.00,0.000,0.000,0,2")
    assert cap.count() == 0


def test_feed_serial_data_frame_when_armed():
    cap = IptCapture()
    cap.arm()
    feed_protocol_line(
        cap,
        "DATA,15.00,25.00,35.00,100.00,0.000,0.000,1,1,1000",
    )
    assert cap.count() == 1
    np.testing.assert_allclose(cap.points()[0], [15, 25, 35])


def test_feed_serial_data_invalid_frame_dropped():
    cap = IptCapture()
    cap.arm()
    feed_protocol_line(
        cap,
        "DATA,15.00,25.00,35.00,100.00,0.000,0.000,0,1,1000",
    )
    assert cap.count() == 0
