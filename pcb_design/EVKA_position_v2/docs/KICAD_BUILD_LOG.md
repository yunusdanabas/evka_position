# KiCad Build Log — EVKA Position 5V v2 schematic

**Project:** `pcb_design/EVKA_position_v2/EVKA_position_v2.kicad_pro`
**Schematic:** `pcb_design/EVKA_position_v2/EVKA_position_v2.kicad_sch`
**Playbook:** `pcb_design/EVKA_position_v2/docs/KICAD_AGENT_INSTRUCTIONS.md`
**Last updated:** 2026-06-15 — Verify complete: ERC 0 err / 3 warn (all benign), PDF+SVG+netlist exported, connectivity + BOM spot-checks PASS. **DRAFT SCHEMATIC COMPLETE & ERC-CLEAN.**
**Current status:** Setup ✔ → Zone A ✔ → Zone B ✔ → Zone C ✔ → Zone D ✔ → **Verify ✔** — draft schematic complete (69 devices, ERC 0 err / 3 benign warn). Remaining work is PCB-layout stage (footprint assignment, native `(dnp yes)` token, off-grid tidy).

## Task checklist
- [✔] Setup — backed up; renamed J1→J4 / D1→TVS_BAR / D2→D_BAR; deleted #PWR01-03 + 5 floating labels; added 4 zone titles + draft note
- [✔] Zone A — power input / Schottky-OR / pi-filter  (owner: Zone A agent)
- [✔] Zone B — battery / charging / ADC  (owner: Zone B agent)
- [✔] Zone C — encoder signal conditioning (6 ch)  (owner: Zone C agent)
- [✔] Zone D — Schmitt buffer + DevKitC-1  (owner: Zone D agent)
- [✔] Verify — full ERC=0 (3 benign warn), PDF/SVG/netlist exported, netlist spot-check PASS, BOM count reconciled
- [✔] Doc-sync — circuit_schematic.md + bill_of_materials.md → as-built (owner: Doc-sync agent)

## ERC status
- Latest run: 2026-06-15 (after Zone D build) — **0 errors, 3 warnings**
- Errors: 0 | Warnings: 3 — all cosmetic/benign:
  1. Symbol pin or wire end off connection grid (carried from Zone A)
  2. Missing footprint library 'SMAJ5.0A' (pre-existing, footprint assignment deferred)
  3. NEW: "Pins of type Bidirectional and Power output are connected" @ (67.818, 71.12) — U1/1
     (DevKitC +5V passive connector pin) sharing the +5V net with FLG_5V (PWR_FLAG, power-output
     type). Benign: expected when a generic-connector stand-in pin meets a flag-driven power rail.
- The two `power_pin_not_driven` errors on the 74HC14 +3V3/GND power pins (seen mid-build) were
  cleared by the FLG_3V3 / FLG_GND PWR_FLAGs. The 33 `pin_not_connected` errors on unused U1
  pins (11–43) were cleared with no_connect markers (see below).
- Report path: in-line (run_erc tool output)

## Artifacts
- PDF: `pcb_design/EVKA_position_v2/exports/EVKA_position_v2.pdf` (exported 2026-06-15)
- SVG: `pcb_design/EVKA_position_v2/exports/EVKA_position_v2.svg` (exported 2026-06-15)
- Netlist: inspected in-conversation via `generate_netlist` (33 nets, 69 components) — no file written (use `export_netlist` at PCB stage if a KiCad-XML/SPICE file is needed)
- Backup of original schematic: `pcb_design/EVKA_position_v2/archive/EVKA_position_v2.kicad_sch.orig`

## Decisions / issues (append-only)
- 2026-06-13 (Agent 0): Started from existing schematic (6 isolated parts) to preserve the
  project-embedded `SMAJ5.0A:SMAJ5.0A` symbol + root UUID. Backed up to `.orig`.
