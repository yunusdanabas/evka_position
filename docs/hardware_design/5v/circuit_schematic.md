# Circuit Schematic — evka_position Hardware Board

> Double-sided pertinax PCB (120mm x 80mm) for Spherical 3D Positioning System.
> ESP32 Wemos D1 R32 + 3 quadrature encoders + dual power source.

---

## 1. Complete System Schematic

```
 ╔══════════════════════════════════════════════════════════════════════════════════════════╗
 ║                        evka_position — FULL CIRCUIT SCHEMATIC                           ║
 ╠══════════════════════════════════════════════════════════════════════════════════════════╣
 ║                                                                                         ║
 ║   EXTERNAL 5V PATH                          BATTERY PATH                                ║
 ║   ════════════════                          ════════════                                 ║
 ║                                                                                         ║
 ║   J4 (DC Jack / 2P)        J6 (KF128V)     USB Micro ──┐                               ║
 ║   ┌─────┐                  ┌─────┐                      │    ┌───────────────┐          ║
 ║   │+5V  │──┐               │+5V  │──┐      EXT 5V ─── 1N5817 ──┤ TP4056+DW01A  │          ║
 ║   │ GND │  │               │ GND │  │                   │    │               │          ║
 ║   └─────┘  │               └─────┘  │                   └────┤ IN+      BAT+ ├── JST ──┐║
 ║            │(parallel)              │                        │ IN-      BAT- ├── JST ──┤║
 ║            └────────┬───────────────┘                        │          OUT+ ├──┐      ││
 ║                     │                                        │          OUT- ├──┤      ││
 ║              ┌──────┴──────┐                                 └───────────────┘  │      ││
 ║              │  SI2301     │                                                    │    ┌─┴┤
 ║              │  P-MOSFET   │                                    ┌───────────┐   │    │  │
 ║              │  (RPP)      │                                    │  MT3608   │   │    │ J5
 ║              │        100k │                                    │  Boost    │   │    │LiPo
 ║              │  G ───┤├── GND                                   │  → 5.3V  │   │    │1S
 ║              └──────┬──────┘                                    │           │   │    │  │
 ║                     │                                     VIN ──┤ IN+  OUT+ ├──┐│    └─┬┤
 ║                     │                                     GND ──┤ IN-  OUT- ├──┤│      ││
 ║                D1 (SS34)                                        └───────────┘  ││      ││
 ║                ──|>──                                                          ││      ││
 ║                     │                                              D2 (SS34)   ││      ││
 ║                     │                                              ──|>──      ││      ││
 ║                     │                                                  │       ││      ││
 ║                     └──────────────────┬───────────────────────────────┘       ││      ││
 ║                                        │                                       ││      ││
 ║  ══════════════════════════ 5V_RAIL ═══╪═══════════════════════════════════════ ││      ││
 ║                                        │                                       ││      ││
 ║                               ┌────────┤                                       ││      ││
 ║                               │  220uF │  100nF                                ││      ││
 ║                               │  ═══   │  ═══                                  ││      ││
 ║                               │  GND   │  GND                                  ││      ││
 ║                               │        │                                       ││      ││
 ║  ═════════════════════════════╪════════╪═══════════════════════════════════════ ││      ││
 ║                               │        │                                       ││      ││
 ║                               │        │                                       ││      ││
 ║   BATTERY ADC                 │        │                                       ││      ││
 ║   ═══════════                 │        │              ┌─────────────────────┐  ││      ││
 ║                               │        │              │  ESP32 Wemos D1 R32 │  ││      ││
 ║   LiPo BAT+ ── 100k ──┬── 100k ── GND│              │                     │  ││      ││
 ║                        │              │              │  VIN ◄──────────────┘  ││      ││
 ║                  ESP32 GPIO 36        │              │  GND ◄── GND          ││      ││
 ║                  (ADC1_CH0)           │              │                     │  ││      ││
 ║                                        │              │  GPIO 14 ◄── DIV1 ─┐ ││      ││
 ║                                        │              │  GPIO 12 ◄── DIV2 ─┤ ││      ││
 ║                                        │              │  GPIO 32 ◄── DIV3 ─┤ ││      ││
 ║                                        │              │  GPIO 35 ◄── DIV4 ─┤ ││      ││
 ║                                        │              │  GPIO 16 ◄── DIV5 ─┤ ││      ││
 ║                                        │              │  GPIO 17 ◄── DIV6 ─┤ ││      ││
 ║                                        │              │  GPIO 18 ◄── DIV7 ─┤ ││      ││
 ║                                        │              │                     │ ││      ││
 ║                                        │              │  [USB]──────────────│─┘│      ││
 ║                                        │              └─────────────────────┘  │      ││
 ║                                        │                                       │      ││
 ║                                        └───────────────────────────────────────┘      ││
 ║                                                                                       ││
 ║   MT3608 IN ◄── TP4056 OUT+ ◄────────────────────────────────────────────────────────┘│
 ║   MT3608 GND ◄── TP4056 OUT- ◄────────────────────────────────────────────────────────┘
 ║                                                                                         ║
 ╚══════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Power Section Detail

### 2a. Reverse Polarity Protection (SI2301 P-MOSFET)

```
    External +5V ───────┬──── D (Drain)
                        │
                   ┌────┴────┐
                   │ SI2301  │  (SOT-23 P-MOSFET)
                   │ P-FET   │
                   └────┬────┘
                        │
              100kΩ ────┤──── G (Gate)
                        │
                       GND

    S (Source) ──────────── to D1 (SS34) ──── 5V_RAIL

    Operation:
    - Correct polarity: Gate pulled LOW via 100k → MOSFET ON → near-zero Vds drop
    - Reversed polarity: Gate driven HIGH → MOSFET OFF → blocks current
    - Body diode provides initial path until MOSFET fully enhances
