"""Auto-reconnect backoff + the FREEZE line gate."""

from tools.evka_gui.model import is_frame_line
from tools.evka_gui.transport import RECONNECT_MAX_S, RECONNECT_MIN_S, next_backoff


def test_backoff_sequence_doubles_from_the_first_step():
    delay, seen = 0.0, []
    for _ in range(8):
        delay = next_backoff(delay)
        seen.append(delay)
    assert seen == [1.0, 2.0, 4.0, 8.0, 16.0, 30.0, 30.0, 30.0]


def test_backoff_first_retry_is_min_not_zero():
    # prev=0.0 must not stay 0.0 (0*2 == 0 would hot-loop the reconnect timer).
    assert next_backoff(0.0) == RECONNECT_MIN_S


def test_backoff_is_capped():
    assert next_backoff(RECONNECT_MAX_S) == RECONNECT_MAX_S
    assert next_backoff(1e6) == RECONNECT_MAX_S


def test_freeze_gates_only_the_position_stream():
    # Suppressed while frozen: the 20 Hz frame lines, on every transport.
    assert is_frame_line("DATA,1,2,3,4,5,6,1,7,8")       # serial + websocket
    assert is_frame_line("X1.00,Y2.00,Z3.00")            # tcp
    assert is_frame_line("SENSOR,900.0,25.0,10.0,1,42")  # tcp

    # Never suppressed: command replies must land even while frozen.
    for reply in (
        "ACK:ZERO",
        "ACK:PONG",
        "ERR:UNKNOWN_CMD",
        "POINT,1,10.0,20.0,30.0,37.4,63.4,53.3",
        "DEL_POINT,0",
        "CONSTANTS,20000.00,8000.00,0.025000,0.018000",
        "SYSINFO,-50,120000,300,1",
        "BATT,3.900,75,0",
        "STA_IP:192.168.1.84",
        "RAW,100,200,300",
    ):
        assert not is_frame_line(reply), reply
