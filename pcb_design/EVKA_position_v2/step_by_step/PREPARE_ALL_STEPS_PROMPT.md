# Prepare all steps — master orchestration prompt

Paste everything below the line into a fresh agent session with KiCad MCP enabled.
Use this when you want **Steps 2–9** prepared in one run (Step 1 is already done).

---

You are assisting the **step-by-step co-build** of the EVKA Position 5V v2 PCB schematic.
Your job is to finish the step drafts under `pcb_design/EVKA_position_v2/step_by_step/steps/` —
**build Step 2**, then **create Steps 3–9** — each as a standalone KiCad sub-circuit plus a readable
lesson markdown file.

## Current state (read this first — do not redo finished work)

| Step | Plan | Step draft (`steps/NN_…/`) | User master schematic |
|---|---|---|---|
| **1** | Done (`MASTER_PLAN.md`, `01_input_schottky_or.md`) | Done — examine only | **Implemented** — do not edit master |
| **2** | Done (`MASTER_PLAN.md`, `NEXT_STEP_PROMPT.md`) | Lesson exists; **add KiCad draft + footprints** | Not implemented — **user copies by hand** |
| **3–9** | Done (`MASTER_PLAN.md`) | **Not built** — create from scratch | Not implemented |

**Your scope:** examine Step 1 for style/consistency → **build Step 2** → create Steps 3–9.
Do **not** rebuild Step 1 unless the existing draft is broken.

Work **sequentially** (Step 2 → Step 9). After each step, append to `BUILD_LOG.md` before starting the next.

## Forbidden — agents must NOT edit these (read-only)

Agents **never** open, write, or call KiCad MCP tools against the user's master design or the reference
design. The user copies step drafts into the master **by hand in KiCad**.

| Forbidden path | Why |
|---|---|
| `…/Master Design/EvkaPosition_v2/*` | User's live master project (`.kicad_sch`, `.kicad_pro`, `.kicad_pcb`, `.kicad_prl`, backups, lock files) |
| `…/EVKA_position_v2/EVKA_position_v2.kicad_sch` | As-built reference schematic (source of truth for extraction only) |
| `…/EVKA_position_v2/EVKA_position_v2.kicad_pro` | Reference project file |
| `…/EVKA_position_v2/EVKA_position_v2.kicad_pcb` | Reference PCB (out of scope) |

You may **read** the master schematic and reference schematic to inspect nets, coords, and deviations —
but every KiCad MCP `schematicPath` used for **editing** must point only under
`step_by_step/steps/NN_<slug>/`.

**Writable by agents:** `step_by_step/steps/*`, `step_by_step/BUILD_LOG.md`, `step_by_step/NEXT_STEP_PROMPT.md`.
**Not writable:** `Master Design/`, root `EVKA_position_v2/*.kicad_*`, `MASTER_PLAN.md` (stable spine).

## Paths (absolute)

| Role | Path |
|---|---|
| This workspace | `/home/yunusdanabas/evka_position/pcb_design/EVKA_position_v2/step_by_step/` |
| Master plan (9-step spine) | `…/step_by_step/MASTER_PLAN.md` |
| Step 2 hand-off (detailed plan) | `…/step_by_step/NEXT_STEP_PROMPT.md` |
| Step 1 lesson (style reference) | `…/step_by_step/steps/01_input_schottky_or/01_input_schottky_or.md` |
| Build log (append-only) | `…/step_by_step/BUILD_LOG.md` |
| **Purchased parts + footprints** | `…/step_by_step/PURCHASED_COMPONENTS.md` |
| Workflow + MCP rules | `…/step_by_step/README.md` |
| Reference schematic (**read-only — never edit**) | `/home/yunusdanabas/evka_position/pcb_design/EVKA_position_v2/EVKA_position_v2.kicad_sch` |
| User's master design (**read-only — entire folder forbidden**) | `/home/yunusdanabas/evka_position/pcb_design/EVKA_position_v2/Master Design/EvkaPosition_v2/` |
| Agent conventions + coords | `…/docs/KICAD_AGENT_INSTRUCTIONS.md` |
| Design rationale / BOM / nets | `…/docs/KICAD_PLAN_DETAILED.md` (Appendix A = BOM, Appendix C = nets) |

## Read first

