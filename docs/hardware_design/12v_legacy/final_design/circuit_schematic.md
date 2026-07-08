# Circuit Schematic - Final EVKA Position Hardware

This is the complete final hardware schematic narrative. It is the selected V3-A design extended into a single 12V-only build.

Final configuration:

- 12V adapter input
- ESP32-S3-DevKitC-1
- 3S LiPo backup
- External balance charging only
- No onboard charger
- Active battery takeover with adapter priority
- Proven 5V encoder signal conditioning

## 1. Full System Block Diagram

```text
ADAPTER INPUT
  J12V_TERM +12V
      |
      +-- F1 adapter fuse/PTC
      |
      +-- TVS_IN P6KE18A to GND
      |
      +-- Q_RPP IRF4905 reverse-polarity P-FET
      |
    V_PROT  (adapter-present protected rail)
      |
      +-- D_ADAPT SS36 or 1N5822, anode=V_PROT, cathode=BUCK_VIN
      |
      +-- D_GATE 1N5819/SS14, anode=V_PROT, cathode=Q_BATT_GATE

BATTERY BACKUP
  3S LiPo main +
      |
      +-- F_BAT 5A blade fuse, physically close to battery positive
      |
      +-- BMS_3S protection board output
      |
      +-- Q_BATT IRF4905 battery switch
             Source = protected battery positive
             Drain  = BUCK_VIN
             Gate   = Q_BATT_GATE

  Q_BATT_GATE
      |
      +-- R_GATE_BAT 100k to GND
      |
      +-- D_GATE from V_PROT raises gate when adapter is present

BUCK AND 5V RAIL
  BUCK_VIN
      |
      +-- C_BV 470uF/35V bulk to GND
      |
      +-- R_ADC_TOP 120k -> ADC_NODE -> R_ADC_BOT 27k -> GND
      |                         |
      |                         +-- ESP32-S3 GPIO1 ADC1_CH0
      |
      +-- MP1584EN buck module, preset 5.05V under load
      |
      +-- L_FILT 22uH -> 5V_RAIL
                         |
                         +-- C_FILT 220uF/10V to GND
                         +-- C_FILT_HF 100nF to GND
                         +-- ESP32-S3 VIN
                         +-- LED_PWR + 1k to GND
                         +-- FB1 -> Theta encoder +5V
                         +-- FB2 -> Phi encoder +5V
                         +-- FB3 -> Wire encoder +5V

ENCODER SIGNALS
  Theta A/B, Phi A/B, Wire A/B/Z
      |
      +-- 10k/20k divider, 1nF filter, 3.3V TVS
      |
      +-- ESP32-S3 GPIO 4,5,6,7,15,16,17
```

## 2. Power Source Behavior

| Condition | V_PROT | Q_BATT gate | Q_BATT | BUCK_VIN source |
|---|---:|---:|---|---|
| Adapter only | About 12V | About 11.7V | OFF | Adapter through `D_ADAPT` |
| Battery only | 0V | 0V | ON | Battery through `Q_BATT` |
| Adapter + battery | About 12V | About 11.7V | OFF | Adapter through `D_ADAPT` |
| Adapter removed | Falls to 0V | Pulled to 0V | ON | Battery takeover |
| Adapter restored | Rises to 12V | Rises to 11.7V | OFF | Adapter priority restored |

`D_ADAPT` is required. It prevents battery-powered `BUCK_VIN` from backfeeding `V_PROT` when the adapter is absent. This keeps `V_PROT` as a true adapter-sense rail.

## 3. Adapter Input Section

### 3a. Connector

```text
J12V_TERM, KF301-2P, 5.08mm

Pin 1: +12V adapter input
Pin 2: GND
```

Use a screw terminal for cabinet wiring. A barrel jack can be added for bench testing, but do not populate multiple adapter connectors unless their polarity and current rating are clearly labeled.

### 3b. Adapter Fuse / PTC

```text
J12V_TERM +12V -> F1 -> TVS/RPP input
```

Default options:

- `MF-R110` resettable PTC, 1.1A hold, for prototype/service convenience
- 2A glass fuse if a non-resettable fuse is preferred

This fuse protects adapter wiring. It does not replace the battery fuse.

### 3c. TVS Clamp

