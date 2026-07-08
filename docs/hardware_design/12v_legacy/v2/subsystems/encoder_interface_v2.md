# Encoder Interface Subsystem — V2 Design

> Signal conditioning for 3× quadrature encoders: 2× E40S6 rotary + 1× DWEM2 draw-wire.  
> Voltage dividers, RC filters, TVS protection, ferrite isolation.  
> Identical electrical design to V1 — only GPIO pin numbers changed.

---

## 1. Encoder Summary

| Encoder | Model | Channels | Supply | Output | PPR (X4) | Firmware PPR |
|---------|-------|----------|--------|--------|----------|--------------|
| Theta | E40S6-5000 | A, B | 5V | Push-Pull TTL | 20000 | `PPR_ROTARY = 20000.0` |
| Phi | E40S6-5000 | A, B | 5V | Push-Pull TTL | 20000 | `PPR_ROTARY = 20000.0` |
| Wire | DWEM2-P2000 | A, B, Z | 5V | Push-Pull TTL | 8000 | `PPR_WIRE = 8000.0` |

**Channel usage:**
- Theta: A + B (quadrature)
- Phi: A + B (quadrature)
- Wire: A + B (quadrature), Z (index pulse, future use)

---

## 2. Voltage Divider Network

### 2a. Single Channel Schematic (repeated ×7)

```
    Encoder Output (0–5V TTL push-pull)
         │
         │
    ┌────┴────┐
    │  10kΩ   │  R_top (1%, 1/4W metal film)
    │         │
    └────┬────┘
         │
         ├────────────────────── ESP32 GPIO input (sees 3.3V HIGH, 0V LOW)
         │
         │         ┌────────┐
         ├─────────┤  1nF   │  C_filter (C0G/NP0 ceramic disc, 5mm pitch)
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
    │  1.5KE3.3CA TVS      │  ESD/overvoltage protection (DO-15 axial)
    │  (bidirectional)      │
    └───────────┬──────────┘
                │
               GND
```

### 2b. Divider Math

```
    V_out = V_in × R_bot / (R_top + R_bot)
          = 5.0V × 20k / (10k + 20k) = 3.33V

    Output impedance = R_top ‖ R_bot = 10k × 20k / (10k + 20k) = 6.67kΩ

    RC time constant = 6.67kΩ × 1nF = 6.67µs
    Rise time ≈ 2.2 × RC = 14.7µs

    Max encoder frequency: ~15kHz → period = 67µs
    Signal passes cleanly (rise time << half-period = 33µs)
```

**WARNING:** Do NOT use 100nF caps. RC = 667µs → signal destroyed above ~750Hz.

**Application constraint:** This 1nF filter (f_3dB ≈ 23.9kHz) is sized for a maximum shaft speed of ~180 RPM. The E40S6-5000 encoder is rated for 5000 RPM mechanical, but at that speed the A/B signal frequency would be ~417kHz — the filter would destroy the signal. This design is correct for the slow-moving spherical scanner (≤200 RPM). Recalculate C_filter if shaft speed ever increases.

### 2c. Component Selection

| Component | Value | Spec | Package | Qty |
|-----------|-------|------|---------|-----|
| R_top | 10kΩ | 1%, 1/4W, metal film | Axial | 7 |
| R_bot | 20kΩ | 1%, 1/4W, metal film | Axial | 7 |
| C_filter | 1nF | C0G/NP0, 50V | Ceramic disc, 5mm | 7 |
| TVS | 1.5KE3.3CA | Bidirectional, 3.3V standoff | DO-15 axial | 7 |

**Why C0G/NP0?** Lowest dielectric absorption and best temperature stability. X7R acceptable but NP0 preferred for precision timing edges.

---

