# KiCad PCB Design Plan — EVKA Position 5V v2

## Context

The 5V v2 board design is fully documented in `pcb_design/EVKA_position_v2/docs/` (schematic, BOM, layout guide). The KiCad project at `pcb_design/EVKA_position_v2/` is created and opened in KiCad v9.0, but both the schematic and PCB files are completely empty. This plan covers the full flow: schematic capture → PCB layout → Gerber export, targeting LPKF S63 milling on FR4.

**Reference docs:**

- `pcb_design/EVKA_position_v2/docs/circuit_schematic.md` — all nets, component values, connector pinouts
- `pcb_design/EVKA_position_v2/docs/bill_of_materials.md` — ~50 reference designators, footprints
- `pcb_design/EVKA_position_v2/docs/pcb_layout_guide.md` — LPKF S63 design rules, zone layout, routing priority

---

## Phase 0 — Workspace Prep *(do once before opening KiCad)*

**Step 0.1 — Read the canonical references in this folder**

- `circuit_schematic.md` — net topology, original component values, ASCII schematics (treat as reference for the *unmodified* design; the procurement deltas in Phase 2 below override it where they conflict)
- `bill_of_materials.md` — to be regenerated from this plan after the first build
- `pcb_layout_guide.md` — LPKF S63 design rules and zone framework

**Step 0.2 — Confirm physical parts on hand**

Before starting schematic capture, check that the following are present (or on order with a known ETA):

- 1× DC barrel jack DC-005 5.5×2.1 mm
- 1× barrel-jack TVS SMAJ5.0A
- 4× Schottky 1N5822-HT axial (D_BAR + D_EXT + D_BOOST + 1 spare)
- 1× PJA3441 SOT-23 (Q_RPP)
- 1× 10 µH 1 A radial inductor
- 1× 220 µF/10 V radial electrolytic, 1× 10 µF/10 V, 1× 22 µF/10 V; 100 nF MLCC ×6
- 1× TP4056+DW01A+FS8205A module
- 1× MT3608 boost module + 300 kΩ + 100 kΩ for FB mod
- 1× ESP32-S3-DevKitC-1 N16R8
- 2× 1×22 female pin headers (or 2× 1×40 to cut)
- 3× KF301-4P (J1/J2/J3) + 1× KF301-2P (J6)  _(was 2×4P + 2P + 3P; J3 is now a single 4P — Z unused)_
- 1× 2.25 mm 2-pin female JST socket
- 1× 74HC14 DIP-14 (any HC variant)
- 1× green LED + 1× 1 kΩ (LED1, R_LED1)
- Resistors 1/4 W metal film: 6× 10 kΩ, 6× 20 kΩ, 1× 100 kΩ (R_RPP), 2× 100 kΩ (R_MON1/2), 1× 300 kΩ + 1× 100 kΩ (MT3608 mod)
- Caps: 6× 10 nF (C_FILT, prefer C0G/NP0 if dielectric known), 1× 100 nF (C_ADC)
- 3× short tinned wire pieces for J_FB jumpers
- 6× test point pins (or use 2.54 mm header pins)
- 1× 1S LiPo cell with male JST mating connector

**Step 0.3 — Modify the MT3608 module (do once, before assembly)**

1. Identify the trim pot and existing FB resistors on the MT3608 PCB
2. Desolder trim pot + both FB resistors (solder wick or hot air at ≤300 °C)
3. Solder R_MT_HI (300 kΩ) between VOUT pad and FB pad
4. Solder R_MT_LO (100 kΩ) between FB pad and GND pad
5. Apply 5 V to IN; measure OUT — should read 5.00 V ± 0.05 V unloaded
6. Load test with 12 Ω/2 W (≈415 mA): OUT should hold 5.00 V ± 0.10 V
7. Mark module "5.0 V FIXED" in permanent marker

---

## Phase 1 — KiCad Project Setup

**Step 1 — Open and inspect the project**

1.1 Launch KiCad v9.0
1.2 File → Open Project → `pcb_design/EVKA_position_v2/EVKA_position_v2.kicad_pro`
1.3 Open Schematic Editor (Eeschema) — confirm the empty sheet appears (no symbols, just the title block)
1.4 Open PCB Editor (PCBnew) — confirm an empty board (no footprints, no edge cuts)
1.5 Save a backup: File → Save As… → name it `EVKA_position_v2_pre_layout`. KiCad will create a `_backups/` zip — keep it as a recovery point before any edits.

**Step 2 — Configure symbol libraries**

2.1 Preferences → Manage Symbol Libraries → "Project Specific Libraries" tab
2.2 Confirm these standard global libraries are enabled (they should be by default):
   - `Device` (R, C, L, D, Q, transistors)
   - `Connector_Generic` (pin headers)
   - `Connector` (named connectors)
   - `power` (GND, +5V, +3V3 power flags)
   - `74xx` (74HC14)
2.3 For the ESP32-S3-DevKitC-1: there is no official Espressif KiCad library shipped with KiCad. Either:
   - **Option A (recommended):** Use a `Connector_Generic:Conn_02x22_Odd_Even` symbol (44 pin, 2×22) and rename pins manually to match the J1/J3 datasheet labels (3V3, RST, 4, 5, 6, 7, 15, 16, 17, 18, 8, 3, 46, 9, 10, 11, 12, 13, 14, 5V, GND on one side; G, TX, RX, 1, 2, 42, 41, 40, 39, 38, 37, 36, 35, 0, 45, 48, 47, 21, 20, 19, G, G on the other).
   - **Option B:** Download an Espressif community symbol from kicad-symbols-master GitHub (e.g. ESP32-S3-DevKitC-1.kicad_sym) — drop into `pcb_design/EVKA_position_v2/symbols/` and add via the library dialog.
2.4 The remaining special parts use generic symbols:
   - **PJA3441**: `Device:Q_PMOS_GSD` (3-terminal P-MOSFET, S/G/D pins match SOT-23)
   - **1N5822**: `Device:D_Schottky`
   - **SMAJ5.0A**: `Device:D_TVS` (unidirectional)
   - **TP4056 module**: `Connector:Conn_01x06` (renamed pins: IN+/IN-/B+/B-/OUT+/OUT-)
   - **MT3608 module**: `Connector:Conn_01x04` (renamed: IN+/IN-/OUT-/OUT+)
   - **74HC14**: `74xx:74HC14`

**Step 3 — Configure footprint libraries**

3.1 Preferences → Manage Footprint Libraries → confirm standard libraries enabled:
   - `Resistor_THT`, `Capacitor_THT`, `Diode_THT`, `Inductor_THT`
   - `Package_TO_SOT_SMD` (SOT-23)
   - `Package_DIP` (DIP-14)
   - `Connector_PinHeader_2.54mm`
3.2 Custom footprints to create or import (drop into `pcb_design/EVKA_position_v2/footprints/`):
   - **KF301-2P / 3P / 4P** — 5.0 mm pitch screw terminals. The 4P/3P/2P share a common cell: 5.08 mm pitch, hole Ø 1.3 mm, pad Ø 2.4 mm, body 7.5 mm tall × N×5 mm wide (see KF301 datasheet)
   - **JST 2.25 mm 2-pin female socket** — match direnc.net part exactly. **Verify pitch with calipers when part arrives**; if it's actually 2.0 or 2.5 mm, edit the footprint pads before placement
   - **TP4056 module footprint** — 6-pad THT, 2.54 mm pitch within rows, row spacing per ordered module (typically 17.78 mm)
   - **MT3608 module footprint** — 4-pad THT, 2.54 mm pitch, row spacing per module (typically 12.7 mm)
   - **ESP32-S3-DevKitC-1 footprint** — 2× rows of 22 holes, 2.54 mm pin pitch, **22.86 mm row spacing** (Espressif spec). Add a graphic outline 63.5 × 25.4 mm with two USB-C cutouts on the short edge for visualization
   - **Test point pin** — single round pad, 1.0 mm hole, 2.0 mm pad
3.3 Standard library footprints used directly (no custom work):
   - `Diode_THT:D_DO-201_P12.70mm_Horizontal` for 1N5822 (D_BAR, D_EXT, D_BOOST)
   - `Diode_SMD:D_SMA` for SMAJ5.0A (TVS_BAR)
   - `Diode_THT:D_DO-201AD_P15.24mm_Horizontal` for the TVS×6 (flexible large-axial — takes DO-15 or DO-201 bodies; populated, part TBD)
   - `Package_TO_SOT_SMD:SOT-23` for PJA3441
   - `Package_DIP:DIP-14_W7.62mm` for 74HC14
   - `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` for 1/4 W metal film resistors
   - `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` for 100 nF / 10 nF ceramic
   - `Capacitor_THT:CP_Radial_D6.3mm_P2.50mm` for 22 µF radial; `D8.0mm_P3.50mm` for 220 µF
   - `LED_THT:LED_D5.0mm` for LED1
   - `Inductor_THT:L_Axial_L8.5mm_D4.0mm_P15.24mm_Horizontal` for L1 (or radial body — match part)

