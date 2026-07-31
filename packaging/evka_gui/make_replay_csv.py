"""Generate a synthetic replay CSV so the GUI can be tested with no hardware.

    python packaging/evka_gui/make_replay_csv.py frames.csv
    python -m tools.evka_gui --replay frames.csv

The output is a dump of raw firmware ``DATA,`` lines, which is the same format
the Record button writes and ``load_replay_frames`` reads — so a synthetic file
and a real recording are interchangeable.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

# Running this by path puts packaging/evka_gui/ on sys.path, not the repo root,
# so `tools` would not import. Keep reusing format_data_line rather than
# duplicating the wire format — the field order is fixed by the firmware.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.evka_gui.session_utils import format_data_line  # noqa: E402

FRAMES = 400
INTERVAL_MS = 50


def frames(count: int = FRAMES):
    """A slow spiral through the workspace — visibly moving on every axis."""
    for i in range(count):
        a = i * 0.05
        r = 300.0 + 80.0 * math.sin(a)
        theta = (math.degrees(a) % 360.0) - 180.0
        phi = 35.0 * math.sin(a * 0.7)

        th_r, ph_r = math.radians(theta), math.radians(phi)
        x = r * math.cos(ph_r) * math.cos(th_r)
        y = r * math.cos(ph_r) * math.sin(th_r)
        z = r * math.sin(ph_r)

        yield format_data_line(x, y, z, r, theta, phi, True, i, i * INTERVAL_MS)


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    path = args[0] if args else "frames.csv"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for line in frames():
            f.write(line + "\n")
    print(f"wrote {FRAMES} frames to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
