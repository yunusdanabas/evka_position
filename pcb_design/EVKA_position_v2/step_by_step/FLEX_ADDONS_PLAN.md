# Flexibility add-ons — Steps 10+ (post-completion expansion)

These are **optional additions** layered on top of the finished, ERC-clean master
(`Master Design/EvkaPosition_v2/EvkaPosition_v2.kicad_sch`, 64 components as of 2026-06-19). Each is a
small self-contained sub-circuit that ties into existing rails (`+5V`, `+3V3`, `GND`) and free ESP32-S3
GPIOs. Build them the same way as Steps 1–9: place → label interface nets → re-run ERC (must stay 0).

**Core set (recommended): Steps 10, 11, 12.** Optional/heavier: Steps 13–15.

## GPIO budget (verified against the netlist)

Reserved, **never route**: encoders 4/5/6/7/15/16 · battery ADC 1 · strapping 0/3/45/46 · USB 19/20 ·
octal-PSRAM 35/36/37 · onboard WS2812 38.
Free & safe: **8, 9, 10, 11, 12, 13, 14, 17, 18, 21, 39, 40, 41, 42, 47, 48** (39–42 = JTAG MTDI/O/CK/MS,
fine if you don't need hardware JTAG).

Allocation used below (with the exact U1 stand-in header pin from the netlist):

| Function | GPIO | U1 pin |
|---|---|---|
| AUX1 (breakout) | 11 | J1_17 |
| AUX2 (breakout) | 12 | J1_18 |
| AUX3 (breakout) | 13 | J1_19 |
| AUX4 (breakout) | 14 | J1_20 |
| I2C_SDA | 8 | J1_12 |
| I2C_SCL | 9 | J1_15 |
| SW_HOME | 17 | J1_10 |
| SW_LIMIT | 18 | J1_11 |

Placement: open area right of / below U1 (≈ Zone E), on the **2.54 mm grid** (never `snap_to_grid`).

---

## Step 10 — Spare GPIO + power breakout header · Zone E

| Refdes | Symbol | Value | Footprint |
|---|---|---|---|
| J_EXP | `Connector_Generic:Conn_02x06_Odd_Even` | AUX_IO | `Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical` |
| R_AUX1..4 | `Device:R` | 100R (optional, DNP) | series protection on each GPIO line |

- **Pinout (2×6, ground-per-signal for SI):** odd pins = signals/power, even pins = GND.
  - 1: AUX1 · 3: AUX2 · 5: AUX3 · 7: AUX4 · 9: `+3V3` · 11: `+5V`
  - 2,4,6,8,10,12: `GND`
- **Nets:** AUX1..4 ← U1 GPIO 11/12/13/14 (optionally through R_AUX series Rs). `+3V3`, `+5V`, `GND` merge
  with existing rails.
- **Interface in:** `+5V` (Step 2), `+3V3` (Step 8). **out:** AUX1..4 to U1.
- **Keypoints:** the catch-all "I wish I'd exposed that" header — future sensor, 4th low-speed input, jumper
  test. Series R_AUX are **DNP** by default (place footprints, leave unpopulated = 0 Ω solder bridge or
  jumper); populate 100 Ω only if you drive long lines and want edge-rate / ESD softening. Ground-per-pin
  keeps return paths short on a ribbon cable.
- **Firmware follow-up:** none required — pins idle until you use them.

## Step 11 — I²C / Qwiic expansion · Zone E

| Refdes | Symbol | Value | Footprint |
|---|---|---|---|
| J_I2C | `Connector_Generic:Conn_01x04` | Qwiic_I2C | `Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal` |
| R_SDA | `Device:R` | 4.7k | pull-up `I2C_SDA` → `+3V3` |
| R_SCL | `Device:R` | 4.7k | pull-up `I2C_SCL` → `+3V3` |
| C_I2C | `Device:C` | 100nF | `+3V3` → GND, near connector |

- **Qwiic standard pinout (do not reorder):** pin1 `GND`, pin2 `+3V3`, pin3 `I2C_SDA`, pin4 `I2C_SCL`.
- **Nets:** `I2C_SDA` ← U1 GPIO8, `I2C_SCL` ← U1 GPIO9; both pulled to `+3V3` via 4.7k.
- **Interface in:** `+3V3` (Step 8). **out:** `I2C_SDA`/`I2C_SCL` to U1.
- **Keypoints:** plug-and-play into the Qwiic/STEMMA-QT ecosystem — IMU (tilt cross-check), OLED, RTC,
  IO-expander, temp/current sensor. 4.7k is the right board-master pull-up at 3.3 V; if you only ever plug
  in modules that carry their own pull-ups, R_SDA/R_SCL can be DNP. Add a 0.1" `Conn_01x04` in parallel if
  you also want a bare-header option.
- **Firmware follow-up:** `Wire.begin(8, 9)`; driver per device. Deferred — hardware-first.

## Step 12 — Home / limit switch inputs · Zone E

| Refdes | Symbol | Value | Footprint |
|---|---|---|---|
| J_SW | `Connector:Screw_Terminal_01x04` | SWITCHES | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-4_1x04_P5.00mm_Horizontal` |
| R_SW1 | `Device:R` | 10k | pull-up `SW_HOME` → `+3V3` |
| R_SW2 | `Device:R` | 10k | pull-up `SW_LIMIT` → `+3V3` |
| C_SW1 | `Device:C` | 100nF | `SW_HOME` → GND (debounce) |
| C_SW2 | `Device:C` | 100nF | `SW_LIMIT` → GND (debounce) |

- **Terminal pinout (1×4):** 1: `GND` · 2: `SW_HOME` · 3: `SW_LIMIT` · 4: `+3V3` (for 3-wire sensors).
- **Nets (each switch):** `+3V3` → R_SWn → `SW_x` → U1 GPIO; C_SWn from `SW_x` to GND. Switch wired between
  the terminal and GND (active-low). `SW_HOME` ← GPIO17, `SW_LIMIT` ← GPIO18.
- **Interface in:** `+3V3` (Step 8). **out:** `SW_HOME`/`SW_LIMIT` to U1.
- **Keypoints:** most device-relevant add — a real home switch lets firmware fire `ZERO` on a mechanical
  reference instead of the 2 s power-on guess; the limit input can flag over-travel. External 10k pull-up
  (not just internal) gives a defined level even before firmware configures the pin; 10k·100nF ≈ 1 ms RC
  debounce. Reuse the MKDS terminal family from Steps 1/5 for a consistent connector BOM. Pin 4 `+3V3`
  supports active 3-wire prox/optical home sensors; leave it unused for dry-contact switches.
- **Firmware follow-up:** `pinMode(17/18, INPUT)`; on `SW_HOME` falling edge → `setZeroPoint()`. Deferred.

---

## Optional / heavier add-ons (spec later if wanted)

### Step 13 — Encoder Z/index inputs (accuracy)
Bring the rotary (and wire) **Z/index** outputs to GPIOs for once-per-rev absolute reference (better homing
/ drift correction). **Cost:** the 4-pin J1/J2/J3 terminals have no Z pin — needs **5-pin connectors** plus
a **second 74HC14** (`U_SCHM2`) + divider/filter per Z channel (Step 6 pattern). Non-trivial; only if homing
accuracy justifies it. Free GPIOs: 21, 47, 48.

### Step 14 — Wired comms to CMD-CNC (robustness) — pick one
- **14a UART header** (`Conn_01x04`: GND/3V3/TX/RX): simplest wired/debug link. GPIO39(TX)/40(RX).
- **14b RS-485** (THVD1450 / MAX3485 + 120 Ω terminator + DE/RE): industrial-noise-robust 2-wire to the
  controller. Adds a transceiver IC + 3 GPIOs (TX/RX/DE). Bigger commitment than 14a.

### Step 15 — Discrete I/O
- **15a low-side MOSFET output** (logic-level NMOS, GPIO→gate, flyback diode if inductive): drive a brake /
  beacon / buzzer on a 2-pin terminal. GPIO41.
- **15b spare analog input** (RC-filtered terminal → ADC1 pin GPIO10): pot / current-sense / NTC.

---

## After placing any step
1. Label the interface nets so they merge with `+5V` / `+3V3` / `GND` and land on the listed U1 pins.
2. `run_erc` → **0 errors** (new passive header/pull-up pins won't add driver errors).
3. Log it in `BUILD_LOG.md`; export PDF/SVG to eyeball.
4. These are schematic-only — firmware support comes after, hardware-first per project convention.
