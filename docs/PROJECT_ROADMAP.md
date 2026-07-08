# Project Roadmap — evka_position

## Completed
- [x] Phase 1: DWE3000 quadrature rework (GPIO 16/17/18)
- [x] Phase 2: Individual hardware tests — draw-wire verified
- [x] Phase 3: Pin remap (Theta→GPIO 14/12, Phi→GPIO 32/35)
- [x] Phase 4: PlatformIO migration (.ino→.cpp), PPR correction (1480→20000 X4), test suite
- [x] Phase 6 (software): Python visualization update
  - [x] Serial auto-reconnect with status routing
  - [x] Replay mode from CSV / raw `DATA,` dumps
  - [x] Optional CSV logger and expanded CLI flags
  - [x] In-place plot updates (no per-frame axis clear)
  - [x] `unittest` coverage for parser/store/reconnect path
- [x] Extensive code & documentation audit + remediation (2026-04-08)
  - [x] Three-pass audit: Claude (all source files), Codex (read-only + build verify), Cursor (first-pass fixes)
  - [x] Thread safety: WebSocket pending-command String race → `portMUX_TYPE` 4-slot queue; CmdTcpServer single-slot → 4-slot queue
  - [x] Protocol: `ENABLE_REMOTE_WIFI_CONFIG` enforced centrally; `STATUS` replies to TCP/WS; `GET_IP` guarded for `ENABLE_WIFI=0`; `CAL_W` negative-count error improved; overflow discard state (serial + TCP); WS fragment guard
  - [x] Math: EMA filter primed reset on all zero operations; consistent sph/cart validation
  - [x] Docs: E30S6 → E40S6 across all files; dead links in `docs/resources.md` fixed
  - [x] Build: `espressif32@6.12.0` pinned; exact library versions; library caret ranges removed
  - [x] Full findings log: superseded by `docs/WIFI_PERFORMANCE_ISSUES_LOG.md` (2026-04-08 section)
- [x] WiFi performance & stability hardening (2026-04-08)
  - [x] Disabled modem sleep (`WiFi.setSleep(WIFI_PS_NONE)`) — primary cause of sluggishness in AP+STA mode
  - [x] Pinned AP to channel 1 (`WiFi.softAP(..., ESPNOW_CHANNEL)`) — prevents channel drift during STA scans
  - [x] Added `WIFI_FAST_SCAN` for STA — reduces radio contention on shared AP channel
  - [x] Fixed WebSocket command buffer truncation (32 → 128 bytes) — `WIFI_SET` commands were silently corrupted
  - [x] Moved `cleanupClients()` to connect/disconnect only — was firing 60×/sec on DATA events
  - [x] Added JS `_dirty3d` dirty flag — 3D canvas now only repaints on new data or gesture, not 60 Hz unconditional
  - [x] Documented 192.168.1.x subnet conflict in `SphericalSensor.h` and `README.md`
  - [x] Full diagnostic log: `docs/WIFI_PERFORMANCE_ISSUES_LOG.md`

## In Progress
- [x] v4 PCB firmware port (2026-07-08) — ESP32-S3-DevKitC-1 board; new PlatformIO env `esp32s3_v4` (`-DPCB_V4`); pins THETA 7/8, PHI 4/5, WIRE 9/10, battery ADC GPIO1; switched both boards to `ESP32Encoder` (hardware PCNT); battery monitor enabled. Both envs build clean. Verified against v4 schematic + PCB pad-nets. Hardware bring-up pending.
- [ ] Phase 5: Full 3-encoder integration test
  - [x] Firmware integration hardening (non-blocking serial + `PING`/`STATUS`)
  - [x] Backward-compatible serial protocol retained (`DATA,...` unchanged)
  - [x] Battery monitoring made optional for 5V-adapter prototype (`ENABLE_BATTERY_MONITOR=0` default)
  - [ ] Flash main firmware (`wemos_d1_r32` classic, or `esp32s3_v4` on the v4 PCB) on final wiring
  - [ ] Verify all 3 encoders produce correct spherical + Cartesian output
  - [ ] Test ZERO command and status lines on hardware
  - [ ] Log sample DATA CSV output for visualization testing

- [ ] Phase 5b: Circuit board design & fabrication
  - [x] ASCII circuit schematic (`docs/hardware_design/5v/circuit_schematic.md`)
  - [x] Bill of materials (`docs/hardware_design/5v/bill_of_materials.md`)
  - [x] PCB layout guide (`docs/hardware_design/5v/pcb_layout_guide.md`)
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
  - Compare measured PPR (20000 @ X4 quadrature) against multiple rotation counts
  - PPR discrepancy resolved: X4 quadrature accounts for 5000×4=20000; wire calibrated to 8020
  - Document final calibration procedure
  - Run calibration pack and store finalized record in `docs/calibration/`
  - Run software-assisted checklist in `docs/integration/final_integration_validation.md`

- [ ] Phase 8: System validation & documentation freeze
  - End-to-end accuracy test at known positions
  - Update `docs/hardware_design/system_architecture.md` with final measured accuracy
  - Tag release version
