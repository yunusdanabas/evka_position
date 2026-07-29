# Firmware Code Walkthrough

A guided tour of `firmware/src/` for someone reading the code for the first time. Pair it with
[../ARCHITECTURE.md](../ARCHITECTURE.md) for the runtime design and
[../PROTOCOL.md](../PROTOCOL.md) for the canonical wire contract.

This is prototype source navigation, not a hardware-verification record.

Build target: PlatformIO env `wemos_d1_r32` (classic ESP32) or `esp32s3_v4` (v4 board). The pin map
is chosen by the `PCB_V4` macro; everything else is shared.

---

## The files

| File | Responsibility |
|---|---|
| `EvkaPosition.cpp` | **Entry point.** `setup()`, `loop()`, command dispatch, the 20 Hz update, and ESP-NOW pendant receiver |
| `SphericalSensor.h` | **All configuration** (`#define`s), data structs, and the `SphericalPositioningSensor` class declaration |
| `SphericalSensor.cpp` | **The math + state:** encoder reads, coordinate conversion, EMA filter, validity checks, NVS calibration, battery |
| `StatusLed.{h,cpp}` | Classic GPIO2 and v4 RGB status state machine |
| `WebDashboard.{h,cpp}` | WiFi AP/STA management, the web dashboard, and the WebSocket data/command channel |
| `CmdTcpServer.{h,cpp}` | Retained TCP compatibility server on port 8080 |

Historical vendor C# material has been deleted from the repository. It is not a
runtime component; the TCP protocol remains.

## Follow one update through the system

Everything hangs off `loop()` in `EvkaPosition.cpp`, which runs one update every
`UPDATE_PERIOD_MS` (50 ms → 20 Hz):

1. **`handleSerialCommands()`** - drains the serial buffer line by line and calls
   `executeCommand()` for each complete line; that wrapper prints exactly one primary reply.
2. **ESP-NOW pendant** - if a button byte arrived, it is turned into a command string and run through
   `executeCommand()`, then the reply is broadcast to the dashboard + TCP.
3. **`dashboard.tick()`** and the WebSocket/TCP command drains - queued commands go through the same
   `executeCommand()` wrapper. TCP still handles `GET_IP` directly for its requesting client.
4. **Position update** (`sensor.updatePosition()`):
   - `readRawEncoders()` → raw counts minus the zero offsets.
   - `countsToSpherical()` → applies `DEG_PER_PULSE` / `MM_PER_PULSE` and the sign constants.
   - `sphericalToCartesian()` → the `x=r·cosφ·cosθ …` formulas.
   - `validateLimits()` → NaN/range check sets `is_valid`.
   - EMA filter smooths the Cartesian output (skipped on invalid frames).
5. **Broadcast** - `DATA,x,y,z,r,theta,phi,valid,frame,ts` goes to Serial and WebSocket. TCP emits
   separate `X...,Y...,Z...` and `SENSOR,...` lines. See the
   [telemetry matrix](../PROTOCOL.md#telemetry-transport-matrix).

So: **to change how position is computed**, edit `SphericalSensor.cpp`. **To change a command or the
loop**, edit `EvkaPosition.cpp`. **To change WiFi/dashboard**, edit `WebDashboard.cpp`.

## `EvkaPosition.cpp` — the conductor

- `setup()` — serial, `sensor.begin()`, (if `ENABLE_WIFI`) dashboard/TCP/ESP-NOW init, then a 2 s
  delay and `setZeroPoint()` (machine must be at home).
- `processCommand(const String&)` - builds one primary success/error reply without transport I/O.
- `executeCommand(String)` - prints that primary reply once to Serial and adds `BATT,...` for
  `STATUS`; ingress code then handles network fan-out. TCP handles `GET_IP` directly before
  forwarding other commands. See
  [PROTOCOL.md](../PROTOCOL.md#current-commands-and-replies).
- `loop()` - the sequence above plus status LED updates and transport-specific fan-out.

## `SphericalSensor.cpp` — the math

Read in this order:
- `begin()` — constructs the three `ESP32Encoder`s (pull-ups **off** — external dividers drive the
  pins), configures the battery ADC, loads PPR from NVS.
- `readRawEncoders()` -> `countsToSpherical()` -> `sphericalToCartesian()` - the core chain.
  `readRawEncoders()` subtracts zero offsets, so `RAW_COUNTS` is zero-relative.
- `updatePosition()` — ties them together and applies the EMA filter + validity.
- `normalizeAngle()` / `validateLimits()` — the small helpers that keep output sane (angle wrap,
  NaN/range rejection).
- `loadPPRFromNVS()` / `savePPRToNVS()` - calibration persistence (namespace `evka_cal`, range
  checked on load and read-back verified on save).
- `readBattery()` — ADC → volts → % (only compiled in when `ENABLE_BATTERY_MONITOR`).

Encoders are heap-allocated in `begin()`, **not** in the constructor — the ESP32 peripheral service
isn't ready during global construction.

## `WebDashboard` / `CmdTcpServer` — the transports

Both receive network data, queue complete commands, and let `loop()` call `processCommand()` rather
than running sensor logic in callbacks. Their telemetry differs: WebSocket receives `DATA,...`, while
TCP receives separate XYZ and `SENSOR` lines. Reply fan-out and transport-specific queue/frame errors
are documented in [PROTOCOL.md](../PROTOCOL.md#reply-fan-out).

## Host Frame Boundary

Firmware emits the sensor frame only. `tools/evka_gui` is the canonical GUI and does not apply an
endpoint/world transform to live data. Its software zero is a display/session offset. An explicitly
supplied passing session JSON affects only the legacy `position_checker` visualizer and must not be
described as canonical world-frame acceptance.

## Where things live — quick lookups

| I want to… | Look at |
|---|---|
| Change a pin | `SphericalSensor.h` pin block (`#if defined(PCB_V4)`) |
| Add/change a command | `processCommand()` in `EvkaPosition.cpp` |
| Change the coordinate math | `sphericalToCartesian()` / `countsToSpherical()` in `SphericalSensor.cpp` |
| Flip an encoder direction | `ENCODER_THETA_SIGN` / `ENCODER_PHI_SIGN` in `SphericalSensor.h` |
| Change the update rate | `UPDATE_PERIOD_MS` in `EvkaPosition.cpp` |
| Change the dashboard/WiFi | `WebDashboard.cpp` |
| Change the TCP protocol | `EvkaPosition.cpp`, `CmdTcpServer.cpp`, and `docs/PROTOCOL.md` |
| Change v4/classic LED behavior | `StatusLed.cpp` plus the LED defines in `SphericalSensor.h` |
