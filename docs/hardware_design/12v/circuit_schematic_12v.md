# Circuit Schematic — evka_position 12V Input PCB

> Carrier for **ESP32 Wemos D1 R32** + **three 5V quadrature encoders** with **12V DC input**, **buck to 5V**, **3S LiPo battery backup** with onboard charging, and optional **USB 5V OR** for bench programming.  
> **Signal conditioning (7× dividers, GPIO pins, TVS, ferrites)** is **identical** to [circuit_schematic.md](../5v/circuit_schematic.md) sections **3–7**; this file documents **power entry**, **battery management**, and **12V rail ADC**.

---

## 1. System block diagram

```
 ╔══════════════════════════════════════════════════════════════════════════════════════════════╗
 ║                    evka_position 12V + 3S LiPo — FULL POWER SCHEMATIC                       ║
 ╠══════════════════════════════════════════════════════════════════════════════════════════════╣
 ║                                                                                             ║
 ║   J12V (+12V GND)                                                                           ║
 ║       │                                                                                     ║
 ║    [F1 FUSE 2A]                                                                             ║
 ║       │                                                                                     ║
 ║   [TVS_IN SMBJ18A] ── GND                                                                  ║
 ║       │                                                                                     ║
 ║   [Q1 AO4407A P-FET RPP]                                                                   ║
 ║       │                                                                                     ║
 ║   V12_PROT ──────────────────────────────────────────────────────────────┐                   ║
 ║       │                                                                  │                   ║
 ║       ├── 120k ──┬── 27k ── GND  → GPIO 36 (12V monitor ADC)           │                   ║
 ║       │          │                                                       │                   ║
 ║       │     (ADC tap)                                                    │                   ║
 ║       │                                                                  │                   ║
 ║       ├── D_EXT (SS34) ──┬── BUCK_VIN                                   │                   ║
 ║       │                   │                                              │                   ║
 ║       │              D_BAT (SS34)                                        │                   ║
 ║       │                   │                                              │                   ║
 ║       │              3S_OUT+ (BMS output, 9.0–12.6V)                    │                   ║
 ║       │                                                                  │                   ║
 ║       │   BUCK_VIN ── [C_IN bulk] ── U_BUCK (MP1584EN 12V→5V)          │                   ║
 ║       │                                   │                              │                   ║
 ║       │                              5V_BUCK (~5.05V)                   │                   ║
 ║       │                                   │                              │                   ║
 ║       │                 D_OR_BUCK (SS34) ──┤                             │                   ║
 ║       │                 D_OR_USB  (SS34) ──┤  (USB optional)            │                   ║
 ║       │                                    │                             │                   ║
 ║       │                              5V_RAIL ── ESP32 VIN, J1–J3 +5V   │                   ║
 ║       │                                                                  │                   ║
 ║       │   ┌──────────────────────────────────────────────────────────────┘                   ║
 ║       │   │                                                                                 ║
 ║       │   │   CHARGER PATH                                                                 ║
 ║       │   │   ═══════════                                                                   ║
 ║       │   └── MT3608 Boost (12V → 15V) ── TP5100 (3S mode)                                ║
 ║       │                                        │                                            ║
 ║       │                                   BAT+/BAT-                                         ║
 ║       │                                        │                                            ║
 ║       │                                   3S BMS Board                                      ║
 ║       │                                        │                                            ║
 ║       │                                   J_BAT (JST-XH 4P)                                ║
 ║       │                                        │                                            ║
 ║       │                                   3S LiPo (11.1V nom)                              ║
 ║       │                                                                                     ║
 ╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. 12V input — fuse, TVS, reverse polarity

### 2a. Fuse

Place a **2A glass fuse** (or **1.1A PTC polyfuse**) immediately after **J12V** `+` terminal. Size to **wire harness** and **total system draw** (~1A buck + ~0.5A charger peak = ~1.5A max).

```
    J12V+ ──── F1 (2A) ──── to TVS_IN node
```

### 2b. Transient clamp (Class A: 9–16V adapter)

```
    F1 output ────┬──── TVS_IN (SMBJ18A) ────┬──── GND
                  │         (cathode to rail) │
                  │                           │
             to RPP (Q1)                      │
