# Final Integration Validation Checklist

This checklist closes the software side of Phases 5-7 and defines the final
bench steps for hardware validation.

## 1) Firmware Build Validation

Run from repo root:

```bash
pio run -e wemos_d1_r32 -e test_drawwire -e test_rotary -e test_single_rotary
```

Pass criteria:
- All four environments compile with no errors.
- Main firmware image links for `wemos_d1_r32`.

## 2) Python Tool Validation

```bash
python -m compileall tools/position_checker
python -m unittest discover -s tools/position_checker/tests -v
```

Pass criteria:
- Compile step succeeds for all modules.
- Unit tests pass (`parser`, `data_store`, `serial_reader` reconnect path).

## 3) Live Serial Prototype Validation (5V Adapter)

Battery path is optional for this stage (`ENABLE_BATTERY_MONITOR=0` default).

1. Flash main firmware:
```bash
pio run -e wemos_d1_r32 --target upload
```
2. Start visualizer with reconnect enabled:
```bash
python -m tools.position_checker.main --port /dev/ttyUSB0 --baud 115200 --csv-log /tmp/evka_live.csv
```
3. Start with board disconnected, then connect USB/adapter power and verify:
- GUI transitions to connected state automatically.
- `DATA,` frames appear in plot and text panel.
4. Click `Zero` button and verify firmware emits `ACK:ZERO`.
5. Click `Ping` button and verify firmware emits `ACK:PONG`.
6. Send `STATUS` from a serial terminal and verify:
- `STATUS,...` line is printed.
- `BATT,...` line appears only if battery monitor is enabled.

## 4) Replay Validation (No Hardware)

```bash
python -m tools.position_checker.main --replay-file /tmp/evka_live.csv --fps 20
```

Pass criteria:
- Playback runs without serial hardware.
- Trajectory and latest sample values update during replay.

## 5) Final Bench Sign-Off (Pending Hardware Execution)

Required before marking Phase 5 and Phase 7 complete:
- 3-encoder full-range movement validation on final wiring.
- Accuracy checks at known reference positions.
- Complete calibration pack and archive artifacts under `docs/calibration/`:
  - per-axis logs (`templates/*_log_template.csv` derived files),
  - draw-wire calibration logs,
  - finalized calibration record from `templates/final_calibration_record_template.md`.
- Final calibration notes linked from project docs.
