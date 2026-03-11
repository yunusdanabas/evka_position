# Calibration Pack — Encoder Hardware

This folder contains repeatable calibration artifacts for the three encoder
subsystems used by `evka_position`.

## Calibration Sequence (run in this order)

1. Draw-wire (`r`) calibration
2. Theta rotary calibration
3. Phi rotary calibration
4. Full-system validation check (main firmware + visualizer)

## Required Firmware Test Binaries

- Draw-wire: `pio run -e test_drawwire --target upload`
- Rotary (theta/phi): `pio run -e test_rotary --target upload`
- Full-system: `pio run -e wemos_d1_r32 --target upload`

## Required Serial Commands

- `ZERO` — zero offsets/counts for current test context
- `CAL` — start draw-wire calibration window
- `DONE` — end draw-wire calibration window and print result
- `CAL_T <n>` — rotary theta calibration after `n` turns
- `CAL_P <n>` — rotary phi calibration after `n` turns
- `STATUS` — print current system status from main firmware

## Current Pin Map (source of truth: `SphericalSensor.h`)

- Theta A/B: GPIO `14` / `12`
- Phi A/B: GPIO `27` / `26`
- Draw-wire A/B/Z: GPIO `32` / `33` / `18`

## Current Working Constants (before recalibration)

- `PPR_ROTARY = 1480.0`
- `PPR_WIRE = 2000.0`
- `DEG_PER_PULSE = 360 / PPR_ROTARY`
- `MM_PER_PULSE = DRUM_CIRCUM_MM / PPR_WIRE = 0.1`

## Formula Reference

```text
counts_per_rev = total_counts / turns
deg_per_pulse = 360 / counts_per_rev
measured_mm = delta_counts * MM_PER_PULSE
factor = actual_mm / measured_mm
new_MM_PER_PULSE = MM_PER_PULSE * factor
```

## Logging and Finalization

- Use templates under `docs/calibration/templates/` for every trial.
- After all trials, complete `final_calibration_record_template.md` and archive
  it as a dated file (example: `final_calibration_record_2026-03-03.md`).
- Only then update firmware constants in `SphericalSensor.h`.

## Files in this Folder

- `draw_wire_calibration.md`
- `theta_rotary_calibration.md`
- `phi_rotary_calibration.md`
- `templates/rotary_calibration_log_template.csv`
- `templates/draw_wire_calibration_log_template.csv`
- `templates/final_calibration_record_template.md`
