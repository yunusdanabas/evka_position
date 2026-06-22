# Bill of Materials — 5V PCB v2

> **As-built reconciliation (2026-06-13):** updated to match KICAD_PLAN_DETAILED.md Appendix A (post-procurement). Earlier revisions described the pre-procurement concept.

> This BOM now mirrors **`KICAD_PLAN_DETAILED.md` → Appendix A** (~32 line items, ~64 parts), which remains authoritative. The pre-procurement design dropped USB-C (J_USB, R_CC1/2, TVS_USB, D_USB), the LTC4412 ideal-diode path (U_IDEAL, Q_SWITCH, R_GATE, C_LTC), the ferrite beads (FB1/2/3), R_GPIO12, SW_RESET, LED2, and R_LED2; substituted PJA3441 for AO3401, 1N5822-HT for the mislabeled "SS34", and ESP32-S3-DevKitC-1 N16R8 for Wemos D1 R32; populates the 6× encoder TVS with a general THT part (flexible axial footprint, part TBD); and added a second 1N5822 (D_EXT) plus three 0Ω wire jumpers (J_FB1/2/3). See `README.md` for the change summary.

> **As-built reconciliation (2026-06-20):** verified against the hand-built master schematic (`Master Design/EvkaPosition_v2/`, 74 components, ERC 0/0). Corrected vs earlier doc: signal conditioning is **×6** channels, not ×7 (3 encoders × A/B = 6 lines, one per 74HC14 gate); encoder/bench terminal blocks are **Phoenix MKDS 5.0 mm** as drawn (KF301 is the pad-compatible alternative); **TP1–TP6** (TP6=GND added); and a **switch block** (J_SW1, BTN1=GPIO17, BTN2=GPIO18) plus a **2×6 AUX expansion header** (J_EXP1, R_AUX1–4 → GPIO11/12/13/14) are present — both documented below.

FR4, 120×80mm, LPKF S63. As-built: ~37 line items, ~85 parts (master schematic = 74 component refs).

---

## Power Section (input + Schottky-OR + pi filter)

| RefDes | Part | Value / Description | Package | Qty | Source / Note |
|---|---|---|---|---|---|
| J4 | DC Barrel Jack DC-005 | 5.5×2.1mm, center positive, PCB-mount, 3 legs (tip/sleeve/switch; switch unused) | THT | 1 | direnc.net — single 5V input (USB-C dropped). As-built footprint = `Connector_BarrelJack:BarrelJack_CUI_PJ-102AH_Horizontal` (round 1.6mm drills fit the Ø1.2mm round legs; verify 2.1mm plug seats) |
| TVS_BAR | SMAJ5.0A | Unidirectional 5V TVS, 400W — barrel jack input ESD | DO-214AC (SMA) | 1 | direnc.net / ozdisan |
| D_BAR | 1N5822-HT | 40V 3A Schottky — input diode | DO-201 axial | 1 | direnc.net (Hottech) |
| Q_RPP | PJA3441 | P-ch MOSFET, −40V, −3.1A, 74mΩ — reverse polarity protection | SOT-23 | 1 | direnc.net (Panjit) — drop-in for AO3401 |
| R_RPP | 100kΩ | 1/4W metal film — Q_RPP gate pull-down to GND | THT | 1 | |
| D_EXT | 1N5822-HT | 40V 3A Schottky — external path OR into PI_NODE | DO-201 axial | 1 | direnc.net |
| D_BOOST | 1N5822-HT | 40V 3A Schottky — battery (MT3608) path OR into PI_NODE | DO-201 axial | 1 | direnc.net |
| L1 | 10µH 1A radial | Power inductor, Isat ≥ 1A — pi filter on 5V_RAIL (MT3608 ripple suppression) | THT axial/radial | 1 | direnc.net (ABCO generic) |
| C_PI | 10µF/10V | Electrolytic — pre-L1 cap of pi filter | THT radial | 1 | |
| C1 | 220µF/10V | Electrolytic — post-L1 5V_RAIL bulk, ground star point | THT radial | 1 | |
| C2 | 100nF | 50V ceramic — 5V_RAIL bypass | THT 5mm | 1 | |
| LED1 | Green LED | Power on indicator | THT 5mm | 1 | |
| R_LED1 | 1kΩ | 1/4W — LED1 current limit | THT | 1 | |
| J6 | Phoenix MKDS-1,5-2 (5.0mm) | 2-pin screw terminal — test/bench 5V input | THT | 1 | As-built = MKDS 5.0mm; KF301-2P / KF128-5.0 pad-compatible |

