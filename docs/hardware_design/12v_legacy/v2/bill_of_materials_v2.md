# Bill of Materials — EVKA Position V2

> Complete parts list for the ESP32-S3 based spherical positioning sensor.  
> **100% through-hole** components + plug-in modules.  
> Designed for LPKF S63 milling and hand soldering.  
> Sourcing focus: Turkey domestic market, AliExpress, LCSC.

---

## BOM Summary by Category

> **Prices verified April 2026** against direnc.net, robolinkmarket.com, and samm.com.  
> Items marked ⚠️ have sourcing notes — read alternatives before ordering.

| Category | Line Items | Est. Cost (₺) |
|----------|-----------|---------------|
| Power input & protection | 10 | ~90₺ |
| Buck converter | 7 | ~50₺ |
| Battery & protection | 4 + battery | ~115₺ |
| MCU & headers | 3 | ~575₺ |
| Signal conditioning | 5 component types | ~45₺ |
| Connectors | 7 | ~70₺ |
| Expansion interfaces | 12 component types | ~60₺ |
| Passives & misc | various | ~30₺ |
| **Total (without battery)** | **~60 line items** | **~1035₺** |
| **Total (with 3S LiPo)** | | **~1185–1285₺** |

> **vs Phase 1 design:** BQ24650 module removed (~200–260₺ saved). Q_BATT circuit added (~65₺). XT60 connector added (~40₺). Net savings ~130–155₺. Onboard charging moved to external balance charger (not included in BOM cost).

---

## 1. Power Input & Protection

| Ref | Qty | Part | Spec | Package | Source | Est. Cost |
|-----|-----|------|------|---------|--------|-----------|
| J12V | 1 | DC barrel jack | 5.5×2.1mm, center +, panel mount | THT | Direnc.net, AliExpress | ~5₺ |
| NTC1 | 1 | NTC thermistor | 5D-9, 5Ω cold | THT disc | Direnc.net | ~3₺ |
| F1 | 1 | PTC polyfuse | MF-R110, 1.1A hold, 2.2A trip (adapter side only) | THT radial | Direnc.net | ~5₺ |
| TVS_IN | 1 | TVS diode | P6KE18A, 18V standoff, 600W, DO-15 | Axial | ⚠️ Arkotek / Entegredunyasi; not confirmed at direnc.net | ~5₺ |
| Q_RPP | 1 | P-ch MOSFET | IRF4905, 55V, 20mΩ, TO-220AB (reverse polarity) | TO-220 | ⚠️ Direnc.net ~12₺ (check stock); backup: Arkotek, Entegredunyasi.com.tr | ~12–35₺ |
| R_G | 1 | Resistor | 100kΩ, 1%, 1/4W (Q_RPP gate pull-down) | Axial | Direnc.net | ~0.5₺ |
| Q_BATT | 1 | P-ch MOSFET | IRF4905, 55V, 20mΩ, TO-220AB (battery load-sharing) | TO-220 | Same as Q_RPP — order 2 total | ~12₺ |
| R_G2 | 1 | Resistor | 100kΩ, 1%, 1/4W (Q_BATT gate pull-down) | Axial | Direnc.net | ~0.5₺ |
| D_GATE | 1 | Schottky diode | SS14 or SS34, 1A, 40V, Vf ≈ 0.3V (Q_BATT gate control) | DO-214AA or DO-201 | Direnc.net | ~1–3₺ |
| Z1 | 1 | Zener diode | 1N4742A, 12V, 1W, DO-41 (Q_BATT V_GS clamp) | DO-41 | Direnc.net | ~1–3₺ |
| F_BAT | 1 | Automotive blade fuse + holder | ATO/ATC 5A (2200mAh) or 10A (5000mAh); inline fuse holder | THT holder + fuse | Automotive supplier, N11, Trendyol | ~10–20₺ |

