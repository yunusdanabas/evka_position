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
- `WIFI_STA_DEFAULT_SSID = "CMD-YAZILIM"` (compile-time default; runtime credentials stored in NVS)

## TCP Protocol Quick Reference

Client -> ESP32 (newline-delimited):

```text
GET_IP
ZERO
WIFI_SET:<ssid>,<password>
WIFI_AYAR:<ssid>,<password>
```

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
ACK:ZERO
ACK:WIFI_SAVED
ERR:WIFI_INVALID
ERR:WIFI_CFG_DISABLED
ERR:SSID_INVALID
ERR:PASS_TOO_SHORT
ERR:UNKNOWN_CMD
```

Note: Firmware may also emit additional lines (`SENSOR,...`, `SYSINFO,...`) for enhanced tools. CMD clients that only parse `X...` and `STA_IP:...` continue to work.
All other newline-delimited commands are forwarded to firmware `processCommand()`
(`PING`, `STATUS`, `CONSTANTS`, `CAL_*`, `SET_PPR_*`, `SAVE_PPR`, etc.).
For enhanced clients parsing `SENSOR,...`, the field order is:
`SENSOR,<r_mm>,<theta_deg>,<phi_deg>,<is_valid>,<frame_count>`.

## Linux CMD GUI (Included Tool)

Run the Linux CMD-compatible GUI from repo root:

```bash
python -m tools.position_checker.cmd_main
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
- `tools/position_checker/cmd_gui.py`
- `tools/position_checker/tcp_client.py`
- `README_TR.md` — Turkish WiFi connection guide for end users
- `docs/WIFI_PERFORMANCE_ISSUES_LOG.md` — WiFi diagnostics and AP resilience notes
