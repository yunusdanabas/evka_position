# PCB Layout Guide — 12V + 3S LiPo evka_position (All-THT)

> All through-hole variant of [pcb_layout_guide_12v.md](../12v/pcb_layout_guide_12v.md).  
> **Signal zones** (encoder connectors, ESP32, dividers) follow the same discipline as the legacy boards.  
> This file covers the **adjusted power zone layout** for TO-220 and DO-201 packages, **mounting notes**, and **simplified assembly sequence** (no SMD steps).

---

## Board specification

| Parameter | Value |
|-----------|-------|
| Dimensions | **120mm × 80mm** (same as SMD version) |
| Material | Double-sided **pertinax** |
| Copper weight | 1 oz (35µm) |
| Vias | 0.8mm tinned copper wire, solder both sides |
| Components | **100% through-hole** + pre-assembled modules |

---

## Layer stack

| Layer | Usage | Min trace width |
|-------|-------|-----------------|
| **Top** | Components, signal traces, power traces | Signal: 0.5mm, Power: see table below |
| **Bottom** | Wide GND bus (3mm+), ground fill areas | GND: 3mm minimum |

**Critical:** Continuous GND copper on the bottom layer under the **buck converter** and **ESP32** zones. This provides a low-impedance return path and reduces switching noise radiation.

---

## Trace width guide

