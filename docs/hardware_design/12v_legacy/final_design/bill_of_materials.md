# Bill Of Materials - Final EVKA Position Hardware

This BOM is for the final 12V external-charge-only board. It intentionally excludes V3-B/V3-C onboard charger parts.

## 1. BOM Summary

| Category | Line Items | Notes |
|---|---:|---|
| Adapter input and protection | 6 | Connector, fuse/PTC, TVS, Q_RPP, gate resistor, test points |
| Adapter isolation and battery switch | 5 | `D_ADAPT`, `D_GATE`, Q_BATT, gate resistor, test points |
| Battery and protection | 6 | 3S LiPo, XT60, JST-XH balance access, F_BAT, BMS, test point |
| Buck and 5V filter | 8 | MP1584EN, input bulk, LC output filter, 5V bulk, test point |
| MCU and headers | 4 | ESP32-S3 DevKitC, two female headers, test point |
| Encoder interface | 5 component types | 7 channels of divider/filter/TVS plus 3 ferrites |
| Connectors, LEDs, test points | 9 | Encoder terminals, LEDs (incl. optional), reset, test pins |

## 2. Adapter Input And Protection

| Ref | Qty | Part | Spec / Example | Package | Notes |
|---|---:|---|---|---|---|
| J12V_TERM | 1 | Screw terminal | KF301-2P, 5.08mm | THT | Main 12V input |
| F1 | 1 | PTC or fuse | MF-R110 PTC or 2A glass fuse | THT | Adapter-side protection |
| TVS_IN | 1 | TVS diode | P6KE18A | DO-15 axial | Cathode to protected rail side, anode to GND |
| Q_RPP | 1 | P-channel MOSFET | IRF4905 | TO-220AB | Adapter reverse-polarity protection |
| R_GATE_RPP | 1 | Resistor | 100k, 1/4W | Axial | Q_RPP gate pull-down |
| TP_IN / TP_PROT | 2 | Test point | 1mm loop or pin | THT | Optional but recommended |

Alternatives:

- `P6KE20A` if the adapter rail can sit above 15V in normal operation.
- IRF9540N can substitute for IRF4905 if IRF4905 is unavailable, but check voltage drop and pinout.

## 3. Adapter Isolation And Battery Source Switch

| Ref | Qty | Part | Spec / Example | Package | Notes |
|---|---:|---|---|---|---|
| D_ADAPT | 1 | Schottky diode | SS36, SS34, or 1N5822 | DO-201 axial preferred | Anode to `V_PROT`, cathode to `BUCK_VIN` |
| Q_BATT | 1 | P-channel MOSFET | IRF4905 | TO-220AB | Battery switch, source=battery, drain=`BUCK_VIN` |
| D_GATE | 1 | Schottky diode | 1N5819, SS14, or SS34 | DO-41 / DO-201 | Anode to `V_PROT`, cathode to Q_BATT gate |
| R_GATE_BAT | 1 | Resistor | 100k, 1/4W | Axial | Q_BATT gate pull-down to GND |
| TP_GATE / TP_BV | 2 | Test point | 1mm loop or pin | THT | Gate and buck input diagnostics |

Final design note: no Q_BATT gate zener is populated in this 12V-only design.

## 4. Battery And Protection

| Ref | Qty | Part | Spec / Example | Package | Notes |
|---|---:|---|---|---|---|
| BAT | 1 | 3S LiPo RC pack | 11.1V nominal, 1500-2200mAh | Pack | Must include main lead and balance lead |
| J_XT60 | 1 | XT60 connector | Panel or THT style | Panel/THT | Main battery connection |
| J_BAL | 1 | JST-XH-4P | 2.5mm pitch | THT/panel | Balance lead access for external charger |
| F_BAT | 1 | Blade fuse + holder | 5A ATO/ATC | Inline/panel | Must be close to battery positive |
| BMS_3S | 1 | 3S protection board | HX-3S-01 or equivalent | Module | Required unless using a protected pack |
| TP_BAT | 1 | Test point | 1mm loop or pin | THT | Protected battery voltage |

Battery notes:

- Use a real 3S balance charger for charging.
- Do not rely on the BMS for balancing.
- Do not omit `F_BAT`, even during prototype testing.

## 5. Buck Converter And 5V Filter

