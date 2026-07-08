# Power-Path Module Interface — V3

> **Superseded.** V3 now uses the discrete Q_BATT (IRF4905 + SS14 + 100kΩ + 1N4742A Z1) active load-sharing circuit from V2, not a ready-made module. See [`circuit_schematic_v3.md`](circuit_schematic_v3.md) Section 4 and [`charging_zone_v3.md`](charging_zone_v3.md). This document is retained for reference only.

---

> V3 originally planned to use a ready-made power-path / UPS / ideal-diode module instead of a custom onboard charger or custom source-selector.  
> This keeps the LPKF PCB simple, but the selected module must be validated before it is trusted.

---

## 1. Required Function

The module selects between:

- Protected 12V adapter rail: `V12_PROT`
- Internal 3S LiPo battery: fused battery positive, about 9.0-12.6V

And outputs:

- `BUCK_VIN`, feeding the 12V-to-5V buck converter

Required behavior:

- Adapter powers the load when adapter is present.
- Battery powers the load when adapter is absent.
- Battery must not significantly discharge into the adapter rail.
- Adapter must not feed uncontrolled current into the battery.
- Output must remain in the buck module input range.

---

## 2. PCB Interface

Use screw terminals or a simple header instead of a fixed unknown footprint.

```text
J_PWRPATH_IN
Pin 1: ADAPTER+  = V12_PROT
Pin 2: BATTERY+  = fused 3S battery positive
Pin 3: GND

J_PWRPATH_OUT
Pin 1: BUCK_VIN
Pin 2: GND
```

If the selected module has separate grounds, tie grounds according to the module datasheet. In most low-cost DC modules, grounds are common.

---

## 3. Acceptance Criteria

Do not install a module permanently unless it passes these checks.

| Test | Requirement |
|---|---|
| Input voltage range | Works from 9.0V to 13.0V minimum |
| Continuous load | >=1A continuous output without overheating |
| Adapter priority | Adapter supplies load when adapter is present |
| Battery takeover | Battery supplies load when adapter is removed |
| Reverse current into adapter | Near zero or within module datasheet limit |
| Uncontrolled battery charge | Not present |
| Quiescent battery drain | Low enough for storage, or battery must be unplugged for storage |
| Thermal behavior | Safe after 30 minutes at expected load |
| Output transient | Buck input must not dip below buck minimum during switchover |

Recommended test load:

- Start with 25 ohm / 10W on `BUCK_VIN` equivalent load, about 0.5A at 12V.
- Then test with the real buck + ESP32 + encoders.

---

## 4. Module Types That May Work

Acceptable candidates, subject to testing:

- 12V DC UPS power-path board with clear input/output terminals and no forced onboard charging use
- Ideal-diode OR module rated for 12V and >=1A
- DC power mux module with adapter-priority behavior
- Protected battery backup module that supports external 3S battery and reverse-current blocking

Avoid:

- Single-cell 1S Li-ion UPS modules
- Modules that boost from 1S to 12V unless explicitly required and tested
- Modules that trickle or float a 3S LiPo without balance charging
- Modules with undocumented charging behavior
- Modules rated only for USB/5V loads

---

## 5. Charging Rule

Default V3 rule:

**Do not charge the 3S LiPo through the V3 PCB or through the power-path module.**

If a candidate module includes charging, use it only if all of these are true:

- It explicitly supports 3S LiPo / Li-ion charging.
- It performs proper CC/CV charge termination for 12.6V packs.
- It provides or supports cell balancing, or is used with a pack that has a proper protected/balanced charging system.
- It is documented well enough to verify charge current, termination, and thermal behavior.

If those conditions are not met, leave all charge functions disconnected and use the external charging procedure.

---

## 6. Validation Procedure

### Adapter-Only Test

1. Connect 12V adapter to module adapter input.
2. Leave battery disconnected.
3. Connect 25 ohm / 10W load to module output.
4. Verify output voltage is stable.
5. Check module temperature after 10 minutes.

### Battery-Only Test

1. Connect charged 3S LiPo through fuse.
2. Leave adapter disconnected.
3. Connect same load.
4. Verify output follows battery voltage and remains stable.
5. Confirm no unexpected heating.

### Both-Sources Test

1. Connect adapter and battery.
2. Connect load.
3. Measure battery current if possible.
4. Battery current should be near zero or match datasheet standby/leakage behavior.
5. Remove adapter and verify output continues from battery.
6. Reconnect adapter and verify output returns to adapter source.

### Real-System Test

1. Connect module to V3 buck input.
2. Run ESP32-S3 + all encoders.
3. Toggle adapter connection 10 times.
4. Verify no ESP32 reset, no encoder count glitch, and no module overheating.

If the real-system test resets, increase `BUCK_VIN` bulk capacitance or select a better module.
