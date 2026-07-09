# evka_gui — EVKA Unified Control GUI (canonical)

Single-window control panel + 3D view for v4 board bring-up and daily operation.
Supports Serial, WiFi/TCP (AP `192.168.1.50` or STA `192.168.1.84`), and CSV
replay. Calibration opens in a separate window.

```bash
python -m tools.evka_gui                              # open disconnected
python -m tools.evka_gui --serial /dev/ttyUSB0 --baud 115200
python -m tools.evka_gui --tcp 192.168.1.50:8080      # AP direct
python -m tools.evka_gui --tcp 192.168.1.84:8080      # STA
```

Modules: `gui.py` (window + panels), `model.py` (session state, software zero,
min/max), `transport.py` (serial/TCP/replay), `calibration.py` (wire/theta/phi
+ endpoint calibration window). Tests: `tests/test_model.py` (run `pytest -q`).

Feature matrix, migration table from the deprecated shims
(`tools/evka_gui_v2`, `tools/position_checker/{main,cmd_main}`), and design
history: [`tools/README.md`](../README.md#evka_gui--unified-control-gui-canonical)
and `docs/gui_unification/`.
