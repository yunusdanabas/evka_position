# Step 1 — Input + reverse-polarity + Schottky-OR (external leg) · Zone A

The DC barrel-jack input. It takes external 5 V, protects against ESD and reverse polarity, and hands a
clean `V_EXT_PROT` rail to Step 2. This is the **external** leg of the dual-source design — the battery
leg (Step 3) joins later at the OR node (`PI_NODE`, Step 2).

Extracted verbatim from the read-only reference `../../EVKA_position_v2.kicad_sch`.

## ASCII schematic

```
   J4 (Barrel 5.5x2.1)
   centre-positive
   pin1 (+) ───┬───────────── V_IN_JACK ──────── A│  D_BAR  │K ── V_EXT_RAW ──┐
               │                                  (1N5822 Schottky)            │
              ═╪═ TVS_BAR                                                       │
            (SMAJ5.0A)                                              S ┌──────┐  │
               │  clamps V_IN_JACK→GND                  V_EXT_RAW ────┤2     │  │  (S=2)
   pin2 (−) ───┴── GND                                       Q_RPP    │ Q_RPP│◄─┘
                                                          (PJA3441    │ PMOS │
                                                           P-MOSFET)  └──┬─┬─┘
                                                              G=1 ───────┘ │ D=3
                                                                │          └── V_EXT_PROT ──► (Step 2)
                                                             RPP_GATE
                                                                │
                                                          ┌─────┴─────┐
                                                          │  R_RPP    │ 100k
                                                          └─────┬─────┘
                                                                │
                                                               GND

   PWR_FLAG: FLG_VEXTRAW → V_EXT_RAW    FLG_VEXTPROT → V_EXT_PROT
```

Current path (correct polarity): `V_IN_JACK → D_BAR → V_EXT_RAW → Q_RPP (S→D) → V_EXT_PROT`.

## Components

| Refdes | Symbol (lib_id) | Value | `(at x y rot)` |
|---|---|---|---|
| J4 | `Connector:Barrel_Jack` | Barrel_Jack_5.5x2.1 | 30.48, 71.12, 0 |
| TVS_BAR | `SMAJ5.0A:SMAJ5.0A` | SMAJ5.0A | 60.96, 71.12, 180 |
| D_BAR | `Diode:1N5822` | 1N5822 | 88.9, 60.96, 0 |
| Q_RPP | `Transistor_FET:Q_PMOS_GSD` | PJA3441 | 121.92, 60.96, 0 |
| R_RPP | `Device:R` | 100k | 121.92, 88.9, 0 |
| FLG_VEXTRAW | `power:PWR_FLAG` | — | 106.68, 45.72, 0 |
| FLG_VEXTPROT | `power:PWR_FLAG` | — | 147.32, 45.72, 0 |

## Nets (as built — verified by ERC)

| Net | Pins | Role |
|---|---|---|
| `V_IN_JACK` | J4/1, TVS_BAR/1, D_BAR/2(A) | raw jack output, pre-diode |
| `V_EXT_RAW` | D_BAR/1(K), Q_RPP/2(S), FLG_VEXTRAW/1 | after Schottky, before RPP FET |
| `V_EXT_PROT` | Q_RPP/3(D), FLG_VEXTPROT/1 | **interface out → Step 2** |
| `RPP_GATE` | Q_RPP/1(G), R_RPP/1 | P-MOSFET gate |
| `GND` | J4/2, TVS_BAR/2, R_RPP/2 | ground |

## Keypoints (the lesson)

- **Barrel-jack centre-positive.** J4 pin 1 = the centre tip = +; pin 2 = sleeve = GND. Get this wrong
  and reverse-polarity protection is the only thing between you and a dead board.
- **Input-side ESD, *before* the OR.** TVS_BAR (SMAJ5.0A, unidirectional 5 V) sits across the bare jack
  input `V_IN_JACK`→GND, so it clamps hot-plug spikes and ESD the instant they arrive — ahead of the
  diode and the OR node. (MASTER_PLAN's prose says "shunts V_EXT_RAW"; the **as-built reference clamps
  `V_IN_JACK`**, i.e. before D_BAR — followed the reference.)
- **P-MOSFET reverse-polarity protection (low drop).** Q_RPP is a high-side P-FET: source = `V_EXT_RAW`,
  drain = `V_EXT_PROT`, gate pulled to GND through R_RPP (100k). Correct polarity → Vgs negative →
  FET fully on, dropping only `I·Rds(on)` (millivolts). A series diode here would burn ~0.4 V instead.
  Reverse polarity → FET stays off, blocking the fault.
- **Schottky drop sets the rail.** D_BAR (1N5822 Schottky, ~0.4 V Vf) is the external arm of the
  passive Schottky-OR completed in Step 2. Its forward drop is why the rail is called `V_EXT_RAW`
  (raw = post-jack, post-diode) and why the battery boost (Step 3) is set to ~5.3 V so it can share/win.
- `R_RPP` = gate pull-down only — no current in steady state.

## ERC on this isolated sub-circuit

`0 errors, 2 warnings` — both benign:
1. *Symbol pin off connection grid @ (54.102, 71.12)* — the SMAJ5.0A custom symbol's own pin pitch is
   not a 2.54 mm multiple; the **body** is on grid (60.96). Inherent to the symbol, present in the
   reference too. Do **not** `snap_to_grid` to chase it.
2. *Symbol 'R' doesn't match copy in library 'Device'* — cosmetic library-version mismatch, harmless.

No floating-net errors: PWR_FLAGs drive `V_EXT_RAW`/`V_EXT_PROT`. `V_EXT_PROT` legitimately continues
to Step 2.

## Copying into your master

Place all 7 parts at the coordinates above (already on the 2.54 grid except the TVS's internal pin
geometry). Add the 5 local net labels by snapping each to its pin — same-named local labels merge, so
no wires are needed in this zone. Carry `V_EXT_PROT` forward; it is the only net that leaves Step 1.
