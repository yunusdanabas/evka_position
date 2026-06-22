# ALL STEP DRAFTS READY → copy Steps 2–9 into your master

> The step-by-step build is fully drafted. There is no "next step to generate" — this file is now a
> **hand-off for you** (the human) to copy each sub-circuit into your master KiCad project by hand,
> checking against the drafts. Step 1 is already in your master.

---

## State

| Step | Folder (`steps/…`) | Draft | ERC (err/warn) | In your master? |
|---|---|---|---|---|
| 1 | `01_input_schottky_or` | ✔ | 0 / 2 | **Yes** (done earlier) |
| 2 | `02_pi_filter_5v_rail` | ✔ + lesson | 0 / 5 | No — copy it |
| 3 | `03_charge_boost_battery` | ✔ | 0 / 4 | No |
| 4 | `04_battery_adc_monitor` | ✔ | 0 / 4 | No |
| 5 | `05_encoder_connectors` | ✔ | 0 / 12 | No |
| 6 | `06_signal_conditioning` | ✔ | 0 / 24 | No |
| 7 | `07_schmitt_buffer` | ✔ | 8 / 13 | No |
| 8 | `08_esp32_devkit` | ✔ | 0 / 9 | No |
| 9 | `09_test_points_final` | ✔ | 0 / 0 | No |

Each `steps/NN_*/` has a standalone openable `.kicad_sch` draft + an `NN_*.md` lesson (ASCII schematic,
component table **with footprints**, net table, keypoints, ERC notes, copy instructions). Full per-step
history is in `BUILD_LOG.md`.

## How to use these

For each step, open its `.kicad_sch` draft beside your master, read the lesson `.md`, then place the
parts in your master at the listed coordinates (2.54 mm grid) and add the net labels. The lesson's
"Copying into your master" section is the checklist. **Do not run `snap_to_grid`** (detaches labels).

## What's benign vs. what to watch

- **All warnings are benign:** *Label connected to only one pin* (interface nets that merge with their
  neighbour step once both are placed) and *Symbol doesn't match copy in library* (cosmetic).
- **Step 7's 8 ERC errors are isolation-only** — undriven Schmitt inputs (driven by Step 6's divider in
  the master) and undriven +3V3/GND power pins (sourced by Step 8, flagged by Step 9). They disappear in
  the assembled master.

## Deviations / corrections to know while copying

- **Step 2** node `LED_A`: reference ties R_LED1→LED1 anode with a **net label `LED_A`**, not a bare wire
  (a wire is electrically equivalent if you prefer).
- **Step 3** battery node split (as-built master, 2026-06-19): the booster input is on its own net
  **`BAT_OUT`** (+ `TP5`), not `BAT_PLUS`. They are the same node electrically and **must be tied** — in
  the current master the tie is **missing**, so the MT3608 input floats and the battery can't drive the
  rail. Fix: wire `BAT_OUT` ↔ `BAT_PLUS`. The Step 4 ADC stays on `BAT_PLUS` (raw cell). Details in the
  updated `steps/03_charge_boost_battery/03_charge_boost_battery.md`.
- **Step 5** wire-encoder connector (as-built master, 2026-06-19): collapsed from `J3a` (2-pin) + `J3b`
  (3-pin) to a **single 4-pin `J3`** (GND/VCC/A/B), because the encoder's Z/index line is unused. No
  `WIRE_Z` net, no no-connect. J3 uses the same KF301-4P / MKDS-1,5-4 block as J1/J2.
- **Step 6** TVS1–6 are **populated** (decision 2026-06-19) with a general THT TVS on a flexible
  large-axial footprint `Diode_THT:D_DO-201AD_P15.24mm_Horizontal` — exact part **TBD** (pick
  bidirectional, V_RWM ≥ ~3.34 V; old-board 1.5KE3.3CA fits and works but leaks slightly at the 3.33 V
  HIGH). No DNP. The wrongly-ordered P6KE39CA (33 V) is not used.
- **Step 7** U_SCHM labels were placed by **explicit pin-endpoint coordinates** — the KiCad MCP's
  multi-unit pin-snap collapses all 7 units onto unit 1's coords. Place by coordinate, verify each label
  sits on its unit's pin.
- **Step 8** U1 footprint left **blank** (stand-in; `Module:ESP32-S3-DevKitC-1` not installed — assign at
  PCB stage). Real GPIO map is in the text note beside U1.
- **Footprint substitutions** (names in `PURCHASED_COMPONENTS.md` absent verbatim in this install):
  L1 → `Inductor_THT:L_Radial_D10.0mm_P5.00mm_Neosid_SD12_style3`;
  TestPoints → `TestPoint:TestPoint_Keystone_5019_Miniature`;
  2-pin terminal → `…MKDS-1,5-2_1x02_P5.00mm_Horizontal`;
  TVS → `Diode_THT:D_DO-201AD_P15.24mm_Horizontal` (flexible large-axial; takes DO-15 or DO-201 bodies).
  Verify J5 (JST) pitch and L1 diameter against the physical parts before ordering.

## After all 9 are in the master

Run the final verification from `steps/09_test_points_final/09_test_points_final.md`: `run_erc` →
0 errors; `list_schematic_components` ≈ 75 symbols (incl. 7 U_SCHM units); spot-check the
`*_IN → DIVIDER_NODE_n → U_SCHM → *_OUT → U1` chain ×6 plus the power rails; export PDF/SVG.
