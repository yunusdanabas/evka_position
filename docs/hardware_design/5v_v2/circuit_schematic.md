# Circuit Schematic — 5V PCB v2

Full ASCII schematic for the improved 5V board (LPKF S63, FR4, 120×80mm).

---

## Section 1: Dual Power Input + ESD + Reverse Polarity Protection

```
     J_USB (USB-C THT)                        J4 (Barrel 5.5/2.1mm)
     VBUS ──────┬──────────────               VIN+ ──────┬──────────
                │                                        │
            [TVS_USB]                                [TVS_BAR]
            SMAJ5.0A                                 SMAJ5.0A
            DO-214AC (SMA)                           DO-214AC (SMA)
            cathode→VBUS, anode→GND                  cathode→VIN+, anode→GND
                │                                        │
              [D_USB]                                  [D_BAR]
              SS34                                     SS34
              DO-201                                   DO-201
                │                                        │
                └────────────────────┬───────────────────┘
                                     │
                              V_EXT_RAW
                                     │
                    ┌────────────────┘
                    │
                  [Q_RPP]  AO3401 P-ch MOSFET (SOT-23)
                  Source ←── V_EXT_RAW
                  Gate  ←── R_RPP (100kΩ) ── GND
                  Drain ──►
                    │
                V_EXT_PROT ────────────────────────────────────┐
                                                               │
                                                    To Section 2 (LTC4412)
                                                    To Section 3 (TP4056 IN)

USB-C CC termination (mandatory for VBUS to be sourced by a compliant DFP):
   J_USB CC1 ─── [R_CC1] 5.1kΩ 1% ── GND
   J_USB CC2 ─── [R_CC2] 5.1kΩ 1% ── GND
   (Place both Rd resistors within ~5mm of the connector body.
    Without these, USB-C chargers do not detect the device and VBUS stays at 0V.)
```

**ESD protection note:**
- TVS_USB and TVS_BAR (SMAJ5.0A, unidirectional) sit *before* the OR-ing Schottky diodes — they shunt incoming transients (hot-plug, ESD strike on connector) directly to GND, before anything reaches Q_RPP gate oxide or the TP4056 input. Standoff Vrwm = 5.0V; Vbr min = 6.4V; safe at the typical USB-C 5.0–5.25V VBUS range with only nA leakage.

**Reverse polarity operation:**
- Correct polarity (5V): Vgs = 0 − 5V = −5V → Q_RPP ON → current flows
- Reversed polarity: Vgs = 0 − (−5V) = +5V → Q_RPP OFF → no current

---

## Section 2: LTC4412 Ideal Diode + MT3608 Boost → 5V_RAIL

```
V_EXT_PROT ─────┬───────────────────────────────────────────────────────┐
                │                                                        │
              [C_LTC]                                            [R_GATE]
              100nF                                              100kΩ
                │                                                        │
               GND                                         Q_SWITCH gate ┤
                                                                         │
                         LTC4412 (SOT-23-6)                              │
                         ┌─────────────┐                                 │
   V_EXT_PROT ───────── pin2 (VIN)    pin1 (GATE) ───────────────────────┘
              GND ─────  pin3 (GND)                         │
              GND ─────  pin5 (SHDN)  (active-LOW; GND = always enabled)
                         pin6 (PFO)  ── (float; power-fail flag, unused)
   5V_RAIL  ──────────  pin4 (SENSE)                        │
                         └─────────────┘                    │
   R_GATE (100kΩ) is a pull-UP from Q_SWITCH gate → V_EXT_PROT (= source).
   Vgs = 0 holds the P-FET OFF whenever LTC4412 is unpowered or asserts GATE high.
                                                            │
                                              Q_SWITCH: AO3401 P-ch (SOT-23)
                                              Source ←── V_EXT_PROT
                                              Gate   ←── LTC4412 GATE + R_GATE
                                              Drain  ──►
                                                         │
                                                    ┌────┘
                                                    │
          ┌───────── MT3608 module (boost) ─────────┤
          │          IN: LiPo BAT+ via DW01A        │
          │          OUT: 5.0V (fixed resistors)    │
          │                │                        │
          │           [C_BOOST] 22µF/10V ── GND     │
          │                │                        │
          │             [D_BOOST]                   │
          │             SS34 DO-201                 │
          │             (Schottky, 0.35V drop)      │
          │                │                        │
          │                └────► V_BOOST_OUT ──────┘
          │
          (V_BOOST_OUT = boost path output before pi filter, when battery powered)

Pi filter on 5V_RAIL — attenuates MT3608 1.2MHz switching noise:

  V_BOOST_OUT (battery path) ─┐
                              ├── joined to LTC4412 path ── PI_NODE ─── [L1] 10µH ─── 5V_RAIL
  Q_SWITCH drain (ext path) ──┘                                                          │
                                                                                         │
                              [C_PI] 10µF/10V ─── GND        [C1] 220µF/10V ─── GND      │
                                  (just before L1)                (after L1, star pt.)   │
                                                                                         │
  L1 = 10µH axial THT, Isat ≥ 1A (Bourns RLB0914-100KL or equiv.)                       │
  LC corner ≈ 16kHz → −58dB at MT3608 f_sw (1.2MHz)                                     │

5V_RAIL ──┬──── [C2] 100nF ─────── GND
           ├──── ESP32 Wemos D1 R32 (5V pin)
           ├──── J1 VCC (Theta encoder, via FB1 ferrite)
           ├──── J2 VCC (Phi encoder, via FB2 ferrite)
           ├──── J3 VCC (Wire encoder, via FB3 ferrite)
           ├──── [LED1] green ─── 1kΩ ─── GND  (power indicator)
           └──── [TP1] test point
```

