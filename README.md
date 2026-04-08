# Evka Position: Spherical 3D Positioning System

> Türkçe WiFi kullanıcı kılavuzu: [README_TR.md](README_TR.md)

## Overview
Evka Position is a firmware project for the **ESP32 (Wemos D1 R32)** that calculates the real-time 3D position (X, Y, Z) of a target object using three sensor inputs:

1. **Theta (θ):** Azimuth angle (horizontal rotation)
2. **Phi (φ):** Elevation angle (vertical tilt)
3. **Radius (r):** Linear distance (draw-wire extension)

## Hardware
- **MCU:** ESP32 (Wemos D1 R32 / ESP32-WROOM-32)
- **Rotary encoders:** Autonics E40S6 — 5000 PPR × X4 quadrature = 20000 counts/rev
- **Draw-wire encoder:** OPKON DWE3000 — 8020 calibrated PPR (~0.02494 mm/pulse)
- **Voltage dividers required** on all 6 encoder signal lines (encoder outputs 5V TTL, ESP32 max 3.3V)

## Pin Map

| Pin | Signal |
|-----|--------|
| 14  | Theta encoder A |
| 12  | Theta encoder B |
| 32  | Phi encoder A |
| 35  | Phi encoder B |
| 16  | Draw-wire encoder A |
| 17  | Draw-wire encoder B |
| 2   | WiFi status LED (active-high) |

## Directory Structure

```
firmware/
  src/          # Production firmware (EvkaPosition.cpp, SphericalSensor, WebDashboard, CmdTcpServer)
  tests/        # Standalone test sketches (DrawWireTest, RotaryEncoderTest, ...)
tools/
  position_checker/   # Python real-time 3D visualiser and TCP CMD GUI
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

pio run -e wemos_d1_r32                        # compile
pio run -e wemos_d1_r32 --target upload        # flash
pio device monitor                             # serial monitor (115200 baud)
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
| `STATUS` | `STATUS,<valid>,<frame>,<ts>,<r>,<theta>,<phi>,<x>,<y>,<z>` | Single status snapshot |
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

### WiFi Status LED (GPIO 2)

| LED state | Meaning |
|-----------|---------|
| OFF | No STA credentials configured |
| BLINK (500 ms) | STA configured, connecting |
| SOLID ON | STA connected to router |

Wiring: `GPIO 2 → 1 kΩ resistor → LED anode → LED cathode → GND`

### Router Mode (STA)

After saving router credentials via the WiFi Settings panel (or `WIFI_SET:<ssid>,<pass>` command when `ENABLE_REMOTE_WIFI_CONFIG=1`), send `GET_IP` to get the router-assigned IP. TCP port remains `8080`. The AP fallback `192.168.1.50` stays active.

## TCP Raw Data (Port 8080)

Connect a TCP socket to `192.168.1.50:8080` (or STA IP after router join). The ESP32 supports up to 3 simultaneous clients.

**ESP32 → client broadcast at 20 Hz:**

```
X123.45,Y-56.78,Z890.12
SENSOR,900.00,25.000,10.000,1,42
```

Field order for `SENSOR`: `r_mm, theta_deg, phi_deg, is_valid, frame_count`

**Client → ESP32:** any command from the table above, newline-terminated.

## WebSocket

Connect to `ws://192.168.1.50/ws`. Broadcasts at 20 Hz:

```
DATA,123.45,-56.78,890.12,900.00,25.000,10.000,1,42,12345
```

Field order: `x_mm, y_mm, z_mm, r_mm, theta_deg, phi_deg, is_valid, frame_count, ts_ms`

Send any command from the table above as a WebSocket text frame.

## Python Visualiser Tools

### 1. Real-time 3D Visualiser (`tools/position_checker`)

```bash
cd tools/position_checker && pip install -r requirements.txt

python -m tools.position_checker --port /dev/ttyUSB0             # live serial
python -m tools.position_checker --replay-file frames.csv --fps 20  # replay
```

Key flags: `--port`, `--baud 115200`, `--maxpoints 500`, `--fps 10`, `--csv-log out.csv`

### 2. CMD TCP GUI (`tools/position_checker/cmd_main.py`)

Linux control panel equivalent of `firmware/src/CMD Soft/gui.cs`. Connects to ESP32 over WiFi TCP.

```bash
python -m tools.position_checker.cmd_main
```

## Mathematical Model

Elevation-azimuth convention (phi = 0 is horizontal):

```
X = r * cos(phi) * cos(theta)
Y = r * cos(phi) * sin(theta)
Z = r * sin(phi)
```

## Integration Docs

- CMD quick integration: `docs/integration/CMD_SOFTWARE_INTEGRATION.md`
- Detailed change history: `docs/integration/CMD_INTEGRATION_CHANGELOG.md`
- Hardware setup & wiring: `docs/integration/setup_test_guide.md`
- Calibration procedures: `docs/calibration/README.md`
- NVS calibration persistence: `docs/firmware/ESP32_NVS_CALIBRATION_GUIDE.md`
- System architecture: `docs/hardware_design/system_architecture.md`
