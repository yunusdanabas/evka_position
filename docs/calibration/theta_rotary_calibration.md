# Theta Rotary Calibration (classic GPIO 14 / 12; v4 J3 GPIO 9 / 10)

Calibrate theta counts-per-revolution. The standalone `test_rotary` path is classic-Wemos-only; on
v4 use main firmware `ZERO_T` and `CAL_T <n>`.

> Current blocker: theta has shown count/return loss up to about 1.1 degrees. A PPR trial can measure
> scale but cannot clear that defect. Require repeated home and marked-point returns before accepting
> the axis.

## 1. Wiring and Environment Pre-check

- Connect only theta encoder signals:
  - Classic ESP32: A (black) -> divider -> GPIO `14`, B (white) -> divider -> GPIO `12`
  - v4 PCB: A (black) -> J3 pin 1 -> GPIO `9`, B (white) -> J3 pin 3 -> GPIO `10`
  - Brown -> `+5V`, Blue -> `GND`
- Keep phi disconnected for isolated theta calibration.
- Provide external 5V to encoder and common GND to ESP32.
- Confirm voltage divider on every signal line (5V -> 3.3V safe input).

## 2. Choose the Firmware Path

Classic bench only:

```bash
pio run -e test_rotary --target upload
pio device monitor -e test_rotary
```

For v4, keep `esp32s3_v4` installed. Do not flash `test_rotary` onto the S3 carrier.

## 3. Trial Loop (CW and CCW)

For each trial:

1. Send `ZERO_T`
2. Rotate exactly `N` full turns (recommended `N=3` or `N=5`)
3. Send `CAL_T N`
4. Record `total_counts`, `counts/rev`, and `deg/pulse` in
   `templates/rotary_calibration_log_template.csv`

Run at least:
- 3 trials CW
- 3 trials CCW

## 4. Acceptance Thresholds (operational defaults)

- Direction consistency:
  - CW trials should keep expected sign and CCW should invert sign.
- Repeatability:
  - `counts_per_rev` spread across accepted trials <= 1.0%
- CW vs CCW agreement:
  - Mean CW and mean CCW magnitudes differ <= 1.0%

If thresholds fail:
- Check coupler slippage, shaft backlash, and A/B wiring integrity.
- Re-run diagnostic (`DIAG`) and repeat trials.

`DIAG` is a standalone classic-test command, not a main-firmware command. For v4 use
`RAW_COUNTS`, scoped electrical measurements, and recorded return tests.

### Repeatability acceptance gate

- Return to the same marked angle and mechanical home several times without re-zeroing.
- Compare zero-relative theta counts in both directions and at representative speeds.
- Reject the axis if counts drift between visits, even when counts/rev spread is below 1%.
- Do not average the drift into PPR.

## 5. Final Value to Commit

Compute accepted theta constants:

```text
PPR_ROTARY_THETA = mean(|counts_per_rev| of accepted trials)
DEG_PER_PULSE_THETA = 360 / PPR_ROTARY_THETA
```

Write final values into `templates/final_calibration_record_template.md`
before touching firmware constants.
