# Circuit Schematic — EVKA Position V2

> Complete system schematic for the ESP32-S3 based spherical positioning sensor.  
> **100% through-hole**, LPKF S63 compatible, double-sided pertinax/FR4.  
> Dimensions: 120mm × 80mm.

---

## 1. Full System Block Diagram

```
 ╔══════════════════════════════════════════════════════════════════════════════════════════════╗
 ║                         EVKA POSITION V2 — FULL SYSTEM SCHEMATIC                            ║
 ╠══════════════════════════════════════════════════════════════════════════════════════════════╣
 ║                                                                                              ║
 ║  POWER INPUT SECTION                                                                         ║
 ║  ═══════════════════                                                                         ║
 ║                                                                                              ║
 ║   J12V (5.5×2.1mm)                                                                           ║
 ║       │                                                                                      ║
 ║    [NTC 5D-9]                                                                                ║
 ║       │                                                                                      ║
 ║    [F1 PTC 1.1A]                                                                             ║
 ║       │                                                                                      ║
 ║   [TVS_IN P6KE18A] ── GND                                                                   ║
 ║       │                                                                                      ║
 ║   [Q1 IRF4905 RPP]                                                                           ║
 ║       │                                                                                      ║
 ║   V12_PROT ────────────────────────────────────────────────────────────────┐                 ║
 ║       │                                                                    │                 ║
 ║       ├── 120k ──┬── 27k ── GND  → GPIO 1 (12V monitor ADC)               │                 ║
 ║       │          │                                                         │                 ║
 ║       │     (ADC tap)                                                      │                 ║
 ║       │                                                                    │                 ║
 ║       ├── D_EXT (SS34) ──┬── BUCK_VIN                                     │                 ║
 ║       │                   │                                                │                 ║
 ║       │              D_BAT (SS34)                                          │                 ║
 ║       │                   │                                                │                 ║
 ║       │              3S_OUT+ (BMS output)                                  │                 ║
 ║       │                                                                    │                 ║
 ║       │   BUCK_VIN ── [220µF/35V] ── U_BUCK (MP1584EN 12V→5.05V)            │                 ║
 ║       │                                   │                                │                 ║
 ║       │                              5V_BUCK (~5.05V)                     │                 ║
 ║       │                                   │                                │                 ║
 ║       │                 22µH ──┬── 220µF/10V ── GND                       │                 ║
 ║       │                        │                                           │                 ║
 ║       │                   5V_FILTERED                                      │                 ║
 ║       │                        │                                           │                 ║
 ║       │                 D_OR (SS36) ──── 5V_RAIL ───┬── ESP32 VIN         │                 ║
 ║       │                                             │                      │                 ║
 ║       │   ┌─────────────────────────────────────────┘                      │                 ║
 ║       │   │                                                                │                 ║
 ║       │   │   CHARGER PATH                                                 │                 ║
 ║       │   │   ═══════════                                                   │                 ║
 ║       │   └── BQ24650 (12V → 12.6V/1A, 3S) ── 3S BMS ── J_BAT (JST-XH 4P)   │                 ║
 ║       │                                        │                           │                 ║
 ║       │                                   3S LiPo (11.1V)                  │                 ║
 ║       │                                                                    │                 ║
 ║       │   (BQ24650 internal UVLO — no external divider needed)               │                 ║
 ║       │                                                                    │                 ║
 ╠═══════╪════════════════════════════════════════════════════════════════════╪═════════════════╣
 ║       │                                                                SIGNAL SECTION      ║
 ║       │                                                                ═══════════════      ║
 ║       │                                                                                      ║
 ║       │   5V_RAIL ──┬── FB1 ── J1 Pin 1 (Theta VCC) ── 100nF ── GND                       ║
 ║       │             │                                                                      ║
 ║       │             ├── FB2 ── J2 Pin 1 (Phi VCC) ── 100nF ── GND                          ║
 ║       │             │                                                                      ║
 ║       │             └── FB3 ── J3 Pin 1 (Wire VCC) ── 100nF ── GND                         ║
 ║       │                                                                                      ║
 ║       │   J1: THETA (GPIO 4,5)     J2: PHI (GPIO 6,7)      J3: WIRE (GPIO 15,16,17)       ║
 ║       │   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐          ║
 ║       │   │ Pin 3: A ──10k──┬──20k─GND─TVS─GPIO 4  │    │ Pin 3: A ──10k──┬──20k─GND─TVS─GPIO 15 │
 ║       │   │ Pin 4: B ──10k──┴──20k─GND─TVS─GPIO 5  │    │ Pin 4: B ──10k──┴──20k─GND─TVS─GPIO 16 │
 ║       │   └──────────────────┘    └──────────────────┘    │ Pin 5: Z ──10k──┬──20k─GND─TVS─GPIO 17 │
 ║       │                                                   └──────────────────────┘          ║
 ║       │                                                                                      ║
 ╠═══════╪══════════════════════════════════════════════════════════════════════════════════════╣
 ║       │                                                          EXPANSION SECTION         ║
 ║       │                                                          ═════════════════         ║
 ║       │                                                                                      ║
 ║       │   RS-485: GPIO 13/14/18 → MAX485 → J_RS485 (A, B, GND)                               ║
 ║       │                                                                                      ║
 ║       │   I2C: GPIO 11/12 → 4.7kΩ pull-ups → 1.5KE3.3CA TVS → J_I2C (SDA, SCL, 3.3V, GND)  ║
 ║       │                                                                                      ║
 ║       │   WATCHDOG: MAX813L → WDI (GPIO 9 toggle) → RESET → ESP32 EN                        ║
 ║       │                                                                                      ║
 ║       │   SPARE GPIO: GPIO 21/38/39/40 → J_GPIO header                                       ║
 ║       │                                                                                      ║
 ║       │   LEDS: GPIO 8 (Blue WiFi), GPIO 9 (Yellow Activity), GPIO 10 (Red Fault)           ║
 ║       │         + Power LED (Green, hardwired from 5V_RAIL)                                 ║
 ║       │                                                                                      ║
 ║       │   RESET: Button → MAX813L MR → ESP32 EN                                             ║
 ║       │                                                                                      ║
 ╚═══════╧══════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Power Input Detail

### 2a. Complete Input Path

```
    J12V+ ──── NTC 5D-9 ──── F1 (PTC 1.1A) ────┬───┬─── P6KE18A (cathode band to rail) ── GND
                                                │   │
                                                │   └─── Q1 IRF4905 Source (pin 3)
                                                │
                                                └─── (alternative: SS36 series Schottky)

    Q1 wiring:
    Pin 3 (Source) ←── F1 output
    Pin 1 (Gate) ←── 100kΩ ─── GND
    Pin 2 (Drain) ──── V12_PROT
    Tab (Drain) ──── V12_PROT  [Do NOT ground tab!]
