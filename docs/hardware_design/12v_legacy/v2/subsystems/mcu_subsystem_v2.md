# MCU Subsystem — V2 Design

> ESP32-S3-DevKitC-1 module on female headers.  
> USB-C programming, native USB-OTG, 45 GPIOs, dual-core 240MHz.  
> Designed for 100% through-hole LPKF S63 fabrication.

---

## 1. Why ESP32-S3?

| Feature | ESP32-WROOM-32 (V1) | ESP32-S3-WROOM-1 (V2) | Impact |
|---|---|---|---|
| CPU | Xtensa LX6 @ 240MHz | **Xtensa LX7 @ 240MHz** | Better IPC, vector instructions |
| USB | External CH340/CP2102 | **Native USB-OTG** | No driver issues, direct CDC |
| Security | Secure Boot V1 | **Secure Boot V2, HMAC, Digital Signature** | Industrial IP protection |
| Bluetooth | BT 4.2 Classic + BLE | **BLE 5.0 only** | ESP-NOW still works (WiFi MAC layer) |
| GPIO | 34 | **45** | More flexibility |
| ADC | 2×12-bit, 18 ch | 2×12-bit, **20 ch** | More analog inputs |
| WiFi | 802.11 b/g/n | **802.11 b/g/n** (same) | No change |
| PCNT | 8 units | **4 units** | Still sufficient (we use interrupt lib) |

**Bottom line:** Same WiFi performance, better USB/debug experience, more GPIOs, future-proof security. No performance bottleneck for our 20Hz control loop.

---

## 2. DevKitC-1 on Headers

### 2a. Physical Mounting

```
    ┌──────────────────────────────────────────────┐
    │                                              │
    │      ESP32-S3-DevKitC-1                      │
    │      ┌────────────────────────────┐          │
    │      │  USB-C    EN  BOOT  GPIOs  │          │
    │      │   [==]   [O]  [O]  [======]│          │
    │      │                            │          │
    │      │    WROOM-1 module          │          │
    │      │    ┌──────────────┐        │          │
    │      │    │  Antenna     │        │          │
    │      │    └──────────────┘        │          │
    │      └────────────────────────────┘          │
    │                                              │
    │  Female headers (2× 20-pin, 2.54mm)          │
    │  └────────────────────────────────────┘      │
    │         Carrier PCB (this design)             │
    └──────────────────────────────────────────────┘
```

**Mounting:**
- 2× 20-pin female headers, 2.54mm pitch, on carrier PCB
- DevKitC-1 plugs in like a DIP package
- Total height: ~25mm (DevKitC-1) + 8mm (headers) = 33mm
- Keep clearance above module for airflow

**Advantages over direct WROOM-1 module:**
- No need to solder the SMD WROOM-1 module itself
- USB-C connector already on board — no separate USB connector on carrier
- Boot/EN buttons accessible
- Can swap DevKitC-1 in seconds for debugging

---

## 3. Pin Map

### 3a. DevKitC-1 Header Pinout

The DevKitC-1 brings out most GPIOs on two 20-pin headers. Below is the **functional assignment** for this design (not the physical DevKitC-1 pin numbering).

