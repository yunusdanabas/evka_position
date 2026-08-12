# PCB Layout Guide — EVKA Position V2 (LPKF S63)

> Layout rules and assembly sequence for double-sided milled PCB.  
> **No soldermask, no silkscreen, no plated holes.**  
> All components through-hole. Modules mount on pin headers.

---

## 1. PCB Specification

| Parameter | Value |
|-----------|-------|
| Dimensions | **120mm × 80mm** |
| Layers | **2** (top copper + bottom copper) |
| Material | FR4 or pertinax (pertinax easier to mill) |
| Copper thickness | 35µm (1 oz) standard |
| Minimum trace width | **0.5mm** (signal), **1.0mm** (power) |
| Minimum clearance | **0.3mm** (no soldermask = higher risk of shorts) |
| Vias | 0.8mm drill, wire-through-hole, solder both sides |
| Mounting holes | 4× M3, 3.2mm drill |
| Edge clearance | ≥2mm from board edge to copper |

---

## 2. LPKF S63 Specific Notes

### 2a. Milling Considerations

```
    LPKF S63 capabilities:
    • Mechanical routing (not laser)
    • Tool diameters: 0.8mm, 1.0mm, 2.0mm typical
    • No plated through-holes (PTH)
    • No soldermask layer
    • No silkscreen layer
    • Contour routing for board outline
```

**Implications for design:**
- **Larger pads:** Use 2.0mm diameter pads for 0.8mm drills (vs 1.5mm for PTH)
- **Wider traces:** 0.5mm minimum (vs 0.25mm for professional PCB)
- **Via stitching:** Wire-through-hole vias must be manually soldered on both sides
- **No soldermask:** Exposed copper everywhere — avoid large copper pours near fine-pitch areas
- **No silkscreen:** Use paper placement template or component polarity markings in copper

### 2b. Via Construction

```
    Standard via (0.8mm drill):
    
    Top side:    Solder blob
                      │
                 ┌────┴────┐
                 │  1.0mm  │   ← Pad on top
                 │  pad    │
                 └────┬────┘
                      │ 0.8mm hole
                 ┌────┴────┐
                 │  1.0mm  │   ← Pad on bottom
                 │  pad    │
                 └────┬────┘
                      │
    Bottom side:   Solder blob
    
    Process: Drill 0.8mm hole → insert 0.6mm copper wire →
             solder top → solder bottom → trim excess
```

**Via current capacity:** ~1A for signal vias, use multiple vias in parallel for power (5V_RAIL, GND).

---

## 3. Board Zone Map

```
    Top view of 120mm × 80mm PCB:
    
    ┌────────────────────────────────────────────────────────────────────────────┐
    │                                                                            │
    │  ┌────────────────────────────────────────────────────────────────────┐   │
    │  │ ZONE A: POWER INPUT (top-left, 30×40mm)                            │   │
    │  │                                                                    │   │
    │  │  J12V ── NTC ── F1 ── TVS ── Q1(IRF4905) ── V12_PROT             │   │
    │  │                                                                    │   │
    │  │  [MP1584EN module]  Q_BATT(IRF4905)  J_XT60(edge)                │   │
    │  │                                                                    │   │
    │  │  Q_RPP  F_BAT-holder  L_FILT  C_FILT  SS36                        │   │
    │  │                                                                    │   │
    │  └────────────────────────────────────────────────────────────────────┘   │
    │  ┌────────────────────────────────────────────────────────────────────┐   │
    │  │ ZONE B: MCU & EXPANSION (right side, 40×80mm)                     │   │
    │  │                                                                    │   │
    │  │  [ESP32-S3-DevKitC-1 on female headers]                           │   │
    │  │                                                                    │   │
    │  │  [MAX485]  [MAX813L]  LEDs(4×)  Reset button                      │   │
    │  │                                                                    │   │
    │  │  J_RS485  J_I2C  J_GPIO                                          │   │
    │  │                                                                    │   │
    │  └────────────────────────────────────────────────────────────────────┘   │
    │  ┌────────────────────────────────────────────────────────────────────┐   │
    │  │ ZONE C: ENCODERS (bottom, 120×30mm)                               │   │
    │  │                                                                    │   │
    │  │  J1(Theta)    J2(Phi)    J3(Wire)                                │   │
    │  │  ┌────────┐  ┌────────┐  ┌──────────┐                            │   │
    │  │  │+ G A B │  │+ G A B │  │+ G A B Z │                            │   │
    │  │  └────────┘  └────────┘  └──────────┘                            │   │
    │  │                                                                    │   │
    │  │  7× divider networks (10k/20k/1nF/TVS)                           │   │
    │  │                                                                    │   │
    │  └────────────────────────────────────────────────────────────────────┘   │
    │                                                                            │
    │  ● MH1                          ● MH2                                    │
    │                                                                            │
    │                                                                            │
    │  ● MH3                          ● MH4                                    │
    │                                                                            │
    └────────────────────────────────────────────────────────────────────────────┘
    
    Mounting hole positions (center-to-center):
    • MH1: (5mm, 5mm) from top-left
    • MH2: (115mm, 5mm) from top-left
    • MH3: (5mm, 75mm) from top-left
    • MH4: (115mm, 75mm) from top-left
    
    DIN rail clip mounting: 105mm × 65mm centers (between MH1-MH2 and MH3-MH4)
```

