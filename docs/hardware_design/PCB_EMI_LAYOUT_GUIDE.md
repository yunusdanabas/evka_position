# PCB Layout Best Practices: Encoder Signal Conditioning + Switching Buck Converter

> Comprehensive guide for co-locating high-speed digital signals (encoder quadrature, Z-index) with SMPS buck/boost converters on the same PCB while maintaining signal integrity and minimizing EMI.

---

## 1. Executive Summary: Key Principles

### Golden Rules
1. **Spatial separation**: SMPS switching node physically distant from analog signal paths (~60-100mm minimum on small boards)
2. **Ground plane partitioning**: Separate analog and power ground planes, unified at single low-impedance star point only
3. **Trace routing hierarchy**: Power → Ground → Analog signals → Digital signals (in priority order)
4. **Ferrite + filter**: Series ferrite bead + 100nF cap on EVERY encoder VCC input
5. **Shield grounding**: Encoder cable shields **single-point** grounded at board entry, NOT floating

---

## 2. Ground Plane Strategy (CRITICAL for EMI Control)

### 2.1 Two-Layer Board Ground Architecture

**Scenario**: 120mm × 80mm double-sided pertinax (like evka_position)

```
┌─────────────────────────────────────────────────────┐
│ TOP LAYER                                           │
│                                                      │
│  [SMPS Zone]   [ENCODER ZONE]   [MCU ZONE]         │
│   Switching    Signal cond.     GPIO interface      │
│   nodes        with ferrites     and decoupling      │
│   adjacent to  away from         near ESP32          │
│   coils        SMPS             VIN & GND           │
│                                                      │
│  Traces: power (thick) > signals (medium) >LED(thin)│
│                                                      │
└─────────────────────────────────────────────────────┘
         │                    │                │
         │ Vias (wide GND)   │ Vias (wide GND)│ Vias (wide GND)
         │ every 10-15mm     │ every 15-20mm  │ every 10-15mm
         ↓                   ↓                ↓
┌─────────────────────────────────────────────────────┐
│ BOTTOM LAYER (GROUND PLANE - PRIMARY CURRENT RETURN)
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │                                               │   │
│  │  SOLID GND fill with vias connecting top     │   │
│  │  traces. Wide traces (3-5mm) for:            │   │
│  │                                               │   │
│  │  • SMPS ground (from MT3608 GND pads)        │   │
│  │  • Encoder connector grounds (J1-J3 GND)     │   │
│  │  • ESP32 GND (from U1 header)                │   │
│  │  • Power section GND (Q1, D1, D2)            │   │
│  │                                               │   │
│  │  All converge to STAR POINT near C1 bulk cap │   │
│  │                                               │   │
│  └──────────────────────────────────────────────┘   │
│                     ↓                               │
│               STAR POINT (0V reference)             │
│               at C1 (220μF) junction                │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 2.2 Star Point Design

**Location**: Bottom layer, centered near C1 (220μF bulk capacitor)

```
From top layer, create 4-5 wide (3-5mm) ground bus traces
converging radially to the star point:

          SMPS Ground ─┐
                       ├─ STAR POINT
    Encoder Ground ─┤  (0V reference)
                       ├─ [C1 GND Pad]
       ESP32 Ground ─┤
                       └─ Power section return
      Signal GND ─┐
```

**Why this works:**
- Single point eliminates ground loops
- Large contact area at star point reduces loop inductance
- Wide radial traces (3-5mm) minimize voltage drops (~10mΩ at 1A)
- Encoder signals "see" consistent 0V reference everywhere

### 2.3 Avoid Ground Plane Splits (Common Mistake #1)

❌ **BAD**: Partitioned ground planes with small coupling area
```
                │ GAP or small coupling area
    ┌──────────┼──────────┐
    │ SMPS GND │ SIGNAL GND│
    │  plane   │  plane    │ ← Currents must pass through few vias
    └──────────┼──────────┘
         ↓
    High ground impedance → encoder noise coupling
