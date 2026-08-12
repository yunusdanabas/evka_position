# Evka Position: Spherical 3D Positioning Prototype

> Turkce operator guide: [README_TR.md](README_TR.md)

Evka Position is an existing-repository prototype that derives a 3D point from two rotary
encoders and one draw-wire encoder:

```text
encoder counts -> (radius, theta, phi) -> sensor-frame (X, Y, Z) mm
```

Start with [HANDOFF.md](HANDOFF.md), use [docs/ONBOARDING.md](docs/ONBOARDING.md) for the
self-contained setup and safety baseline, and browse [docs/README.md](docs/README.md) for the
documentation status index.

## Handoff Status

| Area | Approved statement |
|---|---|
| Current hardware | The assembled ESP32-S3 v4 carrier is the current prototype. It is not a production-qualified product. |
| Firmware | Shared classic/v4 firmware and all PlatformIO environments build successfully. No new flash or hardware validation is claimed. |
| Telemetry | Live 20 Hz telemetry has been observed in earlier work. Full end-to-end hardware acceptance remains open. |
| Repeatability | Theta count loss is unresolved. The recorded return error reached about 1.1 degrees, approximately 35 mm at 2 m. |
| Coordinates | Firmware and `tools/evka_gui` report the sensor frame. No endpoint/world transform has been accepted. |
| Host application | `tools/evka_gui` is the canonical operator GUI. The vendor C# application has been deleted; the TCP compatibility protocol remains supported. |
| Legal/release | The repository has no redistribution license and makes no public production-readiness claim. |

Do not hide theta slip, backlash, or lost counts by changing PPR or fitting a world transform.
Resolve repeatability first, then calibrate scale, fit a candidate transform, and validate it on
hold-out points.

Known repeatability record:
[docs/calibration/sessions/2026-07-17_repeatability.md](docs/calibration/sessions/2026-07-17_repeatability.md).

### Software Verification Record

| Check | Result |
|---|---|
| `QT_QPA_PLATFORM=offscreen pytest -q -m qt_heavy --forked` | PASS: 44 tests |
| `QT_QPA_PLATFORM=offscreen pytest -q -m "not qt_heavy"` | PASS: 160 tests, 11 subtests (204 total with the above) |
| Dashboard harness (`npm ci && npm test`) | PASS: 50 checks |
| `python -m compileall tools -q` | PASS |
| `python -m tools.ipt.solver` | PASS: 0.405 mm target error |
| PlatformIO build matrix | PASS: all 10 configured environments |

The Python suite runs as **two invocations on purpose**. Modules marked `qt_heavy` build
pyqtgraph widgets that segfault when they share a process, so they run forked; forking only
works if the parent has not built a QApplication first, which is why they get their own
invocation. A plain `pytest -q` is still expected to segfault intermittently — use the two
commands above. Background: [docs/CI_PYTEST_SEGFAULT_LOG.md](docs/CI_PYTEST_SEGFAULT_LOG.md).

These are software-only results. Hardware acceptance remains governed by the open
gates in [docs/integration/final_integration_validation.md](docs/integration/final_integration_validation.md).

## Hardware Baseline

- MCU: ESP32-S3-DevKitC-1 on the v4 carrier; classic Wemos D1 R32 remains a compatibility target.
- Theta/Phi: Autonics E40S6-5000, 20,000 counts/rev at X4 quadrature.
- Radius: OPKON DWEM2 P2000, theoretical 8,000 counts/rev at X4 quadrature.
- Main firmware encoder driver: `madhephaestus/ESP32Encoder` using ESP32 PCNT.
- Encoder outputs are 5 V; the v4 carrier includes the signal dividers required by the ESP32.

### v4 Connector Map

| Connector | Axis | PCB pin order | GPIO |
|---|---|---|---|
| J1 | Draw-wire | `1=A, 2=GND, 3=B, 4=+5V` | A=7, B=8 |
| J2 | Phi | `1=+5V, 2=A, 3=GND, 4=B` | A=4, B=5 |
| J3 | Theta | `1=A, 2=GND, 3=B, 4=+5V` | A=9, B=10 |

Cable colors:

| Encoder | A | B | +5V | GND |
|---|---|---|---|---|
| E40S6 theta/phi | Black | White | Brown | Blue |
| DWEM2 draw-wire | Yellow | Green | Brown | White |

This connector order is derived from the v4 KiCad PCB/pad nets and the current firmware pin map.
It was **not physically reverified during this final documentation pass**. Verify the actual board
and cable before applying power.

Compile-time pins, calibration defaults, battery behavior, LED selection, and network constants
are defined in `firmware/src/SphericalSensor.h`. Runtime PPR values may be overridden by NVS, so
query `CONSTANTS` before a calibration session.