**When external 5V present:**  
LTC4412 drives Q_SWITCH ON → 5V_RAIL = V_EXT_PROT − 20mV ≈ 4.98V  
MT3608 → D_BOOST path: 5.0V − 0.35V = 4.65V < 4.98V → D_BOOST reverse-biased → battery isolated

**When external absent:**  
Q_SWITCH OFF → MT3608 path active → 5V_RAIL = 4.65V (battery powered)

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
                                            J5 JST-PH 2-pin
                                              ├─ B+ → LiPo (+)
                                              └─ B− → LiPo (−) / GND

           LiPo B+ ─── R_MON1 (100kΩ) ─── ADC_MON ─── R_MON2 (100kΩ) ─── GND
                                              │
                                          [C_ADC] 100nF ── GND
                                              │
                                          GPIO36 (ADC1_CH0 — battery monitor)
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

## Section 5: Signal Conditioning (×7 channels)

One complete network shown. Repeat for: Theta A, Theta B (+ GPIO12 PD), Phi A, Phi B, Wire A, Wire B.

```
Encoder output (0–5V TTL push-pull — both encoders confirmed totem/LTP)
        │
        │  [Ferrite bead FB1/2/3 on VCC — not on signal]
        │
      [R_TOP] 10kΩ, 1% metal film, 1/4W
        │
  DIVIDER_NODE ─────────────── [TVS] 1.5KE3.9CA ─── GND
        │                       DO-201 bidirectional
        │                       Vrwm = 3.34V (sits just above the
        │                       3.33V divider HIGH → no leakage sag)
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
     74HC14N input (one of pins 1,3,5,9,11,13)
     VCC = 3.3V (from ESP32 Wemos 3.3V pin)
        │
     74HC14N output (one of pins 2,4,6,8,10,12)
        │ (inverted: encoder HIGH → output LOW, encoder LOW → output HIGH)
        │
     ESP32 GPIO (see pin map table)

GPIO12 strapping safety (Theta B output line ONLY):
  74HC14N pin 8 (4Y output) ── trace ──┬── GPIO12
                                       │
                                  [R_GPIO12] 10kΩ
                                       │
                                      GND

  Why on the OUTPUT side: at boot, encoder is at rest → encoder LOW (0V) →
  divider node 0V → Schmitt input LOW → Schmitt output HIGH (it inverts).
  GPIO12 must be LOW at boot (strapping pin selects flash voltage on some
  ESP32 modules). A pull-down on the *input* (divider) side does nothing
  because the inverter sits between it and GPIO12. The 10kΩ pull-down on
  the output line dominates the Schmitt's source current at boot before
  VCC stabilises, holding GPIO12 ≈ GND. Once VCC is up, Schmitt sources
  ~4mA at HIGH → 10kΩ to GND draws 0.33mA, well within drive limits.
```

### 74HC14N Full Connection (DIP-14, VCC = pin14 @ 3.3V, GND = pin7)

| DIP pin | Gate function | Net |
|---|---|---|
| 1 | 1A (input) | Theta A divider node |
| 2 | 1Y (output) | → GPIO14 |
| 3 | 2A (input) | Theta B divider node |
| 4 | 2Y (output) | → GPIO12 (with R_GPIO12 10kΩ to GND) |
| 5 | 3A (input) | Phi A divider node |
| 6 | 3Y (output) | → GPIO32 |
| 7 | GND | board GND |
| 8 | 4Y (output) | → GPIO35 |
| 9 | 4A (input) | Phi B divider node |
| 10 | 5Y (output) | → GPIO16 |
| 11 | 5A (input) | Wire A divider node |
| 12 | 6Y (output) | → GPIO17 |
| 13 | 6A (input) | Wire B divider node |
| 14 | VCC | 3.3V (from ESP32 onboard regulator) |

100nF ceramic bypass between pin 14 and pin 7, placed within 5mm of the IC.

