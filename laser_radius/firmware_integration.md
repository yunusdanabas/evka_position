# Firmware Integration — Laser Radius Variant

**Parent doc:** [`README.md`](README.md). Covers ESP32-S3 interface options, 20 Hz loop feasibility, BLE+WiFi coexistence for Version A, and a `LaserRadiusSensor` API sketch. **No firmware is implemented here — sketch/design only, per task scope.**

**Fixed requirement (2026-07-01, revised):** ≤40 m range, ≤10 mm laser accuracy, no tiers — see `version_a_handheld_devices.md` / `version_b_integrated_modules.md` for the current shortlist (JRT B605B, Meskernel LDL-T, Bosch PLR 40 C, Dimetix D-series). The interface options below are unaffected by the spec change; only the specific device examples are updated.

---

## 1. ESP32-S3 Interface Options

| Interface | Used by | Hardware needed | Notes |
|---|---|---|---|
| **UART TTL direct** | JRT B605B (TTL variant), any device with native 3.3–5V logic UART | None beyond wiring — ESP32-S3 UART pins are 3.3V, confirm device logic level (some run at up to 5V TTL — check before connecting) | Simplest path. Any two free GPIOs via the ESP32-S3 GPIO matrix; the freed wire-encoder pins (GPIO 15/16) are the natural choice in this variant since draw-wire is removed. |
| **RS232 level-shifted** | Dimetix D-series (single-device RS232 mode), JRT B605B RS232 variant, Meskernel LDL-T | MAX3232-class level shifter (small breakout, not currently on the carrier PCB — new addition) | RS232 swings ±5–12V; must not be wired directly to ESP32-S3 GPIOs (not 5V-tolerant, per the as-built board's own AUX-header warning in `circuit_schematic.md`). Route through the level shifter into a free UART pair (e.g., AUX header GPIO 11/12 or the freed wire pins). |
| **RS-485/RS422 half-duplex** | Meskernel LDL-T (RS485 mode), Dimetix D-series (RS422 multi-drop mode) | MAX485-class transceiver (RS-485) or RS422-specific transceiver e.g. MAX3095/MAX489 family (RS422) — not currently on the carrier PCB, new addition either way | See `version_b_integrated_modules.md` §4 for the as-built GPIO correction (13/14 = AUX header TX/RX, 15 = DE/RE, since GPIO 18 is already BTN2 on the current board) and the RS422-vs-RS485 transceiver distinction. Note: unlike the excluded TF02-i, none of the current recommended devices use Modbus RTU — they use proprietary ASCII protocols. |
| **BLE central (GATT)** | Bosch PLR 40 C (Version A fallback) — **BLE 4.2 GATT confirmed** | None — ESP32-S3 has native BLE 5 | **Bluetooth type confirmed (2026-07-09):** Bosch's official manual states "Bluetooth 4.2 (Low Energy)" and "must support the GATT profile." ESP32-S3 is BLE-only, perfect match. Service UUID `02a6c0d0-0451-4000-b000-fb3210111989`, characteristic `02a6c0d1-0451-4000-b000-fb3210111989`. Protocol decrypted from GLM family (CRC-8, IEEE 754 float), but **not yet verified on physical PLR 40 C** — one capture session required before firmware work. Use **NimBLE-Arduino** stack. See [`bosch_plr_40c_integration.md`](bosch_plr_40c_integration.md) for full details, UUIDs, and code sketches. See §3 below for radio coexistence with the existing WiFi AP+STA stack. |

## 2. Bosch PLR 40 C Protocol (decrypted from GLM family, not yet verified on PLR 40 C)

**Bluetooth type: CONFIRMED — BLE 4.2 GATT** (Bosch official manual, 2026-07-09). ESP32-S3 compatible (BLE-only chip matches BLE-only device).

**Protocol status:** Decrypted from Bosch GLM devices (GLM 50C/50CG/120C) via community reverse-engineering. Assumed to work across the GLM/PLR family, but **not yet verified on a physical PLR 40 C unit**. One real-device capture session required before firmware work.

### 2.1 BLE GATT Profile

| UUID Function | Identifier |
|---|---|
| **Service UUID** | `02a6c0d0-0451-4000-b000-fb3210111989` |
| **TX/Indicate Characteristic** | `02a6c0d1-0451-4000-b000-fb3210111989` |
| **RX/Write Characteristic** | (Often unified with TX characteristic) |

**Connection pattern:**
1. Scan for service UUID `02a6c0d0-0451-4000-b000-fb3210111989`
2. Connect, discover characteristic `02a6c0d1-0451-4000-b000-fb3210111989`
3. Subscribe to **indications** (requires acknowledgment)
4. Write commands to the same characteristic
5. Parse indication responses

### 2.2 Frame Format

```
Send frame:    [0xC0][command][length][data...][CRC-8]
Receive frame: [0xC0][status][length][data...][CRC-8]
```

### 2.3 Command Table

| Command | Hex Payload | Description |
|---------|-------------|-------------|
| **Continuous Sync** | `C0 55 02 01 00 1A` | Enable continuous data streaming (~4 Hz) |
| **Single Measurement** | `C0 40 00 EE` | Trigger one distance measurement |
| **Laser On** | `C0 41 00 96` | Turn laser pointer on |
| **Laser Off** | `C0 42 00 1E` | Turn laser pointer off |
| **Backlight On** | `C0 47 00 20` | Turn display backlight on |
| **Backlight Off** | `C0 48 00 62` | Turn display backlight off |

### 2.4 Response Parsing (Continuous Sync Mode)

In continuous sync mode, the device transmits **20-byte response arrays** via BLE indications.

**Distance extraction:**
- Bytes **7, 8, 9, 10** (0-indexed) contain the distance
- **Little-endian IEEE 754 Single-Precision (32-bit) Floating-Point**
- Example: bytes `[162, 180, 151, 62]` → `0x3E97B4A2` → `0.294 m` (294 mm)

**C++ parsing:**
```cpp
float parseDistance(const uint8_t* data, size_t length) {
    if (length < 11 || data[0] != 0xC0) return -1.0f;
    uint32_t raw = (uint32_t)data[10] << 24 | (uint32_t)data[9] << 16 |
                   (uint32_t)data[8] << 8 | (uint32_t)data[7];
    float distance_m;
    memcpy(&distance_m, &raw, sizeof(float));
    return distance_m * 1000.0f;  // convert to mm
}
```

### 2.5 CRC-8 Checksum (Bosch-Specific)

Custom CRC-8 algorithm (not standard):
- **Initialization Vector:** `0xAA`
- **Polynomial:** `0xA6`
- **Input/Output Reflection:** False

```cpp
uint8_t calculateBoschCRC8(const uint8_t* data, size_t length) {
    uint8_t crc = 0xAA;
    for (size_t i = 0; i < length; i++) {
        uint8_t b = data[i];
        for (int j = 0; j < 8; j++) {
            uint8_t x = ((crc >> 7) ^ (b >> (7 - j))) & 1;
            crc = (crc << 1) & 0xFF;
            if (x) crc ^= 0xA6;
        }
    }
    return crc;
}
```

### 2.6 Status Codes

| Code | Meaning |
|------|---------|
| 0 | OK |
| 1 | Communication timeout |
| 3 | Checksum error |
| 4 | Unknown command |
| 5 | Invalid access level |
| 8 | Hardware error |
| 10 | Device not ready |

**Full integration analysis, ESP32-S3 NimBLE code sketches, and risk assessment:** [`bosch_plr_40c_integration.md`](bosch_plr_40c_integration.md).

---

## 3. 20 Hz Loop Feasibility

The firmware's main loop runs at `UPDATE_PERIOD_MS = 50` (20 Hz, `EvkaPosition.cpp`). All wired interfaces (UART/RS232/RS-485/RS422) can be polled well within that budget — their own max sample rates range from ~3–8 Hz (JRT B605B slow/high-accuracy mode) up to 100 Hz (Meskernel LDL-T; corrected 2026-07-08 from an earlier 30 Hz figure) and 50 Hz (Dimetix DAE). The mismatch only matters for the **slower** end:

- **Devices at or faster than 20 Hz** (Meskernel LDL-T at 100 Hz, Dimetix at 20–50 Hz): straightforward — issue a serial read once per 50 ms tick, non-blocking, same pattern as the current encoder read.
- **Devices slower than 20 Hz** (JRT B605B ~8 Hz fast mode, or 0.25–8 Hz in high-accuracy mode): the firmware must **not block** the 50 ms loop waiting for a new sample. Recommended pattern — a small non-blocking state machine per tick:
  1. If no request in flight and enough time has elapsed since the last sample, send a trigger/request.
  2. Each tick, poll the UART RX buffer for a complete response (non-blocking `available()` check, not a blocking read).
  3. On a complete frame, update `r_raw_mm` and timestamp; otherwise, **hold the last valid value** — the same "hold-last-value" pattern the codebase already uses for degraded encoder data, not a new concept.
  4. `isValid()` returns false if the last successful sample is older than a timeout (e.g., 2–3× the device's expected sample interval), following the existing staleness-detection philosophy in `SphericalSensor`.

This means the 20 Hz *loop* rate is unaffected regardless of device speed — only the *effective radius update rate* varies by device, which is already how the system's `is_valid` / staleness concept is designed to be consumed downstream.

## 4. BLE + WiFi Coexistence (Version A Fallback Only — if PLR 40 C is BLE)

The ESP32-S3 has a single 2.4 GHz radio shared between WiFi and Bluetooth — WiFi/BT coexistence is handled by the IDF's time-division scheduler, not two independent radios. This is a well-known ESP-IDF constraint, not specific to this project, but it directly affects the Bosch PLR 40 C fallback path, since the current firmware already runs WiFi AP+STA concurrently (`ENABLE_WIFI=1` default, per `docs/ARCHITECTURE.md`).

**Practical implications:**
- Adding a BLE GATT central role (to read the Bosch PLR 40 C) means three radio roles time-sharing one antenna: WiFi AP, WiFi STA, BLE central. Each one's throughput/latency degrades somewhat when the others are active — documented ESP-IDF behavior, not a bug to "fix."
- Recommended library: **NimBLE-Arduino** (lighter RAM/flash footprint than the Arduino BLE stack, better suited to running alongside the existing AsyncTCP/WebSocket/WiFi stack that's already tight on stack budget — see `docs/ASYNCTCP_STACK_OVERFLOW_ANALYSIS.md` for the existing stack-sizing precedent this project already has to manage).
- **The Bosch PLR 40 C is a manual-trigger device anyway** (§2.3 of `version_a_handheld_devices.md`) — a human aims and fires it, at most ~1 Hz. This actually works in this path's favor: the BLE fallback never needs to sustain 20 Hz, so coexistence latency spikes are far less punishing here than they would be for a continuous-streaming device.
- **Must be measured empirically, not assumed** — before committing to this fallback path for anything beyond occasional manual verification, bench-test actual GATT notification latency with WiFi AP+STA simultaneously active.

## 5. `LaserRadiusSensor` API Sketch (design only, not implemented)

Mirrors the shape of the existing `SphericalSensor` class so it can later replace the draw-wire branch of `readRawEncoders()` / `update()` without touching the theta/phi encoder code:

```cpp
// laser_radius/ — design sketch only, not implemented in firmware/src/
class LaserRadiusSensor {
public:
    void begin();                    // configure UART/RS-485/BLE per LASER_INTERFACE_MODE
    void update();                    // non-blocking poll, called once per 50ms loop tick — see §2
    float getRadiusMM() const;        // last valid r_offset-corrected radius (r_true_mm, see kinematics_and_calibration.md §1.1)
    bool  isValid() const;            // false if stale (timeout) or below device blind-zone floor
    uint32_t getLastUpdateMs() const; // for staleness/timeout detection, mirrors existing frame_count/ts_ms pattern

    // Calibration — replaces CAL_W / PPR_WIRE, see kinematics_and_calibration.md §3
    void  calibrateAt(float known_ref_mm);   // CAL_R command support
    void  setOffsetMM(float v);              // SET_R_OFFSET command support
    float getOffsetMM() const;
    void  saveToNVS();                       // SAVE_R command support — evka_cal namespace, r_offset key
};
```

**Integration point:** `SphericalSensor::update()` currently derives `r` from the draw-wire's raw counts. In this variant, the wire-encoder branch would be replaced with a call to `LaserRadiusSensor::update()` + `getRadiusMM()`, leaving the theta/phi `Encoder`-library code and `sphericalToCartesian()` untouched — the class boundary keeps the blast radius of this variant contained to one source module, matching how the draw-wire code is already isolated today.

## 6. Authoritative Wiring Guidance (Recap)

For implementers: the single source of truth for GPIO assignment in this variant is `version_b_integrated_modules.md` §4 (RS-485/RS422 path) and §1 above (UART/RS232 path) — both reflect the **current as-built** `EVKA_position_v2` 5V board, not the older `12v_legacy/v2` pin plan the original brief cited. Freed pins from draw-wire removal (GPIO 15/16) and the existing AUX header (GPIO 11/12/13/14) cover every interface option in this document without needing new GPIO territory — only new *transceiver hardware* (MAX3232 for RS232, MAX485/RS422-transceiver for the differential path) is a genuinely new PCB addition, pending PCB-owner review.

## Open Risks

1. **No firmware exists yet** — this is a design sketch; actual latency, buffer sizing, and stack usage for any interface (especially BLE + WiFi concurrent) are unverified until bench-tested.
2. **BLE + AsyncTCP/WebSocket stack coexistence is unverified** — this project has prior, well-documented stack-overflow issues under WiFi+WebSocket load alone (`docs/ASYNCTCP_STACK_OVERFLOW_ANALYSIS.md`); adding a BLE central role is new territory and should be treated as a stack-budget risk, not assumed safe.
3. **Hold-last-value semantics for slow devices (§2) need a concrete timeout constant**, not yet chosen — too short causes false invalidation on a slightly slow but healthy device, too long masks a genuinely stuck sensor.
4. **The `LaserRadiusSensor` API sketch has not been validated against any specific device's real command/response timing** — it's a shape, not a proven interface.

## Next Physical Test Steps

1. Bench-test one wired candidate (UART or RS-485) end-to-end on a bare ESP32-S3 dev board before touching the carrier PCB, to validate the non-blocking poll pattern from §2.
2. If pursuing the BLE fallback, run a WiFi AP+STA + BLE-central coexistence latency test in isolation (dedicated test sketch, not the production firmware) to get real numbers before deciding whether it's viable beyond occasional manual use.
3. Prototype the `LaserRadiusSensor` class against whichever device is bench-tested first, and measure actual achievable update rate vs. the device's spec sheet claim.
4. Once real numbers exist, revisit the hold-last-value timeout constant (Open Risk #3) with actual jitter data instead of a guess.

---

*Part of the [laser radius detailed study](README.md). Docs-only — no firmware or PCB changes.*
