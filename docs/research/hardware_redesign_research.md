# Industrial 3D Positioning Sensor — Hardware Redesign Research

**Scope:** Flexibility and future-proofing improvements for the EVKA spherical positioning sensor PCB redesign.  
**Baseline:** ESP32 + 2× E40S6 rotary encoders + DWEM2 draw-wire + WiFi AP+STA + 12V/3S LiPo + ESP-NOW pendant.  
**Sourcing focus:** Turkey domestic market, LCSC, AliExpress.

---

## Executive Summary — Priority Matrix

| Priority | Items | Rationale |
|----------|-------|-----------|
| **High impact / low cost** (do these) | I2C header, SPI header, SD card slot, DS3231 RTC, status LEDs, u.FL antenna, USB-C, OTA | Headers cost pennies; SD/RTC add major capability with <₺100 BOM impact; USB-C is now cheaper than micro-USB in volume |
| **Medium impact / medium cost** (consider these) | W5500 Ethernet header, RS-485/UART header, external watchdog, 4-20mA output, DIN rail enclosure, OLED header | Industrial customers explicitly ask for these; each adds ₺100–₺400 to BOM |
| **Nice to have / high cost** (maybe later) | CAN bus, opto-isolated I/O, 0-10V analog output, relay outputs, IP65 rating, BLE phone config | Significant PCB area and cost; implement only if specific customer requirement exists |

---

## 1. Expansion Interfaces

### 1.1 I2C Header — **HIGH IMPACT / LOW COST**
- **Why:** External sensors (IMU, temp, OLED), GPIO expanders (PCF8574/TCA9534), EEPROM.
- **ESP32 pins:** GPIO 21 (SDA) / GPIO 22 (SCL) are the native I2C pins. **Currently unused.**
- **Implementation:** Unpopulated 4-pin JST-SH or 2.54mm header with 4.7kΩ pull-ups to 3.3V and 1.5KE3.3CA TVS per line.
- **Cost:** ~₺5 header + ₺2 resistors.
- **Parts:** Any 2.54mm 1×4 pin header (AliExpress/LCSC); JST-SH-1.0-4P for compact variant.

### 1.2 SPI Header — **HIGH IMPACT / LOW COST**
- **Why:** SD card module, external flash (W25Q128), ADCs, DACs.
- **ESP32 pins:** VSPI is GPIO 18 (SCK) / 19 (MISO) / 23 (MOSI). **GPIO 18 is used for Wire-Z encoder.** HSPI is GPIO 14 (SCK) / 12 (MISO) / 13 (MOSO) — **GPIO 14/12 are Theta encoder pins.**
- **Conflict resolution:** 
  - **Option A:** Share VSPI with Wire-Z encoder using a 74HC157 mux or simply bit-bang Wire-Z (slow, not recommended).
  - **Option B:** Route HSPI to a header and remap Theta encoder to GPIO 25/26 or GPIO 27/33 (requires firmware pin change, but ESP32 has enough pins).
  - **Option C (recommended):** Add a **dedicated SPI header** using GPIO 19 (MISO), 23 (MOSI), and GPIO 5 (CS) + GPIO 4 (SCK, bit-banged or HSPI remap). GPIO 5 is currently unused.
- **Cost:** ~₺5 header.

### 1.3 UART Header — **MEDIUM IMPACT / LOW COST**
- **Why:** RS-485/Modbus RTU is the most common industrial request for PLC integration.
- **ESP32 pins:** UART2 is GPIO 16 (RX) / GPIO 17 (TX). **Currently used for Wire encoder A/B.**
- **Conflict resolution:**
  - Wire encoder can be moved to GPIO 26/27 or GPIO 33/34 (input-only, but fine for encoders).
  - Or use **UART1** (GPIO 9/10) — **NOT recommended** (flash boot straps).
  - **Best:** Free up UART2 by remapping Wire encoder, then add MAX485/SP485 module header.
- **Parts:** MAX485EESA+ (LCSC ~$0.60), SP485EN (AliExpress ~₺15 for 10pcs). Add 120Ω termination resistor jumper.
- **Cost:** ~₺20 module + header + resistor.

