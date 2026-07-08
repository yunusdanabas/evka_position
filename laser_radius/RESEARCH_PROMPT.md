# Claude Research Prompt — Laser Radius Variant

Copy everything below the line into Claude (with repo access). All outputs go under **`laser_radius/` at the repo root** — not under `docs/research/`.

---

You are researching a hardware variant for the **evka_position** project (ESP32 spherical 3D positioning: θ, φ from rotary encoders, r from distance sensor).

## Read first

- `laser_radius/README.md` — scope, open questions, Version A/B summary
- `docs/hardware_design/system_architecture.md` — current kinematics and accuracy baseline
- `docs/hardware_design/12v_legacy/v2/pin_assignment_v2.md` — ESP32-S3 GPIO plan

## Goal

Expand the brief laser-radius research into a **detailed study**. Do **not** change firmware or PCB files. Create separate markdown files under:

```
laser_radius/
```

## Required outputs

Create all of the following (add others only if clearly useful):

| File | Content |
|------|---------|
| `version_a_handheld_devices.md` | Wired-serial laser shortlist (3–5 devices), protocol notes, update rate, Turkey/LCSC/AliExpress availability; Bosch PLR 40 C as BLE fallback; explain why UNI-T LM50A is unsuitable |
| `version_b_integrated_modules.md` | Industrial ToF modules (TF02-i-RS485 + alternatives), accuracy vs range trade-offs, Modbus/CAN wiring to ESP32-S3 RS-485 (GPIO 13/14/18) |
| `kinematics_and_calibration.md` | Laser-on-phi-head geometry, spherical origin offset correction, calibration workflow replacing `CAL_W` |
| `firmware_integration.md` | ESP32-S3 interface options, 20 Hz loop feasibility, BLE+WiFi coexistence for Version A, sketch `LaserRadiusSensor` API |
| `procurement_and_bom.md` | Rough costs, suppliers, recommended bench-test order list |

Update `laser_radius/README.md` folder index when files are complete. Add an executive summary + Version A vs B recommendation at the top of README (keep existing brief content below or merge cleanly).

## Fixed design decisions

Do not re-litigate unless you find a hard blocker:

- Two rotary encoders for azimuth/elevation; **laser replaces draw-wire** for r
- Laser mounted on **phi head**, pointing at target along boom
- MCU: **ESP32-S3 DevKitC-1** (EVKA_position_v2 direction)
- Version A: **wired serial preferred**; BLE handheld acceptable as fallback
- Range/accuracy requirements: **still TBD** — propose 2–3 requirement tiers and map devices to each

## Per-device documentation

For each candidate, include: range, accuracy, interface, protocol/command example, max sample rate, laser class, power, price ballpark, pros/cons for this application.

## Baseline comparison

Compare against current draw-wire system (~0–3 m typical reach, ~±3 mm combined XYZ at 5 m).

## Closing requirements

- End each file with **open risks** and **next physical test steps**
- Log work in `AGENTS.md` Activity Log when done
