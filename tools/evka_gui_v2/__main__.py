"""Deprecated entry point. Use `python -m tools.evka_gui`."""

from __future__ import annotations

import sys
import warnings

from tools.evka_gui.__main__ import main


if __name__ == "__main__":
    warnings.warn(
        "tools.evka_gui_v2 is deprecated; use tools.evka_gui",
        DeprecationWarning,
        stacklevel=2,
    )
    sys.exit(main())
