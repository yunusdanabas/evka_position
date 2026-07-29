# EVKA Runtime Protocol

This is the canonical protocol reference for the existing prototype. It is derived from the current
`firmware/src/EvkaPosition.cpp`, `firmware/src/CmdTcpServer.cpp`, and
`firmware/src/SphericalSensor.cpp`. Source behavior wins if code and documentation diverge.

The vendor C# application has been deleted from the supported workflow. The TCP wire protocol is
retained for compatibility and for `tools/evka_gui`.

## Coordinate and Framing Rules

- All firmware XYZ, spherical values, saved points, and Quick IPT inputs are in the **sensor frame**.
- Firmware and the canonical `tools/evka_gui` do not apply an endpoint/world transform. A passing
  session JSON can be supplied explicitly only to the legacy visualizer.
- Numeric distance fields are millimetres; angle fields are degrees; timestamps are milliseconds.
- Serial and TCP are line-oriented. Commands end with `\n` or `\r`; empty lines are ignored.
- WebSocket commands are complete text frames; surrounding whitespace is trimmed.
- Commands are case-sensitive.

## Endpoints

| Transport | Endpoint | Command input |
|---|---|---|
| Serial | 115200 baud | Newline/carriage-return terminated ASCII |
| TCP | Port `8080`, maximum 3 clients | Newline/carriage-return terminated ASCII |
| WebSocket | `ws://<device>/ws` on port 80 | One complete text frame |
| HTTP | `http://<device>/` | Dashboard only; live data and commands use its WebSocket |

AP defaults are `CMDCNC_EVKA` / `cmdcnc1234` at `192.168.1.50`. The configured STA profile is
static `192.168.1.84/24` with gateway `192.168.1.254`.

## Telemetry Transport Matrix

| Message | Serial | WebSocket | TCP | Cadence/trigger |
|---|:---:|:---:|:---:|---|
| `DATA,<x>,<y>,<z>,<r>,<theta>,<phi>,<valid>,<frame>,<ts_ms>` | Yes | Yes | No | 20 Hz |
| `X<x>,Y<y>,Z<z>` | No | No | Yes | 20 Hz |
| `SENSOR,<r>,<theta>,<phi>,<valid>,<frame>` | No | No | Yes | 20 Hz, immediately after the TCP XYZ line |
| `X=... Y=... Z=... mm | R=... Th=... Ph=... deg` | Yes | No | No | 20 Hz human-readable debug |
| `! INVALID POSITION (out of bounds)` | Yes | No | No | Throttled to at most 1 Hz while invalid |
| `STATUS,...` | On command | On command | On command | Snapshot |
| `BATT,<voltage>,<percent>,<is_low>` | After serial `STATUS` when enabled | Broadcast after network `STATUS` when enabled | Broadcast after network `STATUS` when enabled | On demand, not 20 Hz |
| `REMOTE_BTN:<n>` / `REMOTE_HB` | Yes | Yes | Yes | ESP-NOW event/heartbeat |
| Boot, WiFi, calibration, and ESP-NOW debug text | Yes | No | No | Event driven |

TCP clients must pair each `X...` line with the following `SENSOR,...` line if they need a complete
sample. TCP does not emit `DATA,...` during its regular 20 Hz stream.

### Snapshot and Diagnostic Schemas

```text
STATUS,<is_valid>,<frame_count>,<last_update_ms>,<r_mm>,<theta_deg>,<phi_deg>,<x_mm>,<y_mm>,<z_mm>
BATT,<voltage_v>,<percentage>,<is_low>
CONSTANTS,<ppr_rotary>,<ppr_wire>,<mm_per_pulse>,<deg_per_pulse>
RAW,<theta_counts>,<phi_counts>,<wire_counts>
SYSINFO,<sta_rssi_dbm>,<free_heap_bytes>,<uptime_s>,<tcp_client_count>
POINT,<index>,<x_mm>,<y_mm>,<z_mm>,<r_mm>,<theta_deg>,<phi_deg>
DEL_POINT,<index>
```