```

**SMBJ18A** clamps at **~18V** standoff — suitable when the **normal** bus stays **≤16V**. For **lower** clamp use **SMBJ15A**; verify **standoff** vs **maximum** adapter open-circuit voltage.

### 2c. Reverse polarity protection (high-side P-FET)

```
    F1/TVS output ──── S (Source)
                       │
                  ┌────┴────┐
                  │ AO4407A │  (SOIC-8 P-MOSFET, Vds = -40V)
                  │ P-FET   │
                  └────┬────┘
                       │
             100kΩ ────┤──── G (Gate)
                       │
                      GND

    D (Drain) ──────────────── V12_PROT (protected 12V rail)

    Operation:
    - Correct polarity: Gate LOW (100k to GND) → Vgs = -12V → MOSFET fully ON
      Rds(on) ~12mΩ @ Vgs = -10V → drop = 12mΩ × 1.5A = 18mV (negligible)
    - Reversed polarity: Gate driven positive → MOSFET OFF → blocks current
    - AO4407A abs max Vgs = ±20V, Vds = -40V → safe at 12V with headroom
```

**Alternative (simpler):** Series Schottky **SS36** (3A, 60V) from F1 output to V12_PROT. Drop ~0.35V at 1.5A. Omit Q1 and R_G.

---

## 3. Schottky OR — 12V external vs 3S battery (at buck input)

Two SS34 Schottky diodes merge the external 12V and battery paths before the buck converter:

```
    V12_PROT ── D_EXT (SS34) ──|>|──┬── BUCK_VIN
                                     │
    3S_OUT+  ── D_BAT (SS34) ──|>|──┘
    (BMS output, 9.0–12.6V)

    SS34 specs: 3A, Vf ≈ 0.3–0.4V @ 1A, DO-214AB (SMA) or DO-201 (axial)
```

**Behavior:**

| Condition | BUCK_VIN | Source |
|-----------|----------|--------|
| 12V only (no battery) | ~11.6V (12V − Vf) | External via D_EXT |
| Battery only (no 12V) | ~10.7V (11.1V nom − Vf) | 3S LiPo via D_BAT |
| Both present | ~11.6V | External wins (higher voltage) |
| 12V disconnected | Seamless switchover <1ms | Battery via D_BAT, C_IN holds voltage during transition |

**Important:** The buck converter (MP1584EN) accepts **4.5–28V input**, so both paths (11.6V external, 9.0–12.2V battery) are within range.

---

## 4. Buck converter 12V → 5V

**Module path (recommended):** MP1584EN adjustable step-down module. Set trim pot to **5.05V** output.

```
    BUCK_VIN ── 68µF/35V ──┬── VIN (MP1584EN module)
                            │
                       100nF/50V X7R
                            │
                           GND

    VOUT (module) ──── LC post-filter ──── 5V_BUCK

    LC Post-Filter (recommended for encoder noise isolation):
    ┌──────────────────────────────────────────────────────┐
    │  VOUT ── L_FILT (10µH) ──┬── 100µF/10V ── GND      │
    │                          │                           │
    │                     5V_BUCK                          │
    │                                                      │
    │  Reduces switching ripple from ~50mV to <5mV         │
    │  on the 5V rail feeding encoders                     │
    └──────────────────────────────────────────────────────┘
```

**Pre-set the trim pot** to 5.05V using a multimeter and ~200mA resistive dummy load (25Ω/2W resistor) **before** connecting to the rest of the circuit.

Confirm **<100mV** sag when WiFi associates.

---

## 5. 5V_RAIL Schottky OR — buck vs USB

```
    5V_BUCK ──|>|── D_OR_BUCK (SS34) ──┬── 5V_RAIL
    5V_USB  ──|>|── D_OR_USB  (SS34) ──┘   (optional, for bench programming)
```

- **Buck** (~5.05V) dominates when **12V** is present → 5V_RAIL ≈ 4.85V after Schottky
- **USB only:** ~4.65V at 5V_RAIL — sufficient for ESP32, marginal for encoders under full load
- If **USB is never connected while 12V is present**, you may omit D_OR_USB and connect buck output directly to 5V_RAIL (one Schottky D_OR_BUCK still recommended for reverse-current protection)

---

## 6. 3S LiPo battery — charger and BMS

### 6a. Boost converter for charger (MT3608)

The TP5100 3S charger requires **Vin > 12.6V + ~1V dropout ≈ 13.6V minimum** to fully charge a 3S pack. Since the 12V input is typically 11.5–12.5V under load, a **boost stage** is needed.

```
    V12_PROT ──┬── 10µF/25V ── GND    (input decoupling for MT3608)
               │
               └── MT3608 Module
                      │
                   VIN ← V12_PROT (~12V)
                   GND ← GND
                   VOUT → 15V (set via trim pot)
                      │
                   To TP5100 VIN

    Set MT3608 trim pot to 15.0V.
    Verify under ~500mA load (33Ω/5W resistor) before connecting TP5100.
    Efficiency ~85% at 12V→15V, 1A → dissipation ~0.5W (module handles this).