```

✅ **GOOD**: Unified ground plane with strategic separation of high-current paths
```
    ┌──────────────────────────────────┐
    │   SINGLE GROUND PLANE             │
    │   (entire bottom layer copper)    │
    │                                   │
    │   ┌─────────────────────────────┐ │
    │   │ Use wide traces (3-5mm)      │ │
    │   │ to separate high-current     │ │
    │   │ SMPS return from sensitive   │ │
    │   │ signal return paths          │ │
    │   │ (not plane islands)          │ │
    │   └─────────────────────────────┘ │
    └──────────────────────────────────┘
         ↓
    Unified return, reduced noise coupling
```

---

## 3. Switching Node Isolation

### 3.1 SMPS Switching Node Location (MT3608 Boost Example)

**Switching node**: High-frequency (500kHz typical) current path between MOSFET and inductor.

```
Safe zone for SMPS:

┌────────────────────────────────────────────────────────────┐
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ [SMPS ZONE — Top Left Corner]                       │  │
│  │                                                     │  │
│  │  TP4056 OUT+ ── C13 (10μF) ── MT3608 VIN          │  │
│  │                                 │                  │  │
│  │                            Switching node          │  │
│  │                            (high dI/dt current)    │  │
│  │                            ↓                       │  │
│  │                            [Inductor coil]         │  │
│  │                            (keep away from signals)│  │
│  │                                 │                  │  │
│  │  GND ──────────────── MT3608 GND ──── D2 anode    │  │
│  │                                                     │  │
│  │  Distance from encoder J1-J3: ≥ 60mm              │  │
│  │  ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ [ENCODER ZONE — Bottom Left]                        │  │
│  │                                                     │  │
│  │  J1 (Wire)  ── FB1 ── 100nF ── dividers          │  │
│  │  J2 (Phi)   ── FB2 ── 100nF ── dividers          │  │
│  │  J3 (Theta) ── FB3 ── 100nF ── dividers          │  │
│  │                                                     │  │
│  │  Traces routed AROUND SMPS zone (right side)      │  │
│  │  ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾              │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 3.2 Minimum Separation Distances

| Component Pair | Min. Distance | Reason |
|---|---|---|
| SMPS switching node ↔ encoder A/B signals | 60-100mm | Minimize magnetic coupling |
| MT3608 inductor ↔ signal dividers | 50mm | Radiated EMI from L di/dt |
| SMPS GND return ↔ encoder signal GND | 40mm (separate traces) | Avoid common impedance |
| MOSFET drain ↔ shielded encoder cable | 30-50mm | Precaution against dV/dt noise |

### 3.3 Inductor Orientation & Placement

```
DO:
  ✓ Place inductor coil centered in SMPS zone
  ✓ Orient coil axis perpendicular to signal traces
  ✓ Wrap a grounded Faraday cage (thin Cu mesh or shield can) around inductor
    if space permits (not mandatory for small boards)

DON'T:
  ✗ Place inductor adjacent to encoder input connectors
  ✗ Route signal traces directly above/below inductor
  ✗ Orient coil axis parallel to encoder cables
```

---

## 4. Signal Trace Routing Best Practices

### 4.1 Trace Separation Matrix

```
Signal Type              Min. Gap    Layer Rule          Notes
─────────────────────────────────────────────────────────────────────
Encoder Phase A/B        0.5mm       Same side (top)     Adjacent traces OK if diff-pair routed
Encoder Z-index          0.5mm       Same side (top)     Separate from Phase A/B by gap
5V_RAIL (power)          1.5mm       Mixed layers        Top layer thick (2mm), keep away from signals
GND traces (return)      1.0mm       Bottom (primary)    Wide traces (3-5mm) converge to star point
ESP32 GPIO (input)       0.5mm       Top layer           Short, direct routes from divider junctions
```

### 4.2 Router Order (Implement in this sequence)

**Priority 1 — Power (highest impedance critical)**
1. 5V_RAIL from D1/D2 junction → C1 bulk cap location (2mm trace, top layer)
2. 5V_RAIL branch to each zone load (1-1.5mm branches)
3. Ferrite bead + 100nF cap at each encoder VCC input

**Priority 2 — Ground (lowest impedance critical)**
1. Bottom layer: wide (3-5mm) GND traces from all sections → star point
2. Vias (0.8-1.0mm) placed every 10-15mm along power GND traces
3. Encoder connector GND pins → bottom-layer wide trace → star point