1. `README.md` — workflow and inherited KiCad MCP rules.
2. **`PURCHASED_COMPONENTS.md`** — footprint for every refdes in this step (mandatory).
3. `MASTER_PLAN.md` — full 9-step spine.
4. `NEXT_STEP_PROMPT.md` — **Step 2 build instructions** (parts, nets, master Step 1 deviations).
5. `steps/01_input_schottky_or/01_input_schottky_or.md` — lesson format + tone to mirror.
6. `KICAD_AGENT_INSTRUCTIONS.md` — symbol pin map, zone coords, net names, PWR_FLAG rules.
7. `BUILD_LOG.md` — append only; Step 1 entry already exists.
8. Reference `EVKA_position_v2.kicad_sch` — extract **exact** `(at x y rot)`, refdes, values, net names.
   Fidelity over invention.

## Hard rules

- **One step folder per step:** `steps/NN_<slug>/` with matching KiCad project name `NN_<slug>`.
- **Grid:** every component at coordinates that are **multiples of 2.54 mm**.
- **NEVER run `snap_to_grid`** — it detaches labels from pins (caused a 29-error revert once).
- **Connectivity:** use `add_schematic_net_label` with `componentRef` + `pinNumber` to snap labels to pins.
  Same-named labels merge. Add wires where needed between pins on the same net (master uses wires; drafts may too).
- **PWR_FLAG:** every power net introduced in a step needs a `power:PWR_FLAG`.
- **Footprints (mandatory):** assign KiCad Footprint field from `PURCHASED_COMPONENTS.md` on every
  populated symbol (`footprint` in `batch_add_and_connect`). Use `search_footprints` to verify the lib
  exists. Step lesson component table must include a **Footprint** column. **74HC14 = SOIC-14, not DIP.**
  **TVS1..6 = populate** (general THT TVS, flexible axial footprint `D_DO-201AD_P15.24mm`, part TBD). **6×6 mm button = do not place.**
- **74HC14:** `74xx:74HC14` is a **7-unit** symbol — unit 7 carries pin 14 (`+3V3`) and pin 7 (`GND`).
- **Do not edit:** anything under `Master Design/`, root reference `EVKA_position_v2.kicad_*`, or Step 1
  draft (unless broken). See **Forbidden** section above.
- **Step-draft ERC:** benign floating-interface-net warnings are OK — document them.
- **`save_project` is a no-op** on the swig backend.

## Per-step deliverables

### Step 1 — examine only (skip build)

- Read `steps/01_input_schottky_or/` (KiCad draft + `.md`).
- Note lesson structure (ASCII schematic, component table, net table, keypoints, ERC notes).
- Carry forward the **master Step 1 deviations** documented in `NEXT_STEP_PROMPT.md` into Step 2+ lessons
  where relevant (J1 vs J4, SMAJ5.0A lib choice, wires vs labels, `V_EXT_PROT` at 104.14, 21.59).
- Do **not** append a new BUILD_LOG entry for Step 1.

### Steps 2–9 — build or create

For each step **NN**:

1. `create_project` at `steps/NN_<slug>/` named `NN_<slug>` (Step 2: create fresh; Steps 3–9: new).
2. Place parts via KiCad MCP using reference `(at x y rot)` coords (2.54 mm grid). **Set footprint** per
   `PURCHASED_COMPONENTS.md` on each part.
3. Add interface nets + PWR_FLAGs for power nets this step introduces.
4. `run_erc` — record error/warning counts.
5. Write `steps/NN_<slug>/NN_<slug>.md` (mirror Step 1 lesson format; **Footprint column required**).
6. Append dated entry to `BUILD_LOG.md`.

After Step 9:

7. Overwrite `NEXT_STEP_PROMPT.md` with a hand-off: all step drafts ready; user copies Steps 2–9 into
   master (Step 1 already done); list any deviations.
8. Stop.

## Step catalogue

Encoder channel order (Steps 5–8): `n = 1..6 =` **THETA_A, THETA_B, PHI_A, PHI_B, WIRE_A, WIRE_B**.

### Step 1 — `01_input_schottky_or` · Zone A — **DONE (examine only)**
Draft + lesson exist. User implemented in master. Interface-out: `V_EXT_PROT`.

### Step 2 — `02_pi_filter_5v_rail` · Zone A — **BUILD THIS**
Follow `NEXT_STEP_PROMPT.md` in full.

