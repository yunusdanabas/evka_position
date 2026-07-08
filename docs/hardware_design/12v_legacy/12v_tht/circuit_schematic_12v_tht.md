# Circuit Schematic — evka_position 12V Input PCB (All-THT)

> **All through-hole variant** of [circuit_schematic_12v.md](../12v/circuit_schematic_12v.md).  
> The circuit topology is **identical** — this document covers only the **package-level changes** that affect physical wiring.  
> For the full system block diagram, Schottky OR logic, buck converter, charger/BMS, ADC divider, and signal section, refer to the [SMD schematic](../12v/circuit_schematic_12v.md).

---

## 1. Summary of package changes

| Section | Component | SMD Version | THT Version | Schematic impact |
|---------|-----------|-------------|-------------|------------------|
| 2c (RPP) | Q1 | AO4407A (SOIC-8) | **IRF4905 (TO-220AB)** | Different pinout — see section 2 below |
| 2b (TVS) | TVS_IN | SMBJ18A (SMB) | **P6KE18A (DO-15 axial)** | Drop-in, polarity band = cathode |
| 3 (Schottky OR) | D_EXT, D_BAT | SS34 (SMA) | **SS34 / 1N5822 (DO-201 axial)** | Drop-in, band = cathode |
| 5 (5V OR) | D_OR_BUCK, D_OR_USB | SS34 (SMA) | **SS34 / 1N5822 (DO-201 axial)** | Drop-in, band = cathode |
| 4 (Buck caps) | C_IN2, C_OUT2 | 100nF (0805) | **100nF ceramic disc (THT)** | Drop-in |
| 4 (ESP32 decap) | C_VIN_ESP | 10µF (0805) | **10µF electrolytic (THT)** | Observe polarity |

Sections **1** (block diagram), **3** (Schottky OR), **4** (buck converter), **5** (5V OR), **6** (charger/BMS), **7** (ADC divider), **8** (signal section), **9** (net summary), **10** (test points), and **11** (warnings) are **unchanged** — use the [SMD schematic](../12v/circuit_schematic_12v.md) directly.

---

## 2. Reverse polarity protection — IRF4905 (TO-220AB)

This replaces section **2c** of the SMD schematic. The circuit function is identical; only the physical package and pinout differ.

### IRF4905 TO-220AB pinout

```
    Facing the marked side (text readable), leads pointing down:

    ┌─────────────────────────┐
    │                         │
    │       IRF4905           │
    │     P-ch MOSFET         │
    │                         │
    │   ┌─────────────────┐   │
    │   │   Metal Tab      │   │  ← Tab is connected to DRAIN
    │   │   (= Drain)      │   │
    └───┴──┬────┬────┬─────┘───┘
           │    │    │
          (1)  (2)  (3)
           G    D    S
         Gate Drain Source
```

**Pin 1 = Gate, Pin 2 = Drain, Pin 3 = Source, Tab = Drain**

### RPP wiring (high-side P-FET)

```
    F1/TVS output ──────────────── Pin 3 (Source)
                                     │
                                ┌────┴────────────┐
                                │    IRF4905       │
                                │   TO-220AB       │
                                │  P-ch MOSFET     │
                                │  Vds = -55V      │
                                │  Rds(on) = 20mΩ  │
                                └────┬────────────┘
                                     │
                          100kΩ ─────┤ Pin 1 (Gate)
                                     │
                                    GND

                           Pin 2 (Drain) ──── V12_PROT (protected 12V rail)

    Operation:
    - Correct polarity: Gate LOW (100k pull-down to GND)
      → Vgs = 0V − 12V = −12V → MOSFET fully ON
      → Rds(on) = 20mΩ @ Vgs = −10V
      → Voltage drop = 20mΩ × 1.5A = 30mV (negligible)
    - Reversed polarity: Source goes negative, Gate pulled to GND
      → Vgs ≈ 0V (relative to source) → MOSFET OFF → blocks current
    - IRF4905 abs max: Vgs = ±20V, Vds = −55V → safe at 12V with headroom
```

### Comparison vs AO4407A

| Parameter | AO4407A (SOIC-8) | IRF4905 (TO-220AB) |
|-----------|-------------------|---------------------|
| Vds | −30V | −55V |
| Rds(on) @ Vgs = −10V | 12mΩ | 20mΩ |
| Id (continuous) | −12A | −74A |
| Vgs(th) | −1.0V (typ) | −2.0V to −4.0V |
| Power dissipation @ 1.5A | 27mW | 45mW |
| Package | SOIC-8 (SMD) | TO-220AB (THT) |
| Heatsink needed? | No | No |

The IRF4905 has slightly higher Rds(on) (20mΩ vs 12mΩ), resulting in 30mV drop instead of 18mV at 1.5A — **negligible** difference. The higher Vds rating (55V vs 30V) provides additional headroom for transients.

**Note on Vgs(th):** The IRF4905 threshold is −2.0V to −4.0V (higher than AO4407A's −1.0V). At Vgs = −12V (normal operation with 12V input), the MOSFET is fully enhanced — no issue. At lower input voltages (e.g., 9V from battery through reverse path), Vgs = −9V is still well above threshold.

### Alternative: Schottky RPP (simpler)

Same as the SMD version — a series **SS36 Schottky** (3A, 60V, DO-201 axial) from F1 output to V12_PROT. Drop ~0.35V at 1.5A. Omit Q1 and R_G. The SS36 in DO-201 is naturally THT.

---

## 3. Axial diode orientation guide

All Schottky and TVS diodes in this version use **axial through-hole packages** (DO-201 or DO-15). Orient by the **cathode band** (painted stripe near one lead):

```
    Schottky diode (SS34 / 1N5822 in DO-201):

         Anode ──────┤ │──────── Cathode
                      ▓            (band)
                   DO-201 body

    In Schottky OR circuits, cathodes join at the output node:

        V12_PROT ── Anode ─┤ │─ Cathode (band) ──┬── BUCK_VIN
                                                   │
        3S_OUT+  ── Anode ─┤ │─ Cathode (band) ──┘

    TVS diode (P6KE18A in DO-15):

         ────────┤ ├──────── (band = cathode for unidirectional)
              DO-15 body

    For unidirectional TVS_IN: cathode (band) toward the 12V rail, anode to GND.
```

---

## 4. Encoder + ESP32 signal section (unchanged)

Copy **verbatim** from [circuit_schematic.md](../5v/circuit_schematic.md):

- **Section 3** — voltage dividers **10k / 20k / 1nF** + **1.5KE3.3CA** (axial, already THT)
- **Section 3b** — **J1 / J2 / J3** pin map to **GPIO 14, 12, 32, 35, 16, 17, 18**
- **Sections 4–7** — ESP32 **VIN** from **5V_RAIL**, ferrites, LEDs, decoupling

All signal section components are already through-hole in the original 5V design. No changes needed.

---

## 5. Important warnings

Same as [SMD schematic section 11](../12v/circuit_schematic_12v.md#11-important-warnings), plus:

1. **IRF4905 TO-220 orientation:** Pin 1 (Gate) is on the left when facing the marked side. Verify with datasheet before soldering — reversed Gate/Source will leave V12_PROT floating.
2. **TO-220 tab is Drain:** The metal tab connects to Pin 2 (Drain) = V12_PROT. If the tab contacts GND (e.g., a mounting screw to ground plane), it will short V12_PROT to GND. **Do not bolt Q1 to a grounded heatsink.** No heatsink is needed at 45mW.
3. **DO-201 cathode band orientation:** Double-check all 4–5 Schottky diodes and TVS_IN. A reversed Schottky in the OR circuit will back-feed current between sources.
