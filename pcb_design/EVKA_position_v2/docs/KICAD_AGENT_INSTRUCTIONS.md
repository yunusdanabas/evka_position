# KiCad Agent Instructions — EVKA Position 5V v2 schematic build

**Read this file + `KICAD_BUILD_LOG.md` before doing anything. Do your assigned task via the KiCad
MCP, append a log entry, then stop.** This is the single source of truth for the schematic build.

## Mission

Capture the **as-built 5V v2 circuit** (authoritative: `KICAD_PLAN_DETAILED.md` Appendix A BOM +
Appendix C net list) as a clean, ERC-clean **draft schematic** on a single A2 sheet, organized into 4
zones. No PCB layout (separate follow-up). Locked decisions: capture full circuit as-is; single flat
zoned sheet; build via the KiCad MCP; multi-agent with this playbook + the build log.

- **Schematic file (all MCP calls use this `schematicPath`):**
  `/home/yunusdanabas/evka_position/pcb_design/EVKA_position_v2/EVKA_position_v2.kicad_sch`
- Project: `…/EVKA_position_v2/EVKA_position_v2.kicad_pro` — KiCad 10.0.3, backend `swig` (file-based).

## Coordination protocol (IMPORTANT)

- The schematic is **one shared file**. **Only one agent edits it at a time.** Zone agents run
  **strictly sequentially** in order: Setup → A → B → C → D → Verify. The build log is the lock/handoff:
  before editing, confirm the previous task is logged ✔; after editing, log your entry (edits persist to the
  `.kicad_sch` directly — no save step).
- **Agent Doc** (doc sync) edits *different* files (`circuit_schematic.md`, `bill_of_materials.md`) and
  may run in parallel.
- Never run two schematic-editing agents concurrently.

## MCP conventions

- **Connectivity is net-label based.** Use `mcp__kicad__batch_add_and_connect` with a `nets:{pin:netName}`
  map per component — it places the part and labels each listed pin. Same-named labels merge into one net
  (single sheet → plain labels are fine). The MCP draws a wire when two facing labels are adjacent.
- Always identify pins by **pin number** (the map key). Pin numbers are in the symbol map below.
- For pins added later / one-offs, use `mcp__kicad__add_schematic_net_label` with `componentRef`+`pinNumber`
  (snaps to the exact endpoint — never pass raw coordinates).
- **Rotation** `angle`/`rotation`: 0 = vertical (resistor vertical), 90 = horizontal, CCW.
- **⚠ GRID RULE (mandatory):** place every component at coordinates that are **multiples of 2.54 mm** so
  pins land on KiCad's connection grid. The per-zone tables below use integer-mm *seed* values for
  readability — **round each x and y to the nearest 2.54 multiple before placing** (e.g. 320→320.04 is
  wrong; use 320.04? no — use the nearest multiple: round(coord/2.54)*2.54, e.g. 320→322.58 or 317.5→317.5).
  Simplest: `x = round(seed/2.54)*2.54`. Zone A was built this way (J4 at 30.48,71.12 etc.).
- **🚫 NEVER run `snap_to_grid`.** It moves components and their net labels independently and *detaches
  labels from pins* — this previously caused 29 ERC errors and forced a full revert. Place on-grid from
  the start instead; do not "fix" off-grid warnings with snap_to_grid.
- **Persistence:** schematic edit tools write the `.kicad_sch` **directly** (no save needed). `save_project`
  does NOT work here (it needs a loaded PCB and returns "No board is loaded") — do not rely on it; confirm
  state with `list_schematic_components` / `list_schematic_labels` instead.
- After each zone: `mcp__kicad__run_erc` (note the error/warning delta).
- Power nets need a driver flag or ERC errors — see **PWR_FLAG** below. The MCP warns when a power net
  lacks one.

## Net names (canonical — use these exact strings)

`GND`, `+5V` (the 5V_RAIL), `+3V3`, `V_IN_JACK`, `V_EXT_RAW`, `RPP_GATE`, `V_EXT_PROT`, `PI_NODE`,
`BAT_PLUS`, `MT3608_OUT`, `ADC_MON`, `LED_A`, `ENC_VCC1..3`, `THETA_A_IN/THETA_B_IN/PHI_A_IN/PHI_B_IN/WIRE_A_IN/WIRE_B_IN`,
`DIVIDER_NODE_1..6`, `THETA_A_OUT/THETA_B_OUT/PHI_A_OUT/PHI_B_OUT/WIRE_A_OUT/WIRE_B_OUT`. _(`WIRE_Z` dropped — wire encoder Z/index unused, single 4-pin J3.)_

## Symbol map (MCP-verified pin numbers)

