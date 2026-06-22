# Master plan — 5V v2 schematic, 9-step co-build

The build spine. Each step is one teachable sub-circuit, extracted from the reference
`../EVKA_position_v2.kicad_sch` (read-only source of truth). Refdes and values below are **as-built** in
that file — verify against it, don't re-derive. Authoritative design source for rationale:
`../docs/KICAD_PLAN_DETAILED.md` (Appendix A = BOM, Appendix C = nets); ASCII overview in
`../docs/circuit_schematic.md`.

**Interface nets** are the named wires that cross between steps — when you place a step into the master,
these are the labels that must match an earlier (or later) step so the sub-circuits connect.

Channel order for the 6 encoder signals (used in steps 5–8): `n = 1..6 =`
**THETA_A, THETA_B, PHI_A, PHI_B, WIRE_A, WIRE_B**.

---

## Step 1 — Input + reverse-polarity + Schottky-OR (external leg) · Zone A

| Refdes | Symbol | Value |
|---|---|---|
| J4 | Connector:Barrel_Jack | Barrel_Jack_5.5x2.1 |
| TVS_BAR | SMAJ5.0A:SMAJ5.0A | SMAJ5.0A |
| D_BAR | Diode:1N5822 | 1N5822 |
| Q_RPP | Transistor_FET:Q_PMOS_GSD | PJA3441 |
| R_RPP | Device:R | 100k |

- **Chain:** J4 (+5 V in) → D_BAR → `V_EXT_RAW` → Q_RPP (P-MOSFET RPP) → `V_EXT_PROT`. TVS_BAR shunts
  `V_EXT_RAW` to GND (ESD, *before* the OR). R_RPP = gate pull for Q_RPP.
- **Interface out:** `V_EXT_PROT` (→ Step 2). **PWR_FLAG:** `FLG_VEXTRAW`, `FLG_VEXTPROT`.
- **Keypoints:** barrel-jack centre-positive polarity; SMAJ5.0A clamps hot-plug/ESD on the input side
  before the OR-ing diode; P-MOSFET reverse-polarity protection (low drop vs a series diode);
  Schottky D_BAR forward drop sets `V_EXT_RAW`.

## Step 2 — Pi-filter + 5 V rail + power LED · Zone A

| Refdes | Symbol | Value |
|---|---|---|
| D_EXT | Diode:1N5822 | 1N5822 |
| C_PI | Device:C_Polarized | 10uF/10V |
| L1 | Device:L | 10uH |
| C1 | Device:C_Polarized | 220uF/10V |
| C2 | Device:C | 100nF |
| R_LED1 | Device:R | 1k |
| LED1 | Device:LED | Green |
| J6 | Connector:Screw_Terminal_01x02 | BENCH_5V |
| TP1 | Connector:TestPoint | 5V_RAIL |

- **Chain:** `V_EXT_PROT` → D_EXT → `PI_NODE`; `PI_NODE` → C_PI → L1 → C1 ∥ C2 → `+5V`. The battery boost
  leg (Step 3, D_BOOST) also feeds `PI_NODE` — this is the **passive Schottky-OR** node. R_LED1+LED1 =
  power-on indicator off `+5V`; J6 = bench 5 V breakout; TP1 = 5 V test point.
- **Interface in:** `V_EXT_PROT` (Step 1), `PI_NODE` (shared w/ Step 3). **out:** `+5V` (→ Steps 5, 8).
  **PWR_FLAG:** `FLG_5V`.
- **Keypoints:** π-filter (C-L-C) knocks down MT3608 switching ripple before the 5 V rail; the OR happens
  at `PI_NODE`, external leg = D_EXT; whichever source is higher supplies the rail.

## Step 3 — Charge + boost + load-share (battery leg) · Zone B

| Refdes | Symbol | Value |
|---|---|---|
| MOD_TP4056 | Connector_Generic:Conn_01x06 | TP4056 |
| MOD_MT3608 | Connector_Generic:Conn_01x04 | MT3608 5V0 |
| D_BOOST | Diode:1N5822 | 1N5822 |
| C_BOOST | Device:C_Polarized | 22uF/10V |
| J5 | Connector_Generic:Conn_01x02 | LiPo 1S |
| TP3 | Connector:TestPoint | MT3608_OUT |
| TP4 | Connector:TestPoint | BAT+ |