Same as [SMD version](../12v/pcb_layout_guide_12v.md#trace-width-guide) — no changes. The current ratings are identical.

| Trace | Current | Min width |
|-------|---------|-----------|
| 12V input (J12V → Q1 → V12_PROT) | 1.5A peak | **2.0mm** |
| V12_PROT to buck VIN (via D_EXT) | 1A | **1.5mm** |
| V12_PROT to MT3608 VIN | 0.5A | **1.0mm** |
| Battery path (3S_OUT+ → D_BAT → BUCK_VIN) | 1A | **1.5mm** |
| 5V_RAIL bus | 500mA | **2.0mm** |
| 5V to each encoder (via ferrite) | 100mA | **1.0mm** |
| TP5100 BAT+/BAT− to BMS | 1A | **1.5mm** |
| Signal traces (divider → GPIO) | <1mA | **0.5mm** |
| GND bus (bottom layer) | Total return | **3.0mm+** |

---

## Zone map

Zone A is expanded from ~35×30mm to ~40×35mm to accommodate the IRF4905 TO-220 package and axial DO-201 diodes. All other zones are unchanged.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          120mm × 80mm                                   │
│                                                                         │
│  ZONE A: 12V INPUT (top-left)      │  ZONE B: BATTERY + CHARGER       │
│  ~40mm × 35mm                      │  ~40mm × 30mm                     │
│  ┌──────────────────────────┐      │  ┌──────────────────────────────┐ │
│  │ J12V (DC jack at edge)   │      │  │ MT3608 boost (12V→15V)       │ │
│  │ F1 (fuse + holder)       │      │  │ TP5100 charger module        │ │
│  │ TVS_IN (P6KE18A axial)   │      │  │ BMS_3S board                 │ │
│  │                          │      │  │ J_BAT (JST-XH at edge)      │ │
│  │ Q1 (IRF4905 TO-220)      │      │  │ D_BAT (SS34 DO-201 axial)  │ │
│  │   ← stands upright,      │      │  │ C_BOOST_IN (10µF)           │ │
│  │     leads bent 90°        │      │  │ LED2 (red, battery low)     │ │
│  │ R_G (100kΩ)              │      │  │ R18 (1kΩ)                   │ │
│  │ D_EXT (SS34 DO-201 axial)│      │  └──────────────────────────────┘ │
│  │ C_IN1 + C_IN2            │      │              │                     │
│  │ R_ADC_TOP, R_ADC_BOT     │      │              │                     │
│  │ LED1 (green, power)      │      │              │                     │
│  └──────────────────────────┘      │              │                     │
│              │                     │              │                     │
│              └── V12_PROT ─────────┼── BUCK_VIN ──┘                     │
│                                    │      │                             │
│  ZONE C: BUCK + 5V RAIL           │      │                             │
│  ~40mm × 20mm (center strip)      │      │                             │
│  ┌─────────────────────────────────┴──────┘                             │
│  │ MP1584EN buck module                                                │
│  │ L_FILT (10µH axial) + C_FILT (100µF electrolytic)                 │
│  │ C_OUT1 (220µF) + C_OUT2 (100nF disc)                              │
│  │ D_OR_BUCK (SS34 DO-201 axial)  [D_OR_USB if used]                 │
│  │ 5V_RAIL distribution star point                                     │
│  └─────────────────────────────────┬──────┐                             │
│              │                     │      │                             │
│  ZONE D: SIGNAL CONDITIONING      │  ZONE E: MCU                      │
│  ~40mm × 40mm (left side)         │  ~40mm × 40mm (right side)        │
│  ┌─────────────────────────┐      │  ┌──────────────────────────┐     │
│  │ J1 (Theta 4P) at edge   │      │  │ ESP32 Wemos D1 R32      │     │
│  │  FB1, C3, dividers, TVS │ sigs │  │ (on female headers)     │     │
│  │                         │──────│──│ VIN from 5V_RAIL        │     │
│  │ J2 (Phi 4P) at edge     │      │  │ GND from star point     │     │
│  │  FB2, C4, dividers, TVS │      │  │                         │     │
│  │                         │      │  │ GPIO 36 ← ADC divider   │     │
│  │ J3 (Wire 5P) at edge    │      │  │ GPIO 25 → LED2 (batt)  │     │
│  │  FB3, C5, dividers, TVS │      │  │ Reset btn               │     │
│  │                         │      │  │       [USB edge →]       │     │
│  └─────────────────────────┘      │  └──────────────────────────┘     │
│                                    │                                    │
│  TEST POINTS (bottom edge, accessible with probe)                      │
│  [TP12:V12] [TP15:15V] [TP_BV:BUCK_VIN] [TP5:5V] [TP33:3.3V]        │
│  [TP_BAT:3S_OUT+] [TPG:GND]                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## TO-220 mounting — Q1 (IRF4905)

The IRF4905 in TO-220AB is the largest discrete component on the board. Mount it properly to avoid mechanical and electrical issues:

### Recommended mounting (upright, leads bent 90°)

```
    Side view:                          Top view (component side):

    ┌──────────┐                         ───────────────
    │ IRF4905  │  ← body stands         │  Metal tab  │
    │          │    upright              │  (= Drain)  │
    │          │    (~15mm tall)         │             │
    └──┬──┬──┬┘                         └──┬──┬──┬───┘
       │  │  │   ← leads bent 90°          G  D  S
       │  │  │     toward board             │  │  │
    ───┴──┴──┴──── PCB                   ───┴──┴──┴──── PCB pad row
                                          2.54mm pitch (standard)
```

### Mounting rules

1. **Bend leads at 90°** about 3mm from the body, so the package stands upright. This minimizes PCB footprint (~10mm × 5mm pad area).
2. **No heatsink needed**: 45mW dissipation at 1.5A. The TO-220 tab radiates this easily in free air.
3. **Do NOT bolt the tab to a grounded plane**: The tab is connected to **Drain** (= V12_PROT). Grounding it would short V12_PROT to GND.
4. **Orientation**: Place with the marked side (text) facing outward for inspection. Pin 1 (Gate) on the left when facing the text.
5. **Clearance**: Keep ≥5mm between the TO-220 body and adjacent electrolytic capacitors (C_IN1, C_IN2) to avoid mechanical interference.
6. **Optional stabilization**: A dab of hot-glue at the base prevents the package from flexing under vibration (robot arm environment).

### Pad layout

```
    PCB footprint for Q1 (TO-220AB, upright mount):

    ┌─────────────────┐
    │  ○    ○    ○    │   ← 3 holes, 2.54mm pitch, 1.0mm drill
    │  G    D    S    │
    │ (1)  (2)  (3)   │
    └─────────────────┘
         ~10mm wide

    Trace connections:
    G (Pin 1) ── 100kΩ (R_G) ── GND
    D (Pin 2) ── V12_PROT (2.0mm trace to Zone C)
    S (Pin 3) ── F1/TVS_IN output (2.0mm trace from input chain)
```

---

## Axial diode mounting

All Schottky diodes (SS34/1N5822 in DO-201) and TVS_IN (P6KE18A in DO-15) are axial packages. Two mounting options:

### Horizontal mount (preferred — lower profile)

```
    ──── Anode lead ──┤ DO-201 body ├── Cathode lead (band) ────
                      └─────────────┘
    PCB:  ○───────────────────────────────────────○
          ~8mm body + leads = ~15mm total span
```

- Suitable when board space allows ~15mm horizontal span
- Lower profile (~4mm above board)
- Easier to inspect cathode band orientation

### Vertical mount (saves horizontal space)

```
    Cathode (band) ── top lead, bent over or trimmed
         │
    ┌────┴────┐
    │ DO-201  │  ← stands upright
    │  body   │
    └────┬────┘
         │
    Anode ── through PCB hole

    PCB footprint: ~5mm × 5mm (two holes, 2.54–5.08mm apart)
```

- Use when horizontal space is tight (Zone A has 4–5 axial diodes)
- Higher profile (~8mm above board)
- Harder to read cathode band — mark on PCB silkscreen

### Recommended layout for Zone A

Use **horizontal mount** for D_EXT (SS34) and TVS_IN (P6KE18A) — these are on the main power path and benefit from visible orientation. Use **horizontal mount** for D_BAT and D_OR_BUCK in Zone B/C as well, space permitting.

---

## EMI isolation — buck converter vs encoder signals

Same rules as [SMD version](../12v/pcb_layout_guide_12v.md#emi-isolation--buck-converter-vs-encoder-signals):

1. **Physical separation:** MP1584EN switch node ≥30mm from nearest encoder signal trace
2. **LC post-filter:** 10µH + 100µF between buck output and 5V_RAIL
3. **No parallel runs:** Cross 12V and signal traces at 90°
4. **Bottom-layer GND flood:** Fill bottom with GND copper under Zones C, D, E
5. **Ferrite beads:** 600Ω@100MHz on each encoder VCC (FB1–FB3)
6. **10µF at ESP32 VIN:** If trace >20mm from C_OUT1, add decoupling at VIN-GND
7. **MT3608 isolation:** Charger boost on opposite side from signal traces (Zone B, top-right)

---

## Ground strategy — star topology

Identical to [SMD version](../12v/pcb_layout_guide_12v.md#ground-strategy--star-topology):

```
                     5V_RAIL GND Star Point (at C_OUT1)
                              │
         ┌────────────────────┼──────────────────┬────────────────┐
         │                    │                  │                │
    ┌────┴────┐          ┌────┴────┐        ┌────┴────┐     ┌────┴────┐
    │ Zone A  │          │ Zone B  │        │ Zone D  │     │ Zone E  │
    │ 12V In  │          │ Battery │        │ Signal  │     │  ESP32  │
    │  GND    │          │  GND    │        │  GND    │     │  GND    │
    └────┬────┘          └────┬────┘        └────┬────┘     └────┬────┘
         │                    │                  │                │
         └────────────────────┼──────────────────┴────────────────┘
                              │
               Bottom copper bus (≥3mm wide traces)
               connecting all zones back to star point
```

**Ground rules:**
1. Each zone gets its own GND spoke — no daisy-chaining
2. Encoder shield wires → board entry only (J1–J3)
3. Multiple wire-link vias (0.8mm copper wire) for low impedance
4. Buck input/output GND pins: short, direct traces to star

---

## Assembly sequence and test checkpoints

### Phase 1: 12V Input + Buck Converter (Zone A + C)

**Solder order:**
1. F1 (fuse holder) + F1 (2A fuse)
2. TVS_IN (**P6KE18A axial** — cathode band toward 12V rail)
3. Q1 (**IRF4905 TO-220** — bend leads 90°, upright mount) + R_G (100kΩ)
4. C_IN1 (68µF/35V electrolytic) + C_IN2 (100nF ceramic disc)
5. D_EXT (**SS34 DO-201 axial** — cathode band toward BUCK_VIN)
6. **MP1584EN module** — solder header pins. **Pre-set trim pot to 5.05V first!**
7. L_FILT (10µH axial) + C_FILT (100µF electrolytic)
8. D_OR_BUCK (**SS34 DO-201 axial** — cathode band toward 5V_RAIL)
9. C_OUT1 (220µF/16V) + C_OUT2 (100nF ceramic disc)
10. J12V (DC jack at board edge)
11. LED1 (green) + R17 (1kΩ)
12. Test point pins: TP12, TP5, TP33, TPG

**Test Checkpoint 1:**
- Apply 12V to J12V
- TP12 (V12_PROT): expect ~12V (Q1 drop ~30mV, negligible)
- TP5 (5V_RAIL): expect 5.0–5.1V
- Apply **reverse polarity** to J12V: verify no current, nothing heats
- Apply **10Ω/5W load** on 5V_RAIL (~500mA): verify voltage holds at 4.9–5.1V
- Touch MP1584EN and Q1 after 5 min under load: both barely warm

### Phase 2: Battery + Charger Section (Zone B)

**Solder order:**
1. C_BOOST_IN (10µF/25V)
2. **MT3608 boost module** — solder header pins. **Pre-set trim pot to 15.0V first!**
3. **TP5100 module** — verify **3S jumper** is correctly set before mounting
4. **BMS_3S board** — mount with short wires or headers
5. J_BAT (JST-XH 4-pin at board edge)
6. D_BAT (**SS34 DO-201 axial** — cathode band toward BUCK_VIN)
7. R_ADC_TOP (120kΩ) + R_ADC_BOT (27kΩ)
8. LED2 (red) + R18 (1kΩ)
9. Test point pins: TP15, TP_BV, TP_BAT

**Test Checkpoint 2:**
- With 12V applied to J12V:
  - TP15 (BOOST_15V): expect 14.8–15.2V
  - TP_BV (BUCK_VIN): expect ~11.6V
- Connect **3S LiPo** (~11V) to J_BAT:
  - TP5100 charging LED should light
  - TP_BAT: expect battery voltage (~11V)
- **Disconnect 12V**: TP_BV → ~10.6V (seamless switchover)
- **Reconnect 12V**: external takes over

### Phase 3: ESP32 + Signal Conditioning (Zone D + E)

Same as legacy — all components already THT:
1. Solder female header strips (U_ESP)
2. Insert ESP32 Wemos D1 R32
3. Wire VIN to 5V_RAIL, GND to star point
4. Solder reset button
5. Solder J1, J2, J3 at left edge
6. For each connector: ferrite bead (axial) + 100nF decap
7. Solder all 7 divider networks (R-top, R-bot, C-filter)
8. Solder 7× TVS diodes (1.5KE3.3CA axial)
9. Route signal traces to ESP32 GPIOs
10. Wire-link vias for crossing traces

**Test Checkpoint 3:**
- Flash firmware: `pio run -e wemos_d1_r32 --target upload`
- `PING` → `ACK:PONG`
- Connect one encoder at a time → verify counts on serial monitor
- `STATUS` → verify ADC voltage reading (~12V if monitoring V12_PROT)

### Phase 4: Full Integration Test

Same as [SMD version](../12v/pcb_layout_guide_12v.md#phase-4-full-integration-test):
- 12V adapter + 3S LiPo + all 3 encoders, 30 min continuous
- [ ] No thermal issues (touch-test all modules + Q1 TO-220)
- [ ] Encoder counts stable (no phantom counts)
- [ ] WiFi AP connects and dashboard loads
- [ ] `STATUS` at 20Hz with valid data
- [ ] Battery charging LED active when 12V present
- [ ] Power switchover 5× rapid plug/unplug → no ESP32 resets
- [ ] `ZERO` command works after switchover

---

## First power-on safety procedure

1. **Visual inspection:** Check all solder joints. Verify Q1 (TO-220) pin orientation — Pin 1 (Gate) left, Pin 3 (Source) right when facing text. Check cathode bands on all axial diodes.
2. **Cold resistance check:** 5V_RAIL to GND should be >10kΩ (no shorts)
3. **Current-limited first power:** Apply 12V at 50mA limit → V12_PROT should read ~12V
4. **Verify buck output:** TP5 should be 5.0–5.1V at <50mA, recheck at 500mA
5. **Reverse polarity test:** Reverse 12V leads → zero current, no heat
6. **MOSFET verification (before soldering):** Diode-check mode: Source (Pin 3) → Drain (Pin 2) shows body diode ~0.4V fwd, Drain → Source blocks

---

## Pertinax-specific tips

1. **TO-220 mounting:** Bend leads carefully with pliers 3mm from body. Avoid flexing the plastic package. Solder quickly (<3 sec per pin at 350°C) to avoid melting the package.

2. **Axial diode mounting:** For horizontal mount, pre-form leads to match hole spacing before inserting. Bend one lead slightly to hold the component in place while flipping the board to solder.

3. **Module mounting:** Solder module pins with generous fillets. Pertinax copper adhesion is weaker than FR4. Consider hot-glue on module edges for vibration resistance.

4. **No SMD required:** Unlike the original 12V design, this version requires **no dead-bug soldering, no breakout boards, and no SMD adapters**. Every discrete component has standard through-hole leads.

5. **Trace lift prevention:** Temperature-controlled iron at ≤350°C, <3 seconds per pad. Pertinax is more sensitive to heat than FR4.

6. **Bottom-layer GND:** Fill bottom layer with GND copper. Use multiple 0.8mm wire-link vias (min 6 from star, min 2 per zone spoke).

7. **Conformal coating (optional):** After full integration test, apply clear nail polish or acrylic over solder joints. Avoid coating module trim pots and test points.
