# tools/

Python utilities for the evka_position project.

## ipt

Quick IPT hidden-point measurement tool. Recovers a target point that the pen
cannot touch directly (around a corner, behind an obstacle, inside a recess)
using the Prodim Proliner's "Quick IPT" (Inverted Pen Technology) method.

```bash
# WiFi (AP fallback)
python -m tools.ipt --tcp 192.168.1.50:8080

# Serial
python -m tools.ipt --serial /dev/ttyUSB0 --baud 115200

# No flag → opens disconnected
python -m tools.ipt
```

Hold the pen **tip** on the hidden target, sweep the **handle** in a wide spiral,
and fit a sphere to recover the target. See `tools/ipt/README.md` for full
workflow, quality flags, and troubleshooting.

## position_checker

Real-time 3D position visualiser that reads the `DATA,` CSV stream from the
firmware and renders a live 3D trajectory view.

Single source of truth for visualizer protocol/format conventions:
- `tools/position_checker/cmd_main.py`

### Install dependencies

```bash
cd tools/position_checker
pip install -r requirements.txt
```

### Run

```bash
# From the repo root
python -m tools.position_checker.main --port /dev/ttyUSB0

# Or from inside tools/
python -m position_checker.main --port /dev/ttyUSB0 --baud 115200 --maxpoints 1000

# Replay mode (no hardware needed)
python -m tools.position_checker.main --replay-file /path/to/frames.csv --fps 20
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--port` | required in live mode | Serial port (`/dev/ttyUSB0`, `COM3`, …) |
| `--baud` | 115200 | Baud rate |
| `--maxpoints` | 500 | Rolling history length |
| `--fps` | 10 | GUI refresh rate (and replay speed) |
| `--reconnect` / `--no-reconnect` | enabled | Auto-reconnect policy in live mode |
| `--reconnect-interval` | 1.0 | Initial reconnect delay (seconds) |
| `--csv-log` | disabled | Optional parsed-frame CSV output file |
| `--replay-file` | disabled | Use recorded CSV / `DATA,` dump as input |

### GUI features

- **3-D view** — trajectory line + head marker; current position in red.
- **Text panel** — X, Y, Z (mm), R, θ, φ, validity flag, frame counter,
  timestamp, total point count, and live connection/command status.
- **Firmware-authoritative angles** — θ/φ values displayed from firmware stream
  (phi sign is not recomputed in visualizer transforms).
- **Zero button** — sends `ZERO\n` to the firmware; firmware responds
  with `ACK:ZERO` and resets the zero point.
- **Ping button** — sends `PING\n`; firmware responds with `ACK:PONG`.
- **Reconnect loop** — keeps trying to restore serial after disconnects.

### Expected firmware output

The firmware emits two lines per update cycle (plus optional status lines):

```
Cartesian: X=123.4 Y=-56.7 Z=890.1 mm | Spherical: R=900.0 mm, Theta=25.00 deg, Phi=10.00 deg
DATA,123.40,-56.70,890.10,900.00,25.000,10.000,1,42,12345
```

The `DATA` field order is fixed as:
`x_mm,y_mm,z_mm,r_mm,theta_deg,phi_deg,is_valid,frame_count,ts_ms`.

The Python parser ignores all lines that do not begin with `DATA,`.

### Test command

Run built-in tests:

```bash
python -m unittest discover -s tools/position_checker/tests -v
```

## Linux TCP CMD GUI

Linux-native control panel equivalent of `firmware/src/CMD Soft/gui.cs`.
It connects to ESP32 over Wi-Fi TCP and displays live `X,Y,Z` values.
Quick integration notes: `docs/integration/CMD_SOFTWARE_INTEGRATION.md`.

For a Turkish WiFi connection guide: [`README_TR.md`](../README_TR.md)

### Run

```bash
# From repo root
python -m tools.position_checker.cmd_main
```

Default endpoint is:
- IP: `192.168.1.84` (example STA target)
- Port: `8080`

AP fallback remains `192.168.1.50` when connected directly to `CMDCNC_EVKA`.

### Features

- Connect / disconnect to ESP32 TCP server
- Live `X,Y,Z` display from streamed telemetry line:
  - `X12.34,Y-56.78,Z90.12`
- Live `SENSOR,...` panel (R, θ, φ, valid, frame)
- Per-axis **software zero** (`X=0`, `Y=0`, `Z=0`) — display-only offset
- **Software Zero (All)** — zeros all axes in the display frame (no firmware command)
- **Clear Software Zero** — return to world coordinates without sending `ZERO`
- **Hardware Zero (Encoder)** — sends `ZERO` to firmware at mechanical home
- **Reset Min/Max** — clears session min/max stats only (not zero offsets)
- Saved points (`SAVE_POINT` / `DEL_POINT`) with session-local list
- ESP-NOW remote button indicators (`REMOTE_BTN`, `REMOTE_HB`)
- Router IP query (`GET_IP` -> `STA_IP:*`)
- System info polling (`SYSINFO` — RSSI, heap, uptime, TCP clients)
- Wi-Fi credential save/forget:
  - Save: `WIFI_SET:<ssid>,<password>` (empty password = open network)
  - Forget: `WIFI_SET:,`
- Local settings persistence via `settings.txt` in current working directory

**Zero semantics:** Software zero subtracts the current raw XYZ as a client-side
offset so the display shows relative position. R/θ/φ are recomputed from the
zeroed Cartesian values. Hardware zero sends `ZERO` and resets encoders. Software
zero is cleared on disconnect.

### TCP Protocol Quick Reference

GUI -> ESP32 (newline-delimited ASCII):

```text
GET_IP
ZERO
SAVE_POINT
DEL_POINT
SYSINFO
WIFI_SET:<ssid>,<password>
WIFI_SET:,
```

ESP32 -> GUI (newline-delimited ASCII):

```text
STA_IP:<ipv4>
STA_IP:NOT_CONNECTED
X<value>,Y<value>,Z<value>
SENSOR,<r>,<theta>,<phi>,<valid>,<frame>
SYSINFO,<rssi>,<heap>,<uptime_s>,<tcp_clients>
POINT,<idx>,<x>,<y>,<z>,<r>,<theta>,<phi>
DEL_POINT,<idx>
REMOTE_BTN:<0|1>
REMOTE_HB
ACK:<cmd>
ERR:<reason>
```

WiFi credential validation: SSID must be 1–32 chars (`ERR:SSID_INVALID`); password must be empty or ≥8 chars (`ERR:PASS_TOO_SHORT`). Unrecognized commands return `ERR:UNKNOWN_CMD`.
