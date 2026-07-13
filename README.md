# Evka Position: Spherical 3D Positioning System

> Türkçe WiFi kullanıcı kılavuzu: [README_TR.md](README_TR.md)

> **New maintainer / taking over this project?** Start at **[HANDOFF.md](HANDOFF.md)**, set up your
> machine with **[CONTRIBUTING.md](CONTRIBUTING.md)** (Ubuntu **and** Windows), learn the internals in
> **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**, and browse everything from the
> **[docs index](docs/README.md)**.

## Overview
Evka Position is a firmware project for the **ESP32** — the classic Wemos D1 R32, or the **ESP32-S3 v4 PCB** (`pcb_design/EVKA_position_v4/`) — that calculates the real-time 3D position (X, Y, Z) of a target object using three sensor inputs:

1. **Theta (θ):** Azimuth angle (horizontal rotation)
2. **Phi (φ):** Elevation angle (vertical tilt)
3. **Radius (r):** Linear distance (draw-wire extension)

## Hardware
- **MCU:** classic ESP32 (Wemos D1 R32 / ESP32-WROOM-32), **or ESP32-S3-DevKitC-1 (N16R8)** on the v4 PCB
- **Rotary encoders:** Autonics E40S6 — 5000 PPR × X4 quadrature = 20000 counts/rev
- **Draw-wire encoder:** OPKON DWEM2 — 8000 theoretical PPR (0.025 mm/count; calibrate with `CAL_W`)
- **Quadrature counting:** `madhephaestus/ESP32Encoder` (hardware PCNT) on both boards
- **Voltage dividers required** on all 6 encoder signal lines (encoder outputs 5V TTL, ESP32 max 3.3V — on the v4 PCB the dividers are on-board)

## Pin Map

The pin map is selected at build time by `PCB_V4` in `SphericalSensor.h`.

**Classic ESP32** (env `wemos_d1_r32`):

| Pin | Signal | | Pin | Signal |
|-----|--------|-|-----|--------|
| 14 / 12 | Theta A / B | | 16 / 17 | Draw-wire A / B |
| 32 / 35 | Phi A / B | | 36 | Battery ADC |
| 2 | WiFi status LED (active-high) | | | |

**v4 PCB — ESP32-S3** (env `esp32s3_v4`, `-DPCB_V4`):

| Pin | Signal | | Pin | Signal |
|-----|--------|-|-----|--------|
| 9 / 10 | Theta A / B | | 7 / 8 | Draw-wire A / B |
| 4 / 5 | Phi A / B | | 1 | Battery ADC (1S LiPo, ÷2) |

v4 encoder ports: J1 = draw-wire, J2 = phi, J3 = theta. Each connector is
`1=A, 2=GND, 3=B, 4=+5V`. Theta/Phi colors: Brown `V+`, Blue `GND`, Black `A`,
White `B`. Draw-wire colors: Yellow `A`, Green `B`, Brown `+V`, White `GND`.

> v4 has **no onboard buttons** (GPIO17/18 unconnected) and no firmware LED (only a hardwired power LED) — the WiFi-status-LED code is a harmless no-op there.

Current compile-time pins, PPR values, battery options, and WiFi feature
flags are defined in `firmware/src/SphericalSensor.h`. If a doc disagrees with
that header, the header is the source of truth.

## Directory Structure

```
firmware/
  src/          # Production firmware (EvkaPosition.cpp, SphericalSensor, WebDashboard, CmdTcpServer)
  tests/        # Standalone test sketches (DrawWireTest, RotaryEncoderTest, ...)
tools/
  position_checker/   # Python real-time 3D visualiser and TCP CMD GUI
  evka_gui/           # Unified control + 3D GUI (Serial/TCP/replay)
  evka_gui_v2/        # Deprecated shim → evka_gui
docs/
  integration/        # CMD software integration guide, setup guide, validation checklist
  calibration/        # Calibration procedures and templates
  firmware/           # NVS guide, FreeRTOS architecture, rework log
  hardware_design/    # System architecture, 5V/12V circuit schematics, BOMs, PCB layouts
```

## Build & Flash (PlatformIO)

> **PlatformIO only** — Arduino IDE and arduino-cli are not supported.

```bash
pip install platformio

pio run -e wemos_d1_r32                        # compile (classic ESP32)
pio run -e wemos_d1_r32 --target upload        # flash
pio device monitor                             # serial monitor (115200 baud)

# v4 PCB (ESP32-S3):
pio run -e esp32s3_v4                           # compile
pio run -e esp32s3_v4 --target upload           # flash
```

