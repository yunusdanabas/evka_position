# Individual Hardware Test Plan — ESP32

Test each hardware unit **one at a time**: draw-wire encoder, theta rotary encoder, phi rotary encoder. Only one device is connected and verified per test. All commands and connections are in this document.

---

## 1. Prerequisites

- **Workflow policy**: Use PlatformIO on ESP32 only. Arduino IDE and `arduino-cli` are not part of this test workflow.
- **Toolchain**: PlatformIO CLI. See [Setup & Test Guide](setup_test_guide.md) for install steps. Board support and Encoder library are auto-installed from `platformio.ini`.
- **USB**: ESP32 connected via USB. Find port with `ls /dev/ttyUSB* /dev/ttyACM*` (replace `/dev/ttyUSB0` in commands below with your port).
- **Ground**: Use a single common GND between any external 5 V supply, the encoder under test, and the ESP32.
- **Voltage conditioning**: Every encoder signal line (A, B, and Z if used) must go through a voltage divider or level-shifter before the ESP32—see Section 2.

### Quick toolchain check

```bash
pio --version
ls /dev/ttyUSB* /dev/ttyACM*
```

If upload fails with permission denied:

```bash
sudo usermod -aG dialout $USER
newgrp dialout
```

---

## 2. ESP32 Connections and Voltage Levels

### Voltage level mismatch

All encoders in this project (OPKON DWE3000 draw-wire and Autonics E40S6 rotary) output **0–5 V TTL**. The ESP32 GPIO maximum input is **3.3 V** (absolute max 3.6 V). Connecting 5 V signals directly to GPIO can damage the ESP32. **Signal conditioning is required on every encoder signal line** (A, B, and Z if used).

### Option A — 10 kΩ / 20 kΩ voltage divider (recommended)

Use one divider per signal. Passive and safe for production.

```
Encoder signal (5 V swing)
        │
       10 kΩ
        │
        ├─────── ESP32 GPIO   (3.33 V when encoder HIGH, 0 V when LOW)
        │
       20 kΩ
        │
       GND (common with ESP32)
```

- GPIO sees **5 V × 20/(10+20) = 3.33 V** when encoder is HIGH, **0 V** when LOW.
- No connection to the ESP32 3.3 V rail; no stress on the MCU.

**Alternative values (220 Ω + 460 Ω):** You can use a 220 Ω resistor from the encoder to the GPIO junction and 460 Ω from the junction to GND. GPIO then sees **5 V × 460/(220+460) ≈ 3.38 V** when HIGH, which is within ESP32 limits. Wire as: encoder signal → 220 Ω → junction (to ESP32 GPIO) → 460 Ω → GND. Current through the divider is about 7.4 mA; ensure the encoder can source that (most can). Same circuit as Option A, different resistor values.

### Option B — 2.2 kΩ + 10 kΩ pull-up (prototyping only)

```
Encoder signal ──── 2.2 kΩ ──── ESP32 GPIO ──── 10 kΩ ──── 3.3 V
```

- Works for development; GPIO reads ~0.6 V (LOW) / ~3.8 V clamped (HIGH).
- ESD diode carries ~0.55 mA continuous current—acceptable for prototyping, not ideal long-term. Prefer Option A for permanent use.
- Before the encoder is powered, GPIO may sit at 3.3 V (pull-up); this is normal.

### Ground

Use a **single common GND** between the external 5 V supply, the encoder(s), and the ESP32. When using an external supply, tie its GND to ESP32 GND. Do not rely on USB GND alone if the encoder is powered from a separate supply.

### Power

- **Do not power the encoders from the ESP32.** Use an external regulated 5 V supply.
- Typical current: DWE3000 ~100 mA; each E40S6 ~50 mA.
- Power the external supply before or together with the ESP32.

### Safe GPIOs on ESP32-WROOM-32

GPIOs **6, 7, 8, 9, 10, 11** are connected to internal SPI flash. **Do not use them as I/O.** The pins used in this project are all safe.

### Pin summary (this project)

| Signal    | GPIO | Encoder / notes |
|-----------|------|------------------|
| Theta A   | 32   | E40S6 (Black)    |
| Theta B   | 35   | E40S6 (White)    |
| Phi A     | 14   | E40S6 (Black)    |
| Phi B     | 12   | E40S6 (White)    |
| Wire A    | 16   | DWE3000          |
| Wire B    | 17   | DWE3000          |
| Wire Z    | 18   | DWE3000 (index)  |

Voltage divider required on every signal line (5 V → 3.3 V).

---

## 3. Test 1: Draw-wire encoder only

Connect **only** the draw-wire encoder (OPKON DWE3000). Do not connect theta or phi encoders.

### Wiring

| DWE3000 terminal | Via 10k/20k divider (or Option B) | ESP32 GPIO |
|------------------|-------------------------------------|------------|
| A (Yellow)       | Divider                             | **16**     |
| B (Green)        | Divider                             | **17**     |
| Z (Gray)         | Divider                             | **18**     |

**Power:**

