# Improvement Research — evka_position

**Comprehensive catalog of all improvement opportunities for the ESP32 Spherical 3D Positioning System.**

This document is the unified index and prioritized roadmap for system enhancements. Where a standalone deep-dive doc already exists in the repo, this file summarizes the key points and cross-references it — it does not duplicate that content. New areas not yet covered by existing docs are described in full here.

**Evaluation criteria used throughout:**
- **Impact** (1–5): benefit to accuracy, reliability, or usability
- **Difficulty** (1–5): implementation effort on ESP32/PlatformIO stack
- **Feasibility**: Yes / Partial / No — whether the ESP32 hardware supports it natively

---

## 1. Current System Baseline

### 1.1 Architecture Snapshot

| Layer | Current State | Known Limitation |
|---|---|---|
| Encoder interface | PaulStoffregen `Encoder` library (ISR-based) | ISR contention under heavy WiFi; max reliable rate ~200kHz per channel |
| Coordinate math | `countsToSpherical()` → `sphericalToCartesian()` | Single-precision float only; no intermediate error propagation |
| Filter | Fixed-alpha EMA on Cartesian output (α=0.2) | `SphericalSensor.cpp:138-141` — no velocity adaptation, no spherical-space filtering |
| Validation | Binary `is_valid` flag | `SphericalSensor.cpp:114-121` — no confidence level, no degraded-accuracy mode |
| Architecture | Single-threaded `millis()` loop at 20Hz | `EvkaPosition.cpp:109` — Core 0 fully idle, no task partitioning |
| Calibration | Compile-time constants (`PPR_WIRE`, `PPR_ROTARY`) | Lost on power cycle; no runtime correction curve |
| Velocity | Not estimated | No derivative term — velocity/acceleration unavailable to filter or host |
| Health monitoring | None | Stale encoder data on cable disconnect goes undetected indefinitely |
| Communication | Serial CSV + optional WiFi WebSocket | No ROS2 integration, no binary protocol, no SD logging |
| Visualization | `tools/position_checker/gui.py` (pyqtgraph) + optional web canvas | 2D projection in web dashboard; no error ellipsoid |

### 1.2 ESP32 Resource Budget (WROOM-32)

| Resource | Total | App Budget | Notes |
|---|---|---|---|
| SRAM | 520 KB | ~160 KB | Remaining after WiFi stack (~130KB) + BT (off) |
| Flash | 4 MB | ~3.5 MB | 512KB NVS partition available |
| CPU | 240 MHz dual-core Xtensa LX6 | Core 0 idle | Core 0 runs WiFi in background |
| FPU | Single-precision | Full use | No double-precision hardware |
| Hardware counters | 8× PCNT units | Unused | Up to 40 MHz count rate |
| ADC | 18 channels (ADC1: GPIO 32-39) | GPIO 36 used (battery) | GPIO 39 available for NTC |

---

## 2. Filtering & Signal Processing

### 2.1 Adaptive EMA Filter

**Current state:** Fixed alpha=0.2 applied to Cartesian X, Y, Z after spherical→Cartesian conversion (`SphericalSensor.cpp:138-141`).

**Problem:** A fixed alpha creates a static trade-off — low alpha smooths noise but adds lag during fast motion; high alpha tracks fast motion but passes through noise.

**Solution — velocity-dependent alpha:**

```
v = |Δcounts| / Δt            // encoder velocity (counts/s)
α = α_min + (α_max − α_min) × min(1, v / v_threshold)
```

Typical values: `α_min = 0.05`, `α_max = 0.5`, `v_threshold = 500 counts/s`.

The velocity estimate is derived cheaply from the difference of successive raw count readings — no extra sensors required.

**Architecture note:** Filter should be applied in spherical space (r, θ, φ separately) before conversion to Cartesian, not after. Filtering X, Y, Z independently introduces trig coupling artifacts — a jump in θ changes X and Y simultaneously, but the EMA treats them as independent signals. Pre-filtering each spherical channel avoids this.

**Implementation:** ~30 lines in `SphericalSensor.cpp`; no external library needed.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 4 | 2 | Yes | 2–4h |

---

### 2.2 Standard Kalman Filter (6-State)

**State vector:** `[r, θ, φ, ṙ, θ̇, φ̇]ᵀ` — position and velocity in spherical coordinates.

**Process model (constant velocity):**

```
x[k+1] = F × x[k] + w[k]

F = | I  ΔtI |   (6×6, I = 3×3 identity)
    | 0   I  |
```

**Measurement model:** Direct observation of position only (`H = [I 0]`, 3×6).

**RAM estimate:** Six 6×6 float matrices (P, Q, R, F, H, K) × 36 floats × 4 bytes = **864 bytes** total — well within the 160KB app budget.