```
Left Header (J1) — 20 pins, facing USB connector
┌────────────────────────────────────────────────────────┐
│ Pin │ GPIO │ Function        │ Direction │ Notes      │
├─────┼──────┼─────────────────┼───────────┼────────────┤
│  1  │ 3V3  │ 3.3V output     │ —         │ From LDO   │
│  2  │ EN   │ Reset           │ Input     │ From MAX813│
│  3  │ 4    │ Theta A         │ Input     │ Quadrature │
│  4  │ 5    │ Theta B         │ Input     │ Quadrature │
│  5  │ 6    │ Phi A           │ Input     │ Quadrature │
│  6  │ 7    │ Phi B           │ Input     │ Quadrature │
│  7  │ 8    │ LED WiFi        │ Output    │ Blue LED   │
│  8  │ 9    │ LED Activity    │ Output    │ Yellow LED │
│  9  │ 10   │ LED Fault       │ Output    │ Red LED    │
│ 10  │ 11   │ I2C SDA         │ Bidir     │ 4.7kΩ PU   │
│ 11  │ 12   │ I2C SCL         │ Bidir (open-drain) │ 4.7kΩ PU   │
│ 12  │ 13   │ RS-485 TX       │ Output    │ UART       │
│ 13  │ 14   │ RS-485 RX       │ Input     │ UART       │
│ 14  │ 15   │ Wire A          │ Input     │ Quadrature │
│ 15  │ 16   │ Wire B          │ Input     │ Quadrature │
│ 16  │ 17   │ Wire Z          │ Input     │ Index      │
│ 17  │ 18   │ RS-485 DE/RE    │ Output    │ Direction  │
│ 18  │ 5V   │ 5V input        │ —         │ VIN rail   │
│ 19  │ GND  │ Ground          │ —         │ Common     │
│ 20  │ GND  │ Ground          │ —         │ Common     │
└────────────────────────────────────────────────────────┘

Right Header (J2) — 20 pins
┌────────────────────────────────────────────────────────┐
│ Pin │ GPIO │ Function        │ Direction │ Notes      │
├─────┼──────┼─────────────────┼───────────┼────────────┤
│  1  │ 3V3  │ 3.3V output     │ —         │ From LDO   │
│  2  │ 3    │ —               │ —         │ Strapping  │
│  3  │ 1    │ Battery ADC     │ Input     │ ADC1_CH0   │
│  4  │ 2    │ LED Power       │ Output    │ Onboard+ext│
│  5  │ 42   │ —               │ —         │ Reserved   │
│  6  │ 41   │ —               │ —         │ Reserved   │
│  7  │ 40   │ Spare GPIO 4    │ Input     │ J_GPIO pin │
│  8  │ 39   │ Spare GPIO 3    │ Input     │ J_GPIO pin │
│  9  │ 38   │ Spare GPIO 2    │ Input     │ J_GPIO pin │
│ 10  │ 37   │ —               │ —         │ Reserved   │
│ 11  │ 36   │ —               │ —         │ Reserved   │
│ 12  │ 35   │ —               │ —         │ Reserved   │
│ 13  │ 34   │ —               │ —         │ Reserved   │
│ 14  │ 33   │ —               │ —         │ Reserved   │
│ 15  │ 26   │ —               │ —         │ Reserved   │
│ 16  │ 21   │ Spare GPIO 1    │ Bidir     │ J_GPIO pin │
│ 17  │ 20   │ —               │ —         │ USB D+     │
│ 18  │ 19   │ —               │ —         │ USB D-     │
│ 19  │ 5V   │ 5V input        │ —         │ VIN rail   │
│ 20  │ GND  │ Ground          │ —         │ Common     │
└────────────────────────────────────────────────────────┘
```

**Note:** DevKitC-1 physical pin numbering differs from GPIO numbers. Always verify against the Espressif pinout diagram. The table above is organized by **function**, not physical position.

### 3b. Pin Selection Rationale

**Why GPIO 4/5/6/7 for encoders?**
- All support GPIO interrupts (required for `Encoder` library)
- None are strapping pins (0, 3, 45, 46)
- None conflict with USB (19, 20) or SPI flash (26–37)
- Spread across both sides for routing convenience

**Why GPIO 1 for ADC?**
- ADC1_CH0 — safe when WiFi is active
- On classic ESP32, GPIO 36 was used (ADC1_CH0 but reserved on S3)
- GPIO 1 is input-only on some packages, but ADC input is fine

**Why GPIO 13/14 for RS-485 UART?**
- On ESP32-S3, any GPIO can be mapped to any peripheral via the GPIO matrix
- UART2 can use GPIO 13 (TX) and GPIO 14 (RX) without conflict
- DevKitC-1 brings these out on accessible header pins

**Why GPIO 11/12 for I2C?**
- Native I2C pins (SDA/SCL) on ESP32-S3
- Both are safe, non-strapping, non-reserved

---

## 4. Strapping Pins — Critical Warning

ESP32-S3 has **4 strapping pins** that determine boot mode. These must have correct pull-up/down at reset:

| GPIO | Function | Requirement |
|------|----------|-------------|
| 0 | Boot mode | Pull-up for normal boot, pull-down for download |
| 3 | JTAG source | Internal, don't drive externally at boot |
| 45 | VDD_SPI voltage | Internal, don't connect |
| 46 | ROM log print | Internal, don't connect |

**In this design:**
- GPIO 0 is **not used** — leave unconnected or weak pull-up
- GPIO 3, 45, 46 are **not on the carrier PCB** (not brought out from DevKitC-1 headers)
- **Safe to ignore** for this design

