# 5V PCB v2 — Improved Design for LPKF S63

**Status:** Design finalized after procurement audit (2026-05-08), KiCad capture in progress
**Substrate:** FR4, 120×80mm, 2-layer
**Milling:** LPKF S63 mechanical PCB milling
**MCU:** **ESP32-S3-DevKitC-1 N16R8** *(changed 2026-05-08, was Wemos D1 R32)*
**Battery:** 1S LiPo 2000mAh, onboard 1A charging via TP4056+DW01A

This is the improved successor to `docs/hardware_design/5v/`. After component procurement (May 2026), the design diverged from the original spec in several places. `KICAD_PLAN_DETAILED.md` remains the canonical "what gets built"; `circuit_schematic.md` and `bill_of_materials.md` were reconciled to the as-built design on 2026-06-13 and now match Appendix A.

## Folder layout

This folder (`pcb_design/EVKA_position_v2/`) is the **single home** for the 5V v2 board — the KiCad project lives at the root; everything else is organized into subfolders:

```
pcb_design/EVKA_position_v2/
├── EVKA_position_v2.kicad_pro / .kicad_sch / .kicad_pcb / .kicad_prl   ← KiCad project (open the .kicad_pro)
├── evka.pretty/ , fp-lib-table                                        ← local footprint library
├── docs/      ← all design docs (this folder): KICAD_PLAN_DETAILED/BASIC, circuit_schematic,
│                 bill_of_materials, pcb_layout_guide, KICAD_AGENT_INSTRUCTIONS, KICAD_BUILD_LOG,
│                 TURKISH_SOURCING, README
├── exports/   ← generated outputs: EVKA_position_v2.pdf, EVKA_position_v2.svg
└── archive/   ← schematic backup (.orig), KiCad auto-backups, editor .history
```

The draft schematic is complete and ERC-clean (0 errors); see `KICAD_BUILD_LOG.md` for the full build history and the PCB-layout follow-ups.

## Documents

| File | Content | Status |
|---|---|---|
| `KICAD_PLAN_DETAILED.md` | **Authoritative**: full step-by-step KiCad workflow with final BOM, post-procurement deltas, and firmware port checklist | Current |
| `KICAD_PLAN_BASIC.md` | Quick-reference 13-step KiCad workflow | Current |
| `circuit_schematic.md` | ASCII schematic — reconciled to as-built (2026-06-13) | Current (mirrors Appendix A/C) |
| `bill_of_materials.md` | BOM, ~32 line items — reconciled to as-built (2026-06-13) | Current (mirrors Appendix A) |
| `pcb_layout_guide.md` | Zone layout, FR4/LPKF rules, assembly sequence | Mostly current; Zone D enlarged for DevKitC-1 (see detailed plan) |

Full design spec: `docs/superpowers/specs/2026-04-29-5v-pcb-v2-design.md`

## Procurement-Driven Design Changes (2026-05-08)

After ordering components from Turkish domestic suppliers (yurtdışı tedarik avoided where possible), the following were applied:

| Change | Reason |
|--------|--------|
| **USB-C dropped** | No Turkish supplier carries THT USB-C; ESP32-S3-DevKitC-1 has dual onboard USB-C |
| **LTC4412 ideal-diode dropped** → passive Schottky-OR with second 1N5822 | Specialty Analog Devices IC not stocked in Turkey; passive OR loses ~0.4 V vs 20 mV but acceptable |
| **MCU: Wemos D1 R32 → ESP32-S3-DevKitC-1 N16R8** | D1 R32 chronically OOS; S3 brings 16 MB flash + 8 MB PSRAM + native USB |
| **Q_RPP: AO3401 → PJA3441** (Panjit) | Drop-in SOT-23 substitute, in stock at direnc.net |
| **Schottky: SS34 (SMD label) → 1N5822-HT** (axial DO-201) | BOM labeling fix; axial part is 1N5822 |
| **Ferrite beads → 0Ω wire jumpers** | Axial 600 Ω@100 MHz ferrites unavailable domestically; resistor substitute would brown out E40S6 |
| **Encoder TVS×6 populated, general THT (part TBD)** | Flexible large-axial footprint (`D_DO-201AD_P15.24mm`) so any proper THT TVS can be soldered; pick bidir V_RWM ≥ ~3.34 V (1.5KE3.9CA ideal/import-only; on-hand 1.5KE3.3CA works but leaks slightly). Not the mis-ordered P6KE39CA (33 V). |
| **SW_RESET dropped** | DevKitC-1 has onboard RST button |
| **Discrete LED2 dropped** → onboard WS2812 RGB on GPIO 38 | Free LED on the dev board, drives richer status indication |
| **R_GPIO12 dropped** | ESP32-S3 strapping pins are 0/3/45/46, not 12 |

