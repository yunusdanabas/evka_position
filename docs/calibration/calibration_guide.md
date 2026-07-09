# Calibration Guide — evka_position

Full end-to-end calibration procedure: per-encoder PPR, firmware update, and endpoint world-transform.

---

## Pipeline Overview

| Stage | What it calibrates | Firmware | Tool |
|-------|--------------------|----------|------|
| 1 | Wire encoder — `MM_PER_PULSE` / `PPR_WIRE` | `test_drawwire` | Serial + this guide |
| 2 | Theta rotary — `PPR_ROTARY` | `test_rotary` or `test_calibration` | Serial + this guide |
| 3 | Phi rotary — `PPR_ROTARY` | `test_rotary` or `test_calibration` | Serial + this guide |
| 4 | Firmware constants | — | Edit `SphericalSensor.h`, reflash |
| 5 | Endpoint world transform | `wemos_d1_r32` (production) | `tools/calibration/calibrate.py` |
| 6 | Validation | `wemos_d1_r32` (production) | `tools/position_checker` |

Complete stages **in order**. Endpoint calibration (Stage 5) is only meaningful after PPR constants are correct (Stages 1–4).

---

## Stage 1 — Wire Encoder (PPR_WIRE / MM_PER_PULSE)

**Goal**: Determine how many mm the wire travels per encoder pulse.

### 1.1 Option A — Web dashboard (recommended, tablet-friendly)

With production firmware (`ENABLE_WIFI=1`) flashed and running:
1. Connect to `EvkaPosition` WiFi → open `http://192.168.4.1` → tap **CALIBRATE → WIRE**
2. For each trial: tap **ZERO WIRE**, pull wire to a known distance, enter the distance in mm, tap **RECORD**
3. Collect at least 5 trials at different distances (e.g. 100, 200, 300, 400, 500 mm)
4. The table shows Factor and PPR_WIRE per trial; the header shows Mean PPR_WIRE and Spread %
5. Tap **APPLY + SAVE (NVS)** to apply the mean and persist it to flash (survives reboot)

### 1.2 Option B — Serial / test firmware

```bash
pio run -e test_drawwire --target upload
pio device monitor -e test_drawwire
```

Wire encoder pins: `A → GPIO 16`, `B → GPIO 17`.

Repeat for at least 5 different known distances, both extend and retract:

```
1. ZERO_W                  ← reset wire encoder to 0
2. Pull wire to exactly <actual_mm> (use a rigid ruler, not a tape)
3. CAL_W <actual_mm>
```

Firmware replies:
```
CAL:WIRE,<factor>,<mm_per_pulse>,<new_ppr_wire>
```

Record each trial. Apply the mean: `SET_PPR_WIRE <mean_ppr>`, then `SAVE_PPR` to persist.

### 1.3 Acceptance criteria

| Check | Threshold |
|-------|-----------|
| Trial-to-trial PPR_WIRE spread | ≤ 1.0% |
| Extend vs retract hysteresis | ≤ 0.5% of actual distance |

If hysteresis exceeds threshold: check cable alignment, spring tension, and pulley friction.

### 1.4 Final value

```
new_PPR_WIRE = mean(ppr_wire of accepted trials)
new_MM_PER_PULSE = DRUM_CIRCUM_MM / new_PPR_WIRE   (= 200 / new_PPR_WIRE)
```

---

## Stage 2 — Theta Rotary Encoder (PPR_ROTARY)

**Goal**: Determine pulses per full revolution for the theta (azimuth) axis.

### 2.1 Flash and connect

```bash
pio run -e test_rotary --target upload
pio device monitor -e test_rotary
```

Theta encoder pins: `A → GPIO 32`, `B → GPIO 35`. Disconnect phi encoder for isolated test.

### 2.2 Trial procedure (interactive)

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

On `DONE`:
```
THETA CAL DONE  turns=<N>  total_counts=<total>  avg_ppr=<p>  deg_per_pulse=<d>
```

Record each `DONE` line in `templates/rotary_calibration_log_template.csv`.

### 2.3 Acceptance criteria

| Check | Threshold |
|-------|-----------|
| Per-trial PPR spread | ≤ 1.0% |
| CW vs CCW mean difference | ≤ 1.0% |

If thresholds fail: check coupler slippage, shaft backlash, A/B wiring.

### 2.4 Final value

```
PPR_ROTARY_THETA = mean(|avg_ppr| of all accepted CW + CCW trials)
DEG_PER_PULSE    = 360 / PPR_ROTARY_THETA
```

---

## Stage 3 — Phi Rotary Encoder (PPR_ROTARY)

