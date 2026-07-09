# CMD Software Integration

This document is the quick guide for integrating CMD-compatible software with this codebase.

For full technical background and design rationale, see `docs/integration/CMD_INTEGRATION_CHANGELOG.md`.

## What Was Integrated

- CMD-compatible WiFi AP settings (`CMDCNC_EVKA`, `cmdcnc1234`, `192.168.1.50`)
- CMD-compatible raw TCP server (`port 8080`)
- CMD-compatible position stream format: `X<val>,Y<val>,Z<val>`
- CMD command compatibility for:
  - `GET_IP`
  - `ZERO`
  - `WIFI_SET:<ssid>,<pass>`
  - `WIFI_AYAR:<ssid>,<pass>` (legacy alias kept for compatibility)

## Firmware Settings Used

These values are currently defined in `firmware/src/SphericalSensor.h`:

- `ENABLE_WIFI = 1`
- `ENABLE_CMD_TCP = 1`
- `ENABLE_REMOTE_WIFI_CONFIG = 1`
- `CMD_TCP_PORT = 8080`
- `WIFI_AP_SSID = "CMDCNC_EVKA"`
- `WIFI_AP_PASSWORD = "cmdcnc1234"`
- AP IP = `192.168.1.50`
- `WIFI_STA_DEFAULT_SSID = "ASMETAL"` (compile-time default; runtime credentials stored in NVS)

## TCP Protocol Quick Reference

Client -> ESP32 (newline-delimited):

```text
GET_IP
ZERO
BLINK
WIFI_SET:<ssid>,<password>
WIFI_AYAR:<ssid>,<password>
```

`BLINK` → `ACK:BLINK`; flashes the board status LED white for ~0.7 s (connection
test over serial, TCP, or WebSocket). On boards without an RGB LED the ACK still
returns; classic ESP32 builds blink GPIO2 instead.

Note: `WIFI_SET`/`WIFI_AYAR` are active (`ENABLE_REMOTE_WIFI_CONFIG = 1`).
On success the device saves credentials to NVS and reboots, sending `ACK:WIFI_SAVED`
to all connected clients (serial, TCP, WebSocket) before restarting.
If the flag is ever disabled (`0`), TCP and WebSocket paths return `ERR:WIFI_CFG_DISABLED`.

WiFi credential validation (applies to both TCP and serial paths):
- SSID must be 1–32 characters → `ERR:SSID_INVALID` if empty or >32 chars
- Password must be empty (open network) or ≥8 characters → `ERR:PASS_TOO_SHORT`
ESP32 -> Client (newline-delimited):

```text
STA_IP:<ipv4>
STA_IP:NOT_CONNECTED
X<value>,Y<value>,Z<value>
SENSOR,<r>,<theta>,<phi>,<valid>,<frame>
SYSINFO,<rssi>,<heap>,<uptime_s>,<tcp_clients>
BATT,<voltage>,<percent>,<is_low>
POINT,<idx>,<x>,<y>,<z>,<r>,<theta>,<phi>
DEL_POINT,<idx>
REMOTE_BTN:<0|1>
REMOTE_HB
ACK:ZERO
ACK:BLINK
ACK:WIFI_SAVED
ERR:WIFI_INVALID
ERR:WIFI_CFG_DISABLED
ERR:SSID_INVALID
ERR:PASS_TOO_SHORT
ERR:NO_POINTS
ERR:UNKNOWN_CMD
```

Note: Firmware may also emit additional lines (`SENSOR,...`, `SYSINFO,...`,
`BATT,...`, `POINT,...`, `DEL_POINT,...`, `REMOTE_BTN:...`, `REMOTE_HB`) for enhanced tools.
CMD clients that only parse `X...` and `STA_IP:...` continue to work.
All other newline-delimited commands are forwarded to firmware `processCommand()`
(`PING`, `STATUS`, `CONSTANTS`, `CAL_*`, `SET_PPR_*`, `SAVE_PPR`,
`SAVE_POINT`, `DEL_POINT`, etc.).
For enhanced clients parsing `SENSOR,...`, the field order is:
`SENSOR,<r_mm>,<theta_deg>,<phi_deg>,<is_valid>,<frame_count>`.
For enhanced clients parsing `BATT,...`, the field order is:
`BATT,<voltage>,<percent>,<is_low>`; it is sent after `STATUS` when battery monitoring is enabled.

