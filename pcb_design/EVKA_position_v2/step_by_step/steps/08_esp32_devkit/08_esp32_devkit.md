# Step 8 — ESP32-S3-DevKitC-1 · Zone D

The brain. A 2×22 generic connector stands in for the ESP32-S3-DevKitC-1 N16R8 dev board (socket-mounted
on the carrier). It receives the six buffered encoder outputs and the battery ADC sense line, takes 5 V
in, and *sources* the 3V3 rail (from the board's onboard regulator) that powers the Step 7 buffer.

Extracted verbatim from the read-only reference `../../EVKA_position_v2.kicad_sch`.

## ASCII schematic (used pins)

```
                 U1  ESP32-S3-DevKitC-1  (Conn_02x22 stand-in)
       +5V ──┤1            2├── GND
      +3V3 ◄─┤3            4├── ADC_MON         (3V3 is an OUTPUT of the board)
THETA_A_OUT ─┤5 (IO4)      6├── THETA_B_OUT (IO5)
  PHI_A_OUT ─┤7 (IO6)      8├── PHI_B_OUT  (IO7)
 WIRE_A_OUT ─┤9 (IO15)    10├── WIRE_B_OUT (IO16)
             │11 … 43  (NC = X)                 (all unused pins no-connect)
          NC─┤43          44├── GND
```

Connector pins 1–10 + 44 are wired; pins 11–43 are `no_connect`.

## Components

| Refdes | Symbol (lib_id) | Value | `(at x y rot)` | Footprint |
|---|---|---|---|---|
| U1 | `Connector_Generic:Conn_02x22_Odd_Even` | ESP32-S3-DevKitC-1 | 480.06, 309.88, 0 | *(blank — stand-in; assign at PCB stage)* |

`Module:ESP32-S3-DevKitC-1` is **not in this KiCad install** and the reference left U1's footprint blank.
At PCB layout, drop in the real DevKitC-1 footprint (or a 2×22 socket + keepout per the layout guide).

## Pin → net map (as built)

| Pin | Net | Real DevKitC-1 signal |
|---|---|---|
| 1 | `+5V` | 5V / VBUS in |
| 2 | `GND` | GND |
| 3 | `+3V3` | 3V3 — **board regulator output** (sources Step 7) |
| 4 | `ADC_MON` | IO1 (ADC) ← Step 4 |
| 5 | `THETA_A_OUT` | IO4 ← Step 7 |
| 6 | `THETA_B_OUT` | IO5 ← Step 7 |
| 7 | `PHI_A_OUT` | IO6 ← Step 7 |
| 8 | `PHI_B_OUT` | IO7 ← Step 7 |
| 9 | `WIRE_A_OUT` | IO15 ← Step 7 |
| 10 | `WIRE_B_OUT` | IO16 ← Step 7 |
| 44 | `GND` | GND |
| 11–43 | — | `no_connect` |

## Keypoints (the lesson)

- **U1 is a stand-in.** A generic 2×22 connector captures the *net* connections only; the physical pin
  order of the real DevKitC-1 is reconciled at PCB layout. That's why the footprint is left blank and a
  text note carries the true GPIO map.
- **The dev board sources 3V3.** `+3V3` is an *output* here — the DevKitC-1's onboard LDO regulates the
  5 V input down to 3.3 V and exposes it on a header pin. That single pin powers the Step 7 74HC14, which
  is why the buffer's outputs are already at ESP32-safe 3.3 V.
- **GPIO choice avoids reserved pins.** Encoder outs land on IO4/5/6/7/15/16 and the ADC on IO1 — all
  general-purpose. The note records what to *avoid*: strapping pins (0/3/45/46), USB (19/20), PSRAM
  (35/36/37), UART0 (43/44), and the onboard WS2812 (38). Put a signal on a strapping pin and the board
  may fail to boot.
- **Everything unused is no-connect.** 33 of the 44 connector pins are explicitly `no_connect` so ERC
  doesn't flag them — and so nothing accidentally gets routed to a reserved function later.

## ERC on this isolated sub-circuit

`0 errors, 9 warnings` — all benign:
- 9× *Label connected to only one pin* — the interface nets `+5V`, `+3V3`, `ADC_MON`, and the six
  `*_OUT`. Each merges with its neighbour step (Step 2 / Step 9 / Step 4 / Step 7) in the master.
- `GND` has two pins (2 and 44) → no single-pin warning. Do **not** `snap_to_grid`.

## Copying into your master

1. Place U1 (`Conn_02x22_Odd_Even`) at (480.06, 309.88). Leave the footprint blank for now.
2. Label pins 1–10 and 44 per the map (these merge with Steps 2/4/7/9). Copy the text note beside U1.
3. `no_connect` pins 11–43 (`batch_add_no_connects` does all 33 in one call).
4. `+3V3` flows *out* to Step 7; `ADC_MON` in from Step 4; `*_OUT` in from Step 7; `+5V` in from Step 2.
