# PCB Layout Guide — evka_position Hardware Board

> 120mm x 80mm double-sided pertinax board.
> Hand-soldered, through-hole components, wire-link vias.

---

## 1. Board Layout — Zone Map

```
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                          120mm                                               │
    │◄────────────────────────────────────────────────────────────────────────────►│
    │                                                                              │
    │  ZONE A: POWER (ext)              │  ZONE B: BATTERY                     │▲ │
    │  ┌───────────────────────┐        │  ┌────────────────────────────┐      ││ │
    │  │ J4 (DC jack / 2P)     │        │  │ TP4056 module (MOD1)      │      ││ │
    │  │ J6 (KF128V test 5V)   │        │  │ J5 (JST-PH LiPo)        │      ││ │
    │  │ Q1 (SI2301 RPP)       │        │  │ MT3608 module (MOD2)     │      ││ │
    │  │ D1 (SS34)             │        │  │ D2 (SS34)                │      ││ │
    │  │ C1 (220μF bulk)       │        │  │ C13 (10μF MT3608 input) │      ││ │
    │  │ C2 (100nF rail)       │        │  │ D3 (1N5817 auto-charge) │      ││ │
    │  │ LED1 (green, power)   │        │  │ R15-R16 (ADC divider)   │      │80mm
    │  │ TP1, TP5              │        │  │ TP3, TP4                │      ││ │
    │  └───────────┬───────────┘        │  └──────────┬─────────────┘      ││ │
    │              └────── 5V_RAIL ─────┴─────────────┘                     ││ │
    │                         │                                              ││ │
    │  ZONE C: SIGNAL COND.   │                ZONE D: MCU                  ││ │
    │  ┌───────────────────┐  │                ┌────────────────────────┐   ││ │
    │  │ J1 (Theta 4P)     │  │                │                        │   ││ │
    │  │  FB1, C3           │  │                │   ┌──────────────┐    │   ││ │
    │  │  R1,R8,C6 (div1)  │  │                │   │  ESP32       │    │   ││ │
    │  │  R2,R9,C7 (div2)  │──┼── signals ────│   │  Wemos D1 R32│    │   ││ │
    │  │  TVS1, TVS2        │  │                │   │              │    │   ││ │
    │  │                    │  │                │   │  (on female  │    │   ││ │
    │  │ J2 (Phi 4P)       │  │                │   │   headers)   │    │   ││ │
    │  │  FB2, C4           │  │                │   │              │    │   ││ │
    │  │  R3,R10,C8 (div3) │──┼── signals ────│   │              │    │   ││ │
    │  │  R4,R11,C9 (div4) │  │                │   └──────┬───────┘    │   ││ │
    │  │  TVS3, TVS4        │  │                │          │[USB]      │   ││ │
    │  │                    │  │                │          │            │   │▼ │
    │  │ J3 (Wire 5P)      │  │                │   Reset btn, LED2    │   │  │
    │  │  FB3, C5           │  │                │   TP2               │   │  │
    │  │  R5,R12,C10 (div5)│──┼── signals ────│                        │   │  │
    │  │  R6,R13,C11 (div6)│  │                └────────────────────────┘   │  │
    │  │  R7,R14,C12 (div7)│──┘                                            │  │
    │  │  TVS5, TVS6, TVS7 │          USB edge ──────────────────────────►│  │
    │  └───────────────────┘                                               │  │
    │                                                                       │  │
    │  ZONE E: TEST POINTS & MISC (along bottom edge)                      │  │
    │  [TP1] [TP2] [TP3] [TP4] [TP5]                                      │  │
    └──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer Assignment

| Layer | Usage |
|-------|-------|
| **Top** | Components, signal traces, power traces (5V_RAIL, VCC feeds) |
| **Bottom** | Wide ground bus (3mm+), ground fill areas, via pads |

### Wire-Link Vias
- Use 0.8mm tinned copper wire pushed through drilled holes
- Solder both sides to create reliable top-bottom connections
- Place a via at every ground connection point

---

## 3. Trace Width Guide

| Trace Type | Current | Minimum Width | Copper Weight |
|------------|---------|--------------|--------------|
| 5V_RAIL main bus | 400mA | 2.0mm | 1oz (35μm) |
| 5V to each encoder (via ferrite) | 100mA | 1.0mm | 1oz |
| GND bus (bottom layer) | 400mA | 3.0mm+ | 1oz |
| Signal traces (divider → GPIO) | <1mA | 0.5mm | 1oz |
| Battery traces (TP4056 → MT3608) | 650mA | 2.0mm | 1oz |
| LED traces | 5mA | 0.3mm | 1oz |

---

## 4. Ground Strategy — Star Topology

```
                          5V_RAIL GND (main star point)
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴──────┐
              │  Zone A    │  │  Zone C    │  │  Zone D     │
              │  Power GND │  │  Encoder   │  │  ESP32 GND  │
              │  (caps,    │  │  GND (J1,  │  │  (VIN GND,  │
              │   diodes)  │  │  J2, J3,   │  │   divider   │
              │            │  │  ferrites) │  │   GND)      │
              └────────────┘  └────────────┘  └─────────────┘
                    │               │               │
              ┌─────┴─────┐                         │
              │  Zone B    │                         │
              │  Battery   │                         │
              │  GND       │                         │
              └────────────┘                         │
                                                     │
              Bottom copper: wide (3mm+) traces      │
              connecting all ground points back to    │
              the central star point near C1 (bulk cap)
