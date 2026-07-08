# PCB Layout Guide — EVKA Position V3

> 120x80mm, 2-layer LPKF S63 milled PCB.  
> No soldermask, no silkscreen, no plated through-holes.  
> Use conservative trace widths, large pads, and accessible test points.

---

## 1. Board Specification

| Parameter | Value |
|---|---|
| Board size | 120mm x 80mm |
| Layers | 2 |
| Manufacturing | LPKF S63 mechanical milling |
| Copper | 1 oz typical |
| Soldermask | None |
| Silkscreen | None; use paper assembly template |
| Vias | Wire-through vias, soldered both sides |
| Minimum signal trace | 0.5mm |
| Minimum clearance | 0.3mm absolute minimum; use more around battery and 12V nodes |
| Preferred components | Through-hole discretes + plug-in modules |

---

## 2. Zone Map

```text
Top view, 120mm x 80mm

+----------------------------+---------------------------------------+
| ZONE A1: CHARGING ZONE     | ZONE A2: 12V INPUT / BATTERY          |
| (V3-B/V3-C only)           |                                       |
| ~40mm x 25mm               | J12V_TERM  NTC  F1  TVS               |
| CN3722 or XL4016 module    | Q_RPP IRF4905                         |
| R_CS, LED_CHRG, R_CHRG     | J_XT60  F_BAT  J_BAL  BMS_3S          |
| wires to CHARGE_OUT        | Q_BATT IRF4905 + D_GATE + R_G2 + Z1   |
|                            |                                       |
+----------------------------+---------------------------------------+
| ZONE B: BUCK + 5V FILTER             | ZONE C: ESP32-S3 DEVKITC    |
|                                      |                             |
| MP1584EN module                      | USB-C facing board edge     |
| C_IN, L_FILT, C_FILT, 5V star node   | 2x20 female headers         |
| TP_BV TP5 GND                        | Power/WiFi LEDs, reset      |
|                                      |                             |
+--------------------------------------+-----------------------------+
| ZONE D: ENCODERS / SIGNAL CONDITIONING                              |
|                                                                    |
| J_THETA       J_PHI       J_WIRE                                    |
| 7x divider/filter/TVS channels                                      |
| Ferrites near 5V feed entries                                       |
|                                                                    |
+--------------------------------------------------------------------+
```

Placement priorities:

1. Keep buck converter and Q_BATT / charging zone away from encoder signal dividers.
2. Put encoder connectors on one board edge for cable strain relief.
3. Put the DevKitC USB-C connector at a board edge.
4. Put all power test points along an accessible edge.
5. Keep battery connector and fuse mechanically protected from accidental shorts.

---

## 3. Trace Width Guide

| Net | Current | Minimum Width | Preferred Width |
|---|---:|---:|---:|
| Battery positive before/after fuse | fault-capable | 2.0mm | 3.0mm or short insulated wire |
| 12V input / V12_PROT | 1-2A peak | 1.5mm | 2.0mm |
| BUCK_VIN | 1A typical peak | 1.5mm | 2.0mm |
| 5V_RAIL main | 0.6A peak | 1.5mm | 2.0mm |
| Encoder 5V branch | <100mA each | 0.8mm | 1.0mm |
| Encoder signal | <1mA | 0.5mm | 0.5mm |
| ADC divider | <1mA | 0.5mm | 0.5mm |
| GND return | total return | 2.0mm | bottom GND pour / 3mm bus |

Use multiple wire vias in parallel for power or ground transitions.

---

## 4. LPKF S63 Rules

- Use large through-hole pads. A 0.8mm drill should have at least a 1.8-2.0mm pad when space allows.
- Avoid fine-pitch SMD parts. V3 should be buildable with a normal soldering iron.
- No soldermask means exposed copper can short against component leads, washers, battery wires, or module standoffs.
- Keep copper away from mounting holes unless that hole is intentionally grounded.
- Add copper text or polarity marks where possible, but rely on a printed 1:1 paper placement template.
- Use 0.8mm tinned copper wire for vias, soldered both sides.

---

## 5. Power Layout

### 5a. Input Protection

Route in a straight, short path:

```text
J12V -> NTC -> F1 -> TVS -> Q_RPP -> V_PROT -> BUCK_VIN (direct) / Q_BATT gate drive
```

Keep the TVS ground return short and direct to the main ground bus.

### 5b. Battery Path

- Place `F_BAT` as close to the battery positive lead as the enclosure allows.
- If the fuse holder is off-board, route only fused battery positive onto the PCB.
- Use insulated wire for battery currents if trace routing becomes awkward.
- Keep battery copper away from exposed grounded metal and mounting screws.

