# Bill of Materials — EVKA Position V3

> 12V/15V ESP32-S3 carrier with internal 3S LiPo backup and discrete Q_BATT active load-sharing.  
> Three population configs on one board: V3-A (no charger, 12V), V3-B (CN3722, 15V), V3-C (XL4016 CC/CV, 15V).  
> All discrete parts are through-hole or module/header based for LPKF S63 assembly.

---

## 1. BOM Summary

| Category | Approx. Line Items | Notes |
|---|---:|---|
| Input protection | 7 | Screw terminal, NTC, fuse/PTC, TVS, Q_RPP, R_G |
| Battery path | 5 | XT60, JST-XH-4P, blade fuse, BMS, battery |
| Q_BATT load-sharing | 4 | IRF4905, SS14, 100kΩ, 1N4742A — replaces ready-made module |
| Charging zone (V3-B) | 4 | CN3722 module, R_CS, LED, R_CHRG |
| Charging zone (V3-C) | 3 | XL4016 module, LED, R_CHRG |
| Buck and 5V filter | 7 | MP1584EN module, capacitors, inductor |
| MCU and headers | 3 | ESP32-S3-DevKitC-1 + 2× female headers |
| Encoder interface | 5 component types | 7 divider channels + 3 ferrites |
| Connectors / test points | 7 | Encoder terminals, test points, reset |
| LEDs | 2–4 | Power LED required, WiFi LED optional |

---

## 2. Input Protection

| Ref | Qty | Part | Spec / Example | Package | Notes |
|---|---:|---|---|---|---|
| J12V_TERM | 1 | Screw terminal | KF301-2P, 5.08mm | THT | Main adapter input |
| NTC1 | 0–1 | NTC thermistor | 5D-9 | THT disc | Optional; recommended to limit inrush |
| F1 | 1 | PTC or fuse | MF-R110 PTC or 2A glass fuse | THT | Adapter-side protection |
| TVS_IN | 1 | TVS diode | P6KE18A (use P6KE20A if rail peaks above 15V) | DO-15 axial | Works for both 12V and 15V configs |
| Q_RPP | 1 | P-channel MOSFET | IRF4905 | TO-220AB | High-side reverse-polarity protection |
| R_G | 1 | Resistor | 100kΩ, 1/4W | Axial | Q_RPP gate pull-down |

---

## 3. Internal 3S LiPo Backup

| Ref | Qty | Part | Spec / Example | Package | Notes |
|---|---:|---|---|---|---|
| BAT | 1 | 3S LiPo RC pack | 11.1V nominal, 1500–2200mAh | Pack | Must include XT60 main lead and JST-XH-4P balance lead |
| J_XT60 | 1 | XT60 connector | THT panel style | THT / panel | Main battery connection |
| J_BAL | 1 | JST-XH-4P connector | 2.5mm pitch | THT / panel | Balance lead; external charger access only |
| F_BAT | 1 | Blade fuse + inline holder | 5A ATO/ATC | Inline / panel | Place within 15cm of J_XT60+ |
| BMS_3S | 1 | 3S protection board | HX-3S-01 or equivalent, or protected RC LiPo pack | Module | Required. Do not rely on firmware ADC cutoff alone. |

Notes:

- V3 does not balance cells onboard. Balancing is done by the external charger via J_BAL.
- The HX-3S-01 provides undervoltage cutoff (~9.6V / 3.2V per cell) and short-circuit protection only.
- Firmware voltage ADC warnings are not a replacement for hardware protection.

---

## 4. Q_BATT Active Load-Sharing

Replaces the generic ready-made power-path module from the original V3 concept. Identical circuit to V2.

| Ref | Qty | Part | Spec / Example | Package | Notes |
|---|---:|---|---|---|---|
| Q_BATT | 1 | P-channel MOSFET | IRF4905 | TO-220AB | Source = battery positive (from BMS); Drain = BUCK_VIN |
| D_GATE | 1 | Schottky diode | SS14 | DO-214AA (SMD) or 1N5819 DO-41 axial | Anode to V_PROT; cathode to Q_BATT gate |
| R_G2 | 1 | Resistor | 100kΩ, 1/4W | Axial | Q_BATT gate pull-down to GND |
| Z1 | 1 | Zener diode | 1N4742A 12V, 1W | DO-41 axial | Gate voltage clamp; cathode to gate, anode to GND |

Behavior: adapter present → D_GATE drives gate high (clamped at 12V by Z1), Vgs ≈ 0V, FET OFF, battery isolated. Adapter absent → R_G2 pulls gate to GND, Vgs = −V_BAT, FET fully ON, battery powers BUCK_VIN.

Do not ground the IRF4905 tab. The tab is the Drain = BUCK_VIN.

---

## 4b. Charging Zone — V3-B (CN3722 Module)

