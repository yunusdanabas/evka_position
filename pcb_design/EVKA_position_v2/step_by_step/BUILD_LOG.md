# Build log — step-by-step co-build

Append one entry per step (newest at the bottom). Keep it short.

Template:
```
## Step NN — <title> — <YYYY-MM-DD> — <agent/session>
- Built: <what was placed; refdes>
- Step-draft ERC: <N errors / M warnings> (<note benign/floating-net warnings>)
- Deviations from reference: <none | describe>
- Notes for user: <anything to watch when copying into the master>
- Next prompt written: yes/no
```

---

## Step 00 — Workspace scaffold — 2026-06-16 — lead session (Opus 4.8)
- Built: `README.md`, `MASTER_PLAN.md` (9-step spine, refdes/values reconciled to the as-built
  `../EVKA_position_v2.kicad_sch`), this log, `NEXT_STEP_PROMPT.md` (seeded with Step 1).
- User creates their own blank master schematic (recommended: grid 2.54 mm, paper A4/A2, mm).
- Reference schematic: untouched (read-only source of truth).
- Note: reconciled R_MON1/R_MON2 to the as-built **100k/100k** (÷2 for 1S LiPo), not the 120k/27k that
  appears in some 12V-era notes.
- Next prompt written: yes (Step 1).

## Step 01 — Input + reverse-polarity + Schottky-OR (external leg) — 2026-06-16 — Opus 4.8
- Built: `steps/01_input_schottky_or/` (KiCad draft + lesson .md). 7 parts: J4, TVS_BAR, D_BAR, Q_RPP,
  R_RPP, FLG_VEXTRAW, FLG_VEXTPROT. 5 nets via snap-to-pin local labels (no wires needed in this zone):
  V_IN_JACK, V_EXT_RAW, V_EXT_PROT, RPP_GATE, GND. All coords = reference, all on 2.54 grid.
- Step-draft ERC: **0 errors, 2 warnings** — benign: (1) SMAJ5.0A custom symbol's pin pitch is off the
  2.54 grid (body is on grid; inherent to the symbol, also in reference) → do NOT snap_to_grid;
  (2) cosmetic `Device:R` library-copy mismatch.
- Deviations from reference: none electrically. Doc note: MASTER_PLAN prose says TVS shunts `V_EXT_RAW`,
  but the as-built reference clamps **`V_IN_JACK`** (pre-diode); followed the reference and flagged it in
  the lesson.
- Notes for user: snap each net label to its pin (same-name local labels merge → no wires). Carry only
  `V_EXT_PROT` forward to Step 2.
- Next prompt written: yes (Step 2).

## Step 02 — Pi-filter + 5V rail + power LED — 2026-06-18 — Sonnet 4.6
- Built: `steps/02_pi_filter_5v_rail/02_pi_filter_5v_rail.md` (lesson only — no KiCad draft; user
  places directly into master). 10 parts: D_EXT, C_PI, L1, C1, C2, R_LED1, LED1, J6, TP1, FLG_5V.
- Step-draft ERC: n/a (doc-only step).
- Deviations from reference: none. Confirmed D_EXT at 0° has anode on RIGHT (V_EXT_PROT) and cathode
  on LEFT (PI_NODE) — current flows right-to-left through D_EXT, matching the reference label coords.
- Notes for user: R_LED1 bottom → LED1 anode requires a **wire** (no net label; ~28 mm vertical run at
  x=264.16). L1 is rotated 90° — verify pin1/pin2 endpoints before labeling PI_NODE vs. +5V. Do not
  run snap_to_grid.
- Next prompt written: yes (Step 3).

## Step 02 (KiCad draft added) — Pi-filter + 5V rail + power LED — 2026-06-18 — Opus 4.8
- Built: `steps/02_pi_filter_5v_rail/02_pi_filter_5v_rail.kicad_sch` (the doc-only step now has a
  standalone draft) + refreshed lesson (added Footprint column, ERC section). 10 parts: D_EXT, C_PI,
  L1, C1, C2, R_LED1, LED1, J6, TP1, FLG_5V. All coords = reference, on 2.54 grid.
- Step-draft ERC: **0 errors, 5 warnings** — benign: (1) single-pin label `V_EXT_PROT` (interface-in,
  merges with Step 1); (2–5) `L`/`C`/`R`/`LED` library-copy cosmetic mismatch.
- Deviations from reference: none. Correction vs the earlier doc-only lesson: the R_LED1→LED1 anode
  node is a **net label `LED_A`** in the reference (not a bare wire) — draft follows the reference.
