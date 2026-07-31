# packaging/evka_gui

Turns `tools/evka_gui` into something you can hand to an operator. Two shippable zips:
a Windows app that needs no Python, and a portable source zip that runs anywhere.

**Start here: [WINDOWS.md](WINDOWS.md)** — prerequisites, build, verification, troubleshooting,
and how to make changes without breaking the frozen build.

| File | What it is |
|---|---|
| [`WINDOWS.md`](WINDOWS.md) | The guide. Read this one. |
| `build_windows.ps1` | The Windows build. Run from the repo root **on Windows**. |
| `build_source_zip.sh` | The portable build. Runs anywhere, including Linux. |
| `build_linux.sh` | Validates the spec + import graph on Linux. Produces a Linux binary, not a shippable one. |
| `evka_gui.spec` | PyInstaller config — what gets bundled, what's excluded, and why. |
| `evka_gui_win.py` | Frozen entry point. Also installs the crash log. |
| `make_replay_csv.py` | Generates synthetic frames so the GUI can be tested with no hardware. |
| `README-WINDOWS.txt` | Ships inside the Windows zip, for the end user. Not for developers. |

## Windows bundle

From the **repo root**, on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\evka_gui\build_windows.ps1
```

Output is `dist\EvkaGUI\` plus `EvkaGUI-win64-v<version>.zip` (~80 MB) — self-contained,
with its own Python and Qt.

PyInstaller cannot cross-compile, so this genuinely needs Windows. Cross-building under
Wine does work, but the result cannot be smoke-tested on real Windows and Wine 9.0 forces
a numpy 1.x pin (its `ucrtbase.dll` lacks `crealf`, which numpy 2.x calls on import) — so
treat a Wine-built artifact as needing a real-Windows check before distribution.

## Portable source zip

From the **repo root**, on any OS:

```bash
./packaging/evka_gui/build_source_zip.sh          # version comes from pyproject.toml
```

Output is `EvkaGUI-src-v<version>.zip` (~170 KB): the five `tools/` packages the GUI
actually imports, plus `requirements.txt` and a `RUN.txt`. Needs Python 3.10+ on the
target machine. This is the only shippable artifact for Linux and macOS operators.

Both scripts verify rather than assume — each launches the built app in replay mode and
fails if it exits early. Both zips are gitignored; they belong on a GitHub release.
