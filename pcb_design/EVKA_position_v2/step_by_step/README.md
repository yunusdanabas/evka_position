# Step-by-step co-build — 5V v2 schematic

This workspace exists so the 5V v2 board can be **re-built by hand, part by part, into a fresh master
KiCad project**, learning the design along the way. An agent assists each step; **you do the final
placement yourself** while checking against the agent's draft.

The complete board already exists and is ERC-clean at
`../EVKA_position_v2.kicad_sch`. That file is the **read-only source of truth** — steps extract their exact
refdes / values / nets from it. Do **not** edit it here.

## Files

| File | Role |
|---|---|
| `MASTER_PLAN.md` | The canonical **9-step spine**. Each step: sub-circuit, component list, interface nets, teaching keypoints. Stable — the map of the whole build. |
| `NEXT_STEP_PROMPT.md` | The **live "do this next" prompt**. Seeded with Step 1; each step agent overwrites it with the next step's prompt (adapted to what actually got built). Always start a new session by reading this. |
| `BUILD_LOG.md` | Append-only history: per step → date, agent, what was built, the step-draft ERC result, any deviation from the reference. |
| `PURCHASED_COMPONENTS.md` | **Footprint map** for parts you bought + passives. Agents assign these footprints on every placed symbol. |
| `steps/NN_<slug>/` | Per-step output (created by the step's agent): the markdown lesson + a standalone openable KiCad draft of just that sub-circuit. |

**Your master schematic** lives under `../Master Design/EvkaPosition_v2/` — a KiCad project **you edit by
hand**. Agents must **never** modify anything in that folder (`.kicad_sch`, `.kicad_pro`, `.kicad_pcb`,
backups, lock files). Agents only write step drafts under `steps/NN_<slug>/`. You copy each step into the
master while checking against the draft.

Recommended master settings: **grid 2.54 mm (100 mil)**; paper A4 to match the reference (parts may sprawl
past the border) or A2 to contain them; units mm.

### Agent forbidden paths (read-only)

| Path | Role |
|---|---|
| `../Master Design/EvkaPosition_v2/*` | User's live master — **no agent edits** |
| `../EVKA_position_v2.kicad_sch` (+ `.kicad_pro`, `.kicad_pcb`) | As-built reference — extract only |
| `MASTER_PLAN.md` | Stable spine — agents read, do not rewrite |

Agents may read the master/reference for net names and coords; all KiCad MCP **writes** go to
`steps/NN_<slug>/` only.

## How a step agent works (one step per run; may be a different agent / session each time)

1. Read `MASTER_PLAN.md` + `NEXT_STEP_PROMPT.md` + **`PURCHASED_COMPONENTS.md`**, and the reference
   `../EVKA_position_v2.kicad_sch` for the exact parts/nets of this step.
2. `create_project` at `steps/NN_<slug>/`; place this step's parts on a **2.54 mm-multiple grid** via the
   KiCad MCP; **assign the correct Footprint** from `PURCHASED_COMPONENTS.md` on every populated symbol;
   add net labels including the **interface nets** (the wires that bridge to neighbouring steps);
   add `PWR_FLAG` on any power net the step introduces. `run_erc` on the draft — a sub-circuit in isolation
   may carry benign warnings from floating interface nets; document them, don't chase 0-error here.
3. Write `steps/NN_<slug>/NN_<slug>.md`: ASCII schematic + component table **with Footprint column** + net
   table + keypoints, all extracted from the reference (fidelity over invention).
4. Append a `BUILD_LOG.md` entry, then **overwrite `NEXT_STEP_PROMPT.md`** with the next step's prompt.
5. Stop. The user copies the step into `Master Design/EvkaPosition_v2/` by hand while checking — the agent
   never touches the master files.

## Inherited KiCad MCP rules (do not relearn the hard way)

- KiCad MCP (`mcp__kicad__*`), swig backend, stateless via `schematicPath`. `save_project` is a **no-op** —
  edits persist directly to the `.kicad_sch`.
- Place every component on a **2.54 mm-multiple grid** so pins land on the connection grid.
- **NEVER run `snap_to_grid`** — it moves components and net labels independently and detaches labels from
  pins (caused a 29-error revert once).
- Connectivity is **net-label based** (same-named labels merge). Each power net (`+5V`, `+3V3`, `GND`,
  `V_EXT_PROT`, `BAT_PLUS`, …) needs a `PWR_FLAG` or ERC raises `power_pin_not_driven`.
- `74xx:74HC14` is a **7-unit** symbol — unit 7 is the power-only unit carrying pin 14 (VCC) / pin 7 (GND).
  **Footprint must be SOIC-14** (`Package_SO:SOIC-14_3.9x8.7mm_P1.27mm`) — purchased part is SOIC, not DIP.
- Full conventions: `../docs/KICAD_AGENT_INSTRUCTIONS.md`.
- Footprint map: `PURCHASED_COMPONENTS.md` (purchased parts + passives; overrides stale DIP-14 BOM text).

Note: a `~...kicad_pro.lck` may exist on the reference project (KiCad open). Step drafts are *separate*
projects, so they don't collide.