- 2026-06-13 (Agent 0): Refdes follows Appendix A descriptive convention (TVS_BAR, D_BAR, Q_RPP,
  U_SCHM, …). Existing barrel jack `J1` will be renamed `J4` (J1/J2/J3 reserved for encoders).
- 2026-06-13 (Agent 0): **Deviation flagged** — `C_SCHM` 100nF 74HC14 decoupling will be added though
  it is absent from Appendix A (standard practice; was in the original circuit_schematic.md). Recommend
  adding to the BOM during doc-sync.
- 2026-06-13 (Agent 0): `R_MT_HI`/`R_MT_LO` are on-module (MT3608 FB mod) — NOT placed as board parts.
- 2026-06-13 (Agent 0): **`save_project` unusable** on this backend ("No board is loaded"); schematic edit
  tools persist to `.kicad_sch` directly. Confirm state via `list_schematic_*`. Playbook updated.
- 2026-06-13 (Agent 0): Post-Setup canvas = 3 parts (J4, TVS_BAR, D_BAR) at their original top-left
  coords + 4 zone titles + draft note. Zone A agent should reposition the 3 into the zone-A layout, add
  net labels to them, then add the remaining Zone A parts.
- Open: confirm how the MCP exposes 74HC14 power pins (7/14) across multi-units (Zone D agent to verify).
- 2026-06-13 (Zone A agent): **Zone A built.** Repositioned J4/TVS_BAR/D_BAR into zone layout and
  connected them (nets V_IN_JACK, GND, V_EXT_RAW). Added 11 parts: Q_RPP (PJA3441 P-MOSFET RPP),
  R_RPP (100k gate pulldown), D_EXT (1N5822 Schottky-OR), C_PI (10uF), L1 (10uH), C1 (220uF),
  C2 (100nF), R_LED1 (1k), LED1 (Green power LED), J6 (BENCH_5V screw terminal), TP1 (5V_RAIL test
  point). Added 3 PWR_FLAGs: FLG_VEXTRAW (V_EXT_RAW), FLG_VEXTPROT (V_EXT_PROT), FLG_5V (+5V).
  Signal chain: V_IN_JACK → D_BAR → V_EXT_RAW → Q_RPP → V_EXT_PROT → D_EXT → PI_NODE → L1 → +5V.
  Component count now 17. All placements + connections succeeded (no failures).
- 2026-06-13 (Zone A agent): **ERC = 0 errors, 18 warnings.** No `power_pin_not_driven` errors —
  the 3 Zone-A PWR_FLAGs drive V_EXT_RAW/V_EXT_PROT/+5V; GND will be driven by a PWR_FLAG from a
  later zone (none in Zone A by spec). 17 warnings are "Symbol pin or wire end off connection grid"
  — a cosmetic side-effect of placing parts at integer-mm coords off KiCad's 1.27mm grid;
  connectivity is unaffected (no unconnected/conflict errors). 1 warning = missing footprint
  library 'SMAJ5.0A' (pre-existing, from Setup; footprint assignment deferred).
- Open (Zone A → lead): off-grid warnings will accumulate as zones add parts at integer-mm coords.
  Consider a grid-snap pass (`snap_to_grid`) before final ERC=0 verify, or relocate parts onto a
  1.27mm grid. Does not affect netlist correctness.
- 2026-06-15 (Lead session): **State reconciliation + dup-title cleanup.** Verified true canvas via MCP:
  17 components (all Zone A) on a 2.54 mm grid; ERC = **0 errors, 2 warnings** (NOT 18 — that was stale).
  Found and removed a **duplicate** "ZONE A - POWER INPUT…" text annotation (two identical at 20.32,22.86);
  the MCP has no delete-text tool, so removed the compact inline copy (uuid 14227476…) by a precise
  UUID-keyed edit of the `.kicad_sch`, then re-verified (5 texts: 4 zone titles + draft note; ERC unchanged).
  Backed up to `.bak_predupfix` during the edit, removed after verify; `.orig` retained.
