# Legacy 12V Hardware Designs (Archived)

This folder contains all 12V hardware design work that was explored before the project changed direction. These designs are **archived for reference** and are no longer the active development target.

## Contents

| Folder | Description |
|--------|-------------|
| [`12v/`](12v/) | Original 12V + 3S LiPo design (Wemos D1 R32, MP1584EN buck, TP5100 charging path) |
| [`12v_tht/`](12v_tht/) | All-through-hole variant of the original 12V design — easier hand soldering |
| [`v2/`](v2/) | ESP32-S3 industrial redesign (RS-485, I2C, MAX813L watchdog, DIN rail) |
| [`v3/`](v3/) | Simplified ESP32-S3 core-only 12V design (no onboard charging, external balance charge only) |
| [`final_design/`](final_design/) | Final selected 12V-only build package based on V3-A with `D_ADAPT` isolation |
| [`comparison/`](comparison/) | Full comparison of all hardware variants, decision guide, and Reveal.js presentation |

## Status

- **Not built or firmware-migrated** (V2, V3, Final Design require ESP32-S3 firmware port).
- **Not recommended for new builds** unless you are explicitly continuing the 12V direction.
- For the current active hardware, see `docs/hardware_design/5v/` and the firmware source of truth in `firmware/src/SphericalSensor.h`.

## Cross-References

All internal links and external documentation references (`AGENTS.md`, `CLAUDE.md`, `firmware/src/SphericalSensor.h`, etc.) have been updated to point to this `12v_legacy/` path.
