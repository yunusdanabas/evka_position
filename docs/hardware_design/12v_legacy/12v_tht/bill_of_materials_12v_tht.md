# Bill of Materials — evka_position 12V + 3S LiPo PCB (All-THT)

> **All through-hole** variant of [bill_of_materials_12v.md](../12v/bill_of_materials_12v.md).  
> Same circuit — every discrete component is THT. No SMD, no dead-bug soldering, no breakout boards needed.  
> **Signal section** (resistors, capacitors, TVS, ferrites, encoder terminals) reuses the same THT line items as the [legacy 5V BOM](../../5v/bill_of_materials.md).

---

## SMD → THT changes (delta vs SMD version)

| Ref | SMD Part | SMD Package | THT Replacement | THT Package | Why |
|-----|----------|-------------|-----------------|-------------|-----|
| Q1 | AO4407A | SOIC-8 | **IRF4905** | TO-220AB | P-ch MOSFET, 55V, Rds(on) 20mΩ. No heatsink needed (45mW @ 1.5A) |
| TVS_IN | SMBJ18A | DO-214AA (SMB) | **P6KE18A** | DO-15 (axial) | 18V standoff, 600W peak pulse power |
| D_EXT | SS34 | SMA (DO-214AB) | **SS34** (or 1N5822) | DO-201 (axial) | Same electrical specs, axial package |
| D_BAT | SS34 | SMA | **SS34** (or 1N5822) | DO-201 (axial) | Same |
| D_OR_BUCK | SS34 | SMA | **SS34** (or 1N5822) | DO-201 (axial) | Same |
| D_OR_USB | SS34 | SMA | **SS34** (or 1N5822) | DO-201 (axial) | Optional — omit if USB not used with 12V |
| C_IN2 | 100nF X7R 50V | 0805 | **100nF 50V ceramic disc** | Radial 5mm THT | Buck input HF bypass |
| C_OUT2 | 100nF X7R 16V | 0805 | **100nF 16V ceramic disc** | Radial 5mm THT | 5V_RAIL HF bypass |
| C_VIN_ESP | 10µF X7R 10V | 0805 | **10µF 16V electrolytic** | Radial THT | ESP32 VIN local decoupling |

All other components were already THT in the original 12V BOM.

---

## 12V power input

| Ref | Qty | Example MPN | Package | Purpose |
|-----|-----|-------------|---------|---------|
| J12V | 1 | CUI PJ-002A or equivalent | Panel/barrel **5.5×2.1mm center +** | 12V DC input |
| F1 | 1 | Littlefuse 0251020.NRT1 **or** Bourns MF-R110 | 2A glass + holder **or** 1.1A PTC | Input protection |
| F1 holder | 1 | Keystone 3549-2 | THT | If using glass fuse (omit if PTC) |
| TVS_IN | 1 | **Littelfuse P6KE18A** | **DO-15 (axial)** | 12V transient clamp (18V standoff) |
| Q1 | 1 | **International Rectifier IRF4905** | **TO-220AB** | High-side P-FET RPP (55V, Rds 20mΩ) |
| R_G | 1 | 100kΩ 1% | 1/4W TH | Q1 gate pull-down |
| D_EXT | 1 | **Vishay SS34** or **1N5822** | **DO-201 (axial)** | Schottky OR: 12V external path |
| D_BAT | 1 | **Vishay SS34** or **1N5822** | **DO-201 (axial)** | Schottky OR: 3S battery path |
| D_OR_BUCK | 1 | **Vishay SS34** or **1N5822** | **DO-201 (axial)** | Schottky OR: buck → 5V_RAIL |
| D_OR_USB | 0–1 | SS34 or 1N5822 | DO-201 (axial) | Optional: USB VBUS → 5V_RAIL |

---

## Buck converter (12V → 5V)