**Alternatives:**
- **Q_RPP / Q_BATT:** IRF9540N (100V, 117mΩ, higher drop but acceptable) or IRF9Z34N (55V, 100mΩ)
- **TVS_IN:** P6KE20A if your adapter outputs >15V routinely
- **F1:** Littlefuse 0251020.NRT1 (2A glass fuse) + Keystone 3549-2 holder if you prefer non-resettable
- **F_BAT:** 5A for 2200mAh pack; 10A for 5000mAh pack; size to 2× expected continuous discharge current

---

## 2. Buck Converter (12V → 5V)

| Ref | Qty | Part | Spec | Package | Source | Est. Cost |
|-----|-----|------|------|---------|--------|-----------|
| U_BUCK | 1 | **MP1584EN module** | "DC-DC 1584", 3A, adjustable | Module ~22×17mm | **direnc.net — 26.46₺ (confirmed in stock)** | **26.46₺** |
| C_IN1 | 1 | Electrolytic capacitor | 220µF, 35V, low-ESR | Radial TH | Direnc.net | ~5₺ |
| C_IN2 | 1 | Ceramic capacitor | 100nF, 50V | Ceramic disc, 5mm | Direnc.net | ~1₺ |
| L_FILT | 1 | Inductor | 22µH, 2A rated | Axial/radial TH | Direnc.net | ~5₺ |
| C_FILT | 1 | Electrolytic capacitor | 220µF, 10V, low-ESR | Radial TH | Direnc.net | ~3₺ |
| C_FILT_HF | 1 | Ceramic capacitor | 100nF, 16V | Ceramic disc, 5mm | Direnc.net | ~1₺ |
| D_OR | 1 | Schottky diode | SS36, 3A, 60V, Vf ~0.25V, DO-201 | Axial | Direnc.net | ~3₺ |

> **Note:** MP2315 is not stocked in Turkey. MP1584EN (direnc.net, 26.46₺) is the confirmed in-stock replacement. With the 22µH + 220µF LC post-filter, output ripple is <5mVpp — same as MP2315.

**Pre-set requirements:**
- MP1584EN: Adjust to **5.10V** with 25Ω/2W dummy load before connecting to circuit (compensates for SS36 Vf drop, targets 4.85V at 5V_RAIL)
- Verify ripple <20mVpp at output before full assembly

**Alternatives:**
- **U_BUCK:** XL4015 (~66₺, direnc.net) if higher current headroom needed
- **L_FILT:** Any 22µH ≥1.5A inductor (axial choke, radial drum core)

---

## 3. Battery & Protection

> **No onboard charging circuit.** The 3S LiPo is charged externally via a dedicated balance charger
> (iMax B3 / SkyRC E3S class). The BMS provides hardware undervoltage cutoff and short-circuit
> protection only. See `subsystems/power_supply_v2.md` Section 5 for charging procedure.

| Ref | Qty | Part | Spec | Package | Source | Est. Cost |
|-----|-----|------|------|---------|--------|-----------|
| BMS_3S | 1 | 3S BMS board | HX-3S-01, 10A, **protection only** (no onboard charging) | Module ~50×18mm | **robolinkmarket.com — 52.20₺ (confirmed in stock)** | **52.20₺** |
| J_XT60 | 1 | XT60 male connector | Panel mount, PCB edge, main battery discharge | THT/Panel | Direnc.net ~40₺, AliExpress | ~40₺ |
| J_BAL | 1 | JST-XH-4P header | 2.5mm pitch, balance lead access (passive, no circuitry) | THT | Direnc.net, AliExpress | ~3₺ |
| BAT | 1 | 3S LiPo pack | 11.1V, 2200mAh (or 5000mAh), with JST-XH balance lead + XT60 main lead | Pack | Local RC shop, AliExpress | ~150–250₺ |

