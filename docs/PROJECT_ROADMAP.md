# Prototype Completion Roadmap

This roadmap replaces older phase checklists that mixed software completion, historical board work,
and unperformed hardware acceptance. The current target is an evidence-backed v4 prototype handoff,
not a production release.

## Existing Baseline

- [x] Shared classic ESP32 / ESP32-S3 main firmware structure exists.
- [x] `esp32s3_v4` build environment and v4 GPIO mapping exist in source.
- [x] Main firmware uses ESP32 PCNT through `ESP32Encoder`.
- [x] Serial, WebSocket, and retained TCP telemetry implementations exist.
- [x] `tools/evka_gui` is the canonical Serial/TCP/WebSocket/replay GUI.
- [x] Quick IPT and calibration-report tooling exist in the repository.
- [x] A v4 carrier has been assembled and earlier work observed live telemetry.
- [x] Theta repeatability failure is documented.

These checkmarks describe repository or historical prototype facts. They are not current hardware
acceptance and were not reverified during this documentation reconciliation.

## Gate 1: Resolve Theta Count Loss

- [ ] Reproduce the loss using zero-relative `RAW_COUNTS` without re-zeroing between visits.
- [ ] Separate coupling slip/backlash from electrical count loss.
- [ ] Inspect coupler, shaft, connector, divider, grounding, and A/B signal integrity.
- [ ] Demonstrate repeatable return to home and repeated marked points.
- [ ] Record the test setup, raw counts, direction, speed, and error per visit.

Do not change PPR or fit a transform to conceal this defect.

## Gate 2: Physically Reverify v4 Interfaces

- [ ] Record continuity/polarity verification for J1: `1=A, 2=GND, 3=B, 4=+5V`.
- [ ] Record continuity/polarity verification for J2: `1=+5V, 2=A, 3=GND, 4=B`.
- [ ] Record continuity/polarity verification for J3: `1=A, 2=GND, 3=B, 4=+5V`.
- [ ] Confirm the actual DevKit RGB GPIO selection.
- [ ] Validate battery ADC scaling if the battery path is part of the intended prototype use.

The connector mapping above is PCB-derived and was not physically reverified in the final docs pass.

## Gate 3: Accept Encoder Scale

- [ ] Run multi-distance draw-wire extend/retract trials.
- [ ] Run theta and phi CW/CCW multi-turn trials after Gate 1 passes.
- [ ] Check trial spread and hysteresis against the active calibration criteria.
- [ ] Record runtime `CONSTANTS` and any NVS overrides.
- [ ] Create a dated calibration record with approved values.

## Gate 4: Fit and Accept a World Transform

- [ ] Collect well-spread sensor/world calibration pairs.
- [ ] Keep independent hold-out validation points.
- [ ] Generate a report with `python -m tools.calibration.report`.
- [ ] Pass calibration RMSE and validation maximum-error thresholds.
- [ ] Archive the evidence and explicitly approve the transform.
- [ ] Decide and implement how an accepted transform is consumed; current `evka_gui` remains
  sensor-frame-only.

No shared/default calibration JSON is checked in or accepted. A passing session JSON remains an
optional explicit input to the legacy visualizer only; `tools/evka_gui` stays sensor-frame-only.

## Gate 5: Full Prototype Validation

- [ ] Verify all three encoders together over the required range and motion profile.
- [ ] Validate hardware zero, per-axis zero, telemetry, saved-point, and reconnect behavior.
- [ ] Validate accuracy and repeatability at known positions.
- [ ] Run representative WiFi/TCP/WebSocket endurance and multi-client checks if required.
- [ ] Record battery and status-LED results if those features are required.
- [ ] Complete [integration/final_integration_validation.md](integration/final_integration_validation.md).

## Gate 6: Legal and Release Decision

- [ ] Resolve repository ownership and choose a redistribution license.
- [x] Historical vendor C# material deleted from the repository.
- [ ] Confirm retained TCP compatibility obligations.
- [ ] Review documentation against final measured hardware.
- [ ] Only then decide whether to create a release or make a production-readiness claim.

## Archive and Research

- `docs/hardware_design/12v_legacy/` is archived and not a current build direction.
- `docs/gui_unification/` and `docs/integration/CMD_INTEGRATION_CHANGELOG.md` are implementation
  history, not acceptance records.
- `laser_radius/` and `docs/research/` are research only and are not part of the current v4 baseline.