| RefDes(es) | symbol | pins |
|---|---|---|
| J4 barrel jack | `Connector:Barrel_Jack` | 1 = tip(+), 2 = sleeve(−) |
| TVS_BAR | `SMAJ5.0A:SMAJ5.0A` (project-embedded — reuse, do not re-import) | 1, 2 (bidir) |
| D_BAR, D_EXT, D_BOOST | `Diode:1N5822` | 1 = K, 2 = A |
| Q_RPP | `Transistor_FET:Q_PMOS_GSD` | **1 = G, 2 = S, 3 = D** |
| R_*, J_FB*, R_TOP*, R_BOT*, R_MON* | `Device:R` | 1, 2 |
| C2, C_ADC, C_FILT*, C_VCC*, C_SCHM | `Device:C` | 1, 2 |
| C_PI, C1, C_BOOST | `Device:C_Polarized` | 1 = +, 2 = − |
| L1 | `Device:L` | 1, 2 |
| LED1 | `Device:LED` | 1 = K, 2 = A |
| U_SCHM | `74xx:74HC14` (multi-unit) | in 1/3/5/9/11/13 → out 2/4/6/8/10/12; **7 = GND, 14 = VCC** |
| J1, J2, J3 | `Connector:Screw_Terminal_01x04` | 1..4 |
| J6 | `Connector:Screw_Terminal_01x02` | 1,2 |
| TP1..TP5 | `Connector:TestPoint` | 1 |
| MOD_TP4056 | `Connector_Generic:Conn_01x06` | 1..6 (assign IN+/IN−/BAT+/BAT−/—/— per net table) |
| MOD_MT3608 | `Connector_Generic:Conn_01x04` | 1..4 (IN+/IN−/OUT+/OUT−) |
| J5 LiPo | `Connector_Generic:Conn_01x02` | 1 = BAT+, 2 = GND |
| U1 DevKitC-1 | `Connector_Generic:Conn_02x22_Odd_Even` | 1..44 passive |
| TVS1..6 (populate) | `Device:D_TVS` (set `value` "TVS 3.3V (THT-TBD)") | 1, 2 |
| power flags | `power:PWR_FLAG` | 1 |

## Zone tasks

Coordinates are mm on an A2 sheet (origin top-left). 2×2 grid: **A** top-left, **B** top-right,
**C** bottom-left, **D** bottom-right. Positions are seed values for readability — connectivity comes
from the net labels, so minor overlaps are acceptable in a draft (tidy later in GUI if desired).

### Zone A — Power input / Schottky-OR / pi-filter  (anchor ~x20–280, y30–175)
`batch_add_and_connect` components (reuse the 3 already-placed parts after Setup renames them):

| ref | symbol | value | pos (x,y) | rot | nets {pin:net} |
|---|---|---|---|---|---|
| J4 | Connector:Barrel_Jack | 5.5x2.1 | 30,70 | 0 | 1:V_IN_JACK, 2:GND |
| TVS_BAR | SMAJ5.0A:SMAJ5.0A | SMAJ5.0A | 60,72 | 0 | 1:GND, 2:V_IN_JACK |
| D_BAR | Diode:1N5822 | 1N5822 | 85,60 | 0 | 2:V_IN_JACK, 1:V_EXT_RAW |
| Q_RPP | Transistor_FET:Q_PMOS_GSD | PJA3441 | 120,62 | 0 | 2:V_EXT_RAW, 1:RPP_GATE, 3:V_EXT_PROT |
| R_RPP | Device:R | 100k | 120,85 | 0 | 1:RPP_GATE, 2:GND |
| D_EXT | Diode:1N5822 | 1N5822 | 155,60 | 0 | 2:V_EXT_PROT, 1:PI_NODE |
| C_PI | Device:C_Polarized | 10uF/10V | 180,85 | 0 | 1:PI_NODE, 2:GND |
| L1 | Device:L | 10uH | 200,55 | 90 | 1:PI_NODE, 2:+5V |
| C1 | Device:C_Polarized | 220uF/10V | 225,85 | 0 | 1:+5V, 2:GND |
| C2 | Device:C | 100nF | 245,85 | 0 | 1:+5V, 2:GND |
| R_LED1 | Device:R | 1k | 265,60 | 0 | 1:+5V, 2:LED_A |
| LED1 | Device:LED | Green | 265,85 | 0 | 2:LED_A, 1:GND |
| J6 | Connector:Screw_Terminal_01x02 | BENCH_5V | 30,120 | 0 | 1:+5V, 2:GND |
| TP1 | Connector:TestPoint | 5V_RAIL | 235,45 | 0 | 1:+5V |

Then PWR_FLAGs (separate components, ref `#FLG…` auto): on `V_EXT_RAW` (pos 105,45), `V_EXT_PROT` (145,45), `+5V` (215,45). e.g. `{symbol:"power:PWR_FLAG", reference:"FLG_VEXTRAW", nets:{1:"V_EXT_RAW"}}`.