Populate for onboard charging with 15V adapter. Leave empty for V3-A.

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| MOD_CHG | 1 | CN3722 charger module | 3S Li-ion, 12V–18V input, 12.6V output | Module ~35×20mm | AliExpress |
| R_CS | 1 | Resistor | 2.0Ω, 1%, 1/4W | Axial | Charge current set: I = 1.0/R_CS → 0.5A |
| LED_CHRG | 1 | LED | 3mm yellow or orange | THT | CHRG pin indicator (ON = charging) |
| R_CHRG | 1 | Resistor | 1kΩ, 1/4W | Axial | LED series current limit |

See [`charging_zone_v3.md`](charging_zone_v3.md) Section 4 for wiring and CHRG pin connection.

---

## 4c. Charging Zone — V3-C (XL4016 CC/CV Module)

Populate for onboard charging with 15V adapter. Leave empty for V3-A. Alternative to V3-B.

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| MOD_CHG | 1 | XL4016 CC/CV buck module | 8–36V input, adjustable CV+CC | Module ~55×22mm | Preset to 12.60V / 0.5A before use |
| LED_CHRG | 1 | LED | 3mm yellow or orange | THT | Output-active indicator (ON = module powered) |
| R_CHRG | 1 | Resistor | 1kΩ, 1/4W | Axial | LED series current limit |

See [`charging_zone_v3.md`](charging_zone_v3.md) Section 5 for trimpot preset procedure.

---

## 5. Buck Converter and Filter

| Ref | Qty | Part | Spec / Example | Package | Notes |
|---|---:|---|---|---|---|
| U_BUCK | 1 | Buck module | MP1584EN adjustable module | Plug-in module | Preset to 5.05–5.10V under load; CA glue trimpot after calibration |
| C_IN1 | 1 | Electrolytic capacitor | 220µF, 35V | Radial | Near buck VIN |
| C_IN2 | 1 | Ceramic capacitor | 100nF, 50V | Disc | Near buck VIN |
| L_FILT | 1 | Inductor | 22µH, ≥2A | Axial / radial | Post-filter |
| C_FILT | 1 | Electrolytic capacitor | 220µF, 10V low-ESR | Radial | Post-filter |
| C_FILT_HF | 1 | Ceramic capacitor | 100nF, 16V | Disc | Post-filter HF bypass |
| C_BULK | 1 | Electrolytic capacitor | 220µF, 16V | Radial | 5V_RAIL bulk |

Acceptable alternatives:

- Fixed 12V-to-5V buck module if output is stable between 4.9V and 5.1V under WiFi load
- LM2596 or XL4015 module if MP1584EN quality or sourcing is poor

Do not feed the ESP32-S3 directly from 12V or 15V.

---

## 6. MCU and Headers

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| U_ESP | 1 | ESP32-S3-DevKitC-1 | N8 or N8R2 preferred | Dev board | USB-C programming |
| H1 | 1 | Female header | 1×20, 2.54mm | THT | Left DevKitC header |
| H2 | 1 | Female header | 1×20, 2.54mm | THT | Right DevKitC header |

Verify exact DevKitC header spacing before drilling the PCB.

---

## 7. Encoder Signal Conditioning

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| R_TOP | 7 | Resistor | 10kΩ, 1%, 1/4W | Axial | Divider top |
| R_BOT | 7 | Resistor | 20kΩ, 1%, 1/4W | Axial | Divider bottom |
| C_SIG | 7 | Capacitor | 1nF, C0G/NP0 preferred | Ceramic disc | Do not use 100nF |
| TVS_SIG | 7 | TVS diode | 1.5KE3.3CA | DO-15 axial | GPIO transient clamp |
| FB | 3 | Ferrite bead | 600Ω @ 100MHz, ≥200mA | Axial | One per encoder VCC feed |

---

## 8. Connectors and User I/O

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| J_THETA | 1 | Screw terminal | KF301-4P, 5.08mm | THT | +5V, GND, A, B |
| J_PHI | 1 | Screw terminal | KF301-4P, 5.08mm | THT | +5V, GND, A, B |
| J_WIRE | 1 | Screw terminal | KF301-5P, 5.08mm | THT | +5V, GND, A, B, Z |
| SW_RST | 0–1 | Tactile button | 6×6mm | THT | Optional reset button to EN/GND |
| TP | 8–10 | Test point pins | 1mm loop / pin | THT | TP12, TP_BAT, TP_BV, TP5, TP33, GND, etc. |
| LED_PWR | 1 | LED | 3mm green | THT | Hardwired from 5V_RAIL |
| R_LED_PWR | 1 | Resistor | 1kΩ, 1/4W | Axial | Power LED limiter |
| LED_WIFI | 0–1 | LED | 3mm blue | THT | GPIO8, optional |
| R_LED_WIFI | 0–1 | Resistor | 1kΩ, 1/4W | Axial | WiFi LED limiter |

---

## 9. Removed vs V2

These V2 line items are intentionally not present in V3:

- MAX485 / RS-485 terminal / termination jumper
- I2C pull-ups, I2C TVS, I2C header
- MAX813L watchdog and associated resistors
- GPIO spare header
- Activity and fault LEDs by default
- DS3231, ADS1115, OLED, SD, Ethernet, CAN placeholders

They can be added later on a daughterboard if needed.
