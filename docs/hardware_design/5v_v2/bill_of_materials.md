# Bill of Materials — 5V PCB v2

FR4, 120×80mm, LPKF S63. Approximately 41 line items (after the 2026-04-30 review pass).

---

## Power Section

| RefDes | Part | Value / Description | Package | Qty | LCSC / Note |
|---|---|---|---|---|---|
| J4 | DC Barrel Jack | 5.5×2.1mm, center positive, PCB-mount | THT | 1 | Standard type |
| J_USB | USB-C Female THT | VBUS + CC1 + CC2 + GND — HRO TYPE-C-31-M-12 or equiv | THT | 1 | LCSC: C165948 |
| R_CC1 | 5.1kΩ | 1% 1/4W metal film — USB-C CC1 pulldown (Rd) to GND | THT | 1 | LCSC: C57450 — **mandatory** for USB-C source detection |
| R_CC2 | 5.1kΩ | 1% 1/4W metal film — USB-C CC2 pulldown (Rd) to GND | THT | 1 | same as R_CC1 |
| TVS_USB | SMAJ5.0A | Unidirectional 5V TVS, 400W — USB-C VBUS input ESD | DO-214AC (SMA) | 1 | LCSC: C134518 |
| TVS_BAR | SMAJ5.0A | Unidirectional 5V TVS, 400W — barrel jack input ESD | DO-214AC (SMA) | 1 | same as TVS_USB |
| D_BAR | SS34 | 40V 3A Schottky diode — barrel jack OR | DO-201 | 1 | LCSC: C8678 |
| D_USB | SS34 | 40V 3A Schottky diode — USB-C OR | DO-201 | 1 | same as D_BAR |
| Q_RPP | AO3401 | P-ch MOSFET, -4A, -30V, Rds(on)=0.069Ω — reverse polarity protection | SOT-23 | 1 | LCSC: C15127 |
| Q_SWITCH | AO3401 | P-ch MOSFET, -4A, -30V — LTC4412 power switch | SOT-23 | 1 | same as Q_RPP |
| U_IDEAL | LTC4412 | Ideal diode controller, SOT-23-6 | SOT-23-6 | 1 | Analog Devices; LCSC: C515726 |
| R_RPP | 100kΩ | 1/4W metal film — Q_RPP gate pull-down to GND | THT | 1 | |
| R_GATE | 100kΩ | 1/4W metal film — Q_SWITCH gate pull-up to V_EXT_PROT | THT | 1 | |
| C_LTC | 100nF | 50V ceramic — LTC4412 VIN bypass | THT 5mm | 1 | |
| L1 | 10µH | Power inductor, Isat ≥ 1A — pi filter on 5V_RAIL (MT3608 ripple suppression) | THT axial | 1 | Bourns RLB0914-100KL or equiv.; LCSC: C1048270 |
| C_PI | 10µF/10V | Electrolytic — pre-L1 cap of pi filter | THT radial | 1 | |
| C1 | 220µF/10V | Electrolytic — post-L1 5V_RAIL bulk, ground star point | THT radial | 1 | |
| C2 | 100nF | 50V ceramic — 5V_RAIL bypass | THT 5mm | 1 | |
| LED1 | Green LED | Power on indicator | THT 5mm | 1 | |
| R_LED1 | 1kΩ | 1/4W — LED1 current limit | THT | 1 | |
| J6 | KF128V-3.5mm | 2-pin screw terminal — test/bench 5V input | THT | 1 | |

---

## Battery & Charging Section

| RefDes | Part | Value / Description | Package | Qty | LCSC / Note |
|---|---|---|---|---|---|
| MOD_TP4056 | TP4056+DW01A module | 1S LiPo charger + protection, micro-USB or bare pads, 1.2kΩ PROG for 1A | Module on headers | 1 | Verify RPROG = 1.2kΩ for 1A; replace if module uses different value |
| MOD_MT3608 | MT3608 boost module | 3.7V→5.0V fixed (trim pot removed, see modification procedure) | Module on headers | 1 | Buy adjustable and modify, OR source fixed-output 5.0V variant |
| R_MT_HI | 300kΩ | 1% 1/4W metal film — MT3608 FB upper resistor (VOUT to FB) | THT | 1 | Solder onto MT3608 module FB pin pads |
| R_MT_LO | 100kΩ | 1% 1/4W metal film — MT3608 FB lower resistor (FB to GND) | THT | 1 | Solder onto MT3608 module FB pin pads |
| D_BOOST | SS34 | 40V 3A Schottky — MT3608 output to 5V_RAIL | DO-201 | 1 | same family as D_BAR/D_USB |
| C_BOOST | 22µF/10V | Electrolytic — MT3608 output hold-up | THT radial | 1 | |
| J5 | JST-PH 2-pin | LiPo connector (red=BAT+, black=BAT−) | THT | 1 | Match polarity to LiPo cable |
| BAT1 | 1S LiPo 2000mAh | 3.7V nominal, JST-PH 2-pin, 2C discharge min (4A) | Cell | 1 | Not on PCB; connect via J5 |
| R_MON1 | 100kΩ | 1% 1/4W — battery ADC divider upper | THT | 1 | |
| R_MON2 | 100kΩ | 1% 1/4W — battery ADC divider lower | THT | 1 | |
| C_ADC | 100nF | 50V ceramic — GPIO36 ADC noise bypass | THT 5mm | 1 | |
| LED2 | Red LED | Battery low indicator (GPIO25 driven) | THT 5mm | 1 | |
| R_LED2 | 1kΩ | 1/4W — LED2 current limit | THT | 1 | |

---

## Signal Conditioning Section (×7 channels)