- **Nets:** J5 = LiPo → `BAT_PLUS`. MOD_TP4056 charges `BAT_PLUS` (pin map per reference). MOD_MT3608
  boosts `BAT_PLUS` → `MT3608_OUT` (≈5.3 V); C_BOOST on `MT3608_OUT`; D_BOOST: `MT3608_OUT` → `PI_NODE`
  (battery OR leg).
- **Interface out:** `BAT_PLUS` (→ Step 4), `PI_NODE` (→ Step 2 via D_BOOST). **PWR_FLAG:** `FLG_BATPLUS`.
- **Keypoints:** **external charging only** (TP4056 + DW01A module); MT3608 boosted to ~5.3 V so that
  after D_BOOST's drop it still beats / shares with the 5 V external leg; passive Schottky-OR (no active
  load-share IC in this as-built rev).

## Step 4 — Battery voltage ADC monitor · Zone B

| Refdes | Symbol | Value |
|---|---|---|
| R_MON1 | Device:R | 100k |
| R_MON2 | Device:R | 100k |
| C_ADC | Device:C | 100nF |

- **Nets:** `BAT_PLUS` → R_MON1 → `ADC_MON` → R_MON2 → GND; C_ADC on `ADC_MON` to GND.
- **Interface in:** `BAT_PLUS` (Step 3). **out:** `ADC_MON` (→ Step 8, GPIO1).
- **Keypoints:** 100k/100k = ÷2 → a 1S LiPo (≤4.2 V) reads ≤2.1 V, safe for the 3.3 V ADC; 100 nF bypass
  filters ADC sampling noise; firmware thresholds live in `SphericalSensor.h`.

## Step 5 — Encoder connectors + VCC feeds · Zone C

| Refdes | Symbol | Value | Pins |
|---|---|---|---|
| J1 | Connector:Screw_Terminal_01x04 | THETA | 1:GND 2:ENC_VCC1 3:THETA_A_IN 4:THETA_B_IN |
| J2 | Connector:Screw_Terminal_01x04 | PHI | 1:GND 2:ENC_VCC2 3:PHI_A_IN 4:PHI_B_IN |
| J3 | Connector:Screw_Terminal_01x04 | WIRE | 1:GND 2:ENC_VCC3 3:WIRE_A_IN 4:WIRE_B_IN |
| J_FB1/2/3 | Device:R | 0R | `+5V` → ENC_VCC1/2/3 |
| C_VCC1/2/3 | Device:C | 100nF | ENC_VCCn → GND |

- **Interface in:** `+5V` (Step 2). **out:** `ENC_VCC1/2/3` (encoder power), and the raw `*_IN` signals
  (THETA_A_IN … WIRE_B_IN) → Step 6. Wire encoder uses a single 4-pin J3 (Z/index unused — not wired).
- **Keypoints:** screw-terminal pinout per encoder; `J_FBn` are **0 Ω jumpers** (ferrite beads were
  unavailable domestically — a resistive bead would brown out the E40S6); `C_VCCn` = per-encoder decoupling.

## Step 6 — Signal-conditioning channel ×6 · Zone C

Per channel `n = 1..6`:

| Refdes | Symbol | Value |
|---|---|---|
| R_TOPn | Device:R | 10k |
| R_BOTn | Device:R | 20k |
| C_FILTn | Device:C | 10nF |
| TVSn | Device:D_TVS | TVS 3.3V (THT-TBD) — **populate** |

- **Net (each):** `<sig>_IN` → R_TOPn → `DIVIDER_NODE_n` → R_BOTn → GND; C_FILTn and TVSn on
  `DIVIDER_NODE_n` to GND. (`<sig>` = THETA_A, THETA_B, PHI_A, PHI_B, WIRE_A, WIRE_B for n=1..6.)
- **Interface in:** `*_IN` (Step 5). **out:** `DIVIDER_NODE_1..6` (→ Step 7).
- **Keypoints:** build **one channel fully**, then replicate ×6; 10k/20k divides the 5 V encoder output to
  5 × 20/30 = **3.33 V** (safe for 3.3 V logic); R_TOP·C_FILT sets the noise-filter corner; the TVS
  footprints are **populated** with a general THT TVS on a flexible large-axial footprint
  (`Diode_THT:D_DO-201AD_P15.24mm_Horizontal`) — exact part TBD (pick bidirectional, V_RWM ≥ ~3.34 V;
  on-hand 1.5KE3.3CA works but leaks slightly).

