# EVKA Position V3 — Simple 12V/15V Hardware Design

> Simple carrier board for the EVKA spherical position sensor.  
> **Manufacturing:** LPKF S63, 2-layer milled PCB, no soldermask, no plated vias.  
> **MCU:** ESP32-S3-DevKitC-1 on female headers.  
> **Backup:** Internal 3S LiPo RC pack; external balance charger only (V3-A) or optional onboard charging (V3-B/C).  
> **Power path:** Discrete Q_BATT (IRF4905) active load-sharing — adapter has priority; battery takes over on adapter loss.  
> **Scope:** Core sensor electronics only: power, ESP32-S3, 3 encoders, ADC monitor, minimal LEDs.

---

## Config Summary

| Config | Adapter | Charging | Charger module |
|---|---|---|---|
| **V3-A** | 12V | External balance charger only | Not populated |
| **V3-B** | 15V | Onboard CN3722, 0.5A | CN3722 module |
| **V3-C** | 15V | Onboard XL4016 CC/CV, 0.5A | XL4016 module (preset) |

Single PCB layout. Populate the charging zone for V3-B or V3-C; leave it empty for V3-A.

---

## Design Goal

V3 is the practical simplification of the previous 12V and V2 hardware packages. It keeps the proven parts and removes non-core features.

Keep:

- 12V input
- ESP32-S3-DevKitC-1 module
- 3S LiPo backup
- External balance charging only
- MP1584EN or equivalent ready-made 12V-to-5V buck module
- Proven encoder signal conditioning: 10k/20k dividers, 1nF filters, TVS, ferrites
- LPKF S63 friendly through-hole parts and plug-in modules

Remove from the default board:

- Onboard LiPo charging circuit
- MT3608 12V-to-15V boost charger path
- TP5100 charger module
- RS-485 / Modbus hardware
- I2C expansion hardware
- External watchdog
- Spare GPIO expansion headers
- SD / Ethernet / CAN future footprints
- Extra status LEDs beyond power and WiFi

---

## Architecture Summary

```text
12V or 15V adapter
    -> NTC (optional) -> fuse/PTC -> TVS clamp -> IRF4905 Q_RPP
    -> V_PROT ──────────────────────────────────────────→ BUCK_VIN
         |                                                    ↑
         +--[V3-B/V3-C] CN3722 or XL4016, 0.5A, 12.60V       |
         |                   |                                |
         |              CHARGE_OUT                            |
         |                   |                                |
         |             F_BAT 5A + BMS_3S                      |
         |                   |                                |
         +── D_GATE SS14 ──> Q_BATT Source (= battery)        |
             R_G2 100k, Z1 12V Zener (gate drive)             |
             Q_BATT Drain ────────────────────────────────────┘

BUCK_VIN -> ADC divider (GPIO1) + MP1584EN buck
MP1584EN -> 22uH + 220uF filter -> 5V_RAIL
5V_RAIL  -> ESP32-S3 VIN + encoder 5V feeds

Encoder outputs -> 10k/20k divider + 1nF filter + 3.3V TVS -> ESP32-S3 GPIOs

J_BAL JST-XH-4P (onboard) = balance lead access for external balance charger
```

---

## Document Index

| Document | Purpose |
|---|---|
| [`circuit_schematic_v3.md`](circuit_schematic_v3.md) | Full V3 net-level schematic narrative, Q_BATT circuit, charging zone |
| [`bill_of_materials_v3.md`](bill_of_materials_v3.md) | BOM for all three configs (V3-A, V3-B, V3-C) |
| [`charging_zone_v3.md`](charging_zone_v3.md) | Charging zone detail: CN3722 (V3-B), XL4016 (V3-C), external-only (V3-A) |
| [`pcb_layout_guide_v3.md`](pcb_layout_guide_v3.md) | 120×80mm LPKF S63 placement and routing guidance |
| [`pin_assignment_v3.md`](pin_assignment_v3.md) | ESP32-S3 GPIO map for core-only V3 |
| [`external_charging_procedure_v3.md`](external_charging_procedure_v3.md) | Safe external charging workflow via J_BAL for all configs |
| [`validation_checklist_v3.md`](validation_checklist_v3.md) | Bring-up and validation checklist |
| [`firmware/pin_assignment_v3.h`](firmware/pin_assignment_v3.h) | Copy-paste GPIO header for future ESP32-S3 firmware migration |
| [`power_path_module_interface_v3.md`](power_path_module_interface_v3.md) | Legacy: original ready-made module interface spec (superseded by Q_BATT) |

---

## V3 vs Previous Versions

| Area | Legacy 12V | V2 | V3 |
|---|---|---|---|
| MCU | Wemos D1 R32 | ESP32-S3-DevKitC-1 | ESP32-S3-DevKitC-1 |
| Charging | Onboard MT3608 + TP5100 | External balance charger only | External balance charger only |
| Battery source selection | Schottky OR | Discrete MOSFET priority (Q_BATT) | Discrete Q_BATT (same as V2, reused) |
| Buck | MP1584EN module | MP1584EN module | MP1584EN or equivalent module |
| Expansion | None | RS-485, I2C, watchdog, spare GPIO | Removed from default |
| PCB style | Mixed / THT variant | 100% THT + modules | 100% THT + modules, simplest routing |

---

## Core Pin Map

| Function | ESP32-S3 GPIO |
|---|---:|
| Battery / 12V ADC | 1 |
| Theta A / B | 4 / 5 |
| Phi A / B | 6 / 7 |
| WiFi LED | 8 |
| Wire A / B / Z | 15 / 16 / 17 |

GPIO 11/12, 13/14/18, and spare GPIOs from V2 are left unused in V3 by default.

---

## Important Safety Decisions

1. **V3-A: no onboard charging.** Use an external 3S balance charger via J_BAL. See [`external_charging_procedure_v3.md`](external_charging_procedure_v3.md).
2. **V3-B/C: use 15V adapter.** The CN3722 and XL4016 require input headroom above 12.6V. A 12V adapter cannot charge a full 3S pack.
3. **Q_BATT prevents false termination.** Battery is isolated from the system load when the adapter is present. This allows the charger to see only the battery and terminate correctly.
4. **BMS_3S is required.** Hardware undervoltage and short-circuit protection is mandatory in all configs. Do not rely on firmware ADC shutdown alone.
5. **Battery fuse is mandatory.** Place F_BAT within 15cm of J_XT60 positive. Do not route unfused battery positive across the PCB.
6. **Do not connect 12V or 15V to ESP32 VIN.** Only filtered 5V from the buck output feeds the DevKitC VIN pins.
7. **Power-test before inserting ESP32-S3.** Follow [`validation_checklist_v3.md`](validation_checklist_v3.md).

---

## Firmware Status

V3 hardware uses the ESP32-S3 pin map, but the active firmware in this repository still targets the Wemos D1 R32 unless migrated separately.

Expected future firmware work:

- Add `esp32-s3-devkitc-1` PlatformIO environment
- Move encoder pins to GPIO 4/5, 6/7, 15/16
- Move ADC to GPIO 1
- Prefer `ESP32Encoder` / PCNT for ESP32-S3 quadrature counting
- Re-test WiFi, TCP, dashboard, and all three encoders on real hardware

Do not treat this documentation package as proof that the ESP32-S3 firmware migration is complete.
