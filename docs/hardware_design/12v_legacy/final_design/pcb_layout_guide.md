# PCB Layout Guide - Final EVKA Position Hardware

This guide lays out the final 12V external-charge-only board for LPKF S63 or similar 2-layer milling.

## 1. Board Specification

| Parameter | Value |
|---|---|
| Board size | 120mm x 80mm |
| Layers | 2 |
| Manufacturing | LPKF S63 mechanical milling |
| Copper | 1 oz typical |
| Soldermask | None |
| Silkscreen | None; use paper placement template |
| Vias | Wire-through vias, soldered both sides |
| Minimum signal trace | 0.5mm |
| Preferred clearance | 0.5mm or more; 0.3mm absolute minimum only where unavoidable |
| Preferred parts | Through-hole discretes plus plug-in modules |

## 2. Final Zone Map

```text
Top view, 120mm x 80mm

+-------------------------------------+----------------------------------+
| ZONE A: ADAPTER INPUT / PROTECTION  | ZONE B: BATTERY / SOURCE SWITCH  |
|                                     |                                  |
| J12V_TERM  F1  TVS_IN               | J_XT60  F_BAT  J_BAL             |
| Q_RPP IRF4905                       | BMS_3S                            |
| V_PROT test point                   | Q_BATT IRF4905                    |
| D_ADAPT to BUCK_VIN                 | D_GATE + R_GATE_BAT               |
|                                     | TP_BAT TP_GATE                    |
+-------------------------------------+----------------------------------+
| ZONE C: BUCK + 5V FILTER            | ZONE D: ESP32-S3 DEVKITC         |
|                                     |                                  |
| C_BV  MP1584EN  L_FILT              | 2x20 female headers               |
| C_FILT  C_5V_BULK                   | USB-C at board edge               |
| TP_BV TP5 GND                       | LED_PWR LED_WIFI SW_RST TP33      |
+-------------------------------------+----------------------------------+
| ZONE E: ENCODERS / SIGNAL CONDITIONING                                  |
|                                                                          |
| J_THETA        J_PHI        J_WIRE                                        |
| 7x 10k/20k/1nF/TVS channels                                               |
| Ferrites on encoder 5V feeds                                               |
+--------------------------------------------------------------------------+
```

## 3. Placement Priorities

1. Put `J12V_TERM` and `J_XT60` on board edges for strain relief.
2. Put `F_BAT` as close to the battery positive lead as physically possible.
3. Keep unfused battery copper off the PCB if possible; use a short inline fuse holder before board entry.
4. Keep `D_ADAPT`, `D_GATE`, and Q_BATT gate routing short and easy to probe.
5. Put `MP1584EN`, `L_FILT`, and output capacitors away from encoder divider traces.
6. Put encoder connectors on one edge so the cables leave in one direction.
7. Put the ESP32-S3 USB-C connector on a board edge.
8. Put test points along accessible edges.

## 4. Trace Width Guide

| Net | Current | Minimum Width | Preferred Width |
|---|---:|---:|---:|
| Battery positive before fuse | fault-capable | Avoid PCB trace | Inline fused wire |
| Fused battery positive | 1A typical, high fault possible | 2.0mm | 3.0mm or insulated wire |
| Adapter input / V_PROT | 1A typical peak | 1.5mm | 2.0mm |
| D_ADAPT to BUCK_VIN | 1A typical peak | 1.5mm | 2.0mm |
| BUCK_VIN | 1A typical peak | 1.5mm | 2.0mm |
| 5V_RAIL main | 0.6A peak | 1.5mm | 2.0mm |
| Encoder 5V branch | <100mA each | 0.8mm | 1.0mm |
| Encoder signal | <1mA | 0.5mm | 0.5mm |
| ADC divider | <1mA | 0.5mm | 0.5mm |
| GND return | total return | 2.0mm | bottom GND bus / pour |

Use multiple wire vias in parallel for power and ground layer changes.

## 5. Power Layout Details

### 5a. Adapter Input

Route in a short line:

```text
J12V_TERM -> F1 -> TVS_IN/Q_RPP -> V_PROT -> D_ADAPT -> BUCK_VIN
```

Rules:

- Place TVS ground close to the main ground return.
- Keep Q_RPP source/drain traces wide.
- Keep Q_RPP tab away from grounded mounting hardware.
- Mark `D_ADAPT` cathode direction on the paper template.

### 5b. Battery Path

Recommended physical route:

```text
Battery lead -> inline F_BAT -> J_XT60 / board entry -> BMS_3S -> Q_BATT -> BUCK_VIN
```

Rules:

- The first protection after the battery positive lead is the fuse.
- Route fused battery positive with short, wide copper or insulated wire.
- Do not pass battery positive under the ESP32 module.
- Keep Q_BATT tab insulated from chassis or grounded hardware.

### 5c. Q_BATT Gate Circuit

Cluster these parts near Q_BATT pin 1:

- `D_GATE`
- `R_GATE_BAT`
- `TP_GATE`

Keep `V_PROT` sense separate from `BUCK_VIN`; `D_ADAPT` is the isolation boundary.

## 6. Buck And 5V Filter Layout

Place components in this order:

```text
BUCK_VIN -> C_BV -> MP1584EN VIN
MP1584EN VOUT -> L_FILT -> 5V_RAIL star node
5V_RAIL star node -> C_FILT + C_FILT_HF + C_5V_BULK
```

Rules:

- Keep the buck switching area at least 30mm from encoder divider nodes if possible.
- Keep `C_BV` close to the buck input pins.
- Keep `L_FILT` and `C_FILT` close to the buck output.
- Make the filtered side of `L_FILT` the 5V star node.
- Route ESP32 VIN and encoder ferrites from the 5V star node separately.

## 7. Encoder Layout

Each signal channel should follow this physical order:

```text
Connector signal pin -> R_TOP 10k -> divider node -> ESP32 GPIO trace
                                  -> R_BOT 20k to GND
                                  -> C_SIG 1nF to GND
                                  -> TVS_SIG to GND
```

Rules:

- Keep divider parts near the connector or at the start of the signal route.
- Keep A/B pairs close together and similar length.
- Do not route encoder signals parallel to 12V, `BUCK_VIN`, or buck switching traces.
- Cross power traces at 90 degrees if a crossing is unavoidable.
- Put GND return close to the divider network.
- Connect cable shields to board GND at the board end only.

## 8. Ground Strategy

Preferred strategy:

- Bottom layer mostly GND bus or GND pour.
- Top layer mostly components, power, and signal routing.
- Short GND returns for TVS, buck capacitors, and encoder filters.
- Multiple wire-through vias around buck and ESP32 ground pins.
- Keep exposed GND copper away from battery terminals and mounting hardware.

LPKF warning: no soldermask means exposed copper can short against component leads, washers, module hardware, or loose battery wires. Use keepouts generously.

## 9. Test Point Placement

Put these test points on accessible board edges:

| Test Point | Placement |
|---|---|
| TP_IN | Near adapter connector |
| TP_PROT | After Q_RPP |
| TP_BAT | Near battery/BMS output |
| TP_GATE | Near Q_BATT gate |
| TP_BV | Near buck input |
| TP_ADC | Near ADC divider |
| TP5 | At filtered 5V star node |
| TP33 | Near ESP32-S3 3V3 pin |
| TPG | At power, MCU, and encoder sections |

## 10. Assembly Order

1. Mill and drill the PCB.
2. Inspect for copper burrs and shorts.
3. Install and solder all wire vias.
4. Solder low-profile resistors.
5. Solder small capacitors and TVS diodes.
6. Solder Schottky diodes, verifying cathode bands.
7. Solder electrolytic capacitors, verifying polarity.
8. Solder ferrites and test points.
9. Solder screw terminals and XT60/panel connectors.
10. Solder Q_RPP and Q_BATT, verifying pin orientation.
11. Solder buck module headers, but pre-set the module before powering the board.
12. Solder ESP32-S3 female headers, but do not insert the DevKitC yet.
13. Run power-only validation.
14. Insert ESP32-S3 only after `5V_RAIL` is verified.
15. Connect and test encoders one at a time.

## 11. Common Layout Mistakes

| Mistake | Result | Prevention |
|---|---|---|
| Omitting `D_ADAPT` | Battery backfeeds adapter-sense rail and Q_BATT may turn off | Always place adapter isolation diode |
| Reversing `D_ADAPT` | Adapter cannot power buck | Cathode band faces `BUCK_VIN` |
| Reversing `D_GATE` | Q_BATT gate is not driven correctly | Cathode band faces Q_BATT gate |
| Q_BATT tab touches chassis | `BUCK_VIN` short | Insulate tab or keep it floating |
| Q_RPP tab touches chassis | `V_PROT` short | Insulate tab or keep it floating |
| Unfused battery trace crosses board | Fire risk on short | Fuse before board entry or route very short |
| Buck placed near divider row | Encoder miscounts | Separate power and signal zones |
| USB-C blocked | Hard to flash/debug | Put DevKitC USB-C on board edge |
| 100nF used for encoder signal filters | Missed quadrature edges | Use 1nF only |