**Library:** `BasicLinearAlgebra` (Arduino-compatible, header-only). Add to `platformio.ini`:
```ini
lib_deps = hideakitai/BasicLinearAlgebra
```

**Benefits over EMA:**
- Velocity estimate is a first-class output (θ̇, φ̇, ṙ)
- Covariance matrix P enables uncertainty quantification and error ellipsoids
- Naturally handles variable update rates if the loop jitter becomes significant

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 5 | 3 | Yes | 8–16h |

---

### 2.3 Extended Kalman Filter (Nonlinear)

**When needed:** If the measurement is taken in Cartesian space (e.g., UWB anchor fixes or camera ArUco poses) while state is maintained in spherical space, the nonlinear `sphericalToCartesian()` transform requires an EKF.

**Jacobian of `sphericalToCartesian()`:**

```
∂x/∂r = sin(φ)cos(θ)    ∂x/∂θ = -r·sin(φ)sin(θ)    ∂x/∂φ = r·cos(φ)cos(θ)
∂y/∂r = sin(φ)sin(θ)    ∂y/∂θ =  r·sin(φ)cos(θ)    ∂y/∂φ = r·cos(φ)sin(θ)
∂z/∂r = cos(φ)           ∂z/∂θ = 0                    ∂z/∂φ = -r·sin(φ)
```

All partial derivatives are computable from quantities already available in `SphericalSensor.cpp`.

**Library:** `TinyEKF` (GitHub: simondlevy/TinyEKF) — designed for embedded systems, pure C++.

**Prerequisite:** Section 2.2 (standard KF) recommended first to validate matrix math on device.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 4 | 4 | Partial | 16–24h |

---

### 2.4 Spike / Outlier Rejection

**Problem:** A cable snag, EMI burst, or encoder skip produces a single large count jump that the EMA cannot suppress quickly. This creates a visible position spike on the trajectory.

**Solution — per-encoder velocity gating:**

```cpp
const int32_t MAX_DELTA_COUNTS = 200;   // tune per encoder
int32_t delta = current_counts - prev_counts;
if (abs(delta) > MAX_DELTA_COUNTS) {
    // reject: use previous value, set a spike_detected flag
    current_counts = prev_counts;
    system_state.spike_count++;
}
```

`MAX_DELTA_COUNTS` maps to physical limits:
- Theta/Phi: 200 counts @ 20000 PPR = 0.36°/frame = 7.2°/s (fast deliberate motion is ~2°/s)
- Wire: 200 counts @ 8000 PPR = 5.00 mm/frame = 100mm/s

The `spike_count` accumulator can be exposed via the `STATUS` serial command for health monitoring.

**Implementation location:** `SphericalSensor::readRawEncoders()` — before count-to-angle conversion.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 4 | 1 | Yes | 1–2h |

---

### 2.5 Pre-Filter vs Post-Filter Architecture

**Current (post-filter):** Raw counts → spherical → **Cartesian** → EMA on X, Y, Z.

**Problem:** X, Y, Z are nonlinearly coupled to r, θ, φ. Filtering them independently introduces artifacts — for example, a noisy θ at large r produces correlated noise in X and Y that the EMA treats as independent, causing the filtered position to drift inside an arc rather than along the true trajectory.

**Recommended (pre-filter):** Raw counts → **EMA/KF on counts** (or on r, θ, φ separately) → spherical → Cartesian.

Each spherical coordinate is physically independent (r is purely the draw-wire; θ and φ are purely the rotary encoders), so pre-filtering each channel independently is mathematically valid.

**Migration path:** Move the EMA from `SphericalSensor::updatePosition()` lines 138–141 to operate on `sph_raw.r_mm`, `sph_raw.theta_deg`, `sph_raw.phi_deg` before the `sphericalToCartesian()` call at line 135.

---

## 3. Sensor Fusion

### 3.1 IMU Integration

**→ See `docs/IMU_INTEGRATION_GUIDE.md` for full setup, wiring, and calibration.**

Summary: MPU6050 (I2C 0x68, GPIO 21/22) or BNO055 provides orientation quaternion. The complementary filter blends IMU short-term response with encoder long-term accuracy:

```
θ_fused = ENCODER_TRUST × θ_encoder + IMU_TRUST × θ_imu
```

Current configuration: `ENCODER_TRUST = 0.98`, `IMU_TRUST = 0.02` (defined in `SensorFusionIntegration.h`).

**→ See `docs/hardware_design/IMU_HARDWARE_NOTES.md` for MPU6050 vs BNO055 wiring and level shifting.**

---

### 3.2 UWB (DW3000) Absolute Position Correction

**Principle:** 3+ UWB anchors at known positions provide time-of-flight ranging. Trilateration gives an absolute Cartesian position fix independent of encoder drift, correcting accumulated error.

**Accuracy:** ~10 cm (1σ) typical for DW3000; encoder system accuracy is better short-term but drifts.