## 3. Complete Wiring Map

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           SIGNAL CONDITIONING SECTION                                │
│                                                                                      │
│   J1: THETA ENCODER (E40S6 #1)                                                      │
│   ┌──────────────────────┐                                                           │
│   │ Pin 1: +5V (Brown)   ├── FB1 (ferrite bead) ── 5V_RAIL ── 100nF ceramic ── GND │
│   │ Pin 2: GND  (Blue)   ├── GND                                                    │
│   │ Pin 3: Ph.A (Black)  ├── 10k ──┬── 20k ── GND ──── TVS1 ── GND                 │
│   │                      │         ├── 1nF ── GND                    → GPIO 4       │
│   │ Pin 4: Ph.B (White)  ├── 10k ──┬── 20k ── GND ──── TVS2 ── GND                 │
│   │                      │         ├── 1nF ── GND                    → GPIO 5       │
│   └──────────────────────┘                                                           │
│                                                                                      │
│   J2: PHI ENCODER (E40S6 #2)                                                        │
│   ┌──────────────────────┐                                                           │
│   │ Pin 1: +5V (Brown)   ├── FB2 (ferrite bead) ── 5V_RAIL ── 100nF ceramic ── GND │
│   │ Pin 2: GND  (Blue)   ├── GND                                                    │
│   │ Pin 3: Ph.A (Black)  ├── 10k ──┬── 20k ── GND ──── TVS3 ── GND                 │
│   │                      │         ├── 1nF ── GND                    → GPIO 6       │
│   │ Pin 4: Ph.B (White)  ├── 10k ──┬── 20k ── GND ──── TVS4 ── GND                 │
│   │                      │         ├── 1nF ── GND                    → GPIO 7       │
│   └──────────────────────┘                                                           │
│                                                                                      │
│   J3: WIRE ENCODER (DWEM2)                                                          │
│   ┌──────────────────────┐                                                           │
│   │ Pin 1: V+   (Brown)  ├── FB3 (ferrite bead) ── 5V_RAIL ── 100nF ceramic ── GND │
│   │ Pin 2: GND  (White)  ├── GND                                                    │
│   │ Pin 3: Ph.A (Yellow) ├── 10k ──┬── 20k ── GND ──── TVS5 ── GND                 │
│   │                      │         ├── 1nF ── GND                    → GPIO 15      │
│   │ Pin 4: Ph.B (Green)  ├── 10k ──┬── 20k ── GND ──── TVS6 ── GND                 │
│   │                      │         ├── 1nF ── GND                    → GPIO 16      │
│   │ Pin 5: Z    (Gray)   ├── 10k ──┬── 20k ── GND ──── TVS7 ── GND                 │
│   │                      │         ├── 1nF ── GND                    → GPIO 17      │
│   └──────────────────────┘                                                           │
│                                                                                      │
│   Shield wires: Connect to GND at board end only (single-point grounding)            │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Connector Pinouts

### J1 — Theta Encoder (KF301-4P, 5.08mm pitch)

| Pin | Signal | Wire Color | To |
|-----|--------|-----------|-----|
| 1 | +5V | Brown | 5V_RAIL via FB1 |
| 2 | GND | Blue | GND |
| 3 | Ph.A | Black | Divider → GPIO 4 |
| 4 | Ph.B | White | Divider → GPIO 5 |

### J2 — Phi Encoder (KF301-4P, 5.08mm pitch)

| Pin | Signal | Wire Color | To |
|-----|--------|-----------|-----|
| 1 | +5V | Brown | 5V_RAIL via FB2 |
| 2 | GND | Blue | GND |
| 3 | Ph.A | Black | Divider → GPIO 6 |
| 4 | Ph.B | White | Divider → GPIO 7 |

### J3 — Wire Encoder (KF301-5P, 5.08mm pitch)

| Pin | Signal | Wire Color | To |
|-----|--------|-----------|-----|
| 1 | V+ | Brown | 5V_RAIL via FB3 |
| 2 | GND | White | GND |
| 3 | Ph.A | Yellow | Divider → GPIO 15 |
| 4 | Ph.B | Green | Divider → GPIO 16 |
| 5 | Z | Gray | Divider → GPIO 17 |

---

## 5. Ferrite Beads

```
    5V_RAIL ── FB (600Ω @ 100MHz, axial) ── Encoder VCC pin
```

| Parameter | Value |
|-----------|-------|
| Impedance | 600Ω @ 100MHz |
| DC resistance | <1Ω |
| Current rating | ≥200mA |
| Package | Axial, 3.5×6mm or similar |
| Qty | 3 (one per encoder) |

**Purpose:** Blocks high-frequency switching noise from the buck converter from coupling into encoder signals. At DC, drop is <100mV @ 100mA — negligible.

---

## 6. TVS Protection

```
    Each signal GPIO line (after voltage divider junction):

    Divider junction ──┬── GPIO
                       │
                  1.5KE3.3CA
                  (bidirectional, DO-15 axial)
                       │
                      GND
```

**1.5KE3.3CA specs:**
- Standoff voltage: 3.3V (does not conduct at normal 3.3V logic)
- Breakdown: 3.5–4.0V
- Clamping: 6.5V @ 23A peak
- Power: 1500W (1ms pulse)

**Protection scenarios:**
1. **ESD discharge** when plugging/unplugging encoder cables → TVS clamps spike
2. **Encoder powered at 12V instead of 5V** → Divider would output 8V without TVS; TVS clamps to ~6.5V. **Note:** 6.5V TVS clamp protects against microsecond ESD transients only. Sustained 12V power to an encoder (5V supply) will damage GPIO inputs regardless of TVS. The TVS prevents damage from cable discharge events, not sustained wiring faults.
3. **Cable short to 12V rail** → TVS conducts, fuse/breaker should trip

---

## 7. Decoupling Capacitors

```
    At each encoder connector VCC pin:

    5V_RAIL ── FB ── VCC pin ──┬── 100nF ceramic disc ── GND
                               │
                          (encoder internal)
```

| Location | Value | Purpose |
|----------|-------|---------|
| J1 VCC | 100nF ceramic | Theta encoder local decoupling |
| J2 VCC | 100nF ceramic | Phi encoder local decoupling |
| J3 VCC | 100nF ceramic | Wire encoder local decoupling |
| 5V_RAIL junction | 220µF/16V + 100nF | System bulk decoupling |

---

## 8. Shield Grounding

**Rule:** Connect encoder cable shield to GND at the **PCB end only**. Do NOT connect shield at encoder end.

```
    Encoder cable shield ──── GND (at PCB connector pin or nearby pad)
                                    │
                                    └─── Do NOT connect at encoder housing
```

**Why single-point grounding?** Prevents ground loops. The shield acts as a Faraday cage for the cable, draining induced currents to the PCB ground plane.

---

## 9. Firmware Quadrature Configuration

### 9a. Encoder Library Pins

**Recommended library for ESP32-S3:** Use `ESP32Encoder` (PCNT-based, `madhephaestus/ESP32Encoder`) for interrupt-driven quadrature counting. PaulStoffregen's `Encoder` library requires `IRAM_ATTR` fixes on ESP32-S3 with arduino-esp32 core 2.x and uses software interrupts.

`ESP32Encoder` uses the hardware PCNT (Pulse Counter) peripheral — available on all 6 encoder GPIOs (4, 5, 6, 7, 15, 16). Up to 4 PCNT units = up to 4 encoders with zero CPU interrupt overhead.

```cpp
// Recommended: ESP32Encoder (PCNT-based)
#include <ESP32Encoder.h>

ESP32Encoder encTheta;
ESP32Encoder encPhi;
ESP32Encoder encWire;

void setup() {
    ESP32Encoder::useInternalWeakPullResistors = puType::up;
    encTheta.attachFullQuad(PIN_THETA_A, PIN_THETA_B);  // GPIO 4, 5
    encPhi.attachFullQuad(PIN_PHI_A, PIN_PHI_B);        // GPIO 6, 7
    encWire.attachFullQuad(PIN_WIRE_A, PIN_WIRE_B);     // GPIO 15, 16
}
```

**Legacy (PaulStoffregen — still works, not recommended for ESP32-S3):**
```cpp
#include <Encoder.h>

// Theta encoder
Encoder encTheta(PIN_THETA_A, PIN_THETA_B);   // GPIO 4, 5

// Phi encoder
Encoder encPhi(PIN_PHI_A, PIN_PHI_B);         // GPIO 6, 7

// Wire encoder
Encoder encWire(PIN_WIRE_A, PIN_WIRE_B);      // GPIO 15, 16
```

### 9b. GPIO Configuration

The `Encoder` library automatically configures pins as inputs with interrupts. No manual `pinMode()` needed.

**Interrupt requirements:** All GPIOs used for encoders must support `attachInterrupt()`. On ESP32-S3, **all 45 GPIOs** support interrupts — no restriction.

### 9c. Index Pulse (Wire Z)

```cpp
#define PIN_WIRE_Z 17

void setup() {
    pinMode(PIN_WIRE_Z, INPUT);
    attachInterrupt(digitalPinToInterrupt(PIN_WIRE_Z), onWireIndex, RISING);
}

void onWireIndex() {
    // Reset wire encoder count at known mechanical position
    encWire.write(0);
}
```

**Note:** Z pulse occurs once per drum revolution (every 200mm on DWEM2). Useful for homing/calibration but not required for normal operation.

---

## 10. Migration from V1

### 10a. What Changed

| Aspect | V1 | V2 |
|---|---|---|
| Theta pins | GPIO 14, 12 | **GPIO 4, 5** |
| Phi pins | GPIO 32, 35 | **GPIO 6, 7** |
| Wire pins | GPIO 16, 17, 18 | **GPIO 15, 16, 17** |
| Electrical design | Identical | **Identical** |
| Components | Identical | **Identical** |

**Only the GPIO numbers changed.** All resistors, capacitors, TVS diodes, ferrites, and connectors are the same as V1.

### 10b. Physical Wiring

When migrating from a V1 board to V2:
1. Keep the same encoder cables
2. Keep the same connectors (KF301-4P/5P)
3. **Change:** Route Theta A/B to GPIO 4/5 instead of 14/12
4. **Change:** Route Phi A/B to GPIO 6/7 instead of 32/35
5. **Change:** Route Wire A/B/Z to GPIO 15/16/17 instead of 16/17/18

---

## 11. Test Points

| TP | Signal | Location | Test Method |
|----|--------|----------|-------------|
| TP_TA | Theta A divider output | Near R_top/R_bot junction | 0–3.3V square wave when rotating |
| TP_TB | Theta B divider output | Near R_top/R_bot junction | 0–3.3V square wave, 90° phase |
| TP_PA | Phi A divider output | Near R_top/R_bot junction | Same |
| TP_PB | Phi B divider output | Near R_top/R_bot junction | Same |
| TP_WA | Wire A divider output | Near R_top/R_bot junction | Same |
| TP_WB | Wire B divider output | Near R_top/R_bot junction | Same |
| TP_WZ | Wire Z divider output | Near R_top/R_bot junction | 3.3V pulse once per rev |

**Quick validation:** Rotate each encoder by hand. All A/B signals should toggle 0–3.3V. Z should pulse once per revolution.

---

## 12. Troubleshooting

| Symptom | Cause | Check |
|---------|-------|-------|
| No counts | Encoder not powered | Check 5V at J1/J2/J3 pin 1 |
| No counts | Wrong pin mapping | Verify GPIO 4/5/6/7/15/16 in firmware |
| Erratic counts | Noisy 5V rail | Measure ripple at encoder VCC (<5mV) |
| Erratic counts | Loose GND | Check GND continuity |
| Constant 3.3V on A/B | Encoder idle or disconnected | Rotate shaft — should toggle |
| Only one channel counts | One divider open | Check both resistors and cap |
| Z never pulses | Z not connected | Check J3 pin 5 wiring |

---

## 13. Layout Notes for LPKF S63

```
    Recommended signal section layout (120mm × 40mm zone):
    
    ┌────────────────────────────────────────────────────────────┐
    │  J1 (Theta)          J2 (Phi)           J3 (Wire)          │
    │  ┌─────────┐        ┌─────────┐        ┌──────────┐        │
    │  │+ G A B  │        │+ G A B  │        │+ G A B Z │        │
    │  └──┬─┬─┬─┘        └──┬─┬─┬─┘        └──┬─┬─┬─┬─┘        │
    │     │ │ │             │ │ │             │ │ │ │          │
    │     │ │ ├──10k──┬─────┘ │ │             │ │ │ │          │
    │     │ │ │       │       │ │             │ │ │ │          │
    │     │ │ └──1nF──┤       │ │             │ │ │ │          │
    │     │ │   20k   │       │ │             │ │ │ │          │
    │     │ │    │    │       │ │             │ │ │ │          │
    │     │ └────┴────┴──TVS──┴─┴─────────────┴─┴─┴─┘          │
    │     │        │                                           │
    │     └────────┴─── GND plane ─────────────────────────────│
    │                                                          │
    │  → GPIO 4,5   → GPIO 6,7   → GPIO 15,16,17              │
    │  (to DevKitC-1 J1)                                       │
    └────────────────────────────────────────────────────────────┘
```

**Routing rules:**
- Keep divider junctions close to ESP32 header (short traces to GPIOs)
- Run GND as a continuous pour or thick trace under all dividers
- Place TVS diodes near the divider junction, not near the connector
- Keep A and B traces parallel and equal length (minimize skew)
