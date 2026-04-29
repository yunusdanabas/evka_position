# Design Spec: 5V PCB v2 — Improved Design for LPKF S63

**Date:** 2026-04-29  
**Board:** 120×80mm, 2-layer, FR4, LPKF S63 mechanical milling  
**MCU:** ESP32 Wemos D1 R32 (unchanged)  
**Battery:** 1S LiPo 2000mAh, onboard charging

## Context

The project switched from 12V back to the 5V design. The existing `docs/hardware_design/5v/` describes the original pertinax board. This v2 design improves power switching, signal integrity, substrate, and input options for production on the LPKF S63 milling machine.

## Key Changes from 5v/

| Item | Before | After |
|---|---|---|
| Power switching | Schottky OR (0.35V drop) | LTC4412 ideal diode (20mV drop) |
| RPP MOSFET | SI2301 SOT-23 (hard on LPKF) | AO3401 SOT-23 (same package as LTC4412, 4A) |
| 5V input | Barrel jack only | Barrel jack + USB-C (Schottky OR) |
| Signal buffering | None (direct to GPIO) | 74HC14N Schmitt trigger DIP-14 |
| Filter caps | 1nF (RC corner 23.9kHz) | 10nF (RC corner 2.4kHz, Schmitt resharpens) |
| MT3608 output | Trimpot (vibration drift) | Fixed 100kΩ/300kΩ divider (5.0V) |
| GPIO12 pull-down | None | 10kΩ on divider node (strapping pin safety) |
| GPIO36 ADC bypass | None | 100nF ceramic |
| PCB substrate | Pertinax (FR2) | FR4 (better adhesion, cleaner milled edges) |
| LPKF registration | Board edge only | 3× corner fiducial marks (±0.05mm) |

## Electrical Architecture

### Power Input
- **J4**: DC barrel jack 5.5/2.1mm (center positive)
- **J_USB**: THT USB-C female (HRO TYPE-C-31-M-12 or equivalent, VBUS + GND only)
- **D_BAR**: SS34 DO-201 axial Schottky — barrel jack OR diode
- **D_USB**: SS34 DO-201 axial Schottky — USB-C OR diode
- Both OR onto `V_EXT_RAW`

### Reverse Polarity Protection
- **Q_RPP**: AO3401 SOT-23 P-channel MOSFET (Id = −4A, Vds = −30V, Rds(on) = 0.069Ω)
  - Source → `V_EXT_RAW`, Drain → `V_EXT_PROT`, Gate → GND via R_RPP (100kΩ)
  - Correct polarity: Vgs = −5V → FET ON → 35mV drop at 500mA
  - Reversed polarity: Vgs = +5V → FET OFF → no current

### System Power Switching (LTC4412 Ideal Diode)
- **LTC4412** (SOT-23-6) + **Q_SWITCH** AO3401 (SOT-23)
  - LTC4412 pin2 (VIN) = `V_EXT_PROT`
  - LTC4412 pin1 (GATE) → Q_SWITCH gate
  - LTC4412 pin4 (SENSE) = `5V_RAIL` (Q_SWITCH drain)
  - LTC4412 pin5 (SHDN) → GND (always enabled)
  - LTC4412 pin3 (GND) → GND; pin6 (PFO) floating
  - Q_SWITCH: source = `V_EXT_PROT`, drain = `5V_RAIL`
  - R_GATE (100kΩ): Q_SWITCH gate to `V_EXT_PROT` (ensures FET off if LTC4412 unpowered)
  - C_LTC (100nF): LTC4412 VIN bypass to GND
- When external present: Q_SWITCH ON → `5V_RAIL` = 4.98V; D_BOOST reverse-biased → battery off
- When external absent: Q_SWITCH off; MT3608/D_BOOST path → `5V_RAIL` = 4.65V

### Charging Path
- `V_EXT_PROT` → TP4056 module IN (1A charge, RPROG = 1.2kΩ on module)
- TP4056 BAT+ → DW01A+FS8205 protection → **J5** JST-PH 2-pin → 1S LiPo 2000mAh
- TP4056 provides: 4.2V overcharge cutoff, ~2.5V overdischarge via DW01A, short-circuit protection

### Battery/Boost Path
- LiPo → DW01A → MT3608 module IN
- MT3608 boost → fixed 5.0V: **R_MT_HI = 300kΩ** (VOUT→FB), **R_MT_LO = 100kΩ** (FB→GND)
  - Vout = 1.25 × (1 + 300/100) = 5.0V (trim pot removed from module)
- MT3608 OUT → **D_BOOST** SS34 Schottky → `5V_RAIL`
- C_BOOST: 22µF electrolytic on MT3608 output

### 5V_RAIL Distribution
- C1: 220µF/10V electrolytic (bulk, ground star point)
- C2: 100nF ceramic
- Feeds: ESP32 Wemos D1 R32 (5V pin), J1/J2/J3 encoder VCC

### Battery Voltage Monitor
- LiPo BAT+ → R_MON1 (100kΩ) → GPIO36 (ADC1_CH0) → R_MON2 (100kΩ) → GND
- C_ADC: 100nF from GPIO36 node to GND
- At 4.2V: ADC = 2.10V; at 3.0V: ADC = 1.50V (linear range of ESP32 ADC with 11dB attenuation)

### Signal Conditioning (7 channels: Theta A/B, Phi A/B, Wire A/B/Z)
Per channel:
1. Encoder 0–5V TTL → R_TOP (10kΩ) → divider node → R_BOT (20kΩ) → GND  
   Output: 3.33V @ 5V in, 0V @ 0V in. Source impedance: 6.67kΩ