**Priority 3 — Analog signals (sensitive)**
1. Divider output junctions → ESP32 GPIO inputs (0.5mm traces, top layer)
2. Signal traces routed on OPPOSITE SIDE of board from SMPS switching node
3. Every signal trace has dedicated return path via bottom-layer GND (use vias at ends)

**Priority 4 — Digital / Low-critical**
1. LED, button, test points (route last)

### 4.3 Trace Routing Topology for Encoder Signals

```
Incoming encoder signal (5V TTL):
           ↓
    [J1/J2/J3 connector] — single-point GND shield
           ↓ (parallel traces, 0.5mm spacing minimum)
           │
      ┌────┴────┐
      │  Ferrite bead (600Ω@100MHz)
      │  + 100nF decap
      └────┬────┘
           │
      [Voltage Divider] ← R_top (10k) ├─ R_bot (20k) ├─ GND
           │                           │
      [1nF filter cap]  ────────────────┤
           │                           │
      [TVS diode (1.5KE3.3CA)] ─────────┼─ GND
           │
      [ESP32 GPIO input] ← direct trace, 0.5mm width, 40-60mm length

VIA STRATEGY:
  • Via near divider junction → GND (top of divider network)
  • Via near TVS cathode → GND (return path for protection)
  • Via near GPIO pin → GND (reference for input signal)
  → Each via placed 5-10mm from its component, converges to GND plane
```

---

## 5. Ferrite Bead + Filter Configuration

### 5.1 Encoder VCC Input Filter (CRITICAL for EMI mitigation)

```
5V_RAIL ──┬── Ferrite bead ──┬── 100nF cap ──┬── GND
          │  (600Ω@100MHz)   │  (ceramic)     │
          │  (0.1Ω DC)       │  (Y5V or X7R)  │
          │  [AXE-FB603-600] │                │
          │                  │                │
          └──────────────────┼── VCC pin (J1/J2/J3)
                             │
                        Encoder supply,
                        decoupled from SMPS noise
```

### 5.2 Why Ferrite + Filter Works

| Component | Purpose | Specifications |
|---|---|---|
| **Ferrite bead** | High-Z path for switching noise (500kHz+), low-Z for DC/slow transients | 600Ω @ 100MHz, <0.1Ω DC resistance |
| **100nF ceramic** | Local charge reservoir, C0G/NP0 dielectric (stable, no aging) | 100nF ± 10%, rated ≥10V |

**Impedance curve** (ferrite bead):
```
Z (Ω)
│
│  ┌────┐
│  │    └────┐
│  │         │
│  │         └─────────────
│  │
└──┴──────────────────────── f (Hz)
   DC    100Hz  1kHz  100kHz  500kHz
   
   Low-impedance   →   Medium Z  →   High-impedance
   for DC power        for mid-freq   for SMPS noise
```

### 5.3 Placement Rules

```
TOP LAYER:

5V_RAIL ── [FB bead] ──── [100nF cap] ──┬── Encoder VCC pin
           ↑               ↑              │
       Compact layout   Close to connector
       (within 5mm)                      
                                         ↓ [Encoder module]

BOTTOM LAYER:

GND ─────────────────────── [100nF cap GND] ──┬── Encoder GND pin
                            │                  │
                         VIA to star point  VIA to connector

Result: Encoder sees clean 5V supply, decoupled from SMPS transients.
```

---

## 6. Digital Signal Routing Near SMPS

### 6.1 Separation Strategy: "Fast Side vs. Noisy Side"

```
BOARD LAYOUT PARTITION:

┌────────────────────────────────────┐  120mm
│                                    │
│  ┌──────────────────────────────┐  │
│  │ SMPS Zone (Top-Left)         │  │  80mm
│  │ • MT3608 module              │  │
│  │ • Switching node area        │  │
│  │ • Inductor coil              │  │
│  │ • High dI/dt currents        │  │
│  └──────────────────────────────┘  │
│                                    │
│  ↕ [QUIET CORRIDOR — 40mm buffer] ↕
│                                    │
│  ┌──────────────────────────────┐  │
│  │ SIGNAL + MCU Zone (Bottom)    │  │
│  │ • Encoder connectors J1-J3    │  │
│  │ • Voltage dividers            │  │
│  │ • ESP32 GPIO pins             │  │
│  │ • Low noise digital signals   │  │
│  └──────────────────────────────┘  │
│                                    │
└────────────────────────────────────┘
```

