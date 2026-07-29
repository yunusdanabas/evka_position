# Calibration Report Workflow

Operator guide for the systematic endpoint (Kabsch) calibration and validation report.

> **Current status:** this workflow produces candidate transforms. Theta count loss is unresolved,
> there is no accepted endpoint/world transform, and no shared/default calibration JSON is checked
> in. `tools/evka_gui` remains sensor-frame-only.

```bash
# From the repo root
python -m tools.calibration.report
```

This is the preferred path for Stages 5-6 of [calibration_guide.md](calibration_guide.md).
It does **not** change firmware — you collect real-world reference points, put them in CSV
files, then the tool fits a candidate sensor-to-world transform and writes a Markdown report.

Full tool notes: [tools/calibration/README.md](../../tools/calibration/README.md).
Session folder layout: [sessions/README.md](sessions/README.md).

---

## 1. Purpose and prerequisites

Endpoint calibration computes a rigid-body transform that maps **sensor XYZ** into your
**machine/world** frame:

```text
world = R @ sensor + t
```

| Requirement | Detail |
|-------------|--------|
| Mechanical repeatability | Theta/phi/radius must return repeatably; Kabsch cannot correct count loss, slip, or backlash. |
| Encoder PPR done | Complete Stages 1–4 first (wire, theta, phi, apply constants). This stage corrects frame tilt/offset, not encoder scale. |
| Calibration points | At least **3** (tool minimum); recommend **8+**, well spread in X/Y/Z |
| Validation points | At least **1** (tool minimum); recommend **3–5** hold-outs not used in the fit |
| Geometry | Calibration set must span **≥ 2 directions** (not collinear or coincident) |

---

## 2. Quick start

Default session directory: `docs/calibration/sessions/current/`.

### Standalone app (normal path)

```bash
python -m tools.calibration.gui --tcp 192.168.1.84:8080     # or --serial /dev/ttyUSB0, --ws HOST
```

