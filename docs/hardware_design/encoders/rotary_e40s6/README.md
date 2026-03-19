# Autonics E40S6-5000-3-T-5 Rotary Encoder

## Overview

The **Autonics E40S6-5000-3-T-5** is a high-resolution incremental rotary encoder used for the theta and phi axes of the Evka Position system.

- 5000 PPR datasheet (20000 counts/rev @ X4 quadrature — confirmed on hardware)
- Compact 40mm housing, 6mm shaft
- Totem-pole (push-pull) output, 0-5V TTL
- Phase A, B, Z (index) outputs

## Technical Specifications

| Parameter | Value |
|-----------|-------|
| **Model** | E40S6-5000-3-T-5 |
| **Resolution** | 5000 PPR |
| **Output Phases** | A, B, Z (Index) |
| **Output Type** | Totem-pole (Push-pull) |
| **Logic Levels** | 0-5V (TTL compatible) |
| **Power Supply** | 5VDC +/-5% |
| **Current Draw** | ~50 mA typical |
| **Max Response Frequency** | 300 kHz |
| **Shaft Diameter** | 6mm |
| **Housing Diameter** | 40mm |
| **Repeatability** | +/-1 pulse |
| **Operating Temperature** | -25 deg C to +70 deg C |
| **Protection** | IP67 |

## Wire Color Coding

| Wire Color | Signal | Function |
|:---|:---|---|
| **Brown** | +V (VCC) | Power supply positive (5V) |
| **Blue** | GND | Ground |
| **Black** | OUT A | Phase A output |
| **White** | OUT B | Phase B output |
| **Orange** | OUT Z | Index signal (1 pulse/rev) |
| **Shield** | F.G. | Frame ground (connect to GND for EMI shielding) |

## ESP32 Wiring (Wemos D1 R32)

**CRITICAL: 5V-to-3.3V voltage divider required on all signal lines.**

The E40S6 outputs 0-5V TTL signals. ESP32 GPIO absolute max input is 3.6V. Connect each signal line (A, B, and optionally Z) through a voltage divider before the ESP32 GPIO:

```
Encoder signal (5V swing)
        |
       10k ohm
        |
        +------- ESP32 GPIO   (reads 3.33V when HIGH)
        |
       20k ohm
        |
       GND
```

### Connections

```
Encoder              ESP32 (via voltage divider)
----------------------------------------------
Brown (+5V)  --> External 5V supply (NOT ESP32 5V pin)
Blue (GND)   --> GND (common with ESP32 and supply)
Black (A)    --> GPIO via 10k/20k divider
White (B)    --> GPIO via 10k/20k divider
Orange (Z)   --> GPIO via 10k/20k divider (optional)
Shield       --> GND (at MCU end only)
```

Current pin assignments in `SphericalSensor.h`:
- **Theta axis**: A = GPIO 32, B = GPIO 35
- **Phi axis**: A = GPIO 14, B = GPIO 12

**Power**: Use an external regulated 5V supply for all encoders (~50 mA each). Share GND with ESP32 but do not power encoders from ESP32.

## Signal Characteristics

- **Voltage Swing**: 0V to 5V (TTL levels)
- **Rise/Fall Time**: < 1 us
- **Output Impedance**: ~100 ohm
- Quadrature: Phase A and B are 90 degrees out of phase for direction detection

### Resolution Modes

Datasheet values (not matching measured results):
```
X1 counting:  5000 counts/rev  (0.072 deg/count)
X2 counting: 10000 counts/rev  (0.036 deg/count)
X4 counting: 20000 counts/rev  (0.018 deg/count)
```

The PaulStoffregen Encoder library uses X4 counting by default when both pins support interrupts.

**Confirmed on hardware:** 20000 counts/rev (~0.0180 deg/count) — matches datasheet X4 quadrature (5000 PPR × 4 edges). Previous measured value of 1480 was an incorrect single-edge measurement.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Missed pulses | ISR latency | Use PaulStoffregen Encoder library |
| Erratic counts | Electrical noise | Add 100nF capacitor, use shielded cable |
| No pulses | Wiring or power | Check wire colors, verify 5V at encoder |
| Direction reversed | A/B swapped | Swap A and B wires |

## Datasheets

Local copies in this directory:
- `E40_EN_TCD210019AD_20250721_MANUAL_W.pdf` — Full manual
- `E40_EN_TCD210019AD_20250721_INST_W.pdf` — Installation guide
- `Rotary_EN_20250415_W.pdf` — Rotary encoder catalog

## External Links

- **Autonics Product Page**: https://www.autonics.com/series/3000430
- **PaulStoffregen/Encoder Library**: https://github.com/PaulStoffregen/Encoder
