# AGENTS.md — Multi-Agent Collaboration Log

## Rules
- Every agent MUST log their changes in the Activity Log below
- Read the full log before starting work to avoid conflicts
- Update CLAUDE.md if you change any firmware constants or pin assignments

## Project Status
- [x] Phase 1: DWE3000 quadrature rework
- [x] Phase 2: Draw-wire encoder test (verified)
- [x] Phase 3: Phi pin remap (GPIO 27/26)
- [x] Phase 4: .ino→.cpp migration, PPR correction, test restructuring
- [ ] Phase 5: Full 3-encoder integration test
- [x] Phase 6: Python visualization tool update (software complete)
- [ ] Phase 7: Final system validation

## Current Configuration (source of truth: SphericalSensor.h)
| Constant | Value |
|---|---|
| PPR_ROTARY | 1480.0 (measured) |
| PPR_WIRE | 2000.0 |
| DEG_PER_PULSE | ~0.2432 |
| MM_PER_PULSE | 0.1 |
| ENABLE_BATTERY_MONITOR | 0 (default, optional battery path) |
| Pins Theta | GPIO 14, 12 |
| Pins Phi | GPIO 27, 26 |
| Pins Wire | GPIO 32, 33, 18(Z) |

## Activity Log
(Most recent first. Format: date | agent | summary)

| Date | Agent | Changes |
|------|-------|---------|
| 2026-03-03 | Codex (GPT-5) | Resolved code-review findings: restored valid data flow after zeroing by validating limited spherical state, hardened replay loader against missing/unreadable files, and added replay loader unit tests |
| 2026-03-03 | Codex (GPT-5) | Added hardware calibration files pack under `docs/calibration/` (theta/phi/draw-wire procedures, CSV templates, final calibration record template) and linked Phase 7 roadmap + final integration validation checklist |
| 2026-03-03 | Codex (GPT-5) | Implemented Phase 5-7 software completion: firmware non-blocking serial commands (`ZERO`,`PING`,`STATUS`), battery monitor compile flag default OFF, validity-flow fix, visualizer reconnect/replay/csv logging/performance upgrade, unit tests, integration validation doc, and diagram-tool path wrappers |
| 2026-02-26 | Claude Code | Phase 4: Updated PPR_ROTARY 5000→1480, synced all docs, cleaned repo, created AGENTS.md and PROJECT_ROADMAP.md |
| 2026-02-21 | Claude Code | Phase 3: Remapped phi pins GPIO 3→27, GPIO 5→26 |
| 2026-02-18 | Claude Code | Phase 2: DWE3000 quadrature rework, pin remap 6/7→16/17 |