---

## 4. Zone Layout Details

### 4a. Zone A — Power Input (30×40mm, top-left)

**Components (left to right):**
```
    J12V (barrel jack, panel mount or PCB edge)
    │
    NTC 5D-9 (disc, 5mm pitch)
    │
    F1 PTC (radial, 5mm pitch)
    │
    P6KE18A (DO-15 axial, 7.5mm body)
    │
    IRF4905 (TO-220, mounted vertically, tab facing right)
    │
    R_G 100kΩ (axial, near Q1 gate pin)
    │
    V12_PROT bus ──┬── 120kΩ/27kΩ divider ── GPIO 1
                   │
                   ├── BUCK_VIN (adapter path, direct)
                   │
                   └── D_GATE (SS14 Schottky) ── Q_BATT Gate (+ 100kΩ pull-down to GND)
    
    Battery path (PCB edge):
    J_XT60 ── F_BAT inline holder ── Q_BATT Source → Drain → BUCK_VIN
```

**MP1584EN module placement:**
- Mount on 4-pin 2.54mm male headers (module plugs in)
- Position near center of Zone A
- Input caps (C_IN1, C_IN2) close to module VIN pins
- Output inductor and caps close to module VOUT pins

**Q_BATT gate circuit placement:**
- IRF4905 TO-220: mount adjacent to Q_RPP, heatsink tab toward board edge
- R_G2 (100kΩ pull-down) and Z1 (1N4742A Zener) close to gate pin
- D_GATE (SS14 Schottky) on gate trace between V12_PROT and Q_BATT gate
- F_BAT inline holder immediately adjacent to J_XT60+ terminal — no unfused battery copper on board

**Trace widths in Zone A:**
- V12_PROT: 1.5mm minimum (adapter branch, continuous 2A load)
- BUCK_VIN: 1.5mm minimum
- 5V_RAIL: 1.0mm minimum
- GND: 1.5mm minimum or ground pour

### 4b. Zone B — MCU & Expansion (40×80mm, right side)

**DevKitC-1 header placement:**
```
    Position: top-right corner, USB-C facing top edge
    
    Two rows of 20-pin female headers:
    • Row spacing: 25.4mm (1 inch) — standard DevKitC-1 spacing
    • Pin pitch: 2.54mm
    • Height: 8mm (standard)
    
    Leave 10mm clearance above headers for DevKitC-1 module
    Leave 5mm clearance on sides for routing
```

**Component placement around DevKitC-1:**
```
    Above DevKitC-1: (keep clear for USB-C access)
    
    Left of DevKitC-1 (facing center of board):
    • MAX485 (DIP-8, socket or direct solder)
    • MAX813L (DIP-8, socket or direct solder)
    • 120Ω termination resistor + jumper
    
    Below DevKitC-1:
    • 4 LEDs in a row (Green, Blue, Yellow, Red)
    • 4× 1kΩ resistors behind LEDs
    • Reset button (6×6mm tactile)
    
    Right edge of board:
    • J_RS485 (KF301-3P, vertical)
    • J_I2C (1×4 pin header, horizontal)
    • J_GPIO (1×6 pin header, horizontal)
    • J_SD (1×5 pin header, horizontal — DNP by default, route GPIO 33–36 traces)
    • J_ETH (2×5 pin header — DNP by default, route W5500 SPI traces)
    • J_CAN (1×4 pin header, near J_RS485 — DNP by default, CAN transceiver footprint)
```

### 4c. Zone C — Encoders (120×30mm, bottom)

**Connector placement:**
```
    J1 (Theta):   bottom-left,  KF301-4P, pins facing down
    J2 (Phi):     bottom-center, KF301-4P, pins facing down
    J3 (Wire):    bottom-right,  KF301-5P, pins facing down
    
    Keep connectors 10mm from board edge for strain relief
```

