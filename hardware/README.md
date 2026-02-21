# Hardware & System Documentation

**System Type:** Spherical 3D Positioning System
**Architecture:** 2 Rotary Axes ($\theta, \phi$) + 1 Linear Axis ($r$)
**Target MCU:** ESP32 (Wemos D1 R32)

## Directory Contents

| Folder / File | Description |
| :--- | :--- |
| [`Rotary_Encoder_E40S6/`](./Rotary_Encoder_E40S6/README.md) | Autonics E40S6 rotary encoder docs, datasheets, and ESP32 wiring |
| [`Draw_Wire_Encoder/`](./Draw_Wire_Encoder/README.md) | OPKON DWE3000 draw-wire encoder specs |
| [`System_Architecture.md`](./System_Architecture.md) | Kinematic math, coordinate formulas, error analysis |

## Hardware List

- **2x** Autonics E40S6-5000-3-T-5 (Rotary Encoders — Theta and Phi)
- **1x** OPKON DWE3000 HLD P2000 Z V3 (Draw-Wire Encoder — Radius)
- **1x** ESP32 Wemos D1 R32
- **6-7x** Voltage dividers (10k/20k) for 5V-to-3.3V signal conditioning
- **1x** External 5V power supply for encoders (~150 mA total)

## Important Notes

- **Voltage dividers required** on all encoder signal lines (5V TTL to 3.3V ESP32). See [`docs/DWE3000_hardware_notes.md`](../docs/DWE3000_hardware_notes.md) for circuit details.
- **External 5V supply** for encoders — do not power from ESP32.
- **Common GND** between supply, all encoders, and ESP32.

For build and test instructions, see [`docs/setup_test_guide.md`](../docs/setup_test_guide.md).
