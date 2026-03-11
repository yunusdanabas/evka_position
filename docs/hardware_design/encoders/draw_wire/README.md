# Draw-Wire Encoder (String Potentiometer)

## Overview
A **Draw-Wire Encoder** (also known as a cable transducer or string pot) measures linear distance by unwinding a flexible cable from a spring-loaded spool. For this system, a **Digital Pulse Output** type is required to match the interface of the rotary encoders and provide high noise immunity.

## Recommended Specifications
To match the system requirements (3D positioning with 2 angles):

| Parameter | Recommended Value | Reason |
| :--- | :--- | :--- |
| **Output Type** | **Incremental Pulse (A/B)** | Direct microcontroller interface, high precision |
| **Measurement Range** | 0 - 5m (or 10m) | Matches typical workspace |
| **Resolution** | 0.05mm - 0.1mm per pulse | <1mm system accuracy |
| **Output Voltage** | 5V (TTL) or 24V (HTL) | 5V preferred for ESP32 + level-shift/divider interfaces |
| **Interface** | Quadrature (A, B Phase) | Same code as rotary encoders |

## DWE part code specification

Part-code breakdown for the Draw Wire Encoder model in use (e.g. DWE-3000-HLD-P2000-Z-V3-5MR):

| Code | Specification | Detail |
| :--- | :--- | :--- |
| **DWE** | Series | Draw Wire Encoder |
| **3000** | Measurement Stroke | 3000 mm (3 m) |
| **HLD** | Output Driver | High Line Driver (5–30 V DC signal levels) |
| **P2000** | Resolution | 0.1 mm / pulse (200 mm turn / 2000 PPR) |
| **Z** | Output Channels | A, B, Z (Z = index pulse, once every 200 mm) |
| **V3** | Supply Voltage | 5–30 V DC |
| **5MR** | Cable | 5 m cable length, radial exit |

## Integration Guide

### Wiring (Pulse Type)
| Signal | Color (Typical) | MCU Connection |
| :--- | :--- | :--- |
| **VCC** | Brown/Red | 5V |
| **GND** | Blue/Black | GND |
| **Phase A** | White | Interrupt Pin (GPIO 32) |
| **Phase B** | Green | GPIO Pin (GPIO 33) |

### Cable identification (ZV35MR SL-TS incremental encoder)

From the encoder nameplate. Use **V** (Brown) and **0 V** (White) for power; **A** (Yellow) and **B** (Green) for quadrature (pulse + direction). **Z** (Gray) is the index pulse; A-bar, B-bar, Z-bar and shield are optional.

**Power and ground**

| Signal | Color (EN) | Color (TR) |
| :--- | :--- | :--- |
| **V** (supply) | Brown | Kahve |
| **0 V** (ground) | White | Beyaz |
| **Earth** | Shield | Toprak |

**Quadrature and index**

| Signal | Color (EN) | Color (TR) |
| :--- | :--- | :--- |
| **A** (phase A) | Yellow | Sari |
| **B** (phase B) | Green | Yesil |
| **Z** (index) | Gray | Gri |
| **A-bar** (A complement) | Blue | Mavi |
| **B-bar** (B complement) | Red | Kirmizi |
| **Z-bar** (Z complement) | Pink | Pembe |

### Mechanical Mounting
1. **Mount Body:** Secure the sensor body to the **phi-axis arm** (the tilting part).
2. **Cable Attachment:** Attach the draw-wire tip to the **target object** or end-effector.
3. **Alignment:** Ensure the wire path is clear and aligns with the measurement axis.

## Selection Options

| Manufacturer | Series | Type | Est. Cost |
| :--- | :--- | :--- | :--- |
| **Balluff** | BTL-S | Pulse/SSI | High |
| **TR Electronics** | SLW | Incremental Pulse | Med-High |
| **SICK** | BCG | EcoLine (Wire Draw) | Med |
| **Generic** | "Draw Wire Pulse" | Encoder-based DIY | Low |

> **Note:** You can also build a custom one by attaching a standard **E40S6 Rotary Encoder** to a spring-loaded cable reel.
> - **Resolution Formula:** `Distance_Per_Pulse = (Drum_Circumference) / PPR`

## Legacy firmware vs current (ESP32 / DWE3000)

| Aspect | Legacy | Current |
| :--- | :--- | :--- |
| **Interface** | Clock + direction (one pin = pulses, one = direction) | Quadrature A/B (both pins carry phase; direction from sequence) |
| **Pins (ESP32)** | PIN_WIRE_CLK = 6, PIN_WIRE_DIR = 7 | PIN_WIRE_A = 32, PIN_WIRE_B = 33 |
| **Why 6/7 changed** | GPIO 6–11 are reserved for SPI flash on ESP32-WROOM-32 (Wemos D1 R32) — must not be used as I/O | 32/33 are safe GPIOs with full I/O and pull-ups |
| **Voltage** | Encoder 5 V outputs; direct connect risks ESP32 (3.3 V max) | Use 10 kΩ / 20 kΩ divider on A, B, Z before ESP32 |
| **Phi encoder** | PIN_PHI_A = 3 (was UART0 RX — serial injected false counts) | Remapped to GPIO 27 (PHI_B to GPIO 26) — conflict resolved |

Current firmware uses the **Encoder** library (quadrature) for the draw-wire; legacy used a single ISR on the clock pin and read direction from the other pin.

## Troubleshooting: constant 3.3 V on both A and B

If you measure **constant 3.3 V on both A and B** (at the MCU pins or after dividers):

| Cause | What you see | What to do |
| :--- | :--- | :--- |
| **Encoder at rest (normal)** | Quadrature encoders sit in one of four states (00, 01, 10, 11). Both high (3.3 V) is a valid idle state. | **Move the wire**; one or both lines should toggle. If they do, behaviour is correct. |
| **Pull-ups only (no encoder drive)** | Legacy code used `INPUT_PULLUP`. If the encoder is disconnected, open-collector and not sinking, or unpowered, both pins float to 3.3 V. | Check encoder supply and GND; confirm A/B are actually connected. If encoder is open-collector, ensure it can pull the line low (try moving the wire and watch with a multimeter). |
| **Wrong encoder type** | Some units output CLK + DIR instead of quadrature. CLK toggles only when moving; DIR may sit high. If you treat both as “A” and “B”, you may see one stable (e.g. 3.3 V) and one pulsing, or both stable when idle. | Confirm from the datasheet whether the encoder is quadrature (A/B) or CLK+DIR. Legacy firmware expected CLK+DIR; current firmware expects quadrature. |
| **Pins configured as output** | If the MCU drives those pins high (e.g. misconfiguration or wrong sketch), they will read 3.3 V. | Ensure the wire-encoder pins are inputs (current code uses the Encoder library, which sets them as input). |
| **5 V clamped to 3.3 V** | 5 V encoder wired directly to ESP32: input protection clamps high to ~3.3 V. When the encoder outputs high, you read 3.3 V. | Normal for “high” state. Use dividers (or level shifter) to avoid long-term damage; then re-check while moving the wire. |

**Quick check:** Pull or push the wire while probing A and B. If the voltage never changes, the encoder is not driving those lines (power, wiring, or wrong output type). If one or both toggle, the encoder is working and 3.3 V was just the idle state.
