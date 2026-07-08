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
There are **no onboard buttons** (GPIO17/18 are unconnected) and no firmware LED
(only a hardwired green power LED).

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

At 20 Hz the firmware streams:

```
DATA,<x>,<y>,<z>,<r>,<theta>,<phi>,<is_valid>,<frame>,<ts_ms>
```

over serial, the web dashboard WebSocket, and the CMD TCP server. Query on demand
with `STATUS` / `CONSTANTS` / `PING`. Full command list is in the repo `CLAUDE.md`
and `docs/integration/CMD_SOFTWARE_INTEGRATION.md`.

## 5. WiFi dashboard

`ENABLE_WIFI=1` (default) → the board makes an AP:

- SSID `CMDCNC_EVKA`, password `cmdcnc1234`
- Dashboard: `http://192.168.1.50` (Live view + CALIBRATE tabs)
- CMD TCP server: `192.168.1.50:8080`

## 6. Battery monitor

`ENABLE_BATTERY_MONITOR=1` on v4. `STATUS` also emits `BATT,<v>,<pct>,<is_low>`;
`<v>` is the 1S cell voltage (~3.0–4.2 V, GPIO1 ÷2 divider).

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