```

**Why 15V?** Gives ~1.4V headroom above 3S full charge (12.6V) + TP5100 dropout (~1V). The TP5100 has internal regulation and will limit the charge voltage precisely to 12.6V regardless of the 15V input.

### 6b. TP5100 charger module (3S mode)

```
    MT3608 VOUT (15V) ──── TP5100 VIN
                            │
    GND ──────────────── TP5100 GND
                            │
    TP5100 BAT+ ──────── BMS P+ (or B+ depending on BMS wiring)
    TP5100 BAT- ──────── BMS P- (or B- depending on BMS wiring)
                            │
    TP5100 mode: Set jumper/solder bridge for 3S (12.6V charge termination)
    Default charge current: ~2A (depends on PROG resistor)
    Recommended: Set to 1A or less for 1500mAh pack (≤1C rate)
```

**TP5100 features:**
- CC/CV charging: constant current until 12.6V, then tapers current
- Status LEDs: charging (red), standby (green)
- Input range: 5–18V (15V from MT3608 is well within range)
- **Does NOT balance cells** — the BMS handles cell-level protection

### 6c. 3S BMS (Battery Management System)

A **3S 10A BMS** module provides individual cell protection:

```
    TP5100 BAT+ ──── P+ ┌───────────────┐ B+ ──── LiPo Cell 3 (+)
    TP5100 BAT- ──── P- │   3S BMS      │ B- ──── LiPo Cell 1 (−)
                        │   10A rated    │ BM ──── Cell 1-2 junction
                        │               │ B2 ──── Cell 2-3 junction
                        └───────────────┘
                             │
    3S_OUT+ ◄──── P+ (charge/discharge common terminal)
    GND      ◄──── P- (charge/discharge common ground)
```

**BMS protections:**
- **Overcharge cutoff:** 4.25V per cell (12.75V total)
- **Overdischarge cutoff:** 2.5–2.8V per cell (7.5–8.4V total)
- **Short-circuit protection:** ~10A (cuts off in <1ms)
- **Overcurrent protection:** 10A continuous

**CRITICAL:** The BMS **P+/P-** terminals are the common charge/discharge path. The **D_BAT Schottky** connects from **P+** (3S_OUT+) to **BUCK_VIN** for the battery backup power path.

### 6d. Battery connector (JST-XH 4-pin)

```
    J_BAT (JST-XH-4P, 2.5mm pitch)
    ┌──────────────────────────────┐
    │ Pin 1: Cell 1 (−) ─── B-    │
    │ Pin 2: Cell 1-2 junction ── BM  │
    │ Pin 3: Cell 2-3 junction ── B2  │
    │ Pin 4: Cell 3 (+) ─── B+    │
    └──────────────────────────────┘

    Standard 3S LiPo balance lead pinout.
    JST-XH used (not JST-PH) — larger pitch, rated for higher current.
```

### 6e. Battery low indicator

```
    GPIO 25 ── 1kΩ (R18) ──┤>── GND    (Red LED — battery low, firmware-driven)
```

Firmware drives GPIO 25 HIGH when battery voltage drops below threshold (~9.5V / 20%).

---

## 7. 12V / battery voltage monitoring (GPIO 36)

Use **120k** (top) + **27k** (bottom) from **V12_PROT** (protected rail) to GND. This monitors whichever source is active (12V external or battery through the Schottky OR and reverse path).

For **direct battery monitoring** (independent of external power), connect the ADC divider from **3S_OUT+** (BMS P+) instead of V12_PROT. Choose one:

- **Option A (recommended):** Monitor V12_PROT — shows the active supply voltage
- **Option B:** Monitor 3S_OUT+ — shows battery state-of-charge specifically

```
    V12_PROT (or 3S_OUT+) ── 120k ──┬── GPIO 36 (ADC1_CH0)
                                     │
                                27k  │
                                     │
                                    GND