```

### 2b. Test Point TP12

```
    V12_PROT ──── TP12
    Expected: 11.5–12.5V (with 12V adapter)
```

---

## 3. Schottky OR Detail

```
    V12_PROT ── Anode ─┤ │─ Cathode (band) ──┬── BUCK_VIN ──── TP_BV
                       │SS34│                │
    3S_OUT+  ── Anode ─┤ │─ Cathode (band) ──┘
                       │SS34│
```

---

## 4. Buck Converter Detail

### 4a. MP1584EN Module Wiring

```
    BUCK_VIN ──┬── 220µF/35V ── GND    (input bulk)
               │
               ├── 100nF ceramic disc ── GND  (HF bypass)
               │
               └── VIN (MP1584EN module pin)
    
    GND ─────── GND (MP1584EN module pin)
    
    VOUT (MP1584EN) ──── 22µH ───┬── 220µF/10V low-ESR ── GND
                                │
                           5V_BUCK
                                │
                           100nF ceramic disc ── GND
                                │
                           SS36 Schottky ──── 5V_RAIL
```

### 4b. 5V Rail Distribution

```
    5V_RAIL ────┬─── ESP32 VIN (pin 18 on both headers)
                │
                ├─── LED1 (Green, power) ── 1kΩ ── GND
                │
                ├─── FB1 ── J1 Pin 1 (Theta VCC) ── 100nF ── GND
                │
                ├─── FB2 ── J2 Pin 1 (Phi VCC) ── 100nF ── GND
                │
                ├─── FB3 ── J3 Pin 1 (Wire VCC) ── 100nF ── GND
                │
                ├─── MAX485 VCC (pin 8)
                │
                ├─── MAX813L VCC (pin 8)
                │
                └─── J_I2C Pin 3 (3.3V via AMS1117, or 5V if needed)
