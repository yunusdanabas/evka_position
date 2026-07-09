# Firmware Code Walkthrough

A guided tour of `firmware/src/` for someone reading the code for the first time. Pair it with
[../ARCHITECTURE.md](../ARCHITECTURE.md) (the *what*) — this is the *where*.

Build target: PlatformIO env `wemos_d1_r32` (classic ESP32) or `esp32s3_v4` (v4 board). The pin map
is chosen by the `PCB_V4` macro; everything else is shared.

---

## The files

| File | Responsibility |
|---|---|
| `EvkaPosition.cpp` | **Entry point.** `setup()`, `loop()`, command dispatch, the 20 Hz update, WiFi status LED, ESP-NOW pendant receiver |
| `SphericalSensor.h` | **All configuration** (`#define`s), data structs, and the `SphericalPositioningSensor` class declaration |
| `SphericalSensor.cpp` | **The math + state:** encoder reads, coordinate conversion, EMA filter, validity checks, NVS calibration, battery |
| `WebDashboard.{h,cpp}` | WiFi AP/STA management, the web dashboard, and the WebSocket data/command channel |
| `CmdTcpServer.{h,cpp}` | The raw TCP "CMD protocol" server (what the Windows CMD app talks to) |
| `CMD Soft/` | The third-party Windows C# app + its original ESP32 firmware (reference, not built here) |

## Follow one update through the system

Everything hangs off `loop()` in `EvkaPosition.cpp`, which runs one update every
`UPDATE_PERIOD_MS` (50 ms → 20 Hz):

1. **`handleSerialCommands()`** — drains the serial buffer line by line and calls
   `processCommand()` for each complete line.
2. **ESP-NOW pendant** — if a button byte arrived, it's turned into a command string and also
   run through `processCommand()`, then the reply is broadcast to the dashboard + TCP.
3. **`dashboard.tick()`** and the WebSocket/TCP command drains — any command from a browser or TCP
   client goes through the same `processCommand()`.
4. **Position update** (`sensor.updatePosition()`):
   - `readRawEncoders()` → raw counts minus the zero offsets.
   - `countsToSpherical()` → applies `DEG_PER_PULSE` / `MM_PER_PULSE` and the sign constants.
   - `sphericalToCartesian()` → the `x=r·cosφ·cosθ …` formulas.
   - `validateLimits()` → NaN/range check sets `is_valid`.
   - EMA filter smooths the Cartesian output (skipped on invalid frames).
5. **Broadcast** — one `DATA,x,y,z,r,θ,φ,valid,frame,ts` line is formatted once and sent to serial,
   the WebSocket, and the TCP server.

So: **to change how position is computed**, edit `SphericalSensor.cpp`. **To change a command or the
loop**, edit `EvkaPosition.cpp`. **To change WiFi/dashboard**, edit `WebDashboard.cpp`.

## `EvkaPosition.cpp` — the conductor

- `setup()` — serial, `sensor.begin()`, (if `ENABLE_WIFI`) dashboard/TCP/ESP-NOW init, then a 2 s
  delay and `setZeroPoint()` (machine must be at home).
- `processCommand(const String&)` — the **one place** every command is handled, no matter which
  transport it arrived on. Returns a reply string. This is the function to read to learn the whole
  command surface (see [ARCHITECTURE.md §6](../ARCHITECTURE.md#6-command-reference-serial--tcp--websocket)).
- `loop()` — the sequence above, plus the WiFi-status-LED state machine (off = no STA, blink =
  connecting, solid = connected).

## `SphericalSensor.cpp` — the math

Read in this order:
- `begin()` — constructs the three `ESP32Encoder`s (pull-ups **off** — external dividers drive the
  pins), configures the battery ADC, loads PPR from NVS.
- `readRawEncoders()` → `countsToSpherical()` → `sphericalToCartesian()` — the core chain.
- `updatePosition()` — ties them together and applies the EMA filter + validity.
- `normalizeAngle()` / `validateLimits()` — the small helpers that keep output sane (angle wrap,
  NaN/range rejection).
- `loadPPRFromNVS()` / `savePPRToNVS()` — calibration persistence (namespace `evka_cal`, validated
  on load).
- `readBattery()` — ADC → volts → % (only compiled in when `ENABLE_BATTERY_MONITOR`).

Encoders are heap-allocated in `begin()`, **not** in the constructor — the ESP32 peripheral service
isn't ready during global construction.

## `WebDashboard` / `CmdTcpServer` — the transports

Both follow the same pattern: they receive bytes on their own callback, stash complete commands in a
small thread-safe queue, and `loop()` drains that queue into `processCommand()`. They never call
firmware logic directly from a network callback (that path was a source of crashes — see the
[WiFi/AsyncTCP troubleshooting docs](../README.md#troubleshooting--wifi--stability)). Both also
broadcast the 20 Hz data out.

## Where things live — quick lookups

| I want to… | Look at |
|---|---|
| Change a pin | `SphericalSensor.h` pin block (`#if defined(PCB_V4)`) |
| Add/change a command | `processCommand()` in `EvkaPosition.cpp` |
| Change the coordinate math | `sphericalToCartesian()` / `countsToSpherical()` in `SphericalSensor.cpp` |
| Flip an encoder direction | `ENCODER_THETA_SIGN` / `ENCODER_PHI_SIGN` in `SphericalSensor.h` |
| Change the update rate | `UPDATE_PERIOD_MS` in `EvkaPosition.cpp` |
| Change the dashboard/WiFi | `WebDashboard.cpp` |
| Change the CMD TCP protocol | `CmdTcpServer.cpp` + `docs/integration/CMD_SOFTWARE_INTEGRATION.md` |
