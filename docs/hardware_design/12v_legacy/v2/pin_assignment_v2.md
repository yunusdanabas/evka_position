# Pin Assignment — V2 Hardware

> Complete GPIO map for ESP32-S3-DevKitC-1 on the EVKA Position V2 carrier PCB.  
> Includes migration guide from V1 (ESP32 Wemos D1 R32).

---

## 1. Pin Assignment Table

### 1a. Encoder Inputs

| Axis | Signal | GPIO | DevKitC-1 Header | Notes |
|------|--------|------|------------------|-------|
| Theta | A | **GPIO 4** | J1 Pin 3 | Quadrature channel A |
| Theta | B | **GPIO 5** | J1 Pin 4 | Quadrature channel B |
| Phi | A | **GPIO 6** | J1 Pin 5 | Quadrature channel A |
| Phi | B | **GPIO 7** | J1 Pin 6 | Quadrature channel B |
| Wire | A | **GPIO 15** | J1 Pin 14 | Quadrature channel A |
| Wire | B | **GPIO 16** | J1 Pin 15 | Quadrature channel B |
| Wire | Z | **GPIO 17** | J1 Pin 16 | Index pulse (future use) |

### 1b. Analog Input

| Function | GPIO | DevKitC-1 Header | ADC Channel | Notes |
|----------|------|------------------|-------------|-------|
| Battery/12V monitor | **GPIO 1** | J2 Pin 3 | ADC1_CH0 | Safe with WiFi active |

### 1c. Status LEDs

| LED | Color | GPIO | DevKitC-1 Header | Drive |
|-----|-------|------|------------------|-------|
| Power | Green | Hardwired | — | 5V_RAIL → 1kΩ → LED → GND |
| WiFi | Blue | **GPIO 8** | J1 Pin 7 | Active HIGH |
| Activity | Yellow | **GPIO 9** | J1 Pin 8 | Active HIGH |
| Fault | Red | **GPIO 10** | J1 Pin 9 | Active HIGH |

### 1d. Communication Buses

| Bus | Signal | GPIO | DevKitC-1 Header | Notes |
|-----|--------|------|------------------|-------|
| I2C | SDA | **GPIO 11** | J1 Pin 10 | 4.7kΩ pull-up to 3.3V |
| I2C | SCL | **GPIO 12** | J1 Pin 11 | 4.7kΩ pull-up to 3.3V |
| RS-485 | TX/DI | **GPIO 13** | J1 Pin 12 | UART2 via GPIO matrix |
| RS-485 | RX/RO | **GPIO 14** | J1 Pin 13 | UART2 via GPIO matrix |
| RS-485 | DE/RE | **GPIO 18** | J1 Pin 17 | Direction control |

### 1e. Spare GPIOs

| Pin | GPIO | DevKitC-1 Header | Direction | Use Case |
|-----|------|------------------|-----------|----------|
| Spare 1 | **GPIO 21** | J2 Pin 16 | Bidirectional | Limit switch, relay, auxiliary output |
| Spare 2 | **GPIO 38** | J2 Pin 9 | Input-only | Limit switch, emergency stop |
| Spare 3 | **GPIO 39** | J2 Pin 8 | Input-only | Limit switch, home sensor |
| Spare 4 | **GPIO 40** | J2 Pin 7 | Input-only | Limit switch, external trigger |

> ⚠️ **GPIO 39 (MTCK) and GPIO 40 (MTDO) are default ESP32-S3 JTAG pins.** External signals on these pins disable hardware JTAG debugging (OpenOCD). This is acceptable in production builds. Developers needing JTAG: remap JTAG to GPIO 33/34 or leave GPIO 39/40 unconnected during debug sessions.

### 1f. Special Pins

| Function | Pin | DevKitC-1 Header | Notes |
|----------|-----|------------------|-------|
| Reset | EN | J1 Pin 2 | Driven by MAX813L RESET + button |
| Power LED | GPIO 2 | J2 Pin 4 | Onboard LED + external green LED |
| USB D- | GPIO 19 | J2 Pin 18 | Native USB, do not use for GPIO |
| USB D+ | GPIO 20 | J2 Pin 17 | Native USB, do not use for GPIO |

---

## 2. Visual Pin Map

