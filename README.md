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

## Directory Structure

```
firmware/
  src/          # Production firmware (EvkaPosition.cpp, SphericalSensor)
  tests/        # Standalone test sketches (DrawWireTest, RotaryEncoderTest, ...)
tools/
  position_checker/   # Python real-time 3D visualiser
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
DATA,<r_mm>,<theta_deg>,<phi_deg>,<x_mm>,<y_mm>,<z_mm>
```

### Serial Commands

| Command | Response | Description |
|---------|----------|-------------|
| `ZERO`  | `ACK:ZERO` | Re-zero all encoder offsets |
| `PING`  | `ACK:PONG` | Connectivity check |
| `STATUS` | `STATUS,<valid>,<frame>,<ts_ms>,<r>,<theta>,<phi>,<x>,<y>,<z>` | Single status snapshot |

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

## WiFi Dashboard (optional)

Set `ENABLE_WIFI 1` in `firmware/src/SphericalSensor.h` to enable a WiFi access point named **EvkaPosition**. Connect and open `http://192.168.4.1` for a live web dashboard.
