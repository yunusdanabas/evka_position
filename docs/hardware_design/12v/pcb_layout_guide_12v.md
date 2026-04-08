# PCB Layout Guide — 12V + 3S LiPo evka_position

Companion to [pcb_layout_guide.md](../5v/pcb_layout_guide.md) for the legacy 5V board. **Signal zones** (encoder connectors, ESP32, dividers) follow the same discipline; this file covers the **12V power section**, **battery/charger section**, **EMI isolation**, and **assembly sequence**.

---

## Board specification

| Parameter | Value |
|-----------|-------|
| Dimensions | **120mm × 80mm** (same as legacy) |
| Material | Double-sided **pertinax** |
| Copper weight | 1 oz (35µm) |
| Vias | 0.8mm tinned copper wire, solder both sides |
| Components | Through-hole + pre-assembled modules |

---

## Layer stack

| Layer | Usage | Min trace width |
|-------|-------|-----------------|
| **Top** | Components, signal traces, power traces | Signal: 0.5mm, Power: see table below |
| **Bottom** | Wide GND bus (3mm+), ground fill areas | GND: 3mm minimum |

**Critical:** On pertinax, ensure a **continuous GND copper area** on the bottom layer under both the **buck converter** and **ESP32** zones. This provides a low-impedance return path and reduces switching noise radiation.

---

## Trace width guide

| Trace | Current | Min width | Notes |
|-------|---------|-----------|-------|
| 12V input (J12V → Q1 → V12_PROT) | 1.5A peak | **2.0mm** | Short path, Zone A |
| V12_PROT to buck VIN (via D_EXT) | 1A | **1.5mm** | Zone A → Zone C |
| V12_PROT to MT3608 VIN | 0.5A | **1.0mm** | Zone A → Zone B (charger) |
| Battery path (3S_OUT+ → D_BAT → BUCK_VIN) | 1A | **1.5mm** | Zone B → Zone C |
| 5V_RAIL bus | 500mA | **2.0mm** | Same as legacy |
| 5V to each encoder (via ferrite) | 100mA | **1.0mm** | Same as legacy |
| TP5100 BAT+/BAT− to BMS | 1A (charging) | **1.5mm** | Zone B internal |
| Signal traces (divider → GPIO) | <1mA | **0.5mm** | Same as legacy |
| GND bus (bottom layer) | Total return | **3.0mm+** | Star topology |
| LED traces | 5mA | **0.3mm** | Lowest priority |

---

## Zone map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          120mm × 80mm                                   │
│                                                                         │
│  ZONE A: 12V INPUT (top-left)      │  ZONE B: BATTERY + CHARGER       │
│  ~35mm × 30mm                      │  ~45mm × 30mm                     │
│  ┌──────────────────────────┐      │  ┌──────────────────────────────┐ │
│  │ J12V (DC jack at edge)   │      │  │ MT3608 boost (12V→15V)       │ │
│  │ F1 (fuse + holder)       │      │  │ TP5100 charger module        │ │
│  │ TVS_IN (P6KE15CA)        │      │  │ BMS_3S board                 │ │
│  │ Q1 (AO4407A) + R_G       │      │  │ J_BAT (JST-XH at edge)      │ │
│  │ D_EXT (SS34)             │      │  │ D_BAT (SS34)                │ │
│  │ C_IN1 + C_IN2            │      │  │ C_BOOST_IN (10µF)           │ │
│  │ R_ADC_TOP, R_ADC_BOT     │      │  │ LED2 (red, battery low)     │ │
│  │ LED1 (green, power)      │      │  │ R18 (1kΩ)                   │ │
│  └──────────────────────────┘      │  └──────────────────────────────┘ │
│              │                     │              │                     │
│              └── V12_PROT ─────────┼── BUCK_VIN ──┘                     │
│                                    │      │                             │
│  ZONE C: BUCK + 5V RAIL           │      │                             │
│  ~40mm × 20mm (center strip)      │      │                             │
│  ┌─────────────────────────────────┴──────┘                             │
│  │ MP1584EN buck module                                                │
│  │ L_FILT (10µH) + C_FILT (100µF)   ← LC post-filter                 │
│  │ C_OUT1 (220µF) + C_OUT2 (100nF)  ← 5V_RAIL bulk + HF              │
│  │ D_OR_BUCK (SS34)                  ← [D_OR_USB if used]             │
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

## EMI isolation — buck converter vs encoder signals

The MP1584EN switches at **~1.5MHz**. On pertinax (no plated vias, no solid ground plane), switching noise couples more easily into nearby signal traces via:
- **Capacitive coupling** between adjacent traces
- **Inductive coupling** from the buck inductor's magnetic field
- **Conducted noise** on the 5V rail (output ripple)

### Layout rules

