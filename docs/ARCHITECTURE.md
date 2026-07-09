# Architecture & Reference

The canonical "how it works" reference for evka_position. Complements the math in
[hardware_design/system_architecture.md](hardware_design/system_architecture.md) and the
source-code tour in [firmware/CODE_WALKTHROUGH.md](firmware/CODE_WALKTHROUGH.md).

> **Source of truth:** all pins, PPR values, and feature flags are `#define`s in
> `firmware/src/SphericalSensor.h`. If this doc and that header ever disagree, **the header wins** —
> update this doc.

---

## 1. The processing pipeline

Three layers, run every 50 ms (20 Hz) in `EvkaPosition.cpp::loop()`:

```
Encoder counts (raw int32, from hardware pulse counters)
        │  countsToSpherical()      × DEG_PER_PULSE / MM_PER_PULSE, × sign
        ▼
Spherical (r mm, θ deg, φ deg)
        │  sphericalToCartesian()   elevation-azimuth convention
        ▼
Cartesian (X, Y, Z mm)             + exponential moving-average filter (α = 0.2)
```

- **θ / φ:** Autonics E40S6-5000 quadrature encoders.
- **r:** OPKON DWEM2 draw-wire encoder (quadrature).
- All three are counted by the **`ESP32Encoder`** library using the ESP32 **hardware pulse
  counters (PCNT)** — no manual interrupt service routines.
- The filter is a per-axis EMA applied to the Cartesian output; invalid frames bypass it.

Implemented in `firmware/src/SphericalSensor.cpp`. See the walkthrough for the function-by-function tour.

## 2. Configuration (`SphericalSensor.h`)

Key compile-time constants (abbreviated — read the header for the full set + comments):

| Constant | Value | Meaning |
|---|---|---|
| `PPR_ROTARY` | 20000 | E40S6-5000 @ ×4 quadrature (5000 PPR × 4 edges) |
| `PPR_WIRE` | 8000 | DWEM2 theoretical; run `CAL_W` after mounting to calibrate |
| `DRUM_CIRCUM_MM` | 200 | Draw-wire drum circumference (mm/rev) |
| `DEG_PER_PULSE` | 360/PPR_ROTARY ≈ 0.018° | Angle per rotary count |
| `MM_PER_PULSE` | DRUM/PPR_WIRE = 0.025 mm | Distance per wire count |
| `ENCODER_THETA_SIGN` / `ENCODER_PHI_SIGN` | −1 / +1 | Mounting-dependent count→angle sign; flip if a direction is reversed |
| `RADIUS_MIN/MAX_MM` | 0 / 2950 | Radius range |
| `THETA_MIN/MAX_DEG` | ±180 | Azimuth range |
| `PHI_MIN/MAX_DEG` | ±180 | Elevation range |
| `ENABLE_WIFI` | 1 | Serial-only (0) vs serial + AP + dashboard (1) |
| `ENABLE_CMD_TCP` | 1 | Raw TCP CMD server on port 8080 |
| `ENABLE_ESPNOW_REMOTE` | 1 | 2-button wireless pendant |
| `ENABLE_BATTERY_MONITOR` | 1 | Battery ADC path (1S LiPo on v4) |
| `UPDATE_PERIOD_MS` | 50 | 20 Hz loop period (in `EvkaPosition.cpp`) |

## 3. Pin maps

Selected at build time by the `PCB_V4` macro (set via `-DPCB_V4` in the `esp32s3_v4` env).

**Classic ESP32 (env `wemos_d1_r32`):**

| θA/θB | φA/φB | rA/rB | Battery ADC | WiFi LED |
|---|---|---|---|---|
| 14 / 12 | 32 / 35 | 16 / 17 | 36 | 2 |

**v4 PCB — ESP32-S3 (env `esp32s3_v4`):** verified against the fabricated schematic + PCB.

| θA/θB | φA/φB | rA/rB | Battery ADC |
|---|---|---|---|
| 7 / 8 | 4 / 5 | 9 / 10 | 1 (1S LiPo, ÷2) |

v4 has no onboard buttons (GPIO17/18 unconnected) and no firmware LED (hardwired power LED only).
Full v4 detail: [../pcb_design/EVKA_position_v4/FIRMWARE.md](../pcb_design/EVKA_position_v4/FIRMWARE.md).

