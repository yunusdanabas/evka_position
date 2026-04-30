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
| `bill_of_materials.md` | Complete BOM, ~50 distinct line items, ~80 parts |
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
8. **GPIO12 pull-down on Schmitt OUTPUT side** — 10kΩ between 74HC14N pin 8 and GND, on the trace to GPIO12; corrects the misplaced divider-side pull-down from the first draft (the inverter sits between input and GPIO, so an input-side pull-down does nothing for boot safety)
9. **GPIO36 ADC bypass** — 100nF ceramic at ADC input; reduces battery voltage measurement noise
10. **LPKF fiducial marks** — 3× corner copper dots; improves flip-and-drill alignment from ±0.2mm to ±0.05mm

### Added in 2026-04-30 review pass

11. **USB-C CC1/CC2 termination (5.1kΩ Rd × 2)** — without these the connector advertises "no device" and a compliant USB-C charger never asserts VBUS; was missing from the first v2 draft
12. **Input ESD protection (SMAJ5.0A × 2)** — one TVS each on USB-C VBUS and barrel-jack VIN+, *before* the OR-ing Schottky diodes, to shunt connector-side hot-plug / ESD transients
13. **Pi filter on 5V_RAIL (10µH + 10µF + 220µF)** — attenuates MT3608's 1.2 MHz switching noise by ~58 dB; protects encoder analog front-end from shared-supply ripple
14. **Encoder signal TVS swap (1.5KE3.3CA → 1.5KE3.9CA)** — the 3.3CA's 2.82V standoff sat below the 3.33V divider HIGH, causing leakage sag at the threshold; 3.9CA's 3.34V standoff fixes it
15. **3.0mm trace width on V_EXT_RAW / V_EXT_PROT** — these carry up to 1.5A (1A charge + 0.5A run); 2.0mm at 18µm copper is only good for 1.3A
16. **SOT-23 / SOT-23-6 pad expansion** — 0.7×0.9mm and 0.6×0.8mm pads (vs library default 0.55×0.65mm) for cleaner LPKF milling and easier hand soldering with no soldermask
17. **74HC14N pin table rewritten with explicit DIP pin numbers** — the original ASCII box was ambiguous about which physical pin each input/output sat on (a wiring error there would land a signal on pin 7, GND, and destroy the IC)

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
- **SMD ICs:** LTC4412 and AO3401 are SOT-23/SOT-23-6 — use fresh isolation bits, 0.3mm pad clearance with 3 milling passes, expand pads to 0.6×0.8mm (SOT-23-6) and 0.7×0.9mm (SOT-23) for hand-solder margin
- **Input ESD TVS (SMAJ5.0A):** SMA package, surface-mount on the THT-otherwise board; one each at the J_USB VBUS pin and J4 VIN+ pin, *before* the OR Schottkys
- **No soldermask** on LPKF boards — tin power traces immediately after milling to prevent oxidation
- **Fiducials:** 3× corner pads, 0.5mm copper, no drill — add before running CircuitPro flip workflow
