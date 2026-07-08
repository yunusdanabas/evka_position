# Kinematics & Calibration — Laser Radius Variant

**Parent doc:** [`README.md`](README.md). Covers laser-on-phi-head geometry, the spherical origin offset correction, and a calibration workflow to replace `CAL_W`/`PPR_WIRE`.

**Fixed requirement (2026-07-01, revised):** the laser device itself must be ≤10 mm accurate out to 40 m (confirmed with the user as a device-selection spec, not a combined-system target — see §4 for what that means for total XYZ accuracy).

---

## 1. Geometry: Laser on the Phi Head

Per the fixed design decision, the laser is mounted **on the phi head, pointing at the target along the boom** — its optical boresight is intended to be coincident with (or as close as mechanically practical to) the phi rotation axis. The laser measures a slant range along the same line `r` already represents in the spherical model, so no trigonometric correction is needed for the aiming direction itself. Two physical facts still need correction terms:

### 1.1 Fixed axial offset (always applies)

The laser's own optical reference plane sits some fixed distance forward of the phi pivot, because the laser body has physical length and a mounting bracket standoff. Simple additive constant, measured once at assembly:

```
r_true_mm = r_laser_reading_mm + d_offset_mm
```

`d_offset_mm` plays the role the old `DRUM_CIRCUM_MM`-derived scale did for the draw-wire, but is additive rather than multiplicative — every candidate device in this revised study (`version_a_handheld_devices.md`, `version_b_integrated_modules.md`) reports calibrated millimeters directly; there's no pulse-counting scale factor to derive.

### 1.2 Blind zone (device-dependent, affects zero-point strategy)

Every phase-shift device in the current shortlist has a minimum range below which it can't report a valid distance (JRT B605B / Meskernel LDL-T: 0.03 m; Bosch PLR 40 C: 0.05 m; Dimetix: 0.05 m). The current firmware's `RADIUS_MIN_MM = 0` supports a true zero-home boot sequence (`setZeroPoint()` 2 s after power-on, per `CLAUDE.md`) — **a laser cannot physically measure `r ≈ 0`.** Consequences:
- Boot-time `setZeroPoint()` cannot rely on reading `r = 0` — home must be a known non-zero reference distance outside the blind zone (§3).
- `RADIUS_MIN_MM` should be raised to the device's blind-zone floor (plus `d_offset_mm`) for this variant.

### 1.3 Lateral (off-axis) offset — only if the on-axis mount can't be achieved

If the laser body ends up with a small lateral displacement `e_mm` from the true phi rotation axis, a target along the boom's pointing direction is measured at a very slightly different slant range than the true on-axis `r`. For `e_mm << r` this is negligible at any range in this study (0–40 m). Recommendation: keep the laser boresight on-axis by design and treat lateral offset as negligible unless bench measurement shows otherwise.

## 2. Target Reflectivity

Phase-shift devices are generally more forgiving of surface reflectivity than pulsed ToF (they integrate over a modulated signal rather than needing a clean single-pulse return), but accuracy still degrades on very dark, glossy, or steeply angled surfaces — Bosch's own spec sheet explicitly notes a ±4 mm worst-case figure "in unfavourable conditions … poorly reflecting surface" (see `version_a_handheld_devices.md` §2.3), still within the ≤10 mm budget but worth planning for. Recommendations:
- Prefer a matte, light-colored, perpendicular target surface at the measurement point where possible.
- If the target surface is uncontrolled, consider a small fixed retroreflective/diffuse reference patch at the expected contact point (Dimetix even sells a purpose-made reflective target plate as an accessory — see `procurement_and_bom.md`).
- Firmware should surface confidence/signal-quality data (if the chosen device exposes it) through `is_valid`, mirroring how the current system already treats degraded encoder data as invalid rather than silently wrong.

## 3. Calibration Workflow — Replacing `CAL_W`

The draw-wire's `CAL_W` exists because a drum-and-pulse-count system has two unknowns: a scale factor (mm per pulse) and a zero offset. A laser device removes the scale unknown — it already reports calibrated millimeters — leaving only the additive offset from §1.1 (and, rarely, a minor linearity check).

### 3.1 New commands (proposed, firmware not implemented — see `firmware_integration.md`)

