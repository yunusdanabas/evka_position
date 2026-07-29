# Retained TCP Compatibility Integration

This is the active integration guide for the line-oriented TCP service on port 8080. The historical
vendor C# application has been deleted from the supported workflow; its deletion does **not** remove
or rename the TCP protocol.

The complete source-derived telemetry, command, reply, error, and fan-out contract is
[../PROTOCOL.md](../PROTOCOL.md). Do not maintain a second command table here.

## Compatibility Surface

Current firmware retains:

- AP `CMDCNC_EVKA` / `cmdcnc1234` at `192.168.1.50`.
- Raw TCP server on port `8080`, maximum three clients.
- 20 Hz Cartesian line: `X<value>,Y<value>,Z<value>`.
- 20 Hz companion line: `SENSOR,<r>,<theta>,<phi>,<valid>,<frame>`.
- `GET_IP`, `ZERO`, and current diagnostics/calibration commands.
- `WIFI_AYAR:<ssid>,<pass>` as an alias of `WIFI_SET:<ssid>,<pass>`.

TCP does not emit regular `DATA,...` lines. Clients that need a complete sample must pair each XYZ
line with the following `SENSOR` line. All positions are sensor-frame values.

## Canonical Client

Use `tools/evka_gui`:

```bash
python -m tools.evka_gui --tcp 192.168.1.50:8080
python -m tools.evka_gui --tcp 192.168.1.84:8080
```

The GUI includes live plots, diagnostics, raw zero-relative counts, saved-point events, recording,
Quick IPT, and calibration-session collection. It remains sensor-frame-only; software zero is a
client-side display/session offset, and no accepted world transform exists.

`tools/position_checker.cmd_main` is a legacy compatibility entry point. Do not recreate or add a
new dependency on the deleted vendor C# application.

## Client Requirements

1. Treat TCP as a newline-delimited stream, not one-message-per-`recv()`.
2. Ignore unknown line prefixes so new diagnostics do not break basic XYZ parsing.
3. Pair XYZ and `SENSOR` records in order when validity or spherical values are required.
4. Expect command replies to be broadcast to all TCP clients except direct TCP `GET_IP` replies.
5. Handle asynchronous `REMOTE_BTN`, `REMOTE_HB`, `POINT`, and `DEL_POINT` records.
6. Reconnect with backoff; do not open more than three simultaneous TCP clients.
7. Do not interpret software-zeroed display values as firmware or world coordinates.

## WiFi Configuration

Current source has `ENABLE_REMOTE_WIFI_CONFIG=1`. `WIFI_SET` and `WIFI_AYAR` save/read back
credentials in NVS, return one `ACK:WIFI_SAVED` on the ingress transport, and schedule a reboot
about 500 ms later. Empty password selects an open STA network; `WIFI_SET:,` clears stored
credentials. WPA2 passwords longer than 63 characters are rejected.

These commands are unauthenticated. Fixed credentials and remote state-changing commands are for an
isolated, trusted lab network only. Do not expose TCP port 8080 or WebSocket port 80 to an untrusted
LAN or the internet.

## Current Addresses

| Path | Value |
|---|---|
| AP fallback | `192.168.1.50:8080` |
| STA static profile | `192.168.1.84:8080`, gateway `192.168.1.254` |
| Web dashboard | `http://192.168.1.50` or the STA host |
| WebSocket | `ws://<host>/ws` |

The `192.168.1.x` AP can conflict with a home/office router. Connect directly to `CMDCNC_EVKA` and
disconnect other WiFi paths when diagnosing routing.

## Source Files

- `firmware/src/EvkaPosition.cpp`: command policy and reply generation.
- `firmware/src/CmdTcpServer.cpp`: client limit, line framing, queue, XYZ/SENSOR telemetry.
- `firmware/src/WebDashboard.cpp`: AP/STA and WebSocket behavior.
- [../PROTOCOL.md](../PROTOCOL.md): canonical external contract.
- [CMD_INTEGRATION_CHANGELOG.md](CMD_INTEGRATION_CHANGELOG.md): archived historical rationale.

This prototype has no redistribution license and no public production-readiness claim.
