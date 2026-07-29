"""Tests for protocol-log line classification."""

from tools.evka_gui.protocol_log import _classify_line


def test_classify_protocol_lines():
    assert _classify_line("DATA,1,2,3,4,5,6,1,7,8") == "data"
    assert _classify_line("SENSOR,1,2,3,1,4") == "data"
    assert _classify_line("X12.34,Y-5.67,Z8.90") == "data"
    assert _classify_line("ACK:PONG") == "ack"
    assert _classify_line("ERR:NO_POINTS") == "err"
    assert _classify_line("hello") == "other"
