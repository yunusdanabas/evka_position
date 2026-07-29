# Existing-Repository Prototype Handoff

This is the approved maintainer handoff for the current repository state. It is self-contained and
does not depend on a private onboarding repository.

## What Is Being Handed Off

Evka Position reads theta, phi, and draw-wire quadrature encoders, converts the zero-relative counts
to spherical coordinates, and emits sensor-frame Cartesian XYZ at 20 Hz. The current board is the
assembled ESP32-S3 v4 carrier in `pcb_design/EVKA_position_v4/`; the classic Wemos build remains a
compatibility and test reference.

`tools/evka_gui` is the canonical operator application. It supports Serial, TCP, WebSocket, replay,
Quick IPT, recording, diagnostics, snapshots, and calibration-session data collection. Its live XYZ,
recordings, snapshots, saved points, and IPT results are sensor-frame values. Software zero changes
only the displayed/session frame. No accepted world transform is applied.

The vendor C# application has been deleted from the supported workflow. Keep the raw TCP protocol:
existing equipment may depend on port 8080 and its line formats. The source-derived contract is
[docs/PROTOCOL.md](docs/PROTOCOL.md).

## Current Status

| Area | Handoff status |
|---|---|
| v4 PCB | Current assembled prototype; not production-qualified |
| Firmware | Main source supports classic ESP32 and v4 ESP32-S3; all 10 configured environments build, with no new flash or hardware claim |
| Host tools | Package version `0.2.0`; Python 3.10+ required |
| Software checks | 191 Python tests, 45 dashboard checks, compileall, IPT solver self-check, and all PlatformIO builds pass |
| Earlier hardware observations | v4 telemetry and individual radius/phi behavior were observed before this pass |
| Blocking defect | Theta count loss/return error remains unresolved; about 1.1 degrees or 35 mm at 2 m was recorded |
| Encoder calibration | Compile defaults exist; final mounted-system constants are not accepted |
| Endpoint/world calibration | No accepted transform and no checked-in shared/default calibration JSON |
| Full integration | Open; no final three-encoder accuracy or repeatability sign-off |
| Release/legal | No redistribution license and no public production claim |

Do not interpret previous flashes, successful software tests, or a generated calibration report as
final system validation.

Software-only verification completed on 2026-07-29:

```text
QT_QPA_PLATFORM=offscreen pytest -q                         191 passed
npm ci && npm test (tools/webdash_harness)                  45 passed
python -m compileall tools -q                               passed
python -m tools.ipt.solver                                  0.405 mm target error
pio run (all 10 configured environments)                    10 passed
```

## v4 Wiring Baseline

| Connector | Axis | PCB-derived pin order | GPIO |
|---|---|---|---|
| J1 | Draw-wire | `1=A, 2=GND, 3=B, 4=+5V` | 7 / 8 |
| J2 | Phi | `1=+5V, 2=A, 3=GND, 4=B` | 4 / 5 |
| J3 | Theta | `1=A, 2=GND, 3=B, 4=+5V` | 9 / 10 |

The J2 order differs from J1/J3. This mapping comes from the v4 PCB/pad nets and current firmware;
it was **not physically reverified in this final pass**. Verify board markings, continuity, cable
colors, and supply polarity before future power-up.

## Blocking Work, In Order

1. Reproduce theta count loss while recording zero-relative raw counts.
2. Inspect and correct coupling slip, backlash, connector integrity, and quadrature signal quality.
3. Repeat return-to-home and multi-point repeatability checks until theta is stable.
4. Calibrate draw-wire and rotary scale without using PPR to mask mechanical loss.
5. Collect sensor/world pairs and generate a candidate endpoint report with hold-outs.
6. Accept a world transform only after calibration and validation thresholds pass.
7. Run the full integration checklist and resolve licensing before any release claim.

Primary evidence:
[docs/calibration/sessions/2026-07-17_repeatability.md](docs/calibration/sessions/2026-07-17_repeatability.md).
Roadmap: [docs/PROJECT_ROADMAP.md](docs/PROJECT_ROADMAP.md).

## Repository Map

```text
firmware/src/                         Main shared firmware
firmware/tests/                       Classic-pin standalone test sketches
pcb_design/EVKA_position_v4/          Current prototype KiCad workspace and board guide
tools/evka_gui/                       Canonical operator GUI
tools/calibration/                    Candidate sensor-to-world report tooling
tools/ipt/                            Quick IPT solver and standalone UI
tools/position_checker/               Legacy tools and shared parsing/transport code
docs/PROTOCOL.md                      Canonical runtime protocol
docs/calibration/                     Active calibration procedures and evidence
docs/integration/                     Active integration guide plus marked history
docs/hardware_design/12v_legacy/      Archive, not the current board
laser_radius/ and docs/research/       Research only, not implemented baseline
```

## Reading Order

1. [AGENTS.md](AGENTS.md) — shared agent guide (working rules, safety boundaries, validation commands)
2. [docs/ONBOARDING.md](docs/ONBOARDING.md)
3. [CONTRIBUTING.md](CONTRIBUTING.md)
4. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
5. [docs/PROTOCOL.md](docs/PROTOCOL.md)
6. [pcb_design/EVKA_position_v4/FIRMWARE.md](pcb_design/EVKA_position_v4/FIRMWARE.md)
7. [docs/calibration/README.md](docs/calibration/README.md)
8. [docs/firmware/CODE_WALKTHROUGH.md](docs/firmware/CODE_WALKTHROUGH.md)

## Network and Credential Boundary

The checked-in AP and STA defaults are unchanged. The AP is `CMDCNC_EVKA` with password
`cmdcnc1234`; AP address is `192.168.1.50`, TCP is port 8080, and WebSocket is `/ws` on port 80.
Remote commands are not application-authenticated. Use only on an isolated, trusted lab network;
do not expose the device to an untrusted LAN or the internet.

## Ownership Boundary

The repository has no license file. Do not redistribute it or describe it as a public production
release. Historical vendor C# content had separate ownership risk and has been deleted from the
supported handoff. The protocol behavior implemented by the current firmware remains part of this
prototype handoff.
