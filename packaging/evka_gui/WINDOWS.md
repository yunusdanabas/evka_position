# Building and shipping the EVKA Position GUI on Windows

Everything you need to turn `tools/evka_gui` into an `EvkaGUI.exe` that a non-technical user
can double-click. No Python on their machine.

**Read this once, top to bottom, before running anything.** The build itself is one command;
the value here is in the verification and troubleshooting sections.

---

## 0. What you are building

| | |
|---|---|
| **Input** | This repo, on a Windows machine |
| **Output** | `dist\EvkaGUI\` — a ~250–350 MB folder containing `EvkaGUI.exe` + its own Python + Qt DLLs |
| **Shippable unit** | `EvkaGUI-win64-v0.2.1.zip` — that folder, zipped |
| **User experience** | Unzip → open folder → double-click `EvkaGUI.exe` |

The zipped folder is completely self-contained. It does not read anything from this repo at
runtime, and the user needs no Python, no venv, and no pip.

**This is one GUI, not two.** The Windows build freezes the exact same source that runs on
Linux — there is no separate Windows port and no feature was dropped. Anything you fix in
`tools/evka_gui` appears in the next build automatically.

---

## 1. Prerequisites (one time)

1. **Python 3.12 (64-bit)** — <https://www.python.org/downloads/>
   Tick **"Add python.exe to PATH"** during install. Verify:
   ```powershell
   py -3.12 --version
   ```
   3.10 and 3.11 also work. Do not use the Microsoft Store build — its sandboxed paths
   confuse PyInstaller.

2. **Git** (to clone the repo) — <https://git-scm.com/download/win>

3. **The repo**, anywhere you like:
   ```powershell
   git clone <repo-url> evka_position
   cd evka_position
   ```

You do **not** need Visual Studio, a C compiler, or admin rights. PyInstaller ships a
prebuilt bootloader.

---

## 2. Build

From the **repo root**, in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\evka_gui\build_windows.ps1
```

Takes roughly 3–8 minutes. Useful variants:

```powershell
# Also build the console version (shows a terminal with error output — for debugging)
... -File packaging\evka_gui\build_windows.ps1 -Console

# Stamp a different version into the zip filename
... -File packaging\evka_gui\build_windows.ps1 -Version 0.3.0

# Use a different interpreter
... -File packaging\evka_gui\build_windows.ps1 -Python "py -3.11"
```

### What the script does, in order

Knowing this makes failures diagnosable instead of mysterious:

1. **Creates a clean venv** at `.venv-build\`, deleting any previous one.
   *Why clean:* PyInstaller bundles whatever it can find. Building from your everyday
   environment silently bloats the exe and can inject broken packages (see PyOpenGL, §5).
2. **Installs** the project (`pip install -e .`) plus PyInstaller.
3. **Pre-flight import check** — fails loudly if `QtWebSockets`, `pyqtgraph`, `numpy`,
   or `pyserial` are missing. **This check exists because PyInstaller does not fail on a
   missing optional import** — it logs one line and builds an app that launches fine and is
   silently broken. Do not remove it.
4. **Runs PyInstaller** against `evka_gui.spec`.
5. **Post-flight launch test** — starts the frozen exe in replay mode for 8 seconds. If it
   dies, the build fails instead of handing you a broken zip.
6. **Copies** `README-WINDOWS.txt` next to the exe and **zips** the folder.

### If it succeeds

```
Built: C:\...\evka_position\EvkaGUI-win64-v0.2.1.zip (<size> MB)
Now smoke-test on a clean Windows machine with no Python installed.
```

A reference Linux build of the same spec came to 222 MB unpacked, so expect the Windows zip
in the tens of MB and the unpacked folder in the low hundreds. An exact figure isn't known
until you run it.

---

## 3. Verify before shipping

Do this on a **clean Windows machine with no Python installed**. That is the real acceptance
test — a dev machine with Python can mask a missing DLL and let a broken build look fine.

Copy the zip over, unzip, and work down the list:

| # | Check | What it proves |
|---|---|---|
| 1 | Double-click `EvkaGUI.exe` — window appears, no black console behind it | Qt platform plugin (`qwindows.dll`) bundled |
| 2 | Plots draw and axes are labelled | pyqtgraph + numpy bundled |
| 3 | Generate a replay file and load it (see §4) | Full data pipeline, no hardware needed |
| 4 | Click **Refresh** by the port list with the board plugged in — a COM port appears | pyserial + Windows backend |
| 5 | Connect over serial at 115200, confirm live frames | Serial transport |
| 6 | Connect over **TCP** (`192.168.1.50:8080`) | Sockets + firewall rule accepted |
| 7 | Connect over **WebSocket** (host, port 80, `/ws`) | **The one that catches a missing `QtWebSockets`** |
| 8 | Open **Remote Tester…** from the toolbar | `tools.remote_tester` was walked by the bundler |
| 9 | Open **Calibration…**, save a session, then check `%LOCALAPPDATA%\evka_position\` | Frozen data root works and is writable |
| 10 | Export a session CSV, **accept the default filename** — it lands in Documents | Export paths don't resolve into the app folder |
| 11 | Force a crash, check `%LOCALAPPDATA%\evka_position\crash.log` | Crash logging works for support |
| 12 | Copy only `EvkaGUI.exe` to the Desktop and run it — it must fail | Confirms the "keep the folder together" warning is real |

> **Never skip #7.** `ws_client.py` catches a missing `QtWebSockets` on purpose and degrades
> gracefully, so an app built without it starts perfectly and only fails when a user clicks
> WebSocket. This has already happened once during development.

---

## 4. Testing without hardware

```powershell
# Generate 400 synthetic frames
py -3.12 packaging\evka_gui\make_replay_csv.py frames.csv

