# Circuit Schematic — 5V PCB v2

> **As-built reconciliation (2026-06-13):** updated to match KICAD_PLAN_DETAILED.md Appendix A (post-procurement). Earlier revisions described the pre-procurement concept.

> The sections below now describe the **as-built** design. `KICAD_PLAN_DETAILED.md` (Phase 2 Steps 5–10 + Appendices A/C) remains the authoritative source; this file mirrors it. Key as-built facts: single barrel-jack input (USB-C dropped); passive Schottky-OR with two 1N5822 (no LTC4412); reverse-polarity MOSFET = PJA3441; ferrite beads → 0Ω wire jumpers; encoder TVS×6 = populated (general THT, flexible footprint, part still placeholder `D_TVS`); MCU = ESP32-S3-DevKitC-1 N16R8; encoders on GPIO 4/5/6/7/15/16; battery ADC on GPIO1; status LED = onboard WS2812 on GPIO38 (no discrete LED2, no SW_RESET). Also as-built (added beyond Appendix A): two-button block J_SW1 with R_SW1/2 pull-ups + C_SW1/2 debounce on **BTN1=GPIO17 / BTN2=GPIO18**, and a 2×6 AUX expansion header J_EXP1 with R_AUX1–4 100Ω series on **GPIO11/12/13/14**. Screw terminals are Phoenix MKDS 5.0mm (KF301 pad-compatible); test points TP1–TP6 (TP6=GND).

Full ASCII schematic for the improved 5V board (LPKF S63, FR4, 120×80mm).

---

## Section 1: Single 5V Input + ESD + Reverse Polarity Protection

> As-built: USB-C input dropped. `J_USB`, `R_CC1`, `R_CC2`, `TVS_USB`, `D_USB` are removed — the ESP32-S3-DevKitC-1 module's dual onboard USB-C handles programming/console. Single 5V input via barrel jack `J4` only. Q_RPP is now **PJA3441**; the axial Schottky is labeled **1N5822-HT (DO-201)** (was mislabeled "SS34").

```
                                              J4 (Barrel 5.5/2.1mm)
                                              VIN+ ──────┬──────────
                                                         │
                                                     [TVS_BAR]
                                                     SMAJ5.0A
                                                     DO-214AC (SMA)
                                                     cathode→VIN+, anode→GND
                                                         │
                                                       [D_BAR]
                                                       1N5822-HT
                                                       DO-201 axial
                                                         │
                                                         │
                                                  V_EXT_RAW
                                                         │
                                        ┌────────────────┘
                                        │
                  [Q_RPP]  PJA3441 P-ch MOSFET (SOT-23, −40V/−3.1A/74mΩ)
                  Source ←── V_EXT_RAW
                  Gate  ←── R_RPP (100kΩ) ── GND
                  Drain ──►
                    │
                V_EXT_PROT ────────────────────────────────────┐
                                                               │
                                          To Section 2 (Schottky-OR, D_EXT)
                                          To Section 3 (TP4056 IN)
```

**ESD protection note:**
- TVS_BAR (SMAJ5.0A, unidirectional) sits *before* the OR-ing Schottky diode — it shunts incoming transients (hot-plug, ESD strike on connector) directly to GND, before anything reaches the Q_RPP gate oxide or the TP4056 input. Standoff Vrwm = 5.0V; Vbr min = 6.4V; safe at the typical 5.0–5.25V input range with only nA leakage.

**Reverse polarity operation:**
- Correct polarity (5V): Vgs = 0 − 5V = −5V → Q_RPP ON → current flows
- Reversed polarity: Vgs = 0 − (−5V) = +5V → Q_RPP OFF → no current

---

## Section 2: Passive Schottky-OR + Pi Filter → 5V_RAIL

