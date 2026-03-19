# Firmware Rework Log — Draw-Wire Encoder (DWE3000 Quadrature)
_Session: 2026-02-18_

> **Note (2026-03-09):** File paths in this log reflect the pre-reorganization layout.
> Current paths: `firmware/src/` (production), `firmware/tests/` (test sketches).

---

## Summary

The original firmware treated the draw-wire encoder as a single-channel clock + direction pin.
The OPKON DWE3000 is a full quadrature encoder (A, B, Z channels).
GPIO 6/7 were also on the flash-reserved range of ESP32-WROOM-32.
This rework corrects both issues.

---

## Files Changed

### 1. `firmware/DrawWireTest/DrawWireTest.cpp` — Full rewrite

**Before:** ISR on clock pin (GPIO 6), direction read from GPIO 7, PPR=1000, MM_PER_PULSE=1.0

**After:** Encoder library on GPIO 16/17 (quadrature A/B), Z-index ISR on GPIO 18,
PPR=2000, MM_PER_PULSE=0.1

Key changes:
- `#include <Encoder.h>` added
- Heap-allocated `Encoder* wireEnc = new Encoder(PIN_WIRE_A, PIN_WIRE_B)` replaces ISR
- `PIN_WIRE_CLK 6` / `PIN_WIRE_DIR 7` → `PIN_WIRE_A 16` / `PIN_WIRE_B 17`
- `PPR_WIRE 1000` → `2000`
- `MM_PER_PULSE = 1000.0/1000.0 = 1.0` → `DRUM_CIRCUM_MM/PPR_WIRE = 200.0/2000.0 = 0.1`
- Z index channel added: `volatile uint32_t z_count = 0; void IRAM_ATTR zISR()`
- Serial output now: `COUNT=<n>  DIST_mm=<n*0.1>  Z_ticks=<z_count>`

---

### 2. `firmware/EvkaPosition/SphericalSensor.h` — Three edits

#### Pin definitions
```cpp
// Removed:
#define PIN_WIRE_CLK  6
#define PIN_WIRE_DIR  7

// Added:
#define PIN_WIRE_A    16    // Quadrature A (safe GPIO on ESP32-WROOM-32)
#define PIN_WIRE_B    17    // Quadrature B
```

#### Encoder specs
```cpp
// Before:
#define PPR_WIRE      1000.0
#define MM_PER_PULSE  (1000.0 / PPR_WIRE)   // = 1.0 mm/pulse

// After:
#define PPR_WIRE        2000.0
#define DRUM_CIRCUM_MM   200.0
#define MM_PER_PULSE   (DRUM_CIRCUM_MM / PPR_WIRE)   // = 0.1 mm/pulse
```

#### Safety limit
```cpp
// Before:
#define RADIUS_MAX_MM   5000.0

// After:
#define RADIUS_MAX_MM   3000.0   // DWE3000 stroke limit
```

#### Class private section
```cpp
// Added:
Encoder wireEncoder;   // alongside thetaEncoder and phiEncoder
```

---

### 3. `firmware/EvkaPosition/SphericalSensor.cpp` — Four edits

#### Removed global ISR block (was lines 3–10)
```cpp
// DELETED:
volatile int32_t wire_pulse_count = 0;
void IRAM_ATTR wireEncoderISR() {
    int direction = digitalRead(PIN_WIRE_DIR) ? 1 : -1;
    wire_pulse_count += direction;
}
```

#### Constructor — added wireEncoder to initializer list
```cpp
// Before:
SphericalPositioningSensor::SphericalPositioningSensor()
    : thetaEncoder(PIN_THETA_A, PIN_THETA_B),
      phiEncoder(PIN_PHI_A, PIN_PHI_B),
      ...

// After:
SphericalPositioningSensor::SphericalPositioningSensor()
    : thetaEncoder(PIN_THETA_A, PIN_THETA_B),
      phiEncoder(PIN_PHI_A, PIN_PHI_B),
      wireEncoder(PIN_WIRE_A, PIN_WIRE_B),   // ADDED
      ...
```

#### `begin()` — removed ISR setup
```cpp
// Before:
void SphericalPositioningSensor::begin() {
    pinMode(PIN_WIRE_CLK, INPUT_PULLUP);
    pinMode(PIN_WIRE_DIR, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_WIRE_CLK), wireEncoderISR, RISING);
    Serial.println("[SphericalSensor] Initialized");
}

// After:
void SphericalPositioningSensor::begin() {
    // Encoder library handles pin modes and interrupts internally
    Serial.println("[SphericalSensor] Initialized");
}
```

#### `setZeroPoint()` and `readRawEncoders()`
```cpp
// Before:
radius_offset = wire_pulse_count;
radius_counts = wire_pulse_count - radius_offset;

// After:
radius_offset = wireEncoder.read();
radius_counts = wireEncoder.read() - radius_offset;
```

---

## Files NOT Changed in This Phase

- `firmware/EvkaPosition/EvkaPosition.cpp`
- `firmware/RotaryEncoderTest/RotaryEncoderTest.cpp`
- Python tools

---

---

# Firmware Rework Log — Phase 3: Phi Pin Remap
_Session: 2026-02-21_

---

## Problem

`PIN_PHI_A` was assigned to GPIO 3 (UART0 RX on ESP32). With Serial active at
115200 baud, UART receive traffic toggled GPIO 3, injecting false phi encoder
counts and corrupting position data.

`PIN_PHI_B` was on GPIO 5, a strapping pin — moved proactively.

---

## Changes

### `firmware/EvkaPosition/SphericalSensor.h` — two defines
```cpp
// Before:
#define PIN_PHI_A     3   // TODO: Remap to GPIO 27 (GPIO 3 = UART0 RX conflict)
#define PIN_PHI_B     5   // TODO: Remap to GPIO 26

// After:
#define PIN_PHI_A     27  // safe GPIO (was GPIO 3)
#define PIN_PHI_B     26  // safe GPIO (was GPIO 5)
```

