# CMD Software Integration

This document is the quick guide for integrating CMD-compatible software with this codebase.

For full technical background and design rationale, see `docs/CMD_INTEGRATION_CHANGELOG.md`.

## What Was Integrated

- CMD-compatible WiFi AP settings (`CMDCNC`, `cmdcnc1234`, `192.168.1.50`)
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
- `CMD_TCP_PORT = 8080`
- `WIFI_AP_SSID = "CMDCNC"`
- `WIFI_AP_PASSWORD = "cmdcnc1234"`
- AP IP = `192.168.1.50`

## TCP Protocol Quick Reference

Client -> ESP32 (newline-delimited):

```text
GET_IP
ZERO
WIFI_SET:<ssid>,<password>
WIFI_AYAR:<ssid>,<password>
```

ESP32 -> Client (newline-delimited):

```text
STA_IP:<ipv4>
STA_IP:NOT_CONNECTED
X<value>,Y<value>,Z<value>
ACK:ZERO
ACK:WIFI_SAVED
```

Note: Firmware may also emit additional lines (`SENSOR,...`, `SYSINFO,...`) for enhanced tools. CMD clients that only parse `X...` and `STA_IP:...` continue to work.

## Linux CMD GUI (Included Tool)

Run the Linux CMD-compatible GUI from repo root:

```bash
python -m tools.position_checker.cmd_main
```

Default target:

- IP: `192.168.1.50`
- Port: `8080`

## Related Files

- `firmware/src/CmdTcpServer.cpp`
- `firmware/src/CmdTcpServer.h`
- `firmware/src/EvkaPosition.cpp`
- `tools/position_checker/cmd_gui.py`
- `tools/position_checker/tcp_client.py`
