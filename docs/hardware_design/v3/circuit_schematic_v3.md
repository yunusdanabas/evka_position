# Circuit Schematic — EVKA Position V3

> Simple 12V ESP32-S3 carrier with internal 3S LiPo backup through a ready-made power-path module.  
> No onboard LiPo charger. No RS-485, I2C expansion, external watchdog, or non-core interfaces by default.

---

## 1. Full System Block Diagram

```text
  J12V 12V INPUT
      |
      +-- NTC1 5D-9, optional but recommended for inrush limiting
      |
      +-- F1 adapter fuse / PTC
      |
      +-- TVS_IN P6KE18A or P6KE20A to GND
      |
      +-- Q_RPP IRF4905 high-side reverse-polarity MOSFET
      |
    V12_PROT -----------------------------------------------+
      |                                                      |
      +--> J_PWRPATH ADAPTER+                                |
                                                             |
  INTERNAL 3S LiPo RC PACK                                  |
      |                                                      |
      +-- XT60 main positive                                 |
      |                                                      |
      +-- F_BAT blade fuse close to battery positive         |
      |                                                      |
      +--> J_PWRPATH BATTERY+                                |
      |                                                      |
      +-- JST-XH-4P balance lead, charger access only        |
                                                             |
  READY-MADE POWER-PATH MODULE                               |
      |                                                      |
      |  Inputs: V12_PROT, fused 3S battery, GND              |
      |  Output: BUCK_VIN                                    |
      |  Must block reverse current between sources           |
      |  Must not perform unsafe unbalanced charging          |
      |                                                      |
    BUCK_VIN                                                 |
      |                                                      |
      +-- R_ADC_TOP 120k --+-- R_ADC_BOT 27k -- GND          |
      |                    |                                 |
      |                    +--> ESP32-S3 GPIO1 ADC           |
      |                                                      |
      +-- C_IN1 220uF/35V + C_IN2 100nF                      |
      |                                                      |
      +-- U_BUCK MP1584EN module, 12V-ish to 5.05-5.10V      |
      |                                                      |
      +-- L_FILT 22uH --+-- C_FILT 220uF/10V -- GND          |
      |                 |                                    |
      |                 +-- C_FILT_HF 100nF -- GND           |
      |                 |                                    |
      |              5V_RAIL                                 |
      |                 |                                    |
      |                 +--> ESP32-S3 DevKitC VIN             |
      |                 +--> Power LED                        |
      |                 +--> FB1 -> Theta encoder VCC         |
      |                 +--> FB2 -> Phi encoder VCC           |
      |                 +--> FB3 -> Wire encoder VCC          |
      |                                                      |
  ENCODER SIGNALS                                           |
      |                                                      |
      +-- 7x 10k/20k divider + 1nF filter + 3.3V TVS         |
      |                                                      |
      +--> ESP32-S3 GPIO 4,5,6,7,15,16,17                    |
```

---

## 2. 12V Input Protection

### 2a. Input Connector

Use one or both of these footprints:

- `J12V_BARREL`: 5.5x2.1mm center-positive DC jack
- `J12V_TERM`: KF301-2P screw terminal for machine cabinet wiring

If both are fitted, join them at the input node before protection. Use only one source at a time unless the upstream system is designed for paralleling.

### 2b. Fuse / PTC

```text
J12V+ -> NTC1 -> F1 -> TVS/RPP input
```

Recommended default:

- `NTC1`: 5D-9 NTC, optional but useful if the power-path module has large input capacitance
- `F1`: 1.1A hold PTC or 2A glass fuse

The adapter-side fuse protects the adapter wiring. The battery path has its own mandatory fuse.

### 2c. TVS Clamp

```text
F1 output ----+---- TVS_IN ---- GND
              |
              +---- Q_RPP source
```

Default:

- `P6KE18A` for regulated 12V adapters that stay below about 15V in normal operation
- `P6KE20A` if the adapter or cabinet rail can sit near 15-16V during normal operation

### 2d. Reverse-Polarity MOSFET