| Command | Response | Behavior |
|---|---|---|
| `ZERO_R` | `ACK:ZERO_R` | Captures the current raw laser reading at a known reference position and zeroes `r_offset_mm` against it (mirrors `ZERO_W`) |
| `CAL_R <known_mm>` | `CAL:RADIUS,<offset_mm>` | Operator places a target at a precisely known distance `known_mm` (outside the device's blind zone); firmware computes `r_offset_mm = known_mm - raw_reading_mm`. Preferred over `ZERO_R` — no need for a literal mechanical zero, which the laser can't measure anyway (§1.2). Errors mirror `CAL_W`'s pattern: `ERR:CAL_R bad value`, `ERR:CAL_R out of range` |
| `SET_R_OFFSET <v>` | `ACK:R_OFFSET,<v>` | Update offset in RAM directly (mirrors `SET_PPR_WIRE`) |
| `SAVE_R` | `ACK:SAVE_R` | Persist `r_offset_mm` (and optional `r_scale`) to NVS (mirrors `SAVE_PPR`) |

### 3.2 Optional linearity spot-check

Phase-shift devices are inherently metric and linear within spec, so a full multi-trial mean/spread calibration (as `CAL_W` requires for the draw-wire's mechanical drum) isn't needed. Place a target at 2–3 known distances spanning 0–40 m, compare reported vs. actual after applying `r_offset_mm`, and confirm the residual stays within the device's ≤10 mm spec (all recommended devices should show far tighter residuals — 1–3 mm class, per `version_a_handheld_devices.md`/`version_b_integrated_modules.md`). Only add a multiplicative `r_scale` term (default `1.0`) if a systematic scale error actually shows up.

### 3.3 NVS persistence

Reuse the existing `evka_cal` namespace. Add `r_offset` (float, mm) and optionally `r_scale` (float, default `1.0`). Apply the same load-time validation pattern already used for PPR values (`isfinite` + range guard): reject `r_offset` outside a sane bound (e.g., `|r_offset| > RADIUS_MAX_MM`) and fall back to `0.0`. The `ppr_wire` NVS key doesn't apply to this variant.

### 3.4 Web dashboard CALIBRATE tab impact

Replace the wire tab's multi-trial table (mean PPR, spread %, APPLY/APPLY+SAVE) with a simpler panel: one `CAL_R` action (enter known distance, click compute) plus a 2–3-row spot-check table (expected vs. measured, pass/fail against the ≤10 mm spec). Theta/Phi tabs are unaffected.

## 4. Combined Error Budget — Why the Laser Spec Alone Isn't the Whole Story

**This section is informational context, not a redesign trigger** — per the user's explicit decision, the ≤10 mm requirement applies to the laser device's own spec, and the encoder side is out of scope for this study. It's included because the number is large enough to be worth knowing before committing to a 40 m working range in practice.

The rotary encoders' angular resolution contributes an arc-length error that **grows linearly with `r`**: `arc_error_mm ≈ r_mm × sin(DEG_PER_PULSE in radians) ≈ r_mm × 3.1416×10⁻⁴` at `DEG_PER_PULSE = 0.018°`. Combining independent error sources by RSS (θ-arc, φ-arc, laser accuracy) for the shortlisted devices:

| Range `r` | θ/φ arc error (each axis) | + JRT B605B (±1mm+40ppm) | + Bosch PLR 40 C (±2mm flat) | + Dimetix/Meskernel (±1mm flat) |
|---|---|---|---|---|
| 5 m | 1.57 mm | ≈2.5 mm | ≈3.0 mm | ≈2.4 mm |
| 20 m | 6.28 mm | ≈9.1 mm | ≈9.1 mm | ≈8.9 mm |
| 40 m | 12.57 mm | ≈18.0 mm | ≈17.9 mm | ≈17.8 mm |

**Key finding, unchanged in substance from the prior tiered pass:** every laser candidate in this revised study clears its own ≤10 mm bar at 40 m by a wide margin (all report ≤2.6 mm of their own error). But the **combined XYZ position accuracy at 40 m is ≈18 mm regardless of which laser is chosen**, because the θ/φ encoders alone contribute ~17.8 mm (RSS both axes) at that range — the laser choice barely moves the total once you're past ~10–15 m. If total system accuracy ever becomes the requirement (rather than laser-device accuracy alone, per this session's clarification), the bottleneck is the encoders, not the laser — see `docs/research/improvement_research.md` §4.4 and §5.1 for encoder resolution / absolute-encoder upgrade paths that would need revisiting in that scenario.

## Open Risks

1. **Zero-point strategy changes fundamentally** — `setZeroPoint()` assumes a literal `r ≈ 0` mechanical home; a laser variant needs a redefined home procedure (§1.2/§3.1) before firmware work starts.
2. **`RADIUS_MIN_MM` needs to move** from `0` to the chosen device's blind-zone floor.
3. **`d_offset_mm` depends on final mechanical mounting**, which doesn't exist yet.
4. **Target reflectivity in real working conditions is unknown** — §2's recommendations are generic.
5. **The 40 m combined-system accuracy figure (§4, ≈18 mm) is out of scope per the user's decision but should be revisited if this variant is ever asked to guarantee total XYZ accuracy, not just laser accuracy, at long range.**

## Next Physical Test Steps

1. Once a laser candidate is on the bench, measure its actual blind zone and confirm the datasheet's minimum range figure.
2. Mock up the phi-head mount and physically measure `d_offset_mm` from the phi rotation axis to the laser's stated optical reference plane.
3. Run the 2–3 point spot-check (§3.2) on a physical device across 5 m / 20 m / 40 m and confirm the ≤10 mm spec holds in practice, not just on the datasheet.
4. Test signal quality against 2–3 representative target surfaces to ground-truth §2's assumptions.

---

*Part of the [laser radius detailed study](README.md). Docs-only — no firmware or PCB changes.*
