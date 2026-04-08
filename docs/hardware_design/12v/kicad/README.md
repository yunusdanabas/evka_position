# evka_position_12v — KiCad 9 schematic (hierarchy)

Open **`evka_position_12v.kicad_pro`** in **KiCad 9**.

## Structure

| Sheet | File | Contents |
|-------|------|----------|
| Root | `evka_position_12v.kicad_sch` | Hierarchical index + pointers to markdown |
| Power | `power_input_12v.kicad_sch` | Block list: fuse, TVS, RPP, buck, USB OR, ADC divider |
| Signals | `encoders_signal_12v.kicad_sch` | Placeholder — copy nets from legacy ASCII doc |

## Authoritative design docs (same folder tree)

- [../circuit_schematic_12v.md](../circuit_schematic_12v.md) — full **12V power** ASCII schematic
- [../../5v/circuit_schematic.md](../../5v/circuit_schematic.md) — **sections 3–7** (encoders + ESP32), unchanged for 12V PCB
- [../bill_of_materials_12v.md](../bill_of_materials_12v.md)
- [../power_supply_12v_spec.md](../power_supply_12v_spec.md)

## Next steps in KiCad

1. Replace placeholder **text** on `power_input_12v.kicad_sch` with symbols from **Device**, **Connector**, **Transistor_FET**, **Diode**, **Regulator_Switching** (or keep **pre-made buck module** as a **Connector** block).
2. On `encoders_signal_12v.kicad_sch`, duplicate the legacy board’s encoder + ESP32 sheet (or redraw from `circuit_schematic.md`).
3. Add **hierarchical labels** or **global labels** (`5V_RAIL`, `GND`, `V12_PROT`) between sheets when you merge power and signal into one PCB.

## ERC

From the repo root:

```bash
kicad-cli sch erc docs/hardware_design/12v/kicad/evka_position_12v.kicad_sch
```
