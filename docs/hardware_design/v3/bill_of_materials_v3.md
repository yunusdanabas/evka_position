# Bill of Materials — EVKA Position V3

> Core-only 12V ESP32-S3 carrier with internal 3S LiPo backup and generic ready-made power-path module interface.  
> All discrete parts are through-hole or module/header based for LPKF S63 assembly.

---

## 1. BOM Summary

| Category | Approx. Line Items | Notes |
|---|---:|---|
| 12V input protection | 7 | Connector, NTC, fuse/PTC, TVS, IRF4905, pull-down |
| Battery path | 5 | XT60, JST-XH, blade fuse, optional BMS/protection, battery |
| Power-path interface | 3 | Terminals/headers + selected ready-made module |
| Buck and 5V filter | 7 | MP1584EN module, capacitors, inductor |
| MCU and headers | 3 | ESP32-S3-DevKitC-1 + 2x female headers |
| Encoder interface | 5 component types | 7 divider channels + 3 ferrites |
| Connectors / test points | 7 | Encoder terminals, test points, reset |
| LEDs | 2-4 | Power LED required, WiFi LED optional |

---

## 2. 12V Input Protection

| Ref | Qty | Part | Spec / Example | Package | Notes |
|---|---:|---|---|---|---|
| J12V_BARREL | 0-1 | DC barrel jack | 5.5x2.1mm center positive | THT / panel | Use if adapter plugs directly into board |
| J12V_TERM | 0-1 | Screw terminal | KF301-2P, 5.08mm | THT | Use for cabinet wiring |
| NTC1 | 1 | NTC thermistor | 5D-9 | THT disc | Optional but recommended |
| F1 | 1 | PTC or fuse | MF-R110 PTC or 2A glass fuse | THT | Adapter-side protection |
| TVS_IN | 1 | TVS diode | P6KE18A, fallback P6KE20A | DO-15 axial | Match adapter max voltage |
| Q_RPP | 1 | P-channel MOSFET | IRF4905 | TO-220AB | High-side reverse-polarity protection |
| R_G | 1 | Resistor | 100k, 1/4W | Axial | Q_RPP gate pull-down |

---

## 3. Internal 3S LiPo Backup

| Ref | Qty | Part | Spec / Example | Package | Notes |
|---|---:|---|---|---|---|
| BAT | 1 | 3S LiPo RC pack | 11.1V nominal, 1500-2200mAh typical | Pack | Must include XT60/main lead and JST-XH balance lead |
| J_XT60 | 1 | XT60 connector | Panel or board-edge style | THT / panel | Main battery connection |
| J_BAL | 1 | JST-XH-4P access | 2.5mm pitch | THT / panel | Balance lead access for external charger |
| F_BAT | 1 | Blade fuse + holder | 5A ATO/ATC default | Inline / panel | Place close to battery positive |
| BMS_3S | 1 | 3S protection board | HX-3S-01 or equivalent, or use a protected RC LiPo pack | Module | Required unless pack has built-in cell protection (verified). Do not rely on firmware ADC cutoff alone for an internal unprotected pack. |

Notes:

- V3 does not rely on BMS balancing. Balancing is done by the external charger.
- If using an unprotected RC LiPo pack internally, add a protection/BMS module or use a power-path module with verified low-voltage cutoff.
- Firmware voltage warnings are not a replacement for hardware battery protection.

---

## 4. Ready-Made Power-Path Module Interface

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| MOD_PWRPATH | 1 | Ready-made 12V UPS / ideal-diode / power-path module | 3S range, >=1A continuous, reverse-current blocking | Module | Exact model TBD and must be validated |
| J_PWRPATH_IN | 1 | Screw terminal or header | ADAPTER+, BATTERY+, GND | KF301 / 2.54mm | Interface to module input wires |
| J_PWRPATH_OUT | 1 | Screw terminal or header | BUCK_VIN, GND | KF301 / 2.54mm | Module output to buck input |

