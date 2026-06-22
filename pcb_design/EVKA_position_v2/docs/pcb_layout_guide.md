# PCB Layout Guide — 5V PCB v2

LPKF S63, FR4, 120×80mm, 2-layer.

> ⚠ **2026-05-08 — Zone D enlarged for ESP32-S3-DevKitC-1.**
> The 120×80 board outline, 2-layer FR4 stackup, LPKF S63 design rules, and trace-width hierarchy in this file are unchanged. After the procurement audit, the MCU footprint changed from Wemos D1 R32 (UNO form) to ESP32-S3-DevKitC-1 (44-pin 2×22, 63.5×25.4 mm + dual USB-C protrusion); Zone A shrank correspondingly because USB-C, LTC4412, and Q_SWITCH were removed. See **`KICAD_PLAN_DETAILED.md` → Phase 3 Step 15** for the updated zone table. Routing priority and design rules below remain authoritative.

---

## Board Specifications

| Parameter | Value |
|---|---|
| Dimensions | 120mm × 80mm |
| Layers | 2 (Top: traces; Bottom: ground copper pour) |
| Substrate | FR4, 1.55mm, 18µm (0.5oz) copper |
| Manufacturing | LPKF S63 mechanical milling |
| Soldermask | None (milled board) — tin power traces after milling |
| Silkscreen | None — use paper component placement template |
| Corner fiducials | 3× copper dots, 0.5mm diameter, no drill, in board corners |
| Mounting holes | 4× M3 (3.2mm drill) at corners, 3mm inset from board edge |

---

## LPKF S63 Design Rules (FR4)

| Parameter | Minimum | Recommended |
|---|---|---|
| Trace width — signal | 0.5mm | **0.8mm** |
| Trace width — power (encoder VCC) | 0.8mm | **1.5mm** |
| Trace width — 5V_RAIL (after L1, system load only) | 1.5mm | **2.0mm** |
| Trace width — V_EXT_RAW, V_EXT_PROT (charge + system, ≤1.5A) | 2.0mm | **3.0mm** |
| Trace width — LiPo BAT+ to MT3608 input | 1.5mm | **2.0mm** |
| Isolation clearance (general) | 0.3mm | **0.4mm** |
| Ground pour clearance | 0.3mm | **0.4mm** |
| Via drill diameter | 0.8mm | **0.8mm** |
| Via pad diameter | 1.6mm | **2.0mm** |
| Component hole — standard (resistors, caps, ICs) | 0.8mm | **1.0mm** |
| Component hole — connectors, large leads | 1.0mm | **1.2mm** |
| Pad annular ring | 0.3mm | **0.5mm** |
| SOT-23 pad size (3-lead, AO3401) | 0.55×0.65mm (lib default) | **0.6×0.9mm** (LPKF-friendly) |
| SOT-23-6 pad size (LTC4412) | 0.55×0.65mm (lib default) | **0.6×0.8mm** (gap ≥0.3mm at 0.95mm pitch) |
| SOT-23 / SOT-23-6 pad-to-pad gap | 0.25mm | **0.3mm** (fresh isolation bit, 3 milling passes) |

**18µm copper current capacity** (derated from IPC-2221, 35µm base, ×0.6 factor, 10°C rise):

| Trace Width | Max Current |
|---|---|
| 0.8mm | ~0.54A |
| 1.0mm | ~0.65A |
| 1.5mm | ~0.90A |
| 2.0mm | ~1.30A |
| 3.0mm | ~1.80A |

**Trace width selection by net:**
- **V_EXT_RAW / V_EXT_PROT** (USB-C / barrel → Q_RPP → LTC4412 + TP4056): up to 1.5A when charging at 1A while running at 0.5A → **3.0mm**.
- **5V_RAIL** (after pi-filter L1): system-only load ~0.5A peak → **2.0mm**.
- **LiPo BAT+ → MT3608 IN**: ~0.7A peak boost-input current → **2.0mm**.
- **Encoder VCC feeds** (after ferrite beads): 100mA each → **1.5mm**.
- **Signal traces** (divider → 74HC14N → GPIO): logic-level → **0.8mm**.

---

