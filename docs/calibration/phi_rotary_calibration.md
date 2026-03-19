# Phi Rotary Calibration (GPIO 14 / 12)

Calibrate phi counts-per-revolution using `test_rotary`.

## 1. Wiring and Environment Pre-check

- Connect only phi encoder signals:
  - A (black) -> divider -> GPIO `14`
  - B (white) -> divider -> GPIO `12`
- Keep theta disconnected for isolated phi calibration.
- Provide external 5V to encoder and common GND to ESP32.
- Confirm voltage divider on every signal line (5V -> 3.3V safe input).

## 2. Flash and Monitor

```bash
pio run -e test_rotary --target upload
pio device monitor -e test_rotary
```

## 3. Trial Loop (CW and CCW)

For each trial:

1. Send `ZERO_P`
2. Rotate exactly `N` full turns (recommended `N=3` or `N=5`)
3. Send `CAL_P N`
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

## 5. Isolated-Test Noise Note

When theta encoder is disconnected during isolated phi tests, ignore any
spurious theta field noise in serial output and evaluate only phi values.

## 6. Final Value to Commit

Compute accepted phi constants:

```text
PPR_ROTARY_PHI = mean(|counts_per_rev| of accepted trials)
DEG_PER_PULSE_PHI = 360 / PPR_ROTARY_PHI
```

Write final values into `templates/final_calibration_record_template.md`
before touching firmware constants.
