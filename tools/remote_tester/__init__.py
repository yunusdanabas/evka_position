"""remote_tester — standalone GUI for the ESP-NOW button pendant test firmware.

This file makes the directory a real package. Without it, setuptools'
``packages.find`` and PyInstaller's module graph both skip it, and
``from tools.remote_tester.remote_test_gui import RemoteTestWindow``
(tools/evka_gui/remote_window.py) fails only in the frozen build.
"""