On first boot, the firmware waits 2 seconds then calls `setZeroPoint()`. **The device must be at mechanical home (all sensors at zero) before powering on.**

## Serial Output

After boot the firmware prints `DATA` lines at 20 Hz:

```
DATA,<x_mm>,<y_mm>,<z_mm>,<r_mm>,<theta_deg>,<phi_deg>,<is_valid>,<frame_count>,<ts_ms>
```

### Serial / TCP / WebSocket Commands

All commands work over serial (115200 baud), TCP port 8080, and WebSocket equally.

| Command | Response | Description |
|---------|----------|-------------|
| `PING` | `ACK:PONG` | Connectivity check |
| `ZERO` | `ACK:ZERO` | Re-zero all encoder offsets |
| `ZERO_T` / `ZERO_P` / `ZERO_W` | `ACK:ZERO_*` | Zero individual encoder |
| `STATUS` | `STATUS,<valid>,<frame>,<ts>,<r>,<theta>,<phi>,<x>,<y>,<z>` plus `BATT,<v>,<pct>,<is_low>` when enabled | Single status snapshot |
| `CONSTANTS` | `CONSTANTS,<ppr_r>,<ppr_w>,<mm_pp>,<deg_pp>` | Current calibration constants |
| `CAL_W <mm>` | `CAL:WIRE,<factor>,<mm_pp>,<ppr_w>` | Wire calibration trial (factor 0.1–10×) |
| `CAL_T <n>` / `CAL_P <n>` | `CAL:THETA/<PHI>,<counts>,<ppr>` | Rotary calibration (N full turns; ≥100 counts) |
| `SET_PPR_WIRE <v>` | `ACK:PPR_WIRE,<v>` | Set wire PPR in RAM |
| `SET_PPR_ROTARY <v>` | `ACK:PPR_ROTARY,<v>` | Set rotary PPR in RAM |
| `SAVE_PPR` | `ACK:SAVE_PPR` | Persist PPR values to NVS flash |
| `GET_IP` | `STA_IP:<ip>` or `STA_IP:NOT_CONNECTED` | Get router-assigned IP |
| `SYSINFO` | `SYSINFO,<rssi>,<heap>,<uptime_s>,<tcp_clients>` | System diagnostics |
| *(unknown)* | `ERR:UNKNOWN_CMD` | Unrecognized command |

## WiFi Dashboard

`ENABLE_WIFI` defaults to `1`. The ESP32 creates a WiFi access point:

| Setting | Value |
|---------|-------|
| SSID | `CMDCNC_EVKA` |
| Password | `cmdcnc1234` |
| Dashboard | `http://192.168.1.50` |
| TCP data port | `8080` |
| WebSocket | `ws://192.168.1.50/ws` |

**Quick connect:** WiFi settings → select `CMDCNC_EVKA` → enter `cmdcnc1234` → open `http://192.168.1.50`

Dashboard tabs:
- **Live view**: 3D trail, XY/XZ/YZ projections, session CSV export
- **CALIBRATE**: multi-trial wire calibration, theta/phi calibration, endpoint point collection; PPR values can be applied to RAM or saved permanently to NVS flash

> **Subnet conflict warning**: `192.168.1.50` is in the range used by most home/office routers. If the dashboard is unreachable, disconnect your device from the home/office WiFi first — your OS may route `192.168.1.50` to the home router. This IP cannot be changed: CMD CNC software is hardcoded to `192.168.1.50:8080`.
>
> **AP resilience note**: Firmware includes event-driven AP recovery for STA disconnects (AP health reassertion + controlled STA retry backoff). If upstream WiFi drops, `CMDCNC_EVKA` should remain reachable. See `docs/WIFI_PERFORMANCE_ISSUES_LOG.md` (Issue 8) for diagnostics and validation steps.

### WiFi Status LED (GPIO 2)

| LED state | Meaning |
|-----------|---------|
| OFF | No STA credentials configured |
| BLINK (500 ms) | STA configured, connecting |
| SOLID ON | STA connected to router |

Wiring: `GPIO 2 → 1 kΩ resistor → LED anode → LED cathode → GND`

> On the **v4 PCB** GPIO2 is not populated (only a hardwired power LED exists), so this LED code is a harmless no-op there.

### Router Mode (STA)

Save router credentials via the WiFi Settings panel (web dashboard) or `WIFI_SET:<ssid>,<pass>` command. `ENABLE_REMOTE_WIFI_CONFIG=1` is the current default — credentials are accepted over TCP and WebSocket, saved to NVS, and the device reboots. STA uses a hardcoded static profile (`192.168.1.84 / 255.255.255.0`, gateway `192.168.1.254`, DNS `8.8.8.8`), so `GET_IP` reports that fixed address when connected. The AP fallback `192.168.1.50` stays active.