```
External 5 V (+) ──────────── DWE3000 V+ (Brown)
External 5 V (−) ──┬───────── DWE3000 0V (White)
                   └───────── ESP32 GND
```

Do not connect encoder +V to ESP32.

### Commands

From the repository root:

```bash
pio run -e test_drawwire --target upload
```

If upload times out: hold **BOOT**, press **RESET**, release **BOOT**, then retry.

```bash
pio device monitor -e test_drawwire
```

### Expected output at rest

```
DrawWireTest ready. (ESP32 / OPKON DWE3000 quadrature)
Pull wire to increase count, push to decrease.
200 mm pull -> COUNT ~2000, Z_ticks +1
--------------------------------------------
COUNT=0  DIST_mm=0.0  Z_ticks=0
```

### Acceptance criteria

| Action              | Expected result                          |
|---------------------|------------------------------------------|
| Pull wire 200 mm    | COUNT ≈ 2000, DIST_mm ≈ 200.0, Z_ticks +1 |
| Push wire back 200 mm | COUNT ≈ 0, DIST_mm ≈ 0.0                |
| Pull 10 mm          | COUNT changes by ≈ 100                   |
| Full back-and-forth | COUNT tracks in both directions          |

If COUNT goes negative when pulling, swap A and B wires.

---

## 4. Test 2: Theta rotary encoder only

Connect **only** the theta axis Autonics E40S6. Leave phi encoder disconnected (pins 14 and 12 unused). Use the same test app as for phi; only the theta column in the serial output is relevant—ignore PHI (it may be 0 or noisy).

### Wiring

| E40S6 (theta) | Via 10k/20k divider | ESP32 GPIO |
|---------------|----------------------|------------|
| A (Black)     | Divider              | **32**     |
| B (White)     | Divider              | **35**     |

**Power:** External 5 V to encoder, GND common with ESP32. Do not power from ESP32.

### Commands

```bash
pio run -e test_rotary --target upload
```

```bash
pio device monitor -e test_rotary
```

### Expected output

Serial prints every 200 ms. Format: `THETA_counts=<n>  THETA_deg=<n*0.018>  |  PHI_counts=<n>  PHI_deg=<n*0.018>`. When testing theta only, watch **THETA_counts** and **THETA_deg**; ignore the PHI column.

### Acceptance criteria

| Action                    | Expected result                    |
|---------------------------|------------------------------------|
| One full turn CW          | THETA_counts +20000, THETA_deg +360 |
| One full turn CCW         | THETA_counts -20000, THETA_deg -360 |
| Small rotation            | Count and angle track smoothly      |

If direction is inverted, swap A and B wires on the theta encoder.

---

## 5. Test 3: Phi rotary encoder only

Connect **only** the phi axis Autonics E40S6. Leave theta encoder disconnected (pins 32 and 35 unused). Use the same RotaryEncoderTest test app; only the phi column is relevant—ignore THETA (it may be 0 or noisy).

### Wiring

| E40S6 (phi) | Via 10k/20k divider | ESP32 GPIO |
|-------------|----------------------|------------|
| A (Black)   | Divider              | **14**     |
| B (White)   | Divider              | **12**     |

**Power:** External 5 V to encoder, GND common with ESP32. Do not power from ESP32.

### Commands

Same as Test 2:

```bash
pio run -e test_rotary --target upload
pio device monitor -e test_rotary
```

### Expected output

Same format as Test 2. When testing phi only, watch **PHI_counts** and **PHI_deg**; ignore the THETA column.

### Acceptance criteria

| Action                    | Expected result                 |
|---------------------------|---------------------------------|
| One full turn CW          | PHI_counts +20000, PHI_deg +360  |
| One full turn CCW         | PHI_counts -20000, PHI_deg -360  |
| Small rotation            | Count and angle track smoothly  |

If direction is inverted, swap A and B wires on the phi encoder.

---

## 6. Troubleshooting

| Symptom                         | Cause / fix |
|---------------------------------|-------------|
| Constant 3.3 V on A/B           | Encoder unpowered or disconnected; power encoder and check wiring. |
| COUNT or counts stay 0          | Wrong GPIO or broken divider; verify pins and circuit. |
| Counts jump erratically         | GND not common; tie supply GND to ESP32 GND. |
| `raw_edges` rises fast but COUNT stays near 0/1 | Likely one quadrature channel is stuck/miswired; confirm draw-wire **B -> GPIO 17** and **Z -> GPIO 18**, check A/B/Z divider continuity, and verify common GND. |
| Count goes wrong direction      | Swap A and B wires on that encoder. |
| Draw-wire: Z_ticks never increments | Check Z wire and its divider to GPIO 18. |
| Upload timeout                  | Hold BOOT, press RESET, release BOOT, retry. |
| Encoder library not found       | PlatformIO auto-installs it from `platformio.ini`; run `pio lib install` if missing. |
| Port permission denied          | `sudo usermod -aG dialout $USER` then `newgrp dialout` |

More detail: [Setup & Test Guide](setup_test_guide.md) and [DWE3000 Hardware Notes](DWE3000_hardware_notes.md).