| Ref | Qty | Example MPN | Package | Purpose |
|-----|-----|-------------|---------|---------|
| U_BUCK | 1 | **MP1584EN** module ("DC-DC 1584") | Module ~22×17mm | 12V→5V step-down; ≥1.5A |
| C_IN1 | 1 | 68µF **35V** low-ESR electrolytic | Radial TH | Buck input bulk |
| C_IN2 | 1 | **100nF 50V ceramic disc** | **Radial 5mm THT** | Buck input HF bypass |
| L_FILT | 1 | 10µH inductor (axial or radial) | TH | LC post-filter (output ripple reduction) |
| C_FILT | 1 | 100µF **10V** electrolytic | Radial TH | LC post-filter capacitor |
| C_OUT1 | 1 | 220µF **16V** low-ESR electrolytic | Radial TH | 5V_RAIL bulk (same as legacy C1) |
| C_OUT2 | 1 | **100nF 16V ceramic disc** | **Radial 5mm THT** | 5V_RAIL HF bypass |
| C_VIN_ESP | 1 | **10µF 16V electrolytic** | **Radial TH** | Local decoupling at ESP32 VIN (WiFi noise) |

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
| R17 | 1 | 1kΩ | 1/4W TH | LED1 current limiter | — |
| R18 | 1 | 1kΩ | 1/4W TH | LED2 current limiter | — |

---

## Removed vs legacy 5V BOM

Same as [SMD version](../12v/bill_of_materials_12v.md#removed-vs-legacy-5v-bom) — no additional removals.

---

## Carried over unchanged (signal + ESP32)

Order the same quantities as [bill_of_materials.md](../../5v/bill_of_materials.md):

- **R1–R14**: 10k / 20k divider networks (14 resistors, 1/4W TH)
- **C2–C5**: 100nF ceramic for rail + encoder VCC decoupling (4 caps, THT)
- **C6–C12**: 1nF C0G/NP0 signal RC filters (7 caps, THT)
- **TVS1–TVS7**: 1.5KE3.3CA on GPIO lines (7 TVS diodes, axial DO-201)
- **FB1–FB3**: ferrite beads 600Ω@100MHz on encoder VCC (3 beads, axial)
- **J1–J3**: KF301 screw terminals for encoders (3 connectors, 5.08mm)
- **U_ESP**: 2× female header strip for Wemos D1 R32 (2.54mm)
- **Reset button**: 6mm tactile
- **Test point pins**: 7+ gold-plated (TP12, TP15, TP_BV, TP5, TP33, TP_BAT, TPG)

---

## Summary

| Category | Count (approx.) |
|----------|-----------------|
| 12V input / protection | 7–9 parts |
| Buck converter + LC filter | 8 parts |
| 3S battery / charger / BMS | 6 parts + pack |
| ADC divider | 2 resistors |
| Indicators | 2 LEDs + 2 resistors |
| Signal section (carried over) | ~25 lines (same as legacy) |
| **Total unique parts** | **~35–38 line items** |

**Zero SMD components.** Every discrete is through-hole. Modules mount via pin headers.

---

## Sourcing notes

- **IRF4905**: Common P-channel TO-220 MOSFET. Any **P-ch, ≥40V, Rds(on) ≤50mΩ** in TO-220 is acceptable. Alternatives: **IRF9540N** (100V, 117mΩ — higher drop but still fine at 1.5A), **IRF9Z34N** (55V, 100mΩ).
- **P6KE18A**: Standard axial TVS. If unavailable, use **P6KE15CA** (bidirectional, 15V standoff) or **P6KE20A** (20V standoff). Match standoff to max DC input voltage.
- **SS34 in DO-201**: The SS34 is available in both SMA (SMD) and DO-201 (axial). Verify you order the **DO-201 / DO-201AD** package. Alternative: **1N5822** (3A, 40V, Vf ≈ 0.525V max — slightly higher Vf than SS34's 0.5V max, but acceptable).
- **100nF ceramic disc**: Standard 5mm-pitch ceramic disc capacitor. Use **X7R** or **Y5V** dielectric. Available everywhere.
- **10µF 16V electrolytic**: Standard small radial electrolytic. Can substitute **10µF 25V** if 16V is unavailable.
- **MP1584EN module**: Same as SMD version. **Pre-set Vout to 5.05V** before connecting.
- **MT3608 module**: Same as SMD version. **Pre-set to 15.0V** before connecting TP5100.
- **TP5100 module**: Same as SMD version. Verify **3S jumper** is set correctly.
- **3S BMS**: Same as SMD version. Verify pin labeling matches your LiPo pack.
- **SS34 / 1N5822**: Need **3 pcs** (D_EXT, D_BAT, D_OR_BUCK) + optionally **1 more** (D_OR_USB). Buy 5+ for spares.
