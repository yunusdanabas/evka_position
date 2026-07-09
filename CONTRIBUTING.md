# Development Setup & Contributing

How to set up a machine to build the firmware, run the Python tools, and (optionally) build the
Windows CMD app. Covers **Ubuntu 24.04** and **Windows 10/11**. If a step differs by OS, both are
shown side by side.

> New here? Read **[HANDOFF.md](HANDOFF.md)** first for the project tour, then use this to get set up.

---

## 0. Prerequisites at a glance

| You want to work on… | You need |
|---|---|
| Firmware (ESP32 / ESP32-S3) | PlatformIO (Python-based) + a USB-serial driver |
| Python tools (visualizer, IPT, calibration) | Python 3.8+ (3.10+ recommended) |
| The CMD C# GUI (Windows only) | .NET 8 SDK |
| Everything | Git |

You do **not** need all of it — install only what you'll touch.

---

## 1. Git

```bash
# Ubuntu
sudo apt update && sudo apt install git

# Windows: install Git for Windows (https://git-scm.com/download/win)
#          — includes "Git Bash", which makes the Linux commands below work.
```

Clone:
```bash
git clone <repo-url> evka_position
cd evka_position
```

Line endings are normalized by `.gitattributes` (LF everywhere), so editing on Windows won't
create spurious diffs.

---

## 2. Firmware — PlatformIO

The firmware uses **PlatformIO only** (Arduino IDE / `arduino-cli` are not supported). Two ways to
install it:

**Option A — CLI (recommended for both OSes):**
```bash
# Ubuntu
pip install -U platformio        # then `pio` is on PATH

# Windows (PowerShell) — 'pio' may not be on PATH; use the module form:
py -m pip install -U platformio
py -m platformio --version
```
Below, wherever you see `pio ...`, Windows users can substitute `py -m platformio ...`.

**Option B — VS Code:** install the **PlatformIO IDE** extension (works identically on both OSes).
Open the repo folder; PlatformIO reads `platformio.ini` and gives you build/upload/monitor buttons.

### Build environments (`platformio.ini`)

| Env | Board | Purpose |
|---|---|---|
| `wemos_d1_r32` | classic ESP32 | Main firmware, original board |
| `esp32s3_v4` | ESP32-S3-DevKitC-1 | Main firmware, **v4 PCB** (`-DPCB_V4`) |
| `button_remote` | ESP32-C3 | Wireless pendant |
| `test_*` | classic ESP32 | Standalone encoder test sketches |

### Build / flash / monitor

```bash
pio run -e esp32s3_v4                    # compile (use wemos_d1_r32 for the classic board)
pio run -e esp32s3_v4 --target upload    # flash over USB
pio device monitor                       # serial monitor @ 115200 baud
```

### USB drivers & serial ports (the #1 cross-platform gotcha)

| | Ubuntu 24 | Windows |
|---|---|---|
| **Driver** | Usually built in. Add yourself to `dialout`: `sudo usermod -aG dialout $USER` (log out/in) | Install the bridge driver: **CP210x** (Wemos D1 R32, ESP32-S3-DevKitC-1 "UART" port) or **CH340** (some clones). ESP32-S3 "USB" port enumerates natively (no driver). |
| **Port name** | `/dev/ttyUSB0` (bridge) or `/dev/ttyACM0` (native USB-CDC) | `COM3`, `COM4`, … — find it in **Device Manager → Ports (COM & LPT)** |
| **Find it** | `ls /dev/ttyUSB* /dev/ttyACM*` | Unplug/replug and watch which COM appears |

Specify a port explicitly if auto-detect fails:
```bash
pio run -e esp32s3_v4 --target upload --upload-port /dev/ttyUSB0   # Linux
pio run -e esp32s3_v4 --target upload --upload-port COM3           # Windows
```

> **ESP32-S3-DevKitC-1 has two USB-C ports.** "UART" goes through the CP2102 bridge (needs the
> Windows driver); "USB" is the chip's native USB. Either can flash/monitor — if one doesn't work,
> try the other.

First-boot behaviour: the firmware waits 2 s then zeroes the encoders — the machine **must be at
mechanical home** at that moment. Details in `pcb_design/EVKA_position_v4/FIRMWARE.md`.

---

## 3. Python tools

Python **3.8+** (3.10+ recommended). Always use a virtual environment.

```bash
# Create + activate a venv
python3 -m venv .venv            # Windows: py -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt  # or:  pip install -e .   (editable, from pyproject.toml)
```

Run the tools (from the repo root, with the venv active):
```bash
python -m tools.evka_gui --serial                     # unified control + 3D GUI (canonical)
python -m tools.evka_gui --tcp 192.168.1.50:8080      # same, over WiFi AP
python -m tools.ipt                                   # hidden-point ("Inverted Pen") measurement tool
python -m tools.ipt.solver                            # solver self-check, no hardware needed
python tools/calibration/calibrate.py                 # Kabsch world<->sensor calibration
```

> `tools.evka_gui_v2` and `tools.position_checker`'s `main`/`cmd_main` entry points are
> **deprecated shims** — see
> [tools/README.md](tools/README.md#evka_gui--unified-control-gui-canonical) for the migration table.

Run the tests (no hardware required):
```bash
pytest -q
```

> **PyQt5 on Windows** installs from pip like any other package — no extra system libraries.
> On some minimal Linux setups you may need `sudo apt install libxcb-xinerama0` for Qt to start.

Per-tool details are in each tool's `README.md` (`tools/<tool>/README.md`).

---

## 4. CMD C# app (Windows only)

The third-party CNC GUI under `firmware/src/CMD Soft/` is a **.NET 8 WinForms** app — it **runs on
Windows only**, but it *builds* on any OS with the .NET 8 SDK (`EnableWindowsTargeting` is set in
the csproj; CI builds it on Linux).

```powershell
# Requires the .NET 8 SDK (https://dotnet.microsoft.com/download)
cd "firmware/src/CMD Soft"
dotnet build CMDScanner.csproj -c Release
dotnet run  --project CMDScanner.csproj
```

It connects to the device's TCP server at `192.168.1.50:8080`. Build artifacts (`bin/`, `obj/`) are
git-ignored. This app came from an external vendor; see `firmware/src/CMD Soft/README.md`.

---

## 5. Coding conventions

- **C/C++/C#:** 4-space indent. Keep the existing `SphericalSensor.h` config-`#define` block as the
  single source of truth for pins/features — don't scatter magic numbers.
- **Python:** PEP 8, 4-space indent, type hints on public functions, a module docstring per file.
- `.editorconfig` enforces indent/charset/EOL automatically in most editors.
- **Hardware needs tuning knobs.** Encoder direction, PPR, and battery divider are calibration
  values — leave them adjustable (they already are), don't hardcode over them.

## 6. Before you commit

1. Firmware changes → `pio run -e wemos_d1_r32 -e esp32s3_v4` builds clean.
2. Python changes → `pytest -q` passes (runs every suite under `tools/`).
3. Commit in small, coherent chunks with a clear message (see `git log` for the style).
4. Don't commit build artifacts — `.gitignore` already excludes `.pio/`, `__pycache__/`, `bin/`,
   KiCad backups, etc.

## 7. Where to go next

- System internals → **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**
- Firmware source tour → **[docs/firmware/CODE_WALKTHROUGH.md](docs/firmware/CODE_WALKTHROUGH.md)**
- Any topic → **[docs/README.md](docs/README.md)** (documentation index)