### 1.4 CAN Bus — **MEDIUM IMPACT / MEDIUM COST**
- **Why:** Native in ESP32 (TWAI driver); robust in noisy factory floors; direct PLC integration via CANopen CiA 406 (position encoder profile).
- **ESP32 pins:** GPIO 4 (TX) / GPIO 5 (RX) are the default TWAI pins. **GPIO 5 is unused; GPIO 4 is unused.** No pin conflict.
- **Implementation:** SN65HVD230 or TJA1051T/3 transceiver (3.3V). Isolated variant: ISO1050 (adds ~$3).
- **Parts:**
  - SN65HVD230 (AliExpress ~₺25–40/pc, LCSC ~$1.20)
  - TJA1051T/3 (LCSC/JLCPCB parts library, ~$0.80)
- **Cost:** ~₺30–50 transceiver + 120Ω terminator + header.
- **Verdict:** **Medium priority.** Add PCB pads and DNP populate unless a customer specifically requests it. The firmware TWAI driver is already mature in ESP-IDF/Arduino.

### 1.5 Additional GPIO Headers — **HIGH IMPACT / LOW COST**
- **Available ESP32 pins** (after current assignment review):
  - **GPIO 0, 4, 5, 19, 21, 22, 23, 25, 26, 27, 33** — free for general I/O.
  - **GPIO 34, 36, 39** — input-only (OK for encoders, limit switches, analog).
  - **GPIO 2** — has onboard LED on most dev boards, but usable.
- **Recommendation:** Bring out 4–6 unused GPIOs to a 2×5 2.54mm header with GND and 3.3V for prototyping.
- **Cost:** ~₺5.

---

## 2. Onboard Storage

### 2.1 SD Card Slot — **HIGH IMPACT / LOW COST**
- **Why:** Offline CSV logging without PC; firmware update from SD; configuration file storage.
- **Interface:** SPI (shared with VSPI or dedicated).
- **Implementation:** Micro-SD socket with push-push mechanism (e.g., CNYICKH TF-015 on LCSC). Connect to VSPI (GPIO 18/19/23) with independent CS on GPIO 5.
  - **Important:** If GPIO 18 (Wire-Z) is kept, use a **GPIO expander** (MCP23S17 on SPI) to free pins, or accept that Wire-Z and SD card cannot be used simultaneously without multiplexing.
  - **Preferred:** Move Wire-Z to GPIO 27 (input-only is fine for slow index pulse) and use VSPI cleanly for SD.
- **Parts:** Micro SD socket (LCSC C91145 ~$0.35; AliExpress ~₺15 for 5pcs).
- **Cost:** ~₺10–15 socket + passives.
- **Firmware:** Arduino `SD.h` or `SD_MMC.h` (1-bit mode uses fewer pins but is slower). SPI mode at 20MHz is sufficient for CSV logging.

### 2.2 SPI Flash (W25Q128) — **MEDIUM IMPACT / LOW COST**
- **Why:** Store calibration coefficients, web dashboard assets, or small config files without wearing SD card. 128Mbit = 16MB.
- **Interface:** SPI (shares bus with SD card, different CS).
- **Parts:** W25Q128JVSIQ (LCSC ~$0.80; AliExpress ~₺20/pc).
- **Cost:** ~₺10–20.
- **Verdict:** Useful if you want to serve the web dashboard from flash instead of PROGMEM strings. **Lower priority than SD card.**

### 2.3 Real-Time Clock (DS3231) — **HIGH IMPACT / LOW COST**
- **Why:** Timestamped CSV logs are essential for industrial traceability. `millis()` wraps and resets on reboot.
- **Interface:** I2C (shares bus with any I2C devices).
- **Implementation:** DS3231 module or chip + coin cell holder (CR2032) + 3.3V level shifting (module usually handles this).
- **Parts:**
  - DS3231SN (chip, LCSC ~$3.50)
  - ZS-042 module (AliExpress ~₺60–80 with battery)
  - CR2032 holder (LCSC ~$0.15)
- **Cost:** ~₺60–100 module approach; ~₺40 chip+holder+battery approach.
- **Verdict:** **Highly recommended.** Add a CR2032 holder on the PCB and either a DS3231 chip footprint or a 4-pin I2C header for an external module.

---

## 3. Display / Interface Options

### 3.1 OLED / I2C LCD Header — **MEDIUM IMPACT / LOW COST**
- **Why:** Local readout of X/Y/Z, battery level, WiFi status — invaluable during field commissioning without a laptop.
- **Interface:** I2C (shares GPIO 21/22).
- **Parts:** SSD1306 0.96" (AliExpress ~₺40); SH1106 1.3" (~₺60). Add 2.54mm 4-pin header.
- **Cost:** ~₺5 header (customer buys display separately).
- **Verdict:** Add the I2C header and a 3.3V/GND pad. Document the supported models.

