# Wireless Button Remote — ESP-NOW Pendant

A battery-powered wireless remote (ESP32-C3) that sends button commands to the main
EvkaPosition board via ESP-NOW. Works with classic ESP32 and v4 ESP32-S3 firmware.

## Overview

| Feature | Value |
|---------|-------|
| Protocol | ESP-NOW (broadcast, 1-byte payload) |
| Latency | 1–5 ms button-to-action |
| Range | 50 m+ indoor (depends on antenna / environment) |
| Power mode | Always-awake (ESP-NOW init once at boot) |
| MCU | ESP32-C3 Mini / SuperMini (ESP32C3FN4) |
| Expansion board | ESP32 C3 SuperMini Expansion Board (LiPo + USB charging) |
| Buttons | 2 in production use / 5 wired for test firmware |
| Main AP SSID | `CMDCNC_EVKA` (scanned at boot for WiFi channel) |
| Firmware version | `ButtonRemote v1.1` |

## Button Map (Production)

Mapping is enforced on the **main board** in `firmware/src/EvkaPosition.cpp`
(`REMOTE_BUTTON_CMD`). Reflash the main ESP32 to change commands — not the remote.

| Button | Color | GPIO | Main-board command | Action |
|--------|-------|------|-------------------|--------|
| 0 | Green | GPIO 4 | `SAVE_POINT` | Save current position |
| 1 | Red | GPIO 5 | `DEL_POINT` | Delete last saved point |

Buttons 2–4 (GPIO 0, 1, 3) are wired but unassigned on the receiver.

## Build & Flash

```bash
pio run -e button_remote --target upload
pio device monitor -e button_remote
```

PlatformIO env `[env:button_remote]` sets USB CDC on boot, and `monitor_rts` /
`monitor_dtr = 0` for stable serial on ESP32-C3 (`ttyACM*`).

**Boot serial should show:**
```
ButtonRemote v1.1
[ButtonRemote] Scanning for 'CMDCNC_EVKA'...
[ButtonRemote] ESP-NOW ready
[ButtonRemote] Heartbeat -> OK
```

Power on the **main board first** so the remote can scan the AP and lock the correct
WiFi channel. See `pcb_design/EVKA_position_v4/FIRMWARE.md` §8 for v4 integration.

## Standalone Hardware Test Mode

Use `button_remote_test` to verify all five buttons **without the main ESP32**.
The ESP32-C3 creates its own WiFi AP; connect your PC directly.

```bash
pio run -e button_remote_test --target upload
pio device monitor -e button_remote_test
python tools/remote_tester/remote_test_gui.py
```

**Test AP:** `REMOTE_TEST` / `remote1234` → IP `192.168.4.1` port `8080`

### Test Button Map (5 buttons)

| Button | GPIO | Protocol Message |
|--------|------|-----------------|
| BTN0 | GPIO 4 (Green) | `BTN:0\n` |
| BTN1 | GPIO 5 (Red) | `BTN:1\n` |
| BTN2 | GPIO 0 | `BTN:2\n` |
| BTN3 | GPIO 1 | `BTN:3\n` |
| BTN4 | GPIO 3 | `BTN:4\n` |

Heartbeat every 5 s: `HB\n`. On connect: `HELLO:REMOTE_TEST\n`.

## Firmware Configuration

Edit `firmware/remote/ButtonRemote.cpp`:

| Define | Default | Description |
|--------|---------|-------------|
| `FIRMWARE_VERSION` | `ButtonRemote v1.1` | Boot banner string |
| `BTN_PINS[]` | `{4,5,0,1,3}` | Button GPIO list (index = ESP-NOW byte) |
| `MAIN_AP_SSID` | `CMDCNC_EVKA` | SSID scanned for channel sync |
| `ESPNOW_CHANNEL` | `1` | Fallback channel if AP not found |
| `HEARTBEAT_INTERVAL_MS` | `10000` | Sends `0xFE` → main rebroadcasts `REMOTE_HB` |
| `PIN_LED` | GPIO 8 | Built-in blue LED (solid=send OK, blink=fail) |

## Main Firmware Configuration

In `firmware/src/SphericalSensor.h`:

| Define | Value | Description |
|--------|-------|-------------|
| `ENABLE_ESPNOW_REMOTE` | `1` | Enable ESP-NOW receiver |
| `ENABLE_WIFI` | `1` | Required — receiver is gated on WiFi |
| `ESPNOW_CHANNEL` | `1` | AP pinned channel (remote scans SSID to match) |

## How It Works

1. Remote boots, scans for `CMDCNC_EVKA`, sets WiFi channel to match main AP
2. ESP-NOW initialised once; broadcast peer added (`FF:FF:FF:FF:FF:FF`)
3. Every 10 s: sends heartbeat byte `0xFE` → main rebroadcasts `REMOTE_HB`
4. On button press (debounced): sends button index `0–4`
5. Main board maps index → command, rebroadcasts `REMOTE_BTN:n` + command reply

## Button-to-Command Mapping (receiver)

```cpp
static const char* const REMOTE_BUTTON_CMD[] = {
    "SAVE_POINT",  // Button 0 — GPIO 4 — Green
    "DEL_POINT",   // Button 1 — GPIO 5 — Red
    nullptr,       // Button 2 — GPIO 0
    nullptr,       // Button 3 — GPIO 1
    nullptr,       // Button 4 — GPIO 3
};
```

## Hardware Docs

- [Circuit Schematic](circuit_schematic.md)
- [Bill of Materials](bill_of_materials.md)
- [ESP32-C3 Mini Board Specs](esp32-c3-mini-specs.md)
