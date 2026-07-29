#!/usr/bin/env python3
"""main.py — entry point for the Spherical 3D Position Checker.

Usage (from project root):
    python -m tools.position_checker --port /dev/ttyUSB0
    python -m tools.position_checker --port COM3 --baud 115200 --maxpoints 1000
    python -m tools.position_checker --replay-file /tmp/evka_frames.csv --fps 20
"""

import argparse
import logging
import sys

logger = logging.getLogger(__name__)

from .data_store import DataStore
from .replay_reader import ReplayReader, load_replay_frames
from .serial_reader import SerialReader
from .gui import run_gui
from .transform import load_calibration


def main(argv=None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="Real-time 3D position visualiser for evka_position firmware."
    )
    parser.add_argument(
        "--legacy-visualizer",
        action="store_true",
        help="Run the original standalone visualizer (deprecated)",
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
    parser.add_argument(
        "--calibration",
        help="Explicit calibration.json path (default: sensor frame, no transform).",
    )
    args = parser.parse_args(argv)

    if not args.legacy_visualizer:
        import warnings
        warnings.warn(
            "python -m tools.position_checker.main is deprecated; "
            "use: python -m tools.evka_gui [--serial PORT | --replay CSV] "
            "(pass --legacy-visualizer for the old visualizer)",
            DeprecationWarning,
            stacklevel=2,
        )
        from tools.evka_gui.__main__ import main as gui_main
        gui_argv = []
        if args.replay_file:
            gui_argv.extend(["--replay", args.replay_file])
        elif args.port:
            gui_argv.extend(["--serial", args.port, "--baud", str(args.baud)])
        sys.exit(gui_main(gui_argv))

    if args.replay_file is None and not args.port:
        parser.error("--port is required unless --replay-file is used")

    store = DataStore(maxpoints=args.maxpoints, csv_log_path=args.csv_log)

    if args.calibration and args.calibration.lower() != "none":
        cal = load_calibration(args.calibration)
        if cal is not None:
            R, t = cal
            store.set_transform(R, t)
            logger.info("Calibration loaded from: %s", args.calibration)
        # if load fails, transform.py already printed a warning; run uncalibrated

    worker = None

    if args.replay_file:
        frames = load_replay_frames(args.replay_file)
        if not frames:
            logger.error("No replay frames loaded from: %s", args.replay_file)
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
        logger.info("Exiting.")


if __name__ == "__main__":
    main()
