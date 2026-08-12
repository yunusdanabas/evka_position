# 12V + 3S LiPo PCB Design Bundle

Documentation and KiCad sources for the **12V-input** evka_position carrier with **3S LiPo battery backup**, buck to 5V, and same encoders and ESP32 signal conditioning as the legacy 5V board.

## Design overview

- **12V DC input** → fuse + TVS + P-FET RPP → protected 12V rail
- **MP1584EN buck** → 5V for ESP32 and encoders
- **3S LiPo backup** via Schottky OR at buck input → seamless switchover
- **MT3608 boost** (12V→15V) → **TP5100** charger (3S mode) → **3S BMS** → battery
- Signal conditioning (7× dividers, TVS, ferrites) **identical** to legacy 5V board

## Files

| File | Description |
|------|-------------|
| [power_supply_12v_spec.md](power_supply_12v_spec.md) | Input class, load budget, battery spec, charging spec, thermal |
| [circuit_schematic_12v.md](circuit_schematic_12v.md) | Full ASCII schematic: 12V input, buck, Schottky OR, charger, BMS, ADC |
| [bill_of_materials_12v.md](bill_of_materials_12v.md) | Complete BOM with example MPNs (~35 line items) |
| [pcb_layout_guide_12v.md](pcb_layout_guide_12v.md) | Layout zones, trace widths, EMI isolation, assembly + test checkpoints |
| [kicad/](kicad/) | KiCad 9 hierarchical project (placeholder) |

## All-THT variant

An **all through-hole version** of this design is available in [../12v_tht/](../12v_tht/). Same circuit topology — all SMD discretes (AO4407A, SMBJ18A, SS34 SMA, 0805 caps) replaced with THT equivalents (IRF4905 TO-220, P6KE18A axial, SS34 DO-201, ceramic disc). Easier to hand-solder on pertinax without SMD rework tools.

## New simple V3 reference

For new simple 12V builds, prefer [../v3/](../v3/). V3 keeps the ESP32-S3 + 3S backup direction, removes onboard charging and V2 expansion hardware, and uses a ready-made power-path module interface for the internal battery backup.

## Legacy 5V reference (unchanged signal section)

- [../../5v/circuit_schematic.md](../../5v/circuit_schematic.md) — sections 3–7 (encoder dividers, GPIO, TVS, ferrites)
- [../../5v/bill_of_materials.md](../../5v/bill_of_materials.md) — signal section components (R1–R14, C2–C12, TVS1–TVS7, FB1–FB3, J1–J3)
