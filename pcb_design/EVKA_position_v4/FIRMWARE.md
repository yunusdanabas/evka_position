# v4 PCB Prototype Firmware Guide

This is the board-specific guide for the assembled EVKA_position v4 prototype using an
ESP32-S3-DevKitC-1. The shared source is selected by `-DPCB_V4` in PlatformIO environment
`esp32s3_v4`.

This document reconciles source and PCB files only. Completed software-only results are recorded in
[../../HANDOFF.md](../../HANDOFF.md); no new flash, continuity, power, encoder, battery, LED, or
motion result is claimed here.

## Prototype Status

- Earlier work observed v4 telemetry at 20 Hz.
- Theta count loss remains unresolved, with recorded return error up to about 1.1 degrees.
- Full three-encoder integration and accuracy acceptance remain open.
- No endpoint/world transform is accepted; `tools/evka_gui` remains sensor-frame-only.
- This board/repository has no public production-readiness or redistribution claim.

## PCB-Derived Pin and Connector Map

| Connector | Axis | Pin order | GPIO |
|---|---|---|---|
| J1 | Draw-wire | `1=A, 2=GND, 3=B, 4=+5V` | A=7, B=8 |
| J2 | Phi | `1=+5V, 2=A, 3=GND, 4=B` | A=4, B=5 |
| J3 | Theta | `1=A, 2=GND, 3=B, 4=+5V` | A=9, B=10 |

| Other signal | GPIO/source definition |
|---|---|
| Battery ADC | GPIO1, current source selects 1S divide-by-2 scaling |
| RGB status LED | GPIO48 by default; `esp32s3_v4_rgb38` selects GPIO38 |
| GPIO17/18 | Not connected on the carrier |

J2 differs from J1/J3. Its A/B signals are pins 2/4. This order is derived from the v4 KiCad
PCB/pad nets and current `SphericalSensor.h` comments. It was **not physically reverified in this
final pass**. Check the actual board before power.

Cable colors:

| Encoder | A | B | +5V | GND |
|---|---|---|---|---|
| Theta/Phi E40S6 | Black | White | Brown | Blue |
| Draw-wire DWEM2 | Yellow | Green | Brown | White |

The carrier includes 10k/20k encoder signal dividers. Do not bypass them with 5 V encoder outputs.

## Build Environment

```bash
pio run -e esp32s3_v4
```

Future upload/monitor, only after wiring and safety review:

```bash
pio run -e esp32s3_v4 --target upload --upload-port /dev/ttyACM0
pio device monitor -e esp32s3_v4
```

Use `esp32s3_v4_rgb38` only after identifying an actual DevKit revision that needs GPIO38. The
`test_*` environments target classic Wemos pins and must not be flashed to v4.

## Boot Zero

The main firmware initializes the sensor and network, waits two seconds, then calls
`setZeroPoint()`. Keep the mechanism at mechanical home and motionless during that period. `ZERO`,
`ZERO_T`, `ZERO_P`, and `ZERO_W` capture new counter offsets later.

`RAW_COUNTS` returns counts relative to those offsets; it is not an absolute PCNT dump.

## Telemetry and Commands

Use [../../docs/PROTOCOL.md](../../docs/PROTOCOL.md) as the canonical reference.

- Serial and WebSocket emit `DATA,...` at 20 Hz.
- TCP port 8080 emits separate `X...,Y...,Z...` and `SENSOR,...` lines.
- `STATUS` emits a snapshot and `BATT,...` when battery monitoring is compiled in.
- Network commands and fixed credentials are trusted-lab-only.

Run the canonical GUI:

```bash
python -m tools.evka_gui --serial /dev/ttyACM0 --baud 115200
python -m tools.evka_gui --tcp 192.168.1.50:8080
python -m tools.evka_gui --ws 192.168.1.50
```

The GUI shows firmware sensor-frame values. Software zero is a client display/session offset. The
calibration window can generate a candidate report/JSON but does not apply a world transform to live
GUI data.

## Network Defaults and Security

- AP: `CMDCNC_EVKA` / `cmdcnc1234`
- Dashboard: `http://192.168.1.50`
- TCP: `192.168.1.50:8080`
- WebSocket: `ws://192.168.1.50/ws`
- STA static profile: `192.168.1.84/24`, gateway `192.168.1.254`

TCP/WebSocket commands have no application authentication. Do not expose the prototype to an
untrusted LAN or the public internet.

## Source-Defined Battery Behavior

Current source has `ENABLE_BATTERY_MONITOR=1` and `BATTERY_ADC_12V_INPUT=0`. It interprets GPIO1 as a
1S LiPo divide-by-2 input, maps roughly 3.0-4.2 V to percentage, and marks values below 15% low.
This is source behavior, not a new hardware accuracy verification.

## Source-Defined RGB Behavior

`StatusLed.cpp` defines these v4 states:

| Priority | State | Source-defined indication |
|---:|---|---|
| 100 | Boot zero/calibration | Amber breathe |
| 95 | ESP-NOW initialization fault | Magenta fast blink |
| 85 | Invalid position | Orange blink |
| 80 | STA reconnecting | Blue/cyan blink |
| 70 | STA connected and position valid | Green solid |
| 60 | AP-only and position valid | Cyan solid |

Transient white flashes acknowledge zero and `BLINK`; purple acknowledges a remote button. Classic
builds use GPIO2 instead. Actual v4 LED GPIO and visible colors still require physical confirmation.

## Bring-Up Stop Conditions

Stop before calibration or endpoint collection if:

- any connector order or supply polarity is uncertain;
- an idle channel changes counts;
- movement changes the wrong channel;
- theta does not return to the same zero-relative count;
- a connector, divider, regulator, or DevKit becomes warm;
- battery/LED behavior is being inferred without measurement.

Continue with [../../docs/calibration/README.md](../../docs/calibration/README.md) and
[../../docs/integration/final_integration_validation.md](../../docs/integration/final_integration_validation.md).