```
    DevKitC-1 mounted on carrier PCB (top view)
    
    ┌──────────────────────────────────────────────────────────┐
    │  USB-C                                                   │
    │  [====]                                                  │
    │  EN  BOOT                                                │
    │  [O]  [O]                                                │
    │                                                          │
    │  J1 (Left header, facing USB)        J2 (Right header)   │
    │  ┌─────────────────────┐            ┌─────────────────┐  │
    │  │ 3V3  EN   4   5   6 │            │ 3V3   3   1   2 │  │
    │  │  7   8   9  10  11  │            │ 41  40  39  38  │  │
    │  │ 12  13  14  15  16  │            │ 37  36  35  34  │  │
    │  │ 17  18  5V  GND GND │            │ 33  26  21  20  │  │
    │  └─────────────────────┘            │ 19  5V  GND     │  │
    │                                     └─────────────────┘  │
    │                                                          │
    │  Carrier PCB wiring:                                     │
    │  • 4,5,6,7     → J1 (Theta/Phi dividers)                 │
    │  • 15,16,17    → J3 (Wire divider)                       │
    │  • 8,9,10      → LEDs (Blue, Yellow, Red)                │
    │  • 11,12       → J_I2C (SDA, SCL) + pull-ups             │
    │  • 13,14,18    → MAX485 (TX, RX, DE)                     │
    │  • 1           → 120k/27k divider (Battery ADC)          │
    │  • 2           → LED Power (Green)                       │
    │  • 21,38,39,40 → J_GPIO spare header                     │
    │  • EN          → MAX813L RESET output                    │
    │  • 5V,GND      → Power rails                             │
    └──────────────────────────────────────────────────────────┘
```

---

## 3. Migration from V1

### 3a. Pin Changes Summary

| Function | V1 GPIO | V2 GPIO | Change Reason |
|----------|---------|---------|---------------|
| Theta A | 14 | **4** | S3: GPIO 14 available but 4 is cleaner for routing |
| Theta B | 12 | **5** | S3: GPIO 12 no longer strapping, but 5 is adjacent to 4 |
| Phi A | 32 | **6** | S3: GPIO 32 reserved for PSRAM |
| Phi B | 35 | **7** | S3: GPIO 35 reserved for PSRAM |
| Wire A | 16 | **15** | S3: GPIO 16 available, but 15/16/17 cluster is cleaner |
| Wire B | 17 | **16** | S3: GPIO 17 available |
| Wire Z | 18 | **17** | S3: GPIO 18 available |
| Battery ADC | 36 | **1** | S3: GPIO 36 reserved for PSRAM; GPIO 1 is ADC1_CH0 |
| LED Battery | 25 | **10** | S3: GPIO 25 available, but 8/9/10 cluster for LEDs |
| LED WiFi | 2 | **8** | Dedicated cluster |

### 3b. What Stayed the Same

| Aspect | Status |
|--------|--------|
| Encoder library | **Recommended: `ESP32Encoder` (PCNT-based, madhephaestus/ESP32Encoder).** `PaulStoffregen/Encoder` still works but needs IRAM_ATTR fixes on ESP32-S3. |
| Quadrature decoding | Same X4 counting |
| PPR values | Same `PPR_ROTARY = 20000`, `PPR_WIRE = 8000` |
| Signal conditioning | Same 10k/20k/1nF dividers, 1.5KE3.3CA TVS |
| Connector pinouts | Same KF301-4P/5P wiring |

### 3c. Firmware Migration Checklist

```cpp
// Step 1: Update platformio.ini
[env:esp32-s3-devkitc-1]
platform = espressif32@6.12.0
board = esp32-s3-devkitc-1
framework = arduino

// Step 2: Update pin definitions in SphericalSensor.h
// OLD (V1):
#define PIN_THETA_A   14
#define PIN_THETA_B   12
#define PIN_PHI_A     32
#define PIN_PHI_B     35
#define PIN_WIRE_A    16
#define PIN_WIRE_B    17
#define PIN_WIRE_Z    18
#define PIN_BATT_ADC  36
#define PIN_LED_WIFI  2

// NEW (V2):
#define PIN_THETA_A   4
#define PIN_THETA_B   5
#define PIN_PHI_A     6
#define PIN_PHI_B     7
#define PIN_WIRE_A    15
#define PIN_WIRE_B    16
#define PIN_WIRE_Z    17
#define PIN_BATT_ADC  1
#define PIN_LED_WIFI  8
#define PIN_LED_ACTIVITY 9
#define PIN_LED_FAULT 10

// Step 3: Add new features (optional)
#define PIN_RS485_TX  13
#define PIN_RS485_RX  14
#define PIN_RS485_DE  18
#define PIN_I2C_SDA   11
#define PIN_I2C_SCL   12
#define PIN_WDI       9
```

---

## 4. Strapping Pins Warning

**DO NOT USE these GPIOs for active signals:**

| GPIO | Function | Risk |
|------|----------|------|
| 0 | Boot mode | Pulled low → enters download mode instead of running firmware |
| 3 | JTAG source | Internal strapping, avoid external drive |
| 45 | VDD_SPI voltage | Internal, not brought out on DevKitC-1 |
| 46 | ROM log print | Internal, not brought out on DevKitC-1 |

**In this design:**
- GPIO 0 is **not connected** on the carrier PCB
- GPIO 3, 45, 46 are **not accessible** from DevKitC-1 headers
- **Safe to ignore** for V2