**Fusion strategy:** UWB fix used as an infrequent (1–5 Hz) absolute correction to reset encoder-integrated position — similar to GPS/INS loose coupling.

**Hardware:** DW3000 SPI module (QORVO EVB). SPI available on ESP32 (VSPI: SCK=18, MISO=19, MOSI=23, CS=5). **GPIO 18 conflict with Wire Z encoder B signal** — see Section 9.3.

**Library:** `Qorvo-DWM3000` or `arduino-dw3000`.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 4 | 4 | Partial | 24–40h |

---

### 3.3 VL53L1X ToF Radius Cross-Validation

**Principle:** A VL53L1X time-of-flight sensor mounted at the origin pointing along the wire axis provides an independent radius measurement. Cross-validate against draw-wire encoder output.

**Specs:** Range 0–4 m, ±3% accuracy at 2.5 m, I2C (0x29, can share GPIO 21/22 bus with IMU).

**Use case:** Detect wire sag events (Section 11.1), validate PPR calibration, flag encoder slip.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 3 | 2 | Yes | 4–8h |

---

### 3.4 Madgwick / Mahony Filter Details

**→ See `docs/IMU_INTEGRATION_GUIDE.md` for complete filter theory, tuning parameters, and code.**

Configured via `IMUSensorFusion.h`: `FILTER_TYPE` (0=Madgwick, 1=Mahony), `MADGWICK_BETA`, `MAHONY_KP/KI`.

---

## 4. Encoder Improvements

### 4.1 ESP32 PCNT Hardware Counting

**→ See `docs/ESP32_PCNT_REFERENCE.md` (719 lines) for complete implementation guide.**

Summary of benefits over PaulStoffregen `Encoder` library:
- **Zero pulse loss** up to 40 MHz count rate (hardware peripheral, not ISR)
- **No ISR contention** with WiFi radio (WiFi triggers ~100µs ISR bursts that can mis-count software encoders)
- **Drop-in replacement** via `ESP32Encoder` library (same `getCount()` API)
- Uses 2 of 8 PCNT units per encoder (6 units for 3 encoders — all fit)

Add to `platformio.ini`:
```ini
lib_deps = madhephaestus/ESP32Encoder
```

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 4 | 2 | Yes | 4–8h |

---

### 4.2 Quadrature Error Detection

**Principle:** A quadrature encoder produces only 4 valid state transitions per cycle: `00→01→11→10→00` (forward) or the reverse. Any other transition (`00→11`, `01→10`, etc.) indicates noise, cable fault, or encoder damage.

**Implementation — state machine in software:**

```cpp
static uint8_t prev_ab = 0;
uint8_t curr_ab = (digitalRead(PIN_THETA_A) << 1) | digitalRead(PIN_THETA_B);
uint8_t transition = (prev_ab << 2) | curr_ab;

// Valid transitions: 0b0001, 0b0111, 0b1110, 0b1000 (forward)
//                   0b0100, 0b1101, 0b1011, 0b0010 (reverse)
static const bool valid[16] = {0,1,0,0, 0,0,0,1, 1,0,0,0, 0,0,1,0};
if (!valid[transition]) system_state.quadrature_errors++;
```

**Note:** This check is only practical when using raw GPIO reads or PCNT event callbacks. The `Encoder` library handles this internally and does not expose error counts. Implementing this requires either switching to PCNT (Section 4.1) or adding GPIO sampling alongside the library.

**Expose via STATUS command:** Add `quadrature_errors` field to the STATUS serial response.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 3 | 2 | Yes | 2–4h |

---

### 4.3 Backlash Compensation

**Problem:** Mechanical backlash in gear trains, pulleys, or wire drums causes the encoder to register motion before the measured point actually moves on direction reversal.

**Deadband algorithm:**

```cpp
static int32_t direction = 0;         // +1 or -1
static int32_t reversal_accum = 0;    // counts accumulated since reversal
const int32_t BACKLASH_COUNTS = 50;   // tune per axis

int32_t delta = current_counts - prev_counts;
if (delta * direction < 0) {          // direction reversal detected
    direction = (delta > 0) ? 1 : -1;
    reversal_accum = 0;
}
reversal_accum += abs(delta);
if (reversal_accum < BACKLASH_COUNTS) delta = 0;  // suppress backlash region
```

**Tuning:** `BACKLASH_COUNTS` is determined empirically — command a reversal and observe the count difference before the attached mechanism moves (using VL53L1X or ArUco ground truth).

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 3 | 2 | Yes | 2–4h |

---

### 4.4 Sub-Count Interpolation

**Principle:** Between quadrature edges, velocity can be used to extrapolate position within a count — effectively increasing resolution beyond the hardware PPR limit.

**Relevance at 20000 PPR:** DEG_PER_PULSE = 0.018°. At 20Hz update rate, sub-count interpolation adds at most 0.018° of improvement — negligible for most applications.

