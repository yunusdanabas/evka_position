# Draw-Wire Calibration (classic GPIO 16 / 17; v4 J1 GPIO 7 / 8)

Calibrate linear scale (`MM_PER_PULSE`) using known travel references. The standalone
`test_drawwire` environment is classic-Wemos-only; on v4 use the main firmware commands.

## 1. Wiring and Environment Pre-check

- Connect draw-wire channels:
  - Classic ESP32: A -> divider -> GPIO `16`, B -> divider -> GPIO `17`
  - v4 PCB: A (Yellow) -> J1 pin 1 -> GPIO `7`, B (Green) -> J1 pin 3 -> GPIO `8`
  - Power: Brown -> `+5V`, White -> `GND`
- External 5V supply and common GND with ESP32.
- Prepare a physical distance reference (steel ruler/tape) with at least
  500 mm usable travel.

## 2. Choose the Firmware Path

Classic bench only:

```bash
pio run -e test_drawwire --target upload
pio device monitor -e test_drawwire
```

For v4, do not flash a `test_*` environment. Keep `esp32s3_v4` installed and send the same
`ZERO_W` / `CAL_W <mm>` commands over Serial, TCP, or WebSocket.

## 3. Known-Distance Trial Method

Recommended distances: `100 mm`, `200 mm`, `500 mm`.

For each trial:

1. Send `ZERO_W`
2. Pull to known `actual_mm`
3. Send `CAL_W <actual_mm>`
4. Record counts and the returned candidate `mm_per_pulse` / `ppr_wire` in
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

## 6. Final Value to Record

Record final accepted `MM_PER_PULSE` in
`templates/final_calibration_record_template.md` before updating firmware.

Draw-wire scale acceptance does not clear the current theta repeatability blocker.
