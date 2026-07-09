# 5V + 1S LiPo PCB Design (Legacy)

Original evka_position carrier board — 5V external input with 1S LiPo battery backup.

## Files

| File | Description |
|------|-------------|
| [circuit_schematic.md](circuit_schematic.md) | Full ASCII schematic: 5V input, TP4056 charger, MT3608 boost, signal conditioning |
| [bill_of_materials.md](bill_of_materials.md) | Complete BOM (~30 line items) |
| [pcb_layout_guide.md](pcb_layout_guide.md) | 120×80 mm pertinax layout, zone map, trace widths, assembly sequence |

## Design overview

- **5V DC input** → SI2301 RPP → 5V_RAIL (Schottky OR with boost output)
- **TP4056 + DW01A** → 1S LiPo charger with cell protection
- **MT3608 boost** → 5.3V from LiPo (compensates Schottky Vf) → Schottky OR → 5V_RAIL
- **Signal conditioning**: 7× 10k/20k dividers + 1nF filters + TVS on all encoder lines
- **Ferrite beads** (600Ω@100MHz) on each encoder VCC feed

## Superseded by

The **12V + 3S LiPo** design in [../12v_legacy/12v/](../12v_legacy/12v/) (archived — the project reverted to 5V) is a historical alternative to this board. The signal conditioning section (dividers, TVS, ferrites) is identical between both designs.