**Verdict:** Low priority for this system. Revisit only if update rate is reduced below 5Hz or PPR is lowered significantly.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 1 | 3 | Yes | 4–8h |

---

## 5. Hardware Upgrades

### 5.1 Absolute Encoders

**Motivation:** Current incremental encoders require homing at boot (`setZeroPoint()` after 2s delay). If the robot is not at mechanical home when powered on, all subsequent positions are wrong. Absolute encoders eliminate this requirement.

| Model | Resolution | Interface | Voltage | Notes |
|---|---|---|---|---|
| AS5048A | 14-bit (16384 steps/rev) | SPI | 3.3V/5V | Hall effect, contactless; daisy-chainable |
| AS5600 | 12-bit (4096 steps/rev) | I2C | 3.3–5V | Cheaper; fixed I2C address (0x36) limits multi-axis use |
| AMT23x | 14-bit | SPI | 5V | Capacitive; excellent noise immunity |

**Trade-off:** Absolute encoders measure one full revolution. For multi-turn tracking (e.g., draw-wire with many wraps), a gear reduction or multi-turn counter IC (e.g., iC-MH or AS5047P) is needed.

**Impact on firmware:** Replace `Encoder` library calls with SPI/I2C reads; remove `setZeroPoint()` boot sequence; rewrite `countsToSpherical()` for absolute angle output.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 4 | 3 | Yes | 16–24h |

---

### 5.2 MCU Alternatives

| MCU | Advantage | Disadvantage | Verdict |
|---|---|---|---|
| STM32F4 (Nucleo-F446RE) | TIM encoder mode (hardware QDC), 180MHz, 256KB SRAM | No built-in WiFi; separate ESP-AT module needed | Overkill at 20Hz |
| Teensy 4.1 | 600MHz, 4× hardware QDC, 1MB SRAM | No WiFi; more expensive | Overkill at 20Hz |
| ESP32-S3 | Upgraded ISR, better ADC, same WiFi | PCNT still available; pin-compatible | Easy upgrade path if S3 available |
| RP2040 (Pico W) | PIO state machines for QDC | No hardware FPU; WiFi limited | Inferior for this task |

**Verdict:** Current ESP32 WROOM-32 is sufficient at 20Hz. If update rate needs to increase to 200Hz+ or encoder count rate approaches the ISR limit, migrate to ESP32-S3 (pin-compatible) or add PCNT (Section 4.1) before considering MCU change.

---

### 5.3 Industrial Protocols

| Protocol | ESP32 Support | Throughput | Notes |
|---|---|---|---|
| CAN 2.0B (TWAI) | Native (GPIO 4/5 transceiver) | 1 Mbit/s | CANopen CiA 406 position profile; needs SN65HVD230 transceiver |
| EtherCAT | No — requires ASIC (e.g., LAN9252) | 100 Mbit/s | External IC + SPI; major hardware change |
| Modbus RTU | Software (RS485 + MAX485 IC) | 115.2 kbaud | Simple; supported by many PLCs |
| OPC-UA | WiFi (open62541 library) | Variable | Too heavy for ESP32 SRAM at full feature set |

**Recommended path:** TWAI (CAN) if industrial integration is needed — hardware is already in the ESP32, only the SN65HVD230 transceiver ($0.50) needs to be added to the PCB.

---

## 6. Calibration Improvements

### 6.1 NVS Persistent Calibration Storage

**→ See `docs/ESP32_NVS_CALIBRATION_GUIDE.md` (866 lines) for complete implementation.**

Summary: ESP32 NVS (Non-Volatile Storage) persists calibration data across power cycles in the 512KB NVS flash partition. A ready-to-integrate `CalibrationManager` class is documented, storing:
- `PPR_WIRE`, `PPR_ROTARY` (runtime-corrected values)
- Zero-point offsets (theta_offset, phi_offset, wire_offset)
- Correction curve coefficients (for multi-point calibration)

Integrates with the existing `calibration/CalibrationTest.cpp` environment.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 5 | 1 | Yes | 2–4h |

---

### 6.2 Multi-Point Least-Squares Calibration

**Problem:** Current calibration is single-point (zero at home). The PPR constant assumes perfectly linear encoder output. In practice, wire tension variation and gear non-uniformity introduce a smooth nonlinear error.

**Procedure:**
1. Command robot to N ≥ 5 known reference positions (e.g., fixed physical stops or ArUco markers)
2. Record encoder counts at each position
3. Fit a linear correction: `angle_corrected = a × counts + b` via least squares
4. Optionally fit a polynomial for higher-order correction

**Least-squares formula (for linear fit):**

```
[a, b] = (AᵀA)⁻¹Aᵀy

A = [[counts_1, 1], [counts_2, 1], ..., [counts_N, 1]]
y = [true_angle_1, true_angle_2, ..., true_angle_N]
```