### Zone B — Battery / charging / ADC  (anchor ~x300–560, y30–175)
| ref | symbol | value | pos | rot | nets |
|---|---|---|---|---|---|
| MOD_TP4056 | Connector_Generic:Conn_01x06 | TP4056 | 320,70 | 0 | 1:V_EXT_PROT, 2:GND, 3:BAT_PLUS, 4:GND |
| MOD_MT3608 | Connector_Generic:Conn_01x04 | MT3608 5V0 | 380,70 | 0 | 1:BAT_PLUS, 2:GND, 3:MT3608_OUT, 4:GND |
| D_BOOST | Diode:1N5822 | 1N5822 | 430,60 | 0 | 2:MT3608_OUT, 1:PI_NODE |
| C_BOOST | Device:C_Polarized | 22uF/10V | 410,90 | 0 | 1:MT3608_OUT, 2:GND |
| J5 | Connector_Generic:Conn_01x02 | LiPo 1S | 320,120 | 0 | 1:BAT_PLUS, 2:GND |
| R_MON1 | Device:R | 100k | 470,60 | 0 | 1:BAT_PLUS, 2:ADC_MON |
| R_MON2 | Device:R | 100k | 470,90 | 0 | 1:ADC_MON, 2:GND |
| C_ADC | Device:C | 100nF | 490,90 | 0 | 1:ADC_MON, 2:GND |
| TP3 | Connector:TestPoint | MT3608_OUT | 445,45 | 0 | 1:MT3608_OUT |
| TP4 | Connector:TestPoint | BAT+ | 350,110 | 0 | 1:BAT_PLUS |

PWR_FLAG on `BAT_PLUS` (pos 460,45). (MOD_TP4056 pins 5/6 = CHRG/STDBY LED — leave unconnected/no-connect. R_MT_HI/R_MT_LO are on-module, NOT board parts — do not place.)

### Zone C — Encoder connectors + 6 conditioning channels  (anchor ~x20–340, y210–410)
Connectors + VCC bypass:
| ref | symbol | value | pos | rot | nets |
|---|---|---|---|---|---|
| J1 | Connector:Screw_Terminal_01x04 | THETA | 30,240 | 0 | 1:GND, 2:ENC_VCC1, 3:THETA_A_IN, 4:THETA_B_IN |
| J2 | Connector:Screw_Terminal_01x04 | PHI | 30,300 | 0 | 1:GND, 2:ENC_VCC2, 3:PHI_A_IN, 4:PHI_B_IN |
| J3 | Connector:Screw_Terminal_01x04 | WIRE | 30,360 | 0 | 1:GND, 2:ENC_VCC3, 3:WIRE_A_IN, 4:WIRE_B_IN |
| J_FB1 | Device:R | 0R | 70,235 | 90 | 1:+5V, 2:ENC_VCC1 |
| J_FB2 | Device:R | 0R | 70,295 | 90 | 1:+5V, 2:ENC_VCC2 |
| J_FB3 | Device:R | 0R | 70,350 | 90 | 1:+5V, 2:ENC_VCC3 |
| C_VCC1 | Device:C | 100nF | 90,250 | 0 | 1:ENC_VCC1, 2:GND |
| C_VCC2 | Device:C | 100nF | 90,310 | 0 | 1:ENC_VCC2, 2:GND |
| C_VCC3 | Device:C | 100nF | 90,365 | 0 | 1:ENC_VCC3, 2:GND |

6 channels — for n=1..6 with (in-net, div-net, the row y): rows at y = 230,255,280,305,330,355.
in-nets: THETA_A_IN, THETA_B_IN, PHI_A_IN, PHI_B_IN, WIRE_A_IN, WIRE_B_IN. div-nets: DIVIDER_NODE_1..6.
| ref | symbol | value | pos x | nets |
|---|---|---|---|---|
| R_TOPn | Device:R | 10k | 130 | 1:`<in>`, 2:`DIVIDER_NODE_n` |
| R_BOTn | Device:R | 20k | 155 | 1:`DIVIDER_NODE_n`, 2:GND |
| C_FILTn | Device:C | 10nF | 175 | 1:`DIVIDER_NODE_n`, 2:GND |
| TVSn | Device:D_TVS | TVS 3.3V (THT-TBD) | 195 | 1:`DIVIDER_NODE_n`, 2:GND **(populate; flexible THT fp)** |

(No `WIRE_Z` no-connect — wire encoder is a single 4-pin J3, Z line not wired.) TVS1..6 are **populated** (general
THT TVS, flexible `D_DO-201AD_P15.24mm` footprint, exact part TBD) — no DNP flag to set.

