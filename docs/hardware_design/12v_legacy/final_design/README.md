# EVKA Position Final Hardware Design

This folder is the final selected hardware package for the next EVKA core sensor board. It is based on the recommended **V3-A simple 12V design** and extends it into a build-ready reference.

The final design is intentionally narrower than the exploratory V2/V3 documents:

- 12V adapter input only
- ESP32-S3-DevKitC-1 module
- Internal 3S LiPo backup
- External balance charging only
- No onboard charger
- No RS-485, I2C expansion, external watchdog, SD, Ethernet, CAN, or spare GPIO headers on the main board
- Proven 7-channel encoder signal conditioning

## Why This Is The Final Baseline

The comparison in [`../comparison/README.md`](../comparison/README.md) recommends V3-A because it gives the best balance of safety, simplicity, manufacturability, and future firmware direction.

This folder turns that recommendation into a single unambiguous final design. It removes the optional V3-B and V3-C onboard charging branches so the board cannot accidentally be built in a mixed or unsafe configuration.

## Design Validation Summary

This package was reviewed against:

- **CN3722 (V3-B alternative)**: real, sourceable (LCSC C77905), but module variants ship with R_CS already populated and may target a different charge current than the formula assumes. Termination behavior is correct on the IC, but the per-module verification step is a sourcing risk that V3-A avoids.
- **XL4016 CC/CV (V3-C alternative)**: rejected for production. No automatic termination; relies on the BMS as the sole cell-level overcharge backstop. Trimpot drift is a documented community failure mode. Acceptable only as supervised bench equipment.
- **IRF4905 worst-case `Vgs(th)`**: see [`circuit_schematic.md`](circuit_schematic.md) Section 6a for OFF-state margin numbers. The 12V-only design has 1.1V margin to the worst-case threshold and negligible quiescent drain.
- **Project history**: a prior onboard-charging path (TP5100 + 3S termination) was flagged as broken/unsafe. External balance charging via iMax B3 / SkyRC E3S is an established workflow with better termination, balancing, and inspection ergonomics than any onboard option studied.

## What Was Copied And Extended

The final design copies the V3-A direction from [`../v3/`](../v3/) and extends it with these final decisions:

| Area | V3-A Baseline | Final Design Decision |
|---|---|---|
| Input voltage | 12V for V3-A, 15V optional for V3-B/C | 12V only |
| Charging zone | Present for V3-B/C options | Removed from final build |
| Battery charging | External balance charger for V3-A | External balance charger only, mandatory |
| Source selection | Discrete `Q_BATT` concept | Extended with `D_ADAPT` so battery cannot backfeed adapter-sense/gate drive |
| Gate clamp | V3 docs mention a zener option | Omitted in final 12V design; OFF-state `Vgs` margin documented in [`circuit_schematic.md`](circuit_schematic.md) Section 6a |
| Expansion interfaces | Removed by default | Still removed; daughterboard only if future need appears |
| Documentation | V3 package with variants | Final package with one selected configuration |

## Document Index

| Document | Purpose |
|---|---|
| [`circuit_schematic.md`](circuit_schematic.md) | Complete final schematic explanation, power path, encoder interface, nets, test points |
| [`bill_of_materials.md`](bill_of_materials.md) | Final BOM only, no V3-B/C charging options |
| [`pcb_layout_guide.md`](pcb_layout_guide.md) | 120x80mm LPKF S63 layout, zones, trace widths, grounding, assembly order |
| [`pin_assignment.md`](pin_assignment.md) | Final ESP32-S3 GPIO map and migration notes |
| [`external_charging_procedure.md`](external_charging_procedure.md) | Required safe charging workflow for the 3S LiPo |
| [`validation_checklist.md`](validation_checklist.md) | Bring-up, power, switchover, encoder, and endurance validation checklist |
| [`copy_manifest.md`](copy_manifest.md) | Maps final files back to the source V3 and comparison documents |
| [`firmware/pin_assignment_final.h`](firmware/pin_assignment_final.h) | Copy-paste pin header for future ESP32-S3 firmware migration |

## Final Architecture

