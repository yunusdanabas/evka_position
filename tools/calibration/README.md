# tools/calibration — world↔sensor calibration

Computes the rigid-body transform (rotation **R**, translation **t**) that maps the sensor's
coordinate frame into the machine/world frame, so measured points can be reported in world
coordinates:

```
world_point ≈ R @ sensor_point + t
```

It uses the **Kabsch algorithm** (least-squares best-fit rotation + translation) on a set of paired
`sensor ↔ world` points.

Current project status: this tool produces **candidate** transforms. Theta count loss is unresolved,
no shared/default calibration JSON is checked in, and no endpoint/world transform is accepted.
`tools/evka_gui` does not apply transforms to live telemetry.

## Preferred workflow — standalone calibration app

```bash
python -m tools.calibration.gui                     # open disconnected
python -m tools.calibration.gui --serial /dev/ttyUSB0
python -m tools.calibration.gui --tcp 192.168.1.84:8080
python -m tools.calibration.gui --ws 192.168.1.50
```

One full-screen window with everything a calibration session needs and nothing else:
connection (serial / TCP / WebSocket), live position, and tabs for **Wire**, **Theta**,
**Phi**, **Endpoint**, **Points**, **Commands**.

The **Endpoint** tab drives this tool end to end: collect world/sensor pairs, assign each to
the calibration or validation set, **Generate report**, and read PASS/FAIL and per-point
residuals. It calls `generate_report()` in-process and needs no device once the points are in.

This app has **no software zero** by design — every captured coordinate is the raw sensor
frame. A display offset would be absorbed into the fit's translation and silently produce a
transform valid only while that offset is active.

**Full operator guide:** [docs/calibration/report_workflow.md](../../docs/calibration/report_workflow.md)

Also available: `evka_gui` → toolbar **Calibration…**, which has the same Endpoint workflow
inside the full telemetry GUI.

## CLI — report tool

Same engine, same session folder, same verdict:

```bash
# From the repo root
python -m tools.calibration.report
```

1. First run creates templates under `docs/calibration/sessions/current/` if missing.
2. Fill `calibration_points.csv` (fit) and `validation_points.csv` (hold-outs).
3. Run again → writes `report.md`, session `calibration.json`, and error CSVs.

The session `calibration.json` is not auto-copied or auto-loaded. After a PASS, it may be supplied
explicitly only to the legacy visualizer:

```bash
python -m tools.position_checker.main --legacy-visualizer --port /dev/ttyUSB0 \
  --calibration docs/calibration/sessions/current/calibration.json
```

Pass criteria: calibration RMSE ≤ 10 mm, validation max error ≤ 15 mm. Both must pass —
`GeneratedReport.passed` ANDs them, and it is what gates the Deploy button. The app,
`evka_gui`, and this CLI all call the same engine, so their verdicts always agree.

A report PASS and optional legacy visualization are not project acceptance. Record the mechanical
repeatability evidence, approval decision, and consuming application separately. The currently named
**Deploy calibration.json** action is legacy source behavior; the CLI prints only an explicit
legacy-visualizer invocation. Neither is the active canonical workflow.

CSV inputs need only the six coordinate columns; `label` and `notes` are optional. Exports
from the web dashboard **CALIBRATE → ENDPOINT** tab load as-is (the GUI's **Import CSV**
reads them through this same parser). `evka_gui` writes the two session CSVs directly, with
the full 8-column header.

## Legacy / quick fit — calibrate.py

Embedded point arrays (or a one-off CLI write):

```bash
python -m tools.calibration.calibrate
python -m tools.calibration.calibrate --out /tmp/evka_candidate_calibration.json
```

Output: the fit **R** and **t**, per-point residuals, and RMS error. Prefer the report
workflow for field sessions and an auditable record. Quick-fit output is not a passing session JSON.

## Providing calibration data

1. Move the tip to each known world point and record the sensor XYZ (`tools.calibration.gui`
   Endpoint tab → **Use Current Sensor XYZ**, `evka_gui` Calibration → Endpoint, web
   dashboard **CALIBRATE → Endpoint**, or serial `STATUS`).
2. In the app: pick **Add to: Calibration** or **Validation** per point — it writes the two
   session CSVs for you. A row's **Set** dropdown moves it between them afterwards.
3. By hand: put fit points in `calibration_points.csv` and hold-outs in
   `validation_points.csv`.
4. For the legacy CLI: replace `SENSOR_PTS` / `WORLD_PTS` in `calibrate.py` and re-run.

More points, well spread in **all three axes**, give a better fit — a single-axis set leaves the
rotation poorly constrained. Collinear or coincident calibration sets are rejected by the
report tool.

## Files

| File | Role |
|---|---|
| `gui.py` | **Standalone calibration app** (`python -m tools.calibration.gui`) — connection, live position, Wire/Theta/Phi/Endpoint/Points/Commands |
| `report.py` | Default calibration + validation CSV workflow; writes `report.md` |
| `calibrate.py` | Kabsch solver + embedded measurement data + legacy CLI |
| `tests/test_report.py` | Report workflow unit tests |
| `tests/test_gui.py` | Standalone app unit tests (offscreen Qt) |

```bash
pytest tools/calibration/tests/test_report.py -q
QT_QPA_PLATFORM=offscreen pytest tools/calibration/tests -q   # includes the app tests
```