```
              74HC14N (DIP-14, top view, notch at top)
                ┌────────U────────┐
   Theta A ──── │ 1 (1A)  14 (VCC)│ ──── 3.3V
        GPIO14 ─│ 2 (1Y)  13 (6A) │ ──── Wire B
   Theta B ──── │ 3 (2A)  12 (6Y) │ ──── GPIO17
        GPIO12 ─│ 4 (2Y)  11 (5A) │ ──── Wire A
     Phi A ──── │ 5 (3A)  10 (5Y) │ ──── GPIO16
        GPIO32 ─│ 6 (3Y)   9 (4A) │ ──── Phi B
           GND ─│ 7 (GND)  8 (4Y) │ ──── GPIO35
                └─────────────────┘
              [100nF bypass: pin14 ↔ pin7]
```

---

## Section 6: Encoder VCC Filtering

```
5V_RAIL ──── [FB1] Ferrite 600Ω@100MHz ─── J1 pin VCC (Theta encoder 5V)
          │                                 [100nF] ── GND (at J1 VCC pin)
          │
          ──── [FB2] Ferrite 600Ω@100MHz ─── J2 pin VCC (Phi encoder 5V)
          │                                  [100nF] ── GND (at J2 VCC pin)
          │
          ──── [FB3] Ferrite 600Ω@100MHz ─── J3 pin VCC (Wire encoder 5V)
                                             [100nF] ── GND (at J3 VCC pin)
```

---

## Section 7: ESP32 Wemos D1 R32 + Indicators

```
5V_RAIL ─────────────────────────── ESP32 5V pin
                                     │
                                   AMS1117-3.3 (onboard regulator)
                                     │
                                   3.3V rail ───────── 74HC14N VCC (pin14)
                                                    ── [TP2] test point

ESP32 GPIO25 ─── [R_LED2] 1kΩ ─── LED2 (red, battery low) ─── GND

5V_RAIL ──── [R_LED1] 1kΩ ─── LED1 (green, power on) ─── GND

ESP32 RESET pin ─── RESET button ─── GND
                                      (momentary push, normally open)

Test points:
  TP1: 5V_RAIL       (4.65V battery, 4.98V external)
  TP2: 3.3V (ESP32)  (target: 3.3V ±0.1V)
  TP3: MT3608 output (target: 5.0V ±0.1V, verify under 415mA load)
  TP4: LiPo BAT+     (3.0–4.2V range)
  TP5: GND reference
```

**GPIO35 floating-input warning:** GPIO34/35/36/39 are input-only on the
ESP32 and have no internal pull resistors. The R_BOT (20kΩ) divider leg
to GND is the only pull on the GPIO35 line. If the Phi encoder is
disconnected, GPIO35 still sees a defined LOW through R_BOT, so this is
safe — but if R_BOT is omitted on assembly the pin floats and produces
phantom counts. Verify R_BOT presence at the Phi B divider during the
Phase 3 checkpoint.

---

## Connector Pinout Reference

### J1 — Theta Encoder (KF301-4P, 5.0mm pitch)
| Pin | Signal | Note |
|---|---|---|
| 1 | GND | Shield/GND |
| 2 | VCC | 5V via FB1 ferrite |
| 3 | A | Theta A, 0–5V TTL |
| 4 | B | Theta B, 0–5V TTL |

### J2 — Phi Encoder (KF301-4P, 5.0mm pitch)
| Pin | Signal | Note |
|---|---|---|
| 1 | GND | |
| 2 | VCC | 5V via FB2 ferrite |
| 3 | A | Phi A, 0–5V TTL |
| 4 | B | Phi B, 0–5V TTL |

### J3 — Wire Encoder (KF301-5P, 5.0mm pitch)
| Pin | Signal | Note |
|---|---|---|
| 1 | GND | |
| 2 | VCC | 5V via FB3 ferrite |
| 3 | A | Wire A, 0–5V TTL |
| 4 | B | Wire B, 0–5V TTL |
| 5 | Z | Index pulse (optional, no conditioning circuit) |

### J4 — DC Barrel Jack (5.5/2.1mm)
| Pin | Signal |
|---|---|
| Center | VIN+ |
| Shield | GND |

### J_USB — USB-C THT (TYPE-C-31-M-12 or equivalent)
| Pin | Signal | Note |
|---|---|---|
| VBUS | V_EXT_RAW (via TVS_USB + D_USB) | Connect to TVS_USB cathode and D_USB anode |
| GND | GND | Connect to board GND |
| CC1 | Rd to GND | **Required** — 5.1kΩ 1% to GND (R_CC1) |
| CC2 | Rd to GND | **Required** — 5.1kΩ 1% to GND (R_CC2) |
| D+, D− | NC | Leave unconnected (data not used) |
| Shell | GND | Solder shield to GND |

Without R_CC1 and R_CC2 a compliant USB-C source will not apply VBUS — the connector advertises "no device attached" and the charger stays at 0V.

### J5 — LiPo (JST-PH 2-pin)
| Pin | Signal |
|---|---|
| 1 | BAT+ (red) |
| 2 | BAT− (black/GND) |

### J6 — Test Input (KF128V-3.5mm, 2-pin)
| Pin | Signal |
|---|---|
| 1 | 5V test input |
| 2 | GND |
