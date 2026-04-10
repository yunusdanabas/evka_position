# Bill of Materials — Wireless Button Remote

ESP-NOW 2-button pendant for the EvkaPosition positioning system.

## Core Components

| # | Component | Specification | Qty | Est. Price | Notes |
|---|-----------|--------------|-----|-----------|-------|
| 1 | ESP32-C3 Mini / SuperMini | ESP32C3FN4, RISC-V 160 MHz, WiFi + BLE 5.0, USB-C, 4 MB flash, 18×23 mm | 1 | $2-4 | Generic clone from AliExpress — verify chip marking "C3FN4" |
| 2 | ESP32 C3 SuperMini Expansion Board | 3.7 V LiPo charging, USB-C, VCC1/VCC2 3.3 V, full IO headers, 37.4×22.5 mm | 1 | $2-4 | Pairs with SuperMini; provides battery charging + clean wiring |
| 3 | LiPo Battery | 3.7 V 500 mAh, JST connector matching expansion board | 1 | $2-4 | 500 mAh gives ~14 months battery life |
| 4 | Tactile Switch (12 mm, tall cap) | 12×12×7.3 mm, 160–260 gF, through-hole | 2 | $0.50 | Tall caps for gloved-hand use |
| 5 | Switch Caps (colored) | 12 mm round caps: Red (ZERO), Green (SAVE_POINT) | 2 | $0.50 | Color-coded per function |

## Optional Components

| # | Component | Specification | Qty | Est. Price | Notes |
|---|-----------|--------------|-----|-----------|-------|
| 7 | Slide Switch | SS12D00, SPDT, 2-pos | 1 | $0.20 | Hard power cutoff (cuts battery to MCU) |
| 8 | U.FL Antenna (2.4 GHz) | 2.4 GHz whip, U.FL connector | 1 | $1-2 | Some SuperMini boards have U.FL pad — improves range |
| 9 | Enclosure | 3D printed or Hammond 1551MBK (50×35×20 mm) | 1 | $1-5 | Handheld pendant form factor |

## Total Cost Estimate

| Configuration | Cost |
|--------------|------|
| Minimal (SuperMini + expansion + battery + 2 buttons) | **~$8-12** |
| Full (+ antenna, switch, enclosure) | **~$12-18** |

## Supplier Notes

- ESP32-C3 SuperMini + expansion board: AliExpress — search "ESP32-C3 SuperMini expansion board"
- Tactile switches + colored caps: AliExpress — search "12mm tactile switch cap assorted"
- LiPo 500 mAh: AliExpress, Amazon — confirm JST connector polarity matches expansion board before connecting