**Divider network placement:**
```
    Each encoder channel needs: 10kΩ + 20kΩ + 1nF + TVS
    
    Layout per channel (15×20mm area):
    
    Encoder signal from connector ── 10kΩ ──┬── 20kΩ ── GND
                                            │
                                            ├── 1nF ── GND
                                            │
                                            ├── 1.5KE3.3CA ── GND
                                            │
                                            └──→ to DevKitC-1 header
    
    Place all 7 channels in a row between connectors and DevKitC-1 headers.
    Keep traces from divider junction to GPIO <30mm.
```

**Ferrite beads:**
```
    5V_RAIL ── FB1 ── J1 Pin 1
    5V_RAIL ── FB2 ── J2 Pin 1
    5V_RAIL ── FB3 ── J3 Pin 1
    
    Place ferrites near the 5V_RAIL distribution point.
    Keep bead-to-connector trace <20mm.
```

---

## 5. Routing Guidelines

### 5a. Power Routing

```
    V12_PROT:    1.5mm trace, top layer preferred
    BUCK_VIN:    1.5mm trace, top layer
    5V_RAIL:     1.0mm trace, star topology from buck output
    3.3V:        0.5mm trace, from DevKitC-1 3V3 pins
    GND:         1.5mm trace OR ground pour on both layers
```

**Star topology for 5V_RAIL:**
```
         MP1584EN output
              │
              ├─── FB1 ── J1 VCC
              ├─── FB2 ── J2 VCC
              ├─── FB3 ── J3 VCC
              ├─── ESP32 VIN
              ├─── LED1 (power)
              ├─── MAX485 VCC
              └─── MAX813L VCC
```

Avoid daisy-chaining 5V through multiple loads — star topology minimizes voltage drop and noise coupling.

### 5b. Signal Routing

```
    Encoder signals (GPIO 4/5/6/7/15/16/17):
    • 0.5mm trace width
    • Keep away from 5V_RAIL and buck switching node
    • Run GND return parallel to signal (minimize loop area)
    • Keep A/B pairs equal length (<5mm difference)
    
    I2C signals (GPIO 11/12):
    • 0.5mm trace width
    • Keep SDA and SCL parallel, <50mm length
    • Avoid crossing buck switching traces
    
    RS-485 signals (A/B):
    • 0.5mm trace width
    • Twist A and B traces together on PCB (if possible)
    • Keep away from switching noise
    • Termination resistor directly at MAX485 pins
```

### 5c. Ground Strategy

```
    Recommended: Single ground plane on bottom layer
    
    Bottom layer: Mostly GND pour with traces as needed
    Top layer:    Signals and power distribution
    
    Connect top GND to bottom GND with:
    • Vias at every ground pad
    • Via grid (10mm spacing) under switching areas
    • Dedicated via for each decoupling cap ground
```

**Without soldermask, a full ground pour can cause shorts if a component lead touches it.** Consider using **GND traces** instead of full pour in dense areas, or keep pour well clear of pads.

---

## 6. Assembly Sequence

### Step 1: Bottom Layer Components

```
    Solder all bottom-layer components first:
    • Jumpers or wires that must be on bottom
    • Via wires (insert and solder)
    • Any bottom-mount connectors
```

### Step 2: Top Layer — Small Passives

```
    Solder in order of height (shortest first):
    1. Resistors (all 1/4W axial) — bend leads, insert, solder, trim
    2. Ceramic disc capacitors (1nF, 100nF)
    3. TVS diodes (watch polarity band!)
    4. Small signal diodes (if any)
```

### Step 3: Top Layer — Medium Components

```
    5. DIP-8 ICs (MAX485, MAX813L) — use sockets if available
    6. Electrolytic capacitors (watch polarity!)
    7. Ferrite beads (axial)
    8. Reset button
```

### Step 4: Top Layer — Large Components

```
    9. TO-220 transistor (IRF4905) — mount vertically, tab away from GND
    10. Screw terminals (KF301 series) — ensure pins fully inserted
    11. Pin headers (J_I2C, J_GPIO)
    12. Female headers for DevKitC-1 (H1, H2)
```

### Step 5: Modules

```
    13. Solder male pin headers to module boards (if not pre-installed)
    14. Insert MP1584EN module into carrier headers
    15. Install Q_BATT (IRF4905 TO-220) and solder F_BAT inline fuse holder adjacent to J_XT60+
    16. Insert 3S BMS module into carrier headers (or wire directly)
```

### Step 6: Power-On Test (CRITICAL)

```
    BEFORE inserting DevKitC-1:
    
    1. Connect 12V lab supply (current limited to 1A)
    2. Measure V12_PROT at TP12: should be ~12V
    3. Measure BUCK_VIN at TP_BV: should be ~11.6V
    4. Measure 5V_RAIL at TP5: should be 4.75–4.85V
    5. Measure 3.3V on H1/H2 pin 1: should be 0V (no DevKitC-1 yet)
    6. Verify no smoke, no excessive heat
    7. If 5V_RAIL is wrong, adjust MP1584EN trim pot
    8. If anything is >6V, DISCONNECT and check wiring
```