```text
F1 output -> TVS_IN cathode
TVS_IN anode -> GND
```

Default part: `P6KE18A`, axial DO-15.

Purpose:

- Clamp adapter transients
- Protect the buck and ESP32 from input spikes
- Provide a fast fault path for severe overvoltage events

Use `P6KE20A` only if the normal 12V rail can sit above 15V during expected operation.

### 3d. Reverse Polarity Protection, Q_RPP

```text
Q_RPP = IRF4905, TO-220AB P-channel MOSFET

Facing marked side, leads down:
Pin 1: Gate
Pin 2: Drain
Pin 3: Source
Tab:   Drain

F1/TVS node -> Source
Gate        -> R_GATE_RPP 100k -> GND
Drain/tab   -> V_PROT
```

Correct adapter polarity turns Q_RPP on because the gate is lower than the source. Reverse polarity keeps the MOSFET off.

Do not bolt the IRF4905 tab to a grounded heatsink. The tab is connected to `V_PROT`.

## 4. Adapter Isolation, D_ADAPT

```text
V_PROT -> D_ADAPT anode
D_ADAPT cathode -> BUCK_VIN
```

Default part: `SS36`, `SS34`, or `1N5822`, rated at least 3A and at least 40V.

Purpose:

- Adapter present: feeds `BUCK_VIN`.
- Adapter absent: blocks battery voltage from raising `V_PROT`.
- Keeps `D_GATE` from falsely turning Q_BATT off during battery operation.

Expected drop is about 0.3V to 0.5V at the EVKA load current. This is acceptable because the MP1584EN buck regulates the 5V output from `BUCK_VIN`.

## 5. Battery Path

### 5a. Battery Pack

Use a 3S LiPo RC pack with:

- XT60 main connector
- JST-XH-4P balance connector
- 1500-2200mAh typical capacity
- No visible swelling or damage

Voltage reference:

| State | Pack Voltage | Cell Voltage |
|---|---:|---:|
| Full | 12.60V | 4.20V |
| Nominal | 11.10V | 3.70V |
| Low warning | 10.50V | 3.50V |
| Shutdown target | 9.90V | 3.30V |
| Absolute minimum | 9.00V | 3.00V |

Do not intentionally run to BMS cutoff.

### 5b. Battery Fuse

```text
Battery positive -> F_BAT 5A blade fuse -> BMS/protected battery positive
```

Rules:

- `F_BAT` must be within 15cm of the battery positive lead.
- Do not route unfused battery positive across the PCB.
- Use insulated wire for the battery positive path if the PCB route would be long or exposed.
- A 3S LiPo can source dangerous fault current; the fuse is mandatory.

### 5c. BMS / Protection Board

The final design requires a 3S protection board or a protected battery pack.

Minimum BMS functions:

- Overdischarge cutoff
- Short-circuit protection
- Overcurrent protection

The BMS is not treated as the charger and is not treated as the balancing solution. Balancing is done by the external charger through the battery balance lead.

## 6. Q_BATT Battery Switch

```text
Q_BATT = IRF4905, TO-220AB P-channel MOSFET

Pin 1 Gate  -> Q_BATT_GATE
Pin 2 Drain -> BUCK_VIN
Pin 3 Source -> protected battery positive from BMS/fuse
Tab -> BUCK_VIN

Q_BATT_GATE -> R_GATE_BAT 100k -> GND
V_PROT -> D_GATE anode
D_GATE cathode -> Q_BATT_GATE
```

Default `D_GATE`: `1N5819` axial or `SS14`/`SS34` Schottky.

Operation:

- Adapter present: `V_PROT` raises the gate through `D_GATE`. `Vgs` is near zero or slightly negative, so Q_BATT is off and the battery is isolated.
- Adapter absent: `R_GATE_BAT` pulls the gate to GND. `Vgs` is about `-V_BAT`, so Q_BATT turns on and powers `BUCK_VIN`.

The final 12V design omits a gate zener. The maximum `Vgs` magnitude is about -12.6V, inside the IRF4905 +/-20V rating.

### 6a. Q_BATT OFF-state Margin

The IRF4905 datasheet specifies `Vgs(th)` between -2V and -4V. The FET is OFF when `Vgs` is less negative than the threshold.

