"""Compatibility shim for the renamed EVKA GUI package."""

from tools.evka_gui import EvkaWindow, run

__all__ = ["EvkaWindow", "run"]