**Important notes:**
- **BMS_3S:** Verify undervoltage cutoff at ~9.6V (3.2V/cell) with bench supply before installing. Some HX-3S-01 variants cut at 2.8V/cell — verify your specific module.
- **Battery:** Must have **both** XT60 main lead and JST-XH-4P balance lead. Pack without balance connector cannot be safely charged.
- **Charging:** External balance charger ONLY. Do not connect any charger through J12V or the PCB. Budget separately: iMax B3 ~450₺, SkyRC E3S ~1700₺.

**Role of BMS in this design:**
- Overdischarge cutoff: YES — hardware backstop if firmware undervoltage shutdown fails
- Short-circuit protection: YES — secondary protection alongside F_BAT blade fuse
- Overcharge protection: NOT USED (no onboard charger)
- Passive balancing: NOT RELIED UPON — external balance charger handles this every charge cycle

---

## 4. ADC Divider

| Ref | Qty | Part | Spec | Package | Source | Est. Cost |
|-----|-----|------|------|---------|--------|-----------|
| R_ADC_TOP | 1 | Resistor | 120kΩ, 1%, 1/4W | Axial | Direnc.net | ~0.5₺ |
| R_ADC_BOT | 1 | Resistor | 27kΩ, 1%, 1/4W | Axial | Direnc.net | ~0.5₺ |

**Scale factor:** (120k + 27k) / 27k = **5.444**

---

## 5. MCU & Headers

| Ref | Qty | Part | Spec | Package | Source | Est. Cost |
|-----|-----|------|------|---------|--------|-----------|
| U_ESP | 1 | ESP32-S3-DevKitC-1 **N8R2** | Dev board, 8MB flash, 2MB PSRAM, USB-C | Module ~55×28mm | **robolinkmarket.com — 564.60₺ (N8R2, in stock)** | **564.60₺** |
| H1 | 1 | Female header | 1×20, 2.54mm, for DevKitC-1 left | THT | Direnc.net, AliExpress | ~5₺ |
| H2 | 1 | Female header | 1×20, 2.54mm, for DevKitC-1 right | THT | Direnc.net, AliExpress | ~5₺ |

**Note:** DevKitC-1 has two rows of 20 pins each, spaced ~25.4mm apart. Verify exact spacing before drilling.

---

## 6. Signal Conditioning

| Ref | Qty | Part | Spec | Package | Source | Est. Cost |
|-----|-----|------|------|---------|--------|-----------|
| R_DIV_TOP | 7 | Resistor | 10kΩ, 1%, 1/4W, metal film | Axial | Direnc.net | ~3.5₺ |
| R_DIV_BOT | 7 | Resistor | 20kΩ, 1%, 1/4W, metal film | Axial | Direnc.net | ~3.5₺ |
| C_FILTER | 7 | Capacitor | 1nF, C0G/NP0, 50V | Ceramic disc, 5mm | Direnc.net | ~7₺ |
| TVS_SIG | 7 | TVS diode | 1.5KE3.3CA, bidirectional, DO-15 | Axial | Direnc.net | ~14₺ |
| FB | 3 | Ferrite bead | 600Ω @ 100MHz, axial | Axial ~3.5×6mm | Direnc.net | ~6₺ |

**Total signal section:** ~7 resistors + 7 resistors + 7 caps + 7 TVS + 3 ferrites = 31 components

---

## 7. Connectors

| Ref | Qty | Part | Spec | Package | Source | Est. Cost |
|-----|-----|------|------|---------|--------|-----------|
| J1 | 1 | Screw terminal | KF301-4P, 5.08mm, Theta encoder | THT | Direnc.net, AliExpress | ~3₺ |
| J2 | 1 | Screw terminal | KF301-4P, 5.08mm, Phi encoder | THT | Direnc.net, AliExpress | ~3₺ |
| J3 | 1 | Screw terminal | KF301-5P, 5.08mm, Wire encoder | THT | Direnc.net, AliExpress | ~4₺ |
| J_RS485 | 1 | Screw terminal | KF301-3P, 5.08mm, RS-485 | THT | Direnc.net, AliExpress | ~3₺ |
| J_I2C | 1 | Pin header | 1×4, 2.54mm, I2C expansion | THT | Direnc.net, AliExpress | ~2₺ |
| J_GPIO | 1 | Pin header | 1×6, 2.54mm, spare GPIOs | THT | Direnc.net, AliExpress | ~2₺ |

