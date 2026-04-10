# Wireless Button Remote — ESP-NOW Pendant

A battery-powered 2-button wireless remote that sends commands to the main EvkaPosition ESP32 via ESP-NOW.

## Overview

| Feature | Value |
|---------|-------|
| Protocol | ESP-NOW (peer-to-peer, MAC layer) |
| Latency | 1-5 ms button-to-action |
| Range | 50m+ indoor, 200m+ outdoor |
| Battery life | ~14 months on 500 mAh LiPo |
| MCU | ESP32-C3 Mini / SuperMini (ESP32C3FN4) |
| Expansion board | ESP32 C3 SuperMini Expansion Board (LiPo + USB charging, full IO) |
| Buttons | 2 (production) / 5 (test mode, GPIOs 4, 5, 0, 1, 3) |

## Button Map (Production)

| Button | Color | GPIO | Command | Action |
|--------|-------|------|---------|--------|
| 0 | Red | GPIO 4 | `ZERO` | Re-zero all encoders |
| 1 | Green | GPIO 5 | `SAVE_POINT` | Save current position (serial + WebSocket) |

## Build & Flash

```bash
# Compile and upload production firmware (ESP-NOW)
pio run -e button_remote --target upload

# Monitor — ESP32-C3 USB-Serial/JTAG requires RTS/DTR suppressed
# (already set in platformio.ini for button_remote_test; add manually for button_remote if needed)
pio device monitor -e button_remote
```

## Standalone Hardware Test Mode

Use `button_remote_test` to verify all buttons and the TCP stack **without the main ESP32**.
The ESP32-C3 creates its own WiFi AP so you connect your PC directly.

```bash
# Flash test firmware
pio run -e button_remote_test --target upload

# Monitor serial output (monitor_rts=0 / monitor_dtr=0 already set in platformio.ini)
pio device monitor -e button_remote_test
```

**Test AP:** `REMOTE_TEST` / `remote1234` → IP `192.168.4.1` port `8080`

**Run the PC-side GUI:**
```bash
python tools/remote_tester/remote_test_gui.py
```

### Test Button Map (5 buttons)

| Button | GPIO | Protocol Message |
|--------|------|-----------------|
| BTN0 | GPIO 4 (Red) | `BTN:0\n` |
| BTN1 | GPIO 5 (Green) | `BTN:1\n` |
| BTN2 | GPIO 0 | `BTN:2\n` |
| BTN3 | GPIO 1 | `BTN:3\n` |
| BTN4 | GPIO 3 | `BTN:4\n` |

Heartbeat sent every 5 s: `HB\n`. On connect: `HELLO:REMOTE_TEST\n`.

### ESP32-C3 Serial Monitor Note

The ESP32-C3 USB-Serial/JTAG peripheral (`ttyACM*`) rejects RTS/DTR control signals.
PlatformIO monitor must suppress them or it disconnects immediately (`[Errno 5]`):

```ini
monitor_rts = 0
monitor_dtr = 0
```

This is already set for `[env:button_remote_test]` in `platformio.ini`.

## Firmware Configuration

Edit `firmware/remote/ButtonRemote.cpp`:

| Define | Default | Description |
|--------|---------|-------------|
| `BTN_ZERO` | GPIO 4 | ZERO button pin |
| `BTN_SAVE_POINT` | GPIO 5 | Save point button pin |
| `PIN_LED` | GPIO 8 | Built-in blue LED on SuperMini |
| `ESPNOW_CHANNEL` | 1 | Must match main AP WiFi channel |
| `DEBUG_MODE` | 0 | 1 = stay awake with serial output |

## Main Firmware Configuration

In `firmware/src/SphericalSensor.h`:

| Define | Value | Description |
|--------|-------|-------------|
| `ENABLE_ESPNOW_REMOTE` | 1 | Enable ESP-NOW receiver in main firmware |
| `ESPNOW_CHANNEL` | 1 | WiFi channel (auto-matches AP) |

## How It Works

1. Both buttons are GPIO wake sources in deep sleep
2. Button press wakes ESP32-C3 (~300 µs)
3. Firmware reads which button is LOW
4. Initializes ESP-NOW, sends 1-byte button ID (0 or 1) as broadcast
5. Waits for send confirmation (~5 ms)
6. Returns to deep sleep
7. Main ESP32 receives packet, maps button ID to command, calls `processCommand()`

## Button-to-Command Mapping

Mapping is defined on the **receiver** side in `firmware/src/EvkaPosition.cpp`:

```cpp
static const char* const REMOTE_BUTTON_CMD[] = {
    "ZERO",         // Button 0 — GPIO 4
    "SAVE_POINT",   // Button 1 — GPIO 5
};
```

Change this array and reflash the main ESP32 to remap buttons — no need to reflash the remote.

## Hardware Docs

- [Circuit Schematic](circuit_schematic.md)
- [Bill of Materials](bill_of_materials.md)
- [ESP32-C3 Mini Board Specs](esp32-c3-mini-specs.md)
