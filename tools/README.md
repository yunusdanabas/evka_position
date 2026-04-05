# tools/

Python utilities for the evka_position project.

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
Quick integration notes: `docs/CMD_SOFTWARE_INTEGRATION.md`.

### Run

```bash
# From repo root
python -m tools.position_checker.cmd_main
```

Default endpoint is:
- IP: `192.168.1.50`
- Port: `8080`

### Features

- Connect / disconnect to ESP32 TCP server
- Live `X,Y,Z` display from streamed telemetry line:
  - `X12.34,Y-56.78,Z90.12`
- Per-axis software zero (`X=0`, `Y=0`, `Z=0`)
- All-axis software zero
- Hardware encoder zero (`ZERO`)
- Router IP query (`GET_IP` -> `STA_IP:*`)
- Wi-Fi credential save/forget:
  - Save: `WIFI_AYAR:ssid,password`
  - Forget: `WIFI_AYAR:,`
- Local settings persistence via `ayarlar.txt` in current working directory

### TCP Protocol Quick Reference

GUI -> ESP32 (newline-delimited ASCII):

```text
GET_IP
ZERO
WIFI_AYAR:<ssid>,<password>
WIFI_AYAR:,
```

ESP32 -> GUI (newline-delimited ASCII):

```text
STA_IP:<ipv4>
STA_IP:NOT_CONNECTED
X<value>,Y<value>,Z<value>
ACK:<cmd>
ERR:<reason>
```

WiFi credential validation: SSID must be 1–32 chars (`ERR:SSID_INVALID`); password must be empty or ≥8 chars (`ERR:PASS_TOO_SHORT`). Unrecognized commands return `ERR:UNKNOWN_CMD`.
