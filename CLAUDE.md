# CLAUDE.md — evka_position

ESP32 firmware for a Spherical 3D Positioning System. Reads encoder pulses from 3 sensors, converts them to (r, theta, phi), then to Cartesian (X, Y, Z) mm.

**Target MCU**: ESP32 (Wemos D1 R32 / ESP32-WROOM-32)

## Build & Flash

**PlatformIO:**
Supported workflow policy: this project uses PlatformIO on ESP32 only. Arduino IDE and `arduino-cli` are not part of the build/flash workflow.
1. Install PlatformIO (see `docs/setup_test_guide.md`)
2. Compile: `pio run -e wemos_d1_r32`
3. Upload: `pio run -e wemos_d1_r32 --target upload`
4. Monitor: `pio device monitor`

Serial monitor: 115200 baud. On boot, the firmware waits 2 s then calls `setZeroPoint()` — the robot **must** be at mechanical home at that moment.

## Key Files

| File | Role |
|---|---|
| `firmware/src/EvkaPosition.cpp` | Entry point: `setup()` / `loop()`, 20 Hz update rate |
| `firmware/src/SphericalSensor.h` | All config `#define`s, struct definitions, class declaration |
| `firmware/src/SphericalSensor.cpp` | Coordinate math, filtering, validation |
| `firmware/tests/DrawWireTest/DrawWireTest.cpp` | Standalone draw-wire encoder test |
| `firmware/tests/RotaryEncoderTest/RotaryEncoderTest.cpp` | Dual rotary encoder test (theta + phi) |
| `firmware/tests/SingleRotaryTest/SingleRotaryTest.cpp` | Single rotary encoder test |
| `docs/hardware_design/circuit_schematic.md` | Full ASCII circuit schematic (power + signal conditioning + protection) |
| `docs/hardware_design/bill_of_materials.md` | Complete BOM (~30 line items) |
| `docs/hardware_design/pcb_layout_guide.md` | PCB layout zones, trace widths, assembly sequence |
| `docs/hardware_design/system_architecture.md` | System-level architecture overview |

## Architecture

Three-layer pipeline:

```
Encoder counts (raw int32)
        |  countsToSpherical()       x DEG_PER_PULSE / MM_PER_PULSE
Spherical (r mm, theta deg, phi deg)
        |  sphericalToCartesian()    standard physics convention
Cartesian (X mm, Y mm, Z mm)        + low-pass EMA filter (alpha = 0.2)
```

- **Theta / Phi**: Autonics E40S6 quadrature encoders via the `Encoder` library
- **Radius**: OPKON DWE3000 draw-wire encoder via the `Encoder` library (quadrature, same as theta/phi)
- **Filter**: exponential moving average applied to Cartesian output, `position_filter_alpha = 0.2`

All three encoders use the PaulStoffregen `Encoder` library — no manual ISRs.

## Configuration (`SphericalSensor.h`)

| Constant | Value | Meaning |
|---|---|---|
| `PPR_ROTARY` | 1480.0 | Measured counts/rev — Autonics E40S6 |
| `PPR_WIRE` | 2000.0 | Pulses/rev — OPKON DWE3000 |
| `DRUM_CIRCUM_MM` | 200.0 | Drum circumference (mm/rev) |
| `DEG_PER_PULSE` | ~0.2432 | 360 / PPR_ROTARY |
| `MM_PER_PULSE` | 0.1 | DRUM_CIRCUM_MM / PPR_WIRE |
| `RADIUS_MIN_MM` / `RADIUS_MAX_MM` | 100 / 3000 | Safety range (mm) |
| `THETA_MIN/MAX_DEG` | -180 / 180 | Azimuth range |
| `PHI_MIN/MAX_DEG` | 0 / 180 | Elevation range |
| `ENABLE_BATTERY_MONITOR` | 0 (default) | 0 = compile out battery ADC path |
| `UPDATE_PERIOD_MS` | 50 | Loop period (20 Hz) — in `EvkaPosition.cpp` |

## Pin Map (current)

| Pin | Define | Signal |
|---|---|---|
| 14 | `PIN_THETA_A` | Theta encoder A |
| 12 | `PIN_THETA_B` | Theta encoder B (strapping pin — add pull-down) |
| 32 | `PIN_PHI_A` | Phi encoder A |
| 35 | `PIN_PHI_B` | Phi encoder B |
| 16 | `PIN_WIRE_A` | Draw-wire encoder A |
| 17 | `PIN_WIRE_B` | Draw-wire encoder B |
| 36 | `PIN_BATTERY_ADC` | Battery voltage monitor (ADC1_CH0, input-only) |

**Voltage dividers required**: All encoder signal lines output 0-5V TTL. ESP32 GPIO max input is 3.6V. Use 10k/20k resistive dividers on every signal line (A and B for each encoder = 6 lines minimum). See `docs/hardware_design/circuit_schematic.md` for full schematic.

## Coordinate Convention

Physics spherical convention:
- phi = polar/elevation angle from +Z axis (0 deg = up, 180 deg = down)
- theta = azimuth from +X axis in XY-plane
- `x = r * sin(phi) * cos(theta)`, `y = r * sin(phi) * sin(theta)`, `z = r * cos(phi)`

## Calibration Workflow

1. Move robot to mechanical home (zero extension, zero angles)
2. Power on — firmware auto-calls `setZeroPoint()` after 2 s delay
3. All subsequent counts are relative to that snapshot
4. To re-zero without reflashing: send `ZERO\n` over serial (firmware responds `ACK:ZERO`)

## Serial Commands (main firmware)

- `ZERO` -> `ACK:ZERO` (re-calibrate offsets)
- `PING` -> `ACK:PONG`
- `STATUS` -> `STATUS,<is_valid>,<frame_count>,<ts_ms>,<r>,<theta>,<phi>,<x>,<y>,<z>`

If `ENABLE_BATTERY_MONITOR=1`, `STATUS` also emits:
- `BATT,<voltage>,<percentage>,<is_low>`
