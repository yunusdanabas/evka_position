# Final Calibration Record (Template)

## Device Information

- Date:
- Operator:
- Board ID / Serial:
- Theta encoder serial (if available):
- Phi encoder serial (if available):
- Draw-wire encoder serial (if available):

## Approved Constants

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

## Sign-off Checklist

- [ ] Draw-wire calibration completed and within threshold
- [ ] Theta calibration completed and within threshold
- [ ] Phi calibration completed and within threshold
- [ ] Full-system validation run completed
- [ ] Constants reviewed and approved
- [ ] Firmware commit/hash recorded
- [ ] Artifacts archived in `docs/calibration/`