```

---

## 5. Charger Detail

### 5a. BQ24650 Module Wiring

> **Part:** BQ24650 3S Charging Module (AliExpress, factory-configured for 3S / 12.6V)  
> **Why:** CN3767 is a lead-acid charger — wrong chemistry for LiPo. BQ24650 is a synchronous
> buck charger with true CC/CV termination at 4.2V/cell (12.6V for 3S).

```
    V12_PROT ──── BQ24650 VIN  (module input, 6–28V range)
    GND ────────── BQ24650 GND
    
    BQ24650 VOUT ──── 3S BMS P+ (charge input)
    BQ24650 GND ───── 3S BMS P-
    
    BMS B+ → LiPo Cell 3 (+)
    BMS BM → LiPo Cell 1-2 junction  (balance)
    BMS B2 → LiPo Cell 2-3 junction  (balance)
    BMS B- → LiPo Cell 1 (-)
    
    BQ24650 ISET: trim pot on module — set to ≤1A for 1500–2200mAh packs
    BQ24650 STAT LED: on-module LED indicates charging / standby
```

### 5b. Input UVLO

```
    BQ24650 internal UVLO: ~4.5V minimum (well below 12V operating point).
    No external voltage divider or CE-pin resistors required.
    The module ceases charging automatically when VIN drops below the internal
    threshold. No assembly action needed for UVLO.
```

### 5c. Battery Connector

```
    J_BAT (JST-XH-4P, 2.5mm pitch, or KF301-4P screw terminal)
    ┌──────────────────────────────┐
    │ Pin 1: B-  (Cell 1 negative)│
    │ Pin 2: BM  (Cell 1-2 mid)   │
    │ Pin 3: B2  (Cell 2-3 mid)   │
    │ Pin 4: B+  (Cell 3 positive)│
    └──────────────────────────────┘
```

---

## 6. ADC Divider Detail

```
    V12_PROT ── 120kΩ 1% ──┬── GPIO 1 (ADC1_CH0)
                           │
                      27kΩ 1%
                           │
                          GND
    
    Scale: V_in = V_adc × (120k + 27k) / 27k = V_adc × 5.444
    
    At 12.0V: ADC = 12.0 / 5.444 = 2.20V → raw = 2730 (of 4095)
    At 9.0V:  ADC = 9.0 / 5.444 = 1.65V → raw = 2048
    At 15.0V: ADC = 15.0 / 5.444 = 2.75V → raw = 3413
```

---

## 7. Signal Conditioning Detail

### 7a. Single Divider (repeated ×7)

```
    Encoder signal (0–5V) ── 10kΩ ──┬── 20kΩ ── GND
                                    │
                                    ├── 1nF ── GND
                                    │
                                    ├── 1.5KE3.3CA ── GND
                                    │
                                    └──→ ESP32 GPIO
```

### 7b. Encoder Connector Pinouts

**J1 — Theta Encoder (KF301-4P):**
```
    Pin 1: +5V ── FB1 ── 5V_RAIL
    Pin 2: GND ── GND
    Pin 3: A ── 10k/20k/1nF/TVS ── GPIO 4
    Pin 4: B ── 10k/20k/1nF/TVS ── GPIO 5
```

**J2 — Phi Encoder (KF301-4P):**
```
    Pin 1: +5V ── FB2 ── 5V_RAIL
    Pin 2: GND ── GND
    Pin 3: A ── 10k/20k/1nF/TVS ── GPIO 6
    Pin 4: B ── 10k/20k/1nF/TVS ── GPIO 7
```

**J3 — Wire Encoder (KF301-5P):**
```
    Pin 1: V+ ── FB3 ── 5V_RAIL
    Pin 2: GND ── GND
    Pin 3: A ── 10k/20k/1nF/TVS ── GPIO 15
    Pin 4: B ── 10k/20k/1nF/TVS ── GPIO 16
    Pin 5: Z ── 10k/20k/1nF/TVS ── GPIO 17
```

---

## 8. RS-485 Detail

```
    MAX485 (DIP-8) wiring:
    
    Pin 1 (RO) ──── GPIO 14     [RX to ESP32]
    Pin 2 (RE) ────┬── GPIO 18   [Receiver enable, active LOW]
    Pin 3 (DE) ────┘             [Driver enable, active HIGH]
    Pin 4 (DI) ──── GPIO 13     [TX from ESP32]
    Pin 5 (GND) ─── GND
    Pin 6 (A) ───── J_RS485 Pin 1
    Pin 7 (B) ───── J_RS485 Pin 2
    Pin 8 (VCC) ─── 5V_RAIL
    
    J_RS485 (KF301-3P):
    Pin 1: A
    Pin 2: B
    Pin 3: GND
    
    A──B termination: 120Ω resistor with solder jumper
