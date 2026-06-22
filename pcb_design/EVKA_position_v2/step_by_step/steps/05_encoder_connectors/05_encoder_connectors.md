# Step 5 — Encoder connectors + VCC feeds · Zone C

Where the three encoders plug in. Screw terminals bring in each encoder's GND, VCC, and two quadrature
signals; a 0 Ω jumper feeds clean 5 V to each encoder, decoupled at the connector. The raw `*_IN`
signals leave here for the dividers in Step 6.

Channel order: n=1..6 = THETA_A, THETA_B, PHI_A, PHI_B, WIRE_A, WIRE_B.
Based on the read-only reference `../../EVKA_position_v2.kicad_sch`, with one **as-built change (2026-06-19)**.

> **Master deviation — single 4-pin J3.** The reference splits the wire encoder across `J3a` (2-pin power)
> + `J3b` (3-pin signal, incl. unused `WIRE_Z`). The draw-wire encoder's Z/index line is **not used**, so
> the master uses **one 4-pin terminal `J3`** (GND, VCC, A, B) — identical to J1/J2. This drops `J3b`, the
> `WIRE_Z` net, and its no-connect. Saves a connector and uses the same KF301-4P / MKDS-1,5-4 block as the
> rotaries.

## ASCII schematic

```
            +5V                                       +5V
             │                                         │
   J_FB1 (0R)│              J_FB2 (0R)                 │   J_FB3 (0R)
       ┌──[ ]──┐                ┌──[ ]──┐                  ┌──[ ]──┐
       │       │                │       │                  │       │
   ENC_VCC1   ...           ENC_VCC2   ...             ENC_VCC3   ...
       │                        │                          │
   J1 (THETA) 01x04         J2 (PHI) 01x04             J3 (WIRE) 01x04
   1 GND                    1 GND                      1 GND
   2 ENC_VCC1 ──┬── C_VCC1  2 ENC_VCC2 ──┬── C_VCC2    2 ENC_VCC3 ──┬── C_VCC3
   3 THETA_A_IN │  100nF    3 PHI_A_IN   │  100nF      3 WIRE_A_IN  │  100nF
   4 THETA_B_IN GND         4 PHI_B_IN   GND           4 WIRE_B_IN  GND

   (wire encoder Z/index line: not wired — leave it off the terminal)
```

Each `J_FBn`: `+5V → ENC_VCCn`. Each `C_VCCn`: `ENC_VCCn → GND`.

## Components

| Refdes | Symbol (lib_id) | Value | `(at x y rot)` | Footprint | Pins |
|---|---|---|---|---|---|
| J1 | `Connector:Screw_Terminal_01x04` | THETA | 30.48, 238.76, 0 | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-4_1x04_P5.00mm_Horizontal` | 1:GND 2:ENC_VCC1 3:THETA_A_IN 4:THETA_B_IN |
| J2 | `Connector:Screw_Terminal_01x04` | PHI | 30.48, 299.72, 0 | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-4_1x04_P5.00mm_Horizontal` | 1:GND 2:ENC_VCC2 3:PHI_A_IN 4:PHI_B_IN |
| J3 | `Connector:Screw_Terminal_01x04` | WIRE | 30.48, 360.68, 0 | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-4_1x04_P5.00mm_Horizontal` | 1:GND 2:ENC_VCC3 3:WIRE_A_IN 4:WIRE_B_IN |
| J_FB1 | `Device:R` | 0R | 71.12, 236.22, 90 | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | 1:+5V 2:ENC_VCC1 |
| J_FB2 | `Device:R` | 0R | 71.12, 294.64, 90 | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | 1:+5V 2:ENC_VCC2 |
| J_FB3 | `Device:R` | 0R | 71.12, 350.52, 90 | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | 1:+5V 2:ENC_VCC3 |
| C_VCC1 | `Device:C` | 100nF | 88.9, 248.92, 0 | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | 1:ENC_VCC1 2:GND |
| C_VCC2 | `Device:C` | 100nF | 88.9, 309.88, 0 | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | 1:ENC_VCC2 2:GND |
| C_VCC3 | `Device:C` | 100nF | 88.9, 365.76, 0 | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | 1:ENC_VCC3 2:GND |

## Nets (as built)

| Net | Pins | Role |
|---|---|---|
| `+5V` | J_FB1/1, J_FB2/1, J_FB3/1 | rail in ← Step 2 |
| `ENC_VCC1/2/3` | J_FBn/2, C_VCCn/1, Jx/2 | per-encoder switched 5 V (out: encoders) |
| `THETA_A_IN`…`WIRE_B_IN` | J1/3,4 · J2/3,4 · J3/3,4 | raw signals — **interface out → Step 6** (×6) |
| `GND` | J1/1, J2/1, J3/1, C_VCCn/2 | ground |

## Keypoints (the lesson)

- **`J_FBn` are 0 Ω jumpers, not ferrite beads.** The original design wanted ferrite beads on each
  encoder VCC, but they were unavailable domestically — and a resistive bead's DCR would brown out the
  E40S6 rotary encoders (they pull real current). A 0 Ω jumper keeps the footprint (drop in a bead later
  if EMI demands it) without the voltage drop.
- **Per-encoder decoupling.** `C_VCCn` (100 nF) sits right at each connector so each encoder gets a local
  charge reservoir — important with several metres of encoder cable between board and sensor.
- **All three connectors are identical 4-pin (GND, VCC, A, B).** J1/J2/J3 are the same KF301-4P /
  MKDS-1,5-4 block. The wire encoder fits a 4-pin like the rotaries because its Z/index line is unused.
- **Z/index line dropped.** The draw-wire encoder exposes a Z/index output this design doesn't read, so it
  is simply not wired to the terminal — no `WIRE_Z` net, no spare pin, no no-connect needed. (The earlier
  reference used a 2-pin + 3-pin pair with `WIRE_Z` no-connect; collapsing to one 4-pin removes that.)

## ERC on this isolated sub-circuit

`0 errors, 12 warnings` — all benign:
1–6. *Label connected to only one pin* @ the six `*_IN` nets — these are interface-outs; each merges
   with its Step 6 divider once both are in the master.
7–12. *Symbol 'R'/'C' doesn't match copy in library 'Device'* — cosmetic (J_FB1–3, C_VCC1–3).

`ENC_VCC1/2/3`, `+5V`, `GND` are multi-pin → no single-pin warning. No `WIRE_Z` no-connect any more (the
Z line is simply absent). Do **not** `snap_to_grid`.

## Copying into your master

1. Place all 9 parts at the coordinates above (2.54 grid). Note J_FB1–3 are rotated 90°.
2. Label `+5V` on each J_FBn/1 (merges with Step 2), `ENC_VCCn` on each J_FBn/2 + C_VCCn/1 + Jx/2,
   the six `*_IN` on the connector signal pins, `GND` (power symbol) on the GND pins.
3. Carry the six **`*_IN`** signals forward to Step 6. (No no-connect needed — Z line is not on the board.)