```

### 2b. Schottky OR Auto-Switching

```
                                    5V_RAIL BUS
                                         │
    External Path:                       │           Battery Path:
    ┌─────────────┐                      │           ┌─────────────┐
    │ J4/J6 → RPP │                      │           │ MT3608 OUT  │
    │   (≈5.0V)   │                      │           │  (5.3V set) │
    └──────┬──────┘                      │           └──────┬──────┘
           │                             │                  │
      D1 (SS34)                          │             D2 (SS34)
      ──|>──                             │             ──|>──
      Vf≈0.2V                           │             Vf≈0.2V
           │                             │                  │
           └────── 4.8V ────────────────┤────── 5.1V ─────┘
                                         │
                                    ┌────┴────┐
                                    │  220uF  │  100nF
                                    │  10V    │  ceramic
                                    │  bulk   │
                                    └────┬────┘
                                        GND

    Priority: External (4.8V) < Battery (5.1V) → Battery preferred when both present
    When external disconnected → battery seamless takeover (<1ms, bulk cap hold-up)
```

### 2c. LiPo Charging Path (TP4056 + DW01A)

```
    USB Micro ─────────────────┐
                               │
    External 5V ── 1N5817 ─────┤  (auto-charge from bench supply)
                               │
                          ┌────┴────────────────┐
                          │     TP4056 Module    │
                          │  (with DW01A prot.)  │
                          │                      │
                          │  IN+          BAT+ ──┼── JST pin 1 ── LiPo (+)
                          │  IN-          BAT- ──┼── JST pin 2 ── LiPo (-)
                          │                      │
                          │  CHRG LED (red)      │  ← charging indicator
                          │  STDBY LED (green)   │  ← full indicator
                          │                      │
                          │  OUT+ ───────────────┼── MT3608 VIN
                          │  OUT- ───────────────┼── MT3608 GND
                          └─────────────────────┘

    CRITICAL: Wire MT3608 to OUT+/OUT- pads (DW01A protected),
              NOT directly to BAT+. DW01A provides:
              - Overcharge cutoff (4.2V)
              - Overdischarge cutoff (~2.5V)
              - Short-circuit protection

    PROG resistor: 1.2kΩ (default) = 1A charge current
    Safe for 1500mAh+ cells at <1C rate
