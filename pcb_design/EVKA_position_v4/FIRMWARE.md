# v4 PCB — Firmware Quickstart

Firmware for the EVKA_position **v4 PCB** (ESP32-S3-DevKitC-1, N16R8). Same source
tree as the classic board; the v4 pin map is compiled in by the `-DPCB_V4` flag
(PlatformIO env `esp32s3_v4`).

## 1. Pin map (as-fabricated — verified against schematic + PCB)

| Signal | GPIO | Connector |
|---|---|---|
| Theta A / B | 7 / 8 | J1 (A=pin3, B=pin4) |
| Phi A / B | 4 / 5 | J2 |
| Wire A / B | 9 / 10 | J3 |
| Battery ADC | 1 | 1S LiPo, on-board 100k/100k ÷2 |

Each encoder connector is `GND, +5V, A, B`. Encoders run at 5 V; the on-board
10k/20k dividers bring the signals to 3.3 V logic — nothing external to add.
There are **no onboard buttons** (GPIO17/18 are unconnected). The carrier has a
hardwired green **power LED** only; status feedback uses the **ESP32-S3 DevKit
onboard RGB LED** (WS2812 on GPIO48 — see §9).

## 2. Build & flash

```bash
pio run -e esp32s3_v4                    # compile
pio run -e esp32s3_v4 --target upload    # flash
pio device monitor                       # serial, 115200 baud
```

## 3. First power-on (zeroing)

On boot the firmware prints a banner, waits **2 s**, then calls `setZeroPoint()`.
The robot **must be at mechanical home** at that moment — all readings are relative
to that snapshot. Re-zero any time without reflashing by sending `ZERO` (serial, or
over WiFi/TCP). Selective: `ZERO_T`, `ZERO_P`, `ZERO_W`.

## 4. Reading position

At 20 Hz the firmware streams position telemetry — the format differs per transport:

- **Serial** and **web dashboard WebSocket**:
  `DATA,<x>,<y>,<z>,<r>,<theta>,<phi>,<is_valid>,<frame>,<ts_ms>`
- **CMD TCP server** (`192.168.1.50:8080`): two separate lines —
  `X<x>,Y<y>,Z<z>` and `SENSOR,<r>,<theta>,<phi>,<is_valid>,<frame>`
  (it does **not** send `DATA,`).

Query on demand with `STATUS` / `CONSTANTS` / `PING`. `BLINK` flashes the status LED
(§9) so you can confirm a live link over any transport. Full command list is in the
repo `CLAUDE.md` and `docs/integration/CMD_SOFTWARE_INTEGRATION.md`.

For a ready-made host GUI that handles both transports (live position, 3D trail,
battery, ESP-NOW remote), use `tools/evka_gui`:
`python -m tools.evka_gui --serial /dev/ttyUSB0` or `--tcp 192.168.1.50:8080`.

## 5. WiFi dashboard

`ENABLE_WIFI=1` (default) → the board makes an AP:

- SSID `CMDCNC_EVKA`, password `cmdcnc1234`
- Dashboard: `http://192.168.1.50` (Live view + CALIBRATE tabs)
- CMD TCP server: `192.168.1.50:8080`

## 6. Battery monitor

`ENABLE_BATTERY_MONITOR=1` on v4. A `STATUS` command emits `BATT,<v>,<pct>,<is_low>`
on serial and broadcasts it to TCP/WebSocket clients; `<v>` is the 1S cell voltage
(~3.0–4.2 V, GPIO1 ÷2 divider). The `tools/evka_gui` GUI polls `STATUS` to keep
its battery panel live.

## 7. Encoder direction (bring-up check)

Rotate each axis by hand and watch the `DATA` line. Forward should raise +X, lift
should raise +Z, wire extension should raise `r`. If an axis is reversed:

- Theta / Phi → flip `ENCODER_THETA_SIGN` / `ENCODER_PHI_SIGN` in `SphericalSensor.h`.
- Wire has no sign flag → swap the wire `attachFullQuad(A, B)` argument order in
  `SphericalSensor.cpp` (or swap the J3 A/B wires).

## 8. Accessories (work unchanged with v4)

- **Wireless pendant** (`pio run -e button_remote`): ESP-NOW, auto-finds the AP
  channel by SSID — no MAC pairing, board-independent. BTN0 (green) = `SAVE_POINT`,
  BTN1 (red) = `DEL_POINT`.
- **IPT hidden-point tool** (`python -m tools.ipt`): consumes the unchanged
  DATA/TCP stream — needs no firmware change.

## 9. RGB status LED (DevKit onboard)

The ESP32-S3-DevKitC-1 module carries a WS2812 RGB LED (default **GPIO48** on
DevKit v1.0, **GPIO38** on v1.1). Firmware env `esp32s3_v4` drives it via
`neopixelWrite(PIN_RGB_LED)` — not `RGB_BUILTIN`, so the pin is explicit in
`SphericalSensor.h`. If the LED stays dark after flash, try env `esp32s3_v4_rgb38`
or set `-DRGB_LED_GPIO=38` in `platformio.ini`.

Higher-priority states override lower ones. Transient flashes (100 ms) play on top
of the base state, then restore it.

| Priority | State | Color | Pattern | Meaning |
|---:|---|---|---|---|
| 100 | Boot calibrating | Amber | Slow breathe | Wait — robot must stay at mechanical home while zeroing |
| 95 | ESP-NOW fault | Magenta | Fast blink (4 Hz) | Wireless pendant unavailable; position streaming still works |
| 85 | Invalid position | Orange | Blink (1 Hz) | Position out of mechanical limits |
| 80 | WiFi reconnecting | Blue | Blink (500 ms) | Joining / rejoining router (STA) |
| 70 | WiFi connected | Green | Solid | Router connected and valid position |
| 60 | AP only | Cyan | Solid (dim) | No STA credentials — use AP `CMDCNC_EVKA` @ 192.168.1.50 |

**Transient flashes**

| Event | Color | Trigger |
|---|---|---|
| Zero ACK | White | Successful `ZERO`, `ZERO_T`, `ZERO_P`, or `ZERO_W` |
| Connection test | White (~0.7 s) | `BLINK` command (serial / TCP / WebSocket) |
| Remote button | Purple | ESP-NOW pendant button processed |

### Troubleshooting the RGB LED

| Symptom | Likely cause | Fix |
|---|---|---|
| `ACK:BLINK` in serial/TCP but LED stays dark | Wrong DevKit revision GPIO | Reflash with `esp32s3_v4_rgb38` (`-DRGB_LED_GPIO=38`) or set `RGB_LED_GPIO` in `SphericalSensor.h` |
| No `ACK:BLINK` at all | Stale firmware image | `pio run -e esp32s3_v4 --target upload` |
| GUI shows `ERR:UNKNOWN_CMD` on Blink | Same as above | Reflash, then retry |

On boot the firmware briefly flashes the RGB LED white (~100 ms) so you can
confirm the GPIO choice before sending `BLINK`.

Classic ESP32 builds (`wemos_d1_r32`) keep the original GPIO2 monochrome WiFi LED
behavior (off / blink / solid). `BLINK` holds GPIO2 high for ~700 ms.