```text
IRF4905, facing marked side, leads down:

Pin 1: Gate
Pin 2: Drain
Pin 3: Source
Tab:   Drain

F1 / TVS node  -> Source
Gate           -> 100k -> GND
Drain / tab    -> V12_PROT
```

Correct polarity: gate is pulled low, `Vgs` is negative, MOSFET turns on.  
Reverse polarity: MOSFET remains off and blocks current.

Do not bolt the tab to grounded metal. The tab is `V12_PROT`.

---

## 3. 3S Battery Path

V3 assumes an internal 3S LiPo RC pack with:

- XT60 main connector
- JST-XH-4P balance connector
- External 3S balance charger
- Optional but strongly recommended 3S protection/BMS module or protected pack

```text
3S LiPo main + -> F_BAT blade fuse -> J_PWRPATH BAT+
3S LiPo main - ---------------------> GND
JST-XH balance lead ----------------> charger access only
```

Fuse placement rule:

- Put `F_BAT` close to the battery positive lead or XT60 positive pin.
- Do not route unfused battery positive across the PCB.
- Use 5A for small 1500-2200mAh packs unless the selected module requires a different value.

---

## 4. Ready-Made Power-Path Module Interface

V3 does not lock the PCB to one unverified module footprint. Instead, it provides a terminal/header interface and mounting area.

```text
J_PWRPATH_IN:
Pin 1: ADAPTER+  = V12_PROT
Pin 2: BATTERY+  = fused 3S battery positive
Pin 3: GND

J_PWRPATH_OUT:
Pin 1: BUCK_VIN
Pin 2: GND
```

The module may be mounted with standoffs and wired with short insulated wires, or plugged into a custom footprint after its dimensions are confirmed.

Required module behavior is defined in [`power_path_module_interface_v3.md`](power_path_module_interface_v3.md).

---

## 5. Buck Converter and 5V Rail

### 5a. Buck Module

Default module:

- `MP1584EN` adjustable buck module
- Input: `BUCK_VIN`, about 9.0-13.0V depending on adapter or battery
- Output preset: 5.05-5.10V under load

```text
BUCK_VIN -> C_IN1 220uF/35V -> U_BUCK VIN
GND -------------------------> U_BUCK GND
U_BUCK VOUT -> L_FILT 22uH -> 5V_RAIL
5V_RAIL -> C_FILT 220uF/10V + 100nF -> GND
```

Pre-set the buck before inserting the ESP32-S3 board.

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

Default monitor point: `BUCK_VIN`, so firmware can observe adapter or battery source voltage after source selection.

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
| 12.6V full 3S | 2.31V |
| 12.0V adapter | 2.20V |
| 10.5V low warning | 1.93V |
| 9.9V shutdown warning | 1.82V |
| 9.0V empty / danger | 1.65V |

Optional: if adapter-only monitoring is preferred, connect the divider to `V12_PROT` instead of `BUCK_VIN`. For backup behavior, `BUCK_VIN` is more useful.

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

Do not replace the 1nF capacitors with 100nF. The larger value will destroy quadrature edges at normal operating speeds.

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

Shield wires should connect to board GND at the PCB end only.

---

## 8. ESP32-S3 Core Connections

```text
5V_RAIL -> DevKitC VIN / 5V pins
GND      -> DevKitC GND pins
GPIO1   -> ADC divider
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

Leave GPIO 0, 3, 19, 20, 26-37, 45, and 46 unrouted.

---

## 9. Test Points

| Test Point | Net | Expected |
|---|---|---|
| TP_IN | Protected input before Q_RPP, optional | 12V nominal |
| TP12 | V12_PROT | 11.5-12.5V adapter typical |
| TP_BAT | Fused battery positive | 9.0-12.6V |
| TP_BV | BUCK_VIN | selected source voltage |
| TP_ADC | ADC_NODE | 1.65-2.31V typical |
| TP5 | 5V_RAIL | 4.9-5.1V target |
| TP33 | DevKitC 3V3 | 3.25-3.35V after DevKit inserted |
| TPG | GND | 0V |