```

### 2d. MT3608 Boost Converter

```
    TP4056 OUT+ ──┬── 10uF ── GND     ┌──────────────┐
                  │   (input           │   MT3608     │
                  │    decoupling)     │   Boost      │
                  └────────────────────┤ VIN    VOUT ├──── D2 (SS34) ──── 5V_RAIL
                                       │              │
    TP4056 OUT- ───────────────────────┤ GND     GND ├──── GND
                                       │              │
                                       │  [TRIM POT]  │  ← Set to 5.3V output
                                       └──────────────┘

    Verification: Connect 33Ω test resistor (~160mA) and confirm 5.0-5.3V at output.
    Efficiency: ~85-90% at 3.7V→5.3V, 400mA load.
```

---

## 3. Signal Conditioning — 7x Voltage Divider Networks

### 3a. Single Divider Schematic (repeated x7)

```
    Encoder Output (0-5V TTL)
         │
         │
    ┌────┴────┐
    │  10kΩ   │  R_top (1%, 1/4W metal film)
    │         │
    └────┬────┘
         │
         ├──────────── ESP32 GPIO input (sees 3.33V HIGH, 0V LOW)
         │
         │         ┌────────┐
         ├─────────┤  1nF   │  C_filter (C0G/NP0 ceramic)
         │         │        │
         │         └────┬───┘
         │              │
    ┌────┴────┐         │
    │  20kΩ   │  R_bot  │
    │         │  (1%,   │
    └────┬────┘  1/4W)  │
         │              │
         └──────┬───────┘
                │
    ┌───────────┴──────────┐
    │  1.5KE3.3CA TVS      │  ESD/overvoltage protection
    │  (bidirectional)      │
    └───────────┬──────────┘
                │
               GND


    MATH:
    ────────────────────────────────────────────────────────
    V_out = V_in × R_bot / (R_top + R_bot)
          = 5.0V × 20k / (10k + 20k) = 3.33V  ✓ (ESP32 max 3.6V)

    Output impedance = R_top ‖ R_bot = 10k×20k/(10k+20k) = 6.67kΩ

    RC time constant = 6.67kΩ × 1nF = 6.67μs
    Rise time ≈ 2.2 × RC = 14.7μs

    Worst-case encoder freq: ~15kHz → period = 67μs
    Signal passes cleanly (rise time << half-period)
    ────────────────────────────────────────────────────────
    WARNING: Do NOT use 100nF caps. RC = 667μs → signal destroyed at >750Hz.