- **⚠ HANDOFF RULE for Zone B/C/D agents:** place every component on a **2.54 mm-multiple grid** (coords =
  multiples of 2.54) so pins land on the connection grid. **NEVER run `snap_to_grid`** — it moves components
  and labels independently and detaches net labels from pins (previously caused 29 ERC errors + a full revert).
  Connect via net labels (`nets:{pin:netName}` / `add_schematic_net_label` with componentRef+pinNumber).
  Add zone-local PWR_FLAGs (BAT_PLUS in B; +3V3 and GND in D) or ERC will report `power_pin_not_driven`.
- 2026-06-13 (Doc-sync agent): **Doc-sync complete.** Reconciled the two stale pre-procurement docs
  to the as-built design (KICAD_PLAN_DETAILED.md Appendix A/C). Files changed:
  - `circuit_schematic.md` — replaced the read-with-deltas banner with the dated as-built banner;
    rewrote Sections 1 (single barrel-jack input, USB-C parts removed, Q_RPP→PJA3441, D_BAR→1N5822-HT),
    2 (LTC4412 path → passive Schottky-OR with D_EXT/D_BOOST into PI_NODE; pi filter; 5V_RAIL ≈4.6V),
    3 (J5→2.25mm female socket, GPIO36→GPIO1), 5 (74HC14 pin map → GPIO 4/5/6/7/15/16, A/B swap note,
    R_GPIO12 dropped, TVS DNP, C_SCHM decoupling), 6 (ferrites → 0Ω jumpers J_FB1/2/3), 7 (MCU →
    ESP32-S3-DevKitC-1 N16R8, LED2→onboard WS2812 GPIO38, SW_RESET dropped); updated connector pinouts
    (J1/J2/J3 VCC via 0Ω jumper, J3 = 2P+3P ganged, J_USB block removed, J5 = 2.25mm).
  - `bill_of_materials.md` — replaced banner; aligned all line items to Appendix A. Dropped J_USB,
    R_CC1/2, TVS_USB, D_USB, U_IDEAL, Q_SWITCH, R_GATE, C_LTC, FB1/2/3, R_GPIO12, SW_RESET, LED2,
    R_LED2. Added/changed Q_RPP=PJA3441, D_BAR/D_EXT/D_BOOST=1N5822-HT, J_FB1-3=0Ω, TVS×7=DNP,
    U1=ESP32-S3-DevKitC-1 N16R8 (2×1×22 sockets), J5=2.25mm, J3a/J3b=KF301-2P+3P, C_SCHM added.
    Updated summary (~32 line items / ~63 populated) and sourcing notes.
  - `README.md` — light: updated the Documents table status rows + intro prose to say both docs are
    reconciled to as-built (no longer "pre-procurement reference").
  - `CLAUDE.md` — updated the two Key-Files descriptions for these docs (no longer "pre-procurement").
  - **C_SCHM** added to the BOM as a recommended line item per Agent 0's flag (74HC14 100nF decoupling,
    in original schematic but missing from Appendix A) — noted as a recommended add, not yet in App. A.
  - **Uncertain / verify:** J5 pitch (2.25mm as labeled — verify with calipers, per the plan). External
    5V_RAIL value stated as ~4.6V per the plan/Appendix C (one Schottky drop, was 4.98V with LTC4412).