### 3.2 Status LEDs — **HIGH IMPACT / LOW COST**
- **Current:** 2 LEDs (power green, battery low red on GPIO 25).
- **Recommended additions:**
  - **WiFi/STA status** (already mentioned GPIO 2 in schematic) — solid=connected, blink=AP mode, off=no WiFi.
  - **DATA/Activity** — brief blink on each 20Hz position update (useful to verify loop health without serial).
  - **SD card activity** — blink on write.
  - **Fault/Alarm** — solid red when position is invalid or encoder error detected.
- **Implementation:** Use a cheap I2C GPIO expander (PCF8574, AliExpress ~₺15) or charlie-plexing if GPIOs are tight. Alternatively, use GPIO 0, 2, 25, 26 for 4 LEDs with 1kΩ resistors.
- **Cost:** ~₺10 for 4 extra LEDs + resistors.

---

## 4. Connectivity Improvements

### 4.1 Ethernet (W5500 SPI Module Header) — **MEDIUM IMPACT / MEDIUM COST**
- **Why:** WiFi is problematic in metal cabinets and EMC-heavy environments. Ethernet is the #1 request from industrial integrators.
- **Interface:** SPI + INT pin + RST pin.
- **Parts:** W5500 module (AliExpress ~₺220–270 for Chinese modules; ~₺1000+ for PoE variants). Chip-only W5500 (LCSC ~$2.50) if designing onto PCB.
- **Cost:** ~₺30 chip + magjack + passives if integrated; ~₺220 if using module header.
- **Implementation:** Add a 2×5 2.54mm header matching the common "W5500 Ethernet Module" pinout (SCK, MISO, MOSI, CS, INT, RST, GND, 3.3V, 5V). Firmware uses `EthernetENC` or `Ethernet2` library.
- **Verdict:** **Add the header footprint, DNP by default.** When an industrial customer needs wired reliability, they populate the module. Zero cost if unpopulated.

### 4.2 External Antenna Connector (u.FL/IPEX) — **HIGH IMPACT / LOW COST**
- **Why:** The ESP32-WROOM-32 has a PCB antenna that performs poorly inside metal enclosures. The -U variant adds a u.FL connector.
- **Implementation:** Simply specify **ESP32-WROOM-32U** (with U.FL) instead of the standard WROOM-32. Add a u.FL keep-out area on the PCB and a small through-hole for an SMA pigtail or bulkhead.
- **Parts:** ESP32-WROOM-32U (LCSC ~$2.80 vs $2.50 for standard — negligible difference). IPX/u.FL to SMA pigtail (AliExpress ~₺30).
- **Cost:** ~₺0.5 module delta + ₺30 pigtail.
- **Verdict:** **Do this.** It’s a BOM line-item change with zero PCB area cost.

### 4.3 Bluetooth Classic / BLE — **LOW IMPACT / LOW COST**
- **Why:** Phone configuration without WiFi AP. ESP32 already has BLE hardware — just not used.
- **Implementation:** Software-only; no hardware changes except possibly a BLE status LED. Use NimBLE-Arduino library (much lighter than Bluedroid).
- **Cost:** ₺0 hardware.
- **Verdict:** **Nice to have software feature; no PCB action required.** However, if implemented, document that BLE + WiFi coexistence requires careful heap management (see `docs/BLE_WIFI_COEXISTENCE.md`).

---

## 5. Industrial Reliability Features

### 5.1 External Watchdog Timer — **MEDIUM IMPACT / LOW COST**
- **Why:** ESP32 software WDT only catches task starvation. An external watchdog catches total firmware hangs (e.g., flash corruption, power glitch during WiFi init).
- **Parts:** TPS3823-33DBVR (Texas Instruments, SOT-23-5, LCSC ~$0.40; AliExpress ~₺50 for 10pcs). Timeout = 1.6s. WDI toggled from firmware every loop.
- **Implementation:** WDI → GPIO 4 (or any spare GPIO). Reset output → ESP32 EN pin via 100Ω + diode OR with manual reset button.
- **Cost:** ~₺5 chip + diode + resistor.
- **Verdict:** **Recommended for industrial variants.** Add footprint, DNP for consumer/light-duty builds.

