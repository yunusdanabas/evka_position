"""Tests for evka_gui model layer."""

import math

from tools.evka_gui.model import (
    TrailBuffer,
    UiState,
    ingest_line,
    parse_batt_line,
    parse_cal_line,
    parse_sysinfo_line,
)


def test_parse_batt_valid():
    b = parse_batt_line("BATT,3.874,72,0")
    assert b is not None
    assert abs(b.voltage - 3.874) < 1e-9
    assert b.pct == 72
    assert b.is_low is False


def test_parse_batt_bad():
    assert parse_batt_line("STATUS,1,2,3") is None
    assert parse_batt_line("BATT,3.8,72") is None


def test_parse_sysinfo():
    si = parse_sysinfo_line("SYSINFO,-42,120000,3661,2")
    assert si is not None
    assert si.rssi == -42
    assert si.heap == 120000
    assert si.uptime_s == 3661
    assert si.tcp_clients == 2


def test_parse_cal_wire():
    cal = parse_cal_line("CAL:WIRE,1.0200,0.024500,8163.27")
    assert cal is not None
    assert math.isclose(cal.factor, 1.02)
    assert math.isclose(cal.ppr_wire, 8163.27)


def test_parse_cal_theta():
    cal = parse_cal_line("CAL:THETA,100000,20000.00")
    assert cal is not None
    assert cal.axis == "theta"
    assert cal.counts == 100000


def test_ingest_data_line():
    ups = ingest_line("DATA,12.34,-5.67,8.90,15.72,45.123,-12.500,1,42,208460")
    kinds = {u.kind for u in ups}
    assert kinds == {"position", "sensor", "ts"}


def test_ingest_tcp_xyz_and_sensor():
    (pos,) = ingest_line("X12.34,Y-5.67,Z8.90")
    assert pos.data == (12.34, -5.67, 8.90)
    (sen,) = ingest_line("SENSOR,15.72,45.123,-12.500,1,42")
    assert sen.data[3] == 1


def test_ingest_sysinfo_and_cal():
    (si,) = ingest_line("SYSINFO,-40,100000,60,1")
    assert si.kind == "sysinfo"
    (cal,) = ingest_line("CAL:PHI,50000,19800.00")
    assert cal.data.axis == "phi"


def test_trailbuffer_maxlen():
    tb = TrailBuffer(maxlen=3)
    for i in range(5):
        tb.add(i, i, i)
    assert len(tb) == 3
    assert list(tb.xs()) == [2.0, 3.0, 4.0]


def test_uistate_reset():
    tb = TrailBuffer()
    tb.add(1, 2, 3)
    st = UiState(tb, last_hb=123.0, battery_seen=True, saved_points=4)
    st.reset()
    assert len(tb) == 0
    assert st.last_hb is None
