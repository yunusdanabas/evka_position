# Pin Assignment — EVKA Position V3

> Core-only ESP32-S3-DevKitC-1 pin map for the V3 12V hardware.  
> This is a hardware design target. The active firmware still targets Wemos D1 R32 until migrated.

---

## 1. Core Pin Table

| Function | GPIO | Direction | Notes |
|---|---:|---|---|
| Battery / supply ADC | 1 | Input | ADC1_CH0, divider from `BUCK_VIN` (monitors actual supply voltage — adapter or battery) |
| Theta A | 4 | Input | Quadrature A |
| Theta B | 5 | Input | Quadrature B |
| Phi A | 6 | Input | Quadrature A |
| Phi B | 7 | Input | Quadrature B |
| WiFi LED | 8 | Output | Optional external LED |
| Wire A | 15 | Input | Quadrature A |
| Wire B | 16 | Input | Quadrature B |
| Wire Z | 17 | Input | Optional index pulse |

---

## 2. Minimal LED Policy

| LED | GPIO | V3 Status | Notes |
|---|---:|---|---|
| Power | Hardwired | Required | `5V_RAIL -> 1k -> LED -> GND` |
| WiFi | 8 | Optional but recommended | Shows AP/STA status if firmware supports it |
| Activity | 9 | Removed by default | Available for future firmware if needed |
| Fault | 10 | Removed by default | Available for future firmware if needed |

GPIO 9 and GPIO 10 are not routed by default unless the board layout keeps optional LED footprints.

---

## 3. Removed V2 Interfaces

These V2 assignments are intentionally not part of the V3 default PCB:

| V2 Function | GPIOs | V3 Default |
|---|---|---|
| I2C SDA/SCL | 11 / 12 | Not routed |
| RS-485 TX/RX/DE | 13 / 14 / 18 | Not routed |
| External watchdog WDI | 9 | Not routed |
| Spare GPIO header | 21 / 38 / 39 / 40 | Not routed |

If an expansion board is needed later, these pins are still useful candidates.

---

## 4. Pins To Avoid

| GPIO | Reason |
|---:|---|
| 0 | Boot mode strapping pin |
| 3 | ESP32-S3 strapping / JTAG related pin |
| 19 / 20 | Native USB D- / D+ on DevKitC |
| 26-37 | Flash / PSRAM related on many modules; avoid for portable carrier design |
| 45 / 46 | Strapping / internal use, not suitable for general external signals |

---

## 5. Firmware Migration Notes

Active firmware currently uses the Wemos D1 R32 pin map. V3 firmware migration should:

1. Add a PlatformIO environment for `esp32-s3-devkitc-1`.
2. Use the pin definitions in [`firmware/pin_assignment_v3.h`](firmware/pin_assignment_v3.h).
3. Prefer `ESP32Encoder` for hardware PCNT quadrature counting on ESP32-S3.
4. Move battery ADC from GPIO36 to GPIO1.
5. Re-test WiFi, TCP dashboard, all three encoders, and battery monitor on real V3 hardware.

Do not flash existing Wemos firmware to this board without pin migration.