### 6.2 Trace Routing Rules in Signal Zone

**When encoder signals MUST pass near SMPS:**

1. **Minimum clearance**: 30-40mm from SMPS switching node
2. **Trace width**: Keep signal traces narrow (0.5mm) to reduce loop area
3. **Layer preference**: Route signals on TOP layer (farther from GND plane below)
4. **Via placement**: Use vias ONLY where absolutely necessary (at component pads)
5. **Ground fill**: Ensure continuous GND plane on BOTTOM layer under signal zone

### 6.3 Differential-Pair Routing (Optional Improvement)

For encoder signals in electrically noisy environments, consider differential pairing:

```
NOT recommended for simple 3-encoder system, but if needed:

Standard routing:
  Ph.A ────┬──────── GPIO
           │ 0.5mm gap
  Ph.B ────┴──────── GPIO

Differential routing (future-proof):
  Ph.A ────┬──────── GPIO   ← routed as twisted pair with ground
           │ 0.2mm gap      ← matched length, opposite edges
  Ph.B ────┴──────── GPIO   ← common-mode noise cancellation

Length matching: |A - B| < 5% of shortest signal wavelength
(not critical for ≤15kHz encoder signals)
```

---

## 7. EMI Shielding Strategies

### 7.1 Encoder Cable Shielding (Primary Defense)

```
SHIELDED ENCODER CABLE:
┌─────────────────────────────────┐
│ 4-conductor twisted pair        │
│ (Phase A, Phase B, Power, GND)  │
│ ─────────────────────────────   │
│ with outer Cu mesh shield       │
│ (spiral wrap or braided)        │
└─────────────────────────────────┘
        ↓
   Encoder connector
        │
        J1/J2/J3
        │
        ├─ Shield wire (connect to PCB GND AT CONNECTOR ONLY)
        ├─ Power (5V)
        ├─ GND
        ├─ Phase A signal → divider network
        └─ Phase B signal → divider network
```

**Critical rule**: Shield terminates at ONE point (board entry). 
**Never** float the shield or connect it to signal GND intermediate points.

```
CORRECT:

    ┌─────────────────┐
    │ Encoder module  │
    │ (remote site)   │
    └────────┬────────┘
             │ shielded cable (30ft max)
             │ ┌─ Ph.A
             │ ├─ Ph.B
             │ ├─ +5V
             │ ├─ GND
             │ └─ Shield
             ↓
        J1 connector
        │
        ├─ Ph.A ──→ divider ──→ GPIO
        │
        ├─ Ph.B ──→ divider ──→ GPIO
        │
        ├─ +5V ──→ ferrite ──→ 5V_RAIL
        │
        ├─ GND ──→ [BOARD GND PLANE]
        │
        └─ Shield ──→ [BOARD GND PLANE, SAME POINT as GND pin]
                      (single-point termination)
```

**WRONG** (floating or multi-point shield grounding):
```
❌ Shield floats → acts as antenna, picks up SMPS noise
❌ Shield connected to signal ground (different from power GND) → ground loop
❌ Shield connected at multiple points → ground loop currents add noise
```

### 7.2 PCB-Level Shielding (Advanced)

**If encoder signals are routed over long distances on PCB:**

```
OPTION A: Guard traces
  
  Signal trace ──→ [Sensitive divider area]
  Guard trace (GND) ┤ parallel on both sides, 1mm gap
  Guard trace (GND) ┤

OPTION B: Faraday cage (small shielded chamber)

  ┌──────────────────────┐
  │ Cu box (0.2mm wall)  │
  │                      │
  │  ┌────────────────┐  │
  │  │  Divider       │  │
  │  │  networks x3   │  │
  │  └────────────────┘  │
  │                      │
  │  (connected to GND)  │
  └──────────────────────┘
  
  → Not practical on hand-soldered board; skip for evka_position.
```

