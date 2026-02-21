# Setup & Test Guide — OPKON DWE3000 on Wemos D1 R32 (ESP32)
_Session: 2026-02-18_

---

## 1. Hardware Wiring

### Power

Use an external 5 V supply (5–30 V accepted by DWE3000).
GND must be shared between supply, encoder, and ESP32.

```
External 5 V (+) ──────────── DWE3000 +V (Red)
External 5 V (−) ──┬───────── DWE3000 GND (Black)
                   └───────── ESP32 GND
```

Do NOT connect encoder +V to ESP32. Power external supply before the ESP32.

### Signal Lines — Two Options

#### Option A: Proper voltage divider (production)

Build one per signal line (A, B, Z):

```
DWE3000 signal (5 V swing)
        │
       10 kΩ
        │
        ├─────── ESP32 GPIO   (3.33 V max when HIGH)
        │
       20 kΩ
        │
       GND (common with ESP32)
```

#### Option B: Legacy circuit (2.2 kΩ + pull-up) — prototyping OK

```
DWE3000 signal ──── 2.2 kΩ ──── ESP32 GPIO ──── 10 kΩ ──── 3.3 V
```

Works correctly. GPIO reads ~0.6 V (LOW) / ~3.8 V clamped (HIGH).
ESD diode current ≈ 0.55 mA — safe for development, not ideal long-term.
Before encoder is powered you will see constant 3.3 V — this is normal (pull-up).

### GPIO Connections

| DWE3000 terminal | Via circuit | ESP32 GPIO |
|---|---|---|
| A (Green) | Divider or 2.2kΩ+pullup | **16** |
| B (White) | Divider or 2.2kΩ+pullup | **17** |
| Z (Yellow) | Divider or 2.2kΩ+pullup | **18** |

---

## 2. PC Toolchain Setup

### Install arduino-cli

```bash
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
sudo mv bin/arduino-cli /usr/local/bin/
arduino-cli version
```

### Add ESP32 board support

```bash
arduino-cli config init
arduino-cli config add board_manager.additional_urls \
  https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

arduino-cli core update-index
arduino-cli core install esp32:esp32
```

### Install Encoder library

```bash
arduino-cli lib install "Encoder"
```

### Verify

```bash
arduino-cli core list    # must show esp32:esp32
arduino-cli lib list     # must show Encoder
```

### Find USB port

```bash
ls /dev/ttyUSB* /dev/ttyACM*
# Unplug, run, plug in, run again — new entry is your port
```

If permission denied:

```bash
sudo usermod -aG dialout $USER
newgrp dialout
```

---

## 3. Phase 1 — DrawWireTest (draw-wire encoder only)

### Compile

```bash
arduino-cli compile \
  --fqbn esp32:esp32:d1_r32 \
  /home/yunusdanabas/evka_position/firmware/tests/DrawWireTest
```

### Upload

```bash
arduino-cli upload \
  --fqbn esp32:esp32:d1_r32 \
  --port /dev/ttyUSB0 \
  /home/yunusdanabas/evka_position/firmware/tests/DrawWireTest
```

If upload times out: hold **BOOT**, press **RESET**, release **BOOT**, retry.

### Serial monitor

```bash
arduino-cli monitor --port /dev/ttyUSB0 --config baudrate=115200
# or:
screen /dev/ttyUSB0 115200
# Exit screen: Ctrl-A then K then Y
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

| Action | Expected result |
|---|---|
| Pull wire 200 mm | `COUNT≈2000  DIST_mm≈200.0  Z_ticks=1` |
| Push wire back 200 mm | `COUNT≈0  DIST_mm≈0.0  Z_ticks=1` |
| Pull 10 mm | COUNT changes by ≈100 |
| Full back-and-forth | COUNT tracks in both directions |

COUNT goes negative when pulling? → Swap A and B wires.

---

## 4. Phase 2 — Compile-Check Main Firmware (no flash yet)

⚠️ Do NOT flash yet. `PIN_PHI_A = 3` is UART0 RX on ESP32 — serial noise causes false phi counts.

```bash
arduino-cli compile \
  --fqbn esp32:esp32:d1_r32 \
  /home/yunusdanabas/evka_position/firmware/EvkaPosition
```

Zero errors = firmware rework is syntactically correct.

---

## 5. Phase 3 — Full System (after PIN_PHI_A remap)

Before flashing the main firmware, edit `SphericalSensor.h`:

```cpp
#define PIN_PHI_A   27   // was 3 (UART0 RX — causes false counts)
#define PIN_PHI_B   26   // was 5
```

Then compile and flash:

```bash
arduino-cli compile \
  --fqbn esp32:esp32:d1_r32 \
  /home/yunusdanabas/evka_position/firmware/EvkaPosition

arduino-cli upload \
  --fqbn esp32:esp32:d1_r32 \
  --port /dev/ttyUSB0 \
  /home/yunusdanabas/evka_position/firmware/EvkaPosition
```

Boot the ESP32 with robot at **mechanical home** (wire fully retracted, angles at zero).
Firmware waits 2 s then auto-calls `setZeroPoint()`.
After that, serial prints `DATA,x,y,z,...` lines at 2 Hz.

To re-zero without reflashing, send `ZERO\n` over serial.

---

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Constant 3.3 V on A/B before powering encoder | Normal — pull-up with encoder unpowered | Power the encoder |
| COUNT stays 0 after powering | Wrong GPIO / broken divider | Probe GPIO 16 — should toggle 0–3.3 V when pulling wire |
| COUNT jumps erratically | GND not common between supply and ESP32 | Tie all GNDs together |
| COUNT goes negative on pull | A and B swapped | Swap A↔B wires |
| Z_ticks never increments | GPIO 18 not connected | Check Z wire and its divider |
| Upload timeout | Board not entering bootloader | Hold BOOT → RESET → release BOOT → retry |
| `Encoder` not found on compile | Library missing | `arduino-cli lib install "Encoder"` |
| Port permission denied | User not in dialout | `sudo usermod -aG dialout $USER && newgrp dialout` |
| False phi counts after main firmware flash | PIN_PHI_A=3 is UART0 RX | Remap to GPIO 27 (Phase 3) |
