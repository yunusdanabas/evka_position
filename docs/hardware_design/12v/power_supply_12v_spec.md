# 12V Power Supply — Design Specification (evka_position PCB)

This document fixes the **electrical environment**, **load budget**, and **battery specifications** for the 12V-input carrier board with 3S LiPo backup. Detailed nets and ASCII schematics live in [circuit_schematic_12v.md](circuit_schematic_12v.md).

---

## Input class (pick one for your product)

### Class A — Regulated 12V adapter / industrial 24V→12V brick (recommended default)

| Parameter | Value |
|-----------|--------|
| Nominal input | 12V DC |
| Continuous range | **9V–16V** |
| Expected transients | Limited (supply stays within range) |
| Front end | Fuse + **SMBJ18A** (or P6KE15CA) TVS + AO4407A RPP + buck |
| Buck IC/module | **28V abs max** input is sufficient (e.g. MP1584EN module) |

Use this class when the unit is powered from a **wall adapter**, a **bench supply**, or a **known-good 12V bus** (e.g. machine cabinet PSU).

### Class B — Automotive / ISO 7637-style environment

| Parameter | Value |
|-----------|--------|
| Nominal | 12V vehicle |
| Requires | **40V+** withstand buck (e.g. LM76003, TPS543620 class), **input TVS + fuse**, optional **common-mode choke**, **load dump** strategy |
| Do not | Use a bare **LM2596/MP1584** module without a qualified front-end network |

If you need Class B, treat this document as a starting point only and complete a transient study against your target standard.

---

## Load budget — 12V side (total system)

### 5V rail loads (via buck converter)

| Consumer | Typical | Peak |
|----------|---------|------|
| ESP32 + WiFi active | 160–250mA @ 3.3V (post-LDO) | ~200–350mA equivalent from 5V |
| 2× E40S6-5000 rotary encoders | ~100mA total @ 5V | 120mA |
| 1× DWE3000 draw-wire encoder | ~50mA @ 5V | 100mA |
| LEDs, GPIO loads | ~10mA | 15mA |
| **5V rail total** | **~400mA** | **~600mA** |

**Buck converter requirement:** ≥1A continuous output capability. The MP1584EN module is rated 3A — provides ample headroom.

### Charger path loads (via MT3608 boost)

| Consumer | Typical | Peak |
|----------|---------|------|
| TP5100 charge current (3S mode) | ~1A @ 12.6V (charging) | 1.5A |
| MT3608 input current at 12V→15V, 1A out | ~1.3A (η ≈ 85%) | 1.8A |

**Note:** Charging only occurs when 12V external is connected. When running on battery only, the MT3608 boost has no load.

### Total 12V input draw

| Mode | 12V input current | Power |
|------|-------------------|-------|
| Normal operation (no charging) | ~0.5A | ~6W |
| Normal + active charging | ~1.8A | ~22W |
| Battery only (no 12V) | 0A (battery supplies ~0.5A @ 11V) | — |

**Fuse sizing:** 2A fuse allows normal + charging with margin. The fuse protects the wiring harness and connector, not the modules (each module has its own current limits).

**12V adapter recommendation:** Use a **12V / 3A** (36W) adapter minimum for normal operation + charging. A 12V / 2A adapter works if charging is not time-critical (TP5100 reduces charge current when input sags).

---

## 3S LiPo battery specification

| Parameter | Value | Notes |
|-----------|-------|-------|
| Chemistry | LiPo (Lithium Polymer) | — |
| Configuration | **3S** (3 cells in series) | 3S1P recommended |
| Nominal voltage | **11.1V** (3 × 3.7V) | — |
| Full charge | **12.6V** (3 × 4.2V) | TP5100 terminates at 12.6V |
| Empty cutoff | **9.0V** (3 × 3.0V) | BMS cuts off at ~2.5–2.8V/cell |
| Recommended capacity | **1500–2200mAh** | Larger = longer backup, heavier |
| Connector | **JST-XH 4-pin** (balance + main) | Standard 3S LiPo balance lead |
| Max discharge rate | ≥2C (≥3A for 1500mAh pack) | System draws ~0.5A — any pack works |

### Battery runtime estimate

| Capacity | Runtime (approx.) | Notes |
|----------|-------------------|-------|
| 1500mAh | ~3 hours | 1500mAh / 0.5A nominal draw |
| 2200mAh | ~4.4 hours | Larger pack, more weight |

Runtime assumes WiFi active, all encoders running, no charger load.

---

## Charging specification