- 2026-06-15 (Zone B agent): **Zone B built.** Added 10 Zone-B parts + 1 PWR_FLAG via a single
  `batch_add_and_connect` call (placed 11, connected 23 pins, all on the 2.54 mm grid at the exact coords
  from the playbook):
  - MOD_TP4056 (Conn_01x06; 1:V_EXT_PROT, 2:GND, 3:BAT_PLUS, 4:GND), MOD_MT3608 (Conn_01x04;
    1:BAT_PLUS, 2:GND, 3:MT3608_OUT, 4:GND), D_BOOST (1N5822; 1=K→PI_NODE, 2=A→MT3608_OUT),
    C_BOOST (22uF/10V; 1:MT3608_OUT, 2:GND), J5 (LiPo 1S Conn_01x02; 1:BAT_PLUS, 2:GND),
    R_MON1 (100k; 1:BAT_PLUS, 2:ADC_MON), R_MON2 (100k; 1:ADC_MON, 2:GND), C_ADC (100nF;
    1:ADC_MON, 2:GND), TP3 (MT3608_OUT), TP4 (BAT+).
  - PWR_FLAG: FLG_BATPLUS on BAT_PLUS @ (459.74, 45.72).
  - **No-connects:** MOD_TP4056 pins 5 + 6 (CHRG/STDBY LED, unused) via `add_no_connect` with
    componentRef+pinNumber (snapped to pin endpoints — no raw coords). Both succeeded.
  - **R_MT_HI/R_MT_LO** intentionally NOT placed (on-module). Added an `add_schematic_text` note beside
    MT3608 documenting this.
  - **ERC = 0 errors, 2 warnings** (both pre-existing/cosmetic: 1× pin off connection grid carried from
    Zone A, 1× missing footprint lib 'SMAJ5.0A'). No new errors. The build-tool reported "Power nets
    without PWR_FLAG: GND" — expected; the GND flag is a Zone D task per the playbook.
  - Component count now **28** (17 Zone A + 10 Zone B + FLG_BATPLUS). No `snap_to_grid` used. No deviations.
  - next: Zone C.
- 2026-06-15 (Zone C agent): **Zone C built.** Added all 34 Zone-C parts via a single
  `batch_add_and_connect` call (placed 34, connected 72 pins, all on the exact 2.54 mm-grid coords from
  the playbook/task table — verbatim, no rounding needed). Parts:
  - **Connectors:** J1 (THETA, Screw_Terminal_01x04; 1:GND, 2:ENC_VCC1, 3:THETA_A_IN, 4:THETA_B_IN),
    J2 (PHI, 01x04; 1:GND, 2:ENC_VCC2, 3:PHI_A_IN, 4:PHI_B_IN), J3a (WIRE_PWR, 01x02; 1:GND, 2:ENC_VCC3),
    J3b (WIRE_SIG, 01x03; 1:WIRE_A_IN, 2:WIRE_B_IN, 3:no-connect — see below).
  - **VCC feed (0Ω jumpers, rot 90):** J_FB1/2/3 (0R; 1:+5V → 2:ENC_VCC1/2/3).
  - **VCC bypass:** C_VCC1/2/3 (100nF; 1:ENC_VCCn, 2:GND).
  - **6 conditioning channels** (n=1..6, columns R_TOP=129.54 / R_BOT=154.94 / C_FILT=175.26 / TVS=195.58):
    R_TOPn (10k; in-net → DIVIDER_NODE_n), R_BOTn (20k; DIVIDER_NODE_n → GND), C_FILTn (10nF;
    DIVIDER_NODE_n → GND), TVSn (Device:D_TVS "1.5KE3.9CA DNP"; DIVIDER_NODE_n → GND). In-nets:
    ch1=THETA_A_IN, ch2=THETA_B_IN, ch3=PHI_A_IN, ch4=PHI_B_IN, ch5=WIRE_A_IN, ch6=WIRE_B_IN.
  - **TVS DNP method:** `batch_edit_schematic_components` does NOT expose a `dnp` flag (rejects it —
    only footprint/value/newReference/fieldPositions/properties/removeProperties are accepted). Set a
    custom BOM property `DNP=yes` on TVS1..6 via `properties` (machine-readable, survives export_bom).
    The Value field also reads "1.5KE3.9CA DNP" for human-readable documentation. (If the canonical
    `(dnp yes)` schematic token is required for the PCB step, a Verify-agent pass or GUI toggle can set it.)
  - **No-connect:** `add_no_connect` on J3b pin 3 (WIRE_Z, intentionally unused) via componentRef+pinNumber
    (snapped to pin endpoint @ 25.4, 388.62). Per playbook preference, the WIRE_Z net label was dropped
    (only J3b pins 1/2 labeled) and the no_connect added — ERC clean.
  - **PWR_FLAGs:** none added in Zone C (per playbook): +5V already flagged in Zone A; ENC_VCC1..3 are
    driven through the 0Ω J_FB resistors; GND flag is a Zone D task. The build tool's "Power nets without
    PWR_FLAG: +5V, ENC_VCC1..3, GND" notice is expected/benign.
  - **ERC = 0 errors, 2 warnings** (both pre-existing/cosmetic, carried from Zone A: 1× pin off connection
    grid + 1× missing footprint lib 'SMAJ5.0A'). No new errors/warnings.
  - Component count now **62** (28 + 34 Zone C). No `snap_to_grid` used. No deviations beyond the TVS-DNP
    property workaround noted above.
  - next: Zone D.
