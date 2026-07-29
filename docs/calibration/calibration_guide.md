# Calibration Guide — evka_position

Full end-to-end calibration procedure: per-encoder PPR, firmware update, and candidate endpoint
world transform.

> **Prototype gate:** theta count loss is unresolved. Stop before changing accepted scale values or
> fitting an endpoint transform until repeated points and home return with stable theta counts. No
> endpoint/world transform or shared/default calibration JSON is accepted. `tools/evka_gui`
> displays sensor-frame data only.

---

## Pipeline Overview

| Stage | What it calibrates | Firmware | Tool |
|-------|--------------------|----------|------|
| 1 | Wire encoder — `MM_PER_PULSE` / `PPR_WIRE` | main firmware (v4) or `test_drawwire` (classic) | Serial/dashboard + this guide |
| 2 | Theta rotary — `PPR_ROTARY` | main firmware (v4) or `test_calibration` (classic) | Serial + this guide |
| 3 | Phi rotary — `PPR_ROTARY` | main firmware (v4) or `test_calibration` (classic) | Serial + this guide |
| 4 | Firmware constants | — | Edit `SphericalSensor.h`, reflash |
| 5 | Candidate endpoint world transform | main firmware (`esp32s3_v4` / `wemos_d1_r32`) | `python -m tools.calibration.report` - see [report_workflow.md](report_workflow.md) |
| 6 | Candidate validation | main firmware | Hold-out CSV in report; `evka_gui` remains sensor-frame-only |

Complete stages **in order** after the theta repeatability gate passes. Endpoint calibration (Stage
5) is only meaningful after mechanics, count return, and PPR constants are correct.

---

## Stage 1 — Wire Encoder (PPR_WIRE / MM_PER_PULSE)

**Goal**: Determine how many mm the wire travels per encoder pulse.

### 1.1 Option A — Web dashboard (recommended, tablet-friendly)

With main firmware (`ENABLE_WIFI=1`) flashed and running:
1. Connect to `CMDCNC_EVKA` WiFi → open `http://192.168.1.50` → tap **CALIBRATE → WIRE**
2. For each trial: tap **ZERO WIRE**, pull wire to a known distance, enter the distance in mm, tap **RECORD**
3. Collect at least 5 trials at different distances (e.g. 100, 200, 300, 400, 500 mm)
4. The table shows Factor and PPR_WIRE per trial; the header shows Mean PPR_WIRE and Spread %
5. Tap **APPLY + SAVE (NVS)** to apply the mean and persist it to flash (survives reboot)

### 1.2 Option B - Main firmware command path

For v4, keep `esp32s3_v4` installed. Repeat at least five known distances in both directions:

```text
ZERO_W
# Pull to exactly <actual_mm>
CAL_W <actual_mm>
```

Main firmware replies:

```text
CAL:WIRE,<factor>,<mm_per_pulse>,<new_ppr_wire>
```

Record each trial. Apply the mean with `SET_PPR_WIRE <mean_ppr>`, then use `SAVE_PPR` only after
reviewing the set.

### 1.3 Option C - Classic standalone test

```bash
pio run -e test_drawwire --target upload
pio device monitor -e test_drawwire
```

This environment uses classic GPIO16/17. It accepts `ZERO_W` and `CAL_W <actual_mm>`, prints a
human-readable result, and updates only its running RAM value. It does not support `SET_PPR_WIRE` or
`SAVE_PPR`. Do not flash it onto v4.

### 1.4 Acceptance criteria

| Check | Threshold |
|-------|-----------|
| Trial-to-trial PPR_WIRE spread | ≤ 1.0% |
| Extend vs retract hysteresis | ≤ 0.5% of actual distance |

If hysteresis exceeds threshold: check cable alignment, spring tension, and pulley friction.

### 1.5 Final value

```
new_PPR_WIRE = mean(ppr_wire of accepted trials)
new_MM_PER_PULSE = DRUM_CIRCUM_MM / new_PPR_WIRE   (= 200 / new_PPR_WIRE)
```

---

## Stage 2 — Theta Rotary Encoder (PPR_ROTARY)

**Goal**: Determine pulses per full revolution for the theta (azimuth) axis.

### 2.1 Flash and connect

The standalone `test_*` environments target the classic Wemos pin map only. For the v4 carrier,
keep main `esp32s3_v4` firmware installed and use `ZERO_T`, rotate a measured number of full
turns, then send `CAL_T <n>`. The interactive SPACE/DONE procedure below is available only in the
classic-board `test_calibration` sketch:

```bash
pio run -e test_calibration --target upload
pio device monitor -e test_calibration
```

Theta encoder pins in this classic test are `A → GPIO 14`, `B → GPIO 12`. Disconnect phi encoder for isolated testing.

### 2.2 v4/main-firmware trial

Repeat at least three CW and three CCW trials:

```text
ZERO_T
# Rotate exactly N full turns
CAL_T N
```

Reply: `CAL:THETA,<signed_counts>,<ppr>`. Record signed counts and compare PPR magnitude. This command
does not apply the candidate PPR.

