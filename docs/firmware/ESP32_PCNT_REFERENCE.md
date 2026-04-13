# ESP32 PCNT Pulse Counter Peripheral for Quadrature Encoders

## Overview

The **PCNT (Pulse Counter)** is a dedicated ESP32 hardware peripheral designed for counting signal edges and decoding quadrature encoders **without consuming CPU interrupts**. This document covers the ESP-IDF PCNT API, the ESP32Encoder Arduino library wrapper, performance characteristics, and practical implementation strategies.

---

## Table of Contents

1. [Hardware Capabilities](#hardware-capabilities)
2. [ESP-IDF PCNT API (Low-Level)](#esp-idf-pcnt-api)
3. [ESP32Encoder Arduino Library](#esp32encoder-library)
4. [Quadrature Decoding Modes](#quadrature-modes)
5. [Performance Comparison](#performance)
6. [Overflow Handling](#overflow)
7. [Pin Configuration](#pins)
8. [Practical Implementation Examples](#examples)
9. [Debugging & Diagnostics](#debugging)
10. [References](#references)

---

## Hardware Capabilities

### PCNT Unit Overview

| Feature | Value |
|---------|-------|
| **Units** | 8 (ESP32) / 2 (ESP32-S3) / 0 (ESP32-C3) |
| **Channels per unit** | 4 |
| **Max simultaneous encoders** | 8 (ESP32), 2 (ESP32-S3) |
| **Counter width (hardware)** | 16-bit (−32768 to +32767) |
| **Counter width (with accumulator)** | 32+ bits (configurable) |
| **Interrupt sources** | 1 shared by all units |
| **Glitch filter** | Built-in, configurable timing |
| **Edge types** | Rising, falling, both |
| **Level control signals** | Yes (for quadrature) |

### Quadrature Capability

- **Full quadrature:** 4 counts per mechanical pulse (both edges of both channels)
- **Half quadrature:** 2 counts per mechanical pulse (both edges of one channel)
- **Single edge:** 1 count per mechanical pulse (rising edge of channel A only)

The PCNT uses **edge + level** signal combination:
- **Edge signal (A):** Count on rising/falling edges
- **Level signal (B):** Direction control — keeps or reverses counting mode

---

## ESP-IDF PCNT API (Low-Level)

### 1. Unit Installation

```c
#include "driver/pcnt.h"

// Configure unit
pcnt_unit_config_t unit_config = {
    .high_limit = 100,           // Upper threshold for auto-reset
    .low_limit = -100,           // Lower threshold for auto-reset
    .flags.accum_count = true    // Enable 32-bit accumulator (optional)
};

pcnt_unit_handle_t pcnt_unit = NULL;
ESP_ERROR_CHECK(pcnt_new_unit(&unit_config, &pcnt_unit));
```

**Key Parameters:**
- `high_limit` / `low_limit`: Counter auto-resets when crossing these values
- `accum_count`: Extends counter width beyond 16-bit hardware limit
- `intr_priority`: 0 = default, >0 = custom priority (must be same for all units)

### 2. Channel Installation

```c
// Configure channel for quadrature
pcnt_chan_config_t chan_config = {
    .edge_gpio_num = GPIO_A,      // Phase A
    .level_gpio_num = GPIO_B,     // Phase B (direction control)
    .flags.invert_edge_input = false,
    .flags.invert_level_input = false
};

pcnt_channel_handle_t pcnt_chan = NULL;
ESP_ERROR_CHECK(pcnt_new_channel(pcnt_unit, &chan_config, &pcnt_chan));
```

**Virtual IO:**
- Set `edge_gpio_num` or `level_gpio_num` to `-1` to use virtual IO (fixed high/low)
- Use `flags.virt_edge_io_level` / `flags.virt_level_io_level` to set virtual level

### 3. Channel Actions (Quadrature Decoding)

```c
// Full quadrature: increment on A rising, decrement on A falling
// Level (B) signal reverses direction when LOW
ESP_ERROR_CHECK(pcnt_channel_set_edge_action(
    pcnt_chan,
    PCNT_CHANNEL_EDGE_ACTION_INCREASE,  // rising edge
    PCNT_CHANNEL_EDGE_ACTION_DECREASE   // falling edge
));

ESP_ERROR_CHECK(pcnt_channel_set_level_action(
    pcnt_chan,
    PCNT_CHANNEL_LEVEL_ACTION_KEEP,     // when B is HIGH: keep counting mode
    PCNT_CHANNEL_LEVEL_ACTION_INVERSE    // when B is LOW: reverse counting mode
));
```

**Edge Actions:**
- `PCNT_CHANNEL_EDGE_ACTION_HOLD` — no change
- `PCNT_CHANNEL_EDGE_ACTION_INCREASE` — increment
- `PCNT_CHANNEL_EDGE_ACTION_DECREASE` — decrement

**Level Actions:**
- `PCNT_CHANNEL_LEVEL_ACTION_KEEP` — keep current mode
- `PCNT_CHANNEL_LEVEL_ACTION_INVERSE` — reverse counting direction

### 4. Glitch Filter

```c
pcnt_glitch_filter_config_t filter_config = {
    .resolution = PCNT_GLITCH_FILTER_2CLK  // 2 APB clock periods (~60 ns @ 80 MHz)
};

ESP_ERROR_CHECK(pcnt_unit_set_glitch_filter(pcnt_unit, &filter_config));
```

**Resolutions (hardware debounce):**
- `PCNT_GLITCH_FILTER_2CLK` to `PCNT_GLITCH_FILTER_512CLK`
- Use for mechanical switch debounce and electrical noise filtering

### 5. Watch Points & Interrupts

```c
// Configure interrupt on counter reaching a value
ESP_ERROR_CHECK(pcnt_unit_add_watch_point(pcnt_unit, 100));  // Trigger at count=100
ESP_ERROR_CHECK(pcnt_unit_add_watch_point(pcnt_unit, -100)); // Trigger at count=-100

// Register callback
void on_pcnt_event(pcnt_unit_handle_t unit, const pcnt_event_data_t *edata, void *user_ctx) {
    int count = edata->watch_point_value;
    // Handle overflow/milestone event
}

pcnt_event_callbacks_t cbs = {
    .on_reach = on_pcnt_event
};
ESP_ERROR_CHECK(pcnt_unit_register_event_callbacks(pcnt_unit, &cbs, NULL));
```

### 6. Start/Stop & Read

```c
// Enable unit
ESP_ERROR_CHECK(pcnt_unit_enable(pcnt_unit));
ESP_ERROR_CHECK(pcnt_unit_start(pcnt_unit));

// Read count
int16_t count;
ESP_ERROR_CHECK(pcnt_unit_get_count(pcnt_unit, &count));

// Stop and cleanup
ESP_ERROR_CHECK(pcnt_unit_stop(pcnt_unit));
ESP_ERROR_CHECK(pcnt_unit_disable(pcnt_unit));
ESP_ERROR_CHECK(pcnt_del_channel(pcnt_chan));
ESP_ERROR_CHECK(pcnt_del_unit(pcnt_unit));
```

---

## ESP32Encoder Arduino Library

### Overview

**Repository:** [madhephaestus/ESP32Encoder](https://github.com/madhephaestus/ESP32Encoder)

**Why use it:** Simplifies PCNT configuration and handles overflow compensation internally.

```cpp
#include "ESP32Encoder.h"

ESP32Encoder encoder;

void setup() {
    // Attach quadrature encoder
    encoder.attachFullQuad(GPIO_A, GPIO_B);  // or attachHalfQuad() or attachSingleEdge()
    encoder.setCount(0);
}

void loop() {
    int32_t count = encoder.getCount();  // Handles 16-bit overflow automatically
    // count can exceed 16-bit due to internal accumulation
}
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `attachFullQuad(pinA, pinB)` | 4x counts (both edges of both channels) |
| `attachHalfQuad(pinA, pinB)` | 2x counts (both edges of channel A only) |
| `attachSingleEdge(pinA)` | 1x counts (rising edge of channel A only) |
| `setCount(value)` | Reset counter to value |
| `getCount()` | Read current count (32-bit) |
| `setFilter(value)` | Set glitch filter (0–1023); use 1023 for maximum debounce |
| `useInternalWeakPullResistors(mode)` | Enable weak pullups/downs (UP, DOWN, NONE) |
| `isrServiceCpuCore` | Set ISR to run on CPU 0 or 1 (prevents concurrency issues) |

### Example: Dual Encoders

```cpp
#include "ESP32Encoder.h"

ESP32Encoder thetaEnc, phiEnc;

void setup() {
    ESP32Encoder::useInternalWeakPullResistors = ESP32Encoder::UP;  // Global setting
    
    thetaEnc.attachFullQuad(32, 35);  // Theta encoder
    phiEnc.attachFullQuad(14, 12);    // Phi encoder
    
    thetaEnc.setFilter(1023);  // Max debounce for both
    phiEnc.setFilter(1023);
}

void loop() {
    int32_t theta_count = thetaEnc.getCount();
    int32_t phi_count = phiEnc.getCount();
    
    // Apply calibration PPR
    float theta_deg = (theta_count / 20000.0f) * 360.0f;
    float phi_deg = (phi_count / 20000.0f) * 360.0f;
    
    Serial.printf("Theta: %d counts (%.2f deg)  Phi: %d counts (%.2f deg)\n",
                  theta_count, theta_deg, phi_count, phi_deg);
    delay(100);
}
```

### Pull Resistors

**Default:** Internal pull-ups disabled.

```cpp
// Global setting (before attachFullQuad)
ESP32Encoder::useInternalWeakPullResistors = ESP32Encoder::UP;    // Pull-up
ESP32Encoder::useInternalWeakPullResistors = ESP32Encoder::DOWN;  // Pull-down
ESP32Encoder::useInternalWeakPullResistors = ESP32Encoder::NONE;  // Disabled
```

**When to use:**
- **UP:** If encoder lines are open-drain or have external pulldowns
- **DOWN:** Rarely needed; encoder outputs are usually active-high
- **NONE:** Normal CMOS encoder with active push-pull outputs

---

## Quadrature Decoding Modes

### Full Quadrature (4x Resolution)

```
Mechanical pulse     A ━┓
                       ┣━ 4 counts per pulse
                     B ━┛
```

- **Count increment on:**
  - Rising edge of A (when B is HIGH)
  - Falling edge of A (when B is LOW)
- **Maximum resolution** for smooth movement
- **Most common** for motion control

### Half Quadrature (2x Resolution)

```
Count on both edges of A only; ignore B
```

- **Use if:** Only need 2x resolution or B line is noisy
- **Simpler signal integrity** requirements

### Single Edge (1x Resolution)

```
Count only on rising edge of A; ignore B
```

- **Minimum resolution**
- **Use for:** Rare manual pulse counting (not typical for servo encoders)

---

## Performance Comparison

### Software Interrupt Counting (e.g., standard Arduino Encoder library)

| Aspect | Performance |
|--------|-------------|
| **CPU usage** | High (interrupt per edge) |
| **Max frequency** | ~50 kHz @ ESP32 (limited by interrupt latency) |
| **Jitter** | Variable (depends on other interrupts) |
| **Max count** | 32-bit (if careful with edge cases) |
| **Overhead** | Context switch per edge |

**E40S6-5000 @ 2000 RPM (full quadrature):**
- Edge frequency: 2000 RPM × 5000 counts × 4 edges ÷ 60 = **667 kHz**
- **Would saturate and miss pulses** with software interrupt counting

### PCNT Hardware Counting

| Aspect | Performance |
|--------|-------------|
| **CPU usage** | Minimal (only on overflow) |
| **Max frequency** | >40 MHz (limited by GPIO sampling rate) |
| **Jitter** | Fixed, zero-loss per-edge |
| **Max count** | 16-bit hardware + 32-bit accumulator (32+ bit total) |
| **Overhead** | No per-edge overhead |

**E40S6-5000 @ 2000 RPM:**
- Edge frequency: **667 kHz** ✓ Handled effortlessly
- Overflow every: ~49 ms (16-bit @ 667 kHz)
- Accumulator compensates → continuous 32-bit count

### Verdict

**PCNT is mandatory for high-speed encoders.** Software interrupts cannot keep up.

---

## Overflow Handling

### 16-bit Hardware Counter Limits

With full quadrature decoding:
- **PPR:** 5000 (E40S6 single shaft)
- **X4 quadrature:** 5000 × 4 = 20,000 counts/rev
- **16-bit range:** ±32,767
- **Overflow interval @ 1000 RPM:** 32,767 ÷ 20,000 × 60 ÷ 1000 = **98 ms**

### Solution: Internal Accumulator

```c
pcnt_unit_config_t unit_config = {
    .high_limit = 100000,
    .low_limit = -100000,
    .flags.accum_count = true  // Enable accumulator
};
```

**How it works:**
1. Hardware counter fills to `high_limit`
2. ISR fires, accumulator adds delta, hardware counter resets
3. Application reads combined 32-bit value (no pulses lost)

**Result:** Continuous 32-bit counting with minimal ISR overhead.

### Watch Point Strategy

```c
// Set overflow watch point to catch when hardware counter hits limit
ESP_ERROR_CHECK(pcnt_unit_add_watch_point(pcnt_unit, EXAMPLE_PCNT_HIGH_LIMIT));
ESP_ERROR_CHECK(pcnt_unit_add_watch_point(pcnt_unit, EXAMPLE_PCNT_LOW_LIMIT));
```

### ESP32Encoder Handles This Automatically

```cpp
int32_t count = thetaEnc.getCount();  // Always returns full 32-bit value
```

No manual overflow handling needed.

---

## Pin Configuration

### GPIO Selection Rules

**ESP32 PCNT GPIO compatibility:**
- Most GPIOs support PCNT (routed via GPIO matrix)
- Avoid GPIO 6, 7, 8, 9, 10, 11 (used by SPI flash in most boards)
- Avoid GPIO 0, 2, 15 on Wemos D1 R32 (strapping pins)

### Typical Configuration (Wemos D1 R32)

| Encoder | Channel A | Channel B | Notes |
|---------|-----------|-----------|-------|
| Theta | GPIO 14 | GPIO 12 | Theta final mapping in `SphericalSensor.h` |
| Phi | GPIO 32 | GPIO 35 | Phi final mapping in `SphericalSensor.h` |
| Draw-wire | GPIO 16 | GPIO 17 | Optional Z (GPIO 18) |

### Voltage Divider (Critical!)

**E40S6 output:** 0–5V  
**ESP32 GPIO max:** 3.3V

**Required for every signal line:**

```
Encoder (0-5V) ──10kΩ──┬──→ ESP32 GPIO (0-3.3V)
                       │
                      20kΩ
                       │
                      GND
```

- **Voltage ratio:** (20k ÷ (10k + 20k)) × 5V = 3.33V ✓
- **Hysteresis:** Not needed if divider is clean
- **Capacitive debounce:** Optional 0.1 µF cap at GPIO

---

## Practical Implementation Examples

### Example 1: Basic PCNT (ESP-IDF)

```c
#include "driver/pcnt.h"
#include "driver/gpio.h"

#define GPIO_ENCODER_A 32
#define GPIO_ENCODER_B 35

void setup_encoder() {
    // Unit config
    pcnt_unit_config_t unit_cfg = {
        .high_limit = 32767,
        .low_limit = -32768,
        .flags.accum_count = true
    };
    pcnt_unit_handle_t unit = NULL;
    ESP_ERROR_CHECK(pcnt_new_unit(&unit_cfg, &unit));

    // Channel config
    pcnt_chan_config_t chan_cfg = {
        .edge_gpio_num = GPIO_ENCODER_A,
        .level_gpio_num = GPIO_ENCODER_B
    };
    pcnt_channel_handle_t chan = NULL;
    ESP_ERROR_CHECK(pcnt_new_channel(unit, &chan_cfg, &chan));

    // Quadrature mode
    ESP_ERROR_CHECK(pcnt_channel_set_edge_action(chan,
        PCNT_CHANNEL_EDGE_ACTION_INCREASE,
        PCNT_CHANNEL_EDGE_ACTION_DECREASE));
    
    ESP_ERROR_CHECK(pcnt_channel_set_level_action(chan,
        PCNT_CHANNEL_LEVEL_ACTION_KEEP,
        PCNT_CHANNEL_LEVEL_ACTION_INVERSE));

    // Glitch filter (optional)
    pcnt_glitch_filter_config_t filter_cfg = {
        .resolution = PCNT_GLITCH_FILTER_2CLK
    };
    ESP_ERROR_CHECK(pcnt_unit_set_glitch_filter(unit, &filter_cfg));

    // Enable
    ESP_ERROR_CHECK(pcnt_unit_enable(unit));
    ESP_ERROR_CHECK(pcnt_unit_start(unit));
}

void read_encoder(pcnt_unit_handle_t unit) {
    int16_t count;
    ESP_ERROR_CHECK(pcnt_unit_get_count(unit, &count));
    printf("Encoder count: %d\n", count);
}
```

### Example 2: Using ESP32Encoder (Arduino)

```cpp
#include "ESP32Encoder.h"

ESP32Encoder thetaEnc, phiEnc;

void setup() {
    Serial.begin(115200);
    
    // Setup encoders with glitch filter
    thetaEnc.attachFullQuad(32, 35);
    phiEnc.attachFullQuad(14, 12);
    
    thetaEnc.setFilter(1023);  // Max hardware debounce
    phiEnc.setFilter(1023);
    
    // Optional: set ISR to CPU 0 to avoid concurrency
    ESP32Encoder::isrServiceCpuCore = 0;
}

void loop() {
    // Read 32-bit counts (overflow-safe)
    int32_t theta_cnt = thetaEnc.getCount();
    int32_t phi_cnt = phiEnc.getCount();
    
    // Convert to angles with calibration
    float ppr = 20000.0f;  // E40S6-5000 @ X4
    float theta_deg = (theta_cnt / ppr) * 360.0f;
    float phi_deg = (phi_cnt / ppr) * 360.0f;
    
    Serial.printf("Theta: %.2f°  Phi: %.2f°\n", theta_deg, phi_deg);
    delay(100);
}
```

### Example 3: Overflow Compensation (Lower-Level Control)

```c
#include "driver/pcnt.h"

pcnt_unit_handle_t unit;
int32_t overflow_count = 0;  // Track full overflows
int16_t last_hardware_count = 0;

void IRAM_ATTR on_overflow(pcnt_unit_handle_t u, const pcnt_event_data_t *e, void *ctx) {
    int16_t current;
    pcnt_unit_get_count(u, &current);
    
    if (current > last_hardware_count) {
        overflow_count += 0x10000;  // Add 65536 for positive overflow
    } else {
        overflow_count -= 0x10000;  // Subtract for negative overflow
    }
    last_hardware_count = current;
}

int32_t get_full_count() {
    int16_t hw_count;
    pcnt_unit_get_count(unit, &hw_count);
    return overflow_count + hw_count;  // Full 32-bit value
}

void setup() {
    // ... unit/channel config ...
    
    pcnt_event_callbacks_t cbs = { .on_reach = on_overflow };
    pcnt_unit_register_event_callbacks(unit, &cbs, NULL);
    
    pcnt_unit_add_watch_point(unit, 32000);   // Upper limit
    pcnt_unit_add_watch_point(unit, -32000);  // Lower limit
}
```

---

## Debugging & Diagnostics

### 1. GPIO Verification

```cpp
void diagnose_encoder() {
    Serial.println("\n=== PCNT GPIO Diagnostic ===");
    Serial.printf("GPIO 14 (Theta A): %d\n", digitalRead(14));
    Serial.printf("GPIO 12 (Theta B): %d\n", digitalRead(12));
    Serial.printf("GPIO 32 (Phi A):   %d\n", digitalRead(32));
    Serial.printf("GPIO 35 (Phi B):   %d\n", digitalRead(35));
    
    // Sample transitions for 1 second
    uint32_t ta = 0, tb = 0, pa = 0, pb = 0;
    uint8_t last_ta = digitalRead(14);
    uint8_t last_tb = digitalRead(12);
    uint8_t last_pa = digitalRead(32);
    uint8_t last_pb = digitalRead(35);
    
    unsigned long start = millis();
    while (millis() - start < 1000) {
        if (digitalRead(14) != last_ta) { ta++; last_ta = !last_ta; }
        if (digitalRead(12) != last_tb) { tb++; last_tb = !last_tb; }
        if (digitalRead(32) != last_pa) { pa++; last_pa = !last_pa; }
        if (digitalRead(35) != last_pb) { pb++; last_pb = !last_pb; }
    }
    
    Serial.printf("Transitions in 1s: TA=%u, TB=%u, PA=%u, PB=%u\n", ta, tb, pa, pb);
    
    if (ta > 0 && tb > 0) Serial.println("Theta: OK");
    if (pa > 0 && pb > 0) Serial.println("Phi: OK");
}
```

### 2. Count Validation

```cpp
// Expected counts for known rotation
void validate_calibration() {
    thetaEnc.setCount(0);
    delay(500);
    
    // Manually rotate encoder N full turns
    int32_t cnt = thetaEnc.getCount();
    float measured_ppr = (float)cnt / N_ROTATIONS;
    
    Serial.printf("Measured PPR: %.0f (expected ~20000)\n", measured_ppr);
    
    if (abs(measured_ppr - 20000) > 500) {
        Serial.println("WARNING: PPR mismatch. Check voltage divider and wiring.");
    }
}
```

### 3. Overflow Verification

```cpp
// Test 16-bit overflow behavior
void test_overflow() {
    thetaEnc.setCount(32000);
    delay(100);
    
    // Rotate encoder rapidly to trigger overflow
    int32_t cnt1 = thetaEnc.getCount();
    delay(1000);
    int32_t cnt2 = thetaEnc.getCount();
    
    Serial.printf("Count after overflow: %ld (should be >32000)\n", cnt2);
    
    if (cnt2 <= 32000) {
        Serial.println("ERROR: Overflow not handled correctly!");
    }
}
```

### 4. Performance Profiling

```cpp
void profile_pcnt() {
    // Measure ISR latency using overflow callback
    volatile uint32_t isr_calls = 0;
    
    // (Use custom ISR callback to count)
    
    unsigned long start = millis();
    delay(10000);  // 10 seconds
    unsigned long elapsed = millis() - start;
    
    float isr_rate = (float)isr_calls / (elapsed / 1000.0f);
    Serial.printf("ISR calls per second: %.1f\n", isr_rate);
    Serial.printf("Expected @ 667 kHz: ~33 calls/sec\n");
}
```

---

## References

### Official Documentation

- **ESP-IDF PCNT Driver:** https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/pcnt.html
- **ESP32 Datasheet (PCNT section):** https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf
- **GPIO Matrix:** https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/gpio.html

### Arduino Libraries

- **ESP32Encoder:** https://github.com/madhephaestus/ESP32Encoder
- **Encoder (Paul Stoffregen):** https://github.com/PaulStoffregen/Encoder (software fallback)

### Application Notes

- **Incremental Encoder Wikipedia:** https://en.wikipedia.org/wiki/Incremental_encoder
- **Quadrature Encoder Basics:** https://en.wikipedia.org/wiki/Rotary_encoder#Incremental_rotary_encoder

### Related Hardware

- **E40S6-5000 (Autonics):** 5000 PPR, 0–5V push-pull output
- **DWEM2 (OPKON):** Draw-wire encoder, 2000 PPR, 200 mm drum, LTP push-pull output

---

## Quick Reference: ESP32Encoder vs PCNT API

| Feature | ESP32Encoder | PCNT API |
|---------|--------------|----------|
| **Ease of use** | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Flexibility** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Overflow handling** | Automatic | Manual or watch points |
| **ISR overhead** | Minimal | Full control |
| **Learning curve** | Shallow | Steep |
| **Typical choice** | Yes | Only if custom behavior needed |

---

## Project Integration (evka_position)

### Current Configuration

From `firmware/src/SphericalSensor.h`:

```cpp
#define PPR_ROTARY 20000.0    // E40S6-5000 @ X4 quadrature
#define PPR_WIRE 8000.0       // DWEM2 P2000 theoretical (2000 PPR × X4 quadrature)
#define DEG_PER_PULSE (360.0 / PPR_ROTARY)
#define MM_PER_PULSE (400.0 / PPR_WIRE)

// Theta encoder: GPIO 14 (A), 12 (B)
// Phi encoder:   GPIO 32 (A), 35 (B)
// Wire sensor:   GPIO 16 (A), 17 (B), 18 (Z)
```

### Implementation Notes

1. **Used by:** `RotaryEncoderTest.cpp`, `AllSensorsTest.cpp`
2. **Hardware:** Wemos D1 R32 (ESP32)
3. **Library:** Uses `Encoder.h` (Paul Stoffregen's software version in tests)
4. **Future upgrade:** Could use `ESP32Encoder` for PCNT hardware acceleration
5. **Voltage protection:** Voltage dividers confirmed on all 4 rotary encoder lines

---

## Troubleshooting Checklist

- [ ] Encoder outputs swing 0–5V? Install 10k/20k voltage dividers on all lines
- [ ] GPIO correct? Verify pin numbers match firmware config
- [ ] Quadrature signal visible? Run GPIO diagnostic (sample transitions)
- [ ] PPR calibrated? Rotate known number of turns, use CAL command
- [ ] ISR overhead acceptable? Monitor count accuracy over long duration
- [ ] Overflow handled? Verify counts exceed 32,767 without loss
- [ ] Glitch filter set? Use `setFilter(1023)` for mechanical switches
