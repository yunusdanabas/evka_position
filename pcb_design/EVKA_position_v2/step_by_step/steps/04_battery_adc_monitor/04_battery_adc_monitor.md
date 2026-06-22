# Step 4 — Battery voltage ADC monitor · Zone B

A two-resistor ÷2 divider so the ESP32 can read the 1S LiPo voltage on a 3.3 V ADC, plus a bypass cap
to quiet the sampling node. Tiny, but it's what lets the firmware do low-battery cutoff.

Extracted verbatim from the read-only reference `../../EVKA_position_v2.kicad_sch`.

## ASCII schematic

```
   BAT_PLUS ──┤ R_MON1 ├──┬── ADC_MON ──────► (Step 8, GPIO1 / ADC)
              (100k)      │
                       ┌──┴──┐   ┌──────┐
                     R_MON2  │  C_ADC   │
                     (100k)  └── 100nF ─┘
                        │         │
                       GND       GND
```

`BAT_PLUS → R_MON1 → ADC_MON → R_MON2 → GND`; `C_ADC` from `ADC_MON` to GND.

## Components

| Refdes | Symbol (lib_id) | Value | `(at x y rot)` | Footprint |
|---|---|---|---|---|
| R_MON1 | `Device:R` | 100k | 469.9, 60.96, 0 | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |
| R_MON2 | `Device:R` | 100k | 469.9, 88.9, 0 | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |
| C_ADC | `Device:C` | 100nF | 490.22, 88.9, 0 | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` |

## Nets (as built)

| Net | Pins | Role |
|---|---|---|
| `BAT_PLUS` | R_MON1/1 | divider top — **interface in ← Step 3** |
| `ADC_MON` | R_MON1/2, R_MON2/1, C_ADC/1 | divider tap — **interface out → Step 8 (GPIO1)** |
| `GND` | R_MON2/2, C_ADC/2 | divider bottom |

## Keypoints (the lesson)

- **÷2, not arbitrary.** 100 k / 100 k halves the input: a full 1S LiPo at 4.2 V reads **2.1 V** at
  `ADC_MON` — comfortably under the 3.3 V ADC ceiling with headroom. Firmware multiplies the reading
  back ×2 (thresholds live in `firmware/src/SphericalSensor.h`).
- **High resistor values save battery.** 100 k + 100 k = 200 kΩ draws only ~21 µA off the LiPo at
  4.2 V — negligible standby drain. The trade-off is source impedance, which is why C_ADC matters.
- **C_ADC (100 nF) = ADC sample bypass.** The ESP32 ADC samples onto an internal cap through a
  sampling switch; a high-impedance source (100 kΩ here) can't settle fast enough alone. The 100 nF
  reservoir supplies the sampling charge so readings are stable, and filters supply noise.
- This is a monitor only — it does **not** power anything; `ADC_MON` is a sense line.

## ERC on this isolated sub-circuit

`0 errors, 4 warnings` — all benign:
1. *Label connected to only one pin* @ `BAT_PLUS` (R_MON1/1) — interface-in; merges with Step 3.
2–4. *Symbol 'R'/'C' doesn't match copy in library 'Device'* — cosmetic. Do **not** `snap_to_grid`.

`ADC_MON` and `GND` are multi-pin → no single-pin warning. No PWR_FLAG needed (no power-input pins here).

## Copying into your master

1. Place the 3 parts at the coordinates above (2.54 grid).
2. Label `BAT_PLUS` on R_MON1/1 (merges with Step 3), `ADC_MON` on the tap (R_MON1/2 + R_MON2/1 +
   C_ADC/1), `GND` (power symbol) on R_MON2/2 + C_ADC/2.
3. Carry **`ADC_MON`** forward to Step 8 (lands on GPIO1).
