# EVKA GUI Unification Log

Most recent first. Single-agent implementation unless this file states otherwise.

| Date | Agent | Entry |
|---|---|---|
| 2026-07-09 | OpenCode | **Final polish**: fixed dead conditional in `calibration.py:241` (removed redundant ternary — firmware uses single `SET_PPR_ROTARY` for both axes); fixed JS indentation in `WebDashboard.cpp` `onWsMessage` handler (SYSINFO/BATT/POINT blocks). All checks pass: `pytest -q` (62 passed), `compileall`, `pio run` (esp32s3_v4, wemos_d1_r32, button_remote). |
| 2026-07-09 | OpenCode | Phase 1 complete. Canonical GUI is `tools/evka_gui` with `python -m tools.evka_gui` and `evka-gui`; `tools/evka_gui_v2` now contains deprecation shims. Added unified GUI operator parity, calibration capture helpers, TCP/WebSocket `BATT` parity, WebDashboard battery polling/display, Windows CMD `BATT` parsing, and docs updates. Verification passed: `pytest tools/evka_gui/tests -q`, `python -m compileall tools/evka_gui tools/evka_gui_v2 tools/position_checker`, offscreen Qt instantiate, `pytest -q` (62 passed), `pio run -e esp32s3_v4`, and `dotnet build CMDScanner.csproj` (success with existing nullability warnings). |
| 2026-07-09 | OpenCode | Phase 0 audit completed. Approved decisions captured: canonical package `tools/evka_gui`, command `python -m tools.evka_gui`, single-agent implementation, and TCP/WebSocket `BATT` parity. Implementation started. |