1. **Physical separation:** Place the MP1584EN module's **switch node ≥30mm** from the nearest encoder signal divider trace, and the **inductor body ≥20mm** away. On the zone map above, Zone C (buck) is separated from Zone D (signals) by the 5V_RAIL distribution strip. Keep the buck module's SW node trace (between inductor, diode, and MOSFET drain) as **short as possible (<10mm)** — it is the primary EMI radiator.

2. **LC post-filter:** Between the MP1584EN output and the 5V_RAIL distribution point, insert a **10µH inductor + 100µF electrolytic**. This reduces conducted ripple from ~50mV peak-to-peak to **<5mV** — well below the encoder signal noise margin.

3. **No parallel runs:** Do not route 12V or BUCK_VIN traces parallel to encoder signal traces. Cross at **90°** if they must intersect.

4. **Bottom-layer GND flood:** Fill as much of the bottom layer as practical with GND copper under Zones C, D, and E. This acts as a partial shield and provides low-impedance return paths. Connect to the star point via multiple wire-link vias.

5. **Ferrite beads remain:** The existing **600Ω@100MHz ferrite beads** on each encoder VCC feed (FB1–FB3) attenuate high-frequency noise at the encoder power pin. Combined with the LC post-filter, this provides two stages of filtering.

6. **10µF ceramic at ESP32 VIN:** If the PCB trace from C_OUT1 (5V_RAIL bulk cap) to the ESP32 VIN pin is longer than **~20mm**, add a **10µF ceramic X7R capacitor** directly at the ESP32 VIN-to-GND pins on the board. This prevents the MP1584EN's 1MHz switching ripple from degrading WiFi performance (the ESP32's on-chip LDO for the RF front-end is sensitive to >50mV ripple on VIN).

6. **MT3608 boost isolation:** The charger boost converter (Zone B) also switches at ~1.2MHz. Place it on the **opposite side** of the board from signal traces (top-right corner). Its output only feeds the TP5100, not the encoder signal path.

---

## Ground strategy — star topology

Same philosophy as the legacy board. Central star point at the **5V_RAIL bulk capacitor** (C_OUT1).

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

**Ground rules for pertinax:**
1. Each zone gets its own GND spoke to the star point — no daisy-chaining
2. Encoder shield wires connect to GND at board entry only (J1–J3)
3. Multiple wire-link vias (0.8mm copper wire) ensure low impedance between top and bottom layers
4. The buck converter's input and output GND pins must have **short, direct** traces (or wire links) to the star point

---

## Assembly sequence and test checkpoints

### Phase 1: 12V Input + Buck Converter (Zone A + C)

**Solder order:**
1. F1 (fuse holder) + F1 (2A fuse)
2. TVS_IN (P6KE15CA or SMBJ18A)
3. Q1 (AO4407A — dead-bug solder SOT-23/SOIC-8 on pertinax, or use breakout) + R_G (100kΩ)
4. C_IN1 (68µF/35V) + C_IN2 (100nF/50V)
5. D_EXT (SS34)
6. **MP1584EN module** — solder header pins through board. **Pre-set trim pot to 5.05V first!**
7. L_FILT (10µH) + C_FILT (100µF) — LC post-filter
8. D_OR_BUCK (SS34)
9. C_OUT1 (220µF/16V) + C_OUT2 (100nF)
10. J12V (DC jack at board edge)
11. LED1 (green) + R17 (1kΩ)
12. Test point pins: TP12, TP5, TP33, TPG

**Test Checkpoint 1:**
- Apply 12V to J12V
- TP12 (V12_PROT): expect ~12V (minimal Q1 drop)
- TP5 (5V_RAIL): expect 5.0–5.1V
- Apply **reverse polarity** to J12V: verify no current, nothing heats
- Apply **10Ω/5W load** on 5V_RAIL (~500mA): verify voltage holds at 4.9–5.1V
- Touch MP1584EN module after 5 min under load: should be barely warm

### Phase 2: Battery + Charger Section (Zone B)

**Solder order:**
1. C_BOOST_IN (10µF/25V)
2. **MT3608 boost module** — solder header pins. **Pre-set trim pot to 15.0V first!**
3. **TP5100 module** — verify **3S jumper** is correctly set before mounting
4. **BMS_3S board** — mount with short wires or headers
5. J_BAT (JST-XH 4-pin at board edge)
6. D_BAT (SS34) — from BMS P+ (3S_OUT+) to BUCK_VIN node
7. R_ADC_TOP (120kΩ) + R_ADC_BOT (27kΩ) — ADC divider
8. LED2 (red) + R18 (1kΩ)
9. Test point pins: TP15, TP_BV, TP_BAT