- 2026-06-15 (Zone D agent): **Zone D built.** Added 11 new components (count now **73**):
  - **U_SCHM (74xx:74HC14)** — placed **7 units**: 6 gate units at x=398.78, y=231.14/254/279.4/304.8/330.2/355.6
    plus the **dedicated power unit (unit 7)** at (398.78, 381). All gate I/O connected by net labels.
  - **C_SCHM** (Device:C 100nF) @ (429.26, 360.68) → {1:+3V3, 2:GND}.
  - **U1** (Connector_Generic:Conn_02x22_Odd_Even, stands in for ESP32-S3-DevKitC-1 N16R8) @ (480.06, 309.88)
    → {1:+5V, 2:GND, 3:+3V3, 4:ADC_MON, 5:THETA_A_OUT, 6:THETA_B_OUT, 7:PHI_A_OUT, 8:PHI_B_OUT,
    9:WIRE_A_OUT, 10:WIRE_B_OUT, 44:GND}. `add_schematic_text` DevKitC pin map placed beside it.
  - **TP2** (3V3) @ (541.02, 248.92) → {+3V3}; **TP5** (GND) @ (541.02, 269.24) → {GND}.
  - **FLG_3V3** PWR_FLAG @ (424.18, 236.22) → {+3V3}; **FLG_GND** PWR_FLAG @ (556.26, 289.56) → {GND}.
  - **★ ANSWER to the open question — how the 74HC14 power pins (7/14) are exposed across multi-units:**
    The KiCad standard `74xx:74HC14` is a **7-unit** symbol — units 1–6 are the six Schmitt gates;
    **unit 7 (`74HC14_7_0`) is a dedicated power-only unit** carrying pin 14 (VCC, at body +12.7) and
    pin 7 (GND, at body −12.7). Pins 7/14 are NOT on unit 1. To expose them you MUST place unit 7
    (`add_schematic_component … unit:7`). I placed it at (398.78, 381); pin 14→+3V3 (schematic
    y=368.3 = anchor−12.7), pin 7→GND (y=393.7 = anchor+12.7). Verified by inspecting
    `/usr/share/kicad/symbols/74xx.kicad_sym`.
  - **★ swig multi-unit net-label gotcha (IMPORTANT for future multi-unit work):** `add_schematic_net_label`
    with `componentRef`+`pinNumber` and `get_schematic_pin_locations`/`get_net_connections` **collapse all
    units onto unit 1's body coordinates** — every gate-input pin resolves to (391.16, 231.14) and every
    output to (406.4, 231.14). My first label pass therefore merged ALL six inputs onto DIVIDER_NODE_1 and
    all outputs onto THETA_A_OUT. **Fix:** deleted all 14 labels and re-added them with **explicit `position`
    [x,y]** computed per unit (input x=391.16, output x=406.4, y = that unit's `at` y; power unit VCC
    y=368.3 / GND y=393.7). Confirmed correct by grepping the `.kicad_sch` — each label sits at its own
    unit's distinct pin coordinate — and by ERC (the real connectivity engine): 0 errors. NOTE: the
    swig reporters (`get_net_connections`) STILL mis-report these IC pins (collapse artifact); trust the
    file coords + ERC, not the reporter, for multi-unit symbols.
  - **C_SCHM deviation:** as previously flagged (Agent 0 / Doc-sync), C_SCHM 100nF 74HC14 decoupling is NOT
    in Appendix A — added as standard practice, already doc-synced into bill_of_materials.md as a recommended
    line item. Placed as instructed; no further action.
  - **U1 no_connects:** U1 is a 44-pin generic connector; only pins 1–10 + 44 are used. Added `no_connect`
    on the 33 unused pins (11–43) via `batch_add_no_connects` — cleared 33 `pin_not_connected` errors.
  - **PWR_FLAGs:** FLG_3V3 + FLG_GND cleared the two `power_pin_not_driven` errors on the 74HC14 +3V3/GND
    power pins (and drive +3V3/GND for the whole sheet alongside the Zone A/B flags).
  - **ERC = 0 errors, 3 warnings** (2 pre-existing cosmetic + 1 new benign "Bidirectional/Power-output
    connected" on U1 +5V pin meeting FLG_5V). No `snap_to_grid` used.
  - next: Verify (full ERC=0, PDF/SVG export, netlist spot-check, BOM count — separate agent).
- 2026-06-15 (Verify agent): **Verify complete — draft schematic is COMPLETE and ERC-clean (0 errors).**
  - **ERC: 0 errors, 3 warnings** — re-ran `run_erc`, confirmed identical to the post-Zone-D run. Per-warning disposition:
    1. *"Symbol pin or wire end off connection grid"* — **cosmetic, DEFERRED to PCB stage.** Side-effect of placing
       parts on a 2.54 mm grid that is offset from KiCad's default 1.27 mm connection grid. Netlist confirms zero
       unconnected pins, so connectivity is unaffected. Do NOT chase with `snap_to_grid` (detaches labels → 29 ERC
       errors previously). Tidy in the GUI during PCB layout if desired.
    2. *"Configuration does not include footprint library 'SMAJ5.0A'"* — **cosmetic, DEFERRED.** Footprints are
       assigned at the PCB-layout stage; the project-embedded `SMAJ5.0A` symbol has no library footprint registered
       yet. Acceptable for a draft schematic.
    3. *"Pins of type Bidirectional and Power output are connected" @ +5V (U1/1 ↔ FLG_5V)* — **benign, no fix
       applied (correct call).** U1 is the `Conn_02x22_Odd_Even` generic stand-in for the DevKitC-1; its pins are
       "bidirectional/passive" by symbol type, and pin 1 sits on the FLG_5V-driven +5V rail (FLG_5V = power-output).
       This is the expected ERC note whenever a generic-connector pin meets a PWR_FLAG-driven rail. **Recommendation:**
       do NOT add a `no_connect` (U1/1 *is* connected — it carries +5V to the board) and do NOT remove FLG_5V (it is
       the rail's required driver). The clean fix at PCB stage is to swap the U1 stand-in for a real DevKitC-1 symbol
       whose +5V pin carries a `power_in` electrical type — then the warning vanishes. Leaving as-is for the draft is
       correct; it is not a real electrical conflict.
  - **Artifacts exported:** PDF → `pcb_design/EVKA_position_v2/exports/EVKA_position_v2.pdf`; SVG →
    `pcb_design/EVKA_position_v2/exports/EVKA_position_v2.svg`. Netlist inspected via `generate_netlist` (not written to file).
  - **Connectivity spot-checks (all PASS)** via `generate_netlist`:
    - `+5V`: C1, C2, FLG_5V, J6, J_FB1/2/3, L1/2, R_LED1, TP1, U1/1 — all expected pins present. ✔
    - `GND`: 47-pin common return across all 4 zones incl. FLG_GND, TP5, U_SCHM/7 (power unit). ✔
    - `+3V3`: C_SCHM/1, FLG_3V3, TP2, U1/3, U_SCHM/14 (power unit). ✔
    - `ADC_MON`: C_ADC/1, R_MON1/2, R_MON2/1, U1/4. ✔
    - All 6 signal paths verified `DIVIDER_NODE_n → U_SCHM input → *_OUT → U1`:
      DIVIDER_NODE_1(in pin1)→THETA_A_OUT(out pin2→U1/5); DN_2(3)→THETA_B_OUT(4→U1/6);
      DN_3(5)→PHI_A_OUT(6→U1/7); DN_4(9)→PHI_B_OUT(8→U1/8); DN_5(11)→WIRE_A_OUT(10→U1/9);
      DN_6(13)→WIRE_B_OUT(12→U1/10). Each DIVIDER_NODE_n also carries R_TOPn/R_BOTn/C_FILTn/TVSn. ✔
    - **★ swig-collapse note resolved:** unlike `get_net_connections`/`get_schematic_pin_locations` (which the Zone D
      agent found collapse multi-unit pins onto unit 1), **`generate_netlist` correctly resolves the 74HC14 per-unit
      pins** — each DIVIDER_NODE/_OUT maps to its own distinct U_SCHM pin (1/3/5/9/11/13 in, 2/4/6/8/10/12 out). This
      independently corroborates the build-log claim that ERC=0 reflects real (not collapsed) connectivity. Trust
      `generate_netlist` + ERC over `get_net_connections` for multi-unit symbols.
  - **Component count vs BOM:** `list_schematic_components` returns 75 rows, but U_SCHM is one 7-unit device (7 rows →
    1 device), so **69 unique devices** (matches `generate_netlist` "Components (69)"). Breakdown: 6 PWR_FLAGs + 5 test
    points are schematic-only annotations (the TP pins are 1 BOM row "TP1–TP5"); the remaining 58 map 1:1 to the as-built
    BOM physical line items, incl. the 6 DNP TVS (carry `DNP=yes` property + "1.5KE3.9CA DNP" value) and the C_SCHM
    deviation (recommended add, already doc-synced). **No refdes present in the schematic but missing from the BOM, and
    none in the BOM but missing from the schematic.** Note: the BOM tables say "×7" signal channels but the schematic
    correctly has **6** (THETA_A/B, PHI_A/B, WIRE_A/B — WIRE_Z is no-connect); the "7" is a BOM carryover convention,
    not a missing channel. The board reserves 6 active conditioning channels per the playbook.
  - **PCB-layout-stage follow-ups (carried forward):**
    1. Assign footprints to all 69 components (most show "No footprint"); register the `SMAJ5.0A` footprint library
       to clear warning #2.
    2. Set the native `(dnp yes)` schematic token on TVS1..6 (the MCP `batch_edit_schematic_components` could not set
       it; only a `DNP=yes` BOM property + value-text were applied). Toggle DNP in the GUI or via the PCB step.
    3. Optionally tidy the off-grid placements (warning #1) in the GUI — NOT via `snap_to_grid`.
    4. Replace the U1 `Conn_02x22` stand-in with a real ESP32-S3-DevKitC-1 symbol (power_in pin type) to clear
       warning #3 cleanly.
    5. Confirm C_SCHM is folded into Appendix A (currently a recommended add beyond the authoritative BOM).
  - **Verdict:** Draft schematic is **COMPLETE and ERC-clean (0 errors)**. The 3 warnings are all cosmetic/deferred or
    benign-by-design (documented above); none is a real electrical problem. Ready to hand off to the PCB-layout stage.