**Goal**: Same as Stage 2, for the phi (elevation) axis.

### 3.1 Flash and connect

Same `test_rotary` firmware. Phi encoder pins: `A → GPIO 14`, `B → GPIO 12`.

### 3.2 Trial procedure

Identical to Stage 2, substituting:
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

Reflash:
```bash
pio run -e wemos_d1_r32 --target upload
```

> **Note**: NVS values take precedence over compile-time defaults. After reflashing, the NVS namespace `evka_cal` will still load unless cleared (use `nvs_flash_erase()` or erase flash fully).

Verify by sending `CONSTANTS` and checking that `r`, `theta`, `phi` values are physically plausible.

---

## Stage 5 — Endpoint World Transform (Kabsch Calibration)

**Goal**: Compute the 3×3 rotation R and translation t that map sensor Cartesian coordinates to your world coordinate frame.

**Requirement**: Complete Stages 1–4 first. This stage corrects frame tilt/orientation, not encoder scale.

### 5.1 Collect reference points

With production firmware running, move the probe to known world positions and record the sensor's output.

**Minimum**: 8 points, **not collinear**. Recommended layout:
- 3–4 points along +X (e.g. 100, 200, 400, 600 mm)
- 3–4 points along +Y (e.g. 100, 200, 400, 600 mm)
- 1–2 points along +Z if possible (or off-plane)

For each point:
```
1. Move probe to known world position (x_w, y_w, z_w)
2. Send STATUS over serial
3. Record sensor output: x_s, y_s, z_s from STATUS reply
```

`STATUS` reply format:
```
STATUS,<is_valid>,<frame_count>,<ts_ms>,<r>,<theta>,<phi>,<x>,<y>,<z>
```
Use the last three fields as `x_s, y_s, z_s`.

### 5.2 Update calibrate.py

Open `tools/calibration/calibrate.py` and replace `SENSOR_PTS` and `WORLD_PTS` with your collected data:

```python
LABELS = ["ORIGIN", "P1", "P2", ...]

SENSOR_PTS = np.array([
    [x_s0, y_s0, z_s0],   # ORIGIN → world (0, 0, 0)
    [x_s1, y_s1, z_s1],   # P1     → world (100, 0, 0)
    ...
], dtype=float)

WORLD_PTS = np.array([
    [0,   0, 0],
    [100, 0, 0],
    ...
], dtype=float)
```

### 5.3 Run calibration

```bash
python -m tools.calibration.calibrate
```

Output includes per-point residuals and RMSE. Target: **RMSE < 10 mm**.

If RMSE is high (> 20 mm):
- Check that PPR calibration (Stages 1–4) is complete
- Verify points are not collinear
- Re-measure any outlier points

Calibration is saved to `tools/calibration/calibration.json` automatically.

---

## Stage 6 — Validation

### 6.1 Live position check

```bash
python -m tools.position_checker --port /dev/ttyUSB0
```

The tool auto-loads `tools/calibration/calibration.json` if present.

### 6.2 Hold-out test

Move the probe to **3–5 positions that were NOT used in Stage 5** and verify the displayed coordinates match expectations. Acceptable error: **< 15 mm** at distances up to 1 m.

### 6.3 Flat-plane check

Place the probe at several points on a flat table (all at the same physical height). After calibration, the displayed `z_mm` should be consistent across all table points (variation < 5 mm).

---

## Acceptance Criteria Summary

| Stage | Metric | Target |
|-------|--------|--------|
| 1 — Wire | Factor spread across trials | ≤ 1.0% |
| 1 — Wire | Extend/retract hysteresis | ≤ 0.5% |
| 2/3 — Rotary | Per-trial PPR spread | ≤ 1.0% |
| 2/3 — Rotary | CW vs CCW agreement | ≤ 1.0% |
| 5 — Endpoint | Kabsch RMSE | < 10 mm |
| 6 — Validation | Hold-out error | < 15 mm |
| 6 — Validation | Flat-plane Z variation | < 5 mm |

---

## Re-calibration Triggers

Re-run the affected stages if:
- Draw-wire drum is replaced or re-spooled → Stage 1 + 4 + 5
- Rotary encoder is replaced or coupling slips → Stage 2/3 + 4 + 5
- Sensor head is physically re-mounted or rotated → Stage 5 only
- RMSE drifts above 20 mm after normal use → Stage 5 only

For Stages 1–3 re-calibration: use the web CALIBRATE tab (no reflash needed). Tap **APPLY + SAVE (NVS)** to persist. Only update compile-time constants in `SphericalSensor.h` when the new value is confirmed stable.
