# Final Calibration Record (Template)

## Device Information

- Date:
- Operator:
- Board ID / Serial:
- Theta encoder serial (if available):
- Phi encoder serial (if available):
- Draw-wire encoder serial (if available):

## Candidate / Approved Constants

| Constant | Value | Unit | Notes |
|---|---:|---|---|
| `PPR_ROTARY_THETA` |  | counts/rev |  |
| `PPR_ROTARY_PHI` |  | counts/rev |  |
| `PPR_WIRE` |  | pulses/rev |  |
| `DEG_PER_PULSE_THETA` |  | deg/pulse |  |
| `DEG_PER_PULSE_PHI` |  | deg/pulse |  |
| `MM_PER_PULSE` |  | mm/pulse |  |
| Calibration date |  | date |  |
| Calibration operator |  | text |  |

## Applied Firmware Reference

- Applied to firmware commit/hash:
- File(s) updated (expected: `firmware/src/SphericalSensor.h`):

## Input Trial Artifacts

- Theta log file:
- Phi log file:
- Draw-wire log file:

## Endpoint Report (Stages 5–6)

- Session folder (e.g. `docs/calibration/sessions/YYYY-MM-DD_operator/`):
- `report.md` attached / archived:
- Calibration RMSE (mm):
- Validation max error (mm) / worst label:
- Calibration status (PASS/FAIL):
- Validation status (PASS/FAIL):
- Optional legacy visualizer JSON path (if used):
- Exact legacy `--calibration` command (if used):
- Explicit acceptance decision and approver:
- Consuming application/frame (note: `evka_gui` is sensor-frame-only):

## Sign-off Checklist

- [ ] Draw-wire calibration completed and within threshold
- [ ] Theta calibration completed and within threshold
- [ ] Phi calibration completed and within threshold
- [ ] Theta repeated-point and home-return count stability demonstrated
- [ ] Endpoint report generated (`python -m tools.calibration.report`)
- [ ] Calibration RMSE ≤ 10 mm and validation max error ≤ 15 mm
- [ ] Optional legacy transform used only from a passing session JSON with an explicit path
- [ ] World transform explicitly accepted; report PASS or legacy visualization alone is not acceptance
- [ ] Full-system validation run completed (live + flat-plane)
- [ ] Constants reviewed and approved
- [ ] Firmware commit/hash recorded
- [ ] Artifacts archived in `docs/calibration/` (including session `report.md`)
