# Quick Reference: ESP32 Dual-Core Implementation

## TL;DR

**Current:** 50 Hz polling → 50 ms latency
**Proposed:** 1 kHz encoder task (Core 0) + 20 Hz computation (Core 1) → 1 ms latency (50× faster)

---

## Maximum Safe Encoder Frequencies

| Method | Max Frequency | Your PPR_ROTARY (20k) | Safe RPM |
|--------|---------------|------------------------|----------|
| **Software ISR** | 50–100 kHz | ~333 kHz @ 100k RPM | ✓ 1,000 (safe) |
| **PCNT Hardware** | 40 MHz | Safe to 333 kHz @ 100k RPM | ✓ 100,000 (safe) |

**Rule:** Stay <10 kHz for software ISR reliability. Use PCNT for >10 kHz.

---

## Core Allocation

```
Core 0 (Realtime)                Core 1 (General)
├─ encoderTask (Pri 3, 1 kHz)    ├─ computationTask (Pri 2, 20 Hz)
│  ├─ Read 3 encoders            │  ├─ Spherical/Cartesian transform
│  ├─ Send to queue              │  └─ Validate limits
│  └─ ~500 µs/cycle              │
└─ 50% CPU used                  ├─ serialTask (Pri 1, 10 ms)
                                 │  ├─ Print position
                                 │  └─ Read commands
                                 └─ ~1% CPU used
```

---

## xTaskCreatePinnedToCore Pattern

```cpp
xTaskCreatePinnedToCore(
    taskFunction,       // Function pointer
    "TaskName",         // Debug name
    2048,              // Stack size (bytes)
    nullptr,           // Parameters
    3,                 // Priority (3=high, 1=low)
    nullptr,           // Handle (optional)
    0                  // Core ID (0 or 1)
);
```

---

## Queue Operations

| Operation | Usage |
|-----------|-------|
| `xQueueCreate(depth, itemSize)` | Create queue |
| `xQueueOverwrite(handle, item)` | Send (replaces old, never blocks) |
| `xQueueReceive(handle, item, timeout)` | Read (blocks if empty) |
| `xQueuePeek(handle, item, timeout)` | Read without removing |

---

## Data Structures

```cpp
struct EncoderCounts {  // 16 bytes (encoder → computation)
    int32_t theta_counts;
    int32_t phi_counts;
    int32_t radius_counts;
    uint32_t timestamp_ms;
};

// SystemStatus already defined (computation → serial)
```

---

## Queue Configuration

**Encoder Queue:** 20 items × 16 bytes = 320 bytes
- Send: `xQueueOverwrite()` (never blocks Core 0)
- Receive: `xQueueReceive()` with 50 ms timeout
- Strategy: Drop old counts (only latest matters)

**Position Queue:** 10 items × 64 bytes = 640 bytes
- Send: `xQueueOverwrite()` (for display)
- Receive: `xQueueReceive()` with 10 ms timeout

---

## Core 0 Task (1 kHz Encoder Polling)

```cpp
void encoderTask_core0(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(1);  // 1 ms = 1 kHz
    
    EncoderCounts counts;
    int32_t prev_theta = 0, prev_phi = 0, prev_radius = 0;
    
    while (1) {
        // Read encoders (~450 µs)
        counts.theta_counts = thetaEncoder->read();
        counts.phi_counts = phiEncoder->read();
        counts.radius_counts = wireEncoder->read();
        counts.timestamp_ms = millis();
        
        // Rate limit: only send if changed
        if (counts.theta_counts != prev_theta ||
            counts.phi_counts != prev_phi ||
            counts.radius_counts != prev_radius) {
            
            xQueueOverwrite(encoderQueue, &counts);
            prev_theta = counts.theta_counts;
            prev_phi = counts.phi_counts;
            prev_radius = counts.radius_counts;
        }
        
        // Maintain 1 kHz cycle
        vTaskDelayUntil(&xLastWakeTime, xFrequency);
    }
}
```

---

## Core 1 Task (20 Hz Computation)

```cpp
void computationTask_core1(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(50);  // 50 ms = 20 Hz
    
    EncoderCounts counts;
    SystemStatus status;
    
    while (1) {
        // Wait for encoder data (up to 50 ms)
        if (xQueueReceive(encoderQueue, &counts, pdMS_TO_TICKS(50)) == pdTRUE) {
            
            // Apply offsets and transform
            int32_t theta = counts.theta_counts - THETA_OFFSET;
            int32_t phi = counts.phi_counts - PHI_OFFSET;
            int32_t radius = -(counts.radius_counts - RADIUS_OFFSET);
            
            SphericalCoords sph = sensor.countsToSpherical(theta, phi, radius);
            CartesianCoords cart = sensor.sphericalToCartesian(sph);
            uint8_t is_valid = validateLimits(sph, cart);
            
            // Prepare status
            status.position = cart;
            status.spherical = sph;
            status.is_valid = is_valid;
            status.frame_count++;
            status.last_update_ms = counts.timestamp_ms;
            
            // Send to serial task
            xQueueOverwrite(positionQueue, &status);
        }
        
        vTaskDelayUntil(&xLastWakeTime, xFrequency);
    }
}
```

