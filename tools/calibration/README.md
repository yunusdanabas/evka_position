# tools/calibration — world↔sensor calibration

Computes the rigid-body transform (rotation **R**, translation **t**) that maps the sensor's
coordinate frame into the machine/world frame, so measured points can be reported in world
coordinates:

```
world_point ≈ R @ sensor_point + t
```

It uses the **Kabsch algorithm** (least-squares best-fit rotation + translation) on a set of paired
`sensor ↔ world` points.

## Run

```bash
# From the repo root
python -m tools.calibration.calibrate
python -m tools.calibration.calibrate --out tools/calibration/calibration.json
```

Output: the fit **R** and **t**, the per-point residuals, and the RMS error; written to
`calibration.json` (consumed by downstream tools that need world coordinates).

## Providing calibration data

The measured point pairs are currently embedded near the top of `calibrate.py`
(`SENSOR_PTS` / `WORLD_PTS` — a dated measurement session). To recalibrate:

1. Move the tip to each known world point and record the sensor XYZ (the web dashboard's
   **CALIBRATE → Endpoint** tab records world/sensor pairs and exports CSV).
2. Replace `SENSOR_PTS` / `WORLD_PTS` in `calibrate.py` (or wire in CSV loading) and re-run.

More points, well spread in **all three axes**, give a better fit — a single-axis set leaves the
rotation poorly constrained.

## Files

| File | Role |
|---|---|
| `calibrate.py` | Kabsch solver + embedded measurement data + CLI |
| `calibration.json` | Last computed transform (`R` 3×3, `t` 3-vector) |