**Implementation:** Calibration host-side in Python (`tools/analysis/`), store resulting coefficients in NVS (Section 6.1). No on-device linear algebra needed.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 4 | 3 | Partial | 8–16h |

---

### 6.3 Temperature Compensation

**Problem:** Quadrature encoder resolution is specified at nominal temperature. Thermal expansion of the drum changes the effective `DRUM_CIRCUM_MM`, and thermal drift in the encoder electronics shifts the PPR slightly.

**Correction model:**

```
PPR_corrected = PPR_nominal × (1 + α_T × ΔT)
DRUM_CIRCUM_corrected = DRUM_CIRCUM_nominal × (1 + α_steel × ΔT)
```

Typical values: `α_T ≈ 50 ppm/°C` for encoder electronics; `α_steel ≈ 12 ppm/°C` for steel drum.

**Hardware:** NTC thermistor (10kΩ B3950) on a 10k/NTC voltage divider → GPIO 39 (ADC1_CH3, available). Note: ESP32 ADC non-linearity above 3.1V requires the 10k/10k NTC divider with 3.3V reference — or use DS18B20 digital sensor on 1-Wire.

**Impact at 25°C swing:** For the draw-wire, 25°C × 12 ppm/°C × 200mm drum = 0.06mm/rev — likely within noise floor. Temperature compensation is most valuable for precision θ/φ at long radius (small angular error → large Cartesian error).

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 2 | 2 | Yes | 4–8h |

---

### 6.4 Camera / ArUco Ground-Truth Validation

**Purpose:** Offline accuracy validation, not runtime calibration. A camera with ArUco marker on the end-effector provides sub-millimeter Cartesian ground truth for comparing against firmware output.

**Toolchain:** OpenCV + `cv2.aruco`, Python script in `tools/analysis/`.

**Limitations:**
- Requires camera calibration (intrinsics matrix)
- Line-of-sight required — not usable during normal operation
- 30 FPS camera vs 20Hz firmware: temporal alignment needed

**Use cases:**
- Validate PPR values after NVS calibration
- Generate reference dataset for multi-point calibration (Section 6.2)
- Characterize systematic errors (sag, backlash)

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 4 | 3 | Yes (offline) | 8–16h |

---

## 7. Real-Time Architecture

### 7.1 Dual-Core FreeRTOS Task Partitioning

**→ See `docs/FreeRTOS_Dual_Core_Architecture.md` (605 lines) for full implementation.**
**→ See `docs/QUICK_REFERENCE_DualCore.md` for quick reference.**

Summary of recommended partition:

| Task | Core | Priority | Period | Responsibility |
|---|---|---|---|---|
| `EncoderTask` | Core 0 | High (10) | 1 ms | Read all 3 encoders, push to queue |
| `ProcessTask` | Core 1 | Normal (5) | 50 ms | Pull from queue, compute spherical→Cartesian, filter |
| `CommTask` | Core 1 | Low (3) | 50 ms | Serial output, WebSocket broadcast |

IPC via `xQueueSendFromISR` / `xQueueReceive` (lock-free queue, 10-deep).

**Current waste:** Core 0 is completely idle. `EvkaPosition.cpp:109` runs both encoder reads and math on Core 1 via Arduino's default task.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 4 | 3 | Yes | 8–16h |

---

### 7.2 ISR Latency Profiling

**Method:** Toggle a spare GPIO pin at the start and end of each encoder ISR handler. Measure the pulse width with a logic analyzer (or oscilloscope). Compare with and without WiFi active.

**Expected findings:**
- Without WiFi: ~2–5µs ISR latency (Xtensa LX6 interrupt overhead)
- With WiFi active: up to ~100µs ISR latency spikes during beacon transmit windows
- This is why PCNT (Section 4.1) is recommended — hardware counting eliminates this latency

**Spare GPIO for toggling:** GPIO 2 (LED pin on Wemos D1 R32) or GPIO 4 (unassigned in current pin map).

---

### 7.3 PSRAM (External RAM)

**Availability:** Only on ESP32-WROVER modules (not the current WROOM-32). PSRAM adds 4MB or 8MB of external QSPI RAM.

**Use cases:** Large trajectory buffers, full 3D visualization mesh in-memory, pre-computed lookup tables for coordinate math.

**Verdict:** Current 160KB app SRAM is sufficient for the encoder+filter pipeline. PSRAM would be relevant if adding an on-device trajectory recorder (Section 9.3) with >2 hours of 20Hz data.

**Board change required:** Swap WROOM-32 for WROVER-32 (pin-compatible; same PCB footprint).

---

## 8. Communication & Data Logging

### 8.1 micro-ROS Integration

**→ See `docs/microros/README.md` and linked files for complete implementation guide.**