```text
12V adapter
  -> input fuse/PTC
  -> TVS clamp
  -> Q_RPP reverse-polarity P-FET
  -> V_PROT adapter rail
  -> D_ADAPT adapter-isolation diode
  -> BUCK_VIN
  -> MP1584EN 12V-to-5V buck
  -> 22uH + 220uF post-filter
  -> 5V_RAIL
  -> ESP32-S3 DevKitC VIN and encoder 5V feeds

Internal 3S LiPo
  -> XT60 main connector
  -> F_BAT blade fuse, close to battery positive
  -> BMS/protection board
  -> Q_BATT P-FET battery switch
  -> BUCK_VIN only when adapter is absent

Adapter sense
  -> V_PROT drives Q_BATT gate through D_GATE when adapter is present
  -> D_ADAPT prevents battery-powered BUCK_VIN from backfeeding V_PROT
  -> Q_BATT gate falls through R_GATE_BAT when adapter is absent

Encoder signals
  -> 10k/20k divider
  -> 1nF edge filter
  -> 3.3V TVS clamp
  -> ESP32-S3 GPIOs
```

## Final Electrical Decisions

| Decision | Final Value |
|---|---|
| Adapter input | 12V DC regulated adapter or cabinet 12V rail |
| Adapter range | 11.5V to 12.5V nominal target, 9V to 16V absolute design class |
| Main MCU | ESP32-S3-DevKitC-1, N8 or N8R2 preferred |
| Battery | 3S LiPo RC pack, 1500-2200mAh typical |
| Battery full voltage | 12.60V |
| Battery low warning target | 10.50V |
| Battery shutdown target | 9.90V |
| Battery absolute minimum | 9.00V, do not intentionally reach this |
| Buck module | MP1584EN or equivalent adjustable 12V-to-5V module |
| Buck output target | 5.05V under load before filter/star distribution |
| 5V_RAIL target | 4.9V to 5.1V at ESP32 VIN and encoder VCC |
| ADC divider | 120k top, 27k bottom, scale factor 5.444 |
| ADC GPIO | GPIO 1, ADC1_CH0 |
| Encoder supply | 5V_RAIL only, never 12V |
| Encoder signal divider | 10k top, 20k bottom, 1nF filter per signal |

## Final Pin Map

| Function | GPIO |
|---|---:|
| Supply ADC | 1 |
| Theta A | 4 |
| Theta B | 5 |
| Phi A | 6 |
| Phi B | 7 |
| WiFi LED | 8 |
| Wire A | 15 |
| Wire B | 16 |
| Wire Z | 17 |

## Safety Rules

These rules are part of the design, not optional assembly advice.

1. Do not populate any onboard LiPo charger on the final board.
2. Charge the 3S LiPo only with an external 3S balance charger.
3. Disconnect the adapter before external charging.
4. If panel charging is used, add a battery load disconnect or service plug.
5. Install `F_BAT` close to the battery positive lead.
6. Do not route unfused battery positive across the PCB.
7. Do not feed 12V into ESP32 VIN.
8. Do not power encoders from 12V.
9. Do not insert the ESP32-S3 module until `5V_RAIL` is verified below 5.2V.
10. Do not use 100nF capacitors on encoder signal filters; use 1nF.
11. Do not let IRF4905 metal tabs touch grounded chassis metal.

## What Is Not Included

The final board intentionally excludes these features:

- RS-485 / Modbus transceiver
- I2C expansion header
- External watchdog
- Spare GPIO header
- SD card, Ethernet, or CAN footprints
- Onboard charger
- 15V adapter mode
- V3-B CN3722 option
- V3-C XL4016 option

If one of these features becomes mandatory, add it as a daughterboard or explicitly reopen the hardware design decision. Do not silently add it to this final core board.

## Future Revision Paths

If a future revision must add onboard charging (for example, an unattended deployment without periodic battery service), reopen the onboard-charging comparison branch documented as **V3-D Onboard 3S Charger Module** in [`../comparison/HARDWARE_COMPARISON.md`](../comparison/HARDWARE_COMPARISON.md). The charger must be isolated from the system load: the system should run from the adapter while the charger sees only the battery path.

The onboard-charging branch must keep these requirements:

