# Wireless Button Remote — ESP-NOW Pendant

A battery-powered 5-button wireless remote that sends commands to the main EvkaPosition ESP32 via ESP-NOW.

## Overview

| Feature | Value |
|---------|-------|
| Protocol | ESP-NOW (peer-to-peer, MAC layer) |
| Latency | 1-5 ms button-to-action |
| Range | 50m+ indoor, 200m+ outdoor |
| Battery life | ~14 months on 500 mAh LiPo |
| MCU | ESP32-C3 (XIAO ESP32-C3 recommended) |
| Buttons | 5 (color-coded) |

## Button Map

| Button | Color | Command | Action |
|--------|-------|---------|--------|
| 0 | Green | `SAVE_POINT` | Save current position (serial + WebSocket) |
| 1 | Red | `ZERO` | Re-zero all encoders |
| 2 | Blue | `RECORD_TOGGLE` | Start/stop recording |
| 3 | Yellow | `ZERO_T` | Zero theta encoder only |
| 4 | White | `ZERO_W` | Zero wire encoder only |

## Build & Flash

```bash
# Compile button remote firmware
pio run -e button_remote

# Upload to XIAO ESP32-C3
pio run -e button_remote --target upload

# Monitor (debug mode only)
pio device monitor -e button_remote
```

## Firmware Configuration

Edit `firmware/remote/ButtonRemote.cpp`:

| Define | Default | Description |
|--------|---------|-------------|
| `BTN_SAVE_POINT` | GPIO 2 | Save point button pin |
| `BTN_ZERO` | GPIO 3 | Zero all button pin |
| `BTN_RECORD` | GPIO 4 | Record toggle button pin |
| `BTN_ZERO_THETA` | GPIO 5 | Zero theta button pin |
| `BTN_ZERO_WIRE` | GPIO 6 | Zero wire button pin |
| `PIN_LED` | -1 | LED pin (-1 = disabled) |
| `ESPNOW_CHANNEL` | 1 | Must match main AP WiFi channel |
| `DEBUG_MODE` | 0 | 1 = stay awake with serial output |

## Main Firmware Configuration

In `SphericalSensor.h`:

| Define | Default | Description |
|--------|---------|-------------|
| `ENABLE_ESPNOW_REMOTE` | 1 | Enable/disable ESP-NOW receiver |
| `ESPNOW_CHANNEL` | 1 | WiFi channel (auto-matches AP) |

## How It Works

1. All 5 buttons are GPIO wake sources in deep sleep
2. Button press wakes ESP32-C3 (~300 us)
3. Firmware reads which button is LOW
4. Initializes ESP-NOW, sends 1-byte button ID as broadcast
5. Waits for send confirmation (~5 ms)
6. Returns to deep sleep
7. Main ESP32 receives packet, maps button ID to command, calls `processCommand()`

## New Serial/WebSocket Commands

These commands are available from any source (serial, TCP, WebSocket, ESP-NOW remote):

- `SAVE_POINT` -> `POINT,<idx>,<x>,<y>,<z>,<r>,<theta>,<phi>` — saves current position
- `RECORD_TOGGLE` -> `ACK:RECORD_ON` / `ACK:RECORD_OFF` — toggles recording mode

## Hardware Docs

- [Bill of Materials](bill_of_materials.md)
- [Circuit Schematic](circuit_schematic.md)

## Changing Button Functions

Button-to-command mapping is defined on the **receiver** side in `EvkaPosition.cpp`:

```cpp
static const char* const REMOTE_BUTTON_CMD[] = {
    "SAVE_POINT",       // Button 0
    "ZERO",             // Button 1
    "RECORD_TOGGLE",    // Button 2
    "ZERO_T",           // Button 3
    "ZERO_W"            // Button 4
};
```

Change this array and reflash the main ESP32 to remap buttons — no need to reflash the remote.