- Footprint substitutions (names absent verbatim in this install): L1 →
  `Inductor_THT:L_Radial_D10.0mm_P5.00mm_Neosid_SD12_style3`; TP1 →
  `TestPoint:TestPoint_Keystone_5019_Miniature`; J6 → `…MKDS-1,5-2_1x02_P5.00mm_Horizontal`.
- Notes for user: carry `PI_NODE` + `+5V` forward; do not run snap_to_grid.
- Next prompt written: deferred — all-steps run; final hand-off written after Step 9.

## Step 03 — Charge + boost + load-share (battery leg) — 2026-06-18 — Opus 4.8
- Built: `steps/03_charge_boost_battery/` (draft + lesson). 8 parts: MOD_TP4056, MOD_MT3608, D_BOOST,
  C_BOOST, J5, TP3, TP4, FLG_BATPLUS. no_connect on MOD_TP4056 pins 5/6 (CHRG/STDBY). Coords = reference.
- Step-draft ERC: **0 errors, 4 warnings** — benign: single-pin labels `V_EXT_PROT` (← Step 1) and
  `PI_NODE` (→ Step 2); 2× Conn_01x0x library-copy cosmetic.
- Deviations from reference: none.
- Footprint notes: modules drawn as pin-header stand-ins (1x06 / 1x04 vertical THT). J5 = JST-PH 2.0 mm
  placeholder — verify pitch with calipers before ordering.
- Notes for user: carry `BAT_PLUS` → Step 4; `PI_NODE` merges with Step 2's OR node.
- Next prompt written: deferred (all-steps run).

## Step 04 — Battery voltage ADC monitor — 2026-06-18 — Opus 4.8
- Built: `steps/04_battery_adc_monitor/` (draft + lesson). 3 parts: R_MON1 100k, R_MON2 100k, C_ADC 100nF.
  Coords = reference.
- Step-draft ERC: **0 errors, 4 warnings** — benign: single-pin label `BAT_PLUS` (← Step 3); 3× R/C
  library-copy cosmetic.
- Deviations from reference: none. (Confirms as-built 100k/100k ÷2 — not the 120k/27k from 12V-era notes.)
- Notes for user: carry `ADC_MON` → Step 8 (GPIO1).
- Next prompt written: deferred (all-steps run).

## Step 05 — Encoder connectors + VCC feeds — 2026-06-18 — Opus 4.8
- Built: `steps/05_encoder_connectors/` (draft + lesson). 10 parts: J1, J2, J3a, J3b, J_FB1/2/3 (0R),
  C_VCC1/2/3. no_connect on J3b pin 3 (WIRE_Z). Coords = reference.
- Step-draft ERC: **0 errors, 12 warnings** — benign: 6 single-pin `*_IN` interface-out labels; 6 R/C
  library-copy cosmetic.
- Deviations from reference: none. WIRE_Z carries a net label + no_connect (faithful to reference) — no
  ERC conflict.
- Footprint notes: 4-pin terminal block = `MKDS-1,5-4_1x04_P5.00mm_Horizontal`; J_FBn are 0 Ω jumpers
  (ferrite beads unavailable; resistive bead would brown out the E40S6).
- Notes for user: carry the six `*_IN` → Step 6.
- Next prompt written: deferred (all-steps run).

## Step 06 — Signal-conditioning channel ×6 — 2026-06-18 — Opus 4.8
- Built: `steps/06_signal_conditioning/` (draft + lesson). 24 parts: R_TOP1..6 (10k), R_BOT1..6 (20k),
  C_FILT1..6 (10nF), TVS1..6 (DNP). Coords = reference. 10k/20k → 3.33 V.
- Step-draft ERC: **0 errors, 24 warnings** — benign: 6 single-pin `*_IN` interface-ins; 18 R/C
  library-copy cosmetic.
- Deviations from reference: TVS footprint set (reference left it blank) per PURCHASED_COMPONENTS intent.
- DNP method: hidden property `DNP=yes` per TVS (matches reference; native `(dnp …)` stays no).
  `batch_edit` has no `dnp` field — use `properties:{DNP:yes}`.
- Footprint correction: `Diode_THT:D_DO-15` (in PURCHASED_COMPONENTS) absent → used
  `Diode_THT:D_DO-15_P12.70mm_Horizontal`.
- Notes for user: carry the six `DIVIDER_NODE_n` → Step 7.
- Next prompt written: deferred (all-steps run).