## Zone Layout — 120×80mm

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ZONE A — POWER INPUT + LTC4412 + PI FILTER (top-left, ~55mm × 35mm)     │
│                                                                           │
│  J_USB ──[TVS_USB]──[D_USB]──┐                                          │
│  R_CC1, R_CC2 (Rd, 5.1kΩ × 2 within 5mm of J_USB)                       │
│                              ├──► V_EXT_RAW ──[Q_RPP]──► V_EXT_PROT     │
│  J4   ──[TVS_BAR]──[D_BAR]──┘                                           │
│                                                                           │
│  R_RPP (100kΩ to GND on Q_RPP gate)                                      │
│  LTC4412 (SOT-23-6) + Q_SWITCH (AO3401)                                  │
│  C_LTC (100nF, within 5mm of LTC4412 pin2), R_GATE (100kΩ)              │
│  Pi filter: C_PI (10µF) ─ L1 (10µH) ─ C1 (220µF) ─ C2 (100nF)           │
│  LED1 (green), R_LED1 (1kΩ)                                              │
│  TP1 (5V_RAIL), TP6 (GND)                                                │
│                                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│  ZONE B — BATTERY & CHARGING (top-right, ~65mm × 35mm)                   │
│                                                                           │
│  TP4056 module ── DW01A module ── J5 (JST-PH LiPo)                      │
│  MT3608 module ── [C_BOOST 22µF] ── [D_BOOST] ──► PI_NODE (joins L1)   │
│  R_MT_HI (300kΩ), R_MT_LO (100kΩ) soldered onto MT3608 FB pin           │
│  R_MON1 + R_MON2 (100kΩ × 2), C_ADC (100nF)                            │
│  TP3 (MT3608 out = 5.0V), TP4 (LiPo BAT+)                              │
│                                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│  ZONE C — SIGNAL CONDITIONING (bottom-left, ~60mm × 45mm)                │
│                                                                           │
│  J1 (Theta, KF301-4P) ── J2 (Phi, KF301-4P) ── J3 (Wire, KF301-4P)    │
│  FB1, FB2, FB3 (ferrite beads on VCC lines)                              │
│  C_VCC × 3 (100nF at each connector VCC pin)                             │
│  6× divider networks: R_TOP(10kΩ) + R_BOT(20kΩ) + C_FILT(10nF C0G)     │
│                       + TVS (general THT, part TBD)                      │
│                                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│  ZONE D — MCU + SCHMITT TRIGGER (bottom-right, ~60mm × 45mm)             │
│                                                                           │
│  74HC14N DIP-14 (place near ESP32 header, Zone D entry side)             │
│  ESP32 Wemos D1 R32 (2× female header, 1×15 + 1×19)                     │
│  R_GPIO12 (10kΩ pull-down on 74HC14N pin 8 output → GPIO12 line → GND)  │
│  C_ADC_GPIO36 (100nF on GPIO36), SW_RESET (tactile button)               │
│  LED2 (red), R_LED2 (1kΩ)                                               │
│  TP2 (3.3V)                                                              │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
     TP1───TP2───TP3───TP4───TP5───TP6   (test point row, bottom edge)