### Linux CMD GUI features (beyond minimal CMD protocol)

The unified GUI (`tools/evka_gui`) and legacy Linux CMD panel (`--legacy-cmd-gui`)
add:

| Feature | Behavior |
|---------|----------|
| Software Zero (All) / X=0 / Y=0 / Z=0 | Client-side display offset; R/θ/φ recomputed from zeroed XYZ |
| Clear Software Zero | Clears offsets without sending `ZERO` |
| Hardware Zero | Sends `ZERO`; clears software zero |
| Reset Min/Max | Session statistics only |
| Saved points | `SAVE_POINT` / `DEL_POINT`; list is session-local |
| Remote indicators | `REMOTE_BTN:0/1`, `REMOTE_HB` link status |
| SYSINFO panel | RSSI, heap, uptime, TCP client count |
| Battery panel | `BATT,<voltage>,<percent>,<is_low>` after `STATUS` |

Software zero is cleared on TCP disconnect. Saved-point indices on the device
(`pt_idx`) persist across reconnects; the GUI list does not.

## Unified Host GUI (recommended)

```bash
python -m tools.evka_gui                              # open disconnected
python -m tools.evka_gui --tcp 192.168.1.84:8080      # STA (ASMETAL)
python -m tools.evka_gui --tcp 192.168.1.50:8080      # AP direct
python -m tools.evka_gui --serial /dev/ttyUSB0
```

Merges the Linux CMD panel, serial visualizer, and v4 control GUI into one window.
Calibration opens in a separate window. Web dashboard (`http://192.168.1.50`) stays
at feature parity for phone/field use.

Legacy entry points (deprecated):

```bash
python -m tools.position_checker.cmd_main              # → evka_gui --tcp
python -m tools.position_checker.cmd_main --legacy-cmd-gui
python -m tools.evka_gui_v2                            # → evka_gui
```

## Linux CMD GUI (legacy shim)

Run the old Linux CMD-compatible GUI:

```bash
python -m tools.position_checker.cmd_main --legacy-cmd-gui
```

Or use the unified GUI (recommended):

```bash
python -m tools.evka_gui --tcp 192.168.1.84:8080
```

Visualizer protocol conventions (prefixes, field ordering, phi policy, and
default endpoints) are centralized in `tools/position_checker/cmd_main.py`.

Default target:

- IP: `192.168.1.84` (example STA target)
- Port: `8080`
- AP fallback IP: `192.168.1.50`

AP/STA resilience update:
- Firmware keeps AP fallback reachable when STA loses upstream WiFi by using event-driven AP reassertion and controlled STA reconnect backoff.
- If `192.168.1.50` is unreachable, first rule out OS routing conflict (disable home/office WiFi on the client and reconnect to `CMDCNC_EVKA` only).
- Deep diagnostics: `docs/WIFI_PERFORMANCE_ISSUES_LOG.md` (Issue 8).

## Related Files

- `firmware/src/CmdTcpServer.cpp`
- `firmware/src/CmdTcpServer.h`
- `firmware/src/EvkaPosition.cpp`
- `tools/evka_gui/` — **canonical** unified control + 3D GUI (Serial/TCP/replay)
- `tools/evka_gui_v2/` — deprecated shim → `evka_gui`
- `tools/position_checker/cmd_gui.py` — legacy Linux CMD panel (`--legacy-cmd-gui`)
- `tools/position_checker/tcp_client.py`
- `README_TR.md` — Turkish WiFi connection guide for end users
- `docs/WIFI_PERFORMANCE_ISSUES_LOG.md` — WiFi diagnostics and AP resilience notes