```

### 3b. All 7 Divider Networks — Wiring Map

```
    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │                           SIGNAL CONDITIONING SECTION                                │
    │                                                                                     │
    │   J1: THETA ENCODER (E40S6 #1)                                                     │
    │   ┌──────────────────────┐                                                          │
    │   │ Pin 1: +5V (Brown)   ├── FB1 (ferrite) ── 5V_RAIL ── 100nF ── GND              │
    │   │ Pin 2: GND  (Blue)   ├── GND                                                   │
    │   │ Pin 3: Ph.A (Black)  ├── 10k ──┬── 20k ── GND ──── TVS1 ── GND                │
    │   │                      │         ├── 1nF ── GND                    → GPIO 14      │
    │   │ Pin 4: Ph.B (White)  ├── 10k ──┬── 20k ── GND ──── TVS2 ── GND                │
    │   │                      │         ├── 1nF ── GND                    → GPIO 12      │
    │   └──────────────────────┘                                                          │
    │                                                                                     │
    │   J2: PHI ENCODER (E40S6 #2)                                                       │
    │   ┌──────────────────────┐                                                          │
    │   │ Pin 1: +5V (Brown)   ├── FB2 (ferrite) ── 5V_RAIL ── 100nF ── GND              │
    │   │ Pin 2: GND  (Blue)   ├── GND                                                   │
    │   │ Pin 3: Ph.A (Black)  ├── 10k ──┬── 20k ── GND ──── TVS3 ── GND                │
    │   │                      │         ├── 1nF ── GND                    → GPIO 32      │
    │   │ Pin 4: Ph.B (White)  ├── 10k ──┬── 20k ── GND ──── TVS4 ── GND                │
    │   │                      │         ├── 1nF ── GND                    → GPIO 35      │
    │   └──────────────────────┘                                                          │
    │                                                                                     │
    │   J3: WIRE ENCODER (DWEM2)                                                         │
    │   ┌──────────────────────┐                                                          │
    │   │ Pin 1: V+   (Brown)  ├── FB3 (ferrite) ── 5V_RAIL ── 100nF ── GND              │
    │   │ Pin 2: GND  (White)  ├── GND                                                   │
    │   │ Pin 3: Ph.A (Yellow) ├── 10k ──┬── 20k ── GND ──── TVS5 ── GND                │
    │   │                      │         ├── 1nF ── GND                    → GPIO 16      │
    │   │ Pin 4: Ph.B (Green)  ├── 10k ──┬── 20k ── GND ──── TVS6 ── GND                │
    │   │                      │         ├── 1nF ── GND                    → GPIO 17      │
    │   │ Pin 5: Z    (Gray)   ├── 10k ──┬── 20k ── GND ──── TVS7 ── GND                │
    │   │                      │         ├── 1nF ── GND                    → GPIO 18      │
    │   └──────────────────────┘                                                          │
    │                                                                                     │
    │   Shield wires: Connect to GND at board end only (single-point grounding)           │
    └─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. ESP32 Power & Pin Connections

```
    5V_RAIL ─────────────────────────────── VIN (pin)
    GND ─────────────────────────────────── GND (pin)
                                             │
                    ┌────────────────────────┤
                    │   ESP32 Wemos D1 R32   │
                    │                        │
                    │   Onboard AMS1117-3.3  │  ← VIN→3.3V regulator
                    │   (VIN → 3.3V rail)    │     Dissipates ~0.25W (safe)
                    │                        │
                    │   GPIO 14 ◄──── DIV1 (Theta A)
                    │   GPIO 12 ◄──── DIV2 (Theta B)
                    │   GPIO 32 ◄──── DIV3 (Phi A)
                    │   GPIO 35 ◄──── DIV4 (Phi B)
                    │   GPIO 16 ◄──── DIV5 (Wire A)
                    │   GPIO 17 ◄──── DIV6 (Wire B)
                    │   GPIO 18 ◄──── DIV7 (Wire Z)
                    │   GPIO 36 ◄──── Battery ADC (input-only, ADC1_CH0)
                    │                        │
                    │   [USB Micro]          │  ← accessible for programming
                    │   (internal backfeed   │
                    │    diode present)      │
                    │                        │
                    │   RST ──── Reset Btn ── GND
                    │                        │
                    └────────────────────────┘
```

---

## 5. Battery Voltage Monitoring (ADC)

```
    LiPo BAT+ (3.0V-4.2V)
         │
    ┌────┴────┐
    │  100kΩ  │
    └────┬────┘
         │
         ├──────── GPIO 36 (ADC1_CH0, input-only)
         │
    ┌────┴────┐
    │  100kΩ  │
    └────┬────┘
         │
        GND

    At full charge (4.2V):  ADC sees 4.2 × 100k/(100k+100k) = 2.10V
    At empty      (3.0V):  ADC sees 3.0 × 100k/(100k+100k) = 1.50V
    At cutoff     (2.5V):  ADC sees 2.5 × 100k/(100k+100k) = 1.25V

    Current draw: 4.2V / 200kΩ = 21μA (negligible)
    ESP32 ADC range: 0-3.3V (12-bit, 0-4095)

    Firmware conversion:
      raw_adc = analogRead(36);
      v_batt  = (raw_adc / 4095.0) * 3.3 * 2.0;  // ×2 for divider
      pct     = map(v_batt, 3.0, 4.2, 0, 100);    // linear approx
```

---

## 6. Protection Components

### 6a. TVS Diode Placement (7x 1.5KE3.3CA)

```
    Each signal GPIO line (after voltage divider junction):

    Divider junction ──┬── GPIO
                       │
                  1.5KE3.3CA
                  (bidirectional)
                       │
                      GND

    Clamps at ±3.3V. Protects ESP32 from ESD when
    connecting/disconnecting encoder cables.
```

### 6b. Ferrite Beads (3x, 600ohm@100MHz, axial)

```
    5V_RAIL ── FB (600Ω@100MHz) ── Encoder VCC pin

    One ferrite bead per encoder VCC feed.
    Isolates high-frequency encoder switching noise from 5V rail.
    DC resistance < 1Ω (negligible voltage drop at 100mA).
```

### 6c. Indicator LEDs

```
    5V_RAIL ── 1kΩ ──┤>── GND    (Green LED — power on)

    GPIO 25 ── 1kΩ ──┤>── GND    (Red LED — battery low, firmware-driven)

    GPIO 2  ── 1kΩ ──┤>── GND    (Optional external WiFi status LED, active-high)
```

---

## 7. Decoupling Capacitor Placement

```
    ┌──────────────────────────────────────────────────────────┐
    │  DECOUPLING MAP                                          │
    │                                                          │
    │  5V_RAIL junction:    220μF/10V electrolytic             │
    │                     + 100nF ceramic (close to junction)  │
    │                                                          │
    │  J1 (Theta) VCC:     100nF ceramic (at connector)       │
    │  J2 (Phi) VCC:       100nF ceramic (at connector)       │
    │  J3 (Wire) VCC:      100nF ceramic (at connector)       │
    │                                                          │
    │  MT3608 input:        10μF/10V (at VIN pad)             │
    │                                                          │
    │  Signal dividers:     7x 1nF C0G/NP0 (at junction)     │
    │                                                          │
    │  TOTAL: 1x 220μF + 4x 100nF + 1x 10μF + 7x 1nF        │
    └──────────────────────────────────────────────────────────┘
```

---

## 8. Test Points

```
    TP1: 5V_RAIL          (verify 4.8-5.1V)
    TP2: 3.3V rail        (verify ESP32 regulator output)
    TP3: MT3608 output    (verify 5.3V before D2)
    TP4: LiPo voltage     (verify battery level)
    TP5: GND reference    (probe ground)
```

---

## 9. Net Summary Table

| Net Name | Source | Destinations | Expected Voltage |
|----------|--------|-------------|-----------------|
| 5V_RAIL | D1/D2 cathodes | ESP32 VIN, J1-J3 VCC (via ferrites), LEDs, TP1 | 4.8-5.1V |
| GND | Common | All components, all connectors | 0V |
| BAT+ | LiPo cell | TP4056 BAT+, ADC divider top | 3.0-4.2V |
| BAT- | LiPo cell | TP4056 BAT-, GND | 0V |
| MT_OUT | MT3608 VOUT | D2 anode | 5.3V |
| DIV1 | Theta A divider | GPIO 14 | 0-3.33V |
| DIV2 | Theta B divider | GPIO 12 | 0-3.33V |
| DIV3 | Phi A divider | GPIO 32 | 0-3.33V |
| DIV4 | Phi B divider | GPIO 35 | 0-3.33V |
| DIV5 | Wire A divider | GPIO 16 | 0-3.33V |
| DIV6 | Wire B divider | GPIO 17 | 0-3.33V |
| DIV7 | Wire Z divider | GPIO 18 | 0-3.33V |
| BAT_ADC | ADC divider | GPIO 36 | 1.25-2.10V |

---

## 10. Connector Pinout Quick Reference

| Connector | Type | Pins | Purpose |
|-----------|------|------|---------|
| J1 | KF301-4P | +5V, GND, A, B | Theta encoder (E40S6 #1) — GPIO 14/12 |
| J2 | KF301-4P | +5V, GND, A, B | Phi encoder (E40S6 #2) — GPIO 32/35 |
| J3 | KF301-5P | V+, GND, A, B, Z | Wire encoder (DWEM2) |
| J4 | DC barrel 5.5x2.1mm | +5V, GND | External power input |
| J5 | JST-PH 2-pin | BAT+, BAT- | LiPo battery |
| J6 | KF128V-5.08-2P | +5V, GND | Direct 5V test input |
| U1 | 2x female headers | All GPIO | ESP32 socket mount |
