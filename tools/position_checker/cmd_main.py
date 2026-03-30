#!/usr/bin/env python3
"""cmd_main.py — entry point for Linux TCP CMD control GUI.

Usage:
    python -m tools.position_checker.cmd_main
"""

import logging
import sys

from .cmd_gui import run_cmd_gui


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    code = run_cmd_gui()
    if code:
        sys.exit(code)


if __name__ == "__main__":
    main()
