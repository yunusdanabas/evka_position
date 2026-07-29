# Calibration Pack — Encoder Hardware

This folder contains repeatable calibration artifacts for the three encoder
subsystems used by `evka_position`.

## Current Stop Condition

Theta count loss is unresolved. A recorded repeatability session reached about 1.1 degrees of
theta return error, roughly 35 mm at 2 m. Do not change PPR or fit/copy a world transform to hide
lost counts, slip, or backlash. Resolve and repeat the theta test first.

There is no accepted endpoint/world transform and no shared/default calibration JSON is checked in.
`tools/evka_gui` remains sensor-frame-only. After both report gates pass, a session JSON may be
supplied explicitly to the legacy visualizer only; this opt-in use is not project acceptance.

## Calibration Sequence (run in this order)

1. Draw-wire (`r`) calibration
2. Theta rotary calibration
3. Phi rotary calibration
4. Full-system validation check (main firmware + visualizer)
5. Candidate endpoint world transform + report - [report_workflow.md](report_workflow.md), only
   after repeatability and scale pass (`python -m tools.calibration.report`)

## Firmware Paths

- v4 prototype: keep main `esp32s3_v4` firmware installed and use its commands.
- Classic draw-wire bench: `pio run -e test_drawwire --target upload`.
- Classic rotary bench: `pio run -e test_rotary --target upload`.
- The `test_*` environments use classic Wemos pins and must not be flashed to v4.

## Required Serial Commands

- `ZERO` — zero offsets/counts for current test context
- `ZERO_W` - capture the current wire count as zero
- `CAL_W <mm>` - compute a draw-wire calibration trial from the known distance
- `CAL_T <n>` — rotary theta calibration after `n` turns
- `CAL_P <n>` — rotary phi calibration after `n` turns
- `STATUS` — print current system status from main firmware

## Current Pin Map (source of truth: `SphericalSensor.h`)

Classic ESP32 (`wemos_d1_r32`):

- Theta A/B: GPIO `14` / `12`
- Phi A/B: GPIO `32` / `35`
- Draw-wire A/B: GPIO `16` / `17`

v4 PCB (`esp32s3_v4`):

- Draw-wire on J1: A/B = GPIO `7` / `8`
- Phi on J2: A/B = GPIO `4` / `5` through J2 pins `2` / `4`
- Theta on J3: A/B = GPIO `9` / `10`

v4 connector order:

| Connector | Order |
|---|---|
| J1 draw-wire | `1=A, 2=GND, 3=B, 4=+5V` |
| J2 phi | `1=+5V, 2=A, 3=GND, 4=B` |
| J3 theta | `1=A, 2=GND, 3=B, 4=+5V` |

This order is PCB-derived and was not physically reverified in the final documentation pass.
Theta/Phi colors are Brown `+5V`, Blue `GND`, Black `A`, White `B`; draw-wire colors are Yellow
`A`, Green `B`, Brown `+5V`, White `GND`.

## Current Working Constants (before recalibration)

- `PPR_ROTARY = 20000.0`  *(E40S6-5000 @ X4 quadrature)*
- `PPR_WIRE = 8000.0`  *(theoretical — OPKON DWEM2 P2000; run CAL_W after mounting to calibrate)*
- `DEG_PER_PULSE = 360 / PPR_ROTARY ≈ 0.0180`
- `MM_PER_PULSE = DRUM_CIRCUM_MM / PPR_WIRE ≈ 0.02500`

## Formula Reference

```text
counts_per_rev = total_counts / turns
deg_per_pulse = 360 / counts_per_rev
measured_mm = delta_counts * MM_PER_PULSE
factor = actual_mm / measured_mm
new_MM_PER_PULSE = MM_PER_PULSE * factor
```

## v4 Encoder Angle Signs (before PPR calibration)

Confirm Cartesian directions match the machine before calibrating PPR:

| Define | Current value | Expected motion |
|--------|---------------|-----------------|
| `ENCODER_PHI_SIGN` | -1.0 | Lift → +Z, φ increases |
| `ENCODER_THETA_SIGN` | +1.0 | Desired +Y → +θ |

Classic builds retain the opposite mounting convention (theta `-1`, phi `+1`). Do not copy v4 sign
values into a classic build without a direction check.

If lift drives −Z or forward drives −X, flip the corresponding sign in
`firmware/src/SphericalSensor.h` and reflash. See `docs/hardware_design/system_architecture.md`.

## Logging and Finalization

- Use templates under `docs/calibration/templates/` for every trial.
- Archive the theta repeatability evidence and require it to pass before endpoint fitting.
- After all trials, complete `final_calibration_record_template.md` and archive
  it as a dated file (example: `final_calibration_record_2026-03-03.md`).
- Only then update firmware constants in `SphericalSensor.h`; NVS may still override them.

## Files in this Folder

- `calibration_guide.md` — end-to-end procedure (Stages 1–6)
- `report_workflow.md` — **endpoint report tool** (CSV → Kabsch → `report.md`)
- `sessions/` — working + archived report sessions (`current/` inputs/outputs)
- `draw_wire_calibration.md`
- `theta_rotary_calibration.md`
- `phi_rotary_calibration.md`
- `templates/rotary_calibration_log_template.csv`
- `templates/draw_wire_calibration_log_template.csv`
- `templates/final_calibration_record_template.md`