**Important:** Do NOT connect encoders or any active signal to GPIO 0. If GPIO 0 is pulled low at boot, ESP32 enters download mode instead of running firmware.

---

## 5. USB-C on DevKitC-1

The DevKitC-1 board has a **USB-C connector** with native USB-OTG support:

```
    USB-C Cable
        │
    ┌───┴───┐
    │  D-   │ ──── GPIO 19
    │  D+   │ ──── GPIO 20
    │  VBUS │ ──── 5V (not used on carrier)
    │  GND  │ ──── GND
    └───────┘
```

**Usage modes:**
1. **Programming:** USB-C → PC, appears as `/dev/ttyACM0` (Linux) or COM port (Windows)
2. **Serial monitor:** Same port, no extra drivers needed on modern OS
3. **Native USB device:** Can act as USB HID, MSC, etc. (not used in this design)

**PlatformIO upload:**
```ini
[env:esp32-s3-devkitc-1]
platform = espressif32@6.12.0
board = esp32-s3-devkitc-1
framework = arduino
upload_port = /dev/ttyACM0  ; Linux
; upload_port = COM3        ; Windows
```

---

## 6. Reset Circuit

```
    MAX813L RESET output ────┬───┬─── ESP32 EN pin
                             │   │
                             │   └── 10kΩ pull-up to 3.3V
                             │
                             └─── Reset Button ──── GND
```

**Operation:**
- **Power-on reset:** MAX813L holds RESET low until 5V stabilizes (~200ms), then releases
- **Watchdog timeout:** If firmware doesn't toggle WDI within 1.6s, MAX813L pulses RESET
- **Manual reset:** Press button → EN pin pulled low → ESP32 reboots

**Why external MAX813L instead of just a button?**
- Catches firmware hangs that ESP32 internal WDT misses
- Brownout protection (reset if 5V sags below 4.65V)
- More reliable than RC reset circuit

---

## 7. 3.3V Rail

The ESP32-S3-DevKitC-1 has an **onboard AMS1117-3.3** LDO:

```
    5V_RAIL ──── DevKitC-1 VIN ──── AMS1117 ──── 3.3V rail
                                         │
                                    onboard caps
                                         │
                                    ESP32 VDD, flash, PSRAM
```

**Specifications:**
- Input: 5V_RAIL (4.75–5.0V)
- Output: 3.3V ±2%
- Current: up to 1A (ESP32 peak ~350mA)
- Dropout: ~1.0V @ 500mA (needs 4.3V minimum input)

**No external 3.3V regulator needed** — the DevKitC-1 handles this.

**External 3.3V usage:**
- I2C pull-ups: 4.7kΩ to 3.3V (from DevKitC-1 3V3 pin)
- RS-485 transceiver VCC: **5V_RAIL** (4.75–4.85V). MAX485EPA+ minimum VCC is 4.75V — do not supply 3.3V. If 3.3V-only operation is needed in future, replace MAX485EPA+ with MAX3485 or SP3485EN.
- ADS1115 VCC: 3.3V (module accepts 2.0–5.5V)

---

## 8. Power Consumption Budget

| Component | Typical | Peak | Notes |
|-----------|---------|------|-------|
| ESP32-S3 (WiFi AP+STA) | 120mA @ 3.3V | 200mA | Dominant consumer |
| 2× E40S6 encoders | 100mA @ 5V | 120mA | |
| DWEM2 encoder | 40mA @ 5V | 100mA | |
| MAX485 | 5mA @ 5V | 10mA | |
| LEDs (4×) | 10mA total | 15mA | 1kΩ resistors |
| I2C pull-ups | 1mA | 2mA | 4.7kΩ × 2 |
| **Total @ 5V** | **~400mA** | **~600mA** | |
| **Total @ 12V** (incl. buck loss) | **~450mA** | **~650mA** | |

**Buck requirement:** MP1584EN rated 3A — plenty of headroom.

---

## 9. Migration from V1 (ESP32 Wemos D1 R32)

### 9a. Pin Changes