### 2.3 Classic interactive trial

Repeat at least 3 × CW and 3 × CCW:

```
1. ZERO_T                          ← reset theta encoder
2. CAL_T                           ← enter interactive calibration mode
3. Rotate one full turn, press SPACE (firmware prints per-turn count)
4. Repeat step 3 for N turns (recommend N = 5)
5. DONE                            ← firmware prints average PPR and updates live values
```

During calibration, firmware prints after each SPACE:
```
Turn 1: delta=<n>  running_avg_ppr=<p>
```

On `DONE`, the standalone sketch prints a human-readable `CAL_T RESULT` block with per-turn counts,
average PPR, and degrees/count. Record the values in
`templates/rotary_calibration_log_template.csv`.

Example fields:
```
Turns recorded : <N>
Average PPR    : <p>
deg/pulse      : <d>
```

### 2.4 Acceptance criteria

| Check | Threshold |
|-------|-----------|
| Per-trial PPR spread | ≤ 1.0% |
| CW vs CCW mean difference | ≤ 1.0% |

If thresholds fail: check coupler slippage, shaft backlash, A/B wiring.

For the current v4 prototype, passing a multi-turn scale trial is not enough: repeated marked-point
and home returns must also show stable theta counts. See
[sessions/2026-07-17_repeatability.md](sessions/2026-07-17_repeatability.md).

### 2.5 Final value

```
PPR_ROTARY_THETA = mean(|avg_ppr| of all accepted CW + CCW trials)
DEG_PER_PULSE    = 360 / PPR_ROTARY_THETA
```

---

## Stage 3 — Phi Rotary Encoder (PPR_ROTARY)

**Goal**: Same as Stage 2, for the phi (elevation) axis.

### 3.1 Flash and connect

Same `test_calibration` firmware. Phi encoder pins in this classic test are `A → GPIO 32`, `B → GPIO 35`.

### 3.2 Trial procedure

For v4/main firmware, use `ZERO_P`, rotate exactly N full turns, then send `CAL_P N`; reply is
`CAL:PHI,<signed_counts>,<ppr>`. For the classic interactive sketch, substitute:
- `ZERO_P` instead of `ZERO_T`
- `CAL_P` instead of `CAL_T`

### 3.3 Compare theta vs phi result

```
If |PPR_ROTARY_THETA - PPR_ROTARY_PHI| / PPR_ROTARY_THETA ≤ 0.5%:
    → Use a single PPR_ROTARY = mean(theta, phi)
Else:
    → Encoders may differ; investigate mechanically before proceeding
```

---

## Stage 4 — Apply Calibrated Constants

Two options — NVS (no reflash) or compile-time (permanent baseline):

### 4a — NVS (recommended for quick iteration)

If you used the web dashboard or sent `SET_PPR_WIRE` / `SET_PPR_ROTARY` over serial, finalize with:

```
SAVE_PPR   →   ACK:SAVE_PPR
```

On every subsequent boot, `loadPPRFromNVS()` restores these values automatically (logged to serial as `[Cal] NVS load: PPR_R=... PPR_W=...`).

### 4b — Compile-time constants (permanent baseline)

Edit `firmware/src/SphericalSensor.h`:

```cpp
#define PPR_ROTARY      <new_PPR_ROTARY>      // from Stage 2/3
#define PPR_WIRE        <new_PPR_WIRE>         // from Stage 1
```

`DEG_PER_PULSE` and `MM_PER_PULSE` are derived automatically — do not edit them directly.

Create a backup before editing:
```bash
cp firmware/src/SphericalSensor.h firmware/src/SphericalSensor.h.bak
```

Reflash the board in use (v4 shown):
```bash
pio run -e esp32s3_v4 --target upload
```

> **Note**: NVS values take precedence over compile-time defaults. After reflashing, the NVS namespace `evka_cal` will still load unless cleared (use `nvs_flash_erase()` or erase flash fully).

Verify by sending `CONSTANTS` and checking that `r`, `theta`, `phi` values are physically plausible.

---

## Stage 5 — Candidate Endpoint World Transform (Kabsch Calibration)

**Goal**: Compute the 3×3 rotation R and translation t that map sensor Cartesian coordinates to your world coordinate frame:

```text
world = R @ sensor + t
```

**Requirement**: Complete Stages 1–4 first. This stage corrects frame tilt/orientation, not encoder scale.

**Preferred tool**: the calibration report workflow. Full operator guide:
[report_workflow.md](report_workflow.md).

### 5.1 Collect reference points

With main firmware running, move the probe to known world positions and record the sensor-frame XYZ
output. Do not collect this set while theta return is unstable.

**Minimum for the report tool**: 3 calibration + 1 validation point.
**Recommended**: 8+ calibration points, **not collinear**, plus 3–5 hold-outs.

Suggested layout:
- 3–4 points along +X (e.g. 100, 200, 400, 600 mm)
- 3–4 points along +Y
- 1–2 points along +Z or otherwise off-plane

