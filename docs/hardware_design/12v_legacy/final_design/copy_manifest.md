# Final Design Copy Manifest

This folder is a copied and extended finalization of the recommended V3-A design. It is not a new unrelated architecture.

## Source Documents

| Source | Used For |
|---|---|
| [`../comparison/README.md`](../comparison/README.md) | Selection rationale and final recommendation |
| [`../v3/README.md`](../v3/README.md) | Core V3-A architecture and ESP32-S3 direction |
| [`../v3/circuit_schematic_v3.md`](../v3/circuit_schematic_v3.md) | Power, buck, ADC, encoder, and ESP32-S3 schematic basis |
| [`../v3/bill_of_materials_v3.md`](../v3/bill_of_materials_v3.md) | BOM basis, with V3-B/C charger items removed |
| [`../v3/pcb_layout_guide_v3.md`](../v3/pcb_layout_guide_v3.md) | LPKF S63 layout basis |
| [`../v3/pin_assignment_v3.md`](../v3/pin_assignment_v3.md) | ESP32-S3 pin map basis |
| [`../v3/external_charging_procedure_v3.md`](../v3/external_charging_procedure_v3.md) | External 3S balance charging procedure basis |
| [`../v3/validation_checklist_v3.md`](../v3/validation_checklist_v3.md) | Bring-up and validation basis |
| [`../v2/subsystems/power_supply_v2.md`](../v2/subsystems/power_supply_v2.md) | Active battery-source selection concept and battery fuse policy |
| [`../v2/subsystems/encoder_interface_v2.md`](../v2/subsystems/encoder_interface_v2.md) | Encoder divider/filter/TVS details |

## Final Files

| Final File | Derived From | Main Changes |
|---|---|---|
| [`README.md`](README.md) | V3 README + comparison recommendation | Locks design to V3-A only and explains final decisions |
| [`circuit_schematic.md`](circuit_schematic.md) | V3 schematic | Removes charger variants, adds `D_ADAPT`, explains final nets |
| [`bill_of_materials.md`](bill_of_materials.md) | V3 BOM | Removes CN3722/XL4016 charger parts, adds adapter-isolation diode |
| [`pcb_layout_guide.md`](pcb_layout_guide.md) | V3 layout guide | Removes charging zone and adds final zone map |
| [`pin_assignment.md`](pin_assignment.md) | V3 pin assignment | Keeps only final pins and firmware migration notes |
| [`external_charging_procedure.md`](external_charging_procedure.md) | V3 external charging procedure | Narrows procedure to final external-only charging policy |
| [`validation_checklist.md`](validation_checklist.md) | V3 validation checklist | Adds `D_ADAPT`/`Q_BATT` behavior tests and final acceptance gates |
| [`firmware/pin_assignment_final.h`](firmware/pin_assignment_final.h) | V3 firmware header | Final copy-paste pin constants for ESP32-S3 migration |

## Final Design Extensions

### Adapter Isolation Diode

The final design adds `D_ADAPT` between `V_PROT` and `BUCK_VIN`.

Purpose:

- Adapter present: `D_ADAPT` feeds `BUCK_VIN` from the protected adapter rail.
- Adapter absent: `D_ADAPT` blocks battery-powered `BUCK_VIN` from backfeeding `V_PROT`.
- This keeps `V_PROT` as a true adapter-sense rail for the `Q_BATT` gate circuit.

Without this isolation, a direct `V_PROT` to `BUCK_VIN` tie can let battery voltage raise the adapter-sense rail during battery operation. That can incorrectly drive the `Q_BATT` gate high and turn the battery path off.

### No Gate Zener In Final V3-A

The final design omits the optional `Q_BATT` gate zener from the simple 12V build.

Reason:

- ON-state `Vgs` magnitude is bounded by the full 3S pack voltage, about -12.6V — well inside the IRF4905 +/-20V rating, so no clamp is required for device protection.
- OFF-state `Vgs` margin is acceptable: at adapter-present and full battery the gate sits at ~11.7V and the source at 12.6V, giving `Vgs` = -0.9V with 1.1V margin to the worst-case `Vgs(th)` = -2V. See [`circuit_schematic.md`](circuit_schematic.md) Section 6a.
- A single gate-source zener can create an unwanted forward path when the gate is above the battery source during adapter-present operation.
- The simplest final 12V circuit is safer and easier to validate without it.

If a future version raises the adapter voltage (15V or higher) or the battery (24V), the OFF-state margin shrinks or inverts. Revisit with a 1N4744A-class higher-Vz unidirectional zener or a proper bidirectional clamp; do not just transplant the V2 12V Zener.

### No Onboard Charging

The final design does not copy the V3-B/C charger population options.

Reason:

- The core sensor does not need onboard charging to measure position.
- 3S LiPo balancing is a safety-critical operation.
- A dedicated external balance charger is easier to validate than an onboard charger assembled on a prototype carrier.
- External review (CN3722 sourcing reality, XL4016 termination behavior, IRF4905 worst-case `Vgs(th)`) confirmed V3-A as the lowest-risk path. See `README.md` "Design Validation Summary" and `circuit_schematic.md` Section 6a for details.

### Q_BATT OFF-state Margin Documented

`circuit_schematic.md` Section 6a now includes the concrete `Vgs` table for adapter-present operation across full / nominal / low battery states. This was not in the V3 source schematic — it was added because external review flagged the IRF4905 worst-case `Vgs(th)` of -2V as worth quantifying explicitly. The 12V-only design passes with 1.1V margin to worst case; future 15V revisions need re-evaluation.

### Future Revision Path Documented

`README.md` "Future Revision Paths" section captures the studied conditions under which V3-B (CN3722, 15V adapter) would be the right answer. Recorded so a future builder does not have to redo the comparison work.
