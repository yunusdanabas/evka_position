# Step 6 — Signal-conditioning channel ×6 · Zone C

Six identical channels, one per encoder signal. Each knocks the 5 V encoder output down to ~3.3 V with
a resistive divider, low-pass filters it, and reserves a TVS footprint for ESD (left unpopulated). Build
**one channel**, then replicate it six times — the only thing that changes is the input net name.

Channel order: n=1..6 = THETA_A, THETA_B, PHI_A, PHI_B, WIRE_A, WIRE_B.
Extracted verbatim from the read-only reference `../../EVKA_position_v2.kicad_sch`.

## ASCII schematic (one channel; ×6)

```
   <sig>_IN ──┤ R_TOPn ├──┬──────── DIVIDER_NODE_n ───────► (Step 7, 74HC14 input)
              (10k)       │
                    ┌─────┼─────┬─────────┐
                  R_BOTn  │   C_FILTn    TVSn
                  (20k)   │   (10nF)   (DNP, DO-15)
                    │     │     │         │
                   GND   GND   GND       GND
```

Per channel: `<sig>_IN → R_TOPn → DIVIDER_NODE_n → R_BOTn → GND`; `C_FILTn` and `TVSn` from
`DIVIDER_NODE_n` to GND.

## Components (n = 1..6; rows at y = 231.14, 254, 279.4, 304.8, 330.2, 355.6)

| Refdes | Symbol (lib_id) | Value | x | Footprint |
|---|---|---|---|---|
| R_TOPn | `Device:R` | 10k | 129.54 | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |
| R_BOTn | `Device:R` | 20k | 154.94 | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |
| C_FILTn | `Device:C` | 10nF | 175.26 | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` |
| TVSn | `Device:D_TVS` | TVS 3.3V (THT-TBD) | 195.58 | `Diode_THT:D_DO-201AD_P15.24mm_Horizontal` **(populate)** |

Input-net per channel: n1=THETA_A_IN, n2=THETA_B_IN, n3=PHI_A_IN, n4=PHI_B_IN, n5=WIRE_A_IN, n6=WIRE_B_IN.
All at rotation 0.

## Nets (as built)

| Net | Pins (per channel) | Role |
|---|---|---|
| `<sig>_IN` | R_TOPn/1 | raw encoder signal — **interface in ← Step 5** |
| `DIVIDER_NODE_n` | R_TOPn/2, R_BOTn/1, C_FILTn/1, TVSn/1 | divided+filtered — **interface out → Step 7** |
| `GND` | R_BOTn/2, C_FILTn/2, TVSn/2 | ground |

## Keypoints (the lesson)

- **10k/20k = 3.33 V, not 2.5 V.** The divider ratio is 20/(10+20) = 2/3, so a 5 V encoder high becomes
  5 × 2/3 = **3.33 V** — right at the 3.3 V logic level (the Schmitt input in Step 7 tolerates it). A
  1:1 divider would waste headroom; this keeps the high level crisp while staying ESP32-safe.
- **R_TOP · C_FILT sets the filter corner.** f = 1/(2π·R·C). With R≈6.67 kΩ (the divider's Thévenin
  resistance) and C_FILT 10 nF, the corner is ~2.4 kHz — wait, use R_TOP for the dominant pole: 10k·10nF
  → ~1.6 kHz visible roll-off; it tames cable-coupled noise and ringing without blunting encoder edges
  (re-sharpened by the Schmitt next stage). Tune C_FILT if your encoder's max edge rate is higher.
- **TVS populated with a flexible THT footprint; exact part TBD.** `TVS1..6` clamp ESD on each divided
  node. The footprint is the roomy axial **`D_DO-201AD_P15.24mm`** — big holes that accept a small DO-15
  body (P6KE) *or* a large DO-201 body (1.5KE) by forming the leads to the 15.24 mm span. Solder whatever
  proper THT TVS you settle on; we'll set the exact value later.
- **Part-selection guide (so you don't reintroduce leakage).** This node sits at **3.33 V** at logic-high,
  so pick a **bidirectional** TVS whose **working voltage V_RWM ≥ ~3.34 V** and clamping stays well under
  the 74HC14's ~3.8 V input max. `1.5KE3.9CA` (V_RWM 3.34 V) is the reviewed-ideal part but is import-only
  in TR. The on-hand **`1.5KE3.3CA`** (from the old 5 V board) *works* — proven on the same 10k/20k divider
  — but its V_RWM is only ~2.82 V, so it lightly clamps/leaks the HIGH (harmless here, the 74HC14 threshold
  is ~2.3 V, but not ideal). Either is fine for a bench build; finalize and update the value when chosen.
- **Replicate, don't redesign.** All six channels are electrically identical; only the input label
  changes. Lay out one, copy it five times, relabel.

## ERC on this isolated sub-circuit

`0 errors, 24 warnings` — all benign:
- 6× *Label connected to only one pin* — the six `*_IN` interface-ins; each merges with its Step 5
  connector pin in the master.
- 18× *Symbol 'R'/'C' doesn't match copy in library 'Device'* — cosmetic library-version mismatch.

TVS1..6 are **populated** (no DNP). Do **not** `snap_to_grid`.

**Footprint:** **`Diode_THT:D_DO-201AD_P15.24mm_Horizontal`** — a flexible large-hole axial pad that takes
either a DO-15 (P6KE-size) or DO-201 (1.5KE-size) body by forming the leads. Keeps the part choice open.

## Copying into your master

1. Build channel 1 fully (R_TOP1, R_BOT1, C_FILT1, TVS1) at the row-1 coordinates, then duplicate the
   block down five times at the listed y-rows.
2. Label each `<sig>_IN` on R_TOPn/1 (merges with Step 5), `DIVIDER_NODE_n` on the tap (R_TOPn/2 +
   R_BOTn/1 + C_FILTn/1 + TVSn/1), `GND` (power symbol) on the bottoms.
3. **Populate** each TVSn (no DNP) on the flexible `D_DO-201AD_P15.24mm` footprint; set the exact value when the THT part is chosen.
4. Carry the six **`DIVIDER_NODE_n`** forward to Step 7.