> **Note:** XT60 (J_XT60) and JST-XH-4P balance header (J_BAL) are listed under Section 3 (Battery & Protection). XT60 must be placed at PCB edge; inline F_BAT fuse holder within 15cm of J_XT60 positive terminal.

---

## 8. Expansion Interfaces

| Ref | Qty | Part | Spec | Package | Source | Est. Cost |
|-----|-----|------|------|---------|--------|-----------|
| U_RS485 | 1 | RS-485 transceiver | MAX485EPA+, DIP-8 | DIP-8 | **direnc.net — 13.23₺ (confirmed in stock)** | **13.23₺** |
| R_TERM | 1 | Resistor | 120Ω, 1/4W | Axial | Direnc.net | ~0.5₺ |
| U_WDT | 1 | Watchdog supervisor | MAX813L, DIP-8 | DIP-8 | ⚠️ **Not stocked in Turkey** — import from DigiKey (~€2–4 + shipping). Alternative: MAX706 DIP-8 (check direnc.net). | ~10–25₺ |
| R_PFI1 | 1 | Resistor | 100kΩ, 1%, 1/4W | Axial | Direnc.net | ~0.5₺ |
| R_PFI2 | 1 | Resistor | 68kΩ, 1%, 1/4W | Axial | Direnc.net | ~0.5₺ |
| R_WDT_PU | 1 | Resistor | 10kΩ, 1/4W | Axial | Direnc.net | ~0.5₺ |
| R_EN_PU | 1 | Resistor | 10kΩ, 1/4W | Axial | Direnc.net | ~0.5₺ |
| R_I2C_PU1 | 1 | Resistor | 4.7kΩ, 1/4W | Axial | Direnc.net | ~0.5₺ |
| R_I2C_PU2 | 1 | Resistor | 4.7kΩ, 1/4W | Axial | Direnc.net | ~0.5₺ |
| TVS_I2C1 | 1 | TVS diode | 1.5KE3.3CA, DO-15 | Axial | Direnc.net | ~2₺ |
| TVS_I2C2 | 1 | TVS diode | 1.5KE3.3CA, DO-15 | Axial | Direnc.net | ~2₺ |
| SW_RST | 1 | Tactile button | 6×6mm, THT | THT | Direnc.net | ~2₺ |

**Alternative for U_RS485:** SP485EN (DIP-8, ~10₺, pin-compatible)

---

## 9. LEDs & Indicators

| Ref | Qty | Part | Spec | Package | Source | Est. Cost |
|-----|-----|------|------|---------|--------|-----------|
| LED1 | 1 | LED | 3mm, Green, 20mA | THT | Direnc.net | ~1₺ |
| LED2 | 1 | LED | 3mm, Blue, 20mA | THT | Direnc.net | ~1₺ |
| LED3 | 1 | LED | 3mm, Yellow, 20mA | THT | Direnc.net | ~1₺ |
| LED4 | 1 | LED | 3mm, Red, 20mA | THT | Direnc.net | ~1₺ |
| R_LED1 | 1 | Resistor | 1kΩ, 1/4W | Axial | Direnc.net | ~0.5₺ |
| R_LED2 | 1 | Resistor | 1kΩ, 1/4W | Axial | Direnc.net | ~0.5₺ |
| R_LED3 | 1 | Resistor | 1kΩ, 1/4W | Axial | Direnc.net | ~0.5₺ |
| R_LED4 | 1 | Resistor | 1kΩ, 1/4W | Axial | Direnc.net | ~0.5₺ |

**LED current:** (5V - 2Vf) / 1kΩ ≈ 3mA — bright enough for indoor visibility, low power.

---