### 7.3 EMI from Switching Node

**Problem**: MT3608 switching node (500kHz, 1-2A transients) radiates high-frequency noise.

```
┌─────────────────────────────────────────────────────────┐
│ SWITCHING NODE NOISE COUPLING PATH                      │
│                                                         │
│  MT3608 MOSFET switching ─┐                            │
│  (500kHz, ~1A di/dt)       │                            │
│                           ├─→ Magnetic field            │
│  ↓                        │    (spreads ~50-100mm)      │
│                           │                            │
│  Nearby signal traces ◄────┘    (capacitive + inductive)│
│  (encoder divider A/B)                                 │
│  ↓                                                      │
│  Induced noise: 100-500mV spikes at 500kHz              │
│  (can corrupt slow encoder signals!)                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Mitigation**:
1. **Distance** (primary): Place SMPS zone 60-100mm from encoder zone
2. **Ferrite + filter** on encoder VCC (prevents noise coupling via power rail)
3. **1nF filter cap** on signal divider (RC corner at ~25kHz attenuates 500kHz noise)
4. **TVS diode** clamps any transients that sneak through

---

## 8. Capacitor Placement & Decoupling

### 8.1 Bulk Capacitor at Star Point

```
┌─ 5V_RAIL (from D1/D2)
│
├─ C1 (220μF, 10V, electrolytic)
│  └─ GND ─────→ [STAR POINT on bottom layer]
│
├─ C2 (100nF, ceramic, C0G/X7R) ─ placed within 2cm of C1
│  └─ GND ─────→ [STAR POINT]

PLACEMENT (top layer):
  Near junction of J4/J6 (external power input area)
  or MT3608 output area (battery power)
  
  C1 & C2 share same GND via → star point
  Minimizes loop inductance.
```

### 8.2 Encoder VCC Decoupling

```
Per encoder (x3 total: J1, J2, J3):

5V_RAIL ── Ferrite ── [100nF] ── VCC pin
                        │
                       GND via (short, <5mm trace) → bottom GND plane

Placement: Capacitor mounted AT CONNECTOR, not remote.
```

### 8.3 Signal Divider Decoupling (1nF Filter Caps)

```
Per divider network (x7 total):

  10kΩ (R_top)
     │
     ├── [1nF, C0G/NP0] ── GND
     │
  20kΩ (R_bot)
     │
    GND

Placement: 1nF cap soldered directly at divider junction,
           1mm trace to GND via.

Purpose: Attenuate 500kHz SMPS noise, allow encoder signals
         (max 15kHz) to pass cleanly.
```

### 8.4 MT3608 Input Decoupling

```
TP4056 OUT+ ── [10μF, 10V] ── MT3608 VIN
              │ (electrolytic)
             GND
             
Placement: At MT3608 input pad (close), GND via to bottom plane.
Purpose: Stabilize boost converter input, prevent voltage spikes.
```

---

## 9. Layer Stack & Via Strategy

### 9.1 Via Placement Checklist

| Location | Via Size | Spacing | Purpose |
|---|---|---|---|
| Power GND traces (bottom) | 0.8-1.0mm | Every 10-15mm | Low-impedance ground return |
| Signal divider GND | 0.8mm | At component pad | Minimize loop area |
| TVS diode GND | 0.8mm | Adjacent | Direct path to plane |
| Encoder connector GND | 1.0mm | At pad | Primary ground entry |
| Decap GND (100nF, 1nF) | 0.8mm | Directly under pad | Short return path |

### 9.2 Thermal Vias (Optional)

**If SI2301 P-MOSFET dissipates significant power** (unlikely in RPP circuit):

```
SI2301 GND pad (SOT-23) ── 2-4 vias (0.8mm) → bottom GND plane
                           (spread around pad)
                           
