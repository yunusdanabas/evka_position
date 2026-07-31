# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the EVKA Position GUI (Windows onedir build).

Run from the REPO ROOT, on Windows, in a clean venv:
    pyinstaller packaging/evka_gui/evka_gui.spec

Set EVKA_CONSOLE=1 to build the console variant for support/debugging.
"""

import os
from PyInstaller.utils.hooks import collect_all

# Repo root — SPECPATH is packaging/evka_gui/, so go up two levels.
ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))

CONSOLE = os.environ.get("EVKA_CONSOLE") == "1"
NAME = "EvkaGUI-console" if CONSOLE else "EvkaGUI"

# PyQt5 must be collected wholesale: the Windows platform plugin
# (platforms/qwindows.dll) is not a Python import, and without it the app dies
# silently before showing a window. pyqtgraph is collected because gui.py:604
# and position_checker/gui.py:221 import it lazily inside a function.
datas, binaries, hiddenimports = [], [], []
for pkg in ("PyQt5", "pyqtgraph"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

hiddenimports += [
    # ws_client.py guards this import, so a missing bundle is not a crash —
    # the WebSocket transport just fails at connect time. Must be explicit.
    "PyQt5.QtWebSockets",
    "PyQt5.QtNetwork",
    # pyserial picks its backend by sys.platform at runtime.
    "serial.tools.list_ports",
    "serial.tools.list_ports_windows",
]

icon_path = os.path.join(SPECPATH, "evka.ico")
if not os.path.exists(icon_path):
    icon_path = None

a = Analysis(
    [os.path.join(SPECPATH, "evka_gui_win.py")],
    pathex=[ROOT],          # evka_gui imports tools.* absolutely
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tools.evka_gui.tests",
        "tools.position_checker.tests",
        "pytest",
        # Other Qt bindings: PyInstaller hard-errors if two are collected, and
        # pyqtgraph probes for all of them at import time.
        "PySide2",
        "PySide6",
        "PyQt6",
        # Large and unused — QtWebEngine alone is ~150 MB if present in the venv.
        "PyQt5.QtWebEngine",
        "PyQt5.QtWebEngineWidgets",
        "PyQt5.QtWebEngineCore",
        "PyQt5.QtBluetooth",
        "PyQt5.QtDesigner",
        "PyQt5.QtQuick",
        "PyQt5.QtQml",
        "matplotlib",
        "tkinter",
        "IPython",
        # PyOpenGL must NOT be bundled. This app never uses it (the 3D views are
        # software-rendered QPainter — see position_checker/gui.py), but
        # pyqtgraph.widgets.RawImageWidget imports it unconditionally at package
        # import time. When PyOpenGL is present in the build environment it gets
        # collected without its platform plugins, and then fails at runtime with
        #     TypeError: 'NoneType' object is not callable
        # from OpenGL/platform/__init__.py:_load. pyqtgraph guards that import
        # with `except (ImportError, AttributeError)`, which does NOT catch a
        # TypeError, so the app dies on startup. Excluding it makes the import a
        # clean ImportError, which pyqtgraph handles (HAVE_OPENGL = False).
        # Verified: bundle crashes on launch without this, runs with it.
        "OpenGL",
        "OpenGL_accelerate",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX off: compressed sections are a strong antivirus heuristic trigger and
    # buy little on an already-large Qt bundle.
    upx=False,
    console=CONSOLE,
    disable_windowed_traceback=False,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=NAME,
)
