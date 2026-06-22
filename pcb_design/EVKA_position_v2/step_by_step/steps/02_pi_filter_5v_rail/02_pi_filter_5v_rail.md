# Step 2 — Pi-filter + 5V rail + power LED

**Sub-circuit:** passive Schottky-OR (external leg) → C-L-C π-filter → 5V output rail.  
**Interface in:** `V_EXT_PROT` (Step 1). **Interface out:** `+5V` (→ Steps 5, 8), `PI_NODE` (shared w/ Step 3's `D_BOOST`).

---

## ASCII schematic

```
V_EXT_PROT                                              +5V
    │                                                    │
    ▼                                            ┌───────┼────── TP1
  D_EXT                             PI_NODE      │       │
  (1N5822)         ┌────────────────────┐       C1    FLG_5V
    │              │                   L1     220uF      │
    │        ┌─ C_PI ─┐         10uH  ──┤       │      GND
    │        │  10uF  │      PI_NODE ───┘     ──┤─── C2 100nF
    │        │   +    │         │             │ │       │
PI_NODE ─────┤        ├─ GND    │          +5V │      GND
             │   −    │                        │
             └────────┘                        ├─── R_LED1 1k ─── LED1(G) ─── GND
                 │                             │
                GND                            ├─── J6 pin1 (+5V)
                                               │    J6 pin2 (GND)
                                               │
                                               └─── (→ Step 5 encoder VCC, Step 8 ESP32)
```

Redrawn more clearly:

```
V_EXT_PROT ──►|──────────────────── PI_NODE ──┬───── L1 ────────── +5V
              D_EXT (Schottky-OR,               │     (10uH)          │
              external leg)                    C_PI               C1 ∥ C2
                                            (10uF/10V)         (220uF + 100nF)
                                                │                     │
                                               GND                   GND

+5V ──── R_LED1 (1k) ──── LED1 (Green) ──── GND   ← power-on indicator

+5V ──── J6 pin 1   J6 pin 2 ──── GND             ← bench 5V breakout

+5V ──── TP1                                       ← test point

+5V ──── FLG_5V                                    ← ERC PWR_FLAG
```

**D_EXT anode = V_EXT_PROT (right side at 0°); cathode = PI_NODE (left side).** Current flows
right-to-left through D_EXT — this is correct: external 5V sources PI_NODE through the diode.

---

## Component table

All coordinates are from the reference `EVKA_position_v2.kicad_sch`. Footprints per
`../../PURCHASED_COMPONENTS.md` (3 substitutions noted in the ERC section).

| Refdes | Library:Symbol | Value | at (x, y, rot°) | Footprint | Role |
|--------|---------------|-------|-----------------|-----------|------|
| D_EXT | Diode:1N5822 | 1N5822 | (152.4, 60.96, 0) | Diode_THT:D_DO-201AD_P15.24mm_Horizontal | Schottky-OR external leg |
| C_PI | Device:C_Polarized | 10uF/10V | (180.34, 86.36, 0) | Capacitor_THT:CP_Radial_D5.0mm_P2.50mm | π-filter input shunt cap |
| L1 | Device:L | 10uH | (203.2, 55.88, 90) | Inductor_THT:L_Radial_D10.0mm_P5.00mm_Neosid_SD12_style3 | π-filter series inductor |
| C1 | Device:C_Polarized | 220uF/10V | (228.6, 86.36, 0) | Capacitor_THT:CP_Radial_D5.0mm_P2.50mm | π-filter output bulk cap |
| C2 | Device:C | 100nF | (243.84, 86.36, 0) | Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm | π-filter output HF bypass |
| R_LED1 | Device:R | 1k | (264.16, 60.96, 0) | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | LED current limit |
| LED1 | Device:LED | Green | (264.16, 88.9, 0) | LED_THT:LED_D5.0mm | Power-on indicator |
| J6 | Connector:Screw_Terminal_01x02 | BENCH_5V | (35.56, 119.38, 0) | TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal | Bench 5V breakout |
| TP1 | Connector:TestPoint | 5V_RAIL | (236.22, 45.72, 0) | TestPoint:TestPoint_Keystone_5019_Miniature | 5V rail test point |
| FLG_5V | power:PWR_FLAG | PWR_FLAG | (215.9, 45.72, 0) | — | ERC power-pin flag |

---

## Net table

| Net | Pins | Label coords (x, y, rot°) |
|-----|------|--------------------------|
| V_EXT_PROT | D_EXT anode (right side) | (156.21, 60.96, 0) |
| PI_NODE | D_EXT cathode (left side) | (148.59, 60.96, 180) |
| PI_NODE | C_PI positive pin (+, top) | (180.34, 82.55, 270) |
| PI_NODE | L1 pin 1 (left when rotated 90°) | (199.39, 55.88, 180) |
| +5V | L1 pin 2 (right when rotated 90°) | (207.01, 55.88, 0) |
| +5V | C1 positive pin (+, top) | (228.6, 82.55, 270) |
| +5V | C2 pin 1 (top) | (243.84, 82.55, 270) |
| +5V | R_LED1 top pin | (264.16, 57.15, 270) |
| +5V | J6 pin 1 | (30.48, 119.38, 180) |
| +5V | TP1 test point pin | (236.22, 45.72, 90) |
| +5V | FLG_5V PWR pin | (215.9, 45.72, 90) |
| GND | C_PI negative (−, bottom) | (use GND power symbol) |
| GND | C1 negative (−, bottom) | (use GND power symbol) |
| GND | C2 pin 2 (bottom) | (use GND power symbol) |
| GND | LED1 cathode (K) | (use GND power symbol) |
| GND | J6 pin 2 | (use GND power symbol) |
| LED_A | R_LED1 pin 2 (bottom) + LED1 anode (pin 2) | snap-to-pin label both ends |

`R_LED1` and `LED1` share the same x-coordinate (264.16), pins ~28 mm apart vertically. The as-built
reference ties them with a **net label `LED_A`** on both pins (same-named labels merge) — that is what
this draft uses, so no wire is needed. A vertical wire between the two pins is electrically equivalent
if you prefer it in your master.

---

## Keypoints

### 1. Passive Schottky-OR at PI_NODE

`PI_NODE` is the junction where two power sources merge:
- **External leg (this step):** 5V barrel jack → Q_RPP → `V_EXT_PROT` → D_EXT → `PI_NODE`
- **Battery leg (Step 3):** LiPo → MT3608 boost (~5.3V) → D_BOOST → `PI_NODE`

Each leg's Schottky diode prevents back-feed into the other source. Whichever leg has higher voltage
minus its diode drop wins and supplies the rail. There is **no active controller** — this is pure
passive OR-ing (also called "ideal diode OR" when active ICs are used, but this design omits them).

Schottky forward drop ≈ 0.3–0.4V. External 5V lands on `PI_NODE` at ~4.65V; battery boost at 5.3V
lands at ~4.95V. Both are safely above 4.5V so the downstream 5V rail (after the π-filter) sits near
4.65–4.95V depending on which source is active.

### 2. C-L-C π-filter

`PI_NODE` is noisy because the MT3608 boost converter switches at ~300 kHz and its ripple appears on
the net. The π-filter attenuates this before it reaches the logic supply rail:

```
PI_NODE ──┬── L1 (10uH, series) ──┬── +5V
           │                       │
          C_PI                 C1 ∥ C2
        (10uF/10V)         (220uF/10V ∥ 100nF)
           │                       │
          GND                     GND
```

- **C_PI (10uF)** — input shunt: short-circuits high-frequency ripple to GND before the inductor
- **L1 (10uH)** — series impedance: blocks ripple from passing through; presents high Z at 300 kHz
- **C1 (220uF) + C2 (100nF)** — output shunt pair: C1 is bulk (low ESR electrolytic handles
  load transients), C2 is 100nF ceramic for high-frequency bypass (electrolytic self-inductance
  rises above ~1 MHz; ceramic covers the gap)

### 3. Power-on LED

```
+5V ── R_LED1 (1k) ── LED1 (green, Vf ≈ 2.0V) ── GND
```

I = (5V − 2V) / 1kΩ ≈ 3 mA. Visible, not over-driven. Confirms the 5V rail is live. The resistor is
in series above the LED (top pin of R_LED1 connects to +5V, bottom pin connects to LED1 anode via wire).

### 4. J6 bench breakout and TP1 test point

- **J6** (Screw_Terminal_01x02, value BENCH_5V): pin 1 = +5V, pin 2 = GND. Two-terminal screw
  terminal for attaching bench instruments or external loads directly to the 5V rail during test.
- **TP1** (TestPoint, value 5V_RAIL): single-pin test point at +5V. Lets a probe clip onto the rail
  without needing a probe tip on a tiny component pad.

### 5. FLG_5V — why every power net needs a PWR_FLAG

KiCad ERC raises `power_pin_not_driven` on any net that has only passive pins (capacitor, resistor,
LED) without an explicit power source. `PWR_FLAG` is a zero-footprint ERC token that tells KiCad
"this net is driven by a power source outside the schematic (or by net label)." One `FLG_5V` on +5V
silences the error. The same pattern will be used for `+3V3` (Step 9) and `GND` (Step 9).

---

## Copying into the master schematic

1. Place all 10 components at the reference coordinates (2.54 mm grid — all coords above are already
   on-grid multiples).
2. Add net labels using `add_schematic_net_label` snapped to pins:
   - `V_EXT_PROT` on D_EXT anode (Step 1 interface-in — merges with Step 1's label automatically)
   - `PI_NODE` on D_EXT cathode, C_PI(+), L1 input
   - `+5V` on L1 output, C1(+), C2 pin1, R_LED1 top, J6 pin1, TP1, FLG_5V
   - `GND` (power symbol) on C_PI(−), C1(−), C2 pin2, LED1(K), J6 pin2
   - `LED_A` on R_LED1 pin 2 (bottom) **and** LED1 anode (pin 2) — both ends, labels merge.
3. Verify L1 orientation: at 90° rotation, confirm which pin is input (PI_NODE) vs. output (+5V) via
   pin-endpoint coordinates — do **not** run `snap_to_grid`.
4. Carry **`PI_NODE`** and **`+5V`** forward to Step 3 and Steps 5/8 respectively.

## ERC on this isolated sub-circuit

A standalone KiCad draft of this step lives beside this file (`02_pi_filter_5v_rail.kicad_sch`).
`run_erc`: **0 errors, 5 warnings** — all benign:
1. *Label connected to only one pin* @ `V_EXT_PROT` — the interface-in net; in isolation only D_EXT's
   anode is on it. It merges with Step 1's `V_EXT_PROT` once both are in the master.
2–5. *Symbol 'L'/'C'/'R'/'LED' doesn't match copy in library 'Device'* — cosmetic library-version
   mismatch, harmless (same class of warning as Step 1).

**Footprint substitutions** (purchased-parts file lists names that don't exist verbatim in this KiCad
install — closest matches used, log them when you order):
- `L1`: `L_Radial_D9.0mm_P5.00mm_V` → **`Inductor_THT:L_Radial_D10.0mm_P5.00mm_Neosid_SD12_style3`**
  (verify against the physical 10 µH part's diameter/pitch).
- `TP1`: `TestPoint_Keystone_5019_Micro_Miniature` → **`TestPoint:TestPoint_Keystone_5019_Miniature`**.
- `J6`: `…MKDS-1,5-2-pol` → **`…MKDS-1,5-2_1x02_P5.00mm_Horizontal`**.
