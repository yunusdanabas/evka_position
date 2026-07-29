# Architecture and Prototype Boundaries

This document describes the current repository implementation. It does not certify the assembled
v4 prototype. Compile-time configuration is defined in `firmware/src/SphericalSensor.h`; runtime
protocol behavior is defined in `firmware/src/EvkaPosition.cpp` and
`firmware/src/CmdTcpServer.cpp`.

See [PROTOCOL.md](PROTOCOL.md) for the canonical telemetry and command/reply contract and
[firmware/CODE_WALKTHROUGH.md](firmware/CODE_WALKTHROUGH.md) for source navigation.

## Processing Pipeline

Every 50 ms, the main loop performs:

```text
PCNT encoder counters
    -> subtract boot/command zero offsets
    -> apply runtime PPR and encoder signs
    -> spherical (r mm, theta deg, phi deg)
    -> Cartesian sensor frame (X, Y, Z mm)
    -> limits/finite validation
    -> Cartesian EMA filter (alpha 0.2)
    -> Serial, WebSocket, and TCP telemetry
```

- Theta and phi use Autonics E40S6-5000 encoders.
- Radius uses an OPKON DWEM2 draw-wire encoder.
- Main firmware uses `ESP32Encoder` hardware PCNT on classic and v4 targets.
- `RAW_COUNTS` is zero-relative because `readRawEncoders()` subtracts stored offsets.
- Invalid frames bypass Cartesian filtering; the filter is re-primed after zero operations.

## Coordinate Frames

Firmware uses elevation/azimuth spherical coordinates:

```text
x = r * cos(phi) * cos(theta)
y = r * cos(phi) * sin(theta)
z = r * sin(phi)
```

Theta is azimuth from +X in the XY plane. Phi is elevation from horizontal. Signs are board-specific:
v4 uses theta `+1` / phi `-1`; classic uses theta `-1` / phi `+1`.

The firmware output frame is the **sensor frame** established by the zero offsets. The canonical
`tools/evka_gui` displays and records that frame. Its software-zero controls create a client-side
display/session offset only. Quick IPT also returns a sensor-frame point.

The calibration tools can fit a candidate rigid transform:

```text
world = R @ sensor + t
```

No transform or shared/default calibration JSON is currently accepted. `evka_gui` never applies a
world transform to live telemetry. A passing session JSON may be supplied explicitly only to the
legacy visualizer.

## Current Configuration Summary

| Constant | Current source value | Meaning |
|---|---:|---|
| `PPR_ROTARY` | 20000 | E40S6-5000 at X4 quadrature |
| `PPR_WIRE` | 8000 | DWEM2 theoretical X4 count; mounted calibration pending |
| `DRUM_CIRCUM_MM` | 200 | Draw-wire conversion basis |
| `ENCODER_THETA_SIGN` | v4 +1; classic -1 | Count-to-theta sign |
| `ENCODER_PHI_SIGN` | v4 -1; classic +1 | Count-to-phi sign |
| `UPDATE_PERIOD_MS` | 50 | 20 Hz main update |
| `ENABLE_WIFI` | 1 | AP/STA dashboard and WebSocket enabled |
| `ENABLE_CMD_TCP` | 1 | TCP port 8080 enabled |
| `ENABLE_ESPNOW_REMOTE` | 1 | Wireless pendant receiver enabled |
| `ENABLE_BATTERY_MONITOR` | 1 | Battery/supply ADC reporting compiled in |
| `BATTERY_ADC_12V_INPUT` | 0 | Current scaling is the 1S divider path |

NVS values in namespace `evka_cal` override the PPR compile defaults. `CONSTANTS` reports the
runtime values.

## Board Pin Maps

| Target | Theta A/B | Phi A/B | Wire A/B | Battery ADC | Status LED |
|---|---|---|---|---|---|
| Classic `wemos_d1_r32` | 14 / 12 | 32 / 35 | 16 / 17 | GPIO36 | GPIO2 monochrome |
| v4 `esp32s3_v4` | 9 / 10 | 4 / 5 | 7 / 8 | GPIO1, 1S divide-by-2 source path | DevKit WS2812 GPIO48 by default |
| v4 `esp32s3_v4_rgb38` | 9 / 10 | 4 / 5 | 7 / 8 | GPIO1 | DevKit WS2812 GPIO38 override |

### v4 Physical Connector Order

| Connector | Axis | PCB-derived order |
|---|---|---|
| J1 | Wire | `1=A, 2=GND, 3=B, 4=+5V` |
| J2 | Phi | `1=+5V, 2=A, 3=GND, 4=B` |
| J3 | Theta | `1=A, 2=GND, 3=B, 4=+5V` |

J2 A/B therefore reach GPIO4/GPIO5 through pins 2/4, not pins 1/3. This mapping is derived from the
current v4 KiCad PCB/pad nets and source pin comments. It was **not physically reverified in this
final documentation pass**.

## Status LED and Battery

Current source includes `StatusLed.{h,cpp}`:

- v4 default uses a DevKit NeoPixel on GPIO48; `esp32s3_v4_rgb38` selects GPIO38.
- Source states include boot calibration, ESP-NOW fault, invalid position, STA reconnecting,
  connected, AP-only, and transient zero/remote/blink overlays.
- Classic builds retain the GPIO2 off/blink/on WiFi indication.

These are source-defined behaviors, not newly physically verified LED behavior.

Battery monitoring is compiled in (`ENABLE_BATTERY_MONITOR=1`). With the current
`BATTERY_ADC_12V_INPUT=0`, source interprets the ADC as a 1S LiPo divide-by-2 path and emits
`BATT,...` after `STATUS`. This pass did not verify ADC scaling or battery accuracy on hardware.

## Runtime Components

| Component | Responsibility |
|---|---|
| `EvkaPosition.cpp` | Setup/loop, zeroing, command dispatch, 20 Hz fan-out, ESP-NOW events |
| `SphericalSensor.{h,cpp}` | Configuration, PCNT reads, conversions, validation, filter, NVS, battery |
| `StatusLed.{h,cpp}` | Classic and RGB status state machine |
| `WebDashboard.{h,cpp}` | AP/STA management, HTTP dashboard, WebSocket queue/fan-out |
| `CmdTcpServer.{h,cpp}` | TCP port 8080, client limits, line framing, XYZ/SENSOR stream |
| `tools/evka_gui` | Canonical sensor-frame host UI |
| `tools/calibration` | Candidate sensor-to-world fitting/report tools |

The vendor C# application has been deleted from the supported architecture. `CMD` remains only as a
compatibility name for the retained TCP protocol.

## Networking and Security

The device runs AP+STA when STA credentials are configured and keeps the AP fallback available.
Current AP is `CMDCNC_EVKA` / `cmdcnc1234` at `192.168.1.50`; current STA profile is
`192.168.1.84/24` with gateway `192.168.1.254`.

TCP and WebSocket commands are unauthenticated. Fixed credentials are trusted-lab-only, not a
production security boundary. Do not expose ports 80/8080 to an untrusted network.

## Open Architecture Risks

- Theta loses or fails to return counts; mechanical slip/backlash and signal integrity remain open.
- v4 connector mapping needs a recorded physical re-verification.
- Mounted encoder constants are not accepted.
- No endpoint/world transform is accepted or applied by the canonical GUI.
- Full three-encoder accuracy, repeatability, battery, LED, WiFi endurance, and system validation are
  not signed off.
- The repository has no redistribution license and no public production status.
