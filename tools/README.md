# tools/

Python utilities for the evka_position project.

## position_checker

Real-time 3D position visualiser that reads the `DATA,` CSV stream from the
firmware and displays a live 3D scatter plot.

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
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--port` | *required* | Serial port (`/dev/ttyUSB0`, `COM3`, …) |
| `--baud` | 115200 | Baud rate |
| `--maxpoints` | 500 | Rolling history length |

### GUI features

- **3-D scatter plot** — trajectory coloured by age; latest point in red.
- **Text panel** — X, Y, Z (mm), R, θ, φ, validity flag, frame counter,
  timestamp, and total point count.
- **Zero button** — sends `ZERO\n` to the firmware; firmware responds
  with `ACK:ZERO` and resets the zero point.

### Expected firmware output

The firmware emits two lines per update cycle:

```
Cartesian: X=123.4 Y=-56.7 Z=890.1 mm | Spherical: R=900.0 mm, Theta=25.00 deg, Phi=10.00 deg
DATA,123.40,-56.70,890.10,900.00,25.000,10.000,1,42,12345
```

The Python parser ignores all lines that do not begin with `DATA,`.
