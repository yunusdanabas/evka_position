# Bill of Materials — evka_position 12V + 3S LiPo PCB

> **Delta** design versus the legacy **5V + 1S LiPo** board in [bill_of_materials.md](../5v/bill_of_materials.md).  
> **Resistors, capacitors, TVS (GPIO), ferrites, encoder terminals, ESP32 headers** — reuse the same line items as the legacy BOM for the **signal section** (see "Carried over" below).

---

## 12V power input (new / replaced)

| Ref | Qty | Example MPN | Package | Purpose |
|-----|-----|-------------|---------|---------|
| J12V | 1 | CUI PJ-002A or equivalent | Panel/barrel **5.5×2.1mm center +** | 12V DC input |
| F1 | 1 | Littlefuse 0251020.NRT1 **or** Bourns MF-R110 | 2A glass + holder **or** 1.1A PTC | Input protection |
| F1 holder | 1 | Keystone 3549-2 | — | If using glass fuse (omit if PTC) |
| TVS_IN | 1 | **Littelfuse SMBJ18A** or **P6KE15CA** (axial) | DO-214AA (SMB) or DO-201 (axial) | 12V transient clamp |
| Q1 | 1 | **Alpha & Omega AO4407A** | SOIC-8 | High-side P-FET RPP (40V, Rds 12mΩ) |
| R_G | 1 | 100kΩ 1% | 1/4W TH | Q1 gate pull-down |
| D_EXT | 1 | **Vishay SS34** | SMA or DO-201 (axial) | Schottky OR: 12V external path |
| D_BAT | 1 | **Vishay SS34** | SMA or DO-201 (axial) | Schottky OR: 3S battery path |
| D_OR_BUCK | 1 | **Vishay SS34** | SMA or DO-201 (axial) | Schottky OR: buck → 5V_RAIL |
| D_OR_USB | 0–1 | SS34 | SMA or DO-201 | Optional: USB VBUS → 5V_RAIL |
| D_RPP_ALT | 0–1 | SS36 | SMA | Alternative to Q1 (omit Q1/R_G if used) |

---

## Buck converter (12V → 5V)

| Ref | Qty | Example MPN | Package | Purpose |
|-----|-----|-------------|---------|---------|
| U_BUCK | 1 | **MP1584EN** module ("DC-DC 1584") | Module ~22×17mm | 12V→5V step-down; ≥1.5A |
| C_IN1 | 1 | 68µF **35V** low-ESR electrolytic | Radial TH | Buck input bulk |
| C_IN2 | 1 | 100nF X7R **50V** | 0805 or TH | Buck input HF |
| L_FILT | 1 | 10µH inductor (axial or radial) | TH | LC post-filter (output ripple reduction) |
| C_FILT | 1 | 100µF **10V** electrolytic | Radial TH | LC post-filter capacitor |
| C_OUT1 | 1 | 220µF **16V** low-ESR electrolytic | Radial TH | 5V_RAIL bulk (same as legacy C1) |
| C_OUT2 | 1 | 100nF X7R **16V** | 0805 or TH | 5V_RAIL ceramic |
| C_VIN_ESP | 1 | 10µF X7R **10V** ceramic | 0805 or TH | Local decoupling at ESP32 VIN (WiFi noise) |

---

## 3S LiPo battery and charger

| Ref | Qty | Example MPN | Package | Purpose |
|-----|-----|-------------|---------|---------|
| MOD_BOOST | 1 | **MT3608** module ("DC-DC boost") | Module ~36×17mm | 12V → 15V boost for charger |
| C_BOOST_IN | 1 | 10µF **25V** ceramic or electrolytic | Radial TH | MT3608 input decoupling |
| MOD_CHG | 1 | **TP5100** module (2S/3S LiPo charger) | Module ~27×19mm | 3S charger (set jumper to 3S) |
| BMS_3S | 1 | 3S 10A BMS board (e.g. HX-3S-FL10A) | Module ~50×18mm | Cell protection (OV/UV/SC/OC) |
| J_BAT | 1 | **JST-XH-4P** (or KF301-4P screw terminal) | 2.5mm / 5.08mm | 3S balance connector |
| LiPo | 1 | 3S 11.1V **1500–2200mAh** LiPo pack | Pack | Backup battery |

---

## 12V ADC divider (replaces legacy 100k+100k LiPo tap)

| Ref | Qty | Value | Notes |
|-----|-----|-------|--------|
| R_ADC_TOP | 1 | **120kΩ** 1% | From V12_PROT (or 3S_OUT+) to GPIO36 |
| R_ADC_BOT | 1 | **27kΩ** 1% | GPIO36 to GND |
| — | — | Ratio **(120k+27k)/27k ≈ 5.444** | Firmware TODO: `BATT_DIVIDER_RATIO 5.444` |

