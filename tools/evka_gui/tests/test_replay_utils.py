"""Tests for replay interval helper."""

from tools.evka_gui.replay_utils import BASE_INTERVAL_MS, interval_for_speed


def test_interval_for_speed():
    assert interval_for_speed(1.0) == BASE_INTERVAL_MS
    assert interval_for_speed(2.0) == BASE_INTERVAL_MS // 2
    assert interval_for_speed(0.25) >= 10
