# Charging Zone — EVKA Position V3

> V3 supports three population configs on one 120×80mm board.  
> The charging zone is a reserved area in the top-left corner that is always drilled and wired to the bus.  
> Populate it for onboard charging (V3-B or V3-C), or leave it empty for external-only charging (V3-A).

---

## 1. Config Summary

| Config | Adapter | Charging method | Charger module | Approx. charge time |
|---|---|---|---|---|
| **V3-A** | 12V | External balance charger only | Not populated | n/a |
| **V3-B** | 15V | Onboard CN3722, 0.5A | CN3722 module | 3-4h for 2000mAh pack |
| **V3-C** | 15V | Onboard XL4016 CC/CV, 0.5A | XL4016 module (preset) | 3-4h for 2000mAh pack |

All three configs use the same Q_BATT active load-sharing circuit. The board continues to run from the adapter while the battery is charging.

---

## 2. Why Q_BATT Enables Safe Onboard Charging

The Q_BATT circuit isolates the battery from the system load (`BUCK_VIN`) when the adapter is present.

```text
  Adapter present:
    Q_BATT OFF → battery positive disconnected from BUCK_VIN
    BUCK_VIN = V_PROT (adapter direct)
    Charger sees: battery only (no system load on battery node)
    → correct CC/CV charge termination, no false termination

  Adapter absent:
    Q_BATT ON → battery powers BUCK_VIN
    Charger has no input power (adapter gone)
    → normal battery-powered operation
```

Without this isolation, a charger module would see both the battery and the system load in parallel. The system load current would prevent the charge current from dropping to the termination threshold, causing the charger to float-charge indefinitely — a known LiPo destruction and fire mechanism.

---

## 3. V3-A: External Charging Only (12V Adapter)

Leave the entire charging zone unpopulated. The zone pads are present on the PCB but carry no components.

Required for safe operation:

- External 3S balance charger (iMax B3, SkyRC E3S, or equivalent)
- Charge via J_BAL (JST-XH-4P onboard balance header) and J_XT60 main lead
- Never leave the battery connected to J_XT60 and the adapter connected simultaneously for more than a few minutes without verifying the power-path behavior

External charging procedure: see [`external_charging_procedure_v3.md`](external_charging_procedure_v3.md).

---

## 4. V3-B: CN3722 Module (Recommended Onboard Option)

### 4a. Module Description

The CN3722 is a dedicated 3-cell (3S) LiPo/Li-ion charger IC available in a ready-made module from AliExpress or similar sources.

| Parameter | Value |
|---|---|
| Input voltage | 12V–18V (use 15V adapter) |
| Charge voltage | 12.6V (3S Li-ion, fixed) |
| Charge current | Set by R_CS resistor, see below |
| Module size | ~35mm × 20mm typical |
| Charge termination | CC/CV with automatic cut-off |
| Cell balancing | None — use external balance charger for balancing |
| CHRG output | Open-drain, active LOW when charging |

### 4b. Wiring

```text
V_PROT (15V adapter) ─→ CN3722 VIN
GND ──────────────────→ CN3722 GND
CN3722 VOUT ──────────→ CHARGE_OUT → F_BAT (5A blade) → BMS_3S IN+ → J_XT60 BAT+
CN3722 CHRG pin ──────→ R_CHRG (1kΩ) → LED_CHRG (yellow/orange 3mm) → GND
```

### 4c. Charge Current Setting

R_CS sets the charge current using CN3722's internal 1.0V reference:

```
I_CHG = 1.0 / R_CS
```

| I_CHG target | R_CS value | Standard resistor |
|---:|---:|---|
| 0.5A | 2.0Ω | 2.0Ω, 1%, 1/4W axial |
| 0.3A | 3.3Ω | 3.3Ω, 1%, 1/4W axial |

Default: **R_CS = 2.0Ω** for 0.5A. Verify against the CN3722 module datasheet if the formula differs — Chinese module variants may use 1.2V reference (R_CS = 1.2/I_CHG → 2.4Ω for 0.5A).

Install R_CS on the pads provided on the CN3722 module or as a discrete on the PCB if the module exposes the CS pin.

### 4d. CHRG LED Indicator

The CHRG pin is open-drain active LOW.

```text
3.3V or 5V ─→ R_CHRG (1kΩ) ─→ CN3722 CHRG ─→ (internal pull to GND when charging)
              also ─→ LED_CHRG anode ─→ LED_CHRG cathode ─→ GND
```

Simplified (LED directly on CHRG pin):

```text
CN3722 VOUT (or 5V_RAIL) ─→ R_CHRG 1kΩ ─→ LED_CHRG ─→ CN3722 CHRG pin ─→ (to GND when active)
```

LED behavior: ON while charging, OFF when charge complete or no input power.

---

## 5. V3-C: XL4016 CC/CV Module (Fallback Option)

### 5a. Module Description