Key files in repo:
- `docs/microros/MICROROS_ESP32_INTEGRATION.md` — firmware-side setup
- `docs/microros/MICROROS_ESP32_2024.md` — 2024 build process
- `docs/microros/MICROROS_PERFORMANCE_ANALYSIS.md` — throughput benchmarks
- `docs/microros/MICROROS_QUICK_REFERENCE.md` — cheat sheet

**Message type:** `geometry_msgs/msg/PoseStamped` at 20Hz over Serial or WiFi-UDP transport.

**Encoder→ROS2 mapping:**
```
pose.position.x = cart.x_mm * 0.001   # → meters
pose.position.y = cart.y_mm * 0.001
pose.position.z = cart.z_mm * 0.001
pose.orientation = {w:1, x:0, y:0, z:0}   # identity until IMU fusion added
```

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 5 | 2 | Yes | 4–8h |

---

### 8.2 MQTT

**Use case:** IoT-friendly publish of position data to a broker (Mosquitto, AWS IoT, etc.) without requiring a ROS2 environment on the host.

**Libraries:**
- `PubSubClient` — lightweight, battle-tested; 20Hz publish at QoS 0
- `AsyncMqttClient` — non-blocking, preferred with FreeRTOS

**Topic structure:**
```
evka/position/spherical   → {"r":1234.5,"theta":45.2,"phi":90.1}
evka/position/cartesian   → {"x":872.3,"y":872.3,"z":0.1}
evka/status               → {"valid":1,"frames":1234,"spikes":0}
```

**Requires:** `ENABLE_WIFI=1`. MQTT and WebSocket can share the same WiFi connection simultaneously.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 3 | 2 | Yes | 4–8h |

---

### 8.3 SD Card Logging

**Use case:** Offline trajectory recording without a host computer.

**Interface:** SPI SD card module. ESP32 VSPI defaults: SCK=GPIO 18, MISO=GPIO 19, MOSI=GPIO 23, CS=GPIO 5.

**GPIO 18 conflict:** Current pin map uses GPIO 17 for Wire encoder B (not 18). However, **GPIO 18 is the Wire Z signal (encoder for radius measurement, the third channel used in AllSensorsTest).** Verify `SphericalSensor.h` pin definitions before proceeding. If conflict exists, remap SD CS to GPIO 5 and SCK to GPIO 25 (available).

**Implementation:**
- `SD.h` (Arduino SPI SD library) — available in PlatformIO
- Circular buffer (512-byte sectors) to avoid SD write latency pauses in main loop
- File naming: `log_<timestamp>.csv` using `millis()` for session ID

**File format:** CSV: `timestamp_ms,r_mm,theta_deg,phi_deg,x_mm,y_mm,z_mm,is_valid`

**Storage estimate:** 8 fields × 8 chars avg × 20 Hz × 3600 s/hr = ~4.6 MB/hr. A 16GB card stores ~3400 hours.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 3 | 2 | Yes | 4–8h |

---

### 8.4 Binary Protocol (nanopb / MessagePack)

**Current overhead:** CSV serial output for 9 floats = ~80 bytes/frame at 20Hz = 1600 bytes/s = 12.8 kbaud.

**Binary alternatives:**

| Format | Size (9 floats) | Library | Notes |
|---|---|---|---|
| IEEE 754 packed | 36 bytes | None | 4 bytes × 9 = raw binary; no schema |
| MessagePack | ~38 bytes | `msgpack-c` | Schema-free; Python `msgpack` for decode |
| nanopb (protobuf) | ~36 bytes | `nanopb` | Schema-defined; Python `betterproto` for decode |
| CBOR | ~42 bytes | `tinycbor` | Self-describing; good for mixed types |

**Recommendation:** nanopb if integrating with ROS2 (protobuf is ROS2 native); MessagePack for simple Python tooling.

**Bandwidth reduction:** 80 → 36 bytes = 55% reduction. At 115200 baud, 20Hz CSV uses 1.4% of bandwidth — binary is only valuable above ~500Hz or for WebSocket transmission.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 2 | 2 | Yes | 4–8h |

---

## 9. Visualization & Analysis

### 9.1 Three.js 3D Web Dashboard

**Current state:** `firmware/src/WebDashboard.cpp` serves a single-page app with a 2D canvas that projects the 3D position onto a flat plane.

**Upgrade:** Replace the canvas with a Three.js scene (loaded from CDN in the HTML template string). No server-side changes; only the HTML/JS embedded in `WebDashboard.cpp` changes.

**Features to add:**
- `THREE.SphereGeometry` for the workspace boundary (r=RADIUS_MAX_MM)
- `THREE.Line` for trajectory history (circular buffer of last 200 points)
- `OrbitControls` for mouse drag rotation and zoom
- Coordinate axes (red=X, green=Y, blue=Z)
- Real-time update via existing WebSocket `DATA,...` messages

