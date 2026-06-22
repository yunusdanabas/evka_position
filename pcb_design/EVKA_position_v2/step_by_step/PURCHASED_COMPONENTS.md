# Purchased components — footprint map for step drafts

Authoritative mapping from **parts you bought** to project refdes and KiCad footprints.
Step agents must assign these footprints on every placed symbol (via `footprint` in
`batch_add_and_connect` / `batch_edit_schematic_components`, or `edit_schematic_component`).

Use `search_footprints` + `get_footprint_info` to confirm the library name exists in your KiCad install
before assigning. If a listed footprint is missing, pick the closest match, log the substitution in
`BUILD_LOG.md`, and note it in the step lesson.

Older docs (`docs/bill_of_materials.md`) may still say **74HC14N DIP-14** — your stock is **SOIC-14**.
Follow this file, not the stale DIP wording.

---

## Purchased parts (your stock)

| Bought component | Refdes | Qty | Footprint (KiCad lib:Name) | Notes |
|---|---|---:|---|---|
| **MT3608 2A DC-DC Boost Module** | `MOD_MT3608` | 1 | `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` (module on 4-pin header) | Boost LiPo → ~5 V. Trim-pot mod per BOM; R_MT_HI/LO on module, not board. |
| **10 µH 1 A inductor** | `L1` | 1 | `Inductor_THT:L_Radial_D9.0mm_P5.00mm_V` | π-filter on 5 V rail. Verify radial vs axial against physical part. |
| **6×6 mm tactile button** | — | 0 | — | **Not used.** DevKitC-1 has onboard reset. Do not place. |
| **1N5822-HT Schottky** | `D_BAR`, `D_EXT`, `D_BOOST` | **3** | `Diode_THT:D_DO-201AD_P15.24mm_Horizontal` | Input diode + both OR diodes. |
| **74HC14 SOIC-14** | `U_SCHM` | 1 | `Package_SO:SOIC-14_3.9x8.7mm_P1.27mm` | **SOIC-14 only — not DIP-14.** Set `value` to `74HC14`. |
| **2.1 mm barrel jack** | `J4` (master may use `J1`) | 1 | `Connector_BarrelJack:BarrelJack_CUI_PJ-002A_Horizontal` | Centre-positive 5.5×2.1 mm. Third switch pin → `add_no_connect`. |
| **2-pin 5.00 mm terminal block** | `J6` | 1 | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-pol` | Bench 5 V input (`J6`). |
| **3-pin 5.00 mm terminal block** | — (spare) | 0 | — | **No longer used.** Was the wire-encoder signal block (`J3b`); design now uses a single 4-pin `J3` (GND/VCC/A/B, Z unused). Keep as spare. |
| **SMAJ5.0A TVS** | `TVS_BAR` | 1 | `Diode_SMD:D_SMA` | Input ESD at barrel jack. Symbol: `Diode:SMAJ5.0A` or custom. |
| **Encoder TVS** | `TVS1`…`TVS6` | 6 (populate) | `Diode_THT:D_DO-201AD_P15.24mm_Horizontal` (flexible) | **Populate** a general THT TVS (part TBD; bidir, V_RWM ≥ ~3.34 V — reuse on-hand 1.5KE3.3CA / import 1.5KE3.9CA). The mis-ordered P6KE39CA (33 V) is **not** used. |
| **PJA3441 P-MOSFET** | `Q_RPP` | 1 | `Package_TO_SOT_SMD:SOT-23` | Reverse-polarity protection. |
| **ESP32-S3 N16R8 DevKitC-1** | `U1` | 1 | `Module:ESP32-S3-DevKitC-1` (or 2×22 socket + keepout per layout guide) | Socket-mounted on carrier PCB. |
| **2.25 mm 2-pin JST female** | `J5` | 1 | `Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` **placeholder** | **Verify pitch with calipers** (may be 2.0 / 2.25 / 2.5 mm). Swap footprint if needed. |

---

## Passives & modules not in purchase list (still need footprints)

These are not in your purchase table but appear on the board — use standard THT footprints unless
the reference schematic specifies otherwise.

| Refdes | Part | Footprint |
|---|---|---|
| `R_RPP`, `R_LED1`, `R_MON1`, `R_MON2`, `R_TOP1..6`, `R_BOT1..6`, `J_FB1..3` | 1/4 W metal film | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |
| `C2`, `C_ADC`, `C_FILT1..6`, `C_VCC1..3`, `C_SCHM` | 100 nF / 10 nF ceramic | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` |
| `C_PI`, `C1`, `C_BOOST` | Electrolytic 10 µF / 220 µF / 22 µF | `Capacitor_THT:CP_Radial_D5.0mm_P2.50mm` (verify diameter vs stock) |
| `LED1` | Green 5 mm LED | `LED_THT:LED_D5.0mm` |
| `MOD_TP4056` | TP4056+DW01A module | `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical` (6-pin module header) |
| `J1`, `J2`, `J3` | 4-pin 5 mm screw terminal (encoders — all three, incl. wire encoder) | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-4-pol` |
| `TP1`…`TP5` | Test point | `TestPoint:TestPoint_Keystone_5019_Micro_Miniature` |
| `FLG_*` | PWR_FLAG | no footprint (ERC token) |

---

## Footprint assignment checklist (every step agent)

1. Read this file before placing parts in the step's refdes range.
2. Set `footprint` on **every** populated symbol when using `batch_add_and_connect` / `batch_add_components`.
3. `TVS1..6` are **populated** (general THT TVS, flexible axial footprint, exact part TBD) — set the footprint; no DNP.
4. Add a **Footprint** column to the step lesson component table.
5. After placement, `list_schematic_components` — confirm no populated part has an empty Footprint field.
6. Log footprint substitutions or pitch verifications (`J5`, `L1`) in `BUILD_LOG.md`.

---

## Step → refdes quick map

| Step | Assign footprints for |
|---|---|
| 1 | `J4`, `TVS_BAR`, `D_BAR`, `Q_RPP`, `R_RPP` |
| 2 | `D_EXT`, `C_PI`, `L1`, `C1`, `C2`, `R_LED1`, `LED1`, `J6`, `TP1` |
| 3 | `MOD_TP4056`, `MOD_MT3608`, `D_BOOST`, `C_BOOST`, `J5`, `TP3`, `TP4` |
| 4 | `R_MON1`, `R_MON2`, `C_ADC` |
| 5 | `J1`, `J2`, `J3`, `J_FB1..3`, `C_VCC1..3` |
| 6 | `R_TOP1..6`, `R_BOT1..6`, `C_FILT1..6`, `TVS1..6` (populate) |
| 7 | `U_SCHM` (**SOIC-14**), `C_SCHM` |
| 8 | `U1` (DevKitC-1) |
| 9 | `TP2`, `TP5` |
