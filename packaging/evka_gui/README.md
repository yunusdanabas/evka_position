# packaging/evka_gui

Turns `tools/evka_gui` into a double-clickable Windows app. Users need no Python.

**Start here: [WINDOWS.md](WINDOWS.md)** — prerequisites, build, verification, troubleshooting,
and how to make changes without breaking the frozen build.

| File | What it is |
|---|---|
| [`WINDOWS.md`](WINDOWS.md) | The guide. Read this one. |
| `build_windows.ps1` | The build. Run from the repo root on Windows. |
| `build_linux.sh` | Validates the spec + import graph on Linux. Produces a Linux binary, not a shippable one. |
| `evka_gui.spec` | PyInstaller config — what gets bundled, what's excluded, and why. |
| `evka_gui_win.py` | Frozen entry point. Also installs the crash log. |
| `make_replay_csv.py` | Generates synthetic frames so the GUI can be tested with no hardware. |
| `README-WINDOWS.txt` | Ships inside the zip, for the end user. Not for developers. |

Quick build, from the **repo root**:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\evka_gui\build_windows.ps1
```

Output is `dist\EvkaGUI\` plus `EvkaGUI-win64-v<version>.zip`. That zip is the shippable
unit — self-contained, with its own Python and Qt.
