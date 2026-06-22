# Step 9 — Test points + power flags + final check · Zone D

The finishing touches. Two more test points (3V3 and GND) for bench probing, and the two PWR_FLAGs that
let ERC sign off on the `+3V3` and `GND` nets across the whole assembled sheet. Placing these is what
turns the eight isolation-artifact errors in Step 7 into a clean master.

Extracted verbatim from the read-only reference `../../EVKA_position_v2.kicad_sch`.

## ASCII schematic

```
   +3V3 ──┤ TP2 (3V3)          +3V3 ──┤ FLG_3V3  (PWR_FLAG)
    GND ──┤ TP6 (GND)           GND ──┤ FLG_GND  (PWR_FLAG)
```

## Components

| Refdes | Symbol (lib_id) | Value | `(at x y rot)` | Footprint |
|---|---|---|---|---|
| TP2 | `Connector:TestPoint` | 3V3 | 541.02, 248.92, 0 | `TestPoint:TestPoint_Keystone_5019_Miniature` |
| TP6 | `Connector:TestPoint` | GND | 541.02, 269.24, 0 | `TestPoint:TestPoint_Keystone_5019_Miniature` |

> TP6, not TP5 — TP5 is already used for BAT_OUT (Step 3) in the master.
| FLG_3V3 | `power:PWR_FLAG` | — | 424.18, 236.22, 0 | — |
| FLG_GND | `power:PWR_FLAG` | — | 556.26, 289.56, 0 | — |

## Nets (as built)

| Net | Pins | Role |
|---|---|---|
| `+3V3` | TP2/1, FLG_3V3/1 | 3V3 rail test point + ERC driver |
| `GND` | TP6/1, FLG_GND/1 | ground test point + ERC driver |

## Keypoints (the lesson)

- **One PWR_FLAG per power net is enough — for the whole sheet.** `FLG_GND` drives every `GND` pin on the
  board; `FLG_3V3` drives every `+3V3` pin (including the Step 7 74HC14 VCC). PWR_FLAG is a zero-footprint
  ERC token meaning "this net is driven by a source ERC can't otherwise see." `+5V` already has Step 2's
  `FLG_5V`; `BAT_PLUS`/`V_EXT_*` have their own flags in Steps 1/3.
- **This step closes Step 7's errors.** In isolation, Step 7 reported "Input Power pin not driven" on
  +3V3 and GND. With `FLG_3V3` / `FLG_GND` present (and Step 8 sourcing +3V3), those clear — the assembled
  master is 0-error.
- **TP2 / TP6** give you probe-able 3V3 and GND points — handy ground reference for scoping the encoder
  signals and confirming the dev board's regulator is alive.

## ERC on this isolated sub-circuit

`0 errors, 0 warnings` — fully clean. Both nets have a flag **and** a test point (2 pins each, driven),
and there are no passive `Device:*` symbols to raise the cosmetic library-copy warning.

## Copying into your master

1. Place TP2, TP6, FLG_3V3, FLG_GND at the coordinates above.
2. Label `+3V3` on TP2/1 + FLG_3V3/1; `GND` on TP6/1 + FLG_GND/1 (both merge with the existing rails).
3. Run the full-master verification (next section).

## Final verification of the assembled master (all 9 steps in)

After copying Steps 1–9 into your master schematic:
- `run_erc` → **0 errors**. Any residual warnings should only be the cosmetic *Symbol doesn't match copy
  in library* class — document, don't chase.
- `list_schematic_components` → **64 components** in the as-built master (incl. the 7-unit `U_SCHM1`).
- Spot-check the signal chain end to end: `*_IN → DIVIDER_NODE_n → U_SCHM → *_OUT → U1` for each of the 6
  channels; plus `+5V`, `GND`, `+3V3`, `BAT_PLUS`, `ADC_MON`.
- `export_schematic_pdf` / `svg` and eyeball the 4 zones.
