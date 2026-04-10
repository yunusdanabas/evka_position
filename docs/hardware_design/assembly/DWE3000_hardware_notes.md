# DWE3000 Hardware Notes
_Session: 2026-02-18_

---

## Encoder Specifications — OPKON DWE3000 HLD P2000 Z V3

| Parameter | Value |
|---|---|
| Model code | DWE3000 HLD P2000 Z V3 |
| PPR | 2000 pulses / revolution |
| Drum circumference | 200 mm / revolution |
| MM_PER_PULSE | ~0.02494 mm / pulse (calibrated; datasheet spec: 0.1) |
| Max stroke | 3000 mm |
| Z channel | 1 pulse per revolution (every 200 mm) |
| Supply voltage | 5–30 V DC |
| Output driver | HLD (High Line Driver) — push-pull, outputs swing to supply rail |

---

## Critical: Voltage Level Mismatch

- Encoder minimum supply: **5 V** → outputs swing **0–5 V**
- ESP32 GPIO absolute maximum input: **3.3 V**
- Connecting encoder outputs directly to ESP32 GPIO **will damage it over time**
- Signal conditioning is required on **every signal line (A, B, Z)**

---

## Option A — Proper Voltage Divider (recommended for production)

```
Encoder signal (5 V swing)
        │
       10 kΩ
        │
        ├─────── ESP32 GPIO   ← V = 5 × 20/(10+20) = 3.33 V ✓
        │
       20 kΩ
        │
       GND
```

- Purely passive — no interaction with ESP32 3.3 V rail
- Encoder HIGH (5 V) → GPIO sees 3.33 V
- Encoder LOW (0 V) → GPIO sees 0 V
- No stress on ESP32 in any condition

---

## Option B — Legacy Circuit (2.2 kΩ + 10 kΩ pull-up)

```
Encoder_A ──── 2.2 kΩ ──── ESP32 GPIO ──── 10 kΩ ──── 3.3 V
```

### What it does

- **2.2 kΩ**: series current-limiting resistor — protects the ESP32 ESD diode
- **10 kΩ to 3.3 V**: pull-up — defines a clean HIGH state when encoder is unpowered or disconnected

### Voltage levels when encoder is powered (5 V HLD output)

| Encoder state | Node voltage | ESP32 reads |
|---|---|---|
| Not powered / disconnected | 3.3 V (pull-up wins) | HIGH — constant |
| Driving HIGH (5 V) | ~3.8 V (ESD diode clamps) | HIGH ✓ |
| Driving LOW (0 V) | ~0.6 V (divider: 3.3V×2.2k/12.2k) | LOW ✓ |

### ESD diode current when encoder drives HIGH

```
I = (5 V − 3.8 V) / 2200 Ω ≈ 0.55 mA
```

ESP32 protection diodes rated ~5–10 mA peak. **0.55 mA is within safe limits.**

### Why you see constant 3.3 V before connecting the encoder

Encoder is unpowered → output transistors off → line floating → 10 kΩ pull-up holds GPIO at 3.3 V. This is expected and correct behaviour.

### Is it safe to use?

- **Yes for prototyping / development** — quadrature signal is correctly read by the Encoder library
- **Not ideal for long-term 24/7 production** — ESD diode sees continuous current (designed for transients)
- For permanent installation: switch to Option A (10k/20k divider)

---

## GPIO Pin Map — Wemos D1 R32 (ESP32-WROOM-32)

| Signal | GPIO | Notes |
|---|---|---|
| PIN_WIRE_A | **16** | Draw-wire encoder quadrature A |
| PIN_WIRE_B | **17** | Draw-wire encoder quadrature B |
| PIN_WIRE_Z | **18** | Index / Z channel (optional sanity check) |
| PIN_THETA_A | 32 | Interrupt-capable, ADC1_CH4 |
| PIN_THETA_B | 35 | Input-only, interrupt-capable |
| PIN_PHI_A | 14 | Interrupt-capable GPIO |
| PIN_PHI_B | 12 | Strapping pin — add pull-down |

### Forbidden GPIOs on ESP32-WROOM-32

GPIOs **6, 7, 8, 9, 10, 11** are wired to internal SPI flash. Never use as I/O.

---

## Power Wiring (External Supply)

```
External 5 V supply (+) ──────────── DWE3000 (+V / Red)
External 5 V supply (−) ──┬───────── DWE3000 (GND / Black)
                          └───────── ESP32 GND
```

- Do **not** connect encoder +V to ESP32
- GND **must be common** between supply, encoder, and ESP32
- Power external supply **before** powering ESP32

---

## Voltage Dividers for Rotary Encoders (E40S6)

The same voltage level mismatch applies to the **Autonics E40S6** rotary encoders used for theta and phi. They output 0-5V TTL on all signal lines.

**Required dividers for rotary encoders:**

| Encoder | Signal | GPIO | Divider needed |
|---|---|---|---|
| Theta | A (Black wire) | 32 | 10k/20k |
| Theta | B (White wire) | 35 | 10k/20k |
| Phi | A (Black wire) | 14 | 10k/20k |
| Phi | B (White wire) | 12 | 10k/20k |

Use the same 10k/20k divider circuit as Option A above. The E40S6 shield wire (bare/braid) should connect to GND at the MCU end only for EMI protection.

**Total voltage dividers across the system:** 7 (2 theta + 2 phi + 3 draw-wire A/B/Z).

**Power:** Each E40S6 draws ~50 mA at 5V. Combined with the DWE3000, total encoder power is ~150-200 mA. Use an external regulated 5V supply; do not power from ESP32.

---

## Phase 3 & 4 Complete

Current firmware pin map (source of truth: `firmware/src/SphericalSensor.h`):
`PIN_THETA_A` = GPIO 14, `PIN_THETA_B` = GPIO 12, `PIN_PHI_A` = GPIO 32,
`PIN_PHI_B` = GPIO 35. UART0 RX conflict remains resolved, and the final
rotary mapping is the one above.
PPR_ROTARY corrected from datasheet 5000 to 20000 (X4 quadrature).
Phase 5 (2026-03-11): PPR_ROTARY further corrected to 20000 (X4 quadrature); PPR_WIRE calibrated to 8020 (400 mm / 1604 mm reading).
Full system testing can proceed.
