# KiCad 5V PCB — Basic Steps *(post-procurement, 2026-05-08)*

Project: `pcb_design/EVKA_position_v2/EVKA_position_v2.kicad_pro`
Detailed reference: `KICAD_PLAN_DETAILED.md`
Schematic reference: `circuit_schematic.md` (read with the procurement deltas in the detailed plan)

---

## 0. Prep before opening KiCad

- Confirm all parts on hand (see Appendix A in detailed plan)
- Modify the MT3608 module: remove trim pot + FB resistors, solder R_MT_HI=300k and R_MT_LO=100k, calibrate to 5.00 V
- Mark the modified MT3608 module "5.0 V FIXED"

## 1. Open project in KiCad v9.0

Save a backup before any edits.

## 2. Add custom symbols (only what's missing)

- **ESP32-S3-DevKitC-1** (44-pin 2×22) — generic `Conn_02x22_Odd_Even` with renamed pins, OR community symbol
- All other parts use generic KiCad symbols (`Q_PMOS_GSD`, `D_Schottky`, `D_TVS`, `74HC14`, etc.)

## 3. Add custom footprints

- **KF301-2P / 4P** screw terminals (5.08 mm pitch, hole Ø 1.3 mm) — J6 = 2P, J1/J2/J3 = 4P (3P no longer used)
- **2.25 mm 2-pin female socket** for J5 — verify pitch with calipers when part arrives
- **TP4056 module** (6-pad THT) and **MT3608 module** (4-pad THT) — pad layouts per ordered modules
- **ESP32-S3-DevKitC-1** (2× rows of 22 holes, 22.86 mm row spacing, 63.5×25.4 mm board)

## 4. Draw schematic in Eeschema (5 blocks)

1. **Single 5V input** — J4 → TVS_BAR → D_BAR → V_EXT_RAW → Q_RPP (PJA3441) → V_EXT_PROT
2. **Schottky-OR + pi filter** — V_EXT_PROT → D_EXT ‖ MT3608→D_BOOST → PI_NODE → L1 → 5V_RAIL (no LTC4412)
3. **TP4056 charger + MT3608 boost** — battery path with J5 (2.25 mm female socket), R_MT_HI/LO already on the modified MT3608 module
4. **Encoder connectors + signal conditioning** — J1/J2/J3 (as-built Phoenix MKDS-1,5-4 5.0mm; KF301-4P pad-compatible; wire encoder Z unused), J_FB jumpers (0Ω wire link), 6× R_TOP/R_BOT/C_FILT dividers + 6× TVS (general THT, flexible axial footprint, **populated**, part TBD)
5. **74HC14 Schmitt + ESP32-S3-DevKitC-1** — encoder GPIOs on J1 pins 4–9, battery ADC on J3 pin 4 (GPIO1), onboard WS2812 RGB LED for battery indicator

## 5. Run ERC

Fix all errors. Tie unused Schmitt inputs to GND.

## 6. Switch to PCBnew — set board outline

- Rectangle: 120 × 80 mm
- 4× M3 mounting holes (3.2 mm drill, 3 mm inset from corners)
- 3× 0.5 mm copper fiducials at corners

## 7. Set design rules (LPKF S63)

- Min trace 0.5 mm; signal recommended 0.8 mm
- Power: V_EXT_RAW/PROT 3.0 mm, 5V_RAIL/BAT+ 2.0 mm, encoder VCC 1.5 mm
- Clearance 0.4 mm; vias 0.8 mm drill / 2.0 mm pad

## 8. Import netlist from schematic

Tools → Update PCB from Schematic.

## 9. Place components per zone

- **Zone A (top-left, 45×35 mm)** — barrel jack J4, TVS_BAR, D_BAR/EXT/BOOST, Q_RPP, L1, C_PI/C1/C2, LED1
- **Zone B (top-right, 65×35 mm)** — TP4056 + MT3608 modules, J5 (LiPo), battery divider
- **Zone C (bottom-left, 60×45 mm)** — J1/J2/J3 encoder connectors, J_FB jumpers, 6-channel divider network
- **Zone D (bottom-right, 70×30 mm)** — 74HC14 + ESP32-S3-DevKitC-1 socket, TP1–TP6, switch block (J_SW1, R_SW1/2, C_SW1/2) + AUX header (J_EXP1, R_AUX1–4) (USB-C connectors face the short edge of the PCB)

## 10. Route traces

Power first (widest), then signal traces. Encoder GPIOs are consecutive on J1 pins 4–9 → single straight bus.

## 11. Add GND copper pour on bottom

Clearance 0.4 mm. Add wire-link vias for isolated islands.

## 12. Run DRC

Target: 0 errors, 0 unrouted nets.

## 13. Export Gerbers + drill file

- F.Cu, B.Cu, F.SilkS, Edge.Cuts (Gerber X2, mm, 4.6 unit)
- Excellon drill file (mm, decimal zeros)
- Output to `pcb_design/EVKA_position_v2/gerbers/`
- Verify in KiCad Gerber Viewer before sending to LPKF S63

---

## Procurement deltas vs original BOM (carry-forward summary)

| Removed | Reason |
|---------|--------|
| J_USB + R_CC1 + R_CC2 + TVS_USB + D_USB | USB-C input dropped; DevKitC-1 has onboard USB-C |
| LTC4412 + Q_SWITCH + R_GATE + C_LTC | Replaced by passive Schottky-OR (D_EXT) |
| FB1/FB2/FB3 ferrite beads | Replaced by 0Ω wire jumpers |
| TVS×6 | **Populated** — general THT TVS, flexible axial footprint, part TBD/placeholder `D_TVS` (not the mis-ordered P6KE39CA) |
| SW_RESET | DevKitC-1 has onboard RST button |
| LED2 + R_LED2 | Replaced by onboard WS2812 RGB on GPIO38 |
| R_GPIO12 | ESP32-S3 strapping pins are 0/3/45/46, not 12 |

| Added / changed | |
|-----------------|---|
| Q_RPP: AO3401 → **PJA3441** (Panjit, drop-in SOT-23) |
| D_BAR/D_EXT/D_BOOST: SS34 (SMD) → **1N5822** (DO-201 axial) |
| L1: Bourns RLB0914 → generic 10 µH 1A radial |
| ESP32: Wemos D1 R32 → **ESP32-S3-DevKitC-1 N16R8** |
| J1/J2/J3/J6/J_SW1: as-built **Phoenix MKDS 5.0mm** (KF301 pad-compatible); wire J3 = single 4-pin, Z unused |
| J5: as-built **JST-PH 2.0 mm** (verify pitch with calipers) |
| Added (not in original plan): switch block **J_SW1 + R_SW1/2 + C_SW1/2** (BTN1=GPIO17, BTN2=GPIO18) and **AUX header J_EXP1 + R_AUX1–4** (→ GPIO11/12/13/14) |
