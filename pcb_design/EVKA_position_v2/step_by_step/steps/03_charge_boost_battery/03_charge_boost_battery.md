# Step 3 — Charge + boost + load-share (battery leg) · Zone B

The **battery** leg of the dual-source design. A 1S LiPo is charged externally through a TP4056+DW01A
module, boosted to ~5.3 V by an MT3608 module, then OR-ed onto the shared rail node `PI_NODE` through a
Schottky diode — the mirror of Step 1/2's external leg. No onboard charger silicon: both `MOD_*` parts
are breakout boards on pin headers, drawn here as generic connector stand-ins.

Extracted from the read-only reference `../../EVKA_position_v2.kicad_sch`, then **reconciled to the
as-built master `../../Master Design/EvkaPosition_v2/EvkaPosition_v2.kicad_sch` (2026-06-19)**.

> **Master deviation — `BAT_OUT` node.** The reference uses a single net `BAT_PLUS` for the whole battery
> node (TP4056 BAT pin, MT3608 input, ADC, J5). The as-built master splits the booster input onto its own
> named net **`BAT_OUT`** (+ a test point `TP5`). This is fine as a named node, **but `BAT_OUT` must be
> tied to `BAT_PLUS`** or the MT3608 has no input and the battery cannot drive the 5 V rail. In the
> current master that tie is **missing** — add it (see "Copying into your master", step 5). The Step 4 ADC
> monitor still reads `BAT_PLUS` (raw cell voltage) — unchanged.

## ASCII schematic

```
   J5 (LiPo 1S, JST-PH)
   pin1 (+) ──── BAT_PLUS ──┬─────────────┬──────── TP4 (BAT+)
   pin2 (−) ──── GND        │             │
                            │             │
              MOD_TP4056    │         MOD_MT3608
            (TP4056+DW01A)  │       (boost ~5.3 V)
   V_EXT_PROT ──┤1  IN+     │    BAT_OUT ──┤1 IN+      OUT+ 3├── MT3608_OUT ──┬──► TP3
          GND ──┤2  IN−     │  (≡BAT_PLUS) │  GND ─┤2 IN−  OUT− 4├── GND        │
     BAT_PLUS ──┤3  BAT+ ───┤      └────► TP5                                   │
                            │  ↑ tie BAT_OUT ↔ BAT_PLUS (else booster unpowered)│
          GND ──┤4  BAT−                                          C_BOOST ─────┤  22uF
           NC ──┤5  CHRG  (X)                                    (MT3608_OUT)  │
           NC ──┤6  STDBY (X)                                        │        GND
                                                                    GND        │
                                            MT3608_OUT ──┤2  A  D_BOOST  K  1├──┴── PI_NODE ──► (Step 2 OR node)
                                                            (1N5822 Schottky)

   PWR_FLAG: FLG_BATPLUS → BAT_PLUS
```

Battery current path: `J5(+) → BAT_PLUS ≡ BAT_OUT → MT3608 → MT3608_OUT → D_BOOST → PI_NODE`.
Charge path (separate): `V_EXT_PROT → TP4056 IN+ → … → BAT_PLUS` (only while the adapter is present).

## Components

| Refdes | Symbol (lib_id) | Value | `(at x y rot)` | Footprint |
|---|---|---|---|---|
| MOD_TP4056 | `Connector_Generic:Conn_01x06` | TP4056 | 320.04, 71.12, 0 | `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical` |
| MOD_MT3608 | `Connector_Generic:Conn_01x04` | MT3608 5V0 | 381, 71.12, 0 | `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` |
| D_BOOST | `Diode:1N5822` | 1N5822 | 429.26, 60.96, 0 | `Diode_THT:D_DO-201AD_P15.24mm_Horizontal` |
| C_BOOST | `Device:C_Polarized` | 22uF/10V | 408.94, 88.9, 0 | `Capacitor_THT:CP_Radial_D5.0mm_P2.50mm` |
| J5 | `Connector_Generic:Conn_01x02` | LiPo 1S | 320.04, 119.38, 0 | `Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` |
| TP3 | `Connector:TestPoint` | MT3608_OUT | 444.5, 45.72, 0 | `TestPoint:TestPoint_Keystone_5019_Miniature` |
| TP4 | `Connector:TestPoint` | BAT+ | 350.52, 109.22, 0 | `TestPoint:TestPoint_Keystone_5019_Miniature` |
| TP5 | `Connector:TestPoint` | BAT_OUT | *(master addition — your placement)* | `TestPoint:TestPoint_Keystone_5019_Miniature` |
| FLG_BATPLUS | `power:PWR_FLAG` | — | 459.74, 45.72, 0 | — |

## Nets (as built)