### 5.2 Opto-Isolated Inputs/Outputs — **NICE TO HAVE / HIGH COST**
- **Why:** galvanic isolation when controlling external VFDs, contactors, or reading 24V PLC signals.
- **Input side:** PC817 or TLP281 optocoupler + 1kΩ + 24V-compatible input (with zener). 2–4 channels.
- **Output side:** PC817 + NPN transistor + freewheeling diode for 24V/100mA loads. Or use isolated relay modules.
- **Cost:** ~₺20–30 per channel.
- **Verdict:** **Skip on main PCB.** Instead, add a 6-pin header with 3.3V/GND/spare GPIOs that can connect to an external opto-isolation daughterboard. This keeps the main PCB simple and low-cost.

### 5.3 4-20mA Analog Output — **MEDIUM IMPACT / MEDIUM COST**
- **Why:** De-facto industrial standard. Every PLC has 4-20mA inputs. Two loops could transmit X and Y (or radius and angle).
- **Implementation:** 
  - **DAC + V-to-I converter:** MCP4725 (I2C, 12-bit) + XTR111 or discrete op-amp + transistor.
  - **Dedicated loop transmitter:** AD5420 (16-bit, SPI, $15+) or cheaper AD5748.
  - **Budget approach:** PWM → RC low-pass → LM358 voltage buffer → 2N2222 current source with 100Ω sense resistor. Accuracy ~1% (good enough for many applications).
- **Parts:**
  - XTR111AIDGST (LCSC ~$4.50)
  - MCP4725 module (AliExpress ~₺30)
  - LM358 + discrete (AliExpress ~₺5)
- **Cost:** ₺50–250 per channel depending on accuracy.
- **Verdict:** **Medium priority.** Add a 2-channel DAC + V-to-I footprint on a corner of the PCB. If unpopulated, zero cost. When a factory automation customer needs it, populate the channel(s) corresponding to their required axes.

### 5.4 Relay Output for Alarms/Limits — **NICE TO HAVE / MEDIUM COST**
- **Why:** Hard-wired safety interlock when position exceeds limits (independent of software/firmware).
- **Parts:** SRD-05VDC-SL-C module (AliExpress ~₺25) or small PCB relay (G5V-1, ~$1.50).
- **Cost:** ~₺20–30 per relay + transistor + flyback diode.
- **Verdict:** Add a single SPDT relay footprint driven by a spare GPIO. Useful for "position valid" or "limit exceeded" dry contacts.

---

## 6. Mechanical / Enclosure Considerations

### 6.1 DIN Rail Mount — **MEDIUM IMPACT / LOW COST**
- **Why:** Standard in every electrical panel worldwide. If the PCB doesn't have mounting holes aligned to a DIN clip, integrators will hacksaw their own bracket.
- **Implementation:** Design PCB to 107.6mm × 72mm (standard Arduino Mega footprint already used by Wemos D1 R32) **or** 100mm × 75mm with M3 holes matching a standard DIN rail carrier (e.g., Phoenix Contact BC 107,6 or cheap AliExpress plastic DIN carriers at ~₺30).
- **Alternative:** Use an off-the-shelf DIN rail enclosure box and design the PCB to fit inside.
- **Parts:** Arduino DIN rail clip (AliExpress ~₺25–40); Hammond 1593K enclosure with DIN option.
- **Cost:** ~₺30 clip if purchased separately; ₺0 if designing mounting holes for it.

### 6.2 IP Rating Considerations — **MEDIUM IMPACT / MEDIUM COST**
- **Current:** Open PCB on pertinax. Not suitable for dusty/wet environments.
- **Target:** **IP54** (dust-protected, water splashing) is achievable with a simple sealed ABS box and cable glands. **IP65** (dust-tight, water jets) requires gaskets, gland nuts on all cables, and conformal coating.
- **Recommendation:** Design for **IP54 minimum** by specifying:
  - ABS enclosure with lid screws (~₺50–100 for 150×100×70mm on AliExpress).
  - PG7/PG9 cable glands for encoder cables (~₺10 each).
  - Conformal coating on PCB (acrylic spray, ~₺50 can does 5+ boards).
- **Verdict:** Enclosure is a BOM/packaging decision more than a PCB decision. Add **mounting holes** and **cable gland cutout guides** on the PCB silkscreen.