**Test Checkpoint 2:**
- With 12V applied to J12V:
  - TP15 (BOOST_15V): expect 14.8–15.2V
  - TP_BV (BUCK_VIN): expect ~11.6V (12V through D_EXT)
- Connect **3S LiPo** (partially charged, ~11V) to J_BAT:
  - TP5100 charging LED should light
  - TP_BAT: expect battery voltage (~11V)
- **Disconnect 12V** (pull J12V plug):
  - TP_BV should show ~10.6V (battery voltage minus D_BAT Vf)
  - TP5 (5V_RAIL) should remain at ~5.0V (seamless switchover)
  - **No glitch or reset on ESP32** (if mounted)
- **Reconnect 12V**: external takes over, battery stops discharging

### Phase 3: ESP32 + Signal Conditioning (Zone D + E)

Same as legacy board:
1. Solder female header strips (U_ESP)
2. Insert ESP32 Wemos D1 R32
3. Wire VIN to 5V_RAIL, GND to star point
4. Solder reset button
5. Solder J1, J2, J3 at left edge
6. For each connector: ferrite bead + 100nF decap
7. Solder all 7 divider networks (R-top, R-bot, C-filter)
8. Solder 7× TVS diodes
9. Route signal traces to ESP32 GPIOs
10. Wire-link vias for crossing traces

**Test Checkpoint 3:**
- Flash firmware: `pio run -e wemos_d1_r32 --target upload`
- `PING` → `ACK:PONG`
- Connect one encoder at a time → verify counts on serial monitor
- `STATUS` → verify ADC voltage reading (should show ~12V if monitoring V12_PROT)

### Phase 4: Full Integration Test

**All systems connected simultaneously:**
- 12V power adapter + 3S LiPo battery + all 3 encoders
- Run for **30 minutes continuous** — check:
  - [ ] No thermal issues (touch-test all modules)
  - [ ] Encoder counts stable (no noise-induced phantom counts)
  - [ ] WiFi AP connects and dashboard loads
  - [ ] `STATUS` command returns valid data at 20Hz
  - [ ] Battery charging LED active when 12V present
- **Power switchover test:**
  - [ ] Unplug 12V → system continues on battery, no encoder count skip
  - [ ] Replug 12V → system seamlessly returns to external power
  - [ ] Repeat 5× rapidly (plug/unplug) → no ESP32 resets
- **ZERO command test:** After switchover, send `ZERO` → `ACK:ZERO`

---

## First power-on safety procedure

Before connecting 12V to the completed board:

1. **Visual inspection:** Check all solder joints with a magnifier. Look for bridges on SOT-23/SOIC-8 pads (Q1) and between adjacent divider resistors
2. **Cold resistance check:** Measure resistance from 5V_RAIL to GND with no power applied — should be >10kΩ. If low, there is a short
3. **Current-limited first power:** Apply 12V through a **current-limited supply set to 50mA**. Measure V12_PROT — should read ~12V. If current limit trips, there is a wiring fault in the protection circuit
4. **Verify buck output:** Measure 5V_RAIL (TP5) — should be 5.0–5.1V with <50mA load. Increase current limit to 500mA and recheck
5. **Reverse polarity test:** Reverse the 12V leads briefly. Verify zero current draw and no component heating
6. **MOSFET verification (if unsure about orientation):** Before soldering Q1, use diode-check mode on your multimeter: Source→Drain should show body diode (~0.4V forward), Drain→Source should block

---

## Pertinax-specific tips

1. **Module mounting:** Solder module pins with generous fillets. Pertinax copper adhesion is weaker than FR4 — avoid pulling on modules during assembly or testing. Consider a dab of **hot-glue** on module edges for vibration resistance (robot arm environment).

2. **SMD on pertinax:** The AO4407A (SOIC-8) and SMBJ18A (SMB) are surface-mount. Options:
   - Dead-bug solder directly to copper pads cut into the pertinax
   - Use a small **SOT-23 or SOIC-8 breakout board** (~$0.10, DIP adapter)
   - For AO4407A: alternative through-hole P-FET in TO-220 (e.g. IRF9540N, 100V/23A — overkill but easy to solder)

3. **Trace lift prevention:** On pertinax, heavy soldering can lift traces. Use a **temperature-controlled iron** at 350°C max, and hold the tip on the pad for <3 seconds.

4. **Bottom-layer GND:** Even without plating, fill the bottom layer generously with GND copper. Use multiple 0.8mm wire-link vias to connect top GND pads to the bottom bus. Minimum **6 vias** from star point to bottom layer, **2 vias** per zone spoke.

5. **Conformal coating (optional):** After full integration test passes, apply a thin layer of **clear nail polish or acrylic conformal coating** over solder joints. This protects against corrosion and vibration in the robot arm environment. Avoid coating module trim pots and test points.