Net BOM change: **41 → 32 line items**, **80 → 64 parts**.

## Key Improvements Over 5v/

1. **FR4 substrate** — replaces pertinax; better copper adhesion, cleaner LPKF milled edges, 0.4mm isolation clearance (vs 0.5mm for pertinax)
2. **LTC4412 ideal diode** — replaces Schottky OR on external power path; only 20mV drop vs 350mV; `5V_RAIL` stays at 4.98V instead of 4.65V when on external power
3. **Dual 5V input** — USB-C THT + barrel jack 5.5/2.1mm, Schottky OR; run from any USB phone charger or bench supply
4. **AO3401 RPP MOSFET** — replaces SI2301 (hard to solder on LPKF); same SOT-23 package, −4A rated vs −3A, identical sourcing with LTC4412 switch
5. **74HC14N Schmitt trigger** — DIP-14, buffers all 6 encoder signal lines; resharpens edges degraded by cable capacitance and RC filter; genuine hysteresis removes GPIO threshold ambiguity
6. **10nF signal filter caps** — replaces 1nF; 74HC14N resharpens so RC corner can be lowered from 23.9kHz to 2.38kHz for better noise rejection
7. **MT3608 fixed output** — trim pot removed from module; 100kΩ/300kΩ resistor divider sets 5.0V precisely; eliminates vibration-induced output drift
8. **GPIO12 pull-down on Schmitt OUTPUT side** — 10kΩ between 74HC14N pin 8 and GND, on the trace to GPIO12; corrects the misplaced divider-side pull-down from the first draft (the inverter sits between input and GPIO, so an input-side pull-down does nothing for boot safety)
9. **GPIO36 ADC bypass** — 100nF ceramic at ADC input; reduces battery voltage measurement noise
10. **LPKF fiducial marks** — 3× corner copper dots; improves flip-and-drill alignment from ±0.2mm to ±0.05mm

### Added in 2026-04-30 review pass

11. **USB-C CC1/CC2 termination (5.1kΩ Rd × 2)** — without these the connector advertises "no device" and a compliant USB-C charger never asserts VBUS; was missing from the first v2 draft
12. **Input ESD protection (SMAJ5.0A × 2)** — one TVS each on USB-C VBUS and barrel-jack VIN+, *before* the OR-ing Schottky diodes, to shunt connector-side hot-plug / ESD transients
13. **Pi filter on 5V_RAIL (10µH + 10µF + 220µF)** — attenuates MT3608's 1.2 MHz switching noise by ~58 dB; protects encoder analog front-end from shared-supply ripple
14. **Encoder signal TVS — general THT, populated, part TBD (2026-06-19)** — flexible large-axial footprint takes any proper THT TVS. Selection guide: bidirectional, V_RWM ≥ ~3.34V (e.g. 1.5KE3.9CA) so it doesn't leak at the 3.33V divider HIGH; the old-board 1.5KE3.3CA (2.82V standoff) fits and works but leaks slightly there. Finalize the value when chosen.
15. **3.0mm trace width on V_EXT_RAW / V_EXT_PROT** — these carry up to 1.5A (1A charge + 0.5A run); 2.0mm at 18µm copper is only good for 1.3A
16. **SOT-23 / SOT-23-6 pad expansion** — 0.7×0.9mm and 0.6×0.8mm pads (vs library default 0.55×0.65mm) for cleaner LPKF milling and easier hand soldering with no soldermask
17. **74HC14N pin table rewritten with explicit DIP pin numbers** — the original ASCII box was ambiguous about which physical pin each input/output sat on (a wiring error there would land a signal on pin 7, GND, and destroy the IC)