FIDUCIALS: 3× copper dots (0.5mm, no drill) at top-left, top-right, bottom-left corners
```

---

## Component Placement Notes

### Zone A — Power Input + LTC4412 + Pi Filter
- J4 (barrel) and J_USB (USB-C): left board edge, cable exits from left
- R_CC1, R_CC2 (5.1kΩ Rd): place within 5mm of J_USB CC1 / CC2 pins, both to GND
- TVS_USB and TVS_BAR (SMAJ5.0A, SMA): directly at the connector VBUS / VIN+ pins, cathode to the rail, anode to GND. They sit *before* D_USB / D_BAR so they shunt connector-side transients before the OR diodes.
- D_BAR and D_USB: adjacent to TVS, anodes toward connectors
- Q_RPP (SOT-23): between OR diodes and LTC4412; use fresh isolation bit
- R_RPP (100kΩ): from Q_RPP gate to GND, tucked beside the FET
- LTC4412 (SOT-23-6): close to Q_SWITCH (AO3401); **C_LTC bypass within 5mm of LTC4412 VIN pin (pin 2)**
- R_GATE (100kΩ): between Q_SWITCH gate and V_EXT_PROT, kept short
- Q_SWITCH (AO3401): drain toward the pi-filter input node; source toward V_EXT_PROT
- Pi filter: C_PI (10µF) on the Q_SWITCH-drain side, then L1 (10µH axial), then C1 (220µF) on the 5V_RAIL side. The boost path (D_BOOST cathode) joins at the same node as Q_SWITCH drain, ahead of L1, so both supply paths share the filter.
- C1 (220µF): at 5V_RAIL star point (after L1); all ground spokes originate here
- LED1: facing board edge for visibility; current-limit resistor between LED and 5V_RAIL

### Zone B — Battery & Charging
- TP4056 module: top-right corner; charge LED faces outward
- MT3608 module: adjacent to TP4056; FB-pin resistors (R_MT_HI, R_MT_LO) soldered directly to module FB pad
- J5 (JST-PH): near MT3608 for short battery wires; short wires = less voltage drop
- C_BOOST (22µF) on MT3608 output, then D_BOOST anode → cathode routes back to Zone A pi-filter input node
- ADC divider (R_MON1, R_MON2, C_ADC): route wire from LiPo BAT+ via R_MON1 to internal node, then R_MON2 to GND, C_ADC at that node; run a 0.8mm trace to GPIO36

### Zone C — Signal Conditioning
- Connectors (J1/J2/J3): bottom-left edge; encoder cables exit from left
- Ferrite beads (FB1/2/3): immediately after 5V_RAIL tap for each encoder VCC; C_VCC bypass at each connector VCC pin
- Divider networks: place each complete network (R_TOP, R_BOT, C_FILT, TVS — general THT, part TBD) in a vertical column between its encoder connector and the 74HC14N

### Zone D — MCU + Schmitt Trigger
- 74HC14N DIP-14: at the boundary of Zone C and Zone D; inputs face Zone C divider outputs, outputs face ESP32 header pins — minimizes signal trace length after buffering
- 74HC14N VCC (pin14) to ESP32 3.3V pin; 100nF bypass between pin14 and pin7, within 5mm of the IC
- R_GPIO12 (10kΩ): on the **trace from 74HC14N pin 8 (4Y) to GPIO12**, with the resistor's other leg to GND. This dominates the Schmitt's source current at boot before VCC stabilises and holds GPIO12 ≈ LOW. Do *not* place R_GPIO12 on the divider input side — the inverter sits between input and output, so a divider-side pull-down does not reach GPIO12.
- ESP32 socket: right board edge for USB-B port access
- SW_RESET: near ESP32; route to ESP32 EN pin

---

## Routing Priority and Strategy

Mill order: bottom copper pour first (flip step), then top traces.

| Priority | Net | Layer | Width |
|---|---|---|---|
| 1 | GND | Bottom (pour) | Fill, 0.4mm clearance |
| 2 | V_EXT_RAW (post-TVS, post-OR diodes) | Top | **3.0mm** |
| 3 | V_EXT_PROT (post-Q_RPP) | Top | **3.0mm** |
| 4 | 5V_RAIL (post-L1) | Top | 2.0mm |
| 5 | Battery traces (LiPo BAT+ → MT3608 IN; MT3608 OUT → D_BOOST → pi node) | Top | 2.0mm |
| 6 | Encoder VCC (after ferrites) | Top | 1.5mm |
| 7 | Signal traces (divider → 74HC14N → GPIO) | Top | 0.8mm |
| 8 | Battery ADC trace (GPIO36) | Top | 0.8mm |
| 9 | LED, reset, GPIO12 pull-down trace | Top | 0.8mm |

**Signal routing rules:**
- Keep signal traces (0.8mm) shorter than 50mm
- Do not run signal traces parallel to 5V_RAIL for more than 10mm
- All signals route on top layer; bottom is GND pour only
- Route divider→74HC14N traces on top, keep <15mm
- Route 74HC14N→GPIO traces on top, keep <20mm

**Ground pour:**
- Bottom layer: solid FR4 copper pour, KiCad fill zone connected to GND
- Set isolation clearance to **0.4mm** (LPKF S63 capability on FR4)
- After milling: blow out channels with compressed air; test isolation with multimeter before populating

---

## Via Strategy

Minimize vias — 2-layer LPKF boards use wire-link vias (not plated).

**Via procedure:**
1. Drill 0.8mm hole in correct position
2. Thread a 0.6mm tinned copper wire (cut component lead) through the hole
3. Solder both sides flush to the copper pad
4. Cut excess wire flush with board surface
5. Test continuity with multimeter before proceeding

**Expected via locations:**
- Near C1 (220µF): GND star connection from top GND pads to bottom pour
- Under ESP32 headers: GND pins from top to bottom pour
- Near LTC4412/Q_SWITCH: GND to bottom pour
- Encoder connector GND pins: top to bottom pour

Use 2–3 parallel wire-link vias for high-current GND connections (5V_RAIL star).

---

## SMD Component Soldering (LTC4412, AO3401)

Both LTC4412 (SOT-23-6) and AO3401 (SOT-23) have 0.95mm pad pitch. On LPKF S63 FR4:

1. Use fresh 0.2mm isolation cutter for these footprints
2. Set isolation clearance to 0.3mm (not 0.4mm) for SOT-23 pads specifically
3. **Run 3 isolation passes in CircuitPro for the SMD area** (default is 2). Extra pass widens the milled channel and removes copper-edge whiskers that can short adjacent SOT-23-6 pads at 0.35mm gap.
4. **Footprint pad expansion**: use 0.6×0.9mm pads for AO3401 (SOT-23) and 0.6×0.8mm for LTC4412 (SOT-23-6) — larger than the standard library default. Larger pads give the cutter more margin and improve hand-solder fillets on a milled board with no soldermask.
5. Apply solder paste with the S63 integrated dispenser, or manually with a toothpick
6. Solder with a fine-tip iron (1.5mm chisel or 0.8mm conical) and 0.5mm solder wire
7. Check for bridges under magnification (10× loupe or macro camera) before powering
8. Three AO3401 pins: source (top pin), gate (left pin), drain (right pin) — verify from datasheet

---

## Assembly Sequence

### Phase 1 — Power Section (Zones A + B)

**Phase 1a — SMD first (hand-solder with fine tip before any THT):**
1. Q_RPP (AO3401 SOT-23) — inspect for bridges under 10× loupe
2. LTC4412 (SOT-23-6) — inspect for bridges
3. Q_SWITCH (AO3401 SOT-23) — inspect for bridges
4. TVS_USB, TVS_BAR (SMAJ5.0A, DO-214AC SMA) — cathode band toward the rail

**Phase 1b — THT power components:**
5. D_BAR, D_USB (SS34 DO-201): test polarity with diode checker
6. R_RPP (100kΩ), R_GATE (100kΩ), C_LTC (100nF) — within 5mm of LTC4412
7. R_CC1, R_CC2 (5.1kΩ Rd, 1%) — within 5mm of J_USB
8. L1 (10µH axial), C_PI (10µF/10V), C1 (220µF/10V), C2 (100nF) — pi filter on 5V_RAIL
9. LED1 + R_LED1
10. TP4056 module (pin headers), MT3608 module (pin headers with fixed resistors already installed)
11. D_BOOST (SS34), C_BOOST (22µF)
12. R_MON1, R_MON2, C_ADC (battery monitor)
13. J5 (JST-PH LiPo connector)
14. J4 (barrel jack), J_USB (USB-C THT)
15. J6 (test screw terminal)

**Phase 1 Checkpoint:**
- Apply 5V at J4 → LED1 lights green
- TP1 = ~4.6V (±0.1V) [passive Schottky-OR via D_EXT, ~0.35V drop, post-pi-filter]
- TP6 = 0V (GND)
- (USB-C / R_CC1 / R_CC2 no longer apply — USB-C input dropped; programming/console is via the ESP32-S3-DevKitC-1 onboard USB-C)
- Do NOT connect LiPo yet

### Phase 2 — ESP32 Mount (Zone D)

14. Solder female pin headers (1×15, 1×19) to board
15. Press-fit ESP32 Wemos D1 R32 into headers
16. SW_RESET button
17. LED2 + R_LED2

**Phase 2 Checkpoint:**
- With 5V at J4: ESP32 boots, USB visible at 115200 baud
- TP2 = 3.3V ±0.1V
- `PING` → `ACK:PONG` via serial

### Phase 3 — Signal Conditioning (Zones C + D)

18. Ferrite beads FB1, FB2, FB3 (on encoder VCC lines)
19. C_VCC ×3 (100nF at each encoder VCC pin)
20. 6× divider networks: for each channel, solder R_TOP + R_BOT + C_FILT + TVS (general THT, part TBD — bidir, V_RWM ≥ ~3.34V)
21. 74HC14N DIP-14 (check orientation notch; VCC=pin14 to ESP32 3.3V, 100nF bypass between pin14↔pin7)
22. Wire 74HC14N outputs to correct ESP32 GPIO pins (see schematic Section 5 — explicit DIP pin table)
23. R_GPIO12 (10kΩ): leg 1 on the trace from 74HC14N pin 8 to GPIO12, leg 2 to GND
24. C_ADC (100nF on GPIO36 node → GND)

**Phase 3 Checkpoint:**
- Connect one encoder (e.g., Theta)
- Scope GPIO14 output → clean square wave with no jitter as encoder shaft rotates
- `STATUS` command → theta encoder counts change, phi and wire = 0

### Phase 4 — LiPo + Final Verification

25. Connect 2000mAh 1S LiPo via J5
26. With 5V external connected: TP4 = LiPo voltage rising (charging)
27. Remove external power: system runs from LiPo, TP1 = 4.65V
28. Re-apply external: TP1 returns to 4.98V
29. Test USB-C input path (J_USB): same behavior as barrel jack
30. Connect all three encoders → `STATUS` → all three axes reporting non-zero values

**Phase 4 Final Checkpoint:**
- Reverse polarity test on J4 (−5V at center): LED1 off, no current, ESP32 unpowered
- `pio run -e wemos_d1_r32` — build passes (firmware pin swap for 74HC14N must be active)
- All six test points within spec (TP1–TP6)

---

## Test Point Verification Table

| Test Point | Location | Expected Voltage | Condition |
|---|---|---|---|
| TP1 | 5V_RAIL | ~4.6V ±0.1V | External 5V connected (Schottky-OR drop) |
| TP1 | 5V_RAIL | ~4.65V ±0.1V | Battery only |
| TP2 | ESP32 3.3V | 3.3V ±0.1V | Any power source |
| TP3 | MT3608 output | 5.0V ±0.1V | Battery or external |
| TP4 | LiPo BAT+ | 3.0–4.2V | Depending on charge state |
| TP5 | BAT_OUT (TP4056 OUT+) | 3.0–4.2V | Tracks cell via TP4056 |
| TP6 | GND | 0V | Reference |

---

## LPKF S63 Workflow Notes (2-layer FR4)

1. **Prepare board:** Cut FR4 to 125×85mm (5mm larger each side for clamping)
2. **Load CircuitPro:** Import Gerber files; set tool to 0.2mm isolation cutter
3. **Mill bottom layer first:** Place board copper-side up, secure with vacuum. Mill bottom copper isolation and component pads
4. **Apply ProConduct (if using):** For via plating, apply conductive paste before flipping
5. **Add fiducial markers:** Drill 0.5mm fiducial holes at 3 corners of board outline (marked in Gerber)
6. **Flip board:** Rotate 180° along horizontal center axis. Camera aligns to fiducials → ±0.05mm
7. **Mill top layer:** Mill top copper isolation, component pads, board outline
8. **Drill all holes:** Component holes (1.0–1.2mm), via holes (0.8mm)
9. **Clean board:** Blow out milling dust with compressed air; brush debris from pads
10. **Tin power traces:** Flood solder 5V_RAIL, GND bus, battery traces to prevent oxidation
11. **Test isolation:** Multimeter check between adjacent pads before populating

**SOT-23 specific note:** Mill LTC4412 and AO3401 footprints last, with freshest isolation cutter. After milling, use 10× magnification to confirm complete copper isolation between all pads. Any residual copper bridge requires re-milling with a clean pass.
