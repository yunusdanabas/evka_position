# Calibration sessions

Working directory for the endpoint report tool:

```bash
python -m tools.calibration.report
```

Full operator guide: [../report_workflow.md](../report_workflow.md).

There is currently no accepted endpoint/world transform or checked-in shared/default calibration
JSON. Session outputs are candidates.

## Layout

| Path | Role |
|------|------|
| `current/` | Active working session — fill CSVs here, then regenerate the report |
| `YYYY-MM-DD_<operator>/` | Optional archives of completed sessions (copy of `current/` after a PASS) |

## Files in a session folder

**Inputs** (edit these):

| File | Role |
|------|------|
| `calibration_points.csv` | Point pairs used to fit `R` and `t` (≥ 3 rows; recommend 8+) |
| `validation_points.csv` | Hold-out pairs for PASS/FAIL and optional repeatability (≥ 1 row) |

**Outputs** (written by the tool; git-ignored):

| File | Role |
|------|------|
| `report.md` | Human-readable calibration + validation report |
| `calibration.json` | Candidate transform (`world = R @ sensor + t`); optional explicit legacy input only after PASS |
| `calibration_errors.csv` | Per-point calibration residuals |
| `validation_errors.csv` | Per-point validation residuals |

The session `calibration.json` is not auto-copied or auto-loaded. See
[report_workflow.md](../report_workflow.md#6-optional-explicit-legacy-transform).