> As-built: the LTC4412 ideal-diode path is dropped. `U_IDEAL` (LTC4412), `Q_SWITCH`, `R_GATE`, `C_LTC` are removed. Power merge is a passive Schottky-OR using two 1N5822-HT axial diodes — **D_EXT** (external path) and **D_BOOST** (battery path) — both feeding **PI_NODE**. External-power 5V_RAIL is ~4.6V (one Schottky drop vs the LTC4412's 20mV), still within the ESP32-S3 5V tolerance and the onboard LDO dropout headroom.

```
External path:
  V_EXT_PROT ──── [D_EXT] 1N5822-HT (DO-201 axial) ──┐
                                                     │
                                                  PI_NODE ─── [L1] 10µH ─── 5V_RAIL
Battery path:                                        │                       │
  ┌───────── MT3608 module (boost) ─────────┐        │                       │
  │   IN: LiPo BAT+ via DW01A               │        │                       │
  │   OUT: 5.0V (fixed FB resistors)        │        │                       │
  │        │                                │        │                       │
  │   [C_BOOST] 22µF/10V ── GND             │        │                       │
  │        │                                │        │                       │
  │     [D_BOOST] 1N5822-HT (DO-201 axial) ─┼────────┘                       │
  │        (Schottky, ~0.35V drop)          │                                │
  └─────────────────────────────────────────┘                                │
                                                                             │
Pi filter on 5V_RAIL — attenuates MT3608 1.2MHz switching noise:            │
                                                                             │
  [C_PI] 10µF/10V ─── GND        [C1] 220µF/10V ─── GND                      │
     (just before L1)                (after L1, star pt.)                    │
                                                                             │
  L1 = 10µH axial THT, Isat ≥ 1A (generic 10µH 1A radial or equiv.)         │
  LC corner ≈ 16kHz → −58dB at MT3608 f_sw (1.2MHz)                         │

5V_RAIL ──┬──── [C2] 100nF ─────── GND
           ├──── ESP32-S3-DevKitC-1 J1 pin 21 (5V pin)
           ├──── J1 VCC (Theta encoder, via J_FB1 0Ω jumper)
           ├──── J2 VCC (Phi encoder, via J_FB2 0Ω jumper)
           ├──── J3 VCC (Wire encoder, via J_FB3 0Ω jumper)
           ├──── [LED1] green ─── 1kΩ (R_LED1) ─── GND  (power indicator)
           └──── [TP1] test point
```

**When external 5V present:**  
D_EXT conducts → 5V_RAIL = V_EXT_PROT − ~0.35V ≈ 4.6V  
MT3608 → D_BOOST path: 5.0V − 0.35V = 4.65V ≈ D_EXT output → whichever path is higher conducts; battery contributes only if external sags. Both Schottkys OR cleanly into PI_NODE.

**When external absent:**  
D_EXT reverse-biased → MT3608/D_BOOST path active → 5V_RAIL ≈ 4.65V (battery powered)

---

## Section 3: Charging Path (TP4056 + DW01A)

```
V_EXT_PROT ─────────────────────────► TP4056 module
                                       │  IN+:  V_EXT_PROT
                                       │  IN−:  GND
                                       │  PROG: 1.2kΩ (1A charge, on module)
                                       │  CHRG: LED (charging indicator, on module)
                                       │  STDBY: LED (charge done, on module)
                                       │
                                       BAT+ ──► DW01A+FS8205 module
                                               │
                                               B+ ─────────┐
                                                           │
                                            J5 (2.25mm 2-pin female socket)
                                              ├─ B+ → LiPo (+)   (cable is male)
                                              └─ B− → LiPo (−) / GND

           LiPo B+ ─── R_MON1 (100kΩ) ─── ADC_MON ─── R_MON2 (100kΩ) ─── GND
                                              │
                                          [C_ADC] 100nF ── GND
                                              │
                                          GPIO1 (ADC1_CH0 — battery monitor, J3 pin 4)
                                          At 4.2V full:  ADC = 2.10V
                                          At 3.0V empty: ADC = 1.50V

           LiPo B+ ─────────────────────────────────────────► MT3608 module IN
                                                              (Section 2 boost)

           TP4 test point: LiPo voltage
```

---

## Section 4: MT3608 Module — Fixed Output Modification

```
MT3608 module internal (after modification):
                                    ┌── VOUT (5.0V out)
                                    │
                           R_MT_HI (300kΩ)
                                    │
                                   FB pin ── MT3608 internal (regulates to 1.25V)
                                    │
                           R_MT_LO (100kΩ)
                                    │
                                   GND

Vout = 1.25V × (1 + 300k/100k) = 1.25V × 4 = 5.0V

Note: Remove the trim pot and original resistors from module before soldering R_MT_HI/R_MT_LO.
Verify: connect 12Ω/2W load (415mA), measure VOUT = 5.0V ±0.1V before installing on board.
```

---

## Section 5: Signal Conditioning (×6 channels)

One complete network shown. Repeat for: Theta A, Theta B, Phi A, Phi B, Wire A, Wire B.

> As-built notes:
> - **No GPIO12 boot pull-down.** `R_GPIO12` is dropped — the ESP32-S3 strapping pins are GPIO 0/3/45/46, and none of the chosen encoder GPIOs (4/5/6/7/15/16) is a strapping pin.
> - **Encoder VCC ferrite → 0Ω wire jumper** at J_FB1/J_FB2/J_FB3 (Section 6).
> - **TVS×6 populated, general THT part, flexible footprint (decision 2026-06-19).** Footprint = `Diode_THT:D_DO-201AD_P15.24mm_Horizontal` (large-axial, takes a DO-15 or DO-201 body by forming leads). Part **TBD** — pick a bidirectional TVS with V_RWM ≥ ~3.34 V (e.g. 1.5KE3.9CA, import-only); the on-hand 1.5KE3.3CA fits and works but leaks slightly at the 3.33 V HIGH. The wrongly-ordered P6KE39CA (33 V) is not used.
> - GPIOs are the ESP32-S3 set: Theta A/B = 4/5, Phi A/B = 6/7, Wire A/B = 15/16.

```
Encoder output (0–5V TTL push-pull — both encoders confirmed totem/LTP)
        │
        │  [0Ω jumper J_FB1/2/3 on VCC — not on signal]
        │
      [R_TOP] 10kΩ, 1% metal film, 1/4W
        │
  DIVIDER_NODE ─────────────── [TVS] D_DO-201AD flexible THT footprint — populated
        │                       (general bidir THT TVS, V_RWM ≥ ~3.34V; part TBD)
        │
      [C_FILT] 10nF C0G
        │         (RC corner: 6.67kΩ × 10nF = 2.38kHz)
        │
       GND ─── [R_BOT] 20kΩ, 1% metal film, 1/4W
        (R_BOT between DIVIDER_NODE and GND, in parallel with C_FILT)

  DIVIDER_NODE
        │
        │ (at 5V encoder HIGH: node = 5×20/(10+20) = 3.33V)
        │ (at 0V encoder LOW:  node = 0V)
        │
     74HC14 input (one of pins 1,3,5,9,11,13)
     VCC = 3.3V (from DevKitC-1 J1 pin 1/2)
        │
     74HC14 output (one of pins 2,4,6,8,10,12)
        │ (inverted: encoder HIGH → output LOW, encoder LOW → output HIGH)
        │
     ESP32-S3 GPIO (see pin map table)
```

**Inverter A/B swap:** the 74HC14 inverts each channel, so firmware swaps A/B in the `Encoder` constructors (`new Encoder(PIN_x_B, PIN_x_A)`) to keep the count direction correct.

### 74HC14 Full Connection (DIP-14, VCC = pin14 @ 3.3V, GND = pin7)

| DIP pin | Gate function | Net |
|---|---|---|
| 1 | 1A (input) | Theta A divider node |
| 2 | 1Y (output) | → GPIO4 |
| 3 | 2A (input) | Theta B divider node |
| 4 | 2Y (output) | → GPIO5 |
| 5 | 3A (input) | Phi A divider node |
| 6 | 3Y (output) | → GPIO6 |
| 7 | GND | board GND |
| 8 | 4Y (output) | → GPIO7 |
| 9 | 4A (input) | Phi B divider node |
| 10 | 5Y (output) | → GPIO15 |
| 11 | 5A (input) | Wire A divider node |
| 12 | 6Y (output) | → GPIO16 |
| 13 | 6A (input) | Wire B divider node |
| 14 | VCC | 3.3V (from DevKitC-1 onboard LDO) |

100nF ceramic bypass (**C_SCHM**) between pin 14 and pin 7, placed within 5mm of the IC.

```
              74HC14 (DIP-14, top view, notch at top)
                ┌────────U────────┐
   Theta A ──── │ 1 (1A)  14 (VCC)│ ──── 3.3V
        GPIO4 ──│ 2 (1Y)  13 (6A) │ ──── Wire B
   Theta B ──── │ 3 (2A)  12 (6Y) │ ──── GPIO16
        GPIO5 ──│ 4 (2Y)  11 (5A) │ ──── Wire A
     Phi A ──── │ 5 (3A)  10 (5Y) │ ──── GPIO15
        GPIO6 ──│ 6 (3Y)   9 (4A) │ ──── Phi B
           GND ─│ 7 (GND)  8 (4Y) │ ──── GPIO7
                └─────────────────┘
              [C_SCHM 100nF bypass: pin14 ↔ pin7]
```

---

## Section 6: Encoder VCC Filtering

> As-built: ferrite beads replaced with **0Ω wire jumpers** at J_FB1/J_FB2/J_FB3. The encoders draw ~80 mA; a series resistor (even 10Ω) would drop ~0.8V and brown out the E40S6 (needs ≥4.5V), so a real ferrite (DC R < 0.5Ω) or a 0Ω link is required. The axial footprint is preserved so a Murata BL01RN1A1D (or equiv.) ferrite can drop in later. The C_VCC bypass caps at each connector preserve local HF filtering.

```
5V_RAIL ──── [J_FB1] 0Ω wire jumper ─── J1 pin VCC (Theta encoder 5V)
          │   (axial footprint, ferrite-ready)  [C_VCC 100nF] ── GND (at J1 VCC pin)
          │
          ──── [J_FB2] 0Ω wire jumper ─── J2 pin VCC (Phi encoder 5V)
          │                               [C_VCC 100nF] ── GND (at J2 VCC pin)
          │
          ──── [J_FB3] 0Ω wire jumper ─── J3 pin VCC (Wire encoder 5V)
                                          [C_VCC 100nF] ── GND (at J3 VCC pin)
```

---

## Section 7: ESP32-S3-DevKitC-1 N16R8 + Indicators

> As-built: MCU is the **ESP32-S3-DevKitC-1 N16R8** (ESP32-S3-WROOM-1, 16MB flash + 8MB PSRAM, dual onboard USB-C) on **2× 1×22 female sockets, 22.86 mm row spacing**. Status indication uses the **onboard WS2812 RGB LED on GPIO38** — the discrete `LED2` + `R_LED2` are dropped. `SW_RESET` is dropped (DevKitC-1 has an onboard RST button). The onboard 5V→3.3V LDO supplies the 3.3V rail.

```
5V_RAIL ─────────────────── DevKitC-1 J1 pin 21 (5V pin)
                                     │
                                   onboard 5V→3.3V LDO
                                     │
                                   3.3V rail ───────── 74HC14 VCC (pin14, via C_SCHM)
                                                    ── [TP2] test point

GPIO38 ─── onboard WS2812 RGB LED (battery status: green/yellow/red/blink)
           (single-wire 800kHz; driven via Adafruit_NeoPixel / FastLED)

5V_RAIL ──── [R_LED1] 1kΩ ─── LED1 (green, power on) ─── GND

RESET: onboard RST button on the DevKitC-1 (no discrete SW_RESET on the carrier board)

Test points:
  TP1: 5V_RAIL       (≈4.6V external, ≈4.65V battery)
  TP2: 3.3V (DevKitC-1 LDO)  (target: 3.3V ±0.1V)
  TP3: MT3608 output (target: 5.0V ±0.1V, verify under 415mA load)
  TP4: LiPo BAT+     (3.0–4.2V range)
  TP5: GND reference
```

**ESP32-S3 GPIO notes:** the chosen encoder GPIOs (4/5/6/7/15/16) and the battery ADC
(GPIO1, ADC1_CH0) are all normal I/O. GPIO 35/36/37 are reserved for the octal SPI
flash/PSRAM on the N16R8 and must not be used. GPIO 19/20 are the native USB-OTG pins
(reserved). Each encoder signal line still has its R_BOT (20kΩ) leg to GND, which holds
the GPIO at a defined LOW if an encoder is disconnected — verify R_BOT presence during
the Phase 3 checkpoint to avoid phantom counts.

---

## Connector Pinout Reference

### J1 — Theta Encoder (KF301-4P, 5.0mm pitch)
| Pin | Signal | Note |
|---|---|---|
| 1 | GND | Shield/GND |
| 2 | VCC | 5V via J_FB1 0Ω jumper |
| 3 | A | Theta A, 0–5V TTL |
| 4 | B | Theta B, 0–5V TTL |

### J2 — Phi Encoder (KF301-4P, 5.0mm pitch)
| Pin | Signal | Note |
|---|---|---|
| 1 | GND | |
| 2 | VCC | 5V via J_FB2 0Ω jumper |
| 3 | A | Phi A, 0–5V TTL |
| 4 | B | Phi B, 0–5V TTL |

### J3 — Wire Encoder (KF301-4P, 5.0mm pitch)
| Pin | Signal | Note |
|---|---|---|
| 1 | GND | |
| 2 | VCC | 5V via J_FB3 0Ω jumper |
| 3 | A | Wire A, 0–5V TTL |
| 4 | B | Wire B, 0–5V TTL |

_(Z/index line: unused — not wired. Wire encoder uses the same 4-pin block as J1/J2 since only GND/VCC/A/B are needed. Earlier revs used a KF301-2P + KF301-3P ganged pair with Z on pin 5.)_

### J4 — DC Barrel Jack (5.5/2.1mm)
| Pin | Signal |
|---|---|
| Center | VIN+ |
| Shield | GND |

_(J_USB — USB-C THT — **removed** in the as-built design; the DevKitC-1 onboard USB-C handles programming/console.)_

### J5 — LiPo (2.25mm 2-pin female socket)
| Pin | Signal |
|---|---|
| 1 | BAT+ (red) |
| 2 | BAT− (black/GND) |

⚠ Pitch is 2.25 mm as labeled by the supplier — verify with calipers when the part arrives (could be 2.0 mm JST-PH or 2.5 mm JST-XH) and adjust the footprint before exporting Gerbers. PCB side is a **female socket** because the LiPo cable terminates in a male plug.

### J6 — Test Input (KF128V-3.5mm, 2-pin)
| Pin | Signal |
|---|---|
| 1 | 5V test input |
| 2 | GND |
