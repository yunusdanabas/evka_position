# GUI Consolidation — Audit & Design

**Date:** 2026-07-09  
**Baseline:** `tools/evka_gui_v2` → canonical `tools/evka_gui`  
**Status:** Approved for implementation

## Feature Matrix

| Feature | evka_gui_v2 | position_checker | cmd_gui | WebDashboard | gui.cs |
|---|:---:|:---:|:---:|:---:|:---:|
| Live X/Y/Z + R/θ/φ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3D trail + 2D plots | ✓ | ✓ | — | ✓ | — |
| Serial transport | ✓ | ✓ | — | — | — |
| TCP transport | ✓ | — | ✓ | WS | ✓ |
| Software zero (all) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Per-axis SW zero | — | — | ✓ | ✓ | partial |
| Hardware ZERO | ✓ | ✓ | ✓ | ✓ | ✓ |
| Min/max + reset | — | — | ✓ | ✓ | — |
| Saved points | ✓ | — | ✓ | ✓ | ✓ |
| Session CSV export | — | csv-log | — | ✓ | — |
| Replay mode | — | ✓ | — | — | — |
| WiFi config | — | — | ✓ | ✓ | ✓ |
| SYSINFO panel | status only | — | ✓ | ✓ | partial |
| ESP-NOW remote LEDs | ✓ | — | ✓ | ✓ | — |
| Battery (serial) | ✓ | — | — | — | — |
| Calibration wizard | — | — | — | ✓ | — |
| BLINK test | ✓ | — | — | — | — |
| Snapshots | — | — | — | ✓ | — |

## Gap List (baseline → target)

1. Min/max tracking and per-axis software zero (from cmd_gui / WebDashboard)
2. WiFi credential save/forget + router IP display (from cmd_gui)
3. Dedicated SYSINFO panel with 5 s polling (from cmd_gui)
4. Calibration window — wire/theta/phi/endpoint (from WebDashboard)
5. Session CSV export and replay mode (from visualizer / WebDashboard)
6. AP (`192.168.1.50`) vs STA (`192.168.1.84` / ASMETAL) quick-select
7. Naming: `evka_gui` canonical; `_v2` deprecated shim

## Chosen Approach

**Evolve evka_gui_v2 in place → rename to `tools/evka_gui`**

- Single PyQt package, one entry point: `python -m tools.evka_gui`
- Calibration as **non-modal secondary window** (live position visible during wire pull)
- WebDashboard: add BLINK button; main page already has most features
- `evka_gui_v2`, `position_checker.main`, `position_checker.cmd_main` → deprecation shims
- TCP protocol unchanged; Windows `gui.cs` unchanged (extensions deferred)

## UX Layout

**Main window (single page, no tabs):**
- Left scroll panel: Connection (Serial/TCP, AP/STA presets) → Position (XYZ, Rθφ, min/max, zero) → Battery → Remote → WiFi → SYSINFO → Commands → Saved points → Export
- Right: 3D + XY/XZ/YZ + trail controls
- Menu/toolbar: Open Calibration, Quick IPT, Export Session CSV

**Calibration window (separate):**
- Tabs: Wire | Theta | Phi | Endpoint
- Sends `CAL_W`, `CAL_T`, `CAL_P`, `SET_PPR_*`, `SAVE_PPR`, `CONSTANTS`
