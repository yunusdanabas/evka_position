# Development Setup and Contribution Rules

Read [HANDOFF.md](HANDOFF.md) first. This repository is an existing hardware prototype, not a
production release. Install only the tools needed for the part you are changing.

## Prerequisites

| Work area | Required tools |
|---|---|
| Firmware | Git, Python, PlatformIO, appropriate USB driver |
| Host tools/docs | Python 3.10+ required, virtual environment |
| PCB/docs | KiCad only when editing board files |

The vendor C# application has been deleted and is not part of the supported development workflow.
Do not add new dependencies on it. TCP port 8080 and the documented line protocol remain supported.

## Clone and Python Setup

The host-tools package version is `0.2.1`.

```bash
git clone <repo-url> evka_position
cd evka_position
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell equivalents:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

Run the canonical GUI from the repository root:

```bash
python -m tools.evka_gui
python -m tools.evka_gui --tcp 192.168.1.50:8080
python -m tools.evka_gui --serial /dev/ttyACM0 --baud 115200
```

`tools/evka_gui` is sensor-frame-only. Do not document software zero or a copied
`calibration.json` as an accepted machine/world coordinate frame.

## Firmware Toolchain

Use PlatformIO. Arduino IDE and `arduino-cli` are not the supported project workflow.

```bash
python -m pip install -U platformio
pio run -e esp32s3_v4
pio run -e wemos_d1_r32
```

Windows users may replace `pio` with `py -m platformio`.

| Environment | Target | Status/use |
|---|---|---|
| `esp32s3_v4` | ESP32-S3 v4 carrier | Current prototype main firmware |
| `esp32s3_v4_rgb38` | v4 with RGB GPIO38 override | Source-supported board variant; verify actual DevKit before use |
| `wemos_d1_r32` | Classic ESP32 | Compatibility main firmware |
| `button_remote` | ESP32-C3 | Wireless pendant firmware |
| `test_*` | Classic Wemos pin map | Standalone bench sketches; never flash to v4 |

USB ports are commonly `/dev/ttyACM0` or `/dev/ttyUSB0` on Linux and `COMx` on Windows. On
Linux, add the user to `dialout` if required. The ESP32-S3 DevKit may expose native USB and a
USB-UART bridge; do not open the same port in two applications at once.

Future flash example, after wiring and safety review:

```bash
pio run -e esp32s3_v4 --target upload --upload-port /dev/ttyACM0
pio device monitor -e esp32s3_v4
```

The firmware waits two seconds and captures mechanical home as its zero. Read
[pcb_design/EVKA_position_v4/FIRMWARE.md](pcb_design/EVKA_position_v4/FIRMWARE.md) before any
hardware work. This documentation reconciliation itself performed no hardware checks.

## Software Checks

Use the smallest relevant check for a change:

```bash
pytest -q
python -m tools.ipt.solver
pio run -e esp32s3_v4
```

Do not run hardware checks, upload, or serial-monitor commands unless the task explicitly calls for
them and the board wiring has been reviewed.

## Source and Documentation Boundaries

- `firmware/src/SphericalSensor.h` is the source of truth for compile-time pins, calibration
  defaults, feature flags, LED selection, battery settings, and network constants.
- `firmware/src/EvkaPosition.cpp` is the command/reply source; `CmdTcpServer.cpp` defines TCP
  framing. Keep [docs/PROTOCOL.md](docs/PROTOCOL.md) aligned with both.
- `tools/evka_gui` is the canonical host GUI. `tools/position_checker` standalone entry points are
  legacy compatibility tools.
- Preserve the distinction between sensor frame, display software-zero frame, and a candidate
  world transform.
- Hardware calibration knobs must remain adjustable; do not hardcode around real sensor drift or
  mechanical defects.

## v4 Documentation Rule

The current PCB-derived connector order is:

| Connector | Order |
|---|---|
| J1 draw-wire | `1=A, 2=GND, 3=B, 4=+5V` |
| J2 phi | `1=+5V, 2=A, 3=GND, 4=B` |
| J3 theta | `1=A, 2=GND, 3=B, 4=+5V` |

It was not physically reverified in the final documentation pass. Do not convert the PCB-derived
statement into a physical-validation claim without recording the actual continuity check.

## Security and Credentials

Credentials in the firmware are unchanged. They are prototype lab credentials, and command
channels have no application-level authentication. Do not commit new secrets, include passwords in
test artifacts, or expose TCP/WebSocket services outside an isolated trusted lab network.

## Before Submitting a Change

1. Keep the diff focused and preserve unrelated uncommitted work.
2. Run the smallest relevant software check; record anything not run.
3. For documentation, run `git diff --check` and verify changed relative Markdown links.
4. Do not claim hardware verification unless the exact physical check was performed and recorded.
5. Do not claim an endpoint transform is accepted without passing calibration and hold-out results.
6. Do not add redistribution or production claims; this repository has no license file.

Continue with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[docs/PROTOCOL.md](docs/PROTOCOL.md), and [docs/README.md](docs/README.md).