---

## Phase 2 — Schematic Capture (Eeschema)

> ### ⚙ Design Changes from Procurement (2026-05-08)
>
> The original `circuit_schematic.md` describes the design as specified. After component selection, the following changes are now in effect — **the schematic to be drawn diverges from the source doc** in these places:
>
> 1. **USB-C input dropped** (procurement #2) — `J_USB`, `R_CC1`, `R_CC2`, `TVS_USB`, `D_USB` are **removed**. The ESP32-S3 module's onboard USB-C handles programming. Single 5V input via barrel jack `J4` only.
> 2. **LTC4412 ideal diode dropped** (procurement #6) — `U_IDEAL`, `Q_SWITCH`, `R_GATE`, `C_LTC` are **removed**. Replaced with passive Schottky OR using a second 1N5822 (`D_EXT`). External path 5V_RAIL ≈ 4.6V (vs 4.98V) — still adequate for ESP32-S3 (5V max, 3.0V min) and AMS1117 LDO.
> 3. **Q_RPP**: AO3401 → **PJA3441** (Panjit, drop-in SOT-23, −40V/−3.1A/74mΩ).
> 4. **Ferrite beads replaced with 0Ω jumpers** (procurement #12) — `FB1`/`FB2`/`FB3` (600Ω@100MHz) → **wire link / 0Ω jumper** at `J_FB1`/`J_FB2`/`J_FB3` positions. **Decision rationale**: encoder current is ~80 mA; even a 10Ω resistor drops 0.8 V (E40S6 brown-out at <4.5 V); a 22Ω drops 1.76 V (encoder fails). A real ferrite bead has DC R < 0.5Ω. Best substitute is a 0Ω jumper. Footprint kept compatible with axial ferrite for future retrofit. C_VCC×3 bypass caps unchanged — provide HF filtering at the connector.
> 5. **ESP32 module: Wemos D1 R32 → ESP32-S3-DevKitC-1 N16R8** (procurement #13, direnc.net) — confirmed: ESP32-S3-WROOM-1-N16R8 module on 44-pin 2×22 DevKitC-1 form factor (J1 left + J3 right, 22.86 mm row spacing, 63.5 mm board length, 25.4 mm wide). GPIO map below uses the official Espressif pinout (datasheet confirmed 2026-05-08). **N16R8 caveat: GPIO 35/36/37 are reserved for octal SPI flash/PSRAM and unusable.** Strapping pins (avoid): GPIO 0/3/45/46. USB native: GPIO 19/20. Onboard RGB LED (WS2812): GPIO 38. UART0 console: GPIO 43/44 (TX/RX). Firmware will need a new PlatformIO env `esp32-s3-devkitc-1`.
> 6. **Encoder TVS×6 POPULATED — general THT, part TBD** (decision 2026-06-19, supersedes the earlier DNP plan). The mis-ordered P6KE39CA (33 V) is not used. The footprint is the flexible large-axial `Diode_THT:D_DO-201AD_P15.24mm_Horizontal`, which accepts a DO-15 (P6KE) or DO-201 (1.5KE) body — so any proper THT TVS can be soldered. **Selection guide:** bidirectional, V_RWM ≥ ~3.34 V so it doesn't leak at the 3.33 V divider HIGH (1.5KE3.9CA ideal but import-only; on-hand **1.5KE3.3CA** from the old 5 V board fits and works, with slight leakage). Set the exact value when the part is finalized.
> 7. **J_USB removed**, **J6 retained** as bench 5V input.
> 8. **J5 LiPo connector**: 2.25 mm pitch female header (procurement #14, direnc.net) — non-standard pitch. **Decision: design footprint at 2.25 mm pitch as labeled** (matches direnc product page). User must measure with calipers when the part arrives and adjust the KiCad footprint if actual pitch is 2.0 mm (JST PH) or 2.5 mm (JST XH). PCB-side is **female socket** because the LiPo cable terminates in a male plug.
> 9. **J3 (wire encoder)**: now a **single KF301-4P** (GND/VCC/A/B), same part as J1/J2. The encoder's Z/index line is unused, so the original KF301-5P (procurement #15) and its KF301-2P + KF301-3P ganged substitute are both dropped. _(Updated 2026-06-19.)_
> 10. **SW_RESET dropped** — DevKitC-1 has an onboard RST button that the enclosure design will expose. Dropping `SW_RESET` from the BOM saves 1 line item and frees Zone D space.
> 11. **Discrete LED2 dropped, onboard WS2812 RGB used instead** — the DevKitC-1 has an addressable RGB LED on GPIO 38. Drive it from firmware to indicate battery state (green=full, yellow=mid, red=low, blinking-red=critical). Removes `LED2` and `R_LED2` from the BOM. Firmware: add `Adafruit_NeoPixel` (or `FastLED`) library and replace `digitalWrite(GPIO25, ...)` calls with `pixel.setPixelColor(0, color)` + `show()`.

Work section by section, following `circuit_schematic.md` **with the changes above applied**. Use hierarchical labels for cross-sheet nets (V_EXT_RAW, V_EXT_PROT, 5V_RAIL, GND).

**Step 4 — Power symbols and net labels**

- Add global power symbols: GND, +5V (5V_RAIL), +3V3
- Add net labels: V_EXT_RAW, V_EXT_PROT, PI_NODE, ADC_MON, DIVIDER_NODE (×6)

**Step 5 — Section 1: Single 5V input + ESD + RPP** *(simplified — USB-C dropped)*

- J4 (barrel 5.5×2.1mm DC-005): VIN+ → TVS_BAR (SMAJ5.0A) → D_BAR (1N5822) → V_EXT_RAW
- V_EXT_RAW → Q_RPP (**PJA3441** SOT-23 P-MOSFET, gate → R_RPP 100k → GND) → V_EXT_PROT
- ~~J_USB, R_CC1, R_CC2, TVS_USB, D_USB~~ — **REMOVED** (USB-C input dropped; ESP32-S3 module has onboard USB-C for programming/debug)

**Step 6 — Section 2: Schottky-OR power merge + pi filter** *(simplified — LTC4412 dropped)*

- External path: V_EXT_PROT → **D_EXT (1N5822 axial)** → PI_NODE
- Battery path: MT3608 OUT → **D_BOOST (1N5822 axial)** → PI_NODE
- Pi filter: C_PI (10µF) — L1 (10µH 1A axial) — C1 (220µF) + C2 (100nF) → 5V_RAIL
- LED1 (green) + R_LED1 (1k) → 5V_RAIL power indicator
- ~~U_IDEAL (LTC4412), Q_SWITCH (AO3401), R_GATE 100k, C_LTC 100nF~~ — **REMOVED**
- 5V_RAIL voltage on external power: **~4.6V** (V_EXT_PROT 4.95V − Vf 0.35V); on battery: ~4.65V (MT3608 5.0V − Vf 0.35V). Within ESP32-S3 5V tolerance and AMS1117 dropout headroom.

**Step 7 — Section 3: Battery charging**

- V_EXT_PROT → MOD_TP4056 (IN) → BAT+ → DW01A+FS8205A protection (on module) → **J5 (2.25mm female header)** ← LiPo cable plugs in here
- J5 BAT+ → MOD_MT3608 (IN) → MT3608 OUT → D_BOOST → PI_NODE
- MT3608 FB divider: R_MT_HI (300k) + R_MT_LO (100k), soldered to MT3608 FB pads → 5.0V fixed
- Battery monitor: LiPo BAT+ → R_MON1 (100k) → ADC_MON → R_MON2 (100k) → GND; C_ADC (100nF) on ADC_MON → **ESP32-S3 GPIO1 (J3 pin 4, ADC1_CH0)** — same channel number as classic ESP32 GPIO36 (ADC1_CH0), simplifies firmware port

**Step 8 — Section 4: Encoder connectors + signal conditioning (×6 channels)**

- J1 (KF301-4P, Theta): Pin 1=GND, 2=VCC, 3=A, 4=B
- J2 (KF301-4P, Phi): Pin 1=GND, 2=VCC, 3=A, 4=B
- J3 (**KF301-4P**, Wire): Pin 1=GND, 2=VCC, 3=A, 4=B  _(Z/index unused — not wired)_
- VCC pins: 5V_RAIL → **0Ω wire jumper at J_FB1/J_FB2/J_FB3 positions** → J1/J2/J3 VCC; C_VCC (100nF) at each connector
  - ⚠ Replaces ferrite beads (FB1/2/3). 0Ω jumper preserves full 5V at encoder (E40S6 needs ≥4.5 V at ~80 mA). Footprint sized for axial ferrite — drop in a real Murata BL01RN1A1D when sourced.
- Signal path (×6): Encoder out → R_TOP (10k) → DIVIDER_NODE → **TVS (flexible THT, populated)** → C_FILT (10nF C0G/NP0) → R_BOT (20k) → GND; DIVIDER_NODE → Schmitt input
  - **TVS populated, general THT part (TBD)** on `D_DO-201AD_P15.24mm` (takes DO-15 or DO-201 bodies). Pick bidirectional, V_RWM ≥ ~3.34 V (1.5KE3.9CA ideal/import; on-hand 1.5KE3.3CA works but leaks slightly). Not the mis-ordered P6KE39CA.

**Step 9 — Section 5: 74HC14 Schmitt trigger + ESP32-S3 GPIO mapping** *(confirmed pinout)*

- U_SCHM (74HC14 DIP-14, any HC variant): VCC pin 14 → 3.3V (from DevKitC-1 J1 pin 1 or 2), GND pin 7
- All 6 encoder GPIOs lie on J1 (left header), pins 4–9 — consecutive, ideal for routing the Schmitt output bus straight across.


| Schmitt pin (DIP-14) | Direction | Signal  | ESP32-S3 GPIO | DevKitC-1 header | Notes               |
| -------------------- | --------- | ------- | ------------- | ---------------- | ------------------- |
| 1 → 2                | 1A → 1Y   | Theta A | **GPIO4**     | J1 pin 4         | RTC, ADC1_CH3, free |
| 3 → 4                | 2A → 2Y   | Theta B | **GPIO5**     | J1 pin 5         | RTC, ADC1_CH4, free |
| 5 → 6                | 3A → 3Y   | Phi A   | **GPIO6**     | J1 pin 6         | RTC, ADC1_CH5, free |
| 9 → 8                | 4A → 4Y   | Phi B   | **GPIO7**     | J1 pin 7         | RTC, ADC1_CH6, free |
| 11 → 10              | 5A → 5Y   | Wire A  | **GPIO15**    | J1 pin 8         | RTC, ADC2_CH4, free |
| 13 → 12              | 6A → 6Y   | Wire B  | **GPIO16**    | J1 pin 9         | RTC, ADC2_CH5, free |


- ⚠ **R_GPIO12 (boot strapping pull-down) DROPPED**: ESP32-S3 strapping pins are GPIO 0/3/45/46. None of the chosen encoder GPIOs (4/5/6/7/15/16) is a strapping pin, so the boot-safety pull-down is no longer required.
- All 6 Schmitt inverters used. J3 pin 5 (Wire Z index pulse) is optional, has no conditioning circuit, and is not routed to the Schmitt.
- **N16R8 reserved pins (do NOT use)**: GPIO 35/36/37 (octal SPI flash/PSRAM internal). These appear on the J3 header but are not available for external use.
- **Firmware note**: Replace pin defines in `firmware/src/SphericalSensor.h`:
  ```cpp
  #define PIN_THETA_A     4
  #define PIN_THETA_B     5
  #define PIN_PHI_A       6
  #define PIN_PHI_B       7
  #define PIN_WIRE_A     15
  #define PIN_WIRE_B     16
  #define PIN_BATTERY_ADC 1   // ADC1_CH0 (was GPIO36)
  #define PIN_RGB_LED    38   // WS2812 onboard, replaces discrete LED2
  ```

**Step 10 — Section 6: ESP32-S3-DevKitC-1 + test points** *(final pinout)*

- U1 (**ESP32-S3-DevKitC-1 N16R8**) on **2× female socket headers, 1×22 each, 2.54 mm pin pitch, 22.86 mm row spacing** (board: 63.5 × 25.4 mm)
  - **5V_RAIL → J1 pin 21 (5V)**, **GND → J1 pin 22 (G) and J3 pin 1/21/22 (G)**
  - **3V3 (for U_SCHM VCC) → J1 pin 1 or pin 2 (3V3)** — onboard 5V→3.3V LDO supplies these
- **Dual USB-C on dev board** — preserve both:
  - Right (CH343p USB-to-UART) — primary programming/console port
  - Left (ESP32-S3 native USB-OTG via GPIO 19/20) — kept available; **GPIO 19/20 reserved, do not assign to other functions**
- ~~SW_RESET~~ — **DROPPED**: the DevKitC-1 has an onboard RST button which the enclosure must expose. Saves a BOM line and Zone D real estate.
- ~~LED2 + R_LED2~~ — **DROPPED**: battery-low indication driven via the **onboard WS2812 RGB LED on GPIO 38**. Firmware uses Adafruit_NeoPixel (or FastLED) to set color: green=≥80%, yellow=20–80%, red=<20%, blinking red=critical (<10%).
- **Test points (6 as-built):** TP1=5V_RAIL, TP2=3V3 (from J1 pin 1), TP3=MT3608 OUT, TP4=LiPo BAT+, TP5=BAT_OUT (TP4056 OUT+/MT3608 VIN+), TP6=GND.
- **As-built additions (not in the original Step 10 plan):**
  - **Two-button block** — J_SW1 (4-pin screw terminal: 1=GND, 2=BTN1, 3=BTN2, 4=3V3); R_SW1/R_SW2 (10k pull-ups) + C_SW1/C_SW2 (100nF debounce) on **BTN1 = GPIO17 (J1 pin 10)** and **BTN2 = GPIO18 (J1 pin 11)**.
  - **AUX expansion header** — J_EXP1 (2×6, 2.54 mm): pins 1/3/5/7 = AUX1–4 (each via 100Ω R_AUX1–4 to **GPIO11/12/13/14**, J1 pins 17–20), pin 9 = 3V3, pin 11 = +5V, even pins = GND.

**Step 11 — Run ERC, fix all errors**

- Accept: ERC "pin unconnected" warnings on unused Schmitt inputs (tie to GND per datasheet)
- Fix: any undriven power pins, missing power flags

---

## Phase 3 — PCB Layout (PCBnew)

**Step 12 — Board outline + mounting holes**

- Draw board edge: 120×80mm rectangle on Edge.Cuts layer
- Add 4× M3 mounting holes (3.2mm drill, no copper, 3mm inset from each corner)
- Add 3× copper fiducial dots (0.5mm circle, 0mm drill) at board corners

**Step 13 — Import netlist**

- Tools → Update PCB from Schematic (or import .netlist)
- Verify all footprints appear, no unmatched references

**Step 14 — Configure design rules (LPKF S63)**


| Rule                  | Value                     |
| --------------------- | ------------------------- |
| Min trace width       | 0.5mm                     |
| Min clearance         | 0.3mm (recommended 0.4mm) |
| Via drill             | 0.8mm                     |
| Via annular ring      | 0.6mm (pad 2.0mm)         |
| Copper pour clearance | 0.4mm                     |


Add net-class overrides:

- `PWR_EXT` (V_EXT_RAW, V_EXT_PROT): 3.0mm trace, 0.4mm clearance
- `PWR_5V` (5V_RAIL, MT3608 out, BAT+): 2.0mm trace
- `PWR_ENC_VCC` (Encoder VCC lines): 1.5mm trace
- `SIG` (all DIVIDER_NODE, GPIO signals): 0.8mm trace, max 50mm length

**Step 15 — Place components per zone**


| Zone                      | Footprint area                                                                                                          | Contents                                  |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| A (top-left, 55×35mm)     | J4, TVS_BAR, D_BAR, Q_RPP (PJA3441), D_EXT, D_BOOST, L1, C_PI, C1, C2, LED1, R_LED1                                     | Single 5V input + Schottky-OR + pi filter |
| B (top-right, 65×35mm)    | MOD_TP4056, MOD_MT3608, J5 (2.25mm fem), R_MON1/2, C_ADC                                                                | Battery + charging + boost                |
| C (bottom-left, 60×45mm)  | J1 (4P), J2 (4P), J3 (4P), J_FB1/2/3 (0Ω jumpers), C_VCC×3, R_TOP×6, R_BOT×6, C_FILT×6, TVS×6 (populated, flexible THT) | Encoder connectors + signal conditioning  |
| D (bottom-right, 70×30mm) | U_SCHM (74HC14 DIP-14), U1 socket (2× 1×22 fem hdrs, 22.86mm row spacing, 63.5×25.4mm board outline), TP1–TP6, J_SW1 + R_SW1/2 + C_SW1/2 (buttons), J_EXP1 + R_AUX1–4 (AUX header) | Schmitt trigger + ESP32-S3-DevKitC-1 + switches/AUX |


**Zone D orientation**: DevKitC-1 footprint (63.5 × 25.4 mm + clearance for both USB-C connectors protruding from the short edge) needs ~70 × 30 mm. Orient the DevKitC-1 with its long axis along the longer board edge (X direction); the dual USB-C connectors face the **short edge** of the PCB so cables plug in from outside the enclosure. Zone A shrinks to ~45 × 35 mm (freed by removed USB-C / LTC4412 / Q_SWITCH); Zone B reclaims a few mm² (LED2/R_LED2 dropped). SW_RESET removed from Zone D.

**Step 16 — Route power traces (priority order)**

1. GND (bottom pour — do last, but plan clearances now)
2. V_EXT_RAW / V_EXT_PROT — 3.0mm, shortest path Zone A
3. 5V_RAIL — 2.0mm, main trunk Zone A→D
4. LiPo BAT+ — 2.0mm, Zone B internal
5. Encoder VCC (post-J_FB jumpers) — 1.5mm, Zone C
6. 3.3V from DevKitC-1 J1 pin 1 → U_SCHM pin 14 — 0.8mm (low current)

**Step 17 — Route signal traces**

- All DIVIDER_NODE → Schmitt inputs: 0.8mm, keep <50mm, avoid crossing power traces
- Schmitt outputs → ESP32-S3 GPIO 4/5/6/7/15/16 (J1 pins 4–9): 0.8mm, direct bus routing in Zone D
- ADC_MON → GPIO1 (J3 pin 4): 0.8mm, short run between Zone B and Zone D right side

**Step 18 — Add GND copper pour**

- Bottom layer, 0.4mm clearance to all pads/traces
- Stitch to GND net via 2–3 wire-link vias (tinned wire, solder both sides) per isolated island
- Check for isolated GND islands and add wire-links as needed

**Step 19 — Silkscreen**

- Reference designators (top silkscreen): keep outside pads, readable after assembly
- Connector labels: J1=THETA, J2=PHI, J3=WIRE, J4=5V_IN, J5=LIPO, J6=BENCH_5V
- TVS×6 are populated (general THT, part TBD) — no DNP silkscreen needed
- Add **0Ω** silkscreen marks at J_FB1/J_FB2/J_FB3 jumper positions to flag wire-link assembly
- Test point labels: TP1=5V, TP2=3V3, TP3=BOOST, TP4=BAT+, TP5=BAT_OUT, TP6=GND
- Board info: "EVKA 5V v2" + date + rev on top silkscreen

**Step 20 — Run DRC, fix all violations**

- No clearance violations (target: 0 errors)
- No unrouted nets (target: 0 ratsnest lines)
- Accepted: LPKF fiducials may trigger "non-copper pad" informational warnings

---

## Phase 4 — Output Files

**Step 21 — Export Gerbers**

21.1 In PCBnew, File → Plot
21.2 Output directory: `pcb_design/EVKA_position_v2/gerbers/`
21.3 Plot format: Gerber
21.4 Layers to plot:
   - F.Cu (top copper)
   - B.Cu (bottom copper, GND pour)
   - F.Silkscreen (reference for hand assembly — LPKF won't print, but useful for review)
   - Edge.Cuts (board outline)
21.5 General Options: leave defaults (Use Protel filename extensions = OFF, Subtract solder mask from silkscreen = OFF for milled boards)
21.6 Gerber Options: 4.6 unit format, mm
21.7 Click "Plot" — confirm 4 .gbr files appear in the gerbers/ folder

**Step 22 — Export drill file**

22.1 Same Plot dialog → "Generate Drill Files"
22.2 Drill File Format: **Excellon**
22.3 Units: mm
22.4 Zeros format: Decimal
22.5 Drill origin: Drill/place file origin (or Absolute, your choice — must be consistent for the LPKF)
22.6 Map output format: Gerber X2 (drill map for visual review)
22.7 Click "Generate Drill File" → confirm `.drl` and `.gbr` (drill map) files appear

**Step 23 — Verify in Gerber viewer**

23.1 Tools → Gerber Viewer
23.2 File → Open Gerber files… → select all 4 .gbr files
23.3 File → Open Excellon Drill File… → load the .drl
23.4 Toggle layers individually:
   - F.Cu only: trace layout matches schematic intent (no gaps in power traces, no missing nets)
   - B.Cu only: GND pour fills cleanly, no isolated copper islands, no necking around pads
   - Edge.Cuts only: board outline is a closed polygon, mounting holes are visible
   - All overlaid: drill holes line up with pad centers; nothing crosses the board edge
23.5 Compare to the LPKF S63 minimum-feature checklist (`pcb_layout_guide.md`):
   - Min trace width: 0.5 mm everywhere (DRC should have caught this — re-verify visually)
   - Min isolation: 0.4 mm everywhere
   - All vias are 0.8 mm drill / 2.0 mm pad

**Step 24 — Hand-off package**

24.1 Zip the gerbers/ folder
24.2 Include `pcb_layout_guide.md`, this `KICAD_PLAN_DETAILED.md`, and a screenshot of the F.Cu+B.Cu+Edge.Cuts overlay
24.3 If sending to a third-party LPKF operator, also include a one-page README with:
   - Material: FR4, 1.55 mm thick, 18 µm copper, 2-layer
   - No solder mask, no silkscreen print
   - Drill: Excellon, mm, decimal zeros
   - Tooling: LPKF S63 mechanical mill
   - Special: 4× M3 mounting holes (3.2 mm drill); 3× 0.5 mm copper fiducials (no drill)

---

## Component Selection — BOM with Alternatives

Each functional role lists the **original** (1st choice) part and **2–3 alternatives**. After ordering, fill in the **ORDERED** field with what you actually procured so the schematic/footprint can be matched to the real part. TR-stock notes use suppliers from previous research: direnc.net, robotistan.com, motorobit.com, ozdisan.com, ersinelektronik.com.

---

### Procurement Quick-Scan


| #   | Role                                | RefDes                | Original             | Best TR Substitute                          | Must Import?            |
| --- | ----------------------------------- | --------------------- | -------------------- | ------------------------------------------- | ----------------------- |
| 1   | DC barrel jack 5.5×2.1mm THT        | J4                    | DC-005 generic       | DC-005 (direnc.net)                         | No                      |
| 2   | USB-C female THT                    | J_USB                 | HRO TYPE-C-31-M-12   | —                                           | **Yes (LCSC)**          |
| 3   | TVS 5V SMA (×2)                     | TVS_USB, TVS_BAR      | SMAJ5.0A             | SMAJ5.0A (ozdisan), 1.5KE6.8A axial         | No                      |
| 4   | Schottky 3A/40V axial (×3)          | D_USB, D_BAR, D_BOOST | 1N5822-HT            | 1N5822 / SR340 / SK34 (direnc.net)          | No                      |
| 5   | P-MOSFET SOT-23 (×2)                | Q_RPP, Q_SWITCH       | AO3401               | PJA3441 / IRLML6402 / SI2301                | No                      |
| 6   | Ideal-diode controller              | U_IDEAL               | LTC4412              | LM66100 (TI) — needs layout change          | **Yes (LCSC)**          |
| 7   | 10µH ≥1A radial inductor            | L1                    | Bourns RLB0914-100KL | Generic 10µH 1A radial (direnc.net 9.71 TL) | No                      |
| 8   | TP4056 charger module               | MOD_TP4056            | TP4056+DW01A combo   | IP5306 module / TP5100 (alt designs)        | No (watch restock)      |
| 9   | Boost converter module              | MOD_MT3608            | MT3608 adjustable    | XL6009 / SX1308 / pre-fixed 5V              | No                      |
| 10  | Hex Schmitt trigger DIP-14          | U_SCHM                | SN74HC14N (TI)       | MM74HC14N / MC74HC14AN / CD40106BE          | No                      |
| 11  | Bidirectional TVS, general THT (×6) | TVS×6                 | part TBD (flexible THT) | on-hand 1.5KE3.3CA / 1.5KE3.9CA (import)  | On-hand / TBD           |
| 12  | Ferrite bead axial 600Ω@100MHz (×3) | FB1, FB2, FB3         | Murata BL01RN1A1D    | 10Ω 1/4W resistor substitute                | No (with substitute)    |
| 13  | ESP32 module UNO form               | U1                    | Wemos D1 R32         | ESPDUINO-32 (UNO) / DevKitC v4 (re-layout)  | No (watch restock)      |
| 14  | LiPo connector 2-pin                | J5                    | JST-PH 2.0mm         | JST-XH 2.5mm (different pitch)              | No                      |
| 15  | Screw terminal 4P 5mm               | J1, J2, J3            | KF301-4P             | Phoenix MKDS 1,5/4 (×10 cost)               | No (all 3 use 4P — Z unused) |
| 16  | Tactile button 6×6mm                | SW_RESET              | Generic 6×6mm 4-pin  | Omron B3F / Alps SKHH                       | No                      |


---

### Detailed Alternatives — Hard Parts

#### 1 — DC Barrel Jack (J4)


| Choice   | Part                     | Package   | Spec             | TR                            | Notes                              |
| -------- | ------------------------ | --------- | ---------------- | ----------------------------- | ---------------------------------- |
| Original | DC-005 generic 5.5×2.1mm | THT 3-pin | center+, ~5A     | Y (direnc, robotistan, ersin) | Industry standard                  |
| Alt 1    | JEC / XKB DC-005-2.1     | THT 3-pin | center+, ~5A     | Y                             | Drop-in same footprint             |
| ⚠ Avoid  | CUI PJ-102A              | THT       | 5.5×**2.0**mm ID | —                             | Plug fits loosely, 0.1mm undersize |
| ⚠ Avoid  | Switchcraft 712A         | THT       | 5.5×**2.5**mm ID | —                             | Wrong pin diameter                 |


**ORDERED:** DC-005 generic 5.5×2.1mm

---

#### 2 — USB-C Female THT (J_USB)


| Choice   | Part               | Package    | Spec                     | TR  | Notes                       |
| -------- | ------------------ | ---------- | ------------------------ | --- | --------------------------- |
| Original | HRO TYPE-C-31-M-12 | 16-pin THT | 1A VBUS, 1.6mm board     | N   | LCSC C165948                |
| Alt 1    | HRO TYPE-C-31-M-14 | 16-pin THT | Same family, deeper seat | N   | LCSC, drop-in for M-12      |
| Alt 2    | GCT USB4085-GF-A   | 6-pin THT  | 1.5A VBUS, power+CC only | N   | All pins fully through-hole |
| Alt 3    | Jing C-24M-Q-T-1   | 24-pin THT | 5A VBUS, full pinout     | N   | LCSC C46407                 |


**This must be imported (LCSC) — no Turkish supplier carries THT USB-C.**

**ORDERED:** _________________

---

#### 3 — TVS at 5V Input (TVS_USB, TVS_BAR — ×2)


| Choice   | Part      | Package        | Spec                                     | TR                                      | Notes                        |
| -------- | --------- | -------------- | ---------------------------------------- | --------------------------------------- | ---------------------------- |
| Original | SMAJ5.0A  | DO-214AC (SMA) | 400W, Vc=[6.7V@43.5A](mailto:6.7V@43.5A) | Y (direnc 4.17 TL, ozdisan multi-brand) | Vishay/Littelfuse            |
| Alt 1    | SMBJ5.0A  | DO-214AA (SMB) | 600W, Vc=9.2V@65A                        | Y likely                                | Larger pad                   |
| Alt 2    | P4SMA5.0A | DO-214AC (SMA) | 400W, drop-in                            | Y likely                                | Vishay                       |
| Alt 3    | 1.5KE6.8A | DO-201 axial   | 1500W, Vc=10.5V                          | Y likely (ersinelektronik)              | All-THT option, looser clamp |


**ORDERED:** SMAJ5.0A

---

#### 4 — Schottky Diode 40V 3A axial (D_BAR, D_USB, D_BOOST — ×3 + 1 spare)

⚠ **BOM labeling fix**: BOM lists "SS34" with package "DO-201". SS34 is actually SMD (DO-214AC). The correct **axial DO-201** part for 3A/40V is **1N5822**. Use 1N5822 for axial positions.


| Choice   | Part                         | Package        | Spec                   | TR                                   | Notes                                      |
| -------- | ---------------------------- | -------------- | ---------------------- | ------------------------------------ | ------------------------------------------ |
| Original | 1N5822 / 1N5822-HT (Hottech) | DO-201AD axial | 3A, 40V, Vf=0.525V@3A  | Y (direnc, 99,999 in stock, 5.31 TL) |                                            |
| Alt 1    | SR340 / SK34                 | DO-201AD axial | 3A, 40V, Vf=0.55V      | Y (direnc, robotistan, ersin)        | Generic clone                              |
| Alt 2    | MBR340 (ON Semi)             | DO-201AD axial | 3A, 40V, Vf=0.50V      | Y likely (ozdisan)                   | Slightly lower Vf                          |
| Alt 3    | 1N5819                       | DO-41 axial    | 1A, 40V — smaller body | Y everywhere                         | Use only if path <1A (USB path acceptable) |


**ORDERED:** 1N5822

---

#### 5 — P-channel MOSFET SOT-23 (Q_RPP, Q_SWITCH — ×2)


| Choice   | Part                 | Package | Vds / Id / Rds    | TR                                      | Notes                            |
| -------- | -------------------- | ------- | ----------------- | --------------------------------------- | -------------------------------- |
| Original | AO3401 / AO3401A     | SOT-23  | −30V, −4A, 69mΩ   | Y (direnc, robotistan)                  | Alpha & Omega                    |
| Alt 1    | **PJA3441** (Panjit) | SOT-23  | −40V, −3.1A, 74mΩ | **Y (direnc 99,999 in stock, 4.99 TL)** | Confirmed substitute, higher Vds |
| Alt 2    | IRLML6402 (Infineon) | SOT-23  | −20V, −3.7A, 65mΩ | Y likely                                | Vgs(th) low; OK for 5V circuit   |
| Alt 3    | SI2301 (Vishay)      | SOT-23  | −20V, −2.3A, 85mΩ | Y (direnc)                              | Lower current, sufficient at 1A  |
| Alt 4    | NTR4101P (ON Semi)   | SOT-23  | −20V, −4.2A, 60mΩ | Y likely                                | High-performance swap            |


**ORDERED:** **PJA3441**

---

#### 6 — Ideal Diode Controller (U_IDEAL)


| Choice       | Part                                 | Package  | Spec                                   | TR  | Notes                                            |
| ------------ | ------------------------------------ | -------- | -------------------------------------- | --- | ------------------------------------------------ |
| Original     | LTC4412 (ADI)                        | SOT-23-6 | 2.5–28V, ext. P-MOSFET, 11µA Iq        | N   | **No domestic stock — must import**              |
| Alt 1        | LM66100 (TI)                         | SC-70-5  | 1.5–5.5V, **integrated FET 1.5A 79mΩ** | N   | Removes Q_SWITCH; layout change needed           |
| Alt 2        | TPS2117 (TI)                         | SOT-23-6 | Dual-input mux, 5.5V, 1.5A             | N   | Different function — power mux not OR controller |
| Alt 3        | MAX38888 (Maxim)                     | SOT-23-6 | 4.5–18V, ext. MOSFET                   | N   | Closest functional drop-in                       |
| ⚙ Workaround | Two 1N5822 Schottkys + no controller | DO-201   | 0.4V drop (vs 20mV)                    | Y   | All-domestic, efficiency penalty                 |


**This must be imported (LCSC) OR redesigned with two Schottkys.**

**ORDERED:** Two 1N5822 Schottkys + no controller

---

#### 7 — Power Inductor 10µH ≥1A radial THT (L1)


| Choice   | Part                              | Package         | Spec                  | TR                                      | Notes                  |
| -------- | --------------------------------- | --------------- | --------------------- | --------------------------------------- | ---------------------- |
| Original | Bourns RLB0914-100KL              | Radial 8.6×12mm | 10µH, 2.7A Isat, 48mΩ | Y likely (ozdisan)                      | Premium                |
| Alt 1    | **Generic 10µH 1A radial (ABCO)** | Radial THT      | 10µH, 1A              | **Y (direnc 9.71 TL, 99,999 in stock)** | Adequate for 0.5A rail |
| Alt 2    | Würth 744771110                   | Radial 10×12mm  | 10µH, 1.5A            | N                                       | Verify pitch           |
| Alt 3    | Generic DR74 drum inductor        | Radial THT      | 10µH, ≥1A             | Y (robotistan)                          | Hobby-grade, fine      |


**ORDERED:** 10UH 1A Kondansatör Tipi Bobin

---

#### 8 — TP4056 LiPo Charger Module (MOD_TP4056)


| Choice   | Part                                 | Spec                                                        | TR                                                                | Notes                                              |
| -------- | ------------------------------------ | ----------------------------------------------------------- | ----------------------------------------------------------------- | -------------------------------------------------- |
| Original | TP4056+DW01A+FS8205A combo module    | 1A charge, 1S LiPo, USB-micro/Type-C, integrated protection | Y (direnc, robotistan, robolinkmarket — restocks every 2–4 weeks) | Verify R_PROG=1.2kΩ for 1A                         |
| Alt 1    | TP4056 with Type-C input             | Same chipset, USB-C jack                                    | Y                                                                 | Most modern variant                                |
| Alt 2    | MCP73831T bare chip + DW01A discrete | 500mA charge, smaller                                       | Y likely                                                          | Halve charge current; build protection separately  |
| Alt 3    | IP5306 module                        | 2.4A charge + 5V/2.1A boost integrated                      | Y likely                                                          | All-in-one but USB-A port output, different pinout |
| Alt 4    | TP5100 module                        | 1S/2S selectable, 2A                                        | Y likely                                                          | More headroom                                      |


**ORDERED:** TP4056+DW01A+FS8205A combo module

---

#### 9 — Boost Converter Module (MOD_MT3608)


| Choice   | Part                                          | Spec                                        | TR                                      | Notes                                 |
| -------- | --------------------------------------------- | ------------------------------------------- | --------------------------------------- | ------------------------------------- |
| Original | **MT3608 adjustable** (modify FB to fixed 5V) | 2A switch, 28V max out, 2–24V adj           | **Y (direnc 20.49 TL, 4,948 in stock)** | Apply R_MT_HI=300k + R_MT_LO=100k mod |
| Alt 1    | SX1308 module                                 | Pin-compatible MT3608 clone, same procedure | Y                                       | Often sold as "MT3608"                |
| Alt 2    | XL6009E1 module                               | 4A switch, 5–32V out, larger                | Y (direnc)                              | Better thermals at heavy load         |
| Alt 3    | PAM2401 / IP2301 fixed-5V boost module        | Pre-set 5V, 1–1.5A, no modification         | Y likely                                | Skip the resistor-mod step            |


**ORDERED:** MT3608

---

#### 10 — Hex Schmitt Trigger DIP-14 (U_SCHM)


| Choice   | Part         | Mfr               | Spec                           | TR                                           | Notes                                             |
| -------- | ------------ | ----------------- | ------------------------------ | -------------------------------------------- | ------------------------------------------------- |
| Original | SN74HC14N    | TI                | DIP-14, 2–6V, 6-ch Vt+≈1.6V    | Y (direnc, ozdisan, ersinelektronik, f1depo) | Currently OOS at majors — try secondary suppliers |
| Alt 1    | 74HC14N,652  | Nexperia          | Drop-in identical              | Y likely (ersin, arkotek)                    | Pin-compatible                                    |
| Alt 2    | MM74HC14N    | Fairchild/ON Semi | Drop-in identical              | Y likely                                     | Brand alternate                                   |
| Alt 3    | MC74HC14AN   | ON Semi           | Drop-in identical              | Y likely                                     | Brand alternate                                   |
| ⚠ Caveat | 74HC**T**14N | any               | TTL inputs — needs 5V supply   | —                                            | NOT recommended at 3.3V                           |
| ⚠ Slow   | CD40106BE    | TI                | 3–18V, ~60ns delay (5× slower) | Y (direnc)                                   | Works for low-freq encoders, wider hysteresis     |


**ORDERED:** 74HC14

---

#### 11 — Bidirectional TVS DO-201 ~3.3–3.9V (TVS ×6 — encoder ESD)


| Choice   | Part                             | Package      | Vrwm / Vc           | TR                 | Notes                                                         |
| -------- | -------------------------------- | ------------ | ------------------- | ------------------ | ------------------------------------------------------------- |
| Original | 1.5KE3.9CA                       | DO-201 axial | 3.34V / 6.2V, 1500W | N — must import    | LCSC C17166                                                   |
| Alt 1    | **P6KE3.9CA**                    | DO-15 axial  | 3.34V / 6.2V, 600W  | Y likely (direnc)  | Smaller body, same Vrwm — recommended TR sub                  |
| Alt 2    | SMBJ3V6CA                        | DO-214AA SMD | 3.6V / 5.8V, 600W   | Y likely (ozdisan) | Layout change to SMD pads                                     |
| ⚠ Avoid  | 1.5KE3.3CA                       | DO-201 axial | 2.83V / 5.3V        | —                  | **Reverts the 2026-04-30 fix** — leakage on 3.3V divider HIGH |
| ⚙ Skip   | Omit — rely on resistive divider | —            | —                   | —                  | Acceptable for non-ESD-critical builds                        |


**ORDERED:** **P6KE300A -HT**

---

#### 12 — Ferrite Bead 600Ω@100MHz Axial THT (FB1, FB2, FB3 — ×3)


| Choice           | Part                                 | Package     | Spec                | TR                         | Notes                                          |
| ---------------- | ------------------------------------ | ----------- | ------------------- | -------------------------- | ---------------------------------------------- |
| Original         | Murata BL01RN1A1D                    | DO-34 axial | 600Ω@100MHz, 200mA  | N                          | LCSC / Mouser                                  |
| Alt 1            | Laird HI1206T601R-10                 | Axial       | 600Ω@100MHz         | N                          | Equivalent                                     |
| Alt 2            | TDK MMZ1608Y601B SMD 0603            | SMD 0603    | 600Ω@100MHz         | Y likely (ozdisan)         | Layout change to SMD pads                      |
| ⚙ **Substitute** | **10–22Ω 1/4W resistor + 100nF cap** | THT         | LC filter, low-freq | **Y (direnc — universal)** | Functional for encoder VCC; loses HF rejection |


**Engineering note:** Encoders run at <10kHz signaling; the ferrite is mainly for HF EMI rejection. A series 10Ω resistor + the existing 100nF C_VCC bypass approximates the LC filter behavior adequately.

**ORDERED:** **10–22Ω 1/4W resistor + 100nF cap**

---

#### 13 — ESP32 Module (U1)


| Choice   | Part             | Form factor                | TR                                                        | Notes                         |
| -------- | ---------------- | -------------------------- | --------------------------------------------------------- | ----------------------------- |
| Original | Wemos D1 R32     | UNO R3 (15+19 pin sockets) | Y (direnc 323 TL OOS, robotistan OOS, Trendyol resellers) | Drop-in for current footprint |
| Alt 1    | ESPDUINO-32      | UNO R3 (same as D1 R32)    | Y likely                                                  | Pin-compatible                |
| Alt 2    | ESP32 DevKitC v4 | 38-pin (2×19)              | Y (direnc, robotistan)                                    | **Requires PCB re-layout**    |
| Alt 3    | NodeMCU-32S      | 38-pin (2×19)              | Y likely                                                  | **Requires PCB re-layout**    |


**ORDERED:** ESP32 S3 N16R8 WiFi Bluetooth Board

---

#### 14 — LiPo Battery Connector (J5)


| Choice   | Part                               | Pitch      | TR                        | Notes                                  |
| -------- | ---------------------------------- | ---------- | ------------------------- | -------------------------------------- |
| Original | JST PH 2-pin male PCB (S2B-PH-K-S) | 2.0mm      | Y (motorobit, robotistan) | Match LiPo cable connector             |
| Alt 1    | JST XH 2-pin male                  | 2.5mm      | Y (direnc, robotistan)    | **Different pitch — change footprint** |
| Alt 2    | JST ZH 2-pin male                  | 1.5mm      | Y likely                  | Smaller, less common                   |
| Alt 3    | KF128 2-pin screw terminal         | 2.54/3.5mm | Y                         | Bench-only, polarity-error risk        |


**Order tip:** Verify your LiPo cell's connector pitch before ordering. JST-PH is the most common for 1S LiPo hobby cells.

**ORDERED:** S2B-PH-K-S and also 2.25mm 2 Pin JST Dişi Konnektör - My lipo has male output

---

#### 15 — Screw Terminals 5mm pitch (J1, J2, J3)


| Choice   | Part                                     | Pitch | TR                                                             | Notes                      |
| -------- | ---------------------------------------- | ----- | -------------------------------------------------------------- | -------------------------- |
| Original | KF301-4P / KF301-5P                      | 5.0mm | Y for 4P (direnc, motorobit, robolinkmarket); 5P OOS at direnc | KF301 blocks snap together |
| Alt 1    | **KF301-2P + KF301-3P ganged** for 5-pin | 5.0mm | **Y (motorobit KF301-3P)**                                     | Substitute when 5P OOS     |
| Alt 2    | Phoenix Contact MKDS 1,5/4 + MKDS 1,5/5  | 5.0mm | Y (ozdisan)                                                    | Drop-in but ~10× cost      |
| Alt 3    | Wago 257-404 / 257-405 spring-cage       | 5.0mm | Y likely                                                       | Same PCB pattern, push-in  |


**ORDERED:** ~~KF301-2P + KF301-3P ganged for 5-pin~~ → **superseded 2026-06-19: J3 is a single KF301-4P** (wire encoder Z/index unused, so only GND/VCC/A/B needed — identical to J1/J2). The 5-pin sourcing problem no longer applies.

---

#### 16 — Tactile Reset Button (SW_RESET)


| Choice   | Part                    | Spec                  | TR                                | Notes         |
| -------- | ----------------------- | --------------------- | --------------------------------- | ------------- |
| Original | Generic 6×6mm 4-pin THT | h=4.3 or 5mm          | Y (direnc, robotistan everywhere) | Buy whichever |
| Alt 1    | Omron B3F-1020          | 6×6mm, 1.57N, premium | Y (ozdisan)                       | Long life     |
| Alt 2    | Alps SKHHAMA010         | 6×6mm, 1.57N          | Y likely                          | Drop-in       |
| Alt 3    | TE 1825910-1            | 6×6mm, 1.6N           | Y likely                          | Drop-in       |


**ORDERED:** 6x6 6mm Tach Buton (4 Bacak)

---

### Engineering Flags Carried Over From Component Audit

1. **BOM labeling**: original BOM listed Schottkys as "SS34" with package "DO-201" — SS34 is SMD. Axial DO-201 part is **1N5822**. ✅ reconciled in this plan.
2. **74HCT14N is NOT a substitute for 74HC14N** at 3.3V — TTL inputs require 5V supply. Stick to 74HC (CMOS) variants.
3. **TVS part choice (updated 2026-06-19):** the footprint is general THT (`D_DO-201AD_P15.24mm`), part TBD. `1.5KE3.9CA` (V_RWM 3.34 V) is the ideal/no-leak choice but import-only. The on-hand **`1.5KE3.3CA`** (V_RWM ~2.82 V) is accepted for this build — it lightly clamps/leaks at the 3.33 V HIGH (flagged in the 2026-04-30 review) but works on this exact divider (proven on the old 5 V board; 74HC14 threshold ~2.3 V gives margin). Avoid lower-V_RWM parts.
4. **Ferrite substitute correction**: earlier "10–22Ω resistor" suggestion was electrically wrong (drops 0.8 V at 80 mA encoder current → E40S6 brown-out). Correct substitute is **0Ω jumper** (matches ferrite DC R < 0.5Ω). C_VCC bypass at the connector preserves local HF filtering.
5. **5V_RAIL voltage regression**: dropping LTC4412 changed external-power 5V_RAIL from 4.98 V to ~4.6 V (one Schottky drop). Still within ESP32-S3 5V tolerance (3.0–5.5 V) and the AMS1117-3.3 dropout (3.6 V min input for clean 3.3 V out). No firmware change needed.
6. **Encoder ESD coverage**: TVS×6 are now **populated** (general THT, part TBD), closing the earlier DNP coverage gap — each divided node has a clamp in addition to the 10 kΩ R_TOP series limiting.

---

## Quick Reference: Net Names


| Net            | Width | Source                        |
| -------------- | ----- | ----------------------------- |
| V_EXT_RAW      | 3.0mm | Post-TVS_BAR / D_BAR          |
| V_EXT_PROT     | 3.0mm | Post-Q_RPP                    |
| PI_NODE        | 2.0mm | Schottky-OR junction (D_EXT ‖ D_BOOST), pre-L1 |
| 5V_RAIL        | 2.0mm | Post-pi-filter (≈4.6 V)       |
| LiPo BAT+      | 2.0mm | J5 pin 1                      |
| Encoder VCC    | 1.5mm | Post-J_FB jumper              |
| DIVIDER_NODE_x | 0.8mm | Signal conditioning           |
| GPIO 4/5/6/7/15/16 | 0.8mm | Schmitt out → DevKitC-1 J1 pins 4–9 |
| ADC_MON (GPIO1) | 0.8mm | Battery divider → DevKitC-1 J3 pin 4 |


## Key Components Needing Custom Symbols/Footprints *(updated post-procurement)*


| Part                                  | Package      | Note                                                                                     |
| ------------------------------------- | ------------ | ---------------------------------------------------------------------------------------- |
| PJA3441 (Q_RPP)                       | SOT-23       | Generic PFET symbol works                                                                |
| 74HC14                                | DIP-14       | Standard KiCad `74xx` library                                                            |
| ESP32-S3-DevKitC-1 N16R8              | 2×22 hdr THT | Confirmed: 22.86mm row spacing, 63.5×25.4mm board, 2.54mm pin pitch — Espressif official |
| KF301-2P / 4P                         | THT 5mm      | Standard screw terminal, 5mm pitch (J6 = 2P; J1/J2/J3 = 4P; 3P no longer used)           |
| 2.25mm 2-pin female header            | THT non-std  | Custom footprint — match direnc.net part exactly                                         |
| MOD_TP4056                            | Module       | Treat as 6-pad THT module (verify pinout per ordered board)                              |
| MOD_MT3608                            | Module       | Treat as 4-pad THT module                                                                |
| TVS (×6)                              | DO-201AD flex| `D_DO-201AD_P15.24mm` — **populated**, general THT (part TBD); takes DO-15 or DO-201 body |
| J_FB1/J_FB2/J_FB3 (×3)                | THT axial    | 0Ω wire jumper now; sized for axial ferrite future retrofit                              |
| ~~LTC4412, Q_SWITCH, R_GATE, C_LTC, USB-C THT, ferrite axial, SW_RESET, LED2, R_LED2, R_GPIO12~~ | — | **Removed from BOM** — no symbols/footprints needed                  |


---

## Open Items — Final Decisions (2026-05-08)

All design questions are now resolved. The single physical verification still needed is the J5 connector pitch.

| # | Item | Decision |
|---|------|----------|
| 1 | ESP32-S3 pinout | ✅ Locked — Espressif DevKitC-1 N16R8, GPIO 4/5/6/7/15/16/1/38 |
| 2 | J5 footprint pitch | Design at **2.25 mm as labeled by direnc.net**; user must verify with calipers when part arrives — if actual is 2.0 (JST PH) or 2.5 (JST XH), open the footprint and edit pad spacing before exporting Gerbers |
| 3 | Encoder TVS×6 | **Populated** — general THT TVS, flexible `D_DO-201AD_P15.24mm` footprint, exact part TBD (bidir, V_RWM ≥ ~3.34 V) |
| 4 | R_VCC value | ✅ **0Ω wire jumper** (was 10–22Ω suggestion — overruled because 10Ω drops 0.8 V at 80 mA, browns out E40S6) |
| 5 | SW_RESET | ✅ **Dropped** — DevKitC-1 onboard RST button is sufficient |
| 6 | LED2 | ✅ **Dropped** — drive onboard WS2812 RGB LED (GPIO38) instead |
| 7 | Firmware port | Add `[env:esp32-s3-devkitc-1]` to `platformio.ini`; update pin defines in `firmware/src/SphericalSensor.h` (see Step 9) |
| 8 | Battery LED protocol | WS2812 single-wire (800 kHz, GRB ordering) — use `Adafruit_NeoPixel` library |

---

## Appendix A — Final BOM (post-procurement)

| RefDes | Part | Value / Description | Package | Qty | Source / Note |
|---|---|---|---|---|---|
| **Power input** | | | | | |
| J4 | DC Barrel jack DC-005 | 5.5×2.1 mm, center-positive | THT | 1 | direnc.net |
| TVS_BAR | SMAJ5.0A | Unidir 5V, 400W | DO-214AC (SMA) | 1 | direnc.net / ozdisan |
| D_BAR | 1N5822-HT | 40V/3A Schottky | DO-201 axial | 1 | direnc.net (Hottech) |
| Q_RPP | PJA3441 | P-MOSFET, −40V, −3.1A, 74mΩ | SOT-23 | 1 | direnc.net (Panjit) |
| R_RPP | 100 kΩ | 1% 1/4W metal film | THT | 1 | |
| **Schottky-OR + pi filter** | | | | | |
| D_EXT | 1N5822-HT | External path OR | DO-201 axial | 1 | direnc.net |
| D_BOOST | 1N5822-HT | Battery path OR | DO-201 axial | 1 | direnc.net |
| L1 | 10 µH 1A radial | Pi-filter inductor | THT axial/radial | 1 | direnc.net (ABCO) |
| C_PI | 10 µF / 10V | Pre-L1 cap | THT radial | 1 | |
| C1 | 220 µF / 10V | Post-L1 bulk + ground star | THT radial | 1 | direnc.net |
| C2 | 100 nF | 5V_RAIL bypass | THT 5mm | 1 | |
| LED1 | Green LED | Power-on indicator | THT 5mm | 1 | |
| R_LED1 | 1 kΩ | LED1 limiter | THT | 1 | |
| J6 | Phoenix MKDS-1,5-2 (5.0mm) | Bench 5V test input | THT | 1 | as-built MKDS 5.0mm; KF301-2P pad-compatible |
| **Battery / charging** | | | | | |
| MOD_TP4056 | TP4056+DW01A+FS8205A | 1S LiPo charger + protection (1A) | Module | 1 | direnc.net / robotistan / robolinkmarket |
| MOD_MT3608 | MT3608 boost (modified) | Fixed 5.0V output (FB mod) | Module | 1 | direnc.net |
| R_MT_HI | 300 kΩ | MT3608 FB upper (on module) | THT | 1 | direnc.net |
| R_MT_LO | 100 kΩ | MT3608 FB lower (on module) | THT | 1 | direnc.net |
| C_BOOST | 22 µF / 10V | MT3608 output hold-up | THT radial | 1 | |
| J5 | JST-PH 2.0 mm 2-pin | LiPo connector (cable is male) | THT | 1 | as-built footprint = JST_PH 2.0mm; verify against your cell's connector pitch |
| BAT1 | 1S LiPo 2000 mAh | External cell, mating male connector | — | 1 | hobby shop |
| R_MON1 | 100 kΩ | Battery ADC divider upper | THT | 1 | |
| R_MON2 | 100 kΩ | Battery ADC divider lower | THT | 1 | |
| C_ADC | 100 nF | GPIO1 ADC bypass | THT 5mm | 1 | |
| **Encoder signal conditioning (×6)** | | | | | |
| J1 | Phoenix MKDS-1,5-4 (5.0mm) | Theta encoder (GND/VCC/A/B) | THT 5mm | 1 | as-built MKDS; KF301-4P pad-compatible |
| J2 | Phoenix MKDS-1,5-4 (5.0mm) | Phi encoder | THT 5mm | 1 | as-built MKDS; KF301-4P pad-compatible |
| J3 | Phoenix MKDS-1,5-4 (5.0mm) | Wire encoder (GND/VCC/A/B; Z unused) | THT 5mm | 1 | as-built MKDS; KF301-4P pad-compatible |
| J_FB1, J_FB2, J_FB3 | 0Ω wire jumper | Replaces ferrite bead (axial footprint) | THT axial | 3 | tinned wire offcuts |
| C_VCC × 3 | 100 nF | Encoder VCC bypass at connector | THT 5mm | 3 | |
| R_TOP1–6 | 10 kΩ | 1% 1/4W divider upper | THT | 6 | direnc.net |
| R_BOT1–6 | 20 kΩ | 1% 1/4W divider lower | THT | 6 | direnc.net |
| C_FILT1–6 | 10 nF C0G/NP0 (preferred) | RC filter cap (2.38 kHz corner) | THT 5mm | 6 | direnc.net (verify dielectric) |
| TVS1–6 | General THT TVS (part TBD) | Bidir, V_RWM ≥ ~3.34V; on-hand 1.5KE3.3CA works (slight leak) / 1.5KE3.9CA ideal. Schematic value still placeholder `D_TVS` | DO-201AD (flexible) | 6 | **Populate** — solder proper THT TVS |
| **Schmitt trigger** | | | | | |
| U_SCHM | 74HC14 | Hex Schmitt inverter, 3.3V supply | DIP-14 | 1 | any HC variant |
| **MCU** | | | | | |
| U1 | ESP32-S3-DevKitC-1 N16R8 | ESP32-S3-WROOM-1 module on DevKitC-1 | 2×22 hdr | 1 | direnc.net |
| U1 socket | Female pin header 1×22 | DevKitC-1 left socket | THT | 1 | cut from 1×40 |
| U1 socket | Female pin header 1×22 | DevKitC-1 right socket | THT | 1 | cut from 1×40 |
| **Switches + expansion (as-built)** | | | | | |
| J_SW1 | Phoenix MKDS-1,5-4 (5.0mm) | 2-button terminal: 1=GND, 2=BTN1, 3=BTN2, 4=3V3 | THT 5mm | 1 | BTN1=GPIO17, BTN2=GPIO18 |
| R_SW1, R_SW2 | 10 kΩ | Pull-ups for BTN1/BTN2 | THT | 2 | |
| C_SW1, C_SW2 | 100 nF | Debounce for BTN1/BTN2 | THT 5mm | 2 | |
| J_EXP1 | 2×6 pin header (2.54mm) | AUX_IO: 1/3/5/7=AUX1–4, 9=3V3, 11=+5V, evens=GND | THT | 1 | |
| R_AUX1–4 | 100 Ω | Series protection AUX1–4 → GPIO11/12/13/14 | THT | 4 | |
| **Test & misc** | | | | | |
| TP1–TP6 | Test point pin 1.0 mm | 5V_RAIL, 3V3, MT3608 OUT, BAT+, BAT_OUT, GND | THT | 6 | header pins |

**Items removed from the original BOM**:

J_USB, R_CC1, R_CC2, TVS_USB, D_USB, U_IDEAL (LTC4412), Q_SWITCH, R_GATE, C_LTC, FB1/FB2/FB3 (ferrite beads), R_GPIO12, SW_RESET, LED2, R_LED2

**Total line items**: ~37 (32 original Appendix A + switch/AUX block + TP6)
**Total parts** (incl. multi-quantity rows): ~85 (master schematic = 74 component refs)

---

## Appendix B — Firmware Port Checklist

After the PCB is fabricated and assembled, the firmware needs:

1. **`platformio.ini`** — add new env:
   ```ini
   [env:esp32-s3-devkitc-1]
   platform = espressif32
   board = esp32-s3-devkitc-1
   framework = arduino
   board_build.flash_mode = qio
   board_build.flash_size = 16MB
   board_build.psram_type = opi
   monitor_speed = 115200
   build_flags =
     -DARDUINO_USB_CDC_ON_BOOT=1
     -DBOARD_HAS_PSRAM
   lib_deps =
     paulstoffregen/Encoder@^1.4.4
     adafruit/Adafruit NeoPixel@^1.12
   ```

2. **`firmware/src/SphericalSensor.h`** — pin defines:
   ```cpp
   #define PIN_THETA_A     4
   #define PIN_THETA_B     5
   #define PIN_PHI_A       6
   #define PIN_PHI_B       7
   #define PIN_WIRE_A     15
   #define PIN_WIRE_B     16
   #define PIN_BATTERY_ADC 1   // ADC1_CH0
   #define PIN_RGB_LED    38   // onboard WS2812
   ```

3. **Battery LED helper** — replace `digitalWrite(PIN_LED_BATT, …)` calls with `Adafruit_NeoPixel` calls; add color states:
   - Green (0,255,0): ≥80% (V > 4.0 V)
   - Yellow (255,255,0): 20–80% (3.5–4.0 V)
   - Red solid (255,0,0): <20% (3.3–3.5 V)
   - Red blink: <10% (<3.3 V)

4. **ADC reference** — ESP32-S3 ADC scaling differs slightly from classic ESP32. With 100k/100k divider on 4.2 V max LiPo: ADC sees 2.1 V max → use `ADC_ATTEN_DB_11` (≈3.3 V full scale) and 12-bit resolution. Recalibrate scale factor in firmware if voltage readings drift.

5. **Strapping pins** — none of the new GPIO assignments (4/5/6/7/15/16/1/38) are strapping pins on ESP32-S3. The classic-ESP32 GPIO12 pull-down workaround is no longer needed.

---

## Appendix C — Net List Summary (post-changes)

**Power tree**:
```
J4 (5V) → TVS_BAR → D_BAR → V_EXT_RAW
V_EXT_RAW → Q_RPP (PJA3441) → V_EXT_PROT
V_EXT_PROT ──┬─ MOD_TP4056 IN (charge path)
             └─ D_EXT (1N5822) ──┐
                                  ├─ PI_NODE → L1 → 5V_RAIL
J5 (LiPo) ─ MOD_TP4056 BAT± ── MOD_MT3608 IN
MOD_MT3608 OUT (5.0V) ── D_BOOST (1N5822) ─┘
5V_RAIL → DevKitC-1 J1 pin 21 (5V) → onboard 3.3V LDO → DevKitC-1 J1 pin 1/2 → U_SCHM VCC
```

**Encoder signal tree (×3 encoders, ×6 lines)**:
```
J1/J2 (KF301-4P) or J3 (2P+3P): GND, VCC, A, B [, Z on J3]
5V_RAIL → J_FBn (0Ω jumper) → encoder VCC; C_VCC at connector
Encoder A/B (0-5V TTL) → R_TOP (10k) → DIVIDER_NODE → C_FILT (10nF) → R_BOT (20k) → GND
DIVIDER_NODE → 74HC14 input → 74HC14 output → DevKitC-1 GPIO
```

**Battery monitor**:
```
J5 BAT+ → R_MON1 (100k) → ADC_MON → R_MON2 (100k) → GND
ADC_MON + C_ADC (100n) → DevKitC-1 J3 pin 4 (GPIO1, ADC1_CH0)
```