---

## 5. Reserved Pins

These pins are used by the ESP32-S3 module internally. **Do not connect external signals:**

| GPIO | Internal Use | Accessible on DevKitC-1? |
|------|-------------|--------------------------|
| 19 | USB D- | Yes — but used for USB-C |
| 20 | USB D+ | Yes — but used for USB-C |
| 26–37 | SPI flash / PSRAM | Some brought out — avoid using |

**In this design:**
- GPIO 19/20 are left unconnected on carrier (USB handled by DevKitC-1)
- GPIO 26–37 are **not routed** on carrier PCB

---

## 6. ADC Channels Reference

| ADC1 Channel | GPIO | Used In V2? | Notes |
|--------------|------|-------------|-------|
| CH0 | GPIO 1 | **Yes** | Battery/12V monitor |
| CH1 | GPIO 2 | No | LED Power — can use for ADC if needed |
| CH2 | GPIO 3 | No | Strapping pin — avoid |
| CH3 | GPIO 4 | No | Theta A — encoder, not analog |
| CH4 | GPIO 5 | No | Theta B — encoder, not analog |
| CH5 | GPIO 6 | No | Phi A — encoder |
| CH6 | GPIO 7 | No | Phi B — encoder |
| CH7 | GPIO 8 | No | LED WiFi |
| CH8 | GPIO 9 | No | LED Activity / WDI |
| CH9 | GPIO 10 | No | LED Fault |
| CH0 (ADC2) | — | — | ADC2 unavailable when WiFi active — do not use |

**Key rule:** Always use **ADC1** channels for analog inputs when WiFi is active. ADC2 is disabled during WiFi transmission.

---

## 7. Interrupt-Capable Pins

All GPIOs on ESP32-S3 support `attachInterrupt()`. **No restrictions** for encoder pins.

| Encoder | GPIO | Interrupt | Verified |
|---------|------|-----------|----------|
| Theta A | 4 | Yes | ✓ |
| Theta B | 5 | Yes | ✓ |
| Phi A | 6 | Yes | ✓ |
| Phi B | 7 | Yes | ✓ |
| Wire A | 15 | Yes | ✓ |
| Wire B | 16 | Yes | ✓ |
| Wire Z | 17 | Yes | ✓ |

---

## 8. Pin Conflict Matrix

```
    If adding optional modules, check for conflicts:
    
    I2C modules (J_I2C):
    ├── DS3231 RTC     @ 0x68  ✓ No conflict
    ├── ADS1115 ADC    @ 0x48  ✓ No conflict
    ├── SSD1306 OLED   @ 0x3C  ✓ No conflict
    └── PCF8574 GPIO   @ 0x20  ✓ No conflict (if not using SSD1306 @ 0x3C)
    
    SPI modules (not on V2 by default):
    └── None planned — all expansion is I2C or UART
    
    UART:
    ├── RS-485         @ UART2 (GPIO 13/14)  ✓ No conflict
    └── Serial monitor @ USB CDC (GPIO 19/20) ✓ No conflict
```

---

## 9. Test & Validation

After assembling V2 board and flashing firmware:

| Test | Command/Action | Expected Result |
|------|---------------|-----------------|
| GPIO 4/5 toggle | Rotate Theta encoder | Counts change in serial monitor |
| GPIO 6/7 toggle | Rotate Phi encoder | Counts change |
| GPIO 15/16 toggle | Pull wire | Counts change |
| GPIO 1 ADC | Read with `analogRead(1)` | Value changes with 12V input |
| GPIO 8 output | `digitalWrite(8, HIGH)` | Blue LED lights |
| GPIO 9 output | `digitalWrite(9, HIGH)` | Yellow LED lights |
| GPIO 10 output | `digitalWrite(10, HIGH)` | Red LED lights |
| GPIO 11/12 I2C | `Wire.begin(11,12); Wire.scan()` | Detects DS3231 @ 0x68 |
| GPIO 13/14/18 RS-485 | Send Modbus query | Response received |
| GPIO 21/38/39/40 | `pinMode(pin, INPUT_PULLUP)` | Read HIGH when open |
| EN reset | Press reset button | ESP32 reboots |
| MAX813L watchdog | Stop firmware toggle of GPIO 9 | ESP32 resets after 1.6s |

---

## 10. Related Documents

- [MCU Subsystem](subsystems/mcu_subsystem_v2.md) — DevKitC-1 mounting, power, reset
- [Encoder Interface](subsystems/encoder_interface_v2.md) — Divider networks, connector pinouts
- [Expansion Interfaces](subsystems/expansion_interfaces_v2.md) — RS-485, I2C, watchdog, LEDs
- [Firmware Header](firmware/pin_assignment_v2.h) — Copy-paste C definitions
