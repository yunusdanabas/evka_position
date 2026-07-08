# Pin Assignment - Final EVKA Position Hardware

This is the final ESP32-S3 pin map for the core-only 12V hardware.

The active repository firmware still targets Wemos D1 R32 until migrated. Do not flash the current Wemos firmware to this board without updating the pin map and board environment.

## 1. Final Pin Table

| Function | GPIO | Direction | Hardware Connection | Notes |
|---|---:|---|---|---|
| Supply ADC | 1 | Input | `BUCK_VIN` through 120k/27k divider | ADC1_CH0, WiFi-safe |
| Theta A | 4 | Input | J_THETA pin 3 through divider | Quadrature A |
| Theta B | 5 | Input | J_THETA pin 4 through divider | Quadrature B |
| Phi A | 6 | Input | J_PHI pin 3 through divider | Quadrature A |
| Phi B | 7 | Input | J_PHI pin 4 through divider | Quadrature B |
| WiFi LED | 8 | Output | Optional LED + 1k to GND | Active high |
| Wire A | 15 | Input | J_WIRE pin 3 through divider | Quadrature A |
| Wire B | 16 | Input | J_WIRE pin 4 through divider | Quadrature B |
| Wire Z | 17 | Input | J_WIRE pin 5 through divider | Optional index pulse |

## 2. Connector Pinout

### J_THETA

| Pin | Signal | Destination |
|---:|---|---|
| 1 | +5V | `5V_RAIL` through FB1 |
| 2 | GND | Board GND |
| 3 | A | GPIO 4 through divider/filter/TVS |
| 4 | B | GPIO 5 through divider/filter/TVS |

### J_PHI

| Pin | Signal | Destination |
|---:|---|---|
| 1 | +5V | `5V_RAIL` through FB2 |
| 2 | GND | Board GND |
| 3 | A | GPIO 6 through divider/filter/TVS |
| 4 | B | GPIO 7 through divider/filter/TVS |

### J_WIRE

| Pin | Signal | Destination |
|---:|---|---|
| 1 | +5V | `5V_RAIL` through FB3 |
| 2 | GND | Board GND |
| 3 | A | GPIO 15 through divider/filter/TVS |
| 4 | B | GPIO 16 through divider/filter/TVS |
| 5 | Z | GPIO 17 through divider/filter/TVS |

## 3. Pins Intentionally Not Used

| GPIO | Reason |
|---:|---|
| 0 | Boot strapping pin |
| 3 | Strapping / JTAG-related risk |
| 9 | Reserved for future activity LED or watchdog daughterboard |
| 10 | Reserved for future fault LED or daughterboard |
| 11 / 12 | Reserved for future I2C daughterboard, not routed by default |
| 13 / 14 / 18 | Reserved for future RS-485 daughterboard, not routed by default |
| 19 / 20 | Native USB D- / D+ |
| 21 | Reserved future expansion, not routed by default |
| 26-37 | Flash / PSRAM risk area on many ESP32-S3 modules |
| 38 / 39 / 40 | Reserved future expansion, not routed by default |
| 45 / 46 | Strapping / internal-use risk |

## 4. Firmware Migration Notes

The current Wemos firmware uses these old pins:

| Function | Current Wemos GPIO | Final ESP32-S3 GPIO |
|---|---:|---:|
| Theta A | 14 | 4 |
| Theta B | 12 | 5 |
| Phi A | 32 | 6 |
| Phi B | 35 | 7 |
| Wire A | 16 | 15 |
| Wire B | 17 | 16 |
| Wire Z | 18 | 17 |
| Battery / supply ADC | 36 | 1 |
| WiFi LED | 2 | 8 |

Required code changes:

1. Add an `esp32-s3-devkitc-1` PlatformIO environment.
2. Update pin definitions using [`firmware/pin_assignment_final.h`](firmware/pin_assignment_final.h).
3. Use ADC1 on GPIO1 for supply voltage.
4. Prefer ESP32-S3 PCNT-based quadrature counting.
5. Verify all web/TCP/serial commands on real ESP32-S3 hardware.

## 5. ADC Scaling

The final board measures `BUCK_VIN` through a 120k/27k divider.

```text
scale = (120k + 27k) / 27k = 5.444444
V_input = V_adc * 5.444444
```

Recommended firmware thresholds:

| Threshold | Voltage | Meaning |
|---|---:|---|
| Full 3S reference | 12.60V | Fully charged battery |
| Low warning | 10.50V | Alert operator |
| Graceful shutdown | 9.90V | Stop operation before BMS cutoff |
| Absolute minimum | 9.00V | Do not intentionally operate here |

When the adapter is present, `BUCK_VIN` reports adapter voltage after `D_ADAPT`. When the adapter is absent, it reports battery voltage after Q_BATT.
