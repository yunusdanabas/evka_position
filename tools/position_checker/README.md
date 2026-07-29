# tools/position_checker — live 3D visualizer + CMD GUI

> **Legacy standalone tools.** Use the canonical GUI instead:
> `python -m tools.evka_gui`. Legacy entry points remain as shims
> (`--legacy-visualizer`, `--legacy-cmd-gui`).

This package still provides shared
libraries (`tcp_client.py`, `cmd_display.py`, `parser.py`) consumed by
`tools/evka_gui` and `tools/ipt`.

The canonical wire contract is [../../docs/PROTOCOL.md](../../docs/PROTOCOL.md), not `cmd_main.py`.

Two host-side apps that read the firmware's telemetry:

- **Visualizer** — reads the serial `DATA,` stream and renders a live 3D trajectory.
- **Legacy TCP GUI** - connects over TCP and shows live X/Y/Z + R/theta/phi, min/max tracking,
  saved points, and WiFi settings.

## Run

```bash
# From the repo root, with the venv active (see ../../CONTRIBUTING.md)
python -m tools.position_checker.main --legacy-visualizer --port /dev/ttyUSB0
python -m tools.position_checker.cmd_main                    # TCP CMD GUI
python -m tools.position_checker.main --legacy-visualizer --replay-file frames.csv --fps 20
```

The legacy visualizer defaults to the sensor frame. After both report gates pass, a session JSON can
be applied only with an explicit path:

```bash
python -m tools.position_checker.main --legacy-visualizer --port /dev/ttyUSB0 \
  --calibration docs/calibration/sessions/current/calibration.json
```

It does not search for or auto-load a shared/default JSON. A JSON with a non-`PASS` verdict is
rejected.

## Tests

```bash
pytest tools/position_checker/tests -q
```

Protocol details live in [../../docs/PROTOCOL.md](../../docs/PROTOCOL.md). New operator workflows
use `tools/evka_gui`.

## Module map

| Module | Role |
|---|---|
| `main.py` / `__main__.py` | Visualizer entry point (serial/replay) |
| `cmd_main.py` / `cmd_gui.py` / `cmd_display.py` | Legacy TCP GUI and display helpers |
| `parser.py` | Parse `DATA,` / `X,Y,Z` / `SENSOR,` lines |
| `serial_reader.py` / `tcp_client.py` / `replay_reader.py` | Transports |
| `data_store.py` / `transform.py` / `gui.py` | State, coordinate transform, pyqtgraph view |

Explicit legacy calibration use does not make the transform accepted and does not change canonical
`evka_gui` sensor-frame behavior.
