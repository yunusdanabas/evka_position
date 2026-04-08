# Bill of Materials — Wireless Button Remote

ESP-NOW button pendant for the EvkaPosition positioning system.

## Core Components

| # | Component | Specification | Qty | Est. Price | Notes |
|---|-----------|--------------|-----|-----------|-------|
| 1 | ESP32-C3 SuperMini + Expansion Board | ESP32-C3, RISC-V 160 MHz, WiFi + BLE 5.0, USB-C, expansion board with GPIO headers | 1 | $3-6 | **Recommended** — expansion board makes button wiring easy |
| 2 | LiPo Battery | 3.7V 500 mAh, JST-PH 2.0 connector | 1 | $3-5 | Minimum 500 mAh (XIAO charge rate is 370 mA) |
| 3 | Tactile Switch (12 mm, tall cap) | 12x12x7.3 mm, 160-260 gF, through-hole | 5 | $1-2 | Tall caps for gloved-hand use |
| 4 | Switch Caps (colored) | 12 mm round caps: Green, Red, Blue, Yellow, White | 5 | $1 | Color-coded per button function |
| 5 | Capacitor 100 nF | Ceramic, 0805 or through-hole | 5 | $0.50 | Hardware debounce — one per button (GPIO to GND) |

## Optional Components

| # | Component | Specification | Qty | Est. Price | Notes |
|---|-----------|--------------|-----|-----------|-------|
| 6 | Slide Switch | SS12D00, SPDT, 2-pos | 1 | $0.20 | Power on/off (cuts battery to MCU) |
| 7 | LED (3 mm, green) | 3 mm diffused, 20 mA | 1 | $0.10 | Send confirmation feedback |
| 8 | Resistor 330R | 1/4W, for LED current limit | 1 | $0.05 | (3.3V - 2.0V) / 330 = ~4 mA |
| 9 | U.FL Antenna (2.4 GHz) | 2.4 GHz PCB or whip, U.FL connector | 1 | $1-2 | XIAO has U.FL pad — improves range |
| 10 | Enclosure | 3D printed or Hammond 1551KTBU (80x40x20 mm) | 1 | $1-5 | Handheld pendant form factor |

## Alternative MCU Options

| Board | Price | LiPo Charging | GPIO | Deep Sleep | Notes |
|-------|-------|--------------|------|-----------|-------|
| **Seeed XIAO ESP32-C3** | $5-9 | **Yes (built-in)** | 11 | ~44 uA | **Recommended** — smallest with charging |
| ESP32-C3 SuperMini | $3-4 | No | ~13 | ~43 uA | Cheapest — add TP4056 module ($0.50) |
| Waveshare ESP32-C3-Zero | $4-6 | No | 15 | ~43 uA | Most GPIO, no charging |
| LilyGO T-Display-S3 | $16-23 | Yes | Many | ~7 uA | Overkill — but has 1.9" TFT display |

## Total Cost Estimate

| Configuration | Cost |
|--------------|------|
| Minimal (XIAO + battery + 5 buttons) | **~$10-15** |
| Full (+ antenna, LED, switch, enclosure) | **~$15-25** |
| Budget (SuperMini + TP4056 + battery + buttons) | **~$8-12** |

## Supplier Notes

- XIAO ESP32-C3: Seeed Studio direct, Mouser, DigiKey, Amazon
- ESP32-C3 SuperMini: AliExpress (verify chip marking includes "FN4" — avoid boards with blurred labels)
- Tactile switches + colored caps: AliExpress (search "12mm tactile switch cap assorted")
- LiPo 500 mAh: AliExpress, Amazon (ensure JST-PH 2.0 connector matches XIAO pads)