**Delivery:** The entire Three.js CDN URL is included in the HTML `<script>` tag; no extra flash storage needed.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 4 | 2 | Yes | 4–8h |

---

### 9.2 Error Ellipsoid Visualization

**Prerequisite:** Section 2.2 (Kalman Filter) — requires covariance matrix P.

**Principle:** The 3×3 position submatrix of P defines a covariance ellipsoid in Cartesian space. Decompose via eigenvalue decomposition to get semi-axes and orientation.

**Rendering:** `THREE.EllipsoidGeometry` (custom, or approximate with scaled `SphereGeometry`) in the Three.js dashboard (Section 9.1). Update ellipsoid dimensions each frame from the P matrix diagonal for a simplified axis-aligned display.

**Python alternative:** Use `matplotlib` `Axes3D` with a parametric ellipsoid surface in `tools/analysis/` for offline post-processing.

---

### 9.3 Trajectory Analysis Tools

**Current state:** `tools/analysis/` directory present. `tools/position_checker/gui.py` provides real-time pyqtgraph visualization.

**Known issue:** `tools/analysis/data_logger.py` contains duplicate log lines — deduplicate before using for analysis.

**Recommended additions:**

| Tool | Description | Implementation |
|---|---|---|
| Velocity/acceleration estimator | Finite-difference on CSV trajectory | NumPy gradient; 3-point Savitzky-Golay for noise |
| Repeatability analyzer | Stddev of N repeated moves to same target | Python + matplotlib histogram |
| Calibration curve fitter | Least-squares PPR correction (Section 6.2) | NumPy `polyfit` + residual plot |
| Error vs radius plot | Accuracy degradation at long wire extension | Scatter plot: error_mm vs r_mm |

---

## 10. Mechanical & System-Level

### 10.1 Wire Sag Correction

**Problem:** At large wire extensions (r > 2m), gravity causes the wire to follow a catenary curve rather than a straight line, making the true Cartesian Z lower than computed.

**Correction model (small-angle approximation):**

```
sag_angle = arctan(m × g × r / (2 × T))   # T = wire tension
r_horizontal = r × cos(sag_angle)
z_corrected = z - r × (1 - cos(sag_angle))
```

Where `m` = wire linear mass density (kg/m), `T` = wire tension (N, from spring constant at current extension).

**Practical threshold:** For a 0.5mm stainless wire (m ≈ 1.5 g/m) at T ≈ 5N, sag error at r=2m is ~1.2mm — comparable to encoder resolution at that range.

**Measurement:** Compare VL53L1X vertical measurement against computed Z at various extensions to characterize sag empirically.

| Impact | Difficulty | Feasibility | Est. Hours |
|---|---|---|---|
| 3 | 2 | Yes (offline) | 4–8h |

---

### 10.2 Vibration Deadband

**Problem:** Mechanical vibration causes high-frequency oscillation of encoder counts even when the robot is stationary. At 20000 PPR, even sub-degree vibration produces visible position noise.

**Software solution:** Suppress count changes smaller than N counts over M consecutive frames:

```cpp
if (abs(delta_theta) < VIBRATION_DEADBAND_COUNTS &&
    abs(delta_phi)   < VIBRATION_DEADBAND_COUNTS &&
    abs(delta_wire)  < VIBRATION_DEADBAND_COUNTS) {
    // robot is stationary — hold last valid position
}
```

**Hardware solution:** Rubber anti-vibration mounts under encoder brackets (McMaster-Carr part family: 9376K series or equivalent). More effective than software deadband for broadband vibration.

**Interaction with Kalman filter:** A KF with a well-tuned process noise matrix Q naturally suppresses vibration by predicting near-zero velocity when measurements are jittery — making this deadband less critical if Section 2.2 is implemented.

---

### 10.3 Environmental Sealing

**Current state:** PCB designed on pertinax (phenolic) substrate; no sealing specified.

**Recommendations for field deployment:**

| Measure | Component | Notes |
|---|---|---|
| IP65 enclosure | DIN rail or panel-mount ABS box | Protects PCB from dust/splash |
| Cable glands | PG7/PG9 for encoder cables | Maintain IP rating at cable entry |
| Conformal coating | Silicone or acrylic spray | Corrosion protection on PCB |
| Operating temperature | -10°C to +70°C | Match to E40S6 encoder spec |

---

## 11. Priority Implementation Roadmap

Ordered by effort-to-impact ratio (highest impact / lowest difficulty first):

