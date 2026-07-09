"""Deprecated import shim for `tools.evka_gui.gui`."""

from tools.evka_gui.gui import EvkaWindow, run

EvkaV2Window = EvkaWindow

__all__ = ["EvkaWindow", "EvkaV2Window", "run"]
