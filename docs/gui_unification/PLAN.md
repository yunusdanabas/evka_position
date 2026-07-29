# EVKA GUI Unification Plan

Status: approved for implementation.

## Decisions

| Item | Decision |
|---|---|
| Canonical Python package | `tools/evka_gui` |
| Canonical command | `python -m tools.evka_gui` |
| Console script | `evka-gui` |
| Baseline | former `tools/evka_gui_v2` (removed 2026-07-16; now only `tools/evka_gui`) |
| Work style | Single agent only |
| Battery parity | Broadcast existing `BATT,<voltage>,<pct>,<is_low>` over TCP/WebSocket after `STATUS` |
| Keep separate | `tools/ipt`, `tools/remote_tester` |

## Target Product

One unified desktop GUI for daily operator use, plus firmware WebDashboard parity for field/phone use.

Main desktop page must show (Connection, Live position and Views always visible; the
rest in left-column tabs — the original "without tab switching" wording did not
survive contact with a 1366×768 screen):

| Area | Required Features |
|---|---|
| Connection | Serial, TCP, WebSocket (`ws://host/ws`), CSV replay, named connection profiles; **auto-reconnect with backoff** |
| Live position | X/Y/Z, R/theta/phi, validity, frame/timestamp; copy coords shortcuts |
| Views | 3D trail (rotate + **wheel zoom**) + XY/XZ/YZ; layer toggles; IPT on 2D + 3D; adjustable trail cap |
| Session | Saved points, snapshots (capture/export), origin, min/max, distances, CSV exports; **record the live stream** |
| Diagnostics | SYSINFO strip, CONSTANTS/PPR strip, `RAW_COUNTS`, compact protocol log (left column, **not** a dock) |
| Remote | ESP-NOW button LEDs; optional **Remote Tester…** window (ButtonRemoteTest firmware) |
| Replay | Pause, speed, step, slider seek |
| Stream | **FREEZE** pauses the view; recording keeps tapping the wire |

Calibration must be a separate dialog/window:

| Stage | Protocol |
|---|---|
| Wire | `ZERO_W`, `CAL_W <mm>`, mean/spread, `SET_PPR_WIRE`, optional `SAVE_PPR` |
| Theta | `ZERO_T`, turn count, `CAL_T <n>`, `SET_PPR_ROTARY` |
| Phi | `ZERO_P`, turn count, `CAL_P <n>`, `SET_PPR_ROTARY` |
| Endpoint | Capture world/sensor pairs and write a session candidate report/JSON; no shared default transform |

Quick IPT is an **inline panel** on the main page plus optional **IPT plots…** pop-out:

| Item | Notes |
|---|---|
| Main panel | **Quick IPT** group: L input, ARM/STOP/SOLVE/CLEAR, result labels |
| 2D overlays | Green capture cloud + orange target + sphere on XY/XZ/YZ session plots |
| Optional pop-out | Toolbar **IPT plots…** — full-height projections (shared `IptPanel` state) |
| WiFi | Toolbar **WiFi Settings…** secondary window (credentials off main scroll panel) |
| Transport | Reuse main connection; feed raw protocol lines in `_drain` |
| Coordinates | Sensor-frame mm only (not software-zero offsets) |
| Standalone | `python -m tools.ipt` unchanged for IPT-only operators |

## Implementation Steps

1. Create `tools/evka_gui` as the canonical package from the former `tools/evka_gui_v2` baseline.
2. Keep old `position_checker` entry points as shims with deprecation messages (`evka_gui_v2` shim later removed).
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
