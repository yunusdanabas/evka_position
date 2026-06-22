# EVKA_position_v2 — PCB design workspace map

5V positioning-board PCB for the ESP32-S3 spherical sensor. This folder holds
several KiCad projects with **distinct roles** — don't confuse them.

| Path | Role |
|---|---|
| `Master Design/EvkaPosition_v2/` | **Authoritative master** — the live, hand-built project. PCB layout happens here. Edit this one. |
| `EVKA_position_v2.kicad_*` (this dir) | **Reference draft** — read-only source of truth the master was built from. Don't edit. |
| `step_by_step/` | Co-build workspace: 9 sub-circuit steps. Spine = `MASTER_PLAN.md`, live next-step = `NEXT_STEP_PROMPT.md`, history = `BUILD_LOG.md`. |
| `docs/` | Design docs — BOM, schematic (`circuit_schematic.md`), layout guide, KiCad plans, sourcing. Start at `docs/README.md`. |
| `libs/` | All custom `.pretty` footprint libraries. Register these paths in KiCad's footprint library table. |
| `exports/` | Generated PDF/SVG — regenerable from the design, not authoritative. |

Auto-backup ZIPs (`*-backups/`), lock files, and `*.kicad_prl` are gitignored —
local-only, not part of the committed design.
