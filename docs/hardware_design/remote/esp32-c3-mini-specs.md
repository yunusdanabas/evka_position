# ESP32-C3 Hardware Reference

Hardware specifications for the button remote components used in the EvkaPosition wireless pendant.

---

## ESP32-C3 Mini WiFi Bluetooth Board

A compact, high-performance WiFi + BLE module based on the ESP32-C3 (RISC-V) core.
Used as the MCU in the 2-button wireless remote.

### Technical Specifications

| Specification | Value |
|---------------|-------|
| Model | ESP32 C3 Mini |
| Chip | ESP32C3FN4 |
| Architecture | 32-bit RISC-V |
| Operating Speed | 160 MHz |
| Flash | 4 MB |
| PSRAM | — |
| ROM | 384 KB |
| SRAM | 400 KB |
| WiFi | 2.4 GHz IEEE 802.11 b/g/n |
| Bluetooth | BLE 5.0 (Bluetooth Low Energy) |
| Digital I/O Pins | 13 |
| Operating Voltage | 3.3 V DC |
| Power Input | USB Type-C |
| Operating Temperature | −10 °C to +65 °C |
| Dimensions | 18 mm × 23 mm |
| Weight | 2 g |

### Application in This Project

- Runs `firmware/remote/ButtonRemote.cpp`
- GPIO 4: Button 0 (ZERO) — active LOW, INPUT_PULLUP
- GPIO 5: Button 1 (SAVE_POINT) — active LOW, INPUT_PULLUP
- GPIO 8: Built-in blue LED (active HIGH) — send confirmation feedback
- Deep sleep between presses (~44 µA) for months of battery life
- ESP-NOW broadcast to main positioning ESP32 (channel 1)

### Programming Notes

- Program via USB-C (CDC/JTAG over USB — no USB-to-UART adapter needed)
- PlatformIO environment: `button_remote` (`esp32-c3-devkitm-1` board definition)
- Strapping pins: GPIO 2 (flash voltage), GPIO 8 (flash voltage), GPIO 9 (boot mode — avoid for buttons)

---

## ESP32 C3 SuperMini Expansion Board

An expansion board designed for the ESP32-C3 SuperMini that adds LiPo battery
charging, regulated power outputs, and easy IO access via headers.

### Technical Specifications

| Specification | Value |
|---------------|-------|
| Dimensions | 37.4 mm × 22.5 mm × 15.2 mm |
| Power Supplies | VCC1 and VCC2 |
| Default Output Voltage | 3.3 V (both VCC outputs) |
| Adjustable Output | 3.7 V (remove 0R resistor, bridge three pads) |
| Battery Support | 3.7 V lithium (LiPo) via JST connector |
| Charging | USB-C (green LED = charging, off = full) |
| IO Access | All GPIO pins exposed on headers |

### Features

- LiPo battery charging via USB-C with charge status LED
- VCC1 and VCC2 regulated outputs for powering external modules or sensors
- Full IO header access — clean wiring for 2 tactile buttons
- Compact form factor suitable for handheld pendant enclosures

### Power Flow

```
USB-C 5V ──→ Charge IC ──→ LiPo 3.7V 500 mAh
                    └──→ LDO 3.3V ──→ ESP32-C3 core
                                  └──→ VCC1 / VCC2 outputs
```

### Wiring for Button Remote

| Header Pin | Connect to |
|-----------|-----------|
| GPIO 4 | Button 0 (ZERO) — other terminal to GND |
| GPIO 5 | Button 1 (SAVE_POINT) — other terminal to GND |
| GND | Common ground (buttons, capacitors) |
| BAT+ / BAT- | LiPo battery JST (verify polarity before connecting) |