Worst-case OFF-state evaluation at adapter-present:

| Condition | V_PROT | Gate (V_PROT - Vf_D_GATE) | Source (battery) | Vgs | Margin to worst-case Vgs(th) = -2V |
|---|---:|---:|---:|---:|---:|
| Adapter + full battery (12.6V) | 12.0V | 11.7V | 12.6V | -0.9V | 1.1V |
| Adapter + nominal battery (11.1V) | 12.0V | 11.7V | 11.1V | +0.6V | firmly off |
| Adapter + low battery (10.5V) | 12.0V | 11.7V | 10.5V | +1.2V | firmly off |

The tightest case is adapter-present with a fully charged battery: `Vgs = -0.9V`, giving a 1.1V margin to the worst-case `Vgs(th)` and ~2.1V to the typical `Vgs(th)` of -3V. The FET is OFF for any production part within datasheet, but subthreshold leakage at this margin is non-zero — expect <100uA at 25C, doubling roughly every 10C above that. For a 1500-2200mAh 3S pack this is negligible quiescent drain (<2.4mAh/day worst case at room temperature).

If a future revision uses a higher-voltage adapter (15V or 24V), revisit the gate clamp: a single-direction zener creates an unwanted forward path during adapter-present operation, so use a bidirectional clamp or a higher-Vz unidirectional zener (e.g., 1N4744A 15V) sized to keep the OFF-state gate at or above the maximum source voltage.

## 7. Buck Converter And 5V Rail

### 7a. Buck Input

```text
BUCK_VIN -> C_BV 470uF/35V -> GND
BUCK_VIN -> MP1584EN VIN
GND -> MP1584EN GND
```

`C_BV` gives hold-up during adapter loss and battery takeover.

Recommended starting value: 470uF/35V low-ESR electrolytic. Increase to 680uF or 1000uF if switchover resets the ESP32 during validation.

### 7b. Buck Output

```text
MP1584EN VOUT -> L_FILT 22uH -> 5V_RAIL
5V_RAIL -> C_FILT 220uF/10V -> GND
5V_RAIL -> C_FILT_HF 100nF -> GND
```

Set the MP1584EN to 5.05V under a dummy load before connecting it to the rest of the circuit.

Final `5V_RAIL` target at the load: 4.9V to 5.1V.

Stop testing immediately if `5V_RAIL` exceeds 5.2V before ESP32 installation.

### 7c. 5V Distribution

```text
5V_RAIL -> ESP32-S3 DevKitC VIN/5V pin
5V_RAIL -> LED_PWR -> R_LED_PWR 1k -> GND
5V_RAIL -> FB1 -> J_THETA pin 1
5V_RAIL -> FB2 -> J_PHI pin 1
5V_RAIL -> FB3 -> J_WIRE pin 1
```

Use star routing from the filtered 5V node. Do not daisy-chain encoder power through the ESP32 header.

## 8. Supply ADC Divider

```text
BUCK_VIN -> R_ADC_TOP 120k -> ADC_NODE -> R_ADC_BOT 27k -> GND
ADC_NODE -> ESP32-S3 GPIO1
```

Scale factor:

```text
V_input = V_adc * (120k + 27k) / 27k
        = V_adc * 5.444
```

Expected values:

| BUCK_VIN | ADC_NODE |
|---:|---:|
| 12.6V | 2.31V |
| 12.0V | 2.20V |
| 10.5V | 1.93V |
| 9.9V | 1.82V |
| 9.0V | 1.65V |

GPIO 1 is ADC1_CH0 on ESP32-S3 and remains usable with WiFi active.

## 9. Encoder Interface

All encoders are powered from `5V_RAIL`. Do not power any encoder from 12V.

Single signal channel, repeated seven times:

```text
Encoder output -> R_TOP 10k -> GPIO_NODE -> ESP32-S3 GPIO
GPIO_NODE -> R_BOT 20k -> GND
GPIO_NODE -> C_SIG 1nF -> GND
GPIO_NODE -> TVS_SIG 1.5KE3.3CA -> GND
```

Divider math:

```text
5.0V * 20k / (10k + 20k) = 3.33V
```

Do not use 100nF for `C_SIG`; it will destroy quadrature edge timing.

### 9a. Encoder Connectors

