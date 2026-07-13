# Setup & Test Guide — OPKON DWEM2 on Wemos D1 R32 (ESP32)
_Session: 2026-02-18_

> **v4 PCB users:** this guide covers bench bring-up on the classic Wemos board with
> breadboard dividers. For the **v4 PCB** (ESP32-S3, `pcb_design/EVKA_position_v4/`)
> the dividers and wiring are on-board — you only connect the three encoder terminal
> blocks (J1=Wire, J2=Phi, J3=Theta) and power. Build/flash with `pio run -e esp32s3_v4`.
> Firmware pins: Theta 9/10, Phi 4/5, Wire 7/8, battery ADC GPIO1. See
> `pcb_design/EVKA_position_v4/FIRMWARE.md`.

---

## 1. Hardware Wiring

### Power

Use an external 5 V supply (5–30 V accepted by DWEM2).
GND must be shared between supply, encoder, and ESP32.

```
External 5 V (+) ──────────── DWEM2 V+ (Brown)
External 5 V (−) ──┬───────── DWEM2 0V (White)
                   └───────── ESP32 GND
```

Do NOT connect encoder +V to ESP32. Power external supply before the ESP32.

### Signal Lines — Two Options

#### Option A: Proper voltage divider (production)

Build one per signal line (A, B, Z):

```
DWEM2 signal (5 V swing)
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
DWEM2 signal ──── 2.2 kΩ ──── ESP32 GPIO ──── 10 kΩ ──── 3.3 V
```

Works correctly. GPIO reads ~0.6 V (LOW) / ~3.8 V clamped (HIGH).
ESD diode current ≈ 0.55 mA — safe for development, not ideal long-term.
Before encoder is powered you will see constant 3.3 V — this is normal (pull-up).

### GPIO Connections

| DWEM2 terminal | Via circuit | ESP32 GPIO |
|---|---|---|
| A (Yellow) | Divider or 2.2kΩ+pullup | **16** |
| B (Green) | Divider or 2.2kΩ+pullup | **17** |
| Z (Gray) | Divider or 2.2kΩ+pullup | **18** |

---

## 2. PC Toolchain Setup

### Install PlatformIO

Linux/macOS:
```bash
pip install -U platformio
pio --version
```

Windows PowerShell:
```powershell
py -m pip install -U platformio
py -m platformio --version
```

> Alternatively install the PlatformIO IDE extension in VS Code (search "PlatformIO IDE").
> Classic Visual Studio (MSVC/.sln workflow) cannot build or flash this ESP32 firmware by itself.

Board support (espressif32) and the `ESP32Encoder` library are declared in `platformio.ini` and downloaded automatically on first build — no manual installation required.

### If a vendor is using Visual Studio

Use one of these supported workflows:

1. **VS Code + PlatformIO extension** (recommended)
2. **PlatformIO CLI** from terminal

Required project root must contain:

- `platformio.ini`
- `firmware/` directory

Working command sequence from project root:

Linux/macOS:
```bash
pio run -e wemos_d1_r32
pio run -e wemos_d1_r32 --target upload
pio device monitor -e wemos_d1_r32
```

Windows PowerShell (works even when `pio` is not in PATH):
```powershell
py -m platformio run -e wemos_d1_r32
py -m platformio run -e wemos_d1_r32 --target upload
py -m platformio device monitor -e wemos_d1_r32
```

If upload fails because wrong port is auto-selected, set explicit upload port:

Linux/macOS:
```bash
pio run -e wemos_d1_r32 --target upload --upload-port /dev/ttyUSB0
```

Windows PowerShell:
```powershell
py -m platformio run -e wemos_d1_r32 --target upload --upload-port COM5
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

### Compile and upload

```bash
pio run -e test_drawwire --target upload
```

If upload times out: hold **BOOT**, press **RESET**, release **BOOT**, retry.

### Serial monitor

```bash
pio device monitor -e test_drawwire
```

### Expected output at rest

```
DrawWireTest ready. (ESP32 / OPKON DWEM2 quadrature)
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