### Step 7: Insert DevKitC-1

```
    9. Align DevKitC-1 with female headers
    10. USB-C connector should face top edge of board
    11. Press gently but firmly until fully seated
    12. Verify no bent pins
```

### Step 8: Final Test

```
    13. Reconnect 12V supply
    14. Measure 3.3V on DevKitC-1 3V3 pin: 3.25–3.35V
    15. Connect USB-C cable to PC
    16. Check for `/dev/ttyACM0` (Linux) or COM port (Windows)
    17. Upload test firmware
    18. Verify LEDs, encoder counts, RS-485, I2C scan
```

---

## 7. Component Placement Template

Since there is no silkscreen, create a paper template for assembly:

```
    Print 1:1 scale drawing of component positions on paper.
    Tape paper to workbench.
    Place components on paper to verify orientation before soldering.
    
    Mark polarity on paper:
    • Diode cathode bands (draw thick line)
    • Electrolytic negative stripe
    • LED flat side / short lead
    • IC notch direction
    • Transistor pin 1 (Gate for IRF4905)
```

---

## 8. Common Layout Mistakes to Avoid

| Mistake | Why It Happens | How to Avoid |
|---------|---------------|--------------|
| IRF4905 tab touches GND | Mounting screw to grounded area | Use insulating washer, or leave floating |
| Reversed Schottky diode | Confusing cathode band direction | Draw arrow on paper template pointing to output |
| Electrolytic cap reversed | No silkscreen polarity marking | Bend positive lead longer, paper template |
| 5V too low for ESP32 | SS36 drop + long trace | Star topology, 1.0mm traces, measure at VIN pin |
| Encoder counts erratic | Buck noise coupling | LC filter close to module, ferrites near connectors |
| I2C not working | Missing pull-ups | Include 4.7kΩ on PCB, not just on module |
| RS-485 no response | Missing termination | 120Ω resistor with jumper at MAX485 pins |
| MAX813L always resetting | WDI not toggled | Verify firmware drives GPIO 9 every <1.6s |

---

## 9. Drilling Schedule

| Hole Type | Drill Diameter | Quantity | Notes |
|-----------|---------------|----------|-------|
| Standard component lead | 0.8mm | ~100 | Resistors, caps, diodes |
| Transistor/IC pin | 0.8mm | 16 | MAX485, MAX813L, IRF4905 |
| Power diode lead | 1.0mm | 12 | SS34/SS36 DO-201 |
| TVS diode lead | 1.0mm | 10 | P6KE18A, 1.5KE3.3CA |
| Electrolytic cap lead | 0.8–1.0mm | 6 | Radial electrolytic |
| Module header pin | 1.0mm | 8 | MP1584EN, BMS headers |
| DevKitC-1 header pin | 1.0mm | 40 | 2× 20-pin female headers |
| Screw terminal pin | 1.2mm | 22 | KF301 series |
| Tactile button pin | 0.8mm | 4 | 6×6mm button |
| Via | 0.8mm | 20–30 | Wire-through-hole |
| Mounting hole | 3.2mm | 4 | M3 screw |

**Total holes:** ~250–280

---

## 10. File Outputs for LPKF Software

| File | Format | Content |
|------|--------|---------|
| `evka_v2_top.gbr` | Gerber | Top copper layer |
| `evka_v2_bottom.gbr` | Gerber | Bottom copper layer |
| `evka_v2_outline.gbr` | Gerber | Board outline (120×80mm) |
| `evka_v2_drill.drl` | Excellon | All drill holes |
| `evka_v2_top.pdf` | PDF | 1:1 print for paper template |

**LPKF import:** Use CircuitPro or BoardMaster software. Import Gerber + drill files. Set tool paths for 0.8mm and 1.0mm end mills.

---

## 11. Related Documents

- [Main V2 README](../README.md) — System overview
- [Circuit Schematic](circuit_schematic_v2.md) — Complete netlist
- [Bill of Materials](bill_of_materials_v2.md) — Parts list
- [Pin Assignment](pin_assignment_v2.md) — GPIO map
- [Power Supply Subsystem](subsystems/power_supply_v2.md) — Power section details
- [MCU Subsystem](subsystems/mcu_subsystem_v2.md) — DevKitC-1 mounting
- [Encoder Interface](subsystems/encoder_interface_v2.md) — Signal conditioning layout
- [Expansion Interfaces](subsystems/expansion_interfaces_v2.md) — RS-485, I2C placement
