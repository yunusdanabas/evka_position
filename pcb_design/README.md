# pcb_design — KiCad workspaces

Four board revisions live side by side. **Only v4 is fabricated and current** —
the rest are kept for reference.

| Workspace | Status | Notes |
|---|---|---|
| `EVKA_position_v4/` | **CURRENT — fabricated** | ESP32-S3-DevKitC-1 carrier; firmware env `esp32s3_v4` (`-DPCB_V4`). Pin map, bring-up, battery, LED: [`EVKA_position_v4/FIRMWARE.md`](EVKA_position_v4/FIRMWARE.md) |
| `EvkaPosition_v2/` | Superseded | Full-featured 5V design (74HC14 buffers, load-sharing). ERC-clean but never fabricated. Its design docs were removed on migration to v4 — recover from git history if needed |
| `EVKA_position_v3/` | Superseded | Stripped "simple" variant of v2 (direct-GPIO dividers, no buffers). Never fabricated |
| `EVKA_position_v5/` | Experimental / WIP | Layout exploration after v4; not fabricated, no firmware support |

Netlists are generated files — regenerate with
`kicad-cli sch export netlist <project>.kicad_sch` (a stray root-level
`EvkaPosition_v2.net` is git-ignored for this reason). KiCad backup folders
(`*-backups/`) are git-ignored too.