```

---

## 9. I2C Bus Detail

```
    3.3V ──── 4.7kΩ ────┬── SDA (GPIO 11) ──── J_I2C Pin 1
                        │
                   1.5KE3.3CA ── GND
    
    3.3V ──── 4.7kΩ ────┬── SCL (GPIO 12) ──── J_I2C Pin 2
                        │
                   1.5KE3.3CA ── GND
    
    J_I2C (1×4 header, 2.54mm):
    Pin 1: SDA
    Pin 2: SCL
    Pin 3: 3.3V
    Pin 4: GND
```

---

## 10. Watchdog Detail

```
    MAX813L (DIP-8) wiring — CORRECT pinout (notch at top-left):
    
    ┌────────────────────┐
    │ Pin 1 GND  │ VCC  Pin 8 │
    │ Pin 2 WDO  │ RESET Pin 7 │
    │ Pin 3 MR   │ PFI  Pin 6 │
    │ Pin 4 WDI  │ PFO  Pin 5 │
    └────────────────────┘
    
    Pin 1 (GND) ─── GND
    Pin 2 (WDO) ─── NC
    Pin 3 (MR) ────┬── Reset Button ── GND
                   │
              10kΩ │
                   │
                  5V_RAIL
    Pin 4 (WDI) ─── GPIO 9
    Pin 5 (PFO) ─── NC (or to GPIO 10 if power-fail interrupt desired)
    Pin 6 (PFI) ─── 100kΩ ───┬── 5V_RAIL
                              │
                         68kΩ │
                              │
                             GND
    Pin 7 (RESET) ─┬── ESP32 EN pin
                   │
              10kΩ │
                   │
                  3.3V
    Pin 8 (VCC) ─── 5V_RAIL
```

---

## 11. LED Detail

```
    5V_RAIL ── 1kΩ ──┤>── GND    LED1 (Green, power)
    
    GPIO 8 ─── 1kΩ ──┤>── GND    LED2 (Blue, WiFi)
    GPIO 9 ─── 1kΩ ──┤>── GND    LED3 (Yellow, activity) [shared with WDI — see note]
    GPIO 10 ── 1kΩ ──┤>── GND    LED4 (Red, fault)
```

**Note:** GPIO 9 drives both WDI (to MAX813L) and LED3 (Yellow activity). This is acceptable — the LED current (<3mA) is negligible compared to MAX813L WDI input current (<1µA). The LED will blink at 20Hz (once per firmware loop) as a brief 100µs pulse — visible as a fast heartbeat.

**Alternative:** If a slower heartbeat is preferred, use a separate GPIO (e.g., GPIO 21) toggled at 2Hz.

---

## 12. Spare GPIO Header

```
    J_GPIO (1×6 header, 2.54mm):
    
    Pin 1: GPIO 21  (bidirectional)
    Pin 2: GPIO 38  (input-only)
    Pin 3: GPIO 39  (input-only)
    Pin 4: GPIO 40  (input-only)
    Pin 5: 3.3V
    Pin 6: GND
```

---

## 13. ESP32-S3-DevKitC-1 Header Connections

### Left Header (J1 on carrier, 20-pin)

```
    Carrier J1          DevKitC-1 Left Header
    Pin 1: 3.3V    ←── 3V3
    Pin 2: EN      ←── EN (from MAX813L RESET)
    Pin 3: GPIO 4  ←── GPIO 4  (Theta A)
    Pin 4: GPIO 5  ←── GPIO 5  (Theta B)
    Pin 5: GPIO 6  ←── GPIO 6  (Phi A)
    Pin 6: GPIO 7  ←── GPIO 7  (Phi B)
    Pin 7: GPIO 8  ←── GPIO 8  (LED WiFi)
    Pin 8: GPIO 9  ←── GPIO 9  (WDI + LED Activity)
    Pin 9: GPIO 10 ←── GPIO 10 (LED Fault)
    Pin 10: GPIO 11←── GPIO 11 (I2C SDA)
    Pin 11: GPIO 12←── GPIO 12 (I2C SCL)
    Pin 12: GPIO 13←── GPIO 13 (RS-485 DI/TX)
    Pin 13: GPIO 14←── GPIO 14 (RS-485 RO/RX)
    Pin 14: GPIO 15←── GPIO 15 (Wire A)
    Pin 15: GPIO 16←── GPIO 16 (Wire B)
    Pin 16: GPIO 17←── GPIO 17 (Wire Z)
    Pin 17: GPIO 18←── GPIO 18 (RS-485 DE/RE)
    Pin 18: 5V     ←── 5V
    Pin 19: GND    ←── GND
    Pin 20: GND    ←── GND