| Net | Pins | Role |
|---|---|---|
| `BAT_PLUS` | J5/1, MOD_TP4056/3, TP4/1, FLG_BATPLUS/1 | raw LiPo + node — **interface out → Step 4 ADC** (read this for SoC) |
| `BAT_OUT` | MOD_MT3608/1 (IN+), TP5/1 | booster input — **must be tied to `BAT_PLUS`** (else MT3608 unpowered) |
| `MT3608_OUT` | MOD_MT3608/3, D_BOOST/2(A), C_BOOST/1, TP3/1 | boost output ~5.3 V |
| `PI_NODE` | D_BOOST/1(K) | **interface out → Step 2** (battery OR leg) |
| `V_EXT_PROT` | MOD_TP4056/1 | charge input from the external leg (interface in ← Step 1) |
| `GND` | J5/2, MOD_TP4056/2,4, MOD_MT3608/2,4, C_BOOST/2 | ground |
| (NC) | MOD_TP4056/5 (CHRG), /6 (STDBY) | `add_no_connect` — module status LEDs, unused |

## Keypoints (the lesson)

- **External charging only.** This as-built rev has *no* onboard charge controller. The TP4056+DW01A
  module (`MOD_TP4056`) does charge + cell protection on its own PCB; the board just routes `V_EXT_PROT`
  into its IN+ and the LiPo into its BAT+. Pins 5/6 (CHRG/STDBY LED drivers) are left no-connect.
- **Boost to ~5.3 V on purpose.** The MT3608 is trimmed above 5 V so that after D_BOOST's ~0.3–0.4 V
  Schottky drop, `PI_NODE` from the battery leg (~4.95 V) is *just higher* than the external leg
  (~4.65 V). When both sources are live the battery shares/wins slightly; pull the adapter and the
  battery seamlessly carries the rail.
- **Passive Schottky-OR — no active load-share IC.** `D_BOOST` (battery) and `D_EXT` (external, Step 2)
  meet cathode-to-cathode at `PI_NODE`. Each diode blocks back-feed into the other source. Cheap,
  robust, costs one diode drop. (`MT3608_OUT →►|D_BOOST→ PI_NODE ←|◄ D_EXT← V_EXT_PROT`.)
- **C_BOOST (22 µF)** smooths the MT3608's switched output before the OR diode — pairs with Step 2's
  π-filter to keep boost ripple off the logic rail.
- **`BAT_OUT` is the booster-input node (master rev).** Electrically it is the *same node* as `BAT_PLUS`
  — a separate label only because the master breaks it out (with test point `TP5`) to meter the current
  the booster pulls. It carries the raw cell voltage, **not** a regulated rail. It **must** connect to
  `BAT_PLUS`; if left isolated the MT3608 has no input and the battery leg is dead.
- **TP3 / TP4 / TP5** let you meter the boost output, the raw battery, and the booster-input feed without
  probing module pins.

## ERC on this isolated sub-circuit

`0 errors, 4 warnings` — all benign:
1. *Label connected to only one pin* @ `V_EXT_PROT` (MOD_TP4056/1) — interface-in; merges with Step 1.
2. *Label connected to only one pin* @ `PI_NODE` (D_BOOST/1) — interface-out; merges with Step 2's D_EXT.
3–4. *Conn_01x02 / Conn_01x04 doesn't match copy in library 'Connector_Generic'* — cosmetic library
   version mismatch, harmless. Do **not** `snap_to_grid`.

No floating-net *errors*: `FLG_BATPLUS` drives `BAT_PLUS`; `GND` carries only passive pins.

## Copying into your master

1. Place all 9 parts at the coordinates above (already 2.54 grid). Set footprints as listed — verify the
   **J5 pitch with calipers** (placeholder is 2.0 mm JST-PH; swap if your connector is 2.25/2.5 mm).
2. Label `BAT_PLUS` (TP4056 BAT pin, TP4, J5+, FLG_BATPLUS), `BAT_OUT` (MT3608 IN+, TP5), `MT3608_OUT`,
   `GND` snapped to pins; `PI_NODE` on D_BOOST cathode (merges with the Step 2 `PI_NODE` already in the
   master); `V_EXT_PROT` on MOD_TP4056 IN+ (merges with Step 1).
3. `add_no_connect` on MOD_TP4056 pins 5 and 6.
4. Carry **`BAT_PLUS`** forward to Step 4 (ADC monitor). `PI_NODE` is the shared OR node — already present.
5. **Tie `BAT_OUT` ↔ `BAT_PLUS`.** In the current master these are two isolated nets, so the MT3608 input
   is floating. Run a wire from the `BAT_PLUS` node to the `BAT_OUT` node (or drop a second `BAT_PLUS`
   label on the `BAT_OUT` wire). Verify with `get_net_connections BAT_PLUS` → it should now also list
   `MOD_MT3608/1` and `TP5/1`. Without this the battery cannot power the rail.
