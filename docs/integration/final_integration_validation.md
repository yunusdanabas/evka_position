# v4 Prototype Integration Validation

This checklist defines evidence required to close the current prototype handoff. Nothing in this
file records a test as completed. The final documentation reconciliation ran no hardware checks.

## Software Baseline

- [ ] Record the final tagged commit/hash after local release preparation.
- [x] Build all 10 configured PlatformIO environments.
- [x] Run the full Python test suite headlessly (two invocations): 204 passed.
- [x] Run the embedded dashboard harness: 50 checks passed.
- [x] Run compileall and the IPT solver self-check.

Software-only verification date: 2026-08-12. No firmware upload, serial session, or hardware command
was run. The PlatformIO matrix covered `wemos_d1_r32`, both v4 RGB variants, both remote variants,
and all five classic test environments.

The `test_*` environments are classic-pin sketches and must not be flashed to v4.

## Physical Interface Gate

- [ ] Verify J1 continuity/polarity: `1=A, 2=GND, 3=B, 4=+5V`.
- [ ] Verify J2 continuity/polarity: `1=+5V, 2=A, 3=GND, 4=B`.
- [ ] Verify J3 continuity/polarity: `1=A, 2=GND, 3=B, 4=+5V`.
- [ ] Verify encoder cable colors against the actual sensor cables.
- [ ] Record the board revision and DevKit RGB LED GPIO.
- [ ] Verify battery ADC scaling only if battery operation is in scope.

The connector mapping is PCB-derived and was not physically reverified in the final docs pass.

## Theta Blocking Gate

- [ ] Reproduce and record zero-relative `RAW_COUNTS` at home and repeated marked points.
- [ ] Resolve coupling slip, backlash, connector, divider, grounding, or signal-integrity faults.
- [ ] Demonstrate stable theta return in both directions and at representative speeds.
- [ ] Confirm radius and phi remain stable during theta motion.

Current evidence shows up to about 1.1 degrees theta return error. Do not proceed to endpoint
acceptance while this gate fails.

## Encoder Scale Gate

- [ ] Complete draw-wire multi-distance extend/retract trials.
- [ ] Complete theta and phi multi-turn CW/CCW trials.
- [ ] Meet spread and hysteresis criteria in [../calibration/calibration_guide.md](../calibration/calibration_guide.md).
- [ ] Record runtime `CONSTANTS`, NVS state, accepted values, operator, and date.

## Telemetry and Control Gate

- [ ] Confirm Serial and WebSocket `DATA,...` schemas at the expected cadence.
- [ ] Confirm TCP emits paired `X...` and `SENSOR,...` lines, not regular `DATA,...`.
- [ ] Confirm `PING`, zero commands, `STATUS`, `CONSTANTS`, and zero-relative `RAW_COUNTS`.
- [ ] Confirm reconnect behavior and required asynchronous remote/saved-point events.
- [ ] Compare observations with [../PROTOCOL.md](../PROTOCOL.md); record source deviations.

Use `tools/evka_gui` as the canonical client. Its output is sensor-frame-only.

## Endpoint/World Gate

- [ ] Collect well-spread calibration pairs only after mechanical and scale gates pass.
- [ ] Keep independent hold-out points.
- [ ] Pass calibration RMSE <= 10 mm and hold-out maximum error <= 15 mm.
- [ ] Archive the report and candidate JSON.
- [ ] Record explicit transform acceptance and the application that will consume it.

No shared/default calibration JSON is checked in or accepted. A passing session JSON may be supplied
explicitly to the legacy visualizer, but doing so is not acceptance and does not change `evka_gui`
to a world frame.

## Security, Endurance, and Legal Gate

- [ ] Use an isolated trusted lab network for all tests.
- [ ] Validate required AP/STA/TCP/WebSocket endurance and client count.
- [ ] Confirm fixed credentials and unauthenticated state-changing commands are acceptable only for
  the prototype environment.
- [ ] Resolve ownership and choose a redistribution license before any public release.
- [x] Historical vendor C# material deleted while required TCP compatibility remains documented.

## Sign-Off

- [ ] Hardware evidence attached.
- [ ] Calibration and hold-out evidence attached.
- [ ] Open deviations documented.
- [ ] Prototype acceptance decision recorded.
- [ ] No production/public redistribution claim made without separate legal and engineering approval.
