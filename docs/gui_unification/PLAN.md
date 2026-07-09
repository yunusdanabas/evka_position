# EVKA GUI Unification Plan

Status: approved for implementation.

## Decisions

| Item | Decision |
|---|---|
| Canonical Python package | `tools/evka_gui` |
| Canonical command | `python -m tools.evka_gui` |
| Console script | `evka-gui` |
| Baseline | `tools/evka_gui_v2` |
| Work style | Single agent only |
| Battery parity | Broadcast existing `BATT,<voltage>,<pct>,<is_low>` over TCP/WebSocket after `STATUS` |
| Keep separate | `tools/ipt`, `tools/remote_tester` |

## Target Product

One unified desktop GUI for daily operator use, plus firmware WebDashboard parity for field/phone use.

Main desktop page must show, without tab switching:

| Area | Required Features |
|---|---|
| Connection | Serial or TCP, ASMETAL STA `192.168.1.84`, AP fallback `192.168.1.50`, persisted last endpoint |
| Live position | X/Y/Z, R/theta/phi, validity, frame/timestamp |
| Views | 3D trail plus XY/XZ/YZ projections, clear trail |
| Zeroing | Hardware zero, software zero all, per-axis software zero, clear software zero |
| Session | Saved points, origin, min/max, distance from origin, distance between last two points, CSV export |
| Diagnostics | Router IP, RSSI, heap, uptime, TCP clients, command status |
| Remote | ESP-NOW button LEDs and heartbeat when available |
| Battery | Serial and TCP/WebSocket when firmware reports `BATT` |
| Quick commands | `PING`, `BLINK`, `STATUS`, `SYSINFO`, `ZERO*`, save/delete point |

Calibration must be a separate dialog/window:

| Stage | Protocol |
|---|---|
| Wire | `ZERO_W`, `CAL_W <mm>`, mean/spread, `SET_PPR_WIRE`, optional `SAVE_PPR` |
| Theta | `ZERO_T`, turn count, `CAL_T <n>`, `SET_PPR_ROTARY` |
| Phi | `ZERO_P`, turn count, `CAL_P <n>`, `SET_PPR_ROTARY` |
| Endpoint | Capture world/sensor pairs, export CSV, optionally write `tools/calibration/calibration.json` |

## Implementation Steps

1. Create `tools/evka_gui` as the canonical package from the `tools/evka_gui_v2` baseline.
2. Keep old entry points as shims with deprecation messages.
3. Move missing operator features from `position_checker/cmd_gui.py` and WebDashboard into the unified GUI.
4. Add the calibration dialog using existing firmware commands.
5. Add TCP/WebSocket `BATT` parity in firmware with compatible clients.
6. Update docs and protocol notes.
7. Verify with `pytest` and `pio run -e esp32s3_v4`.

## Manual Checklist

| Check | Expected |
|---|---|
| Serial GUI | Live `DATA,`, commands, battery, calibration commands |
| AP TCP GUI | `192.168.1.50:8080`, live `X/SENSOR`, saved points, SYSINFO, remote LEDs |
| STA TCP GUI | `192.168.1.84:8080`, same as AP |
| Web AP | `http://192.168.1.50`, live view, calibration, battery after `STATUS` |
| Web STA | `http://192.168.1.84`, same as AP |
| Windows CMD | Existing TCP behavior still works; extra `BATT` line does not break parsing |
