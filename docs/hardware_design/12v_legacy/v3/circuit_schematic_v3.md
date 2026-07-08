# Circuit Schematic — EVKA Position V3

> Simple 12V/15V ESP32-S3 carrier with internal 3S LiPo backup and discrete Q_BATT active load-sharing.  
> No onboard charger by default (V3-A). Optional charging zone for V3-B (CN3722) and V3-C (XL4016 CC/CV).  
> No RS-485, I2C expansion, external watchdog, or non-core interfaces.

---

## 1. Full System Block Diagram

```text
  J12V INPUT (12V for V3-A; 15V for V3-B/V3-C)
      |
      +-- NTC1 5D-9, optional inrush limiting
      |
      +-- F1 PTC 1.1A or 2A glass fuse
      |
      +-- TVS_IN P6KE18A to GND
      |
      +-- Q_RPP IRF4905 high-side reverse-polarity MOSFET
      |         Gate -> R_G 100k -> GND
      |
    V_PROT ──────────────────────────────────────────────→ BUCK_VIN
      |                                                          ↑
      +--[V3-B/V3-C CHARGING ZONE — leave empty for V3-A]       |
      |  CN3722 module (V3-B) or XL4016 CC/CV module (V3-C)     |
      |  Output: 12.60V, 0.5A                                    |
      |  LED_CHRG indicator                                       |
      |        |                                                  |
      |    CHARGE_OUT                                             |
      |        |                                                  |
      |    F_BAT 5A blade fuse (≤15cm from J_XT60+)             |
      |        |                                                  |
      |    BMS_3S HX-3S-01 (required)                            |
      |        |                                                  |
      |    J_XT60 BAT+ (3S LiPo main lead)         Q_BATT = IRF4905
      |    J_BAL JST-XH-4P (balance lead)          Source = J_XT60 BAT+
      |        |                                   Drain ──────────┘
      +──→ D_GATE SS14 anode  ─→  Q_BATT Gate ←── R_G2 100k ── GND
                                  Z1 1N4742A 12V Zener (Gate to GND)

  BUCK_VIN
      |
      +-- R_ADC_TOP 120k --+-- R_ADC_BOT 27k -- GND
      |                    |
      |                    +--> ESP32-S3 GPIO1 ADC
      |
      +-- C_IN1 220uF/35V + C_IN2 100nF
      |
      +-- U_BUCK MP1584EN module, to 5.05-5.10V
      |
      +-- L_FILT 22uH --+-- C_FILT 220uF/10V -- GND
                        |
                        +-- C_FILT_HF 100nF -- GND
                        |
                     5V_RAIL
                        |
                        +--> ESP32-S3 DevKitC VIN
                        +--> Power LED
                        +--> FB1 -> Theta encoder VCC
                        +--> FB2 -> Phi encoder VCC
                        +--> FB3 -> Wire encoder VCC

  ENCODER SIGNALS
      |
      +-- 7x 10k/20k divider + 1nF filter + 3.3V TVS
      |
      +--> ESP32-S3 GPIO 4,5,6,7,15,16,17
```

Q_BATT behavior:

| State | Gate voltage | Vgs | FET | BUCK_VIN source |
|---|---|---|---|---|
| Adapter present | ~V_PROT via D_GATE, clamped by Z1 to 12V | near 0V | OFF | V_PROT direct |
| Adapter absent | 0V via R_G2 pull-down | −V_BAT | ON | Battery via FET |

---

## 2. 12V/15V Input Protection

### 2a. Input Connector

Use a KF301-2P 5.08mm screw terminal (`J12V_TERM`) for all cabinet and machine wiring.

For bench use, a 5.5×2.1mm DC barrel jack footprint may optionally share the same net, but populate only one source at a time.

### 2b. Fuse / PTC

```text
J12V+ -> NTC1 -> F1 -> TVS/RPP input
```

Recommended default:

- `NTC1`: 5D-9 NTC, optional but recommended to limit inrush into C_IN1 on cold start
- `F1`: MF-R110 PTC (1.1A hold) or 2A glass fuse

Adapter-side fuse protects the adapter wiring. The battery path has its own mandatory F_BAT.

### 2c. TVS Clamp

```text
F1 output ----+---- TVS_IN ---- GND
              |
              +---- Q_RPP source
```

Default:

