"""PyInstaller entry point for the EVKA Position GUI.

Why this file exists instead of freezing tools/evka_gui/__main__.py directly:
PyInstaller runs the entry script as top-level ``__main__`` with no package
context, so ``__main__.py``'s ``from .gui import run`` would die with
"attempted relative import with no known parent package". Importing through the
package name keeps the relative imports valid.

It also installs a crash log, because ``--windowed`` builds have no stderr: an
unhandled exception makes the window vanish with nothing for the user to report.

Build from the repo root, not from this directory:
    pyinstaller packaging/evka_gui/evka_gui.spec
"""

from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


def _log_dir() -> Path:
    """Mirrors _project_root() in tools/calibration/report.py — keep in step."""
    base = (
        os.environ.get("LOCALAPPDATA")              # Windows, always set
        or os.environ.get("XDG_DATA_HOME")          # Linux, if configured
        or Path.home() / ".local" / "share"         # Linux default
    )
    return Path(base) / "evka_position"


def _log_crash(exc_type, exc, tb) -> None:
    try:
        log = _log_dir() / "crash.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} ---\n")
            traceback.print_exception(exc_type, exc, tb, file=f)
    except OSError:
        pass  # a crash logger that itself crashes is worse than no crash logger
    sys.__excepthook__(exc_type, exc, tb)


def main() -> int:
    sys.excepthook = _log_crash
    from tools.evka_gui.__main__ import main as gui_main
    return gui_main()


if __name__ == "__main__":
    sys.exit(main())