| # | Improvement | Impact | Difficulty | Feasibility | Existing Doc | Est. Hours |
|---|---|---|---|---|---|---|
| 1 | NVS Persistent Calibration | 5 | 1 | Yes | Complete (866L) | 2–4h |
| 2 | Spike / Outlier Rejection | 4 | 1 | Yes | None (§2.4) | 1–2h |
| 3 | PCNT Hardware Encoder | 4 | 2 | Yes | Complete (719L) | 4–8h |
| 4 | Adaptive EMA Filter | 4 | 2 | Yes | None (§2.1) | 2–4h |
| 5 | micro-ROS Integration | 5 | 2 | Yes | Complete (2431L) | 4–8h |
| 6 | Three.js Web Dashboard | 4 | 2 | Yes | None (§9.1) | 4–8h |
| 7 | Quadrature Error Detection | 3 | 2 | Yes | None (§4.2) | 2–4h |
| 8 | Dual-Core FreeRTOS | 4 | 3 | Yes | Complete (605L) | 8–16h |
| 9 | 6-State Kalman Filter | 5 | 3 | Yes | None (§2.2) | 8–16h |
| 10 | IMU Sensor Fusion | 4 | 3 | Yes | Partial (322L) | 16–24h |
| 11 | Multi-Point Calibration | 4 | 3 | Partial | Partial (NVS) | 8–16h |
| 12 | SD Card Logging | 3 | 2 | Yes | None (§8.3) | 4–8h |
| 13 | Backlash Compensation | 3 | 2 | Yes | None (§4.3) | 2–4h |
| 14 | VL53L1X ToF Validation | 3 | 2 | Yes | None (§3.3) | 4–8h |
| 15 | Wire Sag Correction | 3 | 2 | Yes | None (§10.1) | 4–8h |
| 16 | MQTT Publishing | 3 | 2 | Yes | None (§8.2) | 4–8h |
| 17 | Pre-Filter Architecture | 3 | 2 | Yes | None (§2.5) | 2–4h |
| 18 | Camera / ArUco Validation | 4 | 3 | Yes (offline) | None (§6.4) | 8–16h |
| 19 | Extended Kalman Filter | 4 | 4 | Partial | None (§2.3) | 16–24h |
| 20 | Temperature Compensation | 2 | 2 | Yes | None (§6.3) | 4–8h |
| 21 | Binary Protocol (nanopb) | 2 | 2 | Yes | None (§8.4) | 4–8h |
| 22 | UWB Absolute Correction | 4 | 4 | Partial | None (§3.2) | 24–40h |
| 23 | Absolute Encoders | 4 | 3 | Yes | None (§5.1) | 16–24h |
| 24 | Sub-Count Interpolation | 1 | 3 | Yes | None (§4.4) | 4–8h |
| 25 | PSRAM / Board Upgrade | 2 | 2 | Partial | None (§7.3) | 4–8h |

---

## 12. Cross-Reference Index

| Topic | Section | Existing Document |
|---|---|---|
| IMU sensor fusion | §3.1, §3.4 | `docs/IMU_INTEGRATION_GUIDE.md` |
| IMU hardware wiring | §3.1 | `docs/hardware_design/IMU_HARDWARE_NOTES.md` |
| PCNT hardware encoder | §4.1 | `docs/ESP32_PCNT_REFERENCE.md` |
| NVS persistent calibration | §6.1 | `docs/ESP32_NVS_CALIBRATION_GUIDE.md` |
| Dual-core FreeRTOS | §7.1 | `docs/FreeRTOS_Dual_Core_Architecture.md` |
| Dual-core cheat sheet | §7.1 | `docs/QUICK_REFERENCE_DualCore.md` |
| micro-ROS overview | §8.1 | `docs/microros/README.md` |
| micro-ROS firmware | §8.1 | `docs/microros/MICROROS_ESP32_INTEGRATION.md` |
| micro-ROS 2024 build | §8.1 | `docs/microros/MICROROS_ESP32_2024.md` |
| micro-ROS performance | §8.1 | `docs/microros/MICROROS_PERFORMANCE_ANALYSIS.md` |
| micro-ROS quick ref | §8.1 | `docs/microros/MICROROS_QUICK_REFERENCE.md` |
| micro-ROS README | §8.1 | `docs/microros/README.md` |
| External libraries | All | `docs/resources.md` |
| Circuit schematic | §3.2, §5.3 | `docs/hardware_design/5v/circuit_schematic.md` |
| System architecture | All | `docs/hardware_design/system_architecture.md` |
| DWEM2 draw-wire details | §4.1, §10.1 | `docs/hardware_design/encoders/draw_wire/README.md` |
| E40S6 rotary encoder details | §4.1–4.3 | `docs/hardware_design/encoders/rotary_e40s6/README.md` |
| Filter code | §2.1–2.5 | `firmware/src/SphericalSensor.cpp:138-141` |
| Validation code | §2.4 | `firmware/src/SphericalSensor.cpp:114-121` |
| Main loop | §7.1–7.2 | `firmware/src/EvkaPosition.cpp:109` |
| Calibration test | §6.1–6.3 | `calibration/CalibrationTest.cpp` |
| Phase roadmap | All | `docs/PROJECT_ROADMAP.md` |
