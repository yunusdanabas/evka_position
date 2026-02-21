#!/usr/bin/env python3
"""main.py — entry point for the Spherical 3D Position Checker.

Usage:
    python -m position_checker.main --port /dev/ttyUSB0
    python -m position_checker.main --port COM3 --baud 115200 --maxpoints 1000
"""

import argparse
import sys

from .data_store import DataStore
from .serial_reader import SerialReader
from .gui import run_gui


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Real-time 3D position visualiser for evka_position firmware."
    )
    parser.add_argument(
        "--port", required=True,
        help="Serial port, e.g. /dev/ttyUSB0 or COM3",
    )
    parser.add_argument(
        "--baud", type=int, default=115200,
        help="Baud rate (default: 115200)",
    )
    parser.add_argument(
        "--maxpoints", type=int, default=500,
        help="Maximum number of points to keep in memory (default: 500)",
    )
    args = parser.parse_args()

    store = DataStore(maxpoints=args.maxpoints)

    reader = SerialReader(port=args.port, baud=args.baud, store=store)
    reader.start()

    try:
        run_gui(store)
    except KeyboardInterrupt:
        pass
    finally:
        reader.stop()
        print("[main] Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
