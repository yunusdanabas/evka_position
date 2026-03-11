# Project Roadmap — evka_position

## Completed
- [x] Phase 1: DWE3000 quadrature rework (GPIO 16/17/18)
- [x] Phase 2: Individual hardware tests — draw-wire verified
- [x] Phase 3: Phi pin remap (GPIO 3→27, GPIO 5→26)
- [x] Phase 4: PlatformIO migration (.ino→.cpp), PPR correction (1480), test suite
- [x] Phase 6 (software): Python visualization update
  - [x] Serial auto-reconnect with status routing
  - [x] Replay mode from CSV / raw `DATA,` dumps
  - [x] Optional CSV logger and expanded CLI flags
  - [x] In-place plot updates (no per-frame axis clear)
  - [x] `unittest` coverage for parser/store/reconnect path

## In Progress
- [ ] Phase 5: Full 3-encoder integration test
  - [x] Firmware integration hardening (non-blocking serial + `PING`/`STATUS`)
  - [x] Backward-compatible serial protocol retained (`DATA,...` unchanged)
  - [x] Battery monitoring made optional for 5V-adapter prototype (`ENABLE_BATTERY_MONITOR=0` default)
  - [ ] Flash main firmware (wemos_d1_r32) on final wiring
  - [ ] Verify all 3 encoders produce correct spherical + Cartesian output
  - [ ] Test ZERO command and status lines on hardware
  - [ ] Log sample DATA CSV output for visualization testing

- [ ] Phase 5b: Circuit board design & fabrication
  - [x] ASCII circuit schematic (`docs/hardware_design/circuit_schematic.md`)
  - [x] Bill of materials (`docs/hardware_design/bill_of_materials.md`)
  - [x] PCB layout guide (`docs/hardware_design/pcb_layout_guide.md`)
  - [x] Visual diagram (removed — superseded by ASCII schematic)
  - [x] Battery monitoring firmware (GPIO 36 ADC, `readBattery()`)
  - [ ] Solder Phase 1 — power section (D1, D2, caps, TP4056, MT3608, connectors)
  - [ ] Test: Verify 5V_RAIL (external → 4.8V, LiPo → 5.1V)
  - [ ] Solder Phase 2 — ESP32 mount (female headers, VIN + GND)
  - [ ] Test: ESP32 boot + serial output
  - [ ] Solder Phase 3 — signal conditioning (7× dividers, encoder connectors, ferrite beads)
  - [ ] Test: Per-encoder count verification
  - [ ] Solder Phase 4 — protection (TVS, reset btn, LEDs, test points)
  - [ ] Full integration test: all 3 encoders on permanent board

## Planned
- [ ] Phase 7: Calibration refinement
  - Compare measured PPR (1480) against multiple rotation counts
  - Investigate datasheet vs measured PPR discrepancy
  - Document final calibration procedure
  - Run calibration pack and store finalized record in `docs/calibration/`
  - Run software-assisted checklist in `docs/final_integration_validation.md`

- [ ] Phase 8: System validation & documentation freeze
  - End-to-end accuracy test at known positions
  - Update System_Architecture.md with final measured accuracy
  - Tag release version