---

## Indicators

| Ref | Qty | Color | Size | Purpose | Drive |
|-----|-----|-------|------|---------|-------|
| LED1 | 1 | Green | 3mm | Power on (5V_RAIL) | 5V_RAIL → 1kΩ → LED → GND |
| LED2 | 1 | Red | 3mm | Battery low warning | GPIO 25 → 1kΩ → LED → GND |
| R17 | 1 | 1kΩ | 1/4W | LED1 current limiter | — |
| R18 | 1 | 1kΩ | 1/4W | LED2 current limiter | — |

---

## Removed vs legacy 5V BOM

| Legacy ref | Part | Reason |
|------------|------|--------|
| MOD1 | TP4056 + DW01A | Replaced by TP5100 + 3S BMS |
| MOD2 | MT3608 (5V boost) | Repurposed: now boosts 12V→15V for charger |
| D1–D2 | SS34 (5V Schottky OR) | Replaced by D_EXT, D_BAT, D_OR_BUCK |
| D3 | 1N5817 | Auto-charge path no longer needed |
| J4 | 5V DC barrel jack | Replaced by J12V (12V) |
| J5 | JST-PH 2-pin (1S LiPo) | Replaced by J_BAT JST-XH 4-pin (3S) |
| J6 | KF128V 5V test | Omit or relabel for 12V test |
| R15–R16 | 100k+100k (1S ADC) | Replaced by 120k+27k (12V range ADC) |
| Q1 (legacy) | SI2301 | Replaced by AO4407A (40V rating) |
| C13 | 10µF MT3608 input | Replaced by C_BOOST_IN at new MT3608 position |

---

## Carried over unchanged (signal + ESP32)

Order the same quantities as [bill_of_materials.md](../5v/bill_of_materials.md):

- **R1–R14**: 10k / 20k divider networks (14 resistors)
- **C2–C5**: 100nF ceramic for rail + encoder VCC decoupling (4 caps)
- **C6–C12**: 1nF C0G/NP0 signal RC filters (7 caps)
- **TVS1–TVS7**: 1.5KE3.3CA or SMBJ3.3CA on GPIO lines (7 TVS diodes)
- **FB1–FB3**: ferrite beads 600Ω@100MHz on encoder VCC (3 beads)
- **J1–J3**: KF301 screw terminals for encoders (3 connectors)
- **U_ESP**: 2× female header strip for Wemos D1 R32
- **Reset button**: 6mm tactile
- **Test point pins**: 7+ gold-plated (TP12, TP15, TP_BV, TP5, TP33, TP_BAT, TPG)

---

## Summary

| Category | Count (approx.) |
|----------|-----------------|
| 12V input / protection | 7–9 parts |
| Buck converter + LC filter | 7 parts |
| 3S battery / charger / BMS | 6 parts + pack |
| ADC divider | 2 resistors |
| Indicators | 2 LEDs + 2 resistors |
| Signal section (carried over) | ~25 lines (same as legacy) |
| **Total unique parts** | **~35–38 line items** |

---

## Sourcing notes

- **AO4407A**: Common P-FET; any **40V / low Rds(on)** P-channel in SOIC-8 is acceptable. SOT-23 alternative: **AO3401A** (30V, higher Rds — acceptable for <1A).
- **SMBJ18A**: Alternates **SMBJ15A** / **P6KE15CA** (axial, easier for pertinax). Match standoff to max DC input.
- **MP1584EN module**: Widely cloned; verify **no-load stability** and **pre-set Vout to 5.05V** before connecting ESP32.
- **MT3608 module**: Same module used in V1 board (user has experience). **Pre-set to 15.0V** before connecting TP5100.
- **TP5100 module**: Available as ~$1 breakout. Verify **3S jumper** is set correctly. Some modules default to 2S.
- **3S BMS**: Common 3S 10A boards (~$0.50). Verify pin labeling (B+, BM, B2, B−, P+, P−) matches your LiPo pack wiring.
- **JST-XH-4P**: Standard 3S LiPo balance connector. Match polarity to your pack. Alternative: KF301-4P screw terminal if balance leads are thick.
- **SS34 Schottky**: Need **3 pcs** (D_EXT, D_BAT, D_OR_BUCK) + optionally **1 more** (D_OR_USB). Buy 5+ for spares.
- For **automotive** environment, replace buck with **40V+ rated** part — see [power_supply_12v_spec.md](power_supply_12v_spec.md).
