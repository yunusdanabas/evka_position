# ESP32-C3 Hardware Reference

Hardware specifications for the button remote components used in the EvkaPosition wireless pendant.

---

## ESP32-C3 Mini WiFi Bluetooth Board

A compact WiFi + BLE module based on the ESP32-C3 (RISC-V) core.
Used as the MCU in the 2-button wireless remote.

### Technical Specifications

| Specification | Value |
|---------------|-------|
| Model | ESP32 C3 Mini / SuperMini |
| Chip | ESP32C3FN4 |
| Architecture | 32-bit RISC-V |
| Operating Speed | 160 MHz |
| Flash | 4 MB |
| SRAM | 400 KB |
| WiFi | 2.4 GHz IEEE 802.11 b/g/n |
| Bluetooth | BLE 5.0 |
| Digital I/O Pins | 13 |
| Operating Voltage | 3.3 V DC |
| Power Input | USB Type-C |
| Dimensions | ~18 mm × 23 mm (module) |

### Application in This Project

- Runs `firmware/remote/ButtonRemote.cpp` (`ButtonRemote v1.1`)
- GPIO 4: Button 0 (Green / SAVE_POINT) — active LOW, INPUT_PULLUP
- GPIO 5: Button 1 (Red / DEL_POINT) — active LOW, INPUT_PULLUP
- GPIO 8: Built-in blue LED (active HIGH) — ESP-NOW send feedback
- Always-awake ESP-NOW sender; heartbeat every 10 s (`0xFE`)
- Scans main AP SSID `CMDCNC_EVKA` at boot for WiFi channel sync

### Programming Notes

- Program via USB-C (USB-Serial/JTAG — `ttyACM*` on Linux)
- PlatformIO environment: `button_remote` (`esp32-c3-devkitm-1`)
- Build flags: `ARDUINO_USB_MODE=1`, `ARDUINO_USB_CDC_ON_BOOT=1`
- Monitor: `monitor_rts = 0`, `monitor_dtr = 0` in `platformio.ini`
- Strapping pins: GPIO 9 (boot mode — avoid for buttons)

---

## ESP32 C3 SuperMini Expansion Board

An expansion board for the ESP32-C3 SuperMini that adds LiPo battery charging,
regulated power outputs, and header access for buttons.

### Features

- LiPo battery charging via USB-C with charge status LED
- VCC1 and VCC2 regulated 3.3 V outputs
- Full IO header access for tactile buttons
- Compact handheld form factor

### Power Flow

```
USB-C 5V ──→ Charge IC ──→ LiPo 3.7V 500 mAh
                    └──→ LDO 3.3V ──→ ESP32-C3 core
```

### Wiring for Button Remote

| Header Pin | Connect to |
|-----------|-----------|
| GPIO 4 | Button 0 (Green) — other terminal to GND |
| GPIO 5 | Button 1 (Red) — other terminal to GND |
| GND | Common ground |
| BAT+ / BAT- | LiPo battery JST (verify polarity) |

Optional future mod: 100k/100k divider from BAT+ to GPIO2 for battery voltage sense.