```

### Right Header (J2 on carrier, 20-pin)

```
    Carrier J2          DevKitC-1 Right Header
    Pin 1: 3.3V    ←── 3V3
    Pin 2: NC      ←── GPIO 3 (strapping, do not use)
    Pin 3: GPIO 1  ←── GPIO 1  (Battery ADC)
    Pin 4: GPIO 2  ←── GPIO 2  (LED Power / onboard LED)
    Pin 5: NC      ←── GPIO 42 (reserved)
    Pin 6: NC      ←── GPIO 41 (reserved)
    Pin 7: GPIO 40 ←── GPIO 40 (Spare GPIO 4)
    Pin 8: GPIO 39 ←── GPIO 39 (Spare GPIO 3)
    Pin 9: GPIO 38 ←── GPIO 38 (Spare GPIO 2)
    Pin 10: NC     ←── GPIO 37 (reserved)
    Pin 11: NC     ←── GPIO 36 (reserved)
    Pin 12: NC     ←── GPIO 35 (reserved)
    Pin 13: NC     ←── GPIO 34 (reserved)
    Pin 14: NC     ←── GPIO 33 (reserved)
    Pin 15: NC     ←── GPIO 26 (reserved)
    Pin 16: GPIO 21←── GPIO 21 (Spare GPIO 1)
    Pin 17: NC     ←── GPIO 20 (USB D+)
    Pin 18: NC     ←── GPIO 19 (USB D-)
    Pin 19: 5V     ←── 5V
    Pin 20: GND    ←── GND
```

---

## 14. Net Summary

| Net | Source | Destinations | Voltage |
|-----|--------|-------------|---------|
| J12V+ | DC jack | NTC → F1 → TVS → Q1 | 9–16V |
| V12_PROT | Q1 drain | D_EXT, BQ24650 VIN, ADC divider | ~12V |
| 3S_OUT+ | BMS P+ | D_BAT anode | 9.0–12.6V |
| BUCK_VIN | D_EXT/D_BAT cathodes | MP1584EN VIN, C_IN | 9.0–11.6V |
| 5V_BUCK | MP1584EN output | LC filter → SS36 | 5.05V |
| 5V_RAIL | SS36 cathode | ESP32 VIN, encoders, LEDs, MAX485, MAX813L | 4.75–4.85V |
| 3.3V | DevKitC-1 LDO | I2C pull-ups, spare GPIO | 3.25–3.35V |
| GND | Common | All components | 0V |

---

## 15. Test Points

| TP | Signal | Expected |
|----|--------|----------|
| TP12 | V12_PROT | 11.5–12.5V |
| TP_BV | BUCK_VIN | 9.0–11.6V |
| TP5 | 5V_RAIL | 4.75–4.85V |
| TP33 | 3.3V (DevKitC-1) | 3.25–3.35V |
| TP_BAT | 3S_OUT+ | 9.0–12.6V |
| TPG | GND | 0V |
| TP_EN | ESP32 EN | 3.3V (high) |

---

## 16. Assembly Warnings

1. **Pre-set MP1584EN to 5.10V** before connecting ESP32. Use 25Ω/2W dummy load.
2. **Verify BQ24650 module output** is 12.6V before connecting battery. Set ISET trim pot to ≤1A for 1500–2200mAh packs. BQ24650 modules are factory-configured for 3S but verify before first use.
3. **Verify BMS balance function** — look for small 100Ω resistors on BMS board.
4. **Double-check all Schottky diode bands** — reversed diode causes back-feed.
5. **Do NOT bolt IRF4905 to grounded heatsink** — tab is Drain (V12_PROT).
6. **Do NOT apply 12V to ESP32 VIN** — only 5V_RAIL connects to VIN pin.
7. **Check DevKitC-1 orientation** — USB connector should face board edge.
8. **Verify female header spacing** — DevKitC-1 uses standard 2.54mm, ~25.4mm between rows.
9. **Test 5V_RAIL before inserting DevKitC-1** — protect module from overvoltage.
10. **Do NOT connect active signals to GPIO 0** — strapping pin, may enter download mode.
