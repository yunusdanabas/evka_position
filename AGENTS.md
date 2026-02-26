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
- [ ] Phase 6: Python visualization tool update
- [ ] Phase 7: Final system validation

## Current Configuration (source of truth: SphericalSensor.h)
| Constant | Value |
|---|---|
| PPR_ROTARY | 1480.0 (measured) |
| PPR_WIRE | 2000.0 |
| DEG_PER_PULSE | ~0.2432 |
| MM_PER_PULSE | 0.1 |
| Pins Theta | GPIO 2, 4 |
| Pins Phi | GPIO 27, 26 |
| Pins Wire | GPIO 16, 17, 18(Z) |

## Activity Log
(Most recent first. Format: date | agent | summary)

| Date | Agent | Changes |
|------|-------|---------|
| 2026-02-26 | Claude Code | Phase 4: Updated PPR_ROTARY 5000→1480, synced all docs, cleaned repo, created AGENTS.md and PROJECT_ROADMAP.md |
| 2026-02-21 | Claude Code | Phase 3: Remapped phi pins GPIO 3→27, GPIO 5→26 |
| 2026-02-18 | Claude Code | Phase 2: DWE3000 quadrature rework, pin remap 6/7→16/17 |