1. **Switch the adapter to 15V or use a verified USB-C PD/boost charger module**. A plain 12V buck charger cannot charge a full 3S pack to 12.6V.
2. **Use a verified 12.6V CC/CV 3S charger**. Measure termination current, charge current, charge-status behavior, and thermal rise before treating it as field hardware.
3. **Pair the charger with a documented 3S BMS/protection board**. A 25A or 40A balanced BMS is the practical range for the V3-D module prototype; the rating is load/discharge capability, not charge current. Use 6A only for very low-power electronics and 60A only when the wiring, connector, fuse, and load really require it.
4. **Keep balance-service access**. BMS passive balancing is a backstop, not a substitute for a known balancing/service policy.
5. **Re-evaluate the Q_BATT gate clamp at the chosen input voltage**. The OFF-state `Vgs` margin shrinks at higher V_PROT. A 15V-rated unidirectional zener (e.g., 1N4744A) sized to keep the OFF-state gate at or above the maximum source voltage is the simplest hardening; a bidirectional clamp is the more conservative choice.
6. **Keep BMS_3S as a hardware backstop only**, not as the primary cell-level overcharge protection. The charger provides the primary CC/CV control loop.
7. **Do not use parallel battery-load charging as the production topology**. The system load can corrupt charger termination if it shares the battery charge node.

The studied V3-D implementation options are:

| Option | Stack | Use When | Notes |
|---|---|---|---|
| Option A - simple prototype | 3S 12.6V 2A charger module + 3S 25A or 40A balanced BMS + 15V / 3A adapter | You need the cheapest practical onboard 3S charger branch | Preferred first onboard-charging prototype. Use charge-only mode first if possible. |
| Option B - cleaner enclosure | 3S Type-C 2A charger module + 3S 25A or 40A balanced BMS + required USB-C PD/QC adapter | USB-C is important for user interface or enclosure design | Verify the exact board supports 3S / 12.60V output. A Type-C connector alone does not prove PD or 3S support. |
| Option C - professional custom PCB | TI `BQ24170` charger/power-path circuit + 3S BMS/protection + adapter/load-sharing path | You want a cleaner engineered onboard charger instead of anonymous modules | Best custom-PCB direction for 1-3S with power-path, but it requires SMD layout, thermal design, and charger validation. |

Architecture ranking for that future branch:

| Architecture | Role |
|---|---|
| Charge-only mode | Best first integrated onboard-charging prototype; disconnect the system load while charging. |
| Power-path / load-sharing | Best final run-while-charging architecture; adapter powers the system while the charger sees only the battery path. |
| Docking-style charging | Good enclosure variant if dock detect can stop motors/high-current loads before charging. |
| Smart MCU supervision | Useful safety/control layer for adapter present, battery voltage, temperature, BMS status, LEDs, fan, and shutdown. It does not replace the charger or BMS. |
| Removable battery / external balance charging | Safest development method and the policy selected for this Final Design package. |
| Parallel battery-load charging | Avoid for production. |

Professional IC direction: `BQ24170` is the cleaner custom-PCB path for 1-3S charging with power-path; `BQ24610` is better for a higher-current custom buck charger but requires more external power-stage design; `LTC4015` is a telemetry-heavy professional option and is overkill unless I2C monitoring and a professional PCB process are required.

The V3 documents at [`../v3/`](../v3/) retain the V3-B option and the populated charging zone. Re-opening the V3-B path means re-opening that doc set, not editing this final folder.

## Firmware Status

The hardware pin map targets ESP32-S3. The active firmware in this repository still targets the Wemos D1 R32 unless migrated separately.

Required firmware work before this board is operational:

1. Add a PlatformIO environment for `esp32-s3-devkitc-1`.
2. Move encoder pins to GPIO 4/5, GPIO 6/7, and GPIO 15/16/17.
3. Move supply ADC to GPIO 1.
4. Prefer PCNT-based quadrature counting, such as `ESP32Encoder`, on ESP32-S3.
5. Re-test WiFi, TCP, web dashboard, calibration commands, and all three encoders on real hardware.

## Build Order

Use this sequence for the first final board:

1. Read this `README.md`.
2. Review [`circuit_schematic.md`](circuit_schematic.md) and mark all polarity-sensitive parts.
3. Order only the parts in [`bill_of_materials.md`](bill_of_materials.md).
4. Lay out the board using [`pcb_layout_guide.md`](pcb_layout_guide.md).
5. Assemble power-only first.
6. Run [`validation_checklist.md`](validation_checklist.md) through the 5V rail tests.
7. Insert the ESP32-S3 only after power tests pass.
8. Test one encoder at a time.
9. Test adapter-to-battery switchover.
10. Run a 30-minute full system test before machine use.