### 6.3 Cable Glands vs Screw Terminals — **MEDIUM IMPACT / LOW COST**
- **Current:** KF301 screw terminals for encoders. Fine for lab, but vibration loosens them.
- **Recommendation:** 
  - Keep **KF301** or upgrade to **DG128/KF128V-5.08** with higher torque rating for field wiring.
  - Add **JST-XH or Molex Mini-Fit Jr** shrouded connectors for internal connections (encoder pigtails, display, remote).
  - For the enclosure entry, use **PG7 cable glands** with the gland nut clamping the cable jacket. Inside the box, transition to pluggable terminal blocks or JST connectors.
- **Cost:** Minimal difference.

---

## 7. Firmware Update Mechanisms

### 7.1 Current State
- USB cable + PlatformIO (`pio run --target upload`).
- Requires physical access.

### 7.2 OTA via WiFi — **HIGH IMPACT / LOW COST**
- **Status:** Not currently implemented, but trivial to add.
- **Approach:** `ElegantOTA` (AsyncElegantOTA successor) or ArduinoOTA. Integrates cleanly with existing ESPAsyncWebServer.
- **Security:** Add a password hash check; do NOT leave OTA open on factory floors.
- **Cost:** ₺0 hardware, ~2 hours firmware.
- **Verdict:** **Do this immediately.** It eliminates the #1 support burden ("I need to walk to the crane with a laptop to update firmware").

### 7.3 USB-C Instead of Micro-USB — **HIGH IMPACT / LOW COST**
- **Why:** Micro-USB connectors have a rated insertion life of ~10,000 cycles; in practice, the through-hole variants on dev boards fail after ~200 rough insertions. USB-C is rated for 10,000 cycles and is now the universal standard.
- **Implementation:** 
  - If keeping the Wemos D1 R32 dev board form factor: the board already has micro-USB. Change nothing on carrier PCB.
  - **For a custom ESP32 module design:** Use a mid-mount USB-C 2.0 receptacle (16-pin, no SuperSpeed). Only needs CC pull-down resistors + ESD diode.
- **Parts:** USB-C 2.0 mid-mount (LCSC C2988369 ~$0.25; AliExpress ~₺10 for 10pcs).
- **Cost:** Negligible.
- **Verdict:** **Use USB-C on any custom ESP32 carrier design.** If staying with the Wemos D1 R32 plug-in module, this is out of scope for the carrier PCB.

### 7.4 SD Card Firmware Update — **MEDIUM IMPACT / LOW COST**
- **Why:** Fallback when WiFi credentials are wrong or WiFi is dead.
- **Implementation:** On boot, check SD card for `firmware.bin`. If present and CRC valid, flash and reboot. Arduino `Update` library supports this.
- **Cost:** ₺0 extra if SD slot already present.

---

## 8. Sourcing Guide (Turkey / LCSC / AliExpress)

| Component | Turkey Source | LCSC Part # / Price | AliExpress Price (approx.) |
|-----------|---------------|---------------------|---------------------------|
| ESP32-WROOM-32U | Direnc.net, Komponentci | C82899 ~$2.80 | ₺90–110 |
| TJA1051T/3 CAN XCVR | Moser Elektronik | C89552 ~$0.80 | ₺25–40 |
| SN65HVD230 CAN XCVR | Direnc.net | C46926 ~$1.20 | ₺25–40 |
| MAX485EESA+ RS-485 | Direnc.net | C116736 ~$0.60 | ₺15 for 10pcs |
| W5500 chip | Komponentci | C91153 ~$2.50 | ₺90–130 module |
| DS3231SN RTC | Direnc.net | C5186 ~$3.50 | ₺60–80 module |
| CR2032 holder | Direnc.net | C2884835 ~$0.15 | ₺10 for 10pcs |
| Micro SD socket | — | C91145 ~$0.35 | ₺15 for 5pcs |
| W25Q128JVSIQ | Komponentci | C97521 ~$0.80 | ₺20 |
| TPS3823-33DBVR | Moser Elektronik | C132142 ~$0.40 | ₺50 for 10pcs |
| PC817 optocoupler | Direnc.net | C106090 ~$0.08 | ₺15 for 50pcs |
| MCP4725 DAC (module) | — | — | ₺30 |
| XTR111AIDGST | — | C158788 ~$4.50 | ₺80–100 |
| USB-C 2.0 receptacle | — | C2988369 ~$0.25 | ₺10 for 10pcs |
| DIN rail clip (Arduino) | — | — | ₺25–40 |
| IP54 ABS enclosure 150×100×70 | — | — | ₺50–100 |
| PG7 cable gland | — | — | ₺10–15 each |
| u.FL to SMA pigtail | Direnc.net | — | ₺25–40 |