`RAW_COUNTS` is intentionally named for diagnostics, but its values are **zero-relative**:
`readRawEncoders()` subtracts the theta, phi, and wire offsets captured at boot or by the relevant
`ZERO*` command. It does not expose absolute hardware counter values.

## Current Commands and Replies

All commands below enter `processCommand()` from Serial, TCP, or WebSocket, except that TCP handles
`GET_IP` directly for the requesting client. Compile-time feature flags can remove WiFi-specific
behavior.

| Command | Success reply | Purpose and current behavior |
|---|---|---|
| `PING` | `ACK:PONG` | Liveness check |
| `BLINK` | `ACK:BLINK` | Requests a roughly 700 ms status-LED overlay |
| `ZERO` | `ACK:ZERO` | Captures all current encoder counters as offsets; resets Cartesian filter priming |
| `ZERO_T` | `ACK:ZERO_T` | Captures theta offset only |
| `ZERO_P` | `ACK:ZERO_P` | Captures phi offset only |
| `ZERO_W` | `ACK:ZERO_W` | Captures wire offset only |
| `STATUS` | `STATUS,...` and `BATT,...` when enabled | Returns the latest computed state; it does not force a new sensor update |
| `CONSTANTS` | `CONSTANTS,...` | Returns runtime PPR and derived scale values, including NVS overrides |
| `RAW_COUNTS` | `RAW,...` | Returns zero-relative theta, phi, and wire counts |
| `CAL_W <actual_mm>` | `CAL:WIRE,<factor>,<new_mm_per_pulse>,<new_ppr_wire>` | Computes a trial from the magnitude of current zero-relative wire counts; does not apply the result |
| `CAL_T <turns>` | `CAL:THETA,<signed_counts>,<ppr>` | Computes theta counts/rev from current zero-relative count and positive integer turns |
| `CAL_P <turns>` | `CAL:PHI,<signed_counts>,<ppr>` | Computes phi counts/rev from current zero-relative count and positive integer turns |
| `SET_PPR_ROTARY <value>` | `ACK:PPR_ROTARY,<value>` | Changes shared theta/phi PPR in RAM only; accepted range is 100 to 500000 |
| `SET_PPR_WIRE <value>` | `ACK:PPR_WIRE,<value>` | Changes wire PPR in RAM only; accepted range is 100 to 500000 |
| `SAVE_PPR` | `ACK:SAVE_PPR` | Saves and reads back runtime PPR values in NVS namespace `evka_cal` |
| `SAVE_POINT` | `POINT,...` | Emits the latest sensor-frame point and increments an in-RAM index; firmware does not retain a coordinate list |
| `DEL_POINT` | `DEL_POINT,<index>` | Decrements the in-RAM point index when nonzero |
| `GET_IP` | `STA_IP:<ipv4>` or `STA_IP:NOT_CONNECTED` | Reports STA address; AP address is not returned |
| `WIFI_SET:<ssid>,<pass>` | `ACK:WIFI_SAVED`, then reboot | Saves and reads back STA credentials in NVS; `WIFI_SET:,` clears them |
| `WIFI_AYAR:<ssid>,<pass>` | Same as `WIFI_SET` | Retained legacy alias |
| `SYSINFO` | `SYSINFO,...` | Reports STA RSSI or 0, free heap, uptime, and TCP client count |
| Any other nonempty command | `ERR:UNKNOWN_CMD` | Unknown command |

`CAL_T` and `CAL_P` currently use Arduino `String::toInt()` rather than the strict finite-float
parser used by `CAL_W` and `SET_PPR_*`. Clients should send a plain positive decimal integer; text
with a numeric prefix may be accepted or truncated by `toInt()`.

### Command Validation Errors