```

| Input voltage | ADC node (ideal) | Meaning |
|---------------|-------------------|---------|
| 9.0V | 1.65V | 3S empty (3 × 3.0V) |
| 11.1V | 2.04V | 3S nominal (3 × 3.7V) |
| 12.0V | 2.20V | External 12V present |
| 12.6V | 2.31V | 3S full charge (3 × 4.2V) |
| 15.0V | 2.75V | Max expected (adapter tolerance) |

Scale factor: **V_in = V_adc × (120k + 27k) / 27k** = **V_adc × 5.444**

**Firmware TODO** (when ready): Update `BATT_DIVIDER_RATIO` to `5.444`, `BATT_FULL_V` to `12.6`, `BATT_EMPTY_V` to `9.0` in `SphericalSensor.h`.

---

## 8. Encoder + ESP32 signal section (unchanged)

Copy **verbatim** from [circuit_schematic.md](../5v/circuit_schematic.md):

- **Section 3** — voltage dividers **10k / 20k / 1nF** + **1.5KE3.3CA** (or **SMBJ3.3CA**)
- **Section 3b** — **J1 / J2 / J3** pin map to **GPIO 14, 12, 32, 35, 16, 17, 18** (same as [CLAUDE.md](../../../CLAUDE.md))
- **Sections 4–7** — ESP32 **VIN** from **5V_RAIL**, ferrites, LEDs, decoupling

**Note:** All three encoders run on **5V from 5V_RAIL** — do NOT connect any encoder to the 12V rail. The DWE3000 accepts 5–30V but its HLD output swings to the supply rail; powering it at 12V would produce 0–12V output signals that exceed the voltage divider design (3.33V target) and damage the ESP32.

---

## 9. Net summary (12V + 3S battery)

| Net | Source | Destinations | Expected voltage |
|-----|--------|--------------|------------------|
| J12V+ | Connector | F1 → TVS → Q1 | Raw 12V input |
| V12_PROT | Q1 drain | D_EXT, MT3608 VIN, ADC divider top | ~12V (protected) |
| 3S_OUT+ | BMS P+ | D_BAT anode | 9.0–12.6V (battery dependent) |
| BUCK_VIN | D_EXT / D_BAT cathodes | MP1584EN VIN, C_IN | 9.0–11.8V |
| 5V_BUCK | MP1584EN output | LC filter → D_OR_BUCK anode | 5.05V |
| 5V_USB | USB via Schottky | D_OR_USB anode | ~4.8V (optional) |
| 5V_RAIL | D_OR cathodes | ESP32 VIN, J1–J3 VCC (via ferrites), LEDs | 4.7–4.9V |
| BOOST_15V | MT3608 output | TP5100 VIN | ~15V |
| BAT_CHG+ | TP5100 BAT+ | BMS P+ | 0–12.6V (charging) |
| BAT_ADC | Divider midpoint | GPIO 36 | 1.65–2.75V |
| GND | Common | All components | 0V |

---

## 10. Test points

| TP | Signal | Expected (Class A, 12V adapter) |
|----|--------|----------------------------------|
| TP12 | V12_PROT | 11.5–12.5V (adapter dependent) |
| TP15 | BOOST_15V | 14.8–15.2V (MT3608 output) |
| TP_BV | BUCK_VIN | 9.0–11.8V (whichever OR path is active) |
| TP5 | 5V_RAIL | 4.7–4.9V |
| TP33 | 3.3V (ESP32) | 3.25–3.35V |
| TP_BAT | 3S_OUT+ | 9.0–12.6V (battery state dependent) |
| TPG | GND | 0V reference |

---

## 11. Important warnings

1. **Pre-set ALL module trim pots before connecting to circuit:**
   - MP1584EN → 5.05V (use 25Ω/2W dummy load)
   - MT3608 → 15.0V (use 33Ω/5W dummy load)
2. **TP5100 3S jumper:** Verify solder bridge is set for 3S mode (12.6V termination), NOT 2S (8.4V)
3. **BMS is mandatory:** TP5100 does not balance cells or protect against overdischarge. The 3S BMS provides cell-level safety.
4. **Never connect 3S LiPo without BMS** — unbalanced cells are a fire risk
5. **DWE3000 on 5V only** — see section 8 note
6. **Do not feed 12V directly to ESP32 VIN** — the onboard AMS1117-3.3 would dissipate (12−3.3)×0.2A = 1.74W, risking thermal shutdown. Always use the 5V buck output.
