# tools/position_checker — live 3D visualizer + CMD GUI

> **Deprecated as standalone tools.** Use the unified GUI instead:
> `python -m tools.evka_gui`. Legacy entry points remain as shims
> (`--legacy-visualizer`, `--legacy-cmd-gui`).

This package still provides the **protocol SSOT** (`cmd_main.py`) and shared
libraries (`tcp_client.py`, `cmd_display.py`, `parser.py`) consumed by
`tools/evka_gui`.

Two host-side apps that read the firmware's telemetry:

- **Visualizer** — reads the serial `DATA,` stream and renders a live 3D trajectory.
- **CMD GUI** — a Linux-native equivalent of the Windows CMD app; connects over TCP, shows live
  X/Y/Z + R/θ/φ, min/max tracking, saved points, and WiFi settings.

## Run

```bash
# From the repo root, with the venv active (see ../../CONTRIBUTING.md)
python -m tools.position_checker.main --port /dev/ttyUSB0    # serial visualizer (COM3 on Windows)
python -m tools.position_checker.cmd_main                    # TCP CMD GUI
python -m tools.position_checker.main --replay-file frames.csv --fps 20   # replay, no hardware
```

## Tests

```bash
pytest tools/position_checker/tests -q
```

**Full documentation** — all CLI flags, GUI features, zero semantics, and the complete TCP protocol
reference — lives in the top-level **[../README.md](../README.md)** (sections *position_checker* and
*Linux TCP CMD GUI*). `cmd_main.py` is the single source of truth for the stream/format contract.

## Module map

| Module | Role |
|---|---|
| `main.py` / `__main__.py` | Visualizer entry point (serial/replay) |
| `cmd_main.py` / `cmd_gui.py` / `cmd_display.py` | TCP CMD GUI + the authoritative stream contract |
| `parser.py` | Parse `DATA,` / `X,Y,Z` / `SENSOR,` lines |
| `serial_reader.py` / `tcp_client.py` / `replay_reader.py` | Transports |
| `data_store.py` / `transform.py` / `gui.py` | State, coordinate transform, pyqtgraph view |