| Connector | Pin | Function | GPIO |
|---|---:|---|---:|
| J_THETA | 1 | +5V via FB1 | - |
| J_THETA | 2 | GND | - |
| J_THETA | 3 | Theta A | 4 |
| J_THETA | 4 | Theta B | 5 |
| J_PHI | 1 | +5V via FB2 | - |
| J_PHI | 2 | GND | - |
| J_PHI | 3 | Phi A | 6 |
| J_PHI | 4 | Phi B | 7 |
| J_WIRE | 1 | +5V via FB3 | - |
| J_WIRE | 2 | GND | - |
| J_WIRE | 3 | Wire A | 15 |
| J_WIRE | 4 | Wire B | 16 |
| J_WIRE | 5 | Wire Z | 17 |

Connect cable shields to board GND at the board end only.

## 10. ESP32-S3 Connections

```text
5V_RAIL -> DevKitC VIN/5V
GND -> DevKitC GND
GPIO1 -> ADC_NODE
GPIO4 -> Theta A
GPIO5 -> Theta B
GPIO6 -> Phi A
GPIO7 -> Phi B
GPIO8 -> LED_WIFI, optional
GPIO15 -> Wire A
GPIO16 -> Wire B
GPIO17 -> Wire Z
EN -> reset button to GND, optional
```

Leave these pins unrouted in the final core board:

- GPIO 0
- GPIO 3
- GPIO 11/12 unless a future daughterboard needs I2C
- GPIO 13/14/18 unless a future daughterboard needs RS-485
- GPIO 19/20, native USB
- GPIO 26-37, flash/PSRAM risk area
- GPIO 45/46, strapping/internal use

## 11. Test Points

| Test Point | Net | Expected |
|---|---|---|
| TP_IN | Adapter input after connector | About 12V |
| TP_PROT | V_PROT | About 12V when adapter present, 0V when adapter absent |
| TP_BV | BUCK_VIN | Adapter through diode or battery through Q_BATT |
| TP_BAT | Protected battery positive | 9.0V to 12.6V |
| TP_GATE | Q_BATT_GATE | About 11.7V adapter present, 0V adapter absent |
| TP_ADC | ADC_NODE | 1.65V to 2.31V typical |
| TP5 | 5V_RAIL | 4.9V to 5.1V |
| TP33 | ESP32 3.3V | 3.25V to 3.35V after DevKit inserted |
| TPG | GND | 0V |

## 12. Net Summary

| Net | Source | Destinations | Voltage |
|---|---|---|---|
| J12V+ | Adapter | F1 | 12V nominal |
| V_PROT | Q_RPP drain | D_ADAPT anode, D_GATE anode, TP_PROT | 12V only when adapter present |
| BAT_PROT | Battery fuse/BMS | Q_BATT source, TP_BAT | 9.0V to 12.6V |
| Q_BATT_GATE | D_GATE / R_GATE_BAT | Q_BATT gate, TP_GATE | 0V or about 11.7V |
| BUCK_VIN | D_ADAPT cathode or Q_BATT drain | Buck VIN, ADC divider, C_BV | About 11.7V from adapter; 9.0V to 12.6V from battery |
| ADC_NODE | 120k/27k divider | GPIO1, TP_ADC | 1.65V to 2.31V typical |
| 5V_RAIL | Buck/filter output | ESP32 VIN, encoders, LEDs | 4.9V to 5.1V |
| 3V3 | ESP32-S3 DevKitC regulator | Internal MCU logic only | 3.25V to 3.35V |
| GND | Common return | All sections | 0V |

## 13. Critical Assembly Warnings

1. Verify MP1584EN output before inserting the ESP32-S3.
2. Verify `D_ADAPT` cathode band faces `BUCK_VIN`.
3. Verify `D_GATE` cathode band faces `Q_BATT_GATE`.
4. Verify Q_RPP and Q_BATT IRF4905 pin orientation separately; their drains go to different nets.
5. Do not connect IRF4905 tabs to grounded metal.
6. Do not omit `F_BAT`.
7. Do not charge the battery through `J12V_TERM`.
8. Do not install any charger module on the final board.
9. Do not connect encoder VCC to 12V.
10. Do not substitute 100nF for encoder signal 1nF filters.