## Step 7 — 74HC14 Schmitt buffer · Zone D

| Refdes | Symbol | Value |
|---|---|---|
| U_SCHM | 74xx:74HC14 (7-unit) | 74HC14 | **SOIC-14** (`Package_SO:SOIC-14_3.9x8.7mm_P1.27mm`) — purchased part, not DIP |
| C_SCHM | Device:C | 100nF |

Gate map (extract pin coords from the reference):

| Gate | In pin → net | Out pin → net |
|---|---|---|
| 1 | 1 ← DIVIDER_NODE_1 | 2 → THETA_A_OUT |
| 2 | 3 ← DIVIDER_NODE_2 | 4 → THETA_B_OUT |
| 3 | 5 ← DIVIDER_NODE_3 | 6 → PHI_A_OUT |
| 4 | 9 ← DIVIDER_NODE_4 | 8 → PHI_B_OUT |
| 5 | 11 ← DIVIDER_NODE_5 | 10 → WIRE_A_OUT |
| 6 | 13 ← DIVIDER_NODE_6 | 12 → WIRE_B_OUT |
| power (unit 7) | 14 → `+3V3` | 7 → GND |

- **Interface in:** `DIVIDER_NODE_1..6` (Step 6), `+3V3` (Step 8). **out:** `*_OUT` ×6 (→ Step 8).
  C_SCHM = `+3V3`→GND decoupling.
- **Keypoints:** Schmitt hysteresis re-sharpens edges softened by cable capacitance + the RC filter; the
  74HC14 **inverts**, so firmware swaps A/B in the `Encoder` constructors; it's a **7-unit** symbol —
  place unit 7 to expose power pins 7/14. **Footprint = SOIC-14** per `PURCHASED_COMPONENTS.md`.

## Step 8 — ESP32-S3-DevKitC-1 · Zone D

| Refdes | Symbol | Value |
|---|---|---|
| U1 | Connector_Generic:Conn_02x22_Odd_Even | ESP32-S3-DevKitC-1 (stand-in) |

GPIO map (the six `*_OUT` from Step 7 + the ADC):

| Net | GPIO |
|---|---|
| THETA_A_OUT | 4 |
| THETA_B_OUT | 5 |
| PHI_A_OUT | 6 |
| PHI_B_OUT | 7 |
| WIRE_A_OUT | 15 |
| WIRE_B_OUT | 16 |
| ADC_MON | 1 |

- **Interface in:** `+5V` (Step 2), `ADC_MON` (Step 4), `*_OUT` ×6 (Step 7). **out (source):** `+3V3`
  (dev board → powers Step 7's 74HC14), `GND`.
- **Keypoints:** U1 is a generic 2×22 **stand-in** for the DevKitC-1 (swap for a real symbol at PCB stage);
  the dev board's 3V3 regulator sources `+3V3`; note reserved pins (strapping 0/3/45/46, USB, PSRAM,
  UART, onboard WS2812 on GPIO38) so no signal lands on them.

## Step 9 — Test points + power flags + final check

| Refdes | Symbol | Value |
|---|---|---|
| TP2 | Connector:TestPoint | 3V3 |
| TP5 | Connector:TestPoint | GND |
| FLG_3V3 | power:PWR_FLAG | on `+3V3` |
| FLG_GND | power:PWR_FLAG | on `GND` |

- **Finalize:** TP2 on `+3V3`, TP5 on `GND`; PWR_FLAG on `+3V3` and `GND`.
- **Verify the assembled master:** `run_erc` → **0 errors** (document any residual cosmetic warnings);
  `list_schematic_components` count ≈ reference (75 incl. the 7 U_SCHM units); `export_schematic_pdf/svg`;
  spot-check nets `+5V`, `GND`, `+3V3`, `BAT_PLUS`, `ADC_MON`, and each `DIVIDER_NODE_n → *_OUT → GPIO`.

---

### Interface-net summary (what bridges the steps)

```
Step1 ─V_EXT_PROT→ Step2 ─+5V→ Step5, Step8
Step3 ─BAT_PLUS→ Step4 ─ADC_MON→ Step8
Step3 ─PI_NODE(D_BOOST)→ Step2     (passive OR with Step1's D_EXT)
Step5 ─*_IN→ Step6 ─DIVIDER_NODE_1..6→ Step7 ─*_OUT→ Step8
Step8 ─+3V3→ Step7        GND: everywhere
```