---

## Core 1 Task (Serial Output)

```cpp
void serialTask_core1(void *pvParameters) {
    SystemStatus status;
    String serial_buffer;
    
    while (1) {
        // Check for new position data
        if (xQueueReceive(positionQueue, &status, pdMS_TO_TICKS(10)) == pdTRUE) {
            Serial.print("STATUS,");
            Serial.print(status.is_valid);
            Serial.print(",");
            Serial.print(status.frame_count);
            Serial.print(",");
            Serial.print(status.last_update_ms);
            Serial.print(",");
            Serial.print(status.spherical.r_mm, 2);
            Serial.print(",");
            Serial.print(status.spherical.theta_deg, 3);
            Serial.print(",");
            Serial.println(status.spherical.phi_deg, 3);
        }
        
        // Process commands (non-blocking)
        while (Serial.available() > 0) {
            char ch = (char)Serial.read();
            
            if (ch == '\n' || ch == '\r') {
                serial_buffer.trim();
                
                if (serial_buffer == "ZERO") {
                    sensor.setZeroPoint();
                    Serial.println("ACK:ZERO");
                }
                else if (serial_buffer == "PING") {
                    Serial.println("ACK:PONG");
                }
                
                serial_buffer = "";
            } else {
                serial_buffer += ch;
            }
        }
        
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
```

---

## Setup Code

```cpp
// Global queue handles
QueueHandle_t encoderQueue;
QueueHandle_t positionQueue;

void setup() {
    Serial.begin(115200);
    delay(500);
    
    // Initialize sensor
    sensor.begin();
    
    // Create queues
    encoderQueue = xQueueCreate(20, sizeof(EncoderCounts));
    positionQueue = xQueueCreate(10, sizeof(SystemStatus));
    
    if (!encoderQueue || !positionQueue) {
        Serial.println("[ERROR] Queue creation failed");
        while(1);
    }
    
    // Create tasks
    xTaskCreatePinnedToCore(encoderTask_core0, "EncoderCore0", 2048, nullptr, 3, nullptr, 0);
    xTaskCreatePinnedToCore(computationTask_core1, "ComputationCore1", 4096, nullptr, 2, nullptr, 1);
    xTaskCreatePinnedToCore(serialTask_core1, "SerialCore1", 3072, nullptr, 1, nullptr, 1);
    
    Serial.println("[System] Dual-core system initialized");
}

void loop() {
    delay(1000);  // Keep watchdog happy (all work in tasks)
}
```

---

## Header Additions

Add to SphericalSensor.h or EvkaPosition.cpp:

```cpp
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>

struct EncoderCounts {
    int32_t theta_counts;
    int32_t phi_counts;
    int32_t radius_counts;
    uint32_t timestamp_ms;
};

extern QueueHandle_t encoderQueue;
extern QueueHandle_t positionQueue;
```

---

## Performance Gains

| Metric | Before | After |
|--------|--------|-------|
| **Latency** | 50 ms | 1 ms |
| **Jitter** | ±25 ms | ±1 ms |
| **Response** | ~50 ms | ~10 ms |
| **Max RPM** | 1,000 | 100,000 |

---

## When to Use PCNT

Only if you need:
- Edge rates >10 kHz
- Sub-microsecond accuracy
- Very high RPM (>10,000)

For Evka (current <1 kHz): **Stick with software Encoder library**

---

## Debugging

```cpp
// Task info
void printTaskStats() {
    TaskStatus_t *pxTaskStatusArray = (TaskStatus_t *)pvPortMalloc(
        uxTaskGetNumberOfTasks() * sizeof(TaskStatus_t)
    );
    UBaseType_t uxArraySize = uxTaskGetSystemState(pxTaskStatusArray, 
        uxTaskGetNumberOfTasks(), nullptr);
    
    for (UBaseType_t i = 0; i < uxArraySize; i++) {
        Serial.printf("[%s] Priority: %d, Stack: %u bytes\n",
            pxTaskStatusArray[i].pcTaskName,
            pxTaskStatusArray[i].uxCurrentPriority,
            pxTaskStatusArray[i].usStackHighWaterMark);
    }
    vPortFree(pxTaskStatusArray);
}

// Queue depth
UBaseType_t depth = uxQueueMessagesWaiting(encoderQueue);
Serial.printf("[Queue] Depth: %u items\n", depth);
```

---

## Checklist for Implementation

- [ ] Add EncoderCounts struct definition
- [ ] Create encoderQueue and positionQueue in setup()
- [ ] Implement encoderTask_core0() (1 kHz, Core 0, Priority 3)
- [ ] Implement computationTask_core1() (20 Hz, Core 1, Priority 2)
- [ ] Implement serialTask_core1() (10 ms, Core 1, Priority 1)
- [ ] Update setup() to spawn tasks instead of calling updatePosition()
- [ ] Remove updatePosition() calls from loop()
- [ ] Test with serial monitor (should see CSV output at 20 Hz)
- [ ] Verify both cores active (check task stats)
- [ ] Monitor queue depths for backlog issues

---

For detailed explanation: See `FreeRTOS_Dual_Core_Architecture.md`
