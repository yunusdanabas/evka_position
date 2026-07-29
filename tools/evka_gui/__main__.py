"""CLI entry point for evka_gui — unified EVKA Position control GUI.

    python -m tools.evka_gui                              # open disconnected
    python -m tools.evka_gui --serial /dev/ttyUSB0 --baud 115200
    python -m tools.evka_gui --tcp 192.168.1.50:8080      # AP direct
    python -m tools.evka_gui --tcp 192.168.1.84:8080      # STA (ASMETAL)
    python -m tools.evka_gui --ws 192.168.1.50            # WebSocket (port 80 /ws)
    python -m tools.evka_gui --replay frames.csv

Toolbar: Calibration…, WiFi Settings…, IPT plots…, Remote Tester…, snapshots,
saved-point export, Open Dashboard, Export Session CSV.
"""

from __future__ import annotations

import argparse
import sys

from .gui import run


def _parse(argv=None) -> dict | None:
    p = argparse.ArgumentParser(prog="tools.evka_gui", description=__doc__)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--serial", metavar="PORT", help="serial port, e.g. /dev/ttyUSB0 or COM3")
    g.add_argument("--tcp", metavar="HOST:PORT", help="TCP endpoint, e.g. 192.168.1.50:8080")
    g.add_argument("--ws", metavar="HOST", help="WebSocket host, e.g. 192.168.1.50 (port 80, path /ws)")
    g.add_argument("--replay", metavar="CSV", help="replay DATA, CSV file (no hardware)")
    p.add_argument("--baud", type=int, default=115200)
    a = p.parse_args(argv)

    if a.serial:
        return {"mode": "serial", "port": a.serial, "baud": a.baud, "autoconnect": True}
    if a.tcp:
        host, _, port = a.tcp.partition(":")
        return {"mode": "tcp", "host": host, "port": int(port or 8080), "autoconnect": True}
    if a.ws:
        return {"mode": "ws", "host": a.ws, "autoconnect": True}
    if a.replay:
        return {"mode": "replay", "replay_file": a.replay, "autoconnect": True}
    return None


def main(argv=None) -> int:
    return run(_parse(argv))


if __name__ == "__main__":
    sys.exit(main())