The XL4016 is a generic adjustable step-down (buck) module. It is not a dedicated charger IC — it provides a stable CC/CV output that acts as a safe charging source when correctly preset.

| Parameter | Value |
|---|---|
| Input voltage | 8V–36V (use 15V adapter) |
| Output voltage | Adjustable via CV trimpot, preset to 12.60V |
| Output current limit | Adjustable via CC trimpot, preset to 0.5A |
| Module size | ~55mm × 22mm typical |
| Charge termination | None — relies on CC/CV natural taper |
| Cell balancing | None — use external balance charger |

Note: the XL4016 module does not terminate charging automatically. It provides constant 12.60V at up to 0.5A. The HX-3S-01 BMS protects against overcharge at the cell level, but the charger will continue to supply current at the topping voltage indefinitely. For long-term storage, disconnect the adapter or use a smart external charger via J_BAL.

### 5b. Wiring

```text
V_PROT (15V adapter) ─→ XL4016 VIN
GND ──────────────────→ XL4016 GND
XL4016 VOUT ──────────→ CHARGE_OUT → F_BAT (5A blade) → BMS_3S IN+ → J_XT60 BAT+
```

LED indicator (output-on only, no charge-done signal):

```text
XL4016 VOUT ─→ R_CHRG (1kΩ) ─→ LED_CHRG ─→ GND
```

LED ON = module output is active. LED does not distinguish charging from full.

### 5c. Trimpot Preset Procedure

Perform before connecting to battery.

1. Connect 15V adapter to VIN. Leave VOUT disconnected from battery.
2. Adjust the **CV trimpot** until VOUT measures **12.60V** (±0.02V) at the VOUT terminals.
3. Connect a 25Ω/10W resistor load across VOUT. Confirm VOUT stays at 12.60V.
4. Short-circuit the CC current-sense resistor to disable CC mode. Measure output current with an ammeter in series with the load at various load values to confirm the CV regulation holds.
5. Insert the CC trimpot: with a 12Ω load and ammeter in series, adjust CC trimpot until current reads **0.50A**. At 12.60V × 0.50A = 6.3W — do not exceed load wattage rating.
6. Remove test load. Reconnect VOUT to F_BAT → BMS → battery path.
7. Apply a drop of CA glue to both trimpot bodies after verifying settings. Vibration can drift pot values.

---

## 6. Charging Zone PCB Area

The charging zone occupies approximately **40mm × 25mm** in the top-left of Zone A (see [`pcb_layout_guide_v3.md`](pcb_layout_guide_v3.md)).

| Footprint | Purpose |
|---|---|
| Charger module mounting pads or standoffs | CN3722 or XL4016 module position |
| R_CS (2.0Ω) pads | CN3722 current-set resistor (if not on module) |
| LED_CHRG + R_CHRG pads | Charge indicator LED and 1kΩ series resistor |
| CHARGE_OUT trace to F_BAT | 2.0mm trace minimum from charger output to fuse |

For V3-A: all pads in this zone are present but unused. Leave components unpopulated.

---

## 7. Parts for Charging Zone

### V3-B (CN3722)

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| MOD_CHG | 1 | CN3722 module | 3S charger, 12V-18V input | Module ~35×20mm | AliExpress |
| R_CS | 1 | Resistor | 2.0Ω, 1%, 1/4W | Axial | Charge current set |
| LED_CHRG | 1 | LED | 3mm yellow or orange | THT | Charge indicator |
| R_CHRG | 1 | Resistor | 1kΩ, 1/4W | Axial | LED current limit |

### V3-C (XL4016)

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| MOD_CHG | 1 | XL4016 CC/CV module | 8-36V in, adjustable out, CC+CV | Module ~55×22mm | AliExpress; preset to 12.60V / 0.5A before use |
| LED_CHRG | 1 | LED | 3mm yellow or orange | THT | Output-active indicator |
| R_CHRG | 1 | Resistor | 1kΩ, 1/4W | Axial | LED current limit |

### V3-A (no charger)

No additional parts. Use external balance charger (iMax B3 / SkyRC E3S or equivalent) via J_BAL + J_XT60.

---

## 8. Safety Rules

1. **Do not use the 12V adapter with V3-B or V3-C.** The CN3722 and XL4016 require higher input than the 12.6V battery target. Use a 15V adapter (max 18V for CN3722, max 36V for XL4016).
2. **Do not leave a full battery connected to V3-C (XL4016) for extended storage.** The XL4016 has no charge-done cutoff. The BMS provides overcharge protection at the cell level, but a constant float at 12.6V is not ideal for long-term storage.
3. **BMS_3S is required in all configs.** Hardware protection against undervoltage and short-circuit is mandatory regardless of whether onboard charging is populated.
4. **Never bypass F_BAT.** The blade fuse protects the battery wiring from short-circuit. Place it within 15cm of J_XT60 positive.
5. **Charger output path carries charging current, not system load.** System load is powered by V_PROT (adapter direct to BUCK_VIN) when adapter is present — not through the battery or charger path.