### Zone D — Schmitt buffer + MCU  (anchor ~x360–580, y210–410)
- **U_SCHM (74xx:74HC14, multi-unit)** — place the 6 gate units with `add_schematic_component`
  (`reference:"U_SCHM"`, `unit:1..6`) at y = 230,255,280,305,330,355, x≈400. Then connect by pin number
  with `add_schematic_net_label` (`componentRef:"U_SCHM"`, `pinNumber`):
  - pin1→DIVIDER_NODE_1, pin2→THETA_A_OUT; pin3→DIVIDER_NODE_2, pin4→THETA_B_OUT;
    pin5→DIVIDER_NODE_3, pin6→PHI_A_OUT; pin9→DIVIDER_NODE_4, pin8→PHI_B_OUT;
    pin11→DIVIDER_NODE_5, pin10→WIRE_A_OUT; pin13→DIVIDER_NODE_6, pin12→WIRE_B_OUT;
  - **pin14→+3V3, pin7→GND** (power pins — verify which unit exposes them; place that unit if needed).
- C_SCHM (`Device:C`, 100nF) at 430,360 → `{1:+3V3, 2:GND}`. **NOTE/deviation: C_SCHM is NOT in
  Appendix A; added as standard 74HC14 decoupling. Log it; recommend adding to BOM.**
- **U1 (DevKitC-1, `Connector_Generic:Conn_02x22_Odd_Even`)** at ~480,310. The 44-pin generic connector
  stands in for the dev board; map *used* pins to nets (choose any free connector pins — physical board
  pin order is verified at PCB stage). Suggested: 1:+5V, 2:GND, 3:+3V3, 4:ADC_MON, 5:THETA_A_OUT,
  6:THETA_B_OUT, 7:PHI_A_OUT, 8:PHI_B_OUT, 9:WIRE_A_OUT, 10:WIRE_B_OUT, 44:GND. `add_schematic_text`
  beside U1 with the real DevKitC-1 map: "5V=J1.21, GND, 3V3=J1.1/2, IO4/5/6/7/15/16 = Schmitt outs,
  IO1=ADC_MON, IO38=onboard WS2812. Reserved: 0/3/45/46 strap, 19/20 USB, 35/36/37 PSRAM, 43/44 UART0."
  `add_no_connect` on the unused U1 connector pins (or leave passive — re-check after ERC).
- TP2 (3V3) at 540,250 → {1:+3V3}; TP5 (GND) at 540,270 → {1:GND}.
- PWR_FLAGs: `+3V3` (pos 425,235) and `GND` (pos 555,290). One GND flag for the whole sheet is enough.

## Zone title texts (Setup agent)
`add_schematic_text`, size ~3.5: "ZONE A — POWER INPUT / SCHOTTKY-OR / PI-FILTER" @(20,25);
"ZONE B — BATTERY / CHARGING / ADC" @(300,25); "ZONE C — ENCODER SIGNAL CONDITIONING (6 ch)" @(20,205);
"ZONE D — SCHMITT BUFFER + ESP32-S3 DevKitC-1" @(360,205).
Plus a title-block-ish note: "EVKA Position 5V v2 — DRAFT schematic (as-built per KICAD_PLAN_DETAILED.md Appendix A)".

## PWR_FLAG summary (ERC gate)
One `power:PWR_FLAG` per net on: **GND, +5V, +3V3, V_EXT_RAW, V_EXT_PROT, BAT_PLUS**. Place across the
zones as noted. Without these, `run_erc` raises `power_pin_not_driven` errors.

## ERC / verification gate (Agent V)
1. `run_erc` → resolve to **zero errors**. Expected fixable items: `power_pin_not_driven` (add PWR_FLAG),
   `pin_not_connected` (add `no_connect` on genuinely-unused pins: MOD_TP4056 LED pins, spare U1 pins).
   Document any residual *warnings* in the log with justification.
2. `export_schematic_pdf` → `…/EVKA_position_v2.pdf`; `export_schematic_svg`. Eyeball the 4 zones.
3. `generate_netlist`; spot-check with `list_schematic_nets` / `get_net_connections` that `+5V`, `GND`,
   each `DIVIDER_NODE_n → U_SCHM → *_OUT → U1` path, and `ADC_MON` are correct.
4. `list_schematic_components` count vs Appendix A (~32 line items / ~64 parts incl. multiplicities).

## Logging protocol
After your task, append to `KICAD_BUILD_LOG.md`: a dated entry with agent name, what you placed/changed,
`run_erc` result (errors/warnings counts), files saved, any deviation/decision (e.g. TVS dnp method,
74HC14 power-pin handling, refdes changes), and the next pending task. Flip the task checklist box.
Keep the decisions/issues section append-only.