# From source
py -3.12 -m tools.evka_gui --replay frames.csv

# From the built exe
dist\EvkaGUI\EvkaGUI.exe --replay frames.csv
```

Replay files are plain dumps of firmware `DATA,` lines, so a file recorded from real hardware
via the **Record** button works identically.

Other launch modes:

```powershell
EvkaGUI.exe                              # open disconnected
EvkaGUI.exe --serial COM3 --baud 115200
EvkaGUI.exe --tcp 192.168.1.50:8080
EvkaGUI.exe --ws 192.168.1.50
```

---

## 5. Troubleshooting

### The app closes immediately with no message

`--windowed` builds have no console, so tracebacks go nowhere visible. Two ways in:

1. **Read the crash log:** `%LOCALAPPDATA%\evka_position\crash.log`
2. **Build the console variant:** `-Console`, then run `dist\EvkaGUI-console\EvkaGUI-console.exe`
   from PowerShell and read the traceback directly.

### `ModuleNotFoundError` in the frozen app but not from source

PyInstaller missed a lazy or conditional import. Add it to `hiddenimports` in `evka_gui.spec`
and rebuild. The full list of what it dropped is in
`build\evka_gui\warn-evka_gui.txt` — search it for your module.

### `TypeError: 'NoneType' object is not callable` from `OpenGL/platform`

Already fixed, but if you edit the spec, know the trap: pyqtgraph imports PyOpenGL
unconditionally via `RawImageWidget`. If PyOpenGL is present in the build venv it gets
collected without its platform plugins and blows up on startup. pyqtgraph guards that import
with `except (ImportError, AttributeError)`, which does **not** catch this `TypeError`.
`OpenGL` and `OpenGL_accelerate` are in the spec's `excludes` — leave them there. This app
never uses OpenGL; the 3D view is software-rendered.

### WebSocket fails but TCP works

`QtWebSockets` was not bundled. Confirm it is importable in the build venv:

```powershell
.venv-build\Scripts\python.exe -c "from PyQt5 import QtWebSockets; print('ok')"
```

If that fails, the venv's PyQt5 is incomplete — reinstall it with `pip install --force-reinstall PyQt5`.

### No COM ports listed

Almost always a **driver**, not the app. Install the USB-UART driver and reboot:
- CH340/CH341 — <http://www.wch-ic.com/downloads/CH341SER_EXE.html>
- CP210x — <https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers>

Confirm the port exists in Device Manager under *Ports (COM & LPT)* first. Also rule out a
charge-only USB cable.

### Network connections silently fail

The Windows Firewall prompt was dismissed on first run. Re-enable it in
*Windows Defender Firewall → Allow an app*, or delete the rule so the prompt reappears.

### "Windows protected your PC" (SmartScreen)

Expected — the exe is unsigned. Click **More info → Run anyway**. To remove this permanently
you need an Authenticode certificate; see §8.

### Antivirus quarantines the exe

Also expected for unsigned PyInstaller output. The build deliberately avoids the two worst
triggers (one-file mode and UPX compression). If a specific engine flags it, submit a false
positive report to that vendor. If it becomes chronic, Nuitka produces genuinely compiled
binaries that trip heuristics far less often — a bigger change, kept in reserve.

### Build fails at `pip install -e .`

Run PowerShell from the repo root, not from `packaging\evka_gui\`. The script sets its own
working directory, but a partially-cloned repo or a missing `pyproject.toml` will break it.

---

## 6. Making changes

### Day-to-day: don't rebuild

You do not need to freeze anything to work on the GUI. Set up a normal dev environment once:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e .
pip install pytest pytest-forked
```

Then run and test from source:

```powershell
python -m tools.evka_gui --replay frames.csv
python -m pytest -q
```

This is a seconds-long loop instead of a minutes-long one. Freeze only when you're ready to
ship. **The code is identical either way** — the exe is just this source plus an interpreter.

### Where things live

| To change… | Edit |
|---|---|
| Main window, plots, toolbar | `tools/evka_gui/gui.py` |
| Serial / TCP / WebSocket | `tools/evka_gui/transport.py`, `ws_client.py` |
| Calibration dialog | `tools/evka_gui/calibration.py` |
| Quick IPT panel | `tools/evka_gui/ipt_panel.py`, `ipt_window.py` |
| Colours / design tokens | `tools/evka_gui/tokens.py` (reference values; most widgets still hardcode hexes) |
| **What gets bundled** | `packaging/evka_gui/evka_gui.spec` |
| **Build steps** | `packaging/evka_gui/build_windows.ps1` |
| **Startup + crash log** | `packaging/evka_gui/evka_gui_win.py` |
| **End-user instructions** | `packaging/evka_gui/README-WINDOWS.txt` |

### Rules that keep the frozen build working

These are the ways a source-only change breaks the exe. All four have bitten already.

1. **Never derive a writable path from `__file__`.** A frozen app's `__file__` points inside
   the bundle, which is read-only. Use `report.PROJECT_ROOT` (see
   `tools/calibration/report.py`), which redirects to `%LOCALAPPDATA%\evka_position\` when
   frozen.

2. **Never pass a bare filename to `QFileDialog`.** It resolves against the working directory,
   which for a shortcut is the install folder. Use `default_export_path()` from
   `tools/evka_gui/session_utils.py`.

3. **New third-party dependency?** Add it to `pyproject.toml`, then rebuild and check
   `build\evka_gui\warn-evka_gui.txt`. If it's imported lazily (inside a function) or
   conditionally, add it to `hiddenimports` in the spec.

4. **New directory under `tools/`?** Give it an `__init__.py`. A namespace package without one
   may be skipped by both setuptools and PyInstaller — which is exactly how
   `tools/remote_tester/` broke in the frozen build only.

### Validating spec changes without a Windows machine

If you work on Linux, this catches most freezing bugs in about a minute:

```bash
./packaging/evka_gui/build_linux.sh
```

It builds a Linux binary — not shippable, but it exercises the spec, the whole import graph,
and the frozen-path code. It is how the PyOpenGL crash above was found. It cannot tell you
anything about Windows DLLs, COM ports, or SmartScreen.

### After any change, before shipping

```powershell
python -m pytest -q                                    # 198 tests
powershell -File packaging\evka_gui\build_windows.ps1  # rebuild
```

Then re-run §3 on a clean machine. At minimum re-run checks 1, 3, 7, 9 — those cover the
failure modes unique to freezing.

---

## 7. Shipping to users

1. Build, and verify per §3.
2. Rename the zip so the version is obvious: `EvkaGUI-win64-v0.2.1.zip`.
3. Hand it over by USB, shared drive, or internal file share.
4. Tell users to **unzip first**. Running the exe from inside Windows' zip preview appears to
   work and then fails confusingly.

`README-WINDOWS.txt` ships inside the folder and covers drivers, firewall, file locations, and
the crash log. Point users at it rather than re-explaining.

> **Public distribution is not cleared.** This repo has no license file, and both `HANDOFF.md`
> and `README.md` state it must not be redistributed or described as production-ready. Keep
> this to trusted-lab handoff until that is resolved.

---

## 8. Optional next steps

Not needed for a working handoff; listed so the path is known.

| Step | Effort | Why |
|---|---|---|
| **Icon** — drop `evka.ico` into this folder | minutes | The spec picks it up automatically; without it the exe uses the generic Python icon |
| **Inno Setup installer** — Start Menu + Desktop shortcuts, uninstaller | 0.5–1 day | Nicer than "unzip this folder". Install per-user to `%LOCALAPPDATA%\Programs\EvkaGUI` to avoid a UAC prompt, and set the shortcut's working directory to Documents |
| **CI builds** — `windows-latest` job in `.github/workflows/ci.yml` | 0.5–1 day | Reproducible artifacts without a dedicated Windows box. Note CI cannot test COM ports or reach the device |
| **Code signing** — Authenticode | 1–3 days + procurement | Removes SmartScreen warnings. OV ~$200–400/yr (reputation builds over weeks); EV ~$300–500/yr (immediate trust); Azure Trusted Signing ~$10/mo if your org qualifies. **Only relevant once public distribution is licensed** |
| **Size trim** — currently ~250–350 MB | hours | Add unused Qt modules to `excludes`. Do this last; a missing DLL costs far more than disk space |