Dissipation: ~0.25W max (5V × 50mA at low Vds) → negligible heat.
Thermal vias: Not required, but good practice if space available.
```

---

## 10. Practical Assembly Sequence for Co-Located SMPS + Encoders

### Phase 1: Power Section & SMPS
1. Solder D1 (SS34) and Q1 (SI2301) with short leads to C1/C2 GND star point
2. Mount MT3608 module, TP4056 module
3. Create bottom-layer GND traces from all power components → star point
4. Verify 5V_RAIL: ~5.0-5.1V at TP1

### Phase 2: Encoder VCC Filters
1. Solder ferrite bead (FB1, FB2, FB3) on encoder VCC paths
2. Solder 100nF decap immediately after each ferrite (at connector area)
3. Route VCC traces to connector pads (short, wide if possible)

### Phase 3: Signal Conditioning
1. Solder J1, J2, J3 connectors
2. Solder voltage divider networks (10k/20k resistors, 1nF caps)
3. Solder TVS diodes (1.5KE3.3CA)
4. Route signal traces to ESP32 GPIO pins (long, thin, far from SMPS)

### Phase 4: MCU & Testing
1. Solder ESP32 female header strips
2. Connect 5V_RAIL and GND to ESP32 VIN/GND
3. Program ESP32, test each encoder individually
4. Verify no noise on encoder signals (use oscilloscope if available)

### Test Checkpoint: Noise Measurement

```
Setup:
  • Oscilloscope probe on encoder signal divider output (before GPIO)
  • SMPS under load (e.g., 5V rail driving LEDs or test resistor)
  • Encoder rotating or static

Expected:
  ✓ Clean digital waveform, 0-3.3V
  ✓ Rise time <50μs
  ✓ No visible high-frequency ripple (>100mV spikes = problem)
  
If noisy:
  1. Check ferrite bead is soldered (not loose)
  2. Verify 100nF cap is close to connector
  3. Increase distance between SMPS and signal zone (if physically possible)
  4. Re-solder GND vias near encoder zone
```

---

## 11. Common Mistakes & Fixes

### Mistake #1: Partitioned Ground Planes

❌ **Problem**: Separate "analog" and "digital" ground planes with only small coupling area.
```
    ┌─────────────┬─────────────┐
    │ SMPS GND    │ SIGNAL GND  │
    │  plane      │  plane      │
    └─────────────┴─────────────┘
           ↑ narrow coupling (2-3 vias)
    
    Result: High ground impedance → noise injection into encoder signals
```

✅ **Fix**: Single unified ground plane with wide separation traces
```
    ┌─────────────────────────────┐
    │  SINGLE GND PLANE           │
    │                             │
    │ ┌───────┐      ┌─────────┐  │
    │ │ GND   │ wide │ GND     │  │
    │ │return │ trace│ return  │  │
    │ │SMPS   │──    │SIGNAL   │  │
    │ └───────┘      └─────────┘  │
    │        ↓                     │
    │    STAR POINT               │
    └─────────────────────────────┘
    
    Result: Low impedance, noise confinement via trace resistance
```

### Mistake #2: Long Signal Traces with No Ground Return

❌ **Problem**: Encoder A/B signals routed far from GND layer/traces; loop area → pick up SMPS radiation
```
    Signal trace ──────────── [60mm] ──────────── GPIO
    
    GND return (bottom layer) ══ far away ════════ GPIO GND

    Result: Large loop area (60mm × 2mm height = 120mm²)
            Inductance ~10-50nH → induced noise
```

✅ **Fix**: Via placed near GPIO input; short ground return
```
    Signal trace ──────────── [20mm] ──→ GPIO
    GND return via        ─────────────→ GND plane
    (5mm from signal trace, tightly coupled)
    
    Result: Small loop area (<50mm²) → minimal noise pickup
```

### Mistake #3: Floating Encoder Cable Shield

❌ **Problem**: Shield wire not connected, or connected to wrong GND point
```
    Shielded encoder cable
    ├─ Ph.A → divider
    ├─ Ph.B → divider
    ├─ +5V → ferrite
    ├─ GND → board GND
    └─ Shield → FLOATING (not connected!)
    
    Result: Shield acts as antenna, couples SMPS noise into signal wires
```

✅ **Fix**: Shield grounded at board entry, same point as GND pin
```
    Shielded encoder cable
    ├─ Ph.A → divider
    ├─ Ph.B → divider
    ├─ +5V → ferrite
    ├─ GND ──┐
    └─ Shield┴─→ [Single GND point at J1-J3]
    
    Result: Shield terminates shield current, prevents noise loop