> Removed from this section vs pre-procurement: **J_USB, R_CC1, R_CC2, TVS_USB, D_USB** (USB-C dropped); **U_IDEAL (LTC4412), Q_SWITCH, R_GATE, C_LTC** (ideal-diode path → passive Schottky-OR). D_BOOST moved here from the battery section since both OR diodes now feed PI_NODE.

---

## Battery & Charging Section

| RefDes | Part | Value / Description | Package | Qty | LCSC / Note |
|---|---|---|---|---|---|
| MOD_TP4056 | TP4056+DW01A+FS8205A module | 1S LiPo charger + protection, micro-USB/Type-C or bare pads, 1.2kΩ PROG for 1A | Module on headers | 1 | direnc.net / robotistan / robolinkmarket — verify RPROG = 1.2kΩ for 1A |
| MOD_MT3608 | MT3608 boost module (modified) | 3.7V→5.0V fixed (trim pot removed, see modification procedure) | Module on headers | 1 | direnc.net — buy adjustable and modify |
| R_MT_HI | 300kΩ | 1% 1/4W metal film — MT3608 FB upper resistor (VOUT to FB) | THT | 1 | Solder onto MT3608 module FB pin pads (on-module, not a board part) |
| R_MT_LO | 100kΩ | 1% 1/4W metal film — MT3608 FB lower resistor (FB to GND) | THT | 1 | Solder onto MT3608 module FB pin pads (on-module, not a board part) |
| C_BOOST | 22µF/10V | Electrolytic — MT3608 output hold-up | THT radial | 1 | |
| J5 | 2.25mm 2-pin female socket | LiPo connector (cable is male; red=BAT+, black=BAT−) | THT | 1 | direnc.net — verify pitch with calipers (may be 2.0/2.5mm) |
| BAT1 | 1S LiPo 2000mAh | 3.7V nominal, mating male connector, 2C discharge min (4A) | Cell | 1 | Not on PCB; connect via J5 |
| R_MON1 | 100kΩ | 1% 1/4W — battery ADC divider upper | THT | 1 | |
| R_MON2 | 100kΩ | 1% 1/4W — battery ADC divider lower | THT | 1 | |
| C_ADC | 100nF | 50V ceramic — GPIO1 (ADC1_CH0) ADC noise bypass | THT 5mm | 1 | |

> Removed from this section vs pre-procurement: **LED2, R_LED2** (battery-low indication now uses the onboard WS2812 RGB on GPIO38). **D_BOOST** relocated to the Power Section (Schottky-OR). Battery monitor ADC moved from GPIO36 (classic ESP32) to **GPIO1** (ESP32-S3, same ADC1_CH0).

---

## Signal Conditioning Section (×6 channels)