| RefDes | Part | Value / Description | Package | Qty | Note |
|---|---|---|---|---|---|
| R_TOP × 7 | 10kΩ | 1% 1/4W metal film — divider upper | THT | 7 | One per encoder signal line |
| R_BOT × 7 | 20kΩ | 1% 1/4W metal film — divider lower | THT | 7 | One per encoder signal line |
| C_FILT × 7 | 10nF C0G/NP0 | 50V ceramic — RC filter (2.38kHz corner) | THT 5mm | 7 | C0G/NP0 type required (not X5R/X7R) |
| TVS × 7 | 1.5KE3.9CA | Vrwm 3.34V, 1500W, bidirectional — ESD clamp; standoff above 3.33V divider HIGH avoids leakage sag | DO-201 | 7 | LCSC: C17166 (Littelfuse) — **swapped from 1.5KE3.3CA after 2026-04-30 review** |
| FB1, FB2, FB3 | Ferrite bead | 600Ω@100MHz, axial through-hole | THT axial | 3 | One per encoder VCC feed |
| C_VCC × 3 | 100nF | 50V ceramic — encoder VCC bypass at connector | THT 5mm | 3 | One per encoder connector |
| U_SCHM | 74HC14N | Hex Schmitt trigger inverter, 3.3V supply | DIP-14 | 1 | Texas Instruments or Nexperia; LCSC: C2688 |
| R_GPIO12 | 10kΩ | 1/4W — pull-down on GPIO12 (74HC14N pin 8 output → GPIO12 → R_GPIO12 → GND) | THT | 1 | Boot safety; **place on Schmitt OUTPUT side**, not the divider input — see schematic Section 5 |

---

## MCU + Connectors Section

| RefDes | Part | Value / Description | Package | Qty | Note |
|---|---|---|---|---|---|
| U1 | ESP32 Wemos D1 R32 | ESP32-WROOM-32, 4MB flash, onboard AMS1117-3.3 | Module | 1 | Socket-mounted |
| U1 socket | Female pin header 1×15 | 2.54mm pitch — ESP32 left side | THT | 1 | |
| U1 socket | Female pin header 1×19 | 2.54mm pitch — ESP32 right side | THT | 1 | |
| J1 | KF301-4P | 5.0mm pitch, 4-pin screw terminal — Theta encoder (GND/VCC/A/B) | THT | 1 | |
| J2 | KF301-4P | 5.0mm pitch, 4-pin screw terminal — Phi encoder (GND/VCC/A/B) | THT | 1 | |
| J3 | KF301-5P | 5.0mm pitch, 5-pin screw terminal — Wire encoder (GND/VCC/A/B/Z) | THT | 1 | |
| SW_RESET | Tactile button | 6×6mm momentary, normally open — ESP32 reset | THT | 1 | |
| TP1–TP5 | Test point pins | 1.0mm tinned pin — 5V_RAIL, 3.3V, MT3608 out, LiPo, GND | THT | 5 | |

---

## Summary

| Category | Distinct line items | Total parts |
|---|---|---|
| Power section | 20 | 20 |
| Battery & charging | 13 | 13 |
| Signal conditioning | 9 | 36 (7× R_TOP + 7× R_BOT + 7× C_FILT + 7× TVS + 3× FB + 3× C_VCC + 1× 74HC14N + 1× R_GPIO12) |
| MCU & connectors | 8 | 11 |
| **Total** | **~50 line items** | **~80 parts** |

**New vs 5v/ BOM:**
- Added: LTC4412, AO3401 × 2, 74HC14N, USB-C connector, D_USB, D_BAR, C_ADC, C_LTC, R_GATE, R_RPP, R_GPIO12, R_MT_HI, R_MT_LO, C_FILT change (×7, 1nF → 10nF)
- Added in 2026-04-30 review: R_CC1, R_CC2 (USB-C Rd termination), TVS_USB, TVS_BAR (input ESD), L1 + C_PI (pi filter on 5V_RAIL)
- Swapped in 2026-04-30 review: TVS ×7 from 1.5KE3.3CA → 1.5KE3.9CA (avoid standoff leakage)
- Removed: SI2301, 1N5817 RPP diode, original D1/D2 Schottky OR pair (repurposed as D_BAR + D_BOOST + D_USB)
- Substrate change: pertinax → FR4 (procurement, not BOM item)

---

## MT3608 Module Fixed-Output Modification Procedure

1. Identify the FB pin, trimpot (typically 100kΩ or 200kΩ), and resistor divider on the module
2. Remove trim pot and both existing FB resistors using solder wick or hot air
3. Solder R_MT_HI (300kΩ) between the VOUT net and the FB pin
4. Solder R_MT_LO (100kΩ) between the FB pin and GND
5. Connect 5V to MT3608 IN; measure output on MT3608 OUT: target 5.0V ±0.05V unloaded
6. Load test: connect 12Ω/2W (415mA load); verify output stays at 5.0V ±0.1V
7. Mark module "5.0V FIXED" with permanent marker
8. This is the only module modification required before board assembly

---

## Sourcing Notes

All THT components available from standard electronics distributors (Mouser, DigiKey, LCSC).  
AO3401 and LTC4412 in SOT-23/SOT-23-6 are widely available; buy 5× of each for hand-soldering spares.  
74HC14N in DIP-14 is available from TI (SN74HC14N), Nexperia (74HC14N,652), or Toshiba.  
USB-C THT connector: search LCSC for "USB-C through hole female" or use HRO TYPE-C-31-M-12.  
TP4056 module and MT3608 module: available from LCSC or AliExpress; verify charge current resistor value.