## 10. Decoupling & Bulk Capacitors

| Ref | Qty | Part | Spec | Package | Source | Est. Cost |
|-----|-----|------|------|---------|--------|-----------|
| C_ENC1 | 1 | Ceramic capacitor | 100nF, 50V | Ceramic disc, 5mm | Direnc.net | ~1₺ |
| C_ENC2 | 1 | Ceramic capacitor | 100nF, 50V | Ceramic disc, 5mm | Direnc.net | ~1₺ |
| C_ENC3 | 1 | Ceramic capacitor | 100nF, 50V | Ceramic disc, 5mm | Direnc.net | ~1₺ |
| C_BULK | 1 | Electrolytic capacitor | 220µF, 16V | Radial TH | Direnc.net | ~3₺ |

---

## 11. Mechanical

| Ref | Qty | Part | Spec | Package | Source | Est. Cost |
|-----|-----|------|------|---------|--------|-----------|
| MH1–4 | 4 | Mounting hole | M3, 3.2mm drill | N/A | PCB feature | — |
| DIN_CLIP | 1 | DIN rail clip | 35mm rail, for Arduino form factor | Plastic/metal | AliExpress | ~30₺ |

---

## 12. Optional Plug-in Modules & DNP Feature Additions

These are not required for core operation. Add headers on the PCB during build; populate modules only when the feature is needed.

### I2C Modules (plug into J_I2C header)

| Module | Purpose | Interface | Turkey Source | Est. Cost |
|--------|---------|-----------|--------------|-----------|
| DS3231 ZS-042 | Real-time clock, timestamped logs | I2C 0x68 | samm.com / direnc.net (check stock) | ~113–158₺ |
| ADS1115 | 16-bit 4-channel ADC | I2C 0x48 | AliExpress | ~40₺ |
| SSD1306 OLED | Local X/Y/Z status display | I2C 0x3C | AliExpress, SAMM | ~40₺ |

### DNP Feature Additions (add headers to PCB, do not populate by default)

| Item | Purpose | GPIOs | Turkey Source | Est. Cost |
|------|---------|-------|--------------|-----------|
| **W5500 Ethernet Module** | Wired network (metal enclosures, industrial) | SPI3: GPIO 33/34/35/36 | **samm.com — 180.59₺ (in stock)** | **180.59₺** |
| **Micro-SD socket** | Offline CSV logging, config files | SPI3: GPIO 33/34/35, CS=GPIO 36 | AliExpress, Arkotek | ~10–70₺ |
| **SN65HVD230 CAN transceiver** | CANopen/Modbus CAN bus | GPIO 41 (TX), 42 (RX) | AliExpress ~$1–3 | ~35–100₺ |
| **CR2032 holder** | RTC battery backup for DS3231 | — | direnc.net | ~5₺ |

> ⚠️ **SD card + W5500 share SPI3 (GPIO 33–36).** Add separate CS pins for each device. Verify GPIOs 33–36 are free on the DevKitC-1-N8R2 board schematic (they are NOT available on -N8R8 / PSRAM variant).

---

## 13. Complete BOM Table (Sorted by Reference)