## Step 07 — 74HC14 Schmitt buffer — 2026-06-18 — Opus 4.8
- Built: `steps/07_schmitt_buffer/` (draft + lesson). U_SCHM 74HC14 — all **7 units** placed (u1–u6 gates,
  u7 power) + C_SCHM 100nF. Footprint SOIC-14 (not DIP). Coords = reference.
- Step-draft ERC: **8 errors, 13 warnings** — ALL isolation artifacts, resolve in the assembled master:
  6× "Input pin not driven" @ DIVIDER_NODE_1..6 (Step 6's passive divider drives them in master);
  2× "Input Power pin not driven" @ +3V3/GND (Step 8 sources +3V3, Step 9 adds flags); 12 single-pin
  interface labels + 1 C cosmetic.
- **Build gotcha (important for future steps):** the MCP's multi-unit pin handling is broken —
  `get_schematic_pin_locations` and `componentRef`+`pinNumber` snap ALL units onto unit-1's coords. First
  3 labels via pin-snap stacked at (391.16, 231.14). Fix: place U_SCHM labels by **explicit pin-endpoint
  coordinates** extracted from the reference (inputs x=391.16, outputs x=406.4, per-unit y; VCC@398.78,368.3
  GND@398.78,393.7). Moved the 2 mis-snapped labels, added the rest by position.
- Deviations from reference: none electrically.
- Notes for user: place by coordinate (not multi-unit pin-snap); carry six `*_OUT` → Step 8.
- Next prompt written: deferred (all-steps run).

## Step 08 — ESP32-S3-DevKitC-1 — 2026-06-18 — Opus 4.8
- Built: `steps/08_esp32_devkit/` (draft + lesson). U1 Conn_02x22_Odd_Even stand-in; pins 1–10 + 44 wired
  (+5V, GND, +3V3, ADC_MON, 6×*_OUT, GND); pins 11–43 no_connect (33 via batch). DevKitC-1 GPIO-map text
  note added. Coords = reference.
- Step-draft ERC: **0 errors, 9 warnings** — benign: 9 single-pin interface labels (+5V, +3V3, ADC_MON,
  6×*_OUT); GND multi-pin (2+44) so no warning.
- Deviations from reference: none. U1 footprint left blank (reference does too; `Module:ESP32-S3-DevKitC-1`
  not in this install — assign at PCB stage).
- Notes for user: +3V3 is SOURCED here (board LDO) → powers Step 7; ADC_MON ← Step 4; *_OUT ← Step 7.
- Next prompt written: deferred (all-steps run).

## Step 09 — Test points + power flags + final check — 2026-06-18 — Opus 4.8
- Built: `steps/09_test_points_final/` (draft + lesson). 4 parts: TP2 (3V3), TP5 (GND), FLG_3V3, FLG_GND.
  Coords = reference.
- Step-draft ERC: **0 errors, 0 warnings** — fully clean (both nets flag+TP = 2 pins driven; no passive
  Device:* symbols → no cosmetic warning).
- Deviations from reference: none. These flags close Step 7's isolation power-pin errors in the master.
- Notes for user: one PWR_FLAG per power net drives the whole sheet; run full-master verification.
- Next prompt written: yes — all-steps hand-off (Steps 2–9 ready).

---

### All-steps run complete — 2026-06-18 — Opus 4.8
Steps 2–9 drafts built in one session (Step 1 was already done). Summary:

| Step | Folder | ERC (err/warn) | Notes |
|---|---|---|---|
| 2 | 02_pi_filter_5v_rail | 0 / 5 | KiCad draft added to the doc-only step |
| 3 | 03_charge_boost_battery | 0 / 4 | |
| 4 | 04_battery_adc_monitor | 0 / 4 | |
| 5 | 05_encoder_connectors | 0 / 12 | |
| 6 | 06_signal_conditioning | 0 / 24 | TVS DNP via property; DO-15 footprint fixed |
| 7 | 07_schmitt_buffer | 8 / 13 | 8 errors = isolation artifacts (resolve in master) |
| 8 | 08_esp32_devkit | 0 / 9 | |
| 9 | 09_test_points_final | 0 / 0 | |

All warnings benign (single-pin interface nets + library-copy cosmetic). Step 7's 8 errors are
isolation-only (undriven inputs/power pins) and resolve once neighbours + Step 9 flags are in the master.
Master Design/ and reference EVKA_position_v2.kicad_* untouched.

---

### Master full verification — 2026-06-19 — Opus 4.8
User finished hand-building all 9 steps into `Master Design/EvkaPosition_v2/EvkaPosition_v2.kicad_sch`.
Full check via KiCad netlister (`export_netlist`, authoritative — MCP `get_net_connections` under-reports
module multi-pins). **64 components.**

- **ERC: 2 errors → fixed → 0/0.** Both errors were SnapEDA module **ground** pins typed `Output`:
  `MOD_TP4056/OUT_N` and `MOD_MT3608/VOUT_N` collided on GND with `FLG_GND` (Power output) and each other.
  Fix: changed `(pin output line)` → `(pin passive line)` at lines 4312 (VOUT_N) and 4681 (OUT_N) in the
  embedded `lib_symbols`. ERC reads the embedded copy, so no "Update from Library" needed. (Symbol Editor
  GUI route was blocked — symbol opened read-only.)
- **All 6 encoder channels verified end-to-end:** `Jx → *_IN → R_TOP → DIVIDER_NODE_n {R_BOT+C_FILT+TVS+
  74HC14 gate} → *_OUT → ESP32`. 74HC14 gate pairing correct (one in/one out per gate; no shorted outputs).
- **Battery path verified COMPLETE — earlier "BAT_OUT isolated" worry was WRONG.** TP4056 OUT+ bridges to
  BAT_OUT: `J5→BAT_PLUS→TP4056 BAT+ … TP4056 OUT+→BAT_OUT→MT3608 VIN+→boost→MT3608_OUT→D_BOOST1→PI_NODE`.
  Monitor taps BAT_PLUS (cell voltage). No missing tie.
- **Test points (no TP5/TP6 collision):** TP1=+5V, TP2=3V3, TP3=MT3608_OUT, TP4=BAT_PLUS, TP5=BAT_OUT,
  TP6=GND. (Step 9 lesson text says "TP5=GND" — stale; master correctly uses TP6 for GND.)
- **Informational (not ERC-flagged):** ~28 unused ESP32 GPIOs + RST + USB D± + J4/3 left unconnected
  (passive pins → no warning). Expected; optional NC flags later.

Schematic phase COMPLETE. Next phase: PCB layout.

---

### Flex add-ons Steps 10 & 12 + full re-verification — 2026-06-20 — Opus 4.8
User hand-added two optional expansion sub-circuits to the master, then a stray-wire cleanup pass.
Plan: `FLEX_ADDONS_PLAN.md`. Check via KiCad netlister (`export_netlist`, authoritative). **74 components, 69 nets. ERC 0/0.**

- **Step 10 — Spare GPIO + power breakout (J_EXP1, 2x06):** AUX1–4 → R_AUX1–4 (100R, DNP-capable) →
  ESP32 GPIO11/12/13/14 (U1 J1_17/18/19/20). Header also exposes +5V (pin11), 3V3 (pin9), GND (pins 2/4/6/8/10/12,
  ground-per-signal). Netlist confirms each AUX = [J_EXP1/n, R_AUX/2] and each R_AUX/1 = U1 GPIO. Step 11 (I2C/Qwiic) SKIPPED by user.
- **Step 12 — Two general-purpose buttons (J_SW1, KF301-4P screw terminal):** BTN1/BTN2 each = 10k pull-up
  to 3V3 (R_SW1/2) + 100nF debounce to GND (C_SW1/2) + terminal pin + ESP32 GPIO17/18 (U1 J1_10/J1_11).
  RC ≈ 1ms hardware debounce, active-low. Names made generic (BTN1/BTN2, was SW_HOME/SW_LIMIT) — purpose is
  firmware-defined, repurposable to any slow active-low input. Terminal pinout: 1=GND, 2=BTN1, 3=BTN2, 4=3V3.
  R/C placed on opposite pins from the spec table — harmless (R and non-polar C are symmetric 2-terminal).
- **Stray-wire cleanup:** the add introduced 2 dangling wire endpoints (ERC 2 warnings); user deleted them → ERC 0/0.
  (Note: `find_orphaned_wires` reported 17 — false positives, it can't see symbol pins; ERC is authoritative.)
- **Full master re-verified:** all 6 encoder channels, 74HC14 gate pairing, external-input chain
  (J4→D_BAR1→Q_RPP1→D_EXT1→PI_NODE→L1→+5V), battery path, ADC monitor, all 3 rails — unchanged and intact.
- **U1 pin allocation now:** encoders J1_4..9; ADC J3_4; BTN1/2 = GPIO17/18 (J1_10/11); AUX1–4 = GPIO11–14 (J1_17–20).
  Still free: GPIO8/9/10/21/39/40/41/42/47/48 (+ JTAG/UART/USB if reclaimed).

Schematic + 2 flex add-ons COMPLETE, ERC 0/0. Next phase: PCB layout.