## 4. Phase 2 — Compile Main Firmware

```bash
pio run -e wemos_d1_r32
```

Zero errors = firmware compiles correctly. Proceed to Phase 3 to flash.

---

## 5. Phase 3 — Full System (all encoders connected)

`PIN_THETA_A = 14`, `PIN_THETA_B = 12`, `PIN_PHI_A = 32`, `PIN_PHI_B = 35`

Compile and flash:

```bash
pio run -e wemos_d1_r32 --target upload
```

Boot the ESP32 with robot at **mechanical home** (wire fully retracted, angles at zero).
Firmware waits 2 s then auto-calls `setZeroPoint()`.
After that, serial prints `DATA,x,y,z,...` lines at 20 Hz.

To re-zero without reflashing, send `ZERO\n` over serial.

---

## 6. Wireless Button Remote (ESP32-C3)

The ESP-NOW pendant is a **separate** ESP32-C3 board (`button_remote` env). It does not
use the main sensor firmware.

### Flash the remote

```bash
pio device list                                    # find ttyACM* (ESP32-C3 USB)
pio run -e button_remote --target upload --upload-port /dev/ttyACM0
pio device monitor -e button_remote
```

Expected serial output: `ButtonRemote v1.1`, AP scan for `CMDCNC_EVKA`, `ESP-NOW ready`,
heartbeat every ~10 s.

### Verify with main board

1. Flash main firmware (`esp32s3_v4` or `wemos_d1_r32`) with `ENABLE_ESPNOW_REMOTE=1`
2. Power main board first so AP `CMDCNC_EVKA` is visible
3. Reset remote — it should find the AP channel (or fall back to ch 1)
4. Green button (GPIO 4) → `SAVE_POINT`; red button (GPIO 5) → `DEL_POINT`
5. TCP/WebSocket clients see `REMOTE_HB` and `REMOTE_BTN:0/1`

### Bench test without main board

```bash
pio run -e button_remote_test --target upload
python tools/remote_tester/remote_test_gui.py
```

See `docs/hardware_design/remote/README.md` for hardware wiring and button maps.

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Constant 3.3 V on A/B before powering encoder | Normal — pull-up with encoder unpowered | Power the encoder |
| COUNT stays 0 after powering | Wrong GPIO / broken divider | Probe GPIO 16 — should toggle 0–3.3 V when pulling wire |
| COUNT jumps erratically | GND not common between supply and ESP32 | Tie all GNDs together |
| `raw_edges` rises fast but COUNT stays near 0/1 | One quadrature channel stuck or B/Z pin-map swap | Confirm draw-wire B -> GPIO 17 and Z -> GPIO 18, verify A/B/Z divider continuity, tie all grounds, then run `DIAG` while moving wire |
| COUNT goes negative on pull | A and B swapped | Swap A↔B wires |
| Z_ticks never increments | GPIO 18 not connected | Check Z wire and its divider |
| Upload timeout | Board not entering bootloader | Hold BOOT → RESET → release BOOT → retry |
| `Could not open /dev/ttyS0` (Linux) or `COMx` open failure (Windows) | Auto-selected wrong port or busy port | Run `pio device list` (or `py -m platformio device list` on Windows) and retry with explicit `--upload-port` |
| `Encoder` not found on compile | Library missing | PlatformIO auto-installs from `platformio.ini`; run `pio lib install` if needed |
| Port permission denied | User not in dialout | `sudo usermod -aG dialout $USER && newgrp dialout` |
| False phi counts after main firmware flash | PHI_A wired to wrong GPIO | Verify phi A wire goes to GPIO 32 divider |

### Failure artifact bundle (send to project team)

If flashing still fails, provide:

1. Exact command used
2. First error block from output
3. Result of `pio device list`
4. Board model and USB cable type (data-capable vs charge-only)
