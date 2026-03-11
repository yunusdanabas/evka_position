#!/usr/bin/env python3
"""main.py — entry point for the Spherical 3D Position Checker.

Usage:
    python -m position_checker.main --port /dev/ttyUSB0
    python -m position_checker.main --port COM3 --baud 115200 --maxpoints 1000
    python -m position_checker.main --replay-file /tmp/evka_frames.csv --fps 20
"""

import argparse
import sys

from .data_store import DataStore
from .replay_reader import ReplayReader, load_replay_frames
from .serial_reader import SerialReader
from .gui import run_gui


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Real-time 3D position visualiser for evka_position firmware."
    )
    parser.add_argument("--port", help="Serial port, e.g. /dev/ttyUSB0 or COM3")
    parser.add_argument(
        "--baud", type=int, default=115200,
        help="Baud rate (default: 115200)",
    )
    parser.add_argument(
        "--maxpoints", type=int, default=500,
        help="Maximum number of points to keep in memory (default: 500)",
    )
    parser.add_argument(
        "--fps", type=float, default=10.0,
        help="GUI refresh / replay FPS (default: 10)",
    )
    parser.add_argument(
        "--reconnect",
        dest="reconnect",
        action="store_true",
        default=True,
        help="Enable auto-reconnect for serial mode (default: enabled)",
    )
    parser.add_argument(
        "--no-reconnect",
        dest="reconnect",
        action="store_false",
        help="Disable auto-reconnect in serial mode",
    )
    parser.add_argument(
        "--reconnect-interval", type=float, default=1.0,
        help="Initial reconnect delay in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--csv-log",
        help="Optional output CSV log path for parsed DATA frames",
    )
    parser.add_argument(
        "--replay-file",
        help="Read frames from CSV/raw DATA file instead of serial port",
    )
    args = parser.parse_args()

    if args.replay_file is None and not args.port:
        parser.error("--port is required unless --replay-file is used")

    store = DataStore(maxpoints=args.maxpoints, csv_log_path=args.csv_log)
    worker = None

    if args.replay_file:
        frames = load_replay_frames(args.replay_file)
        if not frames:
            print(f"[main] No replay frames loaded from: {args.replay_file}")
            store.close()
            sys.exit(2)
        worker = ReplayReader(frames=frames, fps=args.fps, store=store, source_path=args.replay_file)
    else:
        worker = SerialReader(
            port=args.port,
            baud=args.baud,
            store=store,
            reconnect=args.reconnect,
            reconnect_interval=args.reconnect_interval,
        )

    worker.start()

    try:
        run_gui(store, fps=args.fps)
    except KeyboardInterrupt:
        pass
    finally:
        worker.stop()
        worker.join(timeout=1.0)
        store.close()
        print("[main] Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