2. C_FILT (10nF C0G) — RC corner 2.38kHz; Schmitt trigger resharpens slow edges
3. TVS (1.5KE3.3CA DO-201) — clamps at 3.3V, bidirectional ESD protection
4. **74HC14N** Schmitt trigger (VCC = 3.3V from ESP32; VIH = 1.98V, VIL = 1.32V)
   - All 6 encoder lines use one DIP-14 IC
   - Output is inverted; fix in firmware (see Firmware Notes)
5. 74HC14N output → ESP32 GPIO

- **GPIO12 pull-down**: 10kΩ from Theta B divider node to GND (boot strapping pin safety)

### 74HC14N Pin Map (DIP-14, VCC=pin14 @ 3.3V, GND=pin7)
| 74HC14N In | Signal | 74HC14N Out | GPIO |
|---|---|---|---|
| Pin 1 (1A) | Theta A divider | Pin 2 (1Y) | GPIO14 |
| Pin 3 (2A) | Theta B divider | Pin 4 (2Y) | GPIO12 |
| Pin 5 (3A) | Phi A divider | Pin 6 (3Y) | GPIO32 |
| Pin 9 (4A) | Phi B divider | Pin 8 (4Y) | GPIO35 |
| Pin 11 (5A) | Wire A divider | Pin 10 (5Y) | GPIO16 |
| Pin 13 (6A) | Wire B divider | Pin 12 (6Y) | GPIO17 |
| 100nF bypass | pin14 to pin7 | | |

### Encoder VCC Filtering
- 3× ferrite beads 600Ω@100MHz axial on encoder VCC lines (J1, J2, J3)
- 3× 100nF ceramic bypass at each encoder connector VCC pin

### Indicators
- LED1 green: 5V_RAIL via 1kΩ to GND (power on)
- LED2 red: GPIO25 via 1kΩ to GND (battery low, firmware-driven)

## Pin Map (unchanged from firmware)
| GPIO | Signal |
|---|---|
| 14 | Theta A (via 74HC14N) |
| 12 | Theta B (via 74HC14N) + 10kΩ pull-down |
| 32 | Phi A (via 74HC14N) |
| 35 | Phi B (via 74HC14N) |
| 16 | Wire A (via 74HC14N) |
| 17 | Wire B (via 74HC14N) |
| 36 | Battery ADC |
| 25 | Battery low LED |

## Firmware Notes

One change required in `firmware/src/SphericalSensor.cpp` `begin()`:
- 74HC14N inverts all encoder signals → encoder counts in reverse direction
- Fix: swap A/B pin arguments in all three `Encoder` constructors:
  `new Encoder(PIN_THETA_A, PIN_THETA_B)` → `new Encoder(PIN_THETA_B, PIN_THETA_A)`
  Apply to theta, phi, and wire encoders

## PCB Design Rules (FR4, LPKF S63)

| Parameter | Value |
|---|---|
| Substrate | FR4, 1.55mm, 18µm (0.5oz) copper |
| Board size | 120×80mm |
| Layers | 2 (top: signal+power, bottom: ground pour) |
| Min trace width — signal | 0.8mm |
| Min trace width — power | 1.5mm |
| Min trace width — 5V_RAIL, battery | 2.0mm |
| Min isolation clearance | 0.4mm |
| Ground pour clearance | 0.4mm |
| Via drill | 0.8mm, pad 2.0mm |
| Via method | Wire-link (tinned wire, solder both sides) |
| Component holes | 1.0mm standard, 1.2mm for power connectors |
| Fiducials | 3× corner copper dots, 0.5mm, no drill |
| Current derate (18µm) | 0.6× IPC-2221 standard 35µm tables |

Current capacity at 18µm copper:
- 0.8mm: ~0.54A | 1.5mm: ~0.90A | 2.0mm: ~1.30A

## Zone Layout

See `docs/hardware_design/5v_v2/pcb_layout_guide.md` for full ASCII layout and assembly sequence.

Zones:
- **Zone A** (top-left): Power input, RPP, LTC4412, bulk caps, LEDs, test points
- **Zone B** (top-right): TP4056 module, DW01A, MT3608 module, LiPo connector, ADC monitor
- **Zone C** (bottom-left): Encoder connectors, signal conditioning networks, ferrite beads
- **Zone D** (bottom-right): 74HC14N, ESP32 socket, GPIO12 pull-down, ADC bypass, reset

## New BOM Items
| Ref | Part | Package | Change |
|---|---|---|---|
| Q_RPP | AO3401 | SOT-23 | Replaces SI2301 |
| Q_SWITCH | AO3401 | SOT-23 | New — LTC4412 switch |
| U_IDEAL | LTC4412 | SOT-23-6 | New |
| U_SCHM | 74HC14N | DIP-14 | New |
| J_USB | USB-C THT | THT | New |
| D_USB, D_BAR | SS34 | DO-201 | New (2 added) |
| C_FILT × 7 | 10nF C0G | THT 5mm | Replaces 1nF |
| C_ADC, C_LTC | 100nF | THT 5mm | New (2 added) |
| R_GATE, R_RPP | 100kΩ | THT | New (2 added) |
| R_GPIO12 | 10kΩ | THT | New |
| R_MT_HI | 300kΩ 1% | THT | New — MT3608 fixed output |
| R_MT_LO | 100kΩ 1% | THT | New — MT3608 fixed output |