For CMD software connection details and fallback behavior, see `docs/integration/CMD_SOFTWARE_INTEGRATION.md`.

## Wireless Button Remote (ESP-NOW)

A 2-button ESP32-C3 SuperMini pendant communicates with the main board via ESP-NOW.
No pairing required — it ESP-NOW-broadcasts and auto-discovers the AP's channel by
scanning for SSID `CMDCNC_EVKA`, so it works unchanged with either the classic ESP32
or the v4 ESP32-S3 board (no MAC is hardcoded).

| Button | GPIO | Color | Command | Action |
|--------|------|-------|---------|--------|
| 0 | 4 | Green | `SAVE_POINT` | Save current position snapshot |
| 1 | 5 | Red | `DEL_POINT` | Delete the last saved point |

**Build & flash remote firmware:**
```bash
pio run -e button_remote --target upload
```

Hardware: ESP32-C3 SuperMini + expansion board (LiPo 500 mAh, USB-C charging). Battery life ~14 months.
See `docs/hardware_design/remote/` for schematic, BOM, and board specs.

## TCP Raw Data (Port 8080)

Connect a TCP socket to `192.168.1.50:8080` (or STA IP after router join). The ESP32 supports up to 3 simultaneous clients.

**ESP32 → client broadcast at 20 Hz:**

```
X123.45,Y-56.78,Z890.12
SENSOR,900.00,25.000,10.000,1,42
```

Field order for `SENSOR`: `r_mm, theta_deg, phi_deg, is_valid, frame_count`

`STATUS` also returns/broadcasts `BATT,<voltage>,<percent>,<is_low>` when
`ENABLE_BATTERY_MONITOR=1`.

**Client → ESP32:** any command from the table above, newline-terminated.

## WebSocket

Connect to `ws://192.168.1.50/ws`. Broadcasts at 20 Hz:

```
DATA,123.45,-56.78,890.12,900.00,25.000,10.000,1,42,12345
```

Field order: `x_mm, y_mm, z_mm, r_mm, theta_deg, phi_deg, is_valid, frame_count, ts_ms`

Send any command from the table above as a WebSocket text frame.
`STATUS` also returns `BATT,<voltage>,<percent>,<is_low>` when battery monitoring is enabled.

## Python Visualiser Tools

### Install dependencies

```bash
pip install -r tools/position_checker/requirements.txt
# or via pyproject.toml:
pip install numpy PyQt5 pyqtgraph pyserial
```

### 1. Real-time 3D Visualiser (`tools/position_checker`)

```bash
# Live serial (Linux)
python -m tools.position_checker --port /dev/ttyUSB0

# Live serial (Windows)
python -m tools.position_checker --port COM3

# Custom baud + point history + GUI refresh rate
python -m tools.position_checker --port /dev/ttyUSB0 --baud 115200 --maxpoints 1000 --fps 20

# Log parsed DATA frames to CSV while running
python -m tools.position_checker --port /dev/ttyUSB0 --csv-log session.csv

# Replay from a previously saved CSV (no hardware needed)
python -m tools.position_checker --replay-file session.csv --fps 20

# Disable calibration transform (raw encoder coordinates)
python -m tools.position_checker --port /dev/ttyUSB0 --calibration none

# Disable serial auto-reconnect
python -m tools.position_checker --port /dev/ttyUSB0 --no-reconnect
```

| Flag | Default | Description |
|------|---------|-------------|
| `--port` | *(required)* | Serial port (`/dev/ttyUSB0`, `COM3`, etc.) |
| `--baud` | `115200` | Baud rate |
| `--maxpoints` | `500` | Point history kept in memory |
| `--fps` | `10` | GUI refresh rate and replay playback speed |
| `--csv-log` | *(off)* | Output CSV path for parsed DATA frames |
| `--replay-file` | *(off)* | Read frames from CSV instead of serial port |
| `--calibration` | `tools/calibration/calibration.json` | Path to calibration JSON; pass `none` to disable |
| `--reconnect` | `true` | Auto-reconnect serial on disconnect |
| `--no-reconnect` | — | Disable serial auto-reconnect |
| `--reconnect-interval` | `1.0` | Initial reconnect delay (seconds) |

### 2. CMD TCP GUI (`tools/position_checker/cmd_main.py`)

Linux control panel equivalent of the Windows CMD CNC GUI. Connects to the ESP32 over WiFi TCP (port 8080). Displays live X/Y/Z, R/θ/φ, min/max tracking, system info, and WiFi settings.

