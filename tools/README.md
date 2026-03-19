# tools/

Python utilities for the evka_position project.

## position_checker

Real-time 3D position visualiser that reads the `DATA,` CSV stream from the
firmware and renders a live OpenGL 3D trajectory (pyqtgraph GLViewWidget, 30-60+ FPS).

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

- **3-D OpenGL view** — trajectory line + scatter trail; current position in red (pyqtgraph, interactive rotation/zoom while streaming).
- **Text panel** — X, Y, Z (mm), R, θ, φ, validity flag, frame counter,
  timestamp, total point count, and live connection/command status.
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

The Python parser ignores all lines that do not begin with `DATA,`.

### Test command

Run built-in tests:

```bash
python -m unittest discover -s tools/position_checker/tests -v
```
