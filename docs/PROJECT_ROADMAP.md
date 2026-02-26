# Project Roadmap — evka_position

## Completed
- [x] Phase 1: DWE3000 quadrature rework (GPIO 16/17/18)
- [x] Phase 2: Individual hardware tests — draw-wire verified
- [x] Phase 3: Phi pin remap (GPIO 3→27, GPIO 5→26)
- [x] Phase 4: PlatformIO migration (.ino→.cpp), PPR correction (1480), test suite

## In Progress
- [ ] Phase 5: Full 3-encoder integration test
  - Flash main firmware (wemos_d1_r32)
  - Verify all 3 encoders produce correct spherical + Cartesian output
  - Test ZERO command, verify re-calibration
  - Log sample DATA CSV output for visualization testing

## Planned
- [ ] Phase 6: Python visualization tool
  - Update `tools/position_checker/` to work with current DATA format
  - Real-time 3D scatter plot (matplotlib)
  - Serial reader with auto-reconnect
  - GUI with Zero button, live stats panel
  - Test with recorded and live data

- [ ] Phase 7: Calibration refinement
  - Compare measured PPR (1480) against multiple rotation counts
  - Investigate datasheet vs measured PPR discrepancy
  - Document final calibration procedure

- [ ] Phase 8: System validation & documentation freeze
  - End-to-end accuracy test at known positions
  - Update System_Architecture.md with final measured accuracy
  - Tag release version