### 5c. Q_BATT and Charging Zone

**Q_BATT circuit** (4 parts — Zone A2):

- Place `Q_BATT` (IRF4905 TO-220) flat or upright near `J_XT60` and `BUCK_VIN` trace.
- `D_GATE` (SS14 SMD or 1N5819 axial), `R_G2` (100kΩ), and `Z1` (1N4742A DO-41) cluster near the gate pin.
- Do not ground the tab. The tab is BUCK_VIN — insulate if it could contact chassis metal.

**Charging zone** (Zone A1, ~40mm × 25mm, top-left):

- For V3-A: leave Zone A1 pads unpopulated. All traces are wired; no components placed.
- For V3-B (CN3722): module footprint ~35mm × 20mm. Mount flat with M2 standoffs or solder directly to pads if module has THT pins. R_CS (2.0Ω axial) and LED_CHRG + R_CHRG adjacent.
- For V3-C (XL4016): module footprint ~55mm × 22mm — larger than Zone A1. If needed, mount with standoffs above Zone A2 or use short wired connection from an off-board position.
- Route CHARGE_OUT with ≥2.0mm trace to F_BAT. Charge current is 0.5A — this is modest, but 2mm is good practice.
- Keep LED_CHRG visible from the top edge for status inspection without disassembly.

### 5d. Buck and Filter

- Place `C_IN1` and `C_IN2` close to buck VIN/GND.
- Place `L_FILT`, `C_FILT`, and `C_FILT_HF` close to buck VOUT/GND.
- Make the filtered `5V_RAIL` node the star point for ESP32 and encoder power.
- Keep the buck module switching side at least 30mm from the encoder divider row when possible.

---

## 6. Encoder Layout

For each signal channel:

```text
Connector signal -> 10k -> divider junction -> short trace -> ESP32 GPIO
                                 |
                                 +-> 20k -> GND
                                 +-> 1nF -> GND
                                 +-> TVS -> GND
```

Rules:

- Place divider/filter/TVS parts close to the encoder connector, before the long run to ESP32.
- Keep divider junction to ESP32 GPIO trace away from 12V, battery, and buck traces.
- Route A/B pairs together with similar length.
- Connect shield to GND at the PCB end only.
- Put ferrite beads on encoder 5V branches near the 5V star node or near each connector.

---

## 7. Ground Strategy

Preferred:

- Bottom layer mostly GND pour or wide GND bus.
- Top layer mostly components, power, and signals.
- Connect all decoupling capacitor grounds to bottom GND with short wire vias.
- Use a central ground reference near the 5V filter output.

LPKF warning:

Full exposed ground pours can cause accidental shorts. Use keepouts around pads, connectors, module standoffs, and battery wiring.

---

## 8. Assembly Sequence

1. Drill and mill PCB.
2. Install and solder wire vias.
3. Solder low-profile passives: resistors, 1nF caps, 100nF caps.
4. Solder TVS diodes and small diodes, verifying polarity.
5. Solder electrolytic capacitors, verifying polarity.
6. Solder ferrites, test points, reset button, LEDs.
7. Solder screw terminals and XT60/power connectors.
8. Solder DevKitC female headers, but do not insert DevKitC yet.
9. Install Q_BATT (IRF4905 TO-220), D_GATE, R_G2, and Z1. For V3-B/C, also populate the charging zone module and LED_CHRG.
10. Mount/wire the buck module after pre-setting it under load.
11. Run the power-only validation checklist.
12. Insert ESP32-S3 DevKitC only after `5V_RAIL` is verified.

---

## 9. Common Mistakes

| Mistake | Result | Prevention |
|---|---|---|
| IRF4905 tab touches grounded enclosure | Short on V12_PROT | Keep tab floating or insulate mechanically |
| Unfused LiPo positive routed across PCB | Fire risk during short | Fuse close to battery positive |
| Q_BATT tab bolted to chassis metal | Shorts BUCK_VIN to chassis GND | Keep tab floating or insulate with washer |
| Buck output not preset | ESP32 damage | Measure buck output before inserting DevKitC |
| 100nF used instead of 1nF on encoder lines | Lost encoder counts | Use 1nF C0G/NP0 or X7R only |
| Full GND pour too close to pads | Shorts during assembly | Use keepouts and inspect with magnification |
| USB-C inaccessible | Hard to flash/debug | Put DevKitC USB-C at board edge |
