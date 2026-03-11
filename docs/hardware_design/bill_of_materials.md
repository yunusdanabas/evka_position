# Bill of Materials — evka_position Hardware Board

> Complete BOM for the double-sided pertinax PCB (120mm x 80mm).
> All components are through-hole unless noted.

---

## Resistors (1/4W, 1%, Metal Film, Through-Hole)

| Ref | Qty | Value | Purpose | Notes |
|-----|-----|-------|---------|-------|
| R1-R7 | 7 | 10kΩ | Voltage dividers (top resistor) | Signal line 5V→3.3V conversion |
| R8-R14 | 7 | 20kΩ | Voltage dividers (bottom resistor) | Signal line 5V→3.3V conversion |
| R15-R16 | 2 | 100kΩ | Battery ADC voltage divider | GPIO 36, draws 21μA |
| R17-R18 | 2 | 1kΩ | LED current limiters | Green (power) + Red (battery low) |
| R19 | 1 | 100kΩ | SI2301 gate pull-down | Reverse polarity protection |

**Subtotal: 19 resistors**

---

## Capacitors

| Ref | Qty | Value | Type | Purpose | Notes |
|-----|-----|-------|------|---------|-------|
| C1 | 1 | 220μF/10V | Electrolytic | 5V_RAIL bulk decoupling | Low ESR preferred |
| C2-C5 | 4 | 100nF | Ceramic (X7R) | Rail + encoder VCC decoupling | C2 at rail, C3-C5 at J1/J2/J3 |
| C6-C12 | 7 | 1nF | Ceramic (C0G/NP0) | Signal line RC filters | At divider junctions |
| C13 | 1 | 10μF/10V | Ceramic or electrolytic | MT3608 input decoupling | At VIN pad |

**Subtotal: 13 capacitors**

---

## Diodes

| Ref | Qty | Part Number | Package | Purpose | Key Specs |
|-----|-----|-------------|---------|---------|-----------|
| D1-D2 | 2 | SS34 | DO-214AB (SMA) or DO-201 | Schottky OR power switching | 3A, Vf ≈ 0.2V @ 400mA |
| D3 | 1 | 1N5817 | DO-41 (axial) | Auto-charge path (ext→TP4056) | 1A, Vf ≈ 0.45V |

**Subtotal: 3 diodes**

---

## Protection Components

| Ref | Qty | Part Number | Package | Purpose | Key Specs |
|-----|-----|-------------|---------|---------|-----------|
| TVS1-TVS7 | 7 | 1.5KE3.3CA | Axial (DO-201) | ESD protection on signal GPIOs | Bidirectional, clamp 3.3V |
| FB1-FB3 | 3 | TDK MPZ1608 or axial equiv. | Axial | EMI filter on encoder VCC | 600Ω @ 100MHz, <1Ω DC |
| Q1 | 1 | SI2301 | SOT-23 | Reverse polarity P-MOSFET | Vgs(th) -1.2V, Rds(on) 110mΩ |

**Subtotal: 11 protection components**

---

## Connectors

| Ref | Qty | Part Number | Pitch | Purpose |
|-----|-----|-------------|-------|---------|
| J1 | 1 | KF301-4P | 5.08mm | Theta encoder (E40S6 #1) |
| J2 | 1 | KF301-4P | 5.08mm | Phi encoder (E40S6 #2) |
| J3 | 1 | KF301-5P | 5.08mm | Wire encoder (DWE3000) |
| J4 | 1 | DC barrel jack 5.5×2.1mm or KF301-2P | — | External 5V power input |
| J5 | 1 | JST-PH 2-pin | 2.0mm | LiPo battery |
| J6 | 1 | KF128V-5.08-2P | 5.08mm | Direct 5V test input |
| U1 | 2 | Female header strip 1×15 or 1×19 | 2.54mm | ESP32 Wemos D1 R32 socket |

**Subtotal: 8 connector assemblies**

---

## Modules

| Ref | Qty | Module | Purpose | Notes |
|-----|-----|--------|---------|-------|
| MOD1 | 1 | TP4056 with DW01A | LiPo charger + battery protection | PROG: 1.2kΩ (1A charge) |
| MOD2 | 1 | MT3608 boost converter | 3.7V LiPo → 5.3V boost | Adjust trim pot to 5.3V |

**Subtotal: 2 modules**

---

## LEDs

| Ref | Qty | Color | Size | Purpose | Drive |
|-----|-----|-------|------|---------|-------|
| LED1 | 1 | Green | 3mm | Power indicator (5V_RAIL on) | 5V_RAIL → 1kΩ → LED → GND |
| LED2 | 1 | Red | 3mm | Battery low warning | GPIO 25 → 1kΩ → LED → GND |

**Subtotal: 2 LEDs**

---

## Mechanical / Misc

| Qty | Item | Purpose |
|-----|------|---------|
| 1 | Tactile push-button 6mm | Reset button (ESP32 RST → GND) |
| 5+ | Test point pins (gold-plated) | TP1-TP5 (5V, 3.3V, MT3608, BAT, GND) |
| 1 | Double-sided pertinax board 120×80mm | PCB substrate |
| — | 0.8mm tinned copper wire | Via links (top↔bottom layer connections) |
| — | Hook-up wire (22AWG) | Point-to-point wiring where needed |

---

## Battery

| Qty | Item | Specs | Notes |
|-----|------|-------|-------|
| 1 | 1S LiPo cell | 3.7V, 1500-2000mAh, JST-PH connector | Recommended: 1500mAh (best size/runtime balance) |

---

## Summary Count

| Category | Count |
|----------|-------|
| Resistors | 19 |
| Capacitors | 13 |
| Diodes | 3 |
| TVS diodes | 7 |
| Ferrite beads | 3 |
| MOSFET | 1 |
| Connectors | 8 assemblies |
| Modules | 2 |
| LEDs | 2 |
| Misc | ~10 items |
| **Total unique parts** | **~30 line items** |

---

## Existing / Already Owned

| Item | Status |
|------|--------|
| ESP32 Wemos D1 R32 | Already owned |
| Autonics E40S6 encoders (×2) | Already owned |
| OPKON DWE3000 draw-wire encoder | Already owned |

---

## Sourcing Notes

- **SS34 Schottky**: Common, available everywhere. DO-201 (through-hole) or SMA (surface mount — use adapter).
- **1.5KE3.3CA TVS**: Axial through-hole. If unavailable, use SMBJ3.3CA (SMD, needs adapter or dead-bug solder).
- **SI2301**: SOT-23 is SMD — dead-bug solder on pertinax, or use a small SOT-23 breakout board.
- **KF301 terminals**: Standard 5.08mm pitch PCB screw terminals, widely available.
- **TP4056 + MT3608 modules**: Pre-assembled breakout boards (~$0.50 each). Solder module headers to pertinax.