```bash
python -m tools.position_checker.cmd_main
```

#### Known IP addresses

| Address | When to use |
|---------|-------------|
| `192.168.1.50` | **AP fallback** — always reachable on the `CMDCNC_EVKA` access point |
| `192.168.1.84` | **STA static IP** — router mode with hardcoded profile (`GW 192.168.1.254`, mask `255.255.255.0`, DNS `8.8.8.8`) |

> After connecting to a router, send `GET_IP` from the GUI (or serial) to confirm STA connectivity. The GUI auto-updates the IP field from the `STA_IP:` response.

Port is always **8080** regardless of AP or STA mode.

### 3. Quick IPT (`tools/ipt`)

Hidden-point measurement tool. Recovers a target point that the pen cannot touch
directly (around a corner, behind an obstacle, inside a recess) using the Prodim
Proliner's "Quick IPT" (Inverted Pen Technology) method.

```bash
# WiFi (AP fallback)
python -m tools.ipt --tcp 192.168.1.50:8080

# Serial
python -m tools.ipt --serial /dev/ttyUSB0 --baud 115200
```

Hold the pen **tip** on the hidden target, sweep the **handle** in a wide spiral,
and fit a sphere to recover the target. See `tools/ipt/README.md` for full
workflow, quality flags, and troubleshooting.

### 4. EVKA Unified Control GUI (`tools/evka_gui`)

Single-window control panel + 3D view for v4 board bring-up and daily operation.
Supports Serial, WiFi/TCP (AP `192.168.1.50` or STA `192.168.1.84`/ASMETAL), and
CSV replay. Calibration opens in a separate window.

```bash
python -m tools.evka_gui                              # open disconnected
python -m tools.evka_gui --serial /dev/ttyUSB0 --baud 115200
python -m tools.evka_gui --tcp 192.168.1.50:8080        # AP direct
python -m tools.evka_gui --tcp 192.168.1.84:8080        # STA (ASMETAL)
```

`tools/evka_gui_v2` and `tools/position_checker/{main,cmd_main}` are deprecated
shims. Full feature matrix:
[`tools/README.md`](tools/README.md#evka_gui--unified-control-gui-canonical).

## Mathematical Model

Elevation-azimuth convention (phi = 0 is horizontal):

```
X = r * cos(phi) * cos(theta)
Y = r * cos(phi) * sin(theta)
Z = r * sin(phi)
```

## Firmware Reliability Status (2026-04-09)

A full code-review pass (Gemini + Copilot) was run after the 2026-04-08 WiFi recovery implementation. All code findings from that session were fixed. Build: **SUCCESS**, Flash −260 bytes.

Key fixes:
- **`normalizeAngle()` was O(N)** — while-loops replaced with `fmodf` (O(1) regardless of encoder count)
- **STA retry watchdog** — if IDF misses a DISCONNECTED event, retry self-recovers after 15 s
- **NaN/Inf guards** on spherical coordinates in `validateLimits()` (before the range checks)
- **Float math** — all trig and EMA filter literals changed to `f`-suffix; `sinf/cosf/asinf/atan2f/sqrtf` used throughout (ESP32 has no hardware double FPU)
- **6 WiFi recovery bugs** fixed: volatile flags, backoff formula dedup, millis() overflow, `setAutoReconnect(false)`, AP mode guard

Full fix log and pending hardware validation steps: `docs/WIFI_PERFORMANCE_ISSUES_LOG.md` (2026-04-09 section + Open Items)

> **Heap note**: ESPAsyncWebServer v1.2.4 (installed) uses a **shared buffer model** for `textAll()` — one malloc per broadcast, not one per client. The heap concern noted in prior documentation was based on GitHub master behavior and does not apply to this version.

## Integration Docs

- CMD quick integration: `docs/integration/CMD_SOFTWARE_INTEGRATION.md`
- Detailed change history: `docs/integration/CMD_INTEGRATION_CHANGELOG.md`
- Hardware setup & wiring: `docs/integration/setup_test_guide.md`
- Calibration procedures: `docs/calibration/README.md`
- NVS calibration persistence: `docs/firmware/ESP32_NVS_CALIBRATION_GUIDE.md`
- System architecture: `docs/hardware_design/system_architecture.md`
- **Full documentation index:** `docs/README.md`

## License & Ownership

This repository currently has **no license file** — it is unlicensed (all rights reserved by
default). The owner should choose a license. The "CMD" C# app and its original ESP32 firmware under
`firmware/src/CMD Soft/` originate from an external vendor; confirm their terms before redistribution.
See [HANDOFF.md](HANDOFF.md) §6.
