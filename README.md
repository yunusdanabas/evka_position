# Evka Position: Spherical 3D Positioning System

## Overview
Evka Position is a firmware project for the **ESP32 (Wemos D1 R32)** that calculates the real-time 3D position $(X, Y, Z)$ of a target object using three sensor inputs:

1. **$\theta$ (Theta):** Azimuth angle (horizontal rotation)
2. **$\phi$ (Phi):** Elevation angle (vertical tilt)
3. **$r$ (Radius):** Linear distance (draw-wire extension)

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
| 2   | WiFi status LED output (active-high) |

## Directory Structure

```
firmware/
  src/          # Production firmware (EvkaPosition.cpp, SphericalSensor)
  tests/        # Standalone test sketches (DrawWireTest, RotaryEncoderTest, ...)
tools/
  position_checker/   # Python real-time 3D visualiser
docs/
  CMD_SOFTWARE_INTEGRATION.md  # Quick CMD software integration guide
```

## Build & Flash (PlatformIO)

> **PlatformIO only** — Arduino IDE and arduino-cli are not supported.

```bash
# Install PlatformIO CLI
pip install platformio

# Compile
pio run -e wemos_d1_r32

# Flash to ESP32
pio run -e wemos_d1_r32 --target upload

# Open serial monitor (115200 baud)
pio device monitor
```

On first boot, the firmware waits 2 seconds then calls `setZeroPoint()`. **Make sure the device is at mechanical home (all sensors at zero position) before powering on.**

## Serial Output

After boot the firmware prints `DATA` lines at 20 Hz:

```
DATA,<x_mm>,<y_mm>,<z_mm>,<r_mm>,<theta_deg>,<phi_deg>,<is_valid>,<frame_count>,<ts_ms>
```

### Serial Commands

| Command | Response | Description |
|---------|----------|-------------|
| `ZERO` | `ACK:ZERO` | Re-zero all encoder offsets |
| `PING` | `ACK:PONG` | Connectivity check |
| `STATUS` | `STATUS,<valid>,<frame>,<ts_ms>,<r>,<theta>,<phi>,<x>,<y>,<z>` | Single status snapshot |
| `CONSTANTS` | `CONSTANTS,<ppr_r>,<ppr_w>,<mm_pp>,<deg_pp>` | Current calibration constants |
| `ZERO_T` / `ZERO_P` / `ZERO_W` | `ACK:ZERO_*` | Zero individual encoder |
| `CAL_W <mm>` | `CAL:WIRE,<factor>,<mm_pp>,<ppr_w>` or `ERR:CAL_W …` | Wire calibration trial (factor must be 0.1–10×) |
| `CAL_T <n>` / `CAL_P <n>` | `CAL:THETA/<PHI>,<counts>,<ppr>` or `ERR:CAL_* …` | Rotary calibration (N full turns; ≥100 encoder counts required) |
| `SET_PPR_WIRE <v>` | `ACK:PPR_WIRE,<v>` | Set wire PPR (RAM) |
| `SET_PPR_ROTARY <v>` | `ACK:PPR_ROTARY,<v>` | Set rotary PPR (RAM) |
| `SAVE_PPR` | `ACK:SAVE_PPR` | Persist current PPR values to NVS flash |
| *(any unknown)* | `ERR:UNKNOWN_CMD` | Unrecognized command |

## Python Visualiser

```bash
cd tools/position_checker
pip install -r requirements.txt
python main.py --port /dev/ttyUSB0
```

Displays a live 3D scatter plot of the position data.

## Mathematical Model

Elevation-azimuth convention (phi = 0 is horizontal):

$$
\begin{align*}
X &= r \cdot \cos(\phi) \cdot \cos(\theta) \\
Y &= r \cdot \cos(\phi) \cdot \sin(\theta) \\
Z &= r \cdot \sin(\phi)
\end{align*}
$$

## WiFi Dashboard

`ENABLE_WIFI` defaults to `1`. The ESP32 creates a WiFi access point named **CMDCNC** (password `cmdcnc1234`). Connect and open `http://192.168.1.50`.

- **Live view**: 3D trail, XY/XZ/YZ projections, session CSV export
- **CALIBRATE tab**: multi-trial wire calibration with mean/spread stats, theta/phi calibration, endpoint world-transform point collection. PPR values can be applied to RAM or saved permanently to NVS flash (survives power cycles).

Router mode note (STA):
- After saving router credentials, query `GET_IP` and use returned `STA_IP:<ip>` for TCP clients.
- Latest confirmed ASMETAL example: `STA_IP:192.168.1.84` (TCP port remains `8080`).
- Keep AP fallback `192.168.1.50` for direct CMDCNC connections.

### WiFi Status LED (GPIO 2)

WiFi status LED behavior is already implemented in firmware on `PIN_WIFI_LED` (`GPIO 2`) in `firmware/src/SphericalSensor.h` and driven in `firmware/src/EvkaPosition.cpp`.

- `OFF`: no STA credentials configured
- `BLINK (500 ms)`: STA configured but not connected yet
- `SOLID ON`: `WiFi.status() == WL_CONNECTED`

External LED connection (recommended):

- `GPIO 2 -> 1k resistor -> LED anode (+)`
- `LED cathode (-) -> GND`
- Keep series resistor in the `680 ohm` to `1k ohm` range (`1k` preferred for lower current)

Quick verification checklist:

1. Boot with no saved STA credentials: LED stays `OFF`.
2. Save STA credentials and reboot: LED should `BLINK` while trying to connect.
3. After successful STA connection: LED should become `SOLID ON`.
4. Power cycle or disconnect router: LED should return to `BLINK` (or `OFF` if STA config is cleared).
## Integration Docs

- CMD quick integration: `docs/CMD_SOFTWARE_INTEGRATION.md`
- Detailed change history and rationale: `docs/CMD_INTEGRATION_CHANGELOG.md`