### `firmware/RotaryEncoderTest/RotaryEncoderTest.cpp`
Updated wiring comment and `#define PIN_PHI_A/B` to match.

---

## Hardware Action Required

Rewire phi encoder: move wire A from GPIO 3 voltage-divider output to GPIO 27 divider
output. Move wire B from GPIO 5 output to GPIO 26 output. Divider circuits unchanged.

---

## Files NOT Changed in This Phase

- `firmware/EvkaPosition/SphericalSensor.cpp`
- `firmware/EvkaPosition/EvkaPosition.cpp`
- `firmware/DrawWireTest/DrawWireTest.cpp`
- Python tools

---

---

# Firmware Rework Log — Phase 4: PlatformIO Migration & PPR Correction
_Session: 2026-02-26_

---

## Summary

Migrated all firmware from `.ino` to `.cpp` for PlatformIO compatibility, corrected
PPR_ROTARY from datasheet 5000 to measured 1480, restructured test directories out
of `firmware/tests/` to `firmware/`, and switched all Encoder objects to heap
allocation (ESP32 GPIO ISR service not ready during global construction).

---

## Changes

### `.ino` → `.cpp` migration
All firmware files renamed from `.ino` to `.cpp`:
- `EvkaPosition.ino` → `EvkaPosition.cpp`
- `DrawWireTest.ino` → `DrawWireTest.cpp`
- `RotaryEncoderTest.ino` → `RotaryEncoderTest.cpp`

### Test directory restructuring
- `firmware/tests/DrawWireTest/` → `firmware/DrawWireTest/`
- `firmware/tests/RotaryEncoderTest/` → `firmware/RotaryEncoderTest/`
- New: `firmware/SingleRotaryTest/` — single encoder test

### PPR correction
- `PPR_ROTARY`: 5000.0 → 1480.0 (measured counts/rev)
- `DEG_PER_PULSE`: 0.072 → ~0.2432 (360/1480)
- Datasheet specifies 5000 PPR; measured value on hardware is 1480

### Heap-allocated Encoder objects
All Encoder objects changed from stack to heap allocation in `begin()`:
```cpp
// Before (global construction — crashes on ESP32):
Encoder thetaEncoder(PIN_THETA_A, PIN_THETA_B);

// After (heap in begin() — ISR service ready):
thetaEncoder = new Encoder(PIN_THETA_A, PIN_THETA_B);
```

---

## Files NOT Changed in This Phase

- Python tools
- Hardware documentation (updated separately)

---

---

# Firmware Rework Log — Phase 5: PPR Calibration Correction (X4 Quadrature)
_Session: 2026-03-11_

---

## Summary

`PPR_ROTARY` corrected from 1480 (incorrect single-edge measurement) to 20000 (correct X4 quadrature: 5000 PPR × 4 edges). `PPR_WIRE` calibrated from datasheet 2000 to 8020 using a 400 mm reference pull (firmware read 1604 mm). Interactive `CalibrationTest.cpp` created.

---

## Changes

### PPR_ROTARY: 1480.0 → 20000.0

The PaulStoffregen Encoder library counts all 4 quadrature edges. The E30S6-5000 has 5000 PPR per channel; at X4: 5000 × 4 = 20000 counts/rev. The previous value of 1480 was an erroneous single-edge measurement.

```cpp
// Before:
#define PPR_ROTARY      1480.0  // Measured counts/rev (Autonics E40S6)
// After:
#define PPR_ROTARY      20000.0  // E30S6-5000 @ X4 quadrature (5000 PPR × 4)
```

Files updated:
- `firmware/src/SphericalSensor.h`
- `firmware/tests/RotaryEncoderTest/RotaryEncoderTest.cpp`
- `firmware/tests/AllSensorsTest/AllSensorsTest.cpp`
- `firmware/tests/SingleRotaryTest/SingleRotaryTest.cpp`

### PPR_WIRE: 2000.0 → 8020.0

Calibrated by pulling wire exactly 400 mm; firmware reported 1604 mm.
- Correction factor: 400 / 1604 = 0.24938
- New `MM_PER_PULSE` = 0.1 × 0.24938 = 0.024938
- New `PPR_WIRE` = 200 / 0.024938 = 8020

```cpp
// Before:
#define PPR_WIRE        2000.0
// After:
#define PPR_WIRE        8020.0  // Calibrated — actual 400mm → firmware read 1604mm
```

Files updated:
- `firmware/src/SphericalSensor.h`
- `firmware/tests/DrawWireTest/DrawWireTest.cpp`
- `firmware/tests/AllSensorsTest/AllSensorsTest.cpp`

### New: `calibration/CalibrationTest.cpp`

All-in-one interactive calibration sketch (project root). Commands:
- `CAL_T` / `CAL_P` — interactive rotary cal: press SPACE each full turn, `DONE` to finalize
- `CAL_W <mm>` — wire cal: `ZERO_W`, pull known distance, send `CAL_W <mm>`
- `STATUS`, `CONSTANTS`, `DIAG`, `CANCEL`

PlatformIO env `test_calibration` added to `platformio.ini` (`build_src_filter = +<../calibration/>`).

### Extended: `firmware/tests/DrawWireTest/DrawWireTest.cpp`

Added `ZERO_W` and `CAL_W <actual_mm>` commands. Runtime `mm_per_pulse` variable replaces compile-time `#define MM_PER_PULSE`.

---

## Files NOT Changed in This Phase

- `firmware/src/SphericalSensor.cpp`
- `firmware/src/EvkaPosition.cpp`
- Python tools
