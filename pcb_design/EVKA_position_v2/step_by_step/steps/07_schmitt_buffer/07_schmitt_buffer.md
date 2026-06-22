# Step 7 — 74HC14 Schmitt buffer · Zone D

One hex inverting Schmitt-trigger chip cleans up all six encoder signals. After several metres of cable
and an RC filter, the edges arrive soft; the 74HC14's hysteresis snaps them back to clean digital edges
before the MCU's counters see them. Six of the seven schematic units are gates; the seventh carries the
power pins.

Extracted verbatim from the read-only reference `../../EVKA_position_v2.kicad_sch`.

## ASCII schematic

```
   DIVIDER_NODE_1 ─►│1  >o─ 2├─► THETA_A_OUT      U_SCHM = 74HC14 (hex inverting Schmitt)
   DIVIDER_NODE_2 ─►│3  >o─ 4├─► THETA_B_OUT
   DIVIDER_NODE_3 ─►│5  >o─ 6├─► PHI_A_OUT
   DIVIDER_NODE_4 ─►│9  >o─ 8├─► PHI_B_OUT
   DIVIDER_NODE_5 ─►│11 >o─10├─► WIRE_A_OUT
   DIVIDER_NODE_6 ─►│13 >o─12├─► WIRE_B_OUT

   +3V3 ──┤14 (VCC)        C_SCHM 100nF: +3V3 ── GND   (decoupling)
   GND  ──┤7  (GND)
```

`74xx:74HC14` is a **7-unit** symbol: units 1–6 are the gates (one in/one out each), **unit 7** is the
power-only unit exposing pin 14 (VCC) and pin 7 (GND).

## Components

| Refdes | Symbol (lib_id) | Value | `(at x y rot)` | Footprint |
|---|---|---|---|---|
| U_SCHM (u1) | `74xx:74HC14` | 74HC14 | 398.78, 231.14, 0 | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` |
| U_SCHM (u2) | `74xx:74HC14` | 74HC14 | 398.78, 254, 0 | (same part) |
| U_SCHM (u3) | `74xx:74HC14` | 74HC14 | 398.78, 279.4, 0 | (same part) |
| U_SCHM (u4) | `74xx:74HC14` | 74HC14 | 398.78, 304.8, 0 | (same part) |
| U_SCHM (u5) | `74xx:74HC14` | 74HC14 | 398.78, 330.2, 0 | (same part) |
| U_SCHM (u6) | `74xx:74HC14` | 74HC14 | 398.78, 355.6, 0 | (same part) |
| U_SCHM (u7) | `74xx:74HC14` | 74HC14 | 398.78, 381, 0 | (power unit: pins 14/7) |
| C_SCHM | `Device:C` | 100nF | 429.26, 360.68, 0 | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` |

**Footprint = SOIC-14**, not DIP-14 — the purchased part is SMD (per `PURCHASED_COMPONENTS.md`).

## Gate map / nets (as built)

| Unit | In pin → net | Out pin → net | Input label (x,y) | Output label (x,y) |
|---|---|---|---|---|
| 1 | 1 ← DIVIDER_NODE_1 | 2 → THETA_A_OUT | 391.16, 231.14 | 406.4, 231.14 |
| 2 | 3 ← DIVIDER_NODE_2 | 4 → THETA_B_OUT | 391.16, 254 | 406.4, 254 |
| 3 | 5 ← DIVIDER_NODE_3 | 6 → PHI_A_OUT | 391.16, 279.4 | 406.4, 279.4 |
| 4 | 9 ← DIVIDER_NODE_4 | 8 → PHI_B_OUT | 391.16, 304.8 | 406.4, 304.8 |
| 5 | 11 ← DIVIDER_NODE_5 | 10 → WIRE_A_OUT | 391.16, 330.2 | 406.4, 330.2 |
| 6 | 13 ← DIVIDER_NODE_6 | 12 → WIRE_B_OUT | 391.16, 355.6 | 406.4, 355.6 |
| 7 (power) | 14 → +3V3 | 7 → GND | 398.78, 368.3 | 398.78, 393.7 |

`C_SCHM`: pin1 → +3V3 (429.26, 356.87), pin2 → GND (429.26, 364.49).

## Keypoints (the lesson)

- **Schmitt hysteresis re-sharpens edges.** The RC filter (Step 6) and long encoder cable round off the
  signal edges. A plain logic input near its threshold would chatter — multiple counts per real edge.
  The 74HC14's input has two thresholds (V_T+ ≈ 2.0 V, V_T− ≈ 1.1 V at 3.3 V VCC); the gap rejects noise
  and the output flips cleanly only on a real crossing.
- **It INVERTS — firmware compensates.** The 74HC14 is an *inverter*. Each `*_OUT` is the logical inverse
  of its `DIVIDER_NODE_n`. Quadrature direction is preserved as long as A and B invert together, but the
  firmware swaps the A/B pins in the `Encoder` constructors to keep counting sense correct. Don't "fix"
  it in hardware.
- **7-unit symbol — place unit 7 for power.** Units 1–6 are the gates; pins 14 (VCC=+3V3) and 7 (GND)
  live on **unit 7**. You must place unit 7 (here at y=381) or the chip has no power connection.
- **Powered from +3V3, not +5V.** The buffer outputs must be 3.3 V logic for the ESP32, so the chip runs
  on the dev board's 3V3 rail (sourced in Step 8). `C_SCHM` (100 nF) decouples VCC right at the package.
- **Multi-unit label gotcha (build note).** The KiCad MCP's `get_schematic_pin_locations` /
  pin-snap collapses all units onto unit 1's coordinates, so labels were placed by **explicit pin-endpoint
  coordinates** (the table above), not by `componentRef`+`pinNumber`. Verify each label sits on its unit's
  pin before trusting connectivity.

## ERC on this isolated sub-circuit

`8 errors, 13 warnings` — **all are isolation artifacts that vanish in the assembled master:**
- 6× *Input pin not driven by any Output pins* @ DIVIDER_NODE_1..6 — in isolation each Schmitt input is
  the only pin on its net. In the master, Step 6's divider (R/C, passive) joins the net and KiCad counts
  the passive as a driver → no error.
- 2× *Input Power pin not driven by any Output Power pins* @ +3V3 (pin 14) and GND (pin 7) — no power
  driver in isolation. In the master, Step 8's dev-board 3V3 regulator drives +3V3 and Step 9's
  `FLG_3V3`/`FLG_GND` PWR_FLAGs satisfy ERC.
- 13 warnings: 12× *Label connected to only one pin* (the interface nets — `DIVIDER_NODE_n` in, `*_OUT`
  out) + 1× `C` library-copy cosmetic.

These are expected for a stand-alone sub-circuit (see workspace README). Do **not** add stray PWR_FLAGs
or `snap_to_grid` to chase them here — they resolve on assembly.

## Copying into your master

1. Place all **7 units** of U_SCHM (reference `U_SCHM`, units 1–7) at the y-coordinates above, x=398.78.
   Set footprint **SOIC-14** on the part. Place C_SCHM at (429.26, 360.68).
2. Label the 12 gate pins and the 2 power pins at the exact coordinates in the gate-map table (place by
   coordinate, not by multi-unit pin-snap). `DIVIDER_NODE_n` merge with Step 6; `+3V3` with Step 8.
3. Carry the six **`*_OUT`** forward to Step 8 (ESP32 GPIOs). `+3V3` comes *from* Step 8.