> As-built: **6 channels** = 3 encoders × (A, B). Each feeds one of the six 74HC14 Schmitt gates. (Earlier doc said ×7; there is no 7th line — the wire encoder's Z/index is unused.)

| RefDes | Part | Value / Description | Package | Qty | Note |
|---|---|---|---|---|---|
| R_TOP1–6 | 10kΩ | 1% 1/4W metal film — divider upper | THT | 6 | One per encoder signal line (A/B × 3) |
| R_BOT1–6 | 20kΩ | 1% 1/4W metal film — divider lower | THT | 6 | One per encoder signal line |
| C_FILT1–6 | 10nF C0G/NP0 | 50V ceramic — RC filter (2.38kHz corner) | THT 5mm | 6 | C0G/NP0 type preferred (not X5R/X7R) |
| TVS1–6 | General THT TVS (part TBD) | **Populate.** Flexible large-axial footprint (`D_DO-201AD_P15.24mm`); pick bidirectional V_RWM ≥ ~3.34V (1.5KE3.9CA ideal, import-only; on-hand 1.5KE3.3CA works but leaks slightly). Not the mis-ordered P6KE39CA (33V). **Schematic value still shows the `D_TVS` placeholder — set the real MPN.** | DO-201AD (flexible) | 6 | Solder a proper THT TVS; set exact value when chosen |
| J_FB1, J_FB2, J_FB3 | 0Ω wire jumper | Replaces ferrite bead — axial footprint, ferrite-ready | THT axial | 3 | tinned wire offcuts; one per encoder VCC feed |
| C_VCC × 3 | 100nF | 50V ceramic — encoder VCC bypass at connector | THT 5mm | 3 | One per encoder connector |
| U_SCHM | 74HC14 | Hex Schmitt trigger inverter, 3.3V supply | DIP-14 | 1 | any HC variant (TI / Nexperia / ON) |
| C_SCHM | 100nF | 50V ceramic — 74HC14 VCC decoupling (pin14↔pin7, within 5mm) | THT 5mm | 1 | **Recommended add** — standard practice, in original schematic but missing from Appendix A |

---

## MCU + Connectors Section

| RefDes | Part | Value / Description | Package | Qty | Note |
|---|---|---|---|---|---|
| U1 | ESP32-S3-DevKitC-1 N16R8 | ESP32-S3-WROOM-1, 16MB flash + 8MB PSRAM, dual onboard USB-C, onboard 3.3V LDO + WS2812 RGB | 2×22 hdr | 1 | direnc.net — socket-mounted, 22.86mm row spacing, 63.5×25.4mm board |
| U1 socket | Female pin header 1×22 | 2.54mm pitch — DevKitC-1 left socket (J1) | THT | 1 | cut from 1×40 |
| U1 socket | Female pin header 1×22 | 2.54mm pitch — DevKitC-1 right socket (J3) | THT | 1 | cut from 1×40 |
| J1 | Phoenix MKDS-1,5-4 (5.0mm) | 5.0mm pitch, 4-pin screw terminal — Theta encoder (GND/VCC/A/B) | THT | 1 | As-built = MKDS 5.0mm; KF301-4P pad-compatible (direnc.net) |
| J2 | Phoenix MKDS-1,5-4 (5.0mm) | 5.0mm pitch, 4-pin screw terminal — Phi encoder (GND/VCC/A/B) | THT | 1 | As-built = MKDS 5.0mm; KF301-4P pad-compatible |
| J3 | Phoenix MKDS-1,5-4 (5.0mm) | 5.0mm pitch, 4-pin screw terminal — Wire encoder (GND/VCC/A/B; Z unused) | THT | 1 | As-built = MKDS 5.0mm; KF301-4P pad-compatible |
| TP1–TP6 | Test point pins | 1.0mm tinned pin — TP1=5V_RAIL, TP2=3V3, TP3=MT3608 out, TP4=BAT+, TP5=BAT_OUT, TP6=GND | THT | 6 | header pins (TP6=GND added as-built) |

---

## Switches + Expansion Section (as-built — was missing from earlier BOM)

> Present in the master schematic but not in the original ~32-line list. Add to procurement, or delete from the design if the local-button / expansion block isn't wanted.

| RefDes | Part | Value / Description | Package | Qty | Note |
|---|---|---|---|---|---|
| J_SW1 | Phoenix MKDS-1,5-4 (5.0mm) | 4-pin screw terminal "SWITCHES": 1=GND, 2=BTN1, 3=BTN2, 4=3V3 | THT | 1 | two external buttons share 3V3/GND |
| R_SW1, R_SW2 | 10kΩ | 1/4W — pull-ups for BTN1 (GPIO17) / BTN2 (GPIO18) | THT | 2 | |
| C_SW1, C_SW2 | 100nF | 50V ceramic — RC debounce on BTN1/BTN2 | THT 5mm | 2 | |
| J_EXP1 | 2×6 pin header (2.54mm) | AUX_IO expansion: pins 1/3/5/7 = AUX1–4, 9 = 3V3, 11 = +5V, evens = GND | THT | 1 | `PinHeader_2x06_P2.54mm_Vertical` |
| R_AUX1–4 | 100Ω | 1/4W — series protection on AUX1–4 → GPIO11/12/13/14 | THT | 4 | |

> Removed from this section vs pre-procurement: **SW_RESET** (DevKitC-1 has an onboard RST button). J3 (wire encoder) is now a **single KF301-4P** (GND/VCC/A/B) — the encoder's Z/index line is unused, so the earlier KF301-5P → KF301-2P + KF301-3P ganged substitution is no longer needed.

---

## Summary (as-built)

| Category | Distinct line items | Total parts |
|---|---|---|
| Power section (input + Schottky-OR + pi filter) | 13 | 13 |
| Battery & charging | 10 | 10 |
| Signal conditioning | 8 | 32 (6× R_TOP + 6× R_BOT + 6× C_FILT + 6× TVS + 3× J_FB + 3× C_VCC + 1× 74HC14 + 1× C_SCHM) |
| MCU & connectors (incl. TP1–6) | 7 | 11 |
| Switches + expansion | 5 | 9 (J_SW1 + 2× R_SW + 2× C_SW + J_EXP1 + 4× R_AUX) |
| **Total** | **~37 line items** | **~85 parts** (master schematic = 74 component refs; difference = multi-pin TP/header counting) |

Counts reconciled to the master schematic (74 refs, 2026-06-20). The 6× TVS are **populated** (general THT TVS, flexible axial footprint, exact part still placeholder `D_TVS` — set MPN). C_SCHM (74HC14 decoupling) and the switch/expansion block are present in the as-built design beyond the original Appendix A list.

**As-built changes vs the pre-procurement BOM:**
- **Removed:** J_USB, R_CC1, R_CC2, TVS_USB, D_USB (USB-C input); U_IDEAL (LTC4412), Q_SWITCH, R_GATE, C_LTC (ideal-diode path); FB1/FB2/FB3 (ferrite beads); R_GPIO12; SW_RESET; LED2; R_LED2
- **Substituted:** Q_RPP AO3401 → PJA3441; Schottkys "SS34" (mislabeled SMD) → 1N5822-HT (axial DO-201); U1 Wemos D1 R32 → ESP32-S3-DevKitC-1 N16R8; J5 JST-PH 2.0mm → 2.25mm 2-pin female socket; J3 wire encoder → **single KF301-4P** (Z line unused; supersedes the earlier 5P→2P+3P ganged substitution)
- **Added:** D_EXT (second 1N5822 for the passive Schottky-OR); J_FB1/J_FB2/J_FB3 (0Ω wire jumpers replacing the ferrites); C_SCHM (74HC14 decoupling)
- **TVS×6 populated** (2026-06-19): general THT TVS on a flexible large-axial footprint (`D_DO-201AD_P15.24mm`), exact part TBD (schematic value still `D_TVS`) — supersedes the earlier DNP/retrofit plan; not the mis-ordered P6KE39CA
- Battery ADC moved GPIO36 → GPIO1 (ESP32-S3, same ADC1_CH0); status LED moved to onboard WS2812 on GPIO38
- Substrate change (carried over): pertinax → FR4

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

Most THT components are available from Turkish domestic suppliers (direnc.net, motorobit.com, robotistan.com, ozdisan.com); see `pcb_design/EVKA_position_v2/docs/TURKISH_SOURCING.md` for the full audit. Detailed per-part alternatives are in `KICAD_PLAN_DETAILED.md` → "Component Selection — BOM with Alternatives".

- **PJA3441** (Q_RPP, SOT-23): direnc.net; drop-in for AO3401 — buy a few spares for hand-soldering.
- **74HC14** in DIP-14: any HC variant (SN74HC14N / 74HC14N,652 / MM74HC14N / MC74HC14AN). Do **not** substitute 74HCT14 (TTL inputs need 5V).
- **1N5822-HT** (D_BAR, D_EXT, D_BOOST, DO-201 axial): direnc.net; SR340 / SK34 are acceptable clones.
- **TP4056 and MT3608 modules**: direnc.net / robotistan; verify the TP4056 PROG resistor is 1.2kΩ for 1A charge.
- **USB-C THT connector is no longer required** — the ESP32-S3-DevKitC-1 has dual onboard USB-C.
- **J5 (2.25mm)**: verify the pitch with calipers when the part arrives; adjust the footprint if it is actually 2.0mm (JST-PH) or 2.5mm (JST-XH).