- `P6KE18A` for both 12V and 15V adapter configs (18V standoff is safely above 15V)
- `P6KE20A` if the adapter or cabinet rail can sit near 16–17V peak during load transients

### 2d. Reverse-Polarity MOSFET (Q_RPP)

```text
IRF4905, facing marked side, leads down:

Pin 1: Gate
Pin 2: Drain
Pin 3: Source
Tab:   Drain

F1 / TVS node  -> Source
R_G 100k       -> Gate -> GND
Drain / tab    -> V_PROT
```

Correct polarity: gate pulled low, Vgs negative, MOSFET conducts.  
Reverse polarity: MOSFET stays off and blocks current.

Do not bolt the tab to grounded metal. The tab is V_PROT.

---

## 3. 3S Battery Path

V3 uses an internal 3S LiPo RC pack with:

- XT60 main connector (`J_XT60`, onboard THT panel connector)
- JST-XH-4P balance connector (`J_BAL`, onboard THT panel header)
- External 3S balance charger for balancing (iMax B3, SkyRC E3S, or equivalent)
- Required HX-3S-01 protection/BMS module (or protected RC LiPo pack)

```text
J_XT60 BAT+ -> F_BAT blade fuse -> BMS_3S IN+ -> Q_BATT Source
J_XT60 BAT- ------------------------------------------> GND
J_BAL JST-XH-4P -> balance lead, external charger access only
```

For V3-B/V3-C: the charger module output feeds into the F_BAT → BMS → J_XT60 path (charging the battery). The Q_BATT Source is the BMS output (post-protection). The system load is powered by V_PROT directly, not through the battery.

Fuse placement rule:

- Place `F_BAT` within 15cm of `J_XT60` positive.
- Do not route unfused battery positive across the PCB.
- 5A ATO/ATC blade fuse for 1500–2200mAh packs.

---

## 4. Q_BATT Active Load-Sharing

Q_BATT selects the power source for `BUCK_VIN`:

- Adapter present → V_PROT connects directly to BUCK_VIN; Q_BATT OFF (battery isolated)
- Adapter absent → R_G2 pulls gate to GND; Q_BATT ON (battery powers BUCK_VIN)

### 4a. Gate Drive Circuit

```text
V_PROT ──→ D_GATE (SS14, anode V_PROT, cathode Gate)
Gate   ──→ R_G2 (100kΩ) ──→ GND
Gate   ──→ Z1 (1N4742A 12V Zener, cathode Gate, anode GND)
```

Z1 clamps the gate voltage to 12V max. This protects the MOSFET from excessive Vgs when the adapter is 15V, and ensures reliable turn-off at all battery states.

### 4b. IRF4905 Connections

```text
IRF4905, TO-220AB:

Pin 1 (Gate): Gate drive node (D_GATE / R_G2 / Z1)
Pin 2 (Drain): BUCK_VIN
Pin 3 (Source): BMS_3S output positive (post-protection battery node)
Tab (Drain): BUCK_VIN — do not ground the tab
```

V_PROT connects directly to BUCK_VIN (the adapter path has no switch — the adapter always drives BUCK_VIN when present). Q_BATT only controls the battery path.

### 4c. Behavior Table

| Adapter | Gate | Vgs | FET | BUCK_VIN |
|---|---|---|---|---|
| 15V present | ~12V (Z1 clamp) | ~12V − V_BAT ≈ 0 to +3V | OFF | V_PROT = 15V |
| 12V present | ~11.7V (D_GATE Vf ≈ 0.3V) | ~11.7V − V_BAT ≈ −0.3V to +2.7V | OFF | V_PROT = 12V |
| Absent | 0V (R_G2 pull-down) | −V_BAT (−9 to −12.6V) | ON | Battery = 9–12.6V |

---

## 5. Buck Converter and 5V Rail

### 5a. Buck Module

Default module:

- `MP1584EN` adjustable buck module
- Input: `BUCK_VIN`, 9.0–15.0V range (adapter or battery)
- Output preset: 5.05–5.10V under load

```text
BUCK_VIN -> C_IN1 220uF/35V -> U_BUCK VIN
GND -------------------------> U_BUCK GND
U_BUCK VOUT -> L_FILT 22uH -> 5V_RAIL
5V_RAIL -> C_FILT 220uF/10V + 100nF -> GND
```

Pre-set the buck output before inserting the ESP32-S3.