**Turkey distributors:**
- **Direnc.net** (Istanbul) — good for semiconductors, passives, connectors.
- **Komponentci.com** — LCSC-like selection, reasonable shipping.
- **Moser Elektronik** (Ankara) — TI, Analog Devices specialist.
- **SAMM Market** — connectors, enclosures, consumables.

---

## 9. Recommended PCB Redesign Action List

### Phase A — Essential (do first, <₺50 BOM increase)
1. **Change ESP32 module** to WROOM-32U; add u.FL keep-out + SMA bulkhead hole.
2. **Add I2C header** (GPIO 21/22) with pull-ups and TVS.
3. **Add SPI/SD header** — remap Wire-Z to GPIO 27; free VSPI for SD card and W5500.
4. **Add UART2 header** — remap Wire A/B to GPIO 26/33; free GPIO 16/17 for RS-485.
5. **Add DS3231 RTC** footprint + CR2032 holder on I2C bus.
6. **Add 4 spare GPIOs** to 2.54mm header.
7. **Add 3 extra status LEDs** (WiFi, Activity, Fault) on GPIO 0/2/25.
8. **Add micro-SD socket** on SPI bus.
9. **Replace micro-USB** with USB-C if designing a custom ESP32 carrier.

### Phase B — Industrial Options (DNP by default, ₺50–200 when populated)
10. **Add W5500 Ethernet module header** (2×5 2.54mm).
11. **Add RS-485 transceiver** footprint (MAX485/SP485) with termination jumper.
12. **Add CAN transceiver** footprint (SN65HVD230 or TJA1051T/3) with termination.
13. **Add TPS3823 external watchdog** footprint.
14. **Add 1× relay output** footprint.
15. **Add 2× 4-20mA loop transmitter** footprints (DAC + V-to-I).

### Phase C — Enclosure & Mechanical
16. **Add M3 mounting holes** matching DIN rail carrier spacing (105mm × 65mm centers).
17. **Add cable gland keep-out outlines** on silkscreen (suggest PG7/PG9 positions).
18. **Conformal coat** production boards.
19. **Specify IP54 enclosure** with gland plate in BOM.

### Phase D — Firmware (parallel to hardware)
20. Implement **ElegantOTA** WiFi update.
21. Implement **SD card CSV logging**.
22. Implement **SD card firmware update** fallback.
23. Add **Modbus RTU** slave register map over UART2.
24. Add **CANopen CiA 406** object dictionary over TWAI (if CAN populated).

---

## 10. Pin Map Proposal (Redesigned PCB)

| GPIO | Function | Notes |
|------|----------|-------|
| 14 | Theta A | Encoder (quadrature) |
| 12 | Theta B | Encoder (quadrature) |
| 32 | Phi A | Encoder (quadrature) |
| 35 | Phi B | Encoder (quadrature) |
| 26 | Wire A | Encoder (quadrature) — remapped from 16 |
| 33 | Wire B | Encoder (quadrature) — remapped from 17 |
| 27 | Wire Z | Index pulse (input-only OK) — remapped from 18 |
| 36 | Battery ADC | Input-only, 1/2 divider |
| 25 | Battery Low LED | Output |
| 2 | WiFi/Status LED | Output (has onboard LED on devkit) |
| 0 | Activity LED | Output (boot mode strap — OK if pulled up) |
| 4 | Watchdog WDI / CAN TX | Output |
| 5 | SPI CS (SD / W5500) / CAN RX | Output |
| 18 | VSPI SCK | SD card + W5500 |
| 19 | VSPI MISO | SD card + W5500 |
| 23 | VSPI MOSI | SD card + W5500 |
| 21 | I2C SDA | RTC, OLED, IMU, DAC |
| 22 | I2C SCL | RTC, OLED, IMU, DAC |
| 16 | UART2 RX | RS-485 (Modbus) |
| 17 | UART2 TX | RS-485 (Modbus) |
| 34, 39 | Spare inputs | Limit switches, 4-20mA readback |

**Total used:** 26 GPIOs. **Remaining:** GPIO 1, 3, 13, 15 (some have boot/strap restrictions).

---

*Document prepared for EVKA positioning system hardware redesign. Review against `docs/research/improvement_research.md` and `docs/hardware_design/system_architecture.md` before finalizing KiCad netlist.*