**Parts:** D_EXT, C_PI, L1, C1, C2, R_LED1, LED1, J6, TP1, FLG_5V  
**Chain:** `V_EXT_PROT` → D_EXT → `PI_NODE`; `PI_NODE` → C_PI → L1 → C1 ∥ C2 → `+5V`; LED; J6 bench; TP1  
**Interface in:** `V_EXT_PROT` (from master Step 1), `PI_NODE` (shared w/ Step 3)  
**Interface out:** `+5V` → Steps 5, 8  

**Master Step 1 context (for the lesson's "notes for user" section):**
- `V_EXT_PROT` is wired and labeled in master at wire endpoint (104.14, 21.59).
- Master uses wires; barrel J1, `Diode:SMAJ5.0A` TVS — cosmetic vs reference only.

### Step 3 — `03_charge_boost_battery` · Zone B — **CREATE**
**Parts:** MOD_TP4056, MOD_MT3608, D_BOOST, C_BOOST, J5, TP3, TP4, FLG_BATPLUS  
**Interface out:** `BAT_PLUS` → Step 4; `PI_NODE` → Step 2 via D_BOOST  
**Key:** external charging only; passive Schottky-OR; MT3608 ≈5.3 V

### Step 4 — `04_battery_adc_monitor` · Zone B — **CREATE**
**Parts:** R_MON1, R_MON2, C_ADC (100k/100k ÷2)  
**Interface in:** `BAT_PLUS` · **out:** `ADC_MON` → Step 8 GPIO1

### Step 5 — `05_encoder_connectors` · Zone C — **CREATE**
**Parts:** J1, J2, J3 (all 4-pin), J_FB1/2/3 (0R), C_VCC1/2/3  
**Interface in:** `+5V` · **out:** `ENC_VCC1/2/3`, `*_IN` ×6 → Step 6  
**Key:** wire encoder is a single 4-pin J3 (GND/VCC/A/B); Z/index unused — not wired

### Step 6 — `06_signal_conditioning` · Zone C — **CREATE**
**Parts (×6):** R_TOPn 10k, R_BOTn 20k, C_FILTn 10nF, TVSn DNP  
**Interface out:** `DIVIDER_NODE_1..6` → Step 7

### Step 7 — `07_schmitt_buffer` · Zone D — **CREATE**
**Parts:** U_SCHM (74HC14 ×7 units), C_SCHM  
Gate map: DIVIDER_NODE_1..6 → THETA_A/B_OUT, PHI_A/B_OUT, WIRE_A/B_OUT  
**Interface in:** `+3V3` (Step 8) · **out:** `*_OUT` ×6

### Step 8 — `08_esp32_devkit` · Zone D — **CREATE**
**Parts:** U1 DevKitC-1 stand-in (`Conn_02x22_Odd_Even`)  
GPIO: 4/5/6/7/15/16 = encoder outs, 1 = ADC_MON · sources `+3V3`

### Step 9 — `09_test_points_final` · Zone D — **CREATE**
**Parts:** TP2, TP5, FLG_3V3, FLG_GND + verification checklist  
(Extract coords from reference; may overlap Step 8 zone)

## Interface-net summary

```
Step1 ─V_EXT_PROT→ Step2 ─+5V→ Step5, Step8
Step3 ─BAT_PLUS→ Step4 ─ADC_MON→ Step8
Step3 ─PI_NODE(D_BOOST)→ Step2     (passive OR with Step1's D_EXT)
Step5 ─*_IN→ Step6 ─DIVIDER_NODE_1..6→ Step7 ─*_OUT→ Step8
Step8 ─+3V3→ Step7        GND: everywhere
```

## Success criteria

- [ ] Step 1 examined; not rebuilt.
- [ ] `steps/02_…` through `steps/09_…` each have `.kicad_pro`, `.kicad_sch`, and `.md` lesson.
- [ ] Every populated symbol has a Footprint from `PURCHASED_COMPONENTS.md` (verify via `list_schematic_components`).
- [ ] `BUILD_LOG.md` has entries for Steps 2–9.
- [ ] `NEXT_STEP_PROMPT.md` updated with "all drafts ready" hand-off.
- [ ] `Master Design/` and reference `EVKA_position_v2.kicad_*` untouched (read-only inspection OK).

**Begin with Step 1 examination (5 min read), then build Step 2, then create Steps 3–9.**
Report a summary table at the end:

| Step | Folder | ERC (errors/warnings) | Status |