## Canonical Operator GUI

The host-tools package is version `0.2.1` and requires Python 3.10 or newer.

Install the Python dependencies from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the canonical GUI:

```bash
python -m tools.evka_gui
python -m tools.evka_gui --serial /dev/ttyACM0 --baud 115200
python -m tools.evka_gui --tcp 192.168.1.50:8080
python -m tools.evka_gui --ws 192.168.1.50
python -m tools.evka_gui --replay frames.csv
```

`evka_gui` supports Serial, TCP, WebSocket, and replay; includes Quick IPT, diagnostics,
recording, snapshots, and the calibration-report workflow; and records raw sensor-frame data.
Software zero is a display/session offset only. The GUI does not apply an endpoint/world transform
to live telemetry, so its XYZ and IPT results remain in the sensor frame.

The standalone `tools/position_checker` entry points are legacy compatibility tools.

## Firmware Build and Flash

PlatformIO is the supported firmware toolchain. Build without uploading:

```bash
pio run -e esp32s3_v4
pio run -e wemos_d1_r32
pio run -e button_remote
```

Flash after wiring and safety review. Replace `/dev/ttyACM0` with the correct port
(`/dev/ttyUSB0` on some boards, `COMx` on Windows). Do not open the same port in two apps at once.

**Main device** (ESP32-S3 v4 carrier — current prototype):

```bash
pio run -e esp32s3_v4 --target upload --upload-port /dev/ttyACM0
pio device monitor -e esp32s3_v4
```

Classic Wemos compatibility target (not for the v4 carrier):

```bash
pio run -e wemos_d1_r32 --target upload --upload-port /dev/ttyUSB0
```

**Remote control** (ESP32-C3 pendant, ESP-NOW):

```bash
pio run -e button_remote --target upload --upload-port /dev/ttyACM0
pio device monitor -e button_remote
```

Bench-only pendant test firmware (own AP `REMOTE_TEST`, no ESP-NOW — see
[`tools/remote_tester/README.md`](tools/remote_tester/README.md)):

```bash
pio run -e button_remote_test --target upload --upload-port /dev/ttyACM0
```

The `test_*` environments use the classic Wemos pin map and must not be flashed onto the v4
carrier. See [CONTRIBUTING.md](CONTRIBUTING.md) and
[pcb_design/EVKA_position_v4/FIRMWARE.md](pcb_design/EVKA_position_v4/FIRMWARE.md) before any
flash or bring-up work.

## Protocol and Networking

The canonical, source-derived transport and command reference is
**[docs/PROTOCOL.md](docs/PROTOCOL.md)**. In summary:

- Serial: 115200 baud; machine-readable `DATA,...` at 20 Hz.
- WebSocket: `ws://<device>/ws`; `DATA,...` at 20 Hz.
- TCP: port 8080; separate `X...,Y...,Z...` and `SENSOR,...` lines at 20 Hz.
- `RAW_COUNTS` returns zero-relative counts, not absolute PCNT values.

The firmware's existing credentials and addresses are unchanged:

| Setting | Current value |
|---|---|
| AP SSID | `CMDCNC_EVKA` |
| AP password | `cmdcnc1234` |
| AP dashboard | `http://192.168.1.50` |
| TCP | `192.168.1.50:8080` |
| WebSocket | `ws://192.168.1.50/ws` |
| STA static profile | `192.168.1.84/24`, gateway `192.168.1.254` |

These fixed credentials and unauthenticated command channels are suitable only for an isolated,
trusted lab network. Do not expose the AP, TCP port, or WebSocket to an untrusted LAN or the public
internet. `WIFI_SET` changes stored STA credentials and reboots the device.

## Calibration Boundary

The active workflow is documented under [docs/calibration/](docs/calibration/). No shared/default
calibration JSON is checked in and no endpoint/world transform is accepted. After the repeatability,
calibration, and hold-out gates pass, a session JSON may be supplied explicitly to the legacy
visualizer with `--legacy-visualizer --calibration <session-calibration.json>`. The canonical
`tools/evka_gui` remains sensor-frame-only.

## Repository Areas

- Active: `firmware/src/`, `tools/evka_gui/`, `docs/PROTOCOL.md`, active calibration and v4 docs.
- Archive/reference: classic test material, integration history, GUI migration logs, and
  `docs/hardware_design/12v_legacy/`.
- Research: `laser_radius/` and `docs/research/`; these are studies, not implemented baseline.

## License and Redistribution

There is no repository license file. Default copyright restrictions apply. Do not redistribute,
publish a product release, or represent this prototype as production-ready until ownership and
licensing are explicitly resolved. Historical vendor C# material has been deleted; that cleanup does
not affect the retained TCP wire protocol.
