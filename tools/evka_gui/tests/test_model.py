"""Tests for evka_gui model layer."""

import math

from tools.evka_gui.model import (
    TrailBuffer,
    UiState,
    command_response_matches,
    ingest_line,
    parse_batt_line,
    parse_cal_line,
    parse_status_line,
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


def test_ingest_constants_and_raw():
    (c,) = ingest_line("CONSTANTS,20000,8000,0.025,0.018")
    assert c.kind == "constants"
    (r,) = ingest_line("RAW,100,200,300")
    assert r.kind == "raw_counts"
    assert r.data == "100,200,300"


def test_status_updates_position_sensor_and_timestamp():
    updates = ingest_line("STATUS,1,42,1234,500.0,10.0,-20.0,100.0,200.0,300.0")
    assert [(u.kind, u.data) for u in updates] == [
        ("position", (100.0, 200.0, 300.0)),
        ("sensor", (500.0, 10.0, -20.0, True, 42)),
        ("ts", 1234),
    ]
    assert parse_status_line("STATUS,1,2,3,nan,0,0,0,0,0") is None


def test_command_replies_match_only_the_command_they_complete():
    cases = [
        ("PING", "ACK:PONG"),
        ("STATUS", "STATUS,1,2,3,4,5,6,7,8,9"),
        ("SYSINFO", "SYSINFO,-50,120000,300,1"),
        ("CONSTANTS", "CONSTANTS,20000,8000,0.025,0.018"),
        ("RAW_COUNTS", "RAW,1,2,3"),
        ("GET_IP", "STA_IP:192.168.1.84"),
        ("CAL_W 500", "CAL:WIRE,1.0,0.025,8000"),
        ("SET_PPR_WIRE 8000.00", "ACK:PPR_WIRE,8000.00"),
        ("SAVE_PPR", "ACK:SAVE_PPR"),
    ]
    for command, response in cases:
        assert command_response_matches(command, response)
    assert not command_response_matches("PING", "ACK:ZERO")
    assert not command_response_matches("SET_PPR_WIRE 8000", "ACK:PPR_WIRE,7999")


def test_command_matching_validates_structured_lines_and_specific_errors():
    assert not command_response_matches("STATUS", "STATUS,not,a,valid,response")
    assert not command_response_matches("SYSINFO", "SYSINFO,bad")
    assert not command_response_matches("CONSTANTS", "CONSTANTS,20000,bad,0.025,0.018")
    assert not command_response_matches("RAW_COUNTS", "RAW,1,2,bad")
    assert not command_response_matches("GET_IP", "STA_IP:not-an-ip")
    assert not command_response_matches("CAL_W 500", "CAL:WIRE,nan,0.025,8000")

    assert command_response_matches("CAL_W 500", "ERR:CAL_W zero counts")
    assert command_response_matches("SET_PPR_WIRE 8000", "ERR:SET_PPR_WIRE bad value")
    assert command_response_matches("DEL_POINT", "ERR:NO_POINTS")
    assert command_response_matches("BLINK", "ERR:UNKNOWN_CMD")
    assert not command_response_matches("PING", "ERR:CAL_W zero counts")
    assert not command_response_matches("STATUS", "ERR:UNKNOWN_CMD")
    assert not command_response_matches("STATUS", "ERR:CMD_QUEUE_FULL")


def test_ingest_control_lines():
    cases = [
        ("REMOTE_BTN:1", "remote_btn", 1),
        ("REMOTE_HB", "remote_hb", None),
        ("POINT,1,2,3,4", "point", "POINT,1,2,3,4"),
        ("DEL_POINT,1", "del_point", "DEL_POINT,1"),
        ("ACK:PONG", "ack", "ACK:PONG"),
        ("ERR:NO_POINTS", "err", "ERR:NO_POINTS"),
        ("STA_IP:192.168.1.84", "sta_ip", "192.168.1.84"),
    ]
    for line, kind, data in cases:
        (up,) = ingest_line(line)
        assert up.kind == kind
        assert up.data == data


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