One full-screen window: connection, live position, and tabs for Wire / Theta / Phi /
**Endpoint** / Points / Commands. On the Endpoint tab: collect pairs (**Use Current Sensor
XYZ** grabs the live reading), set **Add to: Calibration / Validation** per point,
**Generate report**, and read the verdict and per-point residuals. Keep the generated JSON in its
session directory; optional legacy visualization is described in
[Section 6](#6-optional-explicit-legacy-transform).

It has no software zero — captured coordinates are always the raw sensor frame.

### Inside evka_gui

`python -m tools.evka_gui` → toolbar **Calibration…** → **Endpoint** tab has the same
endpoint workflow, if you are already in the telemetry GUI.

Both read and write the two session CSVs directly and call the same `generate_report()` as
the CLI, so all three always agree. No terminal step, and no device connection is needed
once the points are in.

### CLI (two-run workflow)

**First run** — creates empty CSV templates if they are missing:

```bash
python -m tools.calibration.report
```

You should see something like:

```text
Input templates are ready in: .../docs/calibration/sessions/current
Fill `calibration_points.csv` and `validation_points.csv`, then run:
python -m tools.calibration.report
```

**Fill the CSVs** (see [CSV format](#4-csv-format) below), then **run again**:

```bash
python -m tools.calibration.report
```

On success the tool writes `report.md`, `calibration.json`, and the per-point error CSVs
into the same session folder. See
[optional explicit legacy transform](#6-optional-explicit-legacy-transform).

---

## 3. Collecting measurement pairs

For each point: move the probe to a known world position `(world_x, world_y, world_z)` and
record the sensor Cartesian output `(sensor_x, sensor_y, sensor_z)`.

**Recommended layout (calibration set):**
- 3–4 points along +X (e.g. 100, 200, 400, 600 mm)
- 3–4 points along +Y
- 1–2 points along +Z or otherwise off-plane
- Include the world origin when practical

### Collection paths

| Source | How | CSV compatibility |
|--------|-----|-------------------|
| **Calibration app** | `python -m tools.calibration.gui` → Endpoint tab → enter world XYZ, **Use Current Sensor XYZ**, pick the set, **Add pair** | Writes both session CSVs directly — no split step |
| **evka_gui** | Toolbar **Calibration…** → Endpoint tab → same as above | Writes both session CSVs directly — no split step |
| **Web dashboard** | Connect to AP `CMDCNC_EVKA` → `http://192.168.1.50` → **CALIBRATE → ENDPOINT** → SET ORIGIN → RECORD POINT → EXPORT CSV | Header has `label` + 6 coords (no `notes`) — loads as-is, or use the GUI's **Import CSV** |
| **Serial** | Move probe, send `STATUS`, copy last three fields as sensor XYZ into the session CSVs | Manual entry |

`STATUS` reply format:

```text
STATUS,<is_valid>,<frame_count>,<ts_ms>,<r>,<theta>,<phi>,<x>,<y>,<z>
```

Use the last three fields as `sensor_x`, `sensor_y`, `sensor_z`.

### Splitting into calibration vs validation

The split is an operator decision: the **fit** set goes to `calibration_points.csv`, and
**hold-out** points not used in the fit go to `validation_points.csv`.

In either GUI, choose the set in the **Add to** dropdown when adding a point, or change a
row's **Set** dropdown afterwards — the CSVs are rewritten on every change. By hand, edit
the two files directly.

Optional **repeatability**: in the validation set, measure the same world point more than
once and reuse the **same label** with the **same world coordinates**. The report then
computes per-label standard deviation and spread. If the same label is reused for
*different* world points, that label is skipped and a warning is written into `report.md`.

---

## 4. CSV format

**Required columns** (only these six are mandatory):

```text
world_x, world_y, world_z, sensor_x, sensor_y, sensor_z
```

**Optional columns:** `label`, `notes`.

Full header (matches the templates the tool creates):

```csv
label,world_x,world_y,world_z,sensor_x,sensor_y,sensor_z,notes
```

Example rows:

```csv
label,world_x,world_y,world_z,sensor_x,sensor_y,sensor_z,notes
P0,0,0,0,1106.28,25.38,-160.68,origin
PX,100,0,0,1205.10,24.90,-161.20,
PY,0,100,0,1107.00,125.50,-160.40,
```

Blank lines are skipped. Non-numeric coordinates raise an error that names the physical
CSV line number.

---

## 5. Outputs and pass criteria

After a successful run, the session folder contains:

| File | Purpose |
|------|---------|
| `report.md` | Human-readable summary: transform, RMSE, per-point errors, PASS/FAIL |
| `calibration.json` | Candidate transform `{R, t, rmse_mm, n_points}` for review and optional explicit legacy use |
| `calibration_errors.csv` | Per-point calibration residuals |
| `validation_errors.csv` | Per-point validation residuals |

**Pass criteria** (printed in the report Thresholds table):

| Check | Limit |
|-------|------:|
| Calibration RMSE | ≤ 10.0 mm |
| Validation max error | ≤ 15.0 mm |

Both must PASS before you use the session JSON or consider accepting the transform.

**Error sign convention:** in the report tables and error CSVs,

```text
dX / dY / dZ = computed − world
```

Positive means the transformed sensor reading overshoots the known world coordinate.
`error_mm` is the Euclidean norm of that delta.

If calibration uses fewer than 8 points, `report.md` includes a warning — still usable for
bench checks, but prefer 8+ for a final field report.

---

## 6. Optional Explicit Legacy Transform

The session `calibration.json` stays in the session directory. There is no checked-in shared/default
file and no tool auto-loads one. After **both** Calibration and Validation show **PASS**, the legacy
visualizer can inspect that session transform only when the path is supplied explicitly:

```bash
python -m tools.position_checker.main --legacy-visualizer --port /dev/ttyUSB0 \
  --calibration docs/calibration/sessions/current/calibration.json
```

Without `--calibration PATH`, it remains in the sensor frame; a JSON with a non-`PASS` verdict is
rejected. Passing and viewing a transform do not by themselves create project acceptance.

`tools/evka_gui` is not a transform consumer. It records, plots, and solves IPT in the sensor frame.
The currently named **Deploy calibration.json** GUI action is legacy source behavior. The report CLI
prints only an explicit legacy-visualizer invocation; neither path changes the canonical GUI frame.

---

## 7. Session archiving

Before starting a new calibration session:

1. Copy the working folder to a dated archive, for example:

   ```bash
   cp -r docs/calibration/sessions/current \
         docs/calibration/sessions/2026-07-16_operator
   ```

2. Clear or replace the point rows in `current/calibration_points.csv` and
   `current/validation_points.csv` (keep the header).
3. Attach the archived `report.md` (and optionally the error CSVs) to the final calibration
   record — see [templates/final_calibration_record_template.md](templates/final_calibration_record_template.md).

Generated artifacts (`report.md`, `calibration.json`, `*_errors.csv`) are git-ignored under
`sessions/`; archive or attach them outside git if you need a durable paper trail.

---

## 8. Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `Input templates are ready…` | CSVs are empty (header only). Add rows and rerun. |
| `need at least 3 calibration points` | Too few fit points in `calibration_points.csv`. |
| `need at least 1 validation point` | Add at least one hold-out row to `validation_points.csv`. |
| `collinear or coincident` | Spread calibration points in at least two directions (not a single line). |
| `missing columns: …` | CSV is missing one of the six required coordinate headers. |
| `row N has non-numeric coordinates` | Bad cell; `N` is the physical line number (blank lines counted). |
| Calibration **FAIL** (RMSE > 10 mm) | Re-check Stages 1–4; re-measure outliers; avoid collinear sets. |
| Validation **FAIL** (max > 15 mm) | Hold-outs disagree with the fit - re-measure; do not copy or accept. |
| Repeatability warning in report | Same `label` used for different world points — use unique labels or identical world coords for repeats. |
| High residuals after copy | Confirm the session passed and re-check mechanics, scale, labels, and hold-outs. |

---

## 9. Legacy alternative

For a one-off fit without validation CSVs, you can still edit embedded arrays in
`tools/calibration/calibrate.py` and run:

```bash
python -m tools.calibration.calibrate
python -m tools.calibration.calibrate --out /tmp/evka_candidate_calibration.json
```

That path writes (or can write) `calibration.json` directly and does **not** produce
`report.md` or a hold-out validation table. Prefer the report workflow for field sessions
and an auditable PASS/FAIL record. Do not use quick-fit output as a passing session transform.

---

## 10. Tests

```bash
pytest tools/calibration/tests/test_report.py -q
```