## 4. Coordinate convention

**Pan-tilt elevation-azimuth** (matches the physical device — *not* physics-spherical):

- **φ** = elevation from horizontal: −90° straight down, 0° horizontal, +90° straight up.
- **θ** = azimuth from +X in the XY-plane, wraps ±180°.
- `x = r·cos φ·cos θ`, `y = r·cos φ·sin θ`, `z = r·sin φ`.

`ENCODER_THETA_SIGN` / `ENCODER_PHI_SIGN` map quadrature counts to θ/φ before these formulas. If lift
drives −Z or forward drives −X at home, flip the corresponding sign and reflash.

## 5. Calibration workflow

1. Move the machine to mechanical home (zero extension, zero angles).
2. Power on — firmware auto-calls `setZeroPoint()` after a 2 s delay. All counts become relative.
3. Re-zero without reflashing: send `ZERO` (or `ZERO_T`/`ZERO_P`/`ZERO_W` per axis).
4. Calibrate PPR with `CAL_W`/`CAL_T`/`CAL_P`, apply with `SET_PPR_*`, persist with `SAVE_PPR`
   (stored in NVS flash, namespace `evka_cal`, survives reboot).

Step-by-step procedures: [calibration/](calibration/). Web CALIBRATE tab does the same guided flow.

## 6. Command reference (serial + TCP + WebSocket)

All commands are newline-terminated; replies mirror to serial and the active transport.

| Command | Reply | Purpose |
|---|---|---|
| `ZERO` / `ZERO_T` / `ZERO_P` / `ZERO_W` | `ACK:ZERO…` | Re-zero all / theta / phi / wire |
| `PING` | `ACK:PONG` | Liveness |
| `STATUS` | `STATUS,<valid>,<frame>,<ts>,<r>,<θ>,<φ>,<x>,<y>,<z>` | Full snapshot (+`BATT,…` if enabled) |
| `CONSTANTS` | `CONSTANTS,<ppr_rotary>,<ppr_wire>,<mm/pulse>,<deg/pulse>` | Current scale factors |
| `CAL_W <mm>` | `CAL:WIRE,<factor>,<mm/pulse>,<ppr>` | Wire calibration trial |
| `CAL_T <turns>` / `CAL_P <turns>` | `CAL:THETA/PHI,<counts>,<ppr>` | Angle calibration |
| `SET_PPR_WIRE <v>` / `SET_PPR_ROTARY <v>` | `ACK:PPR_…` | Update PPR in RAM |
| `SAVE_PPR` | `ACK:SAVE_PPR` | Persist PPR to NVS |
| `SAVE_POINT` / `DEL_POINT` | `POINT,…` / `DEL_POINT,<idx>` | Record / delete a captured point |
| `GET_IP` | `STA_IP:<ip>` | Router-mode IP |
| `SYSINFO` | `SYSINFO,<rssi>,<heap>,<uptime>,<clients>` | Diagnostics |
| `WIFI_SET:<ssid>,<pass>` | `ACK:WIFI_SAVED` | Set router creds + reboot |
| *(unknown)* | `ERR:UNKNOWN_CMD` | — |

Protocol details for the CMD app: [integration/CMD_SOFTWARE_INTEGRATION.md](integration/CMD_SOFTWARE_INTEGRATION.md).

## 7. Connectivity

- **WiFi AP** `CMDCNC_EVKA` / `cmdcnc1234`, dashboard at **`http://192.168.1.50`**, TCP CMD server at
  **`192.168.1.50:8080`**. The AP IP is **hardcoded** (the CMD app depends on it) and collides with
  common home routers — if unreachable, disconnect from other WiFi first.
- **Router (STA) mode:** static profile `192.168.1.84/24`, gw `192.168.1.254`; `GET_IP` reports it.
- **ESP-NOW pendant:** 2-button ESP32-C3, broadcasts + auto-discovers the AP channel by SSID
  (no MAC pairing) — works with any main board.

WiFi reliability is subtle; the fixes are documented under
[the troubleshooting docs](README.md#troubleshooting--wifi--stability).