## Firmware Changes Required (post-procurement)

1. **A/B pin swap for 74HC14N inversion** (still required from the original v2 design):
   ```cpp
   // 5v_v2 with 74HC14N inverter — swap A/B in Encoder constructors
   enc_theta = new Encoder(PIN_THETA_B, PIN_THETA_A);
   enc_phi   = new Encoder(PIN_PHI_B,   PIN_PHI_A);
   enc_wire  = new Encoder(PIN_WIRE_B,  PIN_WIRE_A);
   ```

2. **GPIO remap for ESP32-S3** (`firmware/src/SphericalSensor.h`):
   ```cpp
   #define PIN_THETA_A     4
   #define PIN_THETA_B     5
   #define PIN_PHI_A       6
   #define PIN_PHI_B       7
   #define PIN_WIRE_A     15
   #define PIN_WIRE_B     16
   #define PIN_BATTERY_ADC 1   // ADC1_CH0 (was GPIO36 on classic ESP32)
   #define PIN_RGB_LED    38   // onboard WS2812 (was discrete LED2 on GPIO25)
   ```

3. **New PlatformIO env** in `platformio.ini`:
   ```ini
   [env:esp32-s3-devkitc-1]
   platform = espressif32
   board = esp32-s3-devkitc-1
   framework = arduino
   board_build.flash_mode = qio
   board_build.flash_size = 16MB
   board_build.psram_type = opi
   monitor_speed = 115200
   build_flags = -DARDUINO_USB_CDC_ON_BOOT=1 -DBOARD_HAS_PSRAM
   lib_deps =
     paulstoffregen/Encoder@^1.4.4
     adafruit/Adafruit NeoPixel@^1.12
   ```

4. **WS2812 battery LED** — replace discrete LED2 calls with `Adafruit_NeoPixel`:
   - Green: ≥80% (V > 4.0 V)
   - Yellow: 20–80%
   - Red solid: <20%
   - Red blink: <10% (critical)

5. **R_GPIO12 boot-strap workaround removed** — ESP32-S3 strapping pins are 0/3/45/46, none of the new encoder GPIOs need a pull-down.

## Manufacturing Notes

- **Machine:** LPKF S63 (flip-and-drill for 2-layer)
- **Material:** FR4 1.55mm, 18µm (0.5oz) copper — use derated current tables (0.6× standard 35µm)
- **Vias:** Wire-link (tinned wire through 0.8mm hole, solder both sides, flush-cut)
- **SMD ICs after procurement:** Only **PJA3441** (SOT-23, Q_RPP) remains — LTC4412 and Q_SWITCH dropped. Use fresh isolation bits, 0.3 mm pad clearance with 3 milling passes, expand pads to 0.7×0.9 mm for hand-solder margin
- **Input ESD TVS (SMAJ5.0A × 1):** SMA package, surface-mount on the THT-otherwise board; one at J4 VIN+, *before* D_BAR (USB-C ESD removed with USB-C input)
- **No soldermask** on LPKF boards — tin power traces immediately after milling to prevent oxidation
- **Fiducials:** 3× corner pads, 0.5mm copper, no drill — add before running CircuitPro flip workflow
- **TVS footprints in Zone C (6×):** flexible large-axial (`D_DO-201AD_P15.24mm`) — **populated** with a general THT TVS (part TBD); no DNP