| Ref | Qty | Part | Spec / Example | Package | Notes |
|---|---:|---|---|---|---|
| U_BUCK | 1 | Buck module | MP1584EN adjustable | Plug-in module | Preset to 5.05V under load |
| C_BV | 1 | Electrolytic capacitor | 470uF, 35V, low ESR | Radial | `BUCK_VIN` hold-up |
| C_IN_HF | 1 | Ceramic capacitor | 100nF, 50V | Disc | Near buck VIN |
| L_FILT | 1 | Inductor | 22uH, >=2A | Axial/radial | Buck output post-filter |
| C_FILT | 1 | Electrolytic capacitor | 220uF, 10V, low ESR | Radial | 5V filter capacitor |
| C_FILT_HF | 1 | Ceramic capacitor | 100nF, 16V | Disc | 5V high-frequency bypass |
| C_5V_BULK | 1 | Electrolytic capacitor | 220uF, 16V | Radial | 5V star-node bulk |
| TP5 | 1 | Test point | 1mm loop or pin | THT | 5V rail validation |

Acceptable buck alternatives:

- Fixed 12V-to-5V buck module, if measured output remains 4.9V to 5.1V under WiFi load.
- XL4015 or LM2596 module if MP1584EN sourcing/quality is poor, but layout and ripple must be revalidated.

## 6. MCU And Headers

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| U_ESP | 1 | ESP32-S3-DevKitC-1 | N8 or N8R2 preferred | Dev board | USB-C programming |
| H1 | 1 | Female header | 1x20, 2.54mm | THT | DevKitC left header |
| H2 | 1 | Female header | 1x20, 2.54mm | THT | DevKitC right header |
| TP33 | 1 | Test point | 1mm loop or pin | THT | 3.3V rail after module insertion |

Verify the exact DevKitC header spacing before drilling the board.

## 7. Encoder Signal Conditioning

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| R_TOP | 7 | Resistor | 10k, 1%, 1/4W | Axial | Divider top resistor |
| R_BOT | 7 | Resistor | 20k, 1%, 1/4W | Axial | Divider bottom resistor |
| C_SIG | 7 | Capacitor | 1nF, C0G/NP0 preferred | Ceramic disc | Do not use 100nF |
| TVS_SIG | 7 | TVS diode | 1.5KE3.3CA | DO-15 axial | GPIO transient clamp |
| FB | 3 | Ferrite bead | 600 ohm at 100MHz, >=200mA | Axial | One per encoder VCC feed |

## 8. Connectors, LEDs, Reset, Test Points

| Ref | Qty | Part | Spec | Package | Notes |
|---|---:|---|---|---|---|
| J_THETA | 1 | Screw terminal | KF301-4P, 5.08mm | THT | +5V, GND, A, B |
| J_PHI | 1 | Screw terminal | KF301-4P, 5.08mm | THT | +5V, GND, A, B |
| J_WIRE | 1 | Screw terminal | KF301-5P, 5.08mm | THT | +5V, GND, A, B, Z |
| LED_PWR | 1 | LED | 3mm green | THT | Hardwired power LED |
| R_LED_PWR | 1 | Resistor | 1k, 1/4W | Axial | Power LED current limit |
| LED_WIFI | 0-1 | LED | 3mm blue | THT | Optional GPIO8 WiFi LED |
| R_LED_WIFI | 0-1 | Resistor | 1k, 1/4W | Axial | Optional WiFi LED resistor |
| SW_RST | 0-1 | Tactile button | 6x6mm | THT | Optional EN-to-GND reset |
| TPG | 3+ | Ground test points | 1mm loop or pin | THT | Place near power, MCU, encoders |

## 9. Do Not Populate

These parts are deliberately not in the final design:

- CN3722 charger module
- XL4016 CC/CV charger module
- TP5100 charger module
- MT3608 boost charger stage
- MAX485 RS-485 transceiver
- MAX813L watchdog
- I2C pull-ups/header
- Spare GPIO header
- SD, Ethernet, or CAN footprints

If a future revision needs these, create a new revision or a daughterboard. Do not silently add them to this final board.

## 10. Minimum Order Extras

Order spare parts for bring-up and repair:

- 3x IRF4905 total, two used and one spare
- 5x Schottky diodes total, two used and spares for polarity mistakes
- 2x MP1584EN buck modules, one used and one spare
- Extra 1nF capacitors; do not substitute 100nF if short on parts
- Extra fuses for `F_BAT`
- Extra screw terminals for connector damage during prototyping