| Ref | Qty | Description | Part Number | Package |
|-----|-----|-------------|-------------|---------|
| BAT | 1 | 3S LiPo battery | 11.1V 2200mAh | Pack |
| BMS_3S | 1 | 3S BMS | HX-3S-01 10A | Module |
| C_BULK | 1 | Electrolytic capacitor | 220µF/16V | Radial |
| C_ENC1–3 | 3 | Ceramic capacitor | 100nF/50V | Disc 5mm |
| C_FILT | 1 | Electrolytic capacitor | 220µF/10V low-ESR | Radial |
| C_FILT_HF | 1 | Ceramic capacitor | 100nF/16V | Disc 5mm |
| C_IN1 | 1 | Electrolytic capacitor | 220µF/35V | Radial |
| C_IN2 | 1 | Ceramic capacitor | 100nF/50V | Disc 5mm |
| D_GATE | 1 | Schottky diode | SS14 | DO-214AA |
| D_OR | 1 | Schottky diode | SS36 | DO-201 |
| F_BAT | 1 | Blade fuse + inline holder | 5A ATO/ATC | Inline |
| FB1–3 | 3 | Ferrite bead | 600Ω @ 100MHz | Axial |
| F1 | 1 | PTC polyfuse | MF-R110 1.1A | Radial |
| H1 | 1 | Female header | 1×20, 2.54mm | THT |
| H2 | 1 | Female header | 1×20, 2.54mm | THT |
| J1 | 1 | Screw terminal | KF301-4P 5.08mm | THT |
| J12V | 1 | DC barrel jack | 5.5×2.1mm | Panel THT |
| J2 | 1 | Screw terminal | KF301-4P 5.08mm | THT |
| J3 | 1 | Screw terminal | KF301-5P 5.08mm | THT |
| J_BAL | 1 | Balance header | JST-XH-4P 2.5mm | THT |
| J_XT60 | 1 | XT60 panel connector | XT60 male | Panel THT |
| J_GPIO | 1 | Pin header | 1×6, 2.54mm | THT |
| J_I2C | 1 | Pin header | 1×4, 2.54mm | THT |
| J_RS485 | 1 | Screw terminal | KF301-3P 5.08mm | THT |
| L_FILT | 1 | Inductor | 22µH, 2A | Axial |
| LED1 | 1 | LED | 3mm Green | THT |
| LED2 | 1 | LED | 3mm Blue | THT |
| LED3 | 1 | LED | 3mm Yellow | THT |
| LED4 | 1 | LED | 3mm Red | THT |
| NTC1 | 1 | NTC thermistor | 5D-9 | Disc |
| Q_BATT | 1 | P-ch MOSFET | IRF4905 | TO-220 |
| Q_RPP | 1 | P-ch MOSFET | IRF4905 | TO-220 |
| R_ADC_BOT | 1 | Resistor | 27kΩ 1% | Axial |
| R_ADC_TOP | 1 | Resistor | 120kΩ 1% | Axial |
| R_DIV_BOT | 7 | Resistor | 20kΩ 1% | Axial |
| R_DIV_TOP | 7 | Resistor | 10kΩ 1% | Axial |
| R_EN_PU | 1 | Resistor | 10kΩ 1% | Axial |
| R_G | 1 | Resistor | 100kΩ 1% | Axial |
| R_G2 | 1 | Resistor | 100kΩ 1% | Axial |
| R_I2C_PU1–2 | 2 | Resistor | 4.7kΩ 1% | Axial |
| R_LED1–4 | 4 | Resistor | 1kΩ 1% | Axial |
| R_PFI1 | 1 | Resistor | 100kΩ 1% | Axial |
| R_PFI2 | 1 | Resistor | 68kΩ 1% | Axial |
| R_TERM | 1 | Resistor | 120Ω 1% | Axial |
| R_WDT_PU | 1 | Resistor | 10kΩ 1% | Axial |
| SW_RST | 1 | Tactile button | 6×6mm | THT |
| TVS_I2C1–2 | 2 | TVS diode | 1.5KE3.3CA | DO-15 |
| TVS_IN | 1 | TVS diode | P6KE18A | DO-15 |
| TVS_SIG1–7 | 7 | TVS diode | 1.5KE3.3CA | DO-15 |
| U_BUCK | 1 | Buck module | **MP1584EN** | 22×17mm |
| U_ESP | 1 | ESP32-S3 dev board | DevKitC-1-N8R2 | Module |
| U_RS485 | 1 | RS-485 transceiver | MAX485EPA+ | DIP-8 |
| U_WDT | 1 | Watchdog supervisor | MAX813L | DIP-8 |
| Z1 | 1 | Zener diode | 1N4742A 12V | DO-41 |

---

## 14. Sourcing Guide