Collection options:
- `python -m tools.calibration.gui` → Endpoint → **Add pair** (writes the session CSVs directly)
- `evka_gui` toolbar **Calibration…** → Endpoint → **Add pair** (same workflow)
- Web dashboard **CALIBRATE → ENDPOINT** → EXPORT CSV (then **Import CSV**)
- Serial `STATUS` (last three fields are sensor `x,y,z`)

`STATUS` reply format:
```
STATUS,<is_valid>,<frame_count>,<ts_ms>,<r>,<theta>,<phi>,<x>,<y>,<z>
```

### 5.2 Assign the sets and run the report

In `python -m tools.calibration.gui` → **Endpoint** (or `evka_gui` → **Calibration…** →
**Endpoint**): pick **Add to: Calibration** (fit) or **Validation** (hold-out) per point,
then **Generate report**. The verdict and per-point residuals appear in the tab.

By hand instead:

```bash
# First run creates templates under docs/calibration/sessions/current/ if missing
python -m tools.calibration.report
```

1. Put **fit** points in `docs/calibration/sessions/current/calibration_points.csv`.
2. Put **hold-out** points in `docs/calibration/sessions/current/validation_points.csv`.
3. Run again:

```bash
python -m tools.calibration.report
```

Outputs: `report.md`, session `calibration.json`, and per-point error CSVs.
Target in the report: **Calibration RMSE ≤ 10 mm**.

If RMSE is high (> 20 mm):
- Check that PPR calibration (Stages 1–4) is complete
- Verify points are not collinear
- Re-measure any outlier points

### 5.3 Optional explicit legacy transform (only after PASS)

Keep the passing `calibration.json` in its session directory. There is no shared/default file and no
auto-load behavior. To inspect the candidate in the legacy visualizer, pass the session path
explicitly:

```bash
python -m tools.position_checker.main --legacy-visualizer --port /dev/ttyUSB0 \
  --calibration docs/calibration/sessions/current/calibration.json
```

This optional legacy view is not approval. `tools/evka_gui` does not consume the transform for live
display. Record explicit acceptance and the consuming application in the final calibration record.

### 5.4 Legacy / quick fit (optional)

For a one-off fit without validation CSVs, edit embedded `SENSOR_PTS` / `WORLD_PTS` in
`tools/calibration/calibrate.py` and run:

```bash
python -m tools.calibration.calibrate
python -m tools.calibration.calibrate --out /tmp/evka_candidate_calibration.json
```

Prefer the report workflow for field sessions and an auditable PASS/FAIL record. A quick-fit output
is not a passing session JSON.

---

## Stage 6 — Validation

### 6.1 Hold-out points (report)

Hold-outs belong in `validation_points.csv` (Stage 5). The report marks Validation
**PASS** when max error is **≤ 15 mm**.

Optional: repeat the same label at the same world coordinates to get repeatability stats
in `report.md`.

### 6.2 Live position check

To inspect the candidate with the legacy transform-aware visualizer:

```bash
python -m tools.position_checker.main --legacy-visualizer --port /dev/ttyUSB0 \
  --calibration docs/calibration/sessions/current/calibration.json
```

Without `--calibration PATH`, the legacy visualizer stays in the sensor frame. A JSON whose report
verdict is not `PASS` is rejected.

`tools/evka_gui` is the canonical operator GUI but intentionally remains sensor-frame-only. Use the
report residuals/hold-outs for candidate validation; do not expect world XYZ in `evka_gui`.

### 6.3 Flat-plane check

Place the probe at several points on a flat table (all at the same physical height). In the report or
a deliberately transform-aware legacy consumer, transformed `z_mm` should be consistent across all
table points (variation < 5 mm). Canonical `evka_gui` still shows sensor-frame Z.

---

## Acceptance Criteria Summary

| Stage | Metric | Target |
|-------|--------|--------|
| 1 — Wire | Factor spread across trials | ≤ 1.0% |
| 1 — Wire | Extend/retract hysteresis | ≤ 0.5% |
| 2/3 — Rotary | Per-trial PPR spread | ≤ 1.0% |
| 2/3 — Rotary | CW vs CCW agreement | ≤ 1.0% |
| 5 — Endpoint | Kabsch RMSE (report) | ≤ 10 mm |
| 6 — Validation | Hold-out max error (report) | ≤ 15 mm |
| 6 — Validation | Flat-plane Z variation | < 5 mm |

---

## Re-calibration Triggers

Re-run the affected stages if:
- Draw-wire drum is replaced or re-spooled → Stage 1 + 4 + 5
- Rotary encoder is replaced or coupling slips → Stage 2/3 + 4 + 5
- Sensor head is physically re-mounted or rotated → Stage 5 only
- RMSE drifts above 20 mm after normal use -> inspect repeatability and scale before deciding which
  stage to repeat

For Stages 1–3 re-calibration: use the web CALIBRATE tab (no reflash needed). Tap **APPLY + SAVE (NVS)** to persist. Only update compile-time constants in `SphericalSensor.h` when the new value is confirmed stable.