| Function | V1 (Wemos D1 R32) | V2 (DevKitC-1) | Action |
|----------|-------------------|----------------|--------|
| Theta A | GPIO 14 | **GPIO 4** | Move wire |
| Theta B | GPIO 12 | **GPIO 5** | Move wire |
| Phi A | GPIO 32 | **GPIO 6** | Move wire |
| Phi B | GPIO 35 | **GPIO 7** | Move wire |
| Wire A | GPIO 16 | **GPIO 15** | Move wire |
| Wire B | GPIO 17 | **GPIO 16** | Move wire |
| Wire Z | GPIO 18 | **GPIO 17** | Move wire |
| Battery ADC | GPIO 36 | **GPIO 1** | Move wire |
| LED Power | GPIO 2 | **GPIO 2** | No change |
| LED Battery Low | GPIO 25 | **GPIO 10** | Move wire |

### 9b. Firmware Changes

```cpp
// Old (V1)
#define PIN_THETA_A   14
#define PIN_THETA_B   12
#define PIN_PHI_A     32
#define PIN_PHI_B     35
#define PIN_WIRE_A    16
#define PIN_WIRE_B    17
#define PIN_WIRE_Z    18
#define PIN_BATT_ADC  36

// New (V2)
#define PIN_THETA_A   4
#define PIN_THETA_B   5
#define PIN_PHI_A     6
#define PIN_PHI_B     7
#define PIN_WIRE_A    15
#define PIN_WIRE_B    16
#define PIN_WIRE_Z    17
#define PIN_BATT_ADC  1
```

### 9c. PlatformIO Changes

```ini
; Old
[env:wemos_d1_r32]
board = wemos_d1_r32

; New
[env:esp32-s3-devkitc-1]
board = esp32-s3-devkitc-1
```

### 9d. USB Port Changes

| Aspect | V1 (CH340) | V2 (Native USB) |
|---|---|---|
| Linux device | `/dev/ttyUSB0` | `/dev/ttyACM0` |
| Windows driver | CH340 driver required | Built-in CDC driver |
| Upload speed | 921600 baud | Auto-negotiated |

Update any scripts or documentation that reference `/dev/ttyUSB0`.

---

## 10. DevKitC-1 Header Wiring Diagram

```
    Carrier PCB (top view, looking down at headers)
    
    ┌─────────────────────────────────────────────────────────┐
    │  J1 (Left header, 20-pin)    J2 (Right header, 20-pin) │
    │  ┌─────────────────────┐    ┌─────────────────────┐     │
    │  │ 3V3  EN   4   5   6 │    │ 3V3   3   1   2  42 │     │
    │  │  7   8   9  10  11  │    │ 41  40  39  38  37 │     │
    │  │ 12  13  14  15  16  │    │ 36  35  34  33  26 │     │
    │  │ 17  18  5V  GND GND │    │ 21  20  19  5V  GND│     │
    │  └─────────────────────┘    └─────────────────────┘     │
    │                                                         │
    │  Signal routing on carrier PCB:                         │
    │  • GPIO 4/5/6/7  → encoder dividers (J1, J2)            │
    │  • GPIO 15/16/17 → wire encoder dividers (J3)           │
    │  • GPIO 8/9/10   → LED current-limit resistors          │
    │  • GPIO 11/12    → I2C pull-ups + TVS + J_I2C header    │
    │  • GPIO 13/14/18 → MAX485 transceiver                   │
    │  • GPIO 1        → 120k/27k divider                     │
    │  • GPIO 21/38/39/40 → J_GPIO spare header               │
    │  • 5V/GND        → power rail                           │
    │  • EN            → MAX813L RESET output                 │
    └─────────────────────────────────────────────────────────┘
```

---

## 11. Test Points (MCU Section)

| TP | Signal | Location | Expected |
|----|--------|----------|----------|
| TP_EN | ESP32 EN | Near reset button | 3.3V (high = running) |
| TP_3V3 | 3.3V rail | DevKitC-1 3V3 pin | 3.25–3.35V |
| TP_BOOT | GPIO 0 | DevKitC-1 header | 3.3V (pulled up) |
| TP_USB_D | USB data | DevKitC-1 USB-C | Differential pair |

---

## 12. Assembly Notes

1. **Solder female headers first** — they're the tallest components, establish reference plane
2. **Do NOT solder DevKitC-1 yet** — test all voltages first
3. **Verify 5V_RAIL** at header pin before plugging in DevKitC-1
4. **Check 3.3V** on DevKitC-1 3V3 pin after insertion
5. **Press RESET button** — ESP32 should boot, onboard LED blink once
6. **Connect USB-C** — should enumerate as `/dev/ttyACM0` (Linux) or COM port (Windows)
