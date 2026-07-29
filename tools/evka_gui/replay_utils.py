"""replay_utils.py — replay speed/interval helpers."""

from __future__ import annotations

BASE_INTERVAL_MS = 50


def interval_for_speed(speed: float) -> int:
    """Return QTimer interval ms for replay speed multiplier."""
    speed = max(0.25, min(4.0, speed))
    return max(10, int(BASE_INTERVAL_MS / speed))