| Command/path | Error reply |
|---|---|
| `CAL_W` nonpositive/missing value | `ERR:CAL_W bad value` |
| `CAL_W` at zero wire count | `ERR:CAL_W zero counts` |
| `CAL_W` factor outside 0.1 to 10.0 | `ERR:CAL_W factor out of range` |
| `CAL_W` candidate PPR outside 100 to 500000 | `ERR:CAL_W PPR out of range` |
| `CAL_T` nonpositive/missing turns | `ERR:CAL_T bad turns` |
| `CAL_T` fewer than 100 absolute counts | `ERR:CAL_T too few counts` |
| `CAL_P` nonpositive/missing turns | `ERR:CAL_P bad turns` |
| `CAL_P` fewer than 100 absolute counts | `ERR:CAL_P too few counts` |
| `SET_PPR_ROTARY` missing/non-finite/outside 100 to 500000 | `ERR:SET_PPR_ROTARY bad value` |
| `SET_PPR_WIRE` missing/non-finite/outside 100 to 500000 | `ERR:SET_PPR_WIRE bad value` |
| PPR NVS open/read-back verification failure | `ERR:SAVE_PPR_FAILED` |
| `DEL_POINT` when index is zero | `ERR:NO_POINTS` |
| `GET_IP` or `SYSINFO` in a build without WiFi | `ERR:WIFI_DISABLED` |
| WiFi write feature disabled | `ERR:WIFI_CFG_DISABLED` |
| WiFi payload has no comma | `ERR:WIFI_INVALID` |
| SSID empty outside the explicit clear request, or over 32 chars | `ERR:SSID_INVALID` |
| Password nonempty and shorter than 8 chars | `ERR:PASS_TOO_SHORT` |
| Password longer than WPA2's 63-character limit | `ERR:PASS_TOO_LONG` |
| WiFi NVS open/read-back verification failure | `ERR:WIFI_SAVE_FAILED` |

### Transport-Level Errors and Limits

| Condition | Behavior |
|---|---|
| Fourth TCP client | Sends `ERR:MAX_CLIENTS`, then closes the new connection |
| TCP line over configured receive limit | Sends `ERR:CMD_TOO_LONG`; discards until line ending |
| Serial command over 128 chars | Prints `ERR:CMD_TOO_LONG`; discards until line ending |
| TCP command queue full | Sends `ERR:CMD_QUEUE_FULL` to the submitting client |
| WebSocket non-text, fragmented, or incomplete frame | Sends `ERR:WS_FRAME_INVALID` to the submitting client |
| WebSocket command over 128 bytes | Sends `ERR:CMD_TOO_LONG` to the submitting client |
| WebSocket command queue full | Sends `ERR:CMD_QUEUE_FULL` to the submitting client and logs the drop to Serial |

## Reply Fan-Out

- Serial commands print exactly one primary success/error reply to Serial.
- Commands that pass through `executeCommand()` also log their primary reply once to Serial before
  network fan-out. Direct TCP `GET_IP` and transport-level ingress errors bypass that wrapper.
- TCP command replies are broadcast to all connected TCP clients, except directly handled TCP
  `GET_IP`, which replies only to its requester.
- WebSocket command replies are broadcast to all connected WebSocket clients.
- Network-originated `POINT,...` and `DEL_POINT,...` replies are mirrored between TCP and WebSocket
  so UIs stay in sync. A Serial-originated command is not mirrored to network clients.
- A network `STATUS` causes `BATT,...` to be broadcast to both wireless transports when battery
  monitoring is enabled.
- Successful `WIFI_SET`/`WIFI_AYAR` returns one `ACK:WIFI_SAVED` on its ingress transport, then a
  deferred restart runs after roughly 500 ms so the ACK can flush. It is not cross-broadcast between
  TCP and WebSocket.

## Security Boundary

The AP password and default STA credentials are compiled into the firmware, and TCP/WebSocket
commands have no application-level authentication or authorization. `WIFI_SET`, zeroing, and PPR
commands can change persistent or operational state. Use this protocol only on an isolated,
trusted lab network. Do not forward ports 80/8080, bridge the AP to an untrusted LAN, or treat the
fixed credentials as a production security control.

## Compatibility Rule

Do not change TCP `X...`/`SENSOR...` framing, port 8080, AP address, or retained command aliases
without reviewing existing equipment. Deletion of the vendor C# application is not permission to
remove the protocol.
