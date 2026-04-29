# 5V PCB v2 — Improved Design for LPKF S63

**Status:** Design complete, pending fabrication  
**Substrate:** FR4, 120×80mm, 2-layer  
**Milling:** LPKF S63 mechanical PCB milling  
**MCU:** ESP32 Wemos D1 R32 (unchanged)  
**Battery:** 1S LiPo 2000mAh, onboard 1A charging

This is the improved successor to `docs/hardware_design/5v/`. All core functionality is preserved while addressing LPKF S63 manufacturability, power rail quality, signal integrity, and input flexibility.

## Documents

| File | Content |
|---|---|
| `circuit_schematic.md` | Full ASCII schematic — all subsystems |
| `bill_of_materials.md` | Complete BOM, ~35 line items |
| `pcb_layout_guide.md` | Zone layout, trace widths, FR4/LPKF rules, assembly sequence |

Full design spec: `docs/superpowers/specs/2026-04-29-5v-pcb-v2-design.md`

## Key Improvements Over 5v/

1. **FR4 substrate** — replaces pertinax; better copper adhesion, cleaner LPKF milled edges, 0.4mm isolation clearance (vs 0.5mm for pertinax)
2. **LTC4412 ideal diode** — replaces Schottky OR on external power path; only 20mV drop vs 350mV; `5V_RAIL` stays at 4.98V instead of 4.65V when on external power
3. **Dual 5V input** — USB-C THT + barrel jack 5.5/2.1mm, Schottky OR; run from any USB phone charger or bench supply
4. **AO3401 RPP MOSFET** — replaces SI2301 (hard to solder on LPKF); same SOT-23 package, −4A rated vs −3A, identical sourcing with LTC4412 switch
5. **74HC14N Schmitt trigger** — DIP-14, buffers all 6 encoder signal lines; resharpens edges degraded by cable capacitance and RC filter; genuine hysteresis removes GPIO threshold ambiguity
6. **10nF signal filter caps** — replaces 1nF; 74HC14N resharpens so RC corner can be lowered from 23.9kHz to 2.38kHz for better noise rejection
7. **MT3608 fixed output** — trim pot removed from module; 100kΩ/300kΩ resistor divider sets 5.0V precisely; eliminates vibration-induced output drift
8. **GPIO12 pull-down** — 10kΩ on Theta B divider node; prevents ESP32 boot failure if strapping pin sees a HIGH during power-on
9. **GPIO36 ADC bypass** — 100nF ceramic at ADC input; reduces battery voltage measurement noise
10. **LPKF fiducial marks** — 3× corner copper dots; improves flip-and-drill alignment from ±0.2mm to ±0.05mm

## Firmware Change Required

In `firmware/src/SphericalSensor.cpp` `begin()`, swap A/B pin order for all three encoders to compensate for 74HC14N signal inversion:
```cpp
// Before (original):
enc_theta = new Encoder(PIN_THETA_A, PIN_THETA_B);
enc_phi   = new Encoder(PIN_PHI_A,   PIN_PHI_B);
enc_wire  = new Encoder(PIN_WIRE_A,  PIN_WIRE_B);

// After (5v_v2 with 74HC14N):
enc_theta = new Encoder(PIN_THETA_B, PIN_THETA_A);
enc_phi   = new Encoder(PIN_PHI_B,   PIN_PHI_A);
enc_wire  = new Encoder(PIN_WIRE_B,  PIN_WIRE_A);
```

## Manufacturing Notes

- **Machine:** LPKF S63 (flip-and-drill for 2-layer)
- **Material:** FR4 1.55mm, 18µm (0.5oz) copper — use derated current tables (0.6× standard 35µm)
- **Vias:** Wire-link (tinned wire through 0.8mm hole, solder both sides, flush-cut)
- **SMD ICs:** LTC4412 and AO3401 are SOT-23/SOT-23-6 — use fresh isolation bits, 0.4mm clearance, careful solder paste application
- **No soldermask** on LPKF boards — tin power traces immediately after milling to prevent oxidation
- **Fiducials:** 3× corner pads, 0.5mm copper, no drill — add before running CircuitPro flip workflow