Do not use a module just because it is sold as a "UPS" board. It must pass the acceptance criteria in [`power_path_module_interface_v3.md`](power_path_module_interface_v3.md).

---

## 5. Buck Converter and Filter

| Ref | Qty | Part | Spec / Example | Package | Notes |
|---|---:|---|---|---|---|
| U_BUCK | 1 | Buck module | MP1584EN adjustable module | Plug-in module | Preset to 5.05-5.10V under load |
| C_IN1 | 1 | Electrolytic capacitor | 220uF, 35V | Radial | Near buck VIN |
| C_IN2 | 1 | Ceramic capacitor | 100nF, 50V | Disc | Near buck VIN |
| L_FILT | 1 | Inductor | 22uH, >=2A | Axial / radial | Post-filter |
| C_FILT | 1 | Electrolytic capacitor | 220uF, 10V low-ESR | Radial | Post-filter |
| C_FILT_HF | 1 | Ceramic capacitor | 100nF, 16V | Disc | Post-filter HF bypass |
| C_BULK | 1 | Electrolytic capacitor | 220uF, 16V | Radial | 5V_RAIL bulk |

Acceptable alternatives:

- Fixed 12V-to-5V buck module, if output is stable between 4.9V and 5.1V under WiFi load
- LM2596 or XL4015 module if MP1584EN quality is poor or sourcing changes

Avoid feeding the ESP32-S3 directly from 12V.

---

## 6. MCU and Headers

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| U_ESP | 1 | ESP32-S3-DevKitC-1 | N8 or N8R2 preferred | Dev board | USB-C programming |
| H1 | 1 | Female header | 1x20, 2.54mm | THT | Left DevKitC header |
| H2 | 1 | Female header | 1x20, 2.54mm | THT | Right DevKitC header |

Verify exact DevKitC header spacing before drilling the PCB.

---

## 7. Encoder Signal Conditioning

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| R_TOP | 7 | Resistor | 10k, 1%, 1/4W | Axial | Divider top |
| R_BOT | 7 | Resistor | 20k, 1%, 1/4W | Axial | Divider bottom |
| C_SIG | 7 | Capacitor | 1nF, C0G/NP0 preferred | Ceramic disc | Do not use 100nF |
| TVS_SIG | 7 | TVS diode | 1.5KE3.3CA | DO-15 axial | GPIO transient clamp |
| FB | 3 | Ferrite bead | 600 ohm @ 100MHz, >=200mA | Axial | One per encoder VCC feed |

---

## 8. Connectors and User I/O

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| J_THETA | 1 | Screw terminal | KF301-4P, 5.08mm | THT | +5V, GND, A, B |
| J_PHI | 1 | Screw terminal | KF301-4P, 5.08mm | THT | +5V, GND, A, B |
| J_WIRE | 1 | Screw terminal | KF301-5P, 5.08mm | THT | +5V, GND, A, B, Z |
| SW_RST | 0-1 | Tactile button | 6x6mm | THT | Optional reset button to EN/GND |
| TP | 8-10 | Test point pins | 1mm loop / pin | THT | TP12, TP_BAT, TP_BV, TP5, TP33, GND, etc. |
| LED_PWR | 1 | LED | 3mm green | THT | Hardwired from 5V_RAIL |
| R_LED_PWR | 1 | Resistor | 1k, 1/4W | Axial | Power LED limiter |
| LED_WIFI | 0-1 | LED | 3mm blue | THT | GPIO8, optional |
| R_LED_WIFI | 0-1 | Resistor | 1k, 1/4W | Axial | WiFi LED limiter |

---

## 9. Removed vs V2

These V2 line items are intentionally not required in V3:

- MAX485 / RS-485 terminal / termination jumper
- I2C pull-ups, I2C TVS, I2C header
- MAX813L watchdog and associated resistors
- GPIO spare header
- Activity and fault LEDs by default
- DS3231, ADS1115, OLED, SD, Ethernet, CAN placeholders

They can be added later on a daughterboard if needed.