```

**Rules:**
1. All ground returns meet at one central star point near C1 (220μF)
2. Bottom layer carries ground traces — keep them wide (3mm minimum)
3. No ground loops — each zone gets its own spoke back to star
4. Encoder shield wires connect to GND at board entry only (J1-J3)

---

## 5. Component Placement Guidelines

### Zone A — Power (top-left, ~40mm x 30mm)
- J4 and J6 at board edge for easy cable access
- Q1 (SI2301) close to J4/J6 for short high-current path
- D1 immediately after Q1
- C1 (220μF) + C2 (100nF) at the 5V_RAIL junction node
- LED1 + R17 near board edge (visible)
- TP1 and TP5 accessible

### Zone B — Battery (top-right, ~40mm x 30mm)
- TP4056 module mounted flat, USB edge accessible from top or right
- J5 (JST-PH) near TP4056 BAT± pads
- MT3608 module near TP4056 OUT± pads (short wires)
- D2 at MT3608 output
- D3 (1N5817) linking external 5V → TP4056 IN+ for auto-charge
- C13 (10μF) at MT3608 VIN
- R15-R16 (ADC divider) near TP4056 BAT+ pad

### Zone C — Signal Conditioning (bottom-left, ~40mm x 40mm)
- J1, J2, J3 at left board edge (encoder cables come from left)
- Each connector has its divider components immediately adjacent
- Layout per connector: connector → ferrite → 100nF → [R-top, R-bot, C-filter, TVS] per signal
- Keep signal traces short between dividers and Zone D
- Group TVS diodes near their respective divider junctions

### Zone D — MCU (bottom-right, ~40mm x 40mm)
- Female header strips oriented with USB port facing right board edge
- ESP32 USB must be accessible for programming cable
- VIN and GND wires come from Zone A (5V_RAIL)
- Signal traces enter from left side (Zone C)
- Reset button and LED2 near ESP32 but accessible
- TP2 near ESP32 3.3V pin

### Zone E — Test Points (along bottom edge)
- TP1: 5V_RAIL
- TP2: 3.3V rail (ESP32 output)
- TP3: MT3608 output (pre-D2)
- TP4: LiPo BAT+
- TP5: GND reference

---

## 6. Routing Priority

Route in this order (highest priority first):

1. **GND bus** (bottom layer) — widest traces, star topology
2. **5V_RAIL** (top layer) — 2mm trace from D1/D2 junction to all loads
3. **Power feeds** — VIN to ESP32, 5V through ferrites to encoder connectors
4. **Signal traces** — divider outputs to ESP32 GPIOs (keep short, no parallel runs)
5. **Battery monitoring** — ADC divider to GPIO 36
6. **LED and reset** — lowest priority, route last

---

## 7. Assembly Sequence

### Phase 1: Power Section
1. Solder C1 (220μF) and C2 (100nF) at the 5V_RAIL junction area
2. Solder D1 (SS34) and Q1 (SI2301 + R19)
3. Mount TP4056 module, solder connections
4. Mount MT3608 module, solder connections
5. Solder D2 (SS34) at MT3608 output
6. Solder D3 (1N5817) for auto-charge path
7. Solder C13 (10μF) at MT3608 input
8. Solder J4 (DC jack) and J6 (KF128V test pin)
9. Solder J5 (JST-PH battery connector)
10. Solder LED1 + R17 (power indicator)

### Test Checkpoint 1
- Apply 5V to J4 → measure 5V_RAIL: expect ~4.8V
- Connect LiPo to J5 → measure 5V_RAIL: expect ~5.1V
- Verify LED1 lights up on both power sources

### Phase 2: ESP32 Mount
1. Solder two female header strips (U1) on top layer
2. Insert ESP32 Wemos D1 R32 into socket
3. Wire VIN to 5V_RAIL, GND to ground bus
4. Solder reset button between RST and GND

### Test Checkpoint 2
- Power on → ESP32 boots
- Connect USB → serial output visible at 115200 baud
- Verify 3.3V at TP2

### Phase 3: Signal Conditioning
1. Solder J1, J2, J3 screw terminals at left edge
2. For each connector, solder ferrite bead + 100nF decoupling cap
3. Solder all 7 voltage divider networks (R-top, R-bot, C-filter)
4. Route signal traces from divider junctions to ESP32 GPIOs
5. Create wire-link vias for any traces that need to cross

### Test Checkpoint 3
- Connect one encoder at a time
- Run `pio device monitor` (115200 baud)
- Rotate/pull encoder → verify counts change on serial output
- Repeat for all 3 encoders

### Phase 4: Protection and Finishing
1. Solder 7x TVS diodes (1.5KE3.3CA) at divider junctions
2. Solder R15-R16 (battery ADC divider) and wire to GPIO 36
3. Solder LED2 + R18 (battery low indicator)
4. Solder all test point pins (TP1-TP5)
5. Add any remaining wire-link vias
6. Label board: connector IDs, polarity markings, "5V TEST" on J6

### Test Checkpoint 4 — Full Integration
- `pio run -e wemos_d1_r32 --target upload`
- Connect all 3 encoders simultaneously
- Verify all 3 axes report correct position data
- Test ZERO command via serial
- Verify battery ADC reading (if firmware updated)

---

## 8. Pertinax-Specific Tips

- **Drilling**: Use 0.8mm drill for component leads, 1.0mm for connectors and test points
- **Trace isolation**: Scratch/cut copper between adjacent traces using a craft knife or trace cutter
- **Solder bridges**: Common issue on pertinax — inspect under magnification after each zone
- **Wire-link vias**: Drill 0.8mm hole, insert tinned wire, solder both sides flush
- **Module mounting**: TP4056 and MT3608 modules sit on top — solder their header pins through the board
- **Heat management**: SI2301 (SOT-23) can be dead-bug soldered with short wire leads to through-hole pads
