# Developer Onboarding

This page is the self-contained setup and safety baseline for the existing v4 prototype. No private
repository or handbook is required.

## Current Reality

- The assembled ESP32-S3 v4 carrier and PlatformIO environment `esp32s3_v4` are the current
  prototype baseline. The classic Wemos target remains for compatibility and standalone tests.
- Earlier sessions observed 20 Hz telemetry. Completed software-only verification is recorded in
  [../HANDOFF.md](../HANDOFF.md); this handoff establishes no new flash, continuity,
  wiring, or motion result.
- Theta count loss is unresolved. One recorded return error reached about 1.1 degrees, roughly
  35 mm at 2 m. Radius and phi were more repeatable in that session.
- No endpoint/world transform or shared/default calibration JSON is accepted.
- `tools/evka_gui` is canonical and displays sensor-frame data only. Software zero is a local
  display/session offset, not a machine coordinate transform.
- The vendor C# application has been deleted. TCP port 8080 and its protocol remain supported.
- This repository does not authorize robot motion or unsupervised operation. Follow the site's
  physical safety process before moving connected machinery.

Read [../HANDOFF.md](../HANDOFF.md), [ARCHITECTURE.md](ARCHITECTURE.md), and
[PROTOCOL.md](PROTOCOL.md) before changing behavior.

## Workstation Setup

Host-tools package version `0.2.0` requires Python 3.10+. PlatformIO is required only for firmware
work.

```bash
git clone <repo-url> evka_position
cd evka_position
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

Optional software-only checks:

```bash
QT_QPA_PLATFORM=offscreen pytest -q
pio run -e wemos_d1_r32 -e esp32s3_v4 -e esp32s3_v4_rgb38
python -m tools.ipt.solver
cd tools/webdash_harness && npm ci && npm test
```

The `test_*` PlatformIO environments target the classic Wemos pin map. Never flash them onto the
v4 carrier.

## v4 Wiring Safety

Have another person compare the physical board, KiCad files, and cable before power is applied.

| Port | Sensor | PCB-derived pin order | Cable colors |
|---|---|---|---|
| J1 | Draw-wire | `1=A, 2=GND, 3=B, 4=+5V` | Yellow A, White GND, Green B, Brown +5V |
| J2 | Phi | `1=+5V, 2=A, 3=GND, 4=B` | Brown +5V, Black A, Blue GND, White B |
| J3 | Theta | `1=A, 2=GND, 3=B, 4=+5V` | Black A, Blue GND, White B, Brown +5V |

J2 is intentionally different from J1 and J3. The order above is derived from v4 PCB/pad nets and
the current firmware mapping. It was **not physically reverified during this final pass**.

The encoders use 5 V signals; the v4 PCB includes dividers to ESP32 logic levels. Do not bypass
them. Place all axes at mechanical home before boot. The firmware waits two seconds and captures
that pose as zero, so movement during the window invalidates the session.

The S3 may enumerate as `/dev/ttyACM0` on native USB or `/dev/ttyUSB0` through a bridge. Do not open
the same port in PlatformIO monitor and a GUI simultaneously.

## First Session

Only perform these hardware steps after wiring and site safety review. They are instructions for a
future session, not checks completed by this reconciliation.

### 1. Observe the source-defined protocol

At mechanical home, monitor Serial at 115200 baud and send:

```text
PING
STATUS
CONSTANTS
RAW_COUNTS
```

Expected schemas and transport differences are in [PROTOCOL.md](PROTOCOL.md). In particular, TCP
emits separate XYZ and `SENSOR` records, and `RAW_COUNTS` reports counts relative to the most recent
zero offsets.

### 2. Use the canonical GUI

Close any serial monitor, then run one transport:

```bash
python -m tools.evka_gui --serial /dev/ttyACM0 --baud 115200
python -m tools.evka_gui --tcp 192.168.1.50:8080
python -m tools.evka_gui --ws 192.168.1.50
```

Confirm frame count and sensor-frame radius/theta/phi/XYZ are plausible. Do not interpret GUI XYZ
as accepted world coordinates.

### 3. Reproduce the blocking defect

1. Start at mechanical home and save zero-relative `RAW_COUNTS`.
2. Visit several marked points at different directions and radii.
3. Return to each point and home without re-zeroing.
4. Record raw counts and sensor-frame XYZ for every visit.
5. Separate theta, phi, and radius return errors.
6. Stop and inspect mechanics/signals if theta does not return; do not compensate with PPR.

Reference record:
[calibration/sessions/2026-07-17_repeatability.md](calibration/sessions/2026-07-17_repeatability.md).

## Calibration Boundary

- Fix theta repeatability before accepting encoder scale or a world transform.
- NVS namespace `evka_cal` overrides compile-time PPR defaults after reflashing; query
  `CONSTANTS` to see runtime values.
- Endpoint Kabsch calibration can correct rigid rotation/translation only. It cannot correct lost
  counts, scale error, backlash, slipping couplings, or flex.
- No shared/default calibration JSON is checked in or auto-loaded.
- A passing session JSON is an optional explicit transform for the legacy visualizer only; use
  `--legacy-visualizer --calibration <session-calibration.json>`. It does not make `evka_gui`
  world-frame-aware or establish approval by itself.

Continue with [calibration/README.md](calibration/README.md) and
[calibration/report_workflow.md](calibration/report_workflow.md).

## Network Security

The current credentials and addresses are unchanged:

- AP: `CMDCNC_EVKA` / `cmdcnc1234`
- Dashboard: `http://192.168.1.50`
- TCP: `192.168.1.50:8080`
- WebSocket: `ws://192.168.1.50/ws`
- STA static address: `192.168.1.84/24`, gateway `192.168.1.254`

The protocol has no application authentication. Use only on an isolated, trusted lab network. Do
not expose the device to the public internet or an untrusted LAN. Do not add new credentials to
documentation, issues, screenshots, or calibration artifacts.

## Contribution and Legal Boundary

Create focused changes, preserve unrelated work, and report checks not run. The repository has no
license file, so do not redistribute it or claim public production readiness. Historical vendor C#
material has been deleted and is not part of the supported operator path.