```

### Mistake #4: Ferrite Bead Omitted or Wrong Value

❌ **Problem**: SMPS high-frequency noise couples directly onto encoder VCC
```
    5V_RAIL ──────── (no ferrite) ──── [Encoder VCC]
    
    500kHz noise rides into encoder power supply.
    Coupled to signal dividers via parasitic capacitance.
    Result: Encoder jitter, missed pulses.
```

✅ **Fix**: 600Ω ferrite + 100nF cap at encoder connector
```
    5V_RAIL ── [600Ω ferrite @ 500kHz] ── [100nF] ── [Encoder VCC]
    
    Ferrite blocks 500kHz noise (high-Z path)
    Capacitor provides local clean 5V
    Result: Encoder sees <50mV ripple @ 500kHz
```

### Mistake #5: 100nF Cap Too Far from Encoder

❌ **Problem**: Capacitor in middle of board, traces to connector long
```
    [100nF cap somewhere on board] ──[long wire]── Encoder VCC
    
    Long trace = series inductance → defeats decoupling
```

✅ **Fix**: Capacitor located AT CONNECTOR
```
    Ferrite [FB] ── [100nF cap] ── [Encoder VCC pin (J1)]
                    └─────────────── direct GND connection
                    (within 1cm)
    
    Minimized loop inductance → effective decoupling
```

---

## 12. Summary: Design Checklist

Before PCB layout, verify:

- [ ] **Ground plane unified** (single plane with wide separation traces, not islands)
- [ ] **Star point defined** (central location, typically near bulk cap)
- [ ] **SMPS zone isolated** (60-100mm from encoder zone, switching node identified)
- [ ] **Ferrite + filter on each encoder VCC** (600Ω ferrite, 100nF ceramic, at connector)
- [ ] **Signal traces routed away from SMPS** (on opposite board area, 30-40mm min separation)
- [ ] **Encoder cable shield single-point grounded** (at board entry, same GND as power)
- [ ] **Vias strategically placed** (every 10-15mm on GND traces, at component pads)
- [ ] **Decoupling caps close to supply points** (C1/C2 at star, 100nF at connectors, 1nF at dividers)
- [ ] **Trace width hierarchy** (5V_RAIL: 2mm, encoder VCC: 1mm, signals: 0.5mm, GND: 3-5mm)
- [ ] **Test points accessible** (TP1: 5V_RAIL, TP5: GND, for noise measurement)

---

## 13. Reference: evka_position Configuration

**Current PCB**: 120mm × 80mm double-sided pertinax (hand-soldered through-hole)

**SMPS**: MT3608 boost converter (3.7V LiPo → 5.3V, 500kHz switching, <100mA typical)

**Encoders**: 3x quadrature + Z-index (E40S6 rotary, DWEM2 draw-wire)
- Max signal frequency: ~15kHz (at 20kHz encoder PPR, 750 RPM max)
- Signal levels: 0-5V TTL → 0-3.3V after divider

**Applied best practices**:
1. ✓ Unified ground plane (bottom layer entirely copper)
2. ✓ Star point near C1 (220μF bulk cap)
3. ✓ SMPS (MT3608 module) in top-left zone
4. ✓ Encoder section (J1-J3, dividers) in bottom-left zone, separated by ~60mm
5. ✓ Ferrite + 100nF at each encoder VCC input
6. ✓ Wide GND traces (3-5mm) on bottom layer converging to star point
7. ✓ Signal traces routed via right side of board, away from SMPS
8. ✓ TVS diodes (1.5KE3.3CA) at divider junctions for ESD protection

---

## 14. References & Standards

- **IEC 61000-4-6**: RF immunity testing (useful for understanding EMI threats)
- **IPC-A-610**: PCB assembly quality (via placement, trace width, spacing)
- **EDN**: "PCB Layout for Switching Power Supplies" (practical guidance)
- **MT3608 datasheet**: Section 5 (PCB layout recommendations)

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-05  
**Applied to**: evka_position encoder + buck/boost SMPS integration  
**Status**: Verified on hand-soldered pertinax board with 3x encoders + MT3608 + TP4056
