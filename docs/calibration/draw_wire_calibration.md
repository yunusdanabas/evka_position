# Draw-Wire Calibration (classic GPIO 16 / 17; v4 J1 GPIO 7 / 8)

Calibrate linear scale (`MM_PER_PULSE`) using `test_drawwire` and known travel
references.

## 1. Wiring and Environment Pre-check

- Connect draw-wire channels:
  - Classic ESP32: A -> divider -> GPIO `16`, B -> divider -> GPIO `17`
  - v4 PCB: A (Yellow) -> J1 pin 1 -> GPIO `7`, B (Green) -> J1 pin 3 -> GPIO `8`
  - Power: Brown -> `+5V`, White -> `GND`
- External 5V supply and common GND with ESP32.
- Prepare a physical distance reference (steel ruler/tape) with at least
  500 mm usable travel.

## 2. Flash and Monitor

```bash
pio run -e test_drawwire --target upload
pio device monitor -e test_drawwire
```

## 3. Known-Distance Trial Method

Recommended distances: `100 mm`, `200 mm`, `500 mm`.

For each trial:

1. Send `ZERO`
2. Send `CAL` at start position
3. Pull to known `actual_mm`
4. Send `DONE`
5. Record `delta_counts` and `measured_mm` from serial output in
   `templates/draw_wire_calibration_log_template.csv`

Use both directions:
- Outward pull trial
- Return (inward) trial

## 4. Interpretation and Formula Use

Given current firmware value `MM_PER_PULSE`:

```text
measured_mm = delta_counts * MM_PER_PULSE
factor = actual_mm / measured_mm
new_MM_PER_PULSE = MM_PER_PULSE * factor
```

Use accepted trials to compute final `MM_PER_PULSE` as mean of
`new_MM_PER_PULSE` values.

## 5. Hysteresis / Backlash Check

Compare outward vs return trial for same nominal distance:

```text
hysteresis_mm = |measured_out_mm - measured_return_mm|
```

Operational default acceptance:
- `hysteresis_mm <= max(1.0 mm, 0.5% of actual_mm)`

If exceeded:
- Check cable alignment, spring tension, mount rigidity, and pulley friction.

## 6. Final Value to Commit

Record final accepted `MM_PER_PULSE` in
`templates/final_calibration_record_template.md` before updating firmware.