### Turkey Domestic Sources

| Supplier | Location | Strengths | Website |
|----------|----------|-----------|---------|
| **Direnc.net** | Istanbul | Passives, semiconductors, connectors | direnc.net |
| **Robolinkmarket.com** | Istanbul | Dev boards, modules, sensors | robolinkmarket.com |
| **Komponentci.com** | Istanbul | Wide selection, LCSC-like | komponentci.com |
| **Moser Elektronik** | Ankara | TI, Analog Devices, industrial ICs | moserelektronik.com |
| **SAMM Market** | Istanbul | Connectors, enclosures, tools | sammmarket.com |

### International Sources

| Supplier | Strengths | Shipping to Turkey |
|----------|-----------|-------------------|
| **LCSC** | Cheapest components, huge selection | ~$15–25 DHL, 3–7 days |
| **AliExpress** | Modules, cheap passives | ~$5–15, 2–4 weeks |
| **Digi-Key** | Guaranteed stock, datasheets | ~$25–35, 3–5 days |
| **Mouser** | Wide industrial selection | ~$25–35, 3–5 days |

### Recommended Ordering Strategy

1. **DevKitC-1 N8R2:** robolinkmarket.com (564.60₺, confirmed in stock)
2. **MP1584EN buck module:** direnc.net (26.46₺, in stock)
3. **MAX485EPA+ DIP-8:** direnc.net (13.23₺, in stock)
4. **MAX813L DIP-8:** ⚠️ Order from DigiKey or Mouser (not stocked in Turkey). Alternative: check direnc.net for MAX706 DIP-8.
5. **IRF4905 TO-220 × 2 (Q_RPP + Q_BATT):** ⚠️ Check stock at direnc.net (~12₺ each) and komponentci.net (~35₺) — temporarily OOS April 2026. Backup: Arkotek Elektronik or Entegredunyasi.com.tr
6. **HX-3S-01 BMS:** robolinkmarket.com (52.20₺, in stock)
7. **1N4742A Zener 12V:** direnc.net (~1–3₺)
8. **SS14 Schottky (D_GATE):** direnc.net or AliExpress (~1–3₺)
9. **ATO/ATC 5A blade fuse + inline holder (F_BAT):** Auto parts shop or AliExpress (~10–20₺)
10. **XT60 male panel connector (J_XT60):** direnc.net or AliExpress (~40₺)
11. **Passives (resistors, caps, TVS, ferrites):** direnc.net bulk
12. **P6KE18A TVS:** Not confirmed at major retailers — check Arkotek or order from LCSC (~$0.20 + shipping)
13. **Connectors, screw terminals:** SAMM Market or AliExpress
14. **Battery:** Local RC hobby shop (avoids shipping restrictions on LiPo)

---

## 15. Assembly Notes

1. **Pre-set modules BEFORE soldering to PCB:**
   - MP1584EN: 5.10V output with 25Ω/2W load; apply one drop of CA glue to trimpot body after calibration

2. **Component order for soldering:**
   - Step 1: Resistors and small passives (all 1/4W axial)
   - Step 2: Diodes (watch band orientation!)
   - Step 3: Capacitors (electrolytic: watch polarity!)
   - Step 4: ICs in sockets or direct (MAX485, MAX813L)
   - Step 5: Transistor/Q1 (IRF4905 TO-220)
   - Step 6: Connectors and headers
   - Step 7: Modules (MP1584EN, BMS) on pin headers
   - Step 8: Female headers for DevKitC-1
   - Step 9: Final test before inserting DevKitC-1

3. **Polarity-sensitive components:**
   - P6KE18A: cathode band toward V12_PROT
   - SS34/SS36: cathode band toward output (BUCK_VIN or 5V_RAIL)
   - Electrolytic caps: negative stripe toward GND
   - LEDs: flat side / short lead = cathode (GND side)
   - IRF4905: pin 1=Gate, pin 2=Drain, pin 3=Source