| Parameter | Value |
|-----------|-------|
| Charger IC | **TP5100** (module, 3S mode jumper) |
| Charge voltage | **12.6V** (CC/CV, ±1%) |
| Charge current | **~1A** (set by PROG resistor on module) |
| Charger input | **15V** from MT3608 boost |
| MT3608 input | **V12_PROT** (~12V from external supply) |
| Charge time (empty→full) | ~1.5–2.2 hours (1500–2200mAh @ 1A) |
| Trickle/termination | TP5100 tapers current when cell voltage reaches 4.2V/cell |

### Why a boost stage is needed

The TP5100 is a linear CC/CV charger. It needs **Vin > Vbat + dropout**:
- TP5100 dropout: ~0.6–1.0V (depends on charge current and temperature)
- 3S full charge: 12.6V
- Minimum Vin for full charge: **~13.6V**
- 12V adapter under load: typically **11.5–12.5V**
- **12V < 13.6V → cannot fully charge without boost**

The MT3608 boosts 12V → 15V, providing **~1.4V headroom** above the worst-case requirement. The TP5100's internal regulation ensures it never overcharges beyond 12.6V regardless of the 15V input.

### Charging behavior table

| External power | Battery state | Charger action |
|----------------|---------------|----------------|
| 12V present | Discharged (<12.6V) | MT3608 active → TP5100 CC charging at ~1A |
| 12V present | Full (12.6V) | TP5100 STDBY LED, trickle mode, minimal current |
| 12V removed | Any | MT3608 off (no input), charger inactive |
| No battery connected | N/A | TP5100 floats, no damage |

---

## Battery switchover specification

| Event | Response time | Voltage dip at 5V_RAIL |
|-------|---------------|------------------------|
| 12V disconnected | <1ms (Schottky reverse recovery + C_IN discharge) | <200mV (C_IN1 68µF holds) |
| 12V reconnected | Immediate (D_EXT forward-biases) | None (12V is higher than battery) |
| Battery empty (BMS cutoff) | Instant | System loses power — ESP32 resets |

The **C_IN1 (68µF/35V)** bulk capacitor at BUCK_VIN provides hold-up energy during the switchover transient. At 500mA load and 68µF:

```
dV = I × dt / C = 0.5A × 0.001s / 68µF = 7.4V
```

This means even a **1ms** switchover only drops BUCK_VIN by 7.4V — from 11.6V to ~4.2V. The MP1584EN operates down to 4.5V input, so this is tight. **Recommendation:** Increase C_IN1 to **100µF/35V** or **220µF/35V** if switchover glitches are observed during testing.

---

## Firmware TODO (when ready to update)

The following constants in `firmware/src/SphericalSensor.h` need updating for the 12V + 3S board:

```
ENABLE_BATTERY_MONITOR  →  1
BATT_DIVIDER_RATIO      →  5.444    (was 2.0 for 1S 100k+100k)
BATT_FULL_V             →  12.6     (was 4.2 for 1S)
BATT_EMPTY_V            →  9.0      (was 3.0 for 1S)
BATT_LOW_THRESHOLD      →  20       (was 15)
```

Do not make these changes until the hardware is built and tested.

---

## Output regulation

- **5V_RAIL**: **4.7–4.9V** at ESP32 VIN under load (5.05V buck output minus ~0.2V Schottky D_OR_BUCK)
- Do **not** feed **12V** directly to Wemos VIN; use the buck output
- Verify at **TP5** with ~200mA dummy load during bring-up

---

## Thermal considerations

| Component | Dissipation | Concern |
|-----------|-------------|---------|
| MP1584EN (12V→5V, 500mA) | ~0.3W (η ≈ 92%) | None — module handles it |
| MT3608 (12V→15V, 1A) | ~0.5W (η ≈ 85%) | Warm during charging, acceptable |
| TP5100 (15V→12.6V, 1A) | ~2.4W (linear charger!) | **Gets hot during charging** — normal, do not cover |
| AO4407A (12V, 1.5A) | <0.03W | Negligible |
| ESP32 AMS1117 (5V→3.3V, 200mA) | ~0.34W | Same as legacy — safe |
| SS34 Schottky diodes (0.3V × 1A) | ~0.3W each | Warm, acceptable |

**TP5100 is the hottest component** during active charging (~2.4W). Ensure adequate airflow around the module. Do not place other heat-sensitive components (electrolytic caps, LiPo pack) directly adjacent.

---

## Related files

- [circuit_schematic_12v.md](circuit_schematic_12v.md) — full schematic narrative + ASCII diagrams
- [bill_of_materials_12v.md](bill_of_materials_12v.md) — parts list with example MPNs
- [pcb_layout_guide_12v.md](pcb_layout_guide_12v.md) — layout notes + assembly sequence
- KiCad project: [kicad/README.md](kicad/README.md)
- [README.md](README.md) — index of this folder