### 5b. 5V Distribution

```text
5V_RAIL
  +-> ESP32-S3 DevKitC VIN pins
  +-> LED_PWR -> 1k -> GND
  +-> FB1 -> J_THETA Pin 1
  +-> FB2 -> J_PHI Pin 1
  +-> FB3 -> J_WIRE Pin 1
```

Use star routing from the filtered 5V node. Do not daisy-chain encoder power through the ESP32 header.

---

## 6. ADC Divider

Monitor point: `BUCK_VIN` — shows actual supply voltage (adapter when adapter is present, battery when running on battery).

```text
BUCK_VIN -> 120k -> ADC_NODE -> GPIO1
ADC_NODE -> 27k -> GND
```

Scale:

```text
V_input = V_adc * (120k + 27k) / 27k
        = V_adc * 5.444
```

Expected ADC node values:

| Source Voltage | ADC Node |
|---:|---:|
| 15.0V adapter (V3-B/C) | 2.76V |
| 12.6V full 3S | 2.31V |
| 12.0V adapter (V3-A) | 2.20V |
| 10.5V low warning | 1.93V |
| 9.9V shutdown warning | 1.82V |
| 9.0V empty / danger | 1.65V |

Note: at 15V, ADC_NODE = 2.76V, which is within the ESP32-S3 ADC1 safe range (3.3V max). GPIO1 (ADC1_CH0) can be read safely with WiFi active on the S3.

---

## 7. Encoder Interface

The encoder electrical interface is inherited from V2.

### 7a. Single Signal Channel

Repeated 7 times: Theta A/B, Phi A/B, Wire A/B/Z.

```text
Encoder 5V TTL output -> 10k -> GPIO_NODE -> ESP32-S3 GPIO
GPIO_NODE             -> 20k -> GND
GPIO_NODE             -> 1nF -> GND
GPIO_NODE             -> 1.5KE3.3CA TVS -> GND
```

Divider output:

```text
5.0V * 20k / (10k + 20k) = 3.33V
```

Do not replace the 1nF capacitors with 100nF. The larger value destroys quadrature edge timing at normal operating speeds.

### 7b. Connector Pinout

| Connector | Pin | Signal | ESP32-S3 GPIO |
|---|---:|---|---:|
| J_THETA | 1 | +5V via FB1 | - |
| J_THETA | 2 | GND | - |
| J_THETA | 3 | A | 4 |
| J_THETA | 4 | B | 5 |
| J_PHI | 1 | +5V via FB2 | - |
| J_PHI | 2 | GND | - |
| J_PHI | 3 | A | 6 |
| J_PHI | 4 | B | 7 |
| J_WIRE | 1 | +5V via FB3 | - |
| J_WIRE | 2 | GND | - |
| J_WIRE | 3 | A | 15 |
| J_WIRE | 4 | B | 16 |
| J_WIRE | 5 | Z index | 17 |

Shield wires connect to board GND at the PCB end only.

---

## 8. ESP32-S3 Core Connections

```text
5V_RAIL -> DevKitC VIN / 5V pins
GND      -> DevKitC GND pins
GPIO1   -> ADC divider (BUCK_VIN monitor)
GPIO4   -> Theta A
GPIO5   -> Theta B
GPIO6   -> Phi A
GPIO7   -> Phi B
GPIO8   -> WiFi LED, optional
GPIO15  -> Wire A
GPIO16  -> Wire B
GPIO17  -> Wire Z, optional
EN      -> reset button to GND, optional
```

Leave GPIO 0, 3, 19, 20, 26–37, 45, and 46 unrouted.

---

## 9. Test Points

| Test Point | Net | Expected |
|---|---|---|
| TP_IN | Input before Q_RPP, optional | 12V or 15V nominal |
| TP12 | V_PROT | 11.5–12.5V (12V adapter) or 14.5–15.5V (15V adapter) |
| TP_BAT | Fused battery positive | 9.0–12.6V |
| TP_BV | BUCK_VIN | Adapter voltage or battery voltage |
| TP_ADC | ADC_NODE | 1.65–2.31V (battery) or up to 2.76V (15V adapter) |
| TP5 | 5V_RAIL | 4.9–5.1V target |
| TP33 | DevKitC 3V3 | 3.25–3.35V after DevKit inserted |
| TPG | GND | 0V |
