# ESP32 NVS (Non-Volatile Storage) for Calibration Parameters

Complete reference for storing encoder calibration offsets using Preferences library vs nvs_flash API.

---

## Table of Contents
1. [Quick Comparison](#quick-comparison)
2. [Preferences Library (Recommended)](#preferences-library-recommended)
3. [nvs_flash API (Low-level)](#nvs_flash-api-low-level)
4. [Float Array Storage](#float-array-storage)
5. [Wear Leveling & Limits](#wear-leveling--limits)
6. [Implementation Examples](#implementation-examples)
7. [EEPROM vs NVS](#eeprom-vs-nvs)
8. [Production Checklist](#production-checklist)

---

## Quick Comparison

| Feature | Preferences | nvs_flash API | EEPROM Emulation |
|---------|-------------|---------------|------------------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Type Support** | String, int, float, blob | All types via blob | Limited |
| **Namespace Support** | Yes (isolated) | Manual partitioning | No |
| **Wear Leveling** | Built-in, automatic | Built-in, automatic | Manual |
| **Recommended For** | Most applications | Raw performance needs | Legacy code |
| **Flash Writes** | ~100k cycles | ~100k cycles | ~100k cycles |
| **Per-Key Size** | 4096 bytes max | 4096 bytes max | Per-EEPROM sector |

**Best Practice**: Use **Preferences** for calibration — it's user-friendly and battle-tested.

---

## Preferences Library (Recommended)

### Why Preferences?
- **Simple API**: Open namespace → read/write → close
- **Type Safety**: Automatic serialization for float, int, string, blob
- **Namespace Isolation**: Multiple independent calibration sets
- **Automatic Wear Leveling**: NVS handles erasure cycles
- **Error Recovery**: Built-in CRC validation

### Basic Usage

```cpp
#include <Preferences.h>

Preferences prefs;

// Open read/write namespace (auto-creates if missing)
prefs.begin("calibration", false);  // namespace, readOnly

// Write values
prefs.putFloat("theta_offset_deg", 0.5f);
prefs.putFloat("phi_offset_deg", -1.2f);
prefs.putFloat("wire_scale", 1.0025f);
prefs.putUInt("calibration_timestamp", millis());

// Read values with defaults
float theta_offset = prefs.getFloat("theta_offset_deg", 0.0f);
float phi_offset = prefs.getFloat("phi_offset_deg", 0.0f);
float wire_scale = prefs.getFloat("wire_scale", 1.0f);

// Verify existence
if (prefs.isKey("theta_offset_deg")) {
    Serial.println("Theta offset exists in NVS");
}

// Clean up
prefs.end();
```

### Writing Calibration Structure

For your **SphericalSensor** calibration parameters:

```cpp
#include <Preferences.h>

struct CalibrationData {
    float theta_offset_deg;  // Azimuth zero offset
    float phi_offset_deg;    // Elevation zero offset
    float wire_scale;        // Draw-wire scale factor (PPR_WIRE multiplier)
    float wire_offset_mm;    // Draw-wire retraction offset
    uint32_t timestamp_s;    // Unix timestamp of calibration
    uint8_t valid_flag;      // 0: not calibrated, 1: calibrated
};

class CalibrationManager {
private:
    Preferences nvs;
    CalibrationData cached_data;
    
public:
    bool begin() {
        return nvs.begin("evka_cal", false);  // namespace "evka_cal"
    }
    
    void end() {
        nvs.end();
    }
    
    /**
     * Save calibration to NVS
     * @return true if successful
     */
    bool save(const CalibrationData& cal) {
        nvs.putFloat("theta_off", cal.theta_offset_deg);
        nvs.putFloat("phi_off", cal.phi_offset_deg);
        nvs.putFloat("wire_scale", cal.wire_scale);
        nvs.putFloat("wire_off", cal.wire_offset_mm);
        nvs.putUInt("timestamp", cal.timestamp_s);
        nvs.putUChar("valid", cal.valid_flag);
        cached_data = cal;
        return true;
    }
    
    /**
     * Load calibration from NVS
     * @return true if valid calibration exists
     */
    bool load(CalibrationData& cal) {
        if (nvs.getUChar("valid", 0) == 0) {
            return false;  // Not calibrated yet
        }
        
        cal.theta_offset_deg = nvs.getFloat("theta_off", 0.0f);
        cal.phi_offset_deg = nvs.getFloat("phi_off", 0.0f);
        cal.wire_scale = nvs.getFloat("wire_scale", 1.0f);
        cal.wire_offset_mm = nvs.getFloat("wire_off", 0.0f);
        cal.timestamp_s = nvs.getUInt("timestamp", 0);
        cal.valid_flag = nvs.getUChar("valid", 0);
        
        cached_data = cal;
        return true;
    }
    
    /**
     * Get timestamp of last calibration
     */
    uint32_t getLastCalibrationTime() {
        return nvs.getUInt("timestamp", 0);
    }
    
    /**
     * Erase all calibration data
     */
    void reset() {
        nvs.clear();
    }
    
    /**
     * Print all calibration keys/values (debug)
     */
    void printAll() {
        Serial.println("=== Calibration Data ===");
        Serial.printf("Theta Offset: %.6f°\n", nvs.getFloat("theta_off", 0.0f));
        Serial.printf("Phi Offset: %.6f°\n", nvs.getFloat("phi_off", 0.0f));
        Serial.printf("Wire Scale: %.6f\n", nvs.getFloat("wire_scale", 1.0f));
        Serial.printf("Wire Offset: %.6f mm\n", nvs.getFloat("wire_off", 0.0f));
        Serial.printf("Valid: %d\n", nvs.getUChar("valid", 0));
        Serial.printf("Timestamp: %u\n", nvs.getUInt("timestamp", 0));
    }
    
    /**
     * Get cached data (after load())
     */
    const CalibrationData& getCached() const {
        return cached_data;
    }
};
```

### Integration with SphericalSensor

In `SphericalSensor.cpp`:

```cpp
#include <Preferences.h>
#include "CalibrationManager.h"

class SphericalPositioningSensor {
private:
    CalibrationManager cal_mgr;
    CalibrationData current_calibration;
    
    // Apply calibration offsets to raw readings
    float applyThetaCalibration(float raw_theta) {
        return raw_theta + current_calibration.theta_offset_deg;
    }
    
    float applyPhiCalibration(float raw_phi) {
        return raw_phi + current_calibration.phi_offset_deg;
    }
    
    float applyWireCalibration(float raw_mm) {
        // Scale first, then apply offset
        float scaled = raw_mm * current_calibration.wire_scale;
        return scaled + current_calibration.wire_offset_mm;
    }
    
public:
    /**
     * Initialize sensor with calibration load
     */
    bool begin() {
        // ... existing sensor init ...
        
        // Load calibration from NVS
        cal_mgr.begin();
        if (cal_mgr.load(current_calibration)) {
            Serial.println("[SphericalSensor] Calibration loaded from NVS");
            cal_mgr.printAll();
        } else {
            Serial.println("[SphericalSensor] No calibration in NVS, using defaults");
            current_calibration = {0.0f, 0.0f, 1.0f, 0.0f, 0, 0};
        }
        cal_mgr.end();
        
        return true;
    }
    
    /**
     * Save current calibration to NVS
     */
    bool saveCalibration(float theta_off, float phi_off, 
                        float wire_scale, float wire_off) {
        current_calibration.theta_offset_deg = theta_off;
        current_calibration.phi_offset_deg = phi_off;
        current_calibration.wire_scale = wire_scale;
        current_calibration.wire_offset_mm = wire_off;
        current_calibration.timestamp_s = time(nullptr);
        current_calibration.valid_flag = 1;
        
        cal_mgr.begin();
        bool success = cal_mgr.save(current_calibration);
        cal_mgr.end();
        
        return success;
    }
    
    /**
     * Get calibration status
     */
    bool isCalibrated() const {
        return current_calibration.valid_flag == 1;
    }
    
    /**
     * Reset calibration to defaults
     */
    void resetCalibration() {
        cal_mgr.begin();
        cal_mgr.reset();
        cal_mgr.end();
        
        current_calibration = {0.0f, 0.0f, 1.0f, 0.0f, 0, 0};
        Serial.println("[SphericalSensor] Calibration reset");
    }
};
```

---

## nvs_flash API (Low-level)

Use `nvs_flash` API only if you need:
- Direct control over flash operations
- Custom partitioning schemes
- Integration with other NVS consumers

### Basic API

```cpp
#include <nvs_flash.h>
#include <nvs.h>

// Initialize NVS (usually done in begin())
void initNVS() {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        // NVS partition truncated, erase and retry
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
}

// Open NVS handle (namespace)
nvs_handle_t handle;
esp_err_t err = nvs_open("evka_cal", NVS_READWRITE, &handle);

if (err == ESP_OK) {
    // Read value
    float theta_offset = 0.0f;
    nvs_get_i32(handle, "theta_off_i32", (int32_t*)&theta_offset);
    
    // Write value
    nvs_set_i32(handle, "theta_off_i32", *(int32_t*)&theta_offset);
    
    // Commit changes
    nvs_commit(handle);
    
    // Close handle
    nvs_close(handle);
}
```

**Problem**: nvs_flash doesn't have native float support. Workaround:

```cpp
// Store float as uint32_t
uint32_t theta_bits = *(uint32_t*)&theta_offset;
nvs_set_u32(handle, "theta_bits", theta_bits);

// Retrieve
uint32_t retrieved_bits = 0;
nvs_get_u32(handle, "theta_bits", &retrieved_bits);
float retrieved_offset = *(float*)&retrieved_bits;
```

**Better**: Use Preferences which handles this automatically.

---

## Float Array Storage

### Storing Multiple Calibration Points (Advanced)

For non-linear calibration curves, store float arrays as **blobs**:

```cpp
#include <Preferences.h>

// Array of calibration points
struct CalibrationPoint {
    float input_value;   // e.g., raw encoder counts
    float output_value;  // e.g., corrected mm
};

class AdvancedCalibrationManager {
private:
    Preferences nvs;
    static const size_t MAX_POINTS = 64;
    
public:
    bool begin() {
        return nvs.begin("cal_advanced", false);
    }
    
    void end() {
        nvs.end();
    }
    
    /**
     * Save calibration curve (array of points)
     */
    bool saveCurve(const char* key, const CalibrationPoint* points, size_t count) {
        if (count > MAX_POINTS) {
            Serial.printf("Error: Too many calibration points (%zu > %zu)\n", count, MAX_POINTS);
            return false;
        }
        
        // Store count first
        char count_key[64];
        snprintf(count_key, sizeof(count_key), "%s_count", key);
        nvs.putUInt(count_key, count);
        
        // Store array as blob
        size_t blob_size = count * sizeof(CalibrationPoint);
        if (blob_size > 4096) {  // NVS max per-key size
            Serial.printf("Error: Blob too large (%zu > 4096)\n", blob_size);
            return false;
        }
        
        nvs.putBlob(key, (const uint8_t*)points, blob_size);
        return true;
    }
    
    /**
     * Load calibration curve
     */
    bool loadCurve(const char* key, CalibrationPoint* points, size_t& count) {
        char count_key[64];
        snprintf(count_key, sizeof(count_key), "%s_count", key);
        
        // Get count
        count = nvs.getUInt(count_key, 0);
        if (count == 0) {
            return false;  // Not stored
        }
        
        // Get blob
        size_t blob_size = count * sizeof(CalibrationPoint);
        size_t retrieved_size = nvs.getBlob(key, points, blob_size);
        
        return (retrieved_size == blob_size);
    }
    
    /**
     * Interpolate calibration value
     */
    float interpolate(const CalibrationPoint* curve, size_t count, float input) {
        if (count == 0) return input;  // No calibration
        
        // Find bracketing points
        for (size_t i = 0; i < count - 1; i++) {
            if (input >= curve[i].input_value && input <= curve[i + 1].input_value) {
                // Linear interpolation
                float t = (input - curve[i].input_value) / 
                         (curve[i + 1].input_value - curve[i].input_value);
                return curve[i].output_value + 
                       t * (curve[i + 1].output_value - curve[i].output_value);
            }
        }
        
        // Out of bounds, use nearest
        if (input < curve[0].input_value) return curve[0].output_value;
        return curve[count - 1].output_value;
    }
};

// Usage
AdvancedCalibrationManager adv_cal;
adv_cal.begin();

// Example: Non-linear draw-wire calibration
CalibrationPoint wire_curve[] = {
    {0.0f,    0.0f},      // 0 counts → 0 mm
    {400.0f,  10.0f},     // 400 counts → 10 mm
    {4000.0f, 100.0f},    // 4000 counts → 100 mm
    {8000.0f, 200.0f},    // 8000 counts (1 rev, DWEM2 P2000 × X4) → 200 mm
};

adv_cal.saveCurve("wire_cal_curve", wire_curve, 4);

// Load and interpolate
CalibrationPoint loaded_curve[64];
size_t loaded_count;
if (adv_cal.loadCurve("wire_cal_curve", loaded_curve, loaded_count)) {
    float corrected_mm = adv_cal.interpolate(loaded_curve, loaded_count, 2010.0f);  // ~50mm
}

adv_cal.end();
```

---

## Wear Leveling & Limits

### NVS Wear Leveling Mechanism

**How it works**:
1. **Sector Allocation**: Default NVS partition is 16 sectors (64 KB @ 4KB/sector)
2. **Wear Tracking**: Each sector has an erasure counter
3. **Leveling**: ESP-IDF automatically rotates writes across sectors
4. **Wear Threshold**: ~100,000 erase cycles per sector (industry standard SPI NOR flash)

**Calculation**:
- Total erase cycles available = 16 sectors × 100,000 cycles/sector = **1.6M erase cycles**
- If you write calibration **once per minute** = 1,440 writes/day
- Expected lifespan = 1.6M ÷ 1,440 ÷ 365 ≈ **3 years**

### Partition Configuration (optional)

In `platformio.ini` (advanced):

```ini
[env:esp32]
board_build.partitions = partitions.csv
```

Custom `partitions.csv`:

```csv
# Name,   Type, SubType, Offset,  Size,    Flags
nvs,      data, nvs,     0x9000,  0x5000,  # 20 KB (default)
otadata,  data, ota,     0xe000,  0x2000,  
factory,  app,  factory, 0x10000, 0x1f0000,
```

**To increase NVS to 32 KB** (lower wear):
```csv
nvs,      data, nvs,     0x9000,  0x8000,  # 32 KB
```

### Sector Size Reference

| Partition Size | Sectors | Erase Cycles | Write Freq (1/min) | Lifespan |
|---|---|---|---|---|
| 16 KB (default) | 4 | 400k | 1/min | ~9 months |
| 20 KB | 5 | 500k | 1/min | ~11 months |
| 32 KB | 8 | 800k | 1/min | ~1.8 years |
| 64 KB | 16 | 1.6M | 1/min | **3.6 years** |

**Recommendation**: For calibration-at-startup workflows, default 16 KB is sufficient. For continuous recalibration, increase to 32-64 KB.

### Key Size Limits

```
Maximum per-key size:        4096 bytes
Maximum namespace length:    16 bytes (e.g., "evka_cal")
Maximum key length:          16 bytes (e.g., "theta_off")
Maximum NVS partition size:  Flash size − other partitions
(typically 16 KB − 512 KB available)
```

---

## Implementation Examples

### Example 1: Simple Calibration Save/Load

```cpp
// calibration_example.cpp
#include <Preferences.h>
#include <Arduino.h>

class SimpleCalibration {
private:
    Preferences nvs;
    
public:
    void initNVS() {
        nvs.begin("cal", false);
    }
    
    void saveOffsets(float theta, float phi, float wire_mm) {
        nvs.putFloat("theta", theta);
        nvs.putFloat("phi", phi);
        nvs.putFloat("wire", wire_mm);
        Serial.println("Calibration saved");
    }
    
    bool loadOffsets(float& theta, float& phi, float& wire_mm) {
        if (!nvs.isKey("theta")) {
            return false;  // Not calibrated
        }
        theta = nvs.getFloat("theta", 0.0f);
        phi = nvs.getFloat("phi", 0.0f);
        wire_mm = nvs.getFloat("wire", 0.0f);
        return true;
    }
    
    void closeNVS() {
        nvs.end();
    }
};

// Usage in main
void setup() {
    Serial.begin(115200);
    
    SimpleCalibration cal;
    cal.initNVS();
    
    float theta_off, phi_off, wire_off;
    if (cal.loadOffsets(theta_off, phi_off, wire_off)) {
        Serial.printf("Loaded: theta=%.2f, phi=%.2f, wire=%.2f\n", 
                     theta_off, phi_off, wire_off);
    } else {
        Serial.println("No calibration found, using defaults");
        cal.saveOffsets(0.0f, 0.0f, 0.0f);
    }
    
    cal.closeNVS();
}
```

### Example 2: Multi-Profile Calibration (Different Namespaces)

```cpp
// multi_profile_example.cpp
#include <Preferences.h>

class MultiProfileCalibration {
private:
    Preferences nvs;
    
public:
    /**
     * Save calibration for specific profile
     * profiles: "profile_a", "profile_b", etc.
     */
    void saveProfile(const char* profile_name, 
                    float theta, float phi, float wire_mm) {
        nvs.begin(profile_name, false);
        nvs.putFloat("theta", theta);
        nvs.putFloat("phi", phi);
        nvs.putFloat("wire", wire_mm);
        nvs.end();
        Serial.printf("Profile '%s' saved\n", profile_name);
    }
    
    /**
     * Load calibration for specific profile
     */
    bool loadProfile(const char* profile_name, 
                    float& theta, float& phi, float& wire_mm) {
        nvs.begin(profile_name, true);  // Read-only
        
        if (!nvs.isKey("theta")) {
            nvs.end();
            return false;
        }
        
        theta = nvs.getFloat("theta", 0.0f);
        phi = nvs.getFloat("phi", 0.0f);
        wire_mm = nvs.getFloat("wire", 0.0f);
        nvs.end();
        return true;
    }
    
    /**
     * List all stored profiles
     */
    void listProfiles() {
        Serial.println("Available profiles:");
        // Note: Standard Preferences API doesn't iterate namespaces,
        // so you'd need to maintain a "profiles_list" key
    }
    
    /**
     * Delete profile
     */
    void deleteProfile(const char* profile_name) {
        nvs.begin(profile_name, false);
        nvs.clear();
        nvs.end();
        Serial.printf("Profile '%s' deleted\n", profile_name);
    }
};

// Usage
MultiProfileCalibration cal;

// Save different calibrations
cal.saveProfile("indoor", 0.5f, -1.0f, 0.0f);
cal.saveProfile("outdoor", 0.2f, 0.5f, 0.1f);

// Load specific profile
float theta, phi, wire;
if (cal.loadProfile("indoor", theta, phi, wire)) {
    Serial.printf("Loaded indoor profile: theta=%f\n", theta);
}
```

### Example 3: Timestamp & Version Control

```cpp
// versioned_calibration_example.cpp
#include <Preferences.h>
#include <time.h>

class VersionedCalibration {
private:
    Preferences nvs;
    static const uint32_t CALIBRATION_VERSION = 1;
    
public:
    struct CalData {
        uint32_t version;
        uint32_t timestamp_unix;
        float theta_offset;
        float phi_offset;
        float wire_scale;
        float wire_offset;
    };
    
    bool save(const CalData& cal) {
        nvs.begin("cal_versioned", false);
        
        // Store version for compatibility checks
        nvs.putUInt("version", cal.version);
        nvs.putUInt("timestamp", cal.timestamp_unix);
        nvs.putFloat("theta_off", cal.theta_offset);
        nvs.putFloat("phi_off", cal.phi_offset);
        nvs.putFloat("wire_scale", cal.wire_scale);
        nvs.putFloat("wire_off", cal.wire_offset);
        
        // Increment write counter (debug)
        uint32_t writes = nvs.getUInt("write_count", 0);
        nvs.putUInt("write_count", writes + 1);
        
        nvs.end();
        return true;
    }
    
    bool load(CalData& cal) {
        nvs.begin("cal_versioned", true);  // Read-only
        
        uint32_t stored_version = nvs.getUInt("version", 0);
        if (stored_version != CALIBRATION_VERSION) {
            Serial.printf("Version mismatch: expected %u, got %u\n", 
                         CALIBRATION_VERSION, stored_version);
            nvs.end();
            return false;
        }
        
        cal.version = stored_version;
        cal.timestamp_unix = nvs.getUInt("timestamp", 0);
        cal.theta_offset = nvs.getFloat("theta_off", 0.0f);
        cal.phi_offset = nvs.getFloat("phi_off", 0.0f);
        cal.wire_scale = nvs.getFloat("wire_scale", 1.0f);
        cal.wire_offset = nvs.getFloat("wire_off", 0.0f);
        
        nvs.end();
        return true;
    }
    
    /**
     * Print human-readable calibration info
     */
    void printInfo() {
        nvs.begin("cal_versioned", true);
        
        time_t cal_time = nvs.getUInt("timestamp", 0);
        struct tm* timeinfo = localtime(&cal_time);
        char time_str[32];
        strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", timeinfo);
        
        Serial.println("=== Calibration Info ===");
        Serial.printf("Version: %u\n", nvs.getUInt("version", 0));
        Serial.printf("Timestamp: %s\n", time_str);
        Serial.printf("Theta Offset: %.6f°\n", nvs.getFloat("theta_off", 0.0f));
        Serial.printf("Phi Offset: %.6f°\n", nvs.getFloat("phi_off", 0.0f));
        Serial.printf("Wire Scale: %.6f\n", nvs.getFloat("wire_scale", 1.0f));
        Serial.printf("Wire Offset: %.6f mm\n", nvs.getFloat("wire_off", 0.0f));
        Serial.printf("Total Writes: %u\n", nvs.getUInt("write_count", 0));
        
        nvs.end();
    }
};

// Usage
VersionedCalibration vcal;

VersionedCalibration::CalData cal_data = {
    .version = 1,
    .timestamp_unix = time(nullptr),
    .theta_offset = 0.25f,
    .phi_offset = -0.75f,
    .wire_scale = 1.0025f,
    .wire_offset = 0.5f
};

vcal.save(cal_data);
vcal.printInfo();
```

---

## EEPROM vs NVS

| Aspect | EEPROM Emulation | NVS |
|---|---|---|
| **Implementation** | RAM image flushed to flash | Direct NVS driver |
| **Partition** | Generic data partition | Dedicated NVS partition |
| **Wear Leveling** | Manual (must manage) | Automatic |
| **Type Support** | Byte array only | Native types (float, int) |
| **Size** | Limited (e.g., 4 KB) | Up to 512 KB typical |
| **Speed** | Slower (RAM copy) | Faster (direct write) |
| **Fragmentation** | Can occur | Minimal |

### When to Use EEPROM Emulation
- Legacy code compatibility
- Very small data (< 1 KB)
- No type variation needed

### When to Use NVS
- ✅ **Modern ESP32 code** (RECOMMENDED)
- ✅ Calibration data (mixed types)
- ✅ Configuration parameters
- ✅ User settings

---

## Production Checklist

- [ ] **Calibration Data Structure**: Define struct with all parameters (offsets, scales, timestamps)
- [ ] **Namespace Choice**: Pick unique namespace (e.g., "evka_cal", "motor_cal")
- [ ] **Default Values**: Provide sensible fallbacks if NVS empty
- [ ] **Error Handling**: Check return values from nvs_get_* calls
- [ ] **Versioning**: Store version number for future compatibility
- [ ] **Timestamp**: Record when calibration was performed
- [ ] **Wear Leveling**: Confirm NVS partition size sufficient (16 KB min)
- [ ] **Testing**: Verify save/load across power cycles
- [ ] **Documentation**: Comment calibration procedure for users
- [ ] **Reset Mechanism**: Provide command to clear NVS (calibration reset)
- [ ] **Validation Flag**: Store boolean indicating calibration status
- [ ] **Performance**: Measure NVS access time (typically < 10 ms)

### Pre-Flight Commands

```cpp
// Add to your serial command handler:

void handleSerialCommand(const char* cmd) {
    if (strcmp(cmd, "CAL_SAVE") == 0) {
        // Save current calibration
        float theta = getThetaOffset();
        float phi = getPhiOffset();
        float wire = getWireScale();
        
        cal_mgr.begin();
        if (cal_mgr.save({theta, phi, wire, 0.0f, time(nullptr), 1})) {
            Serial.println("OK: Calibration saved to NVS");
        } else {
            Serial.println("ERROR: Save failed");
        }
        cal_mgr.end();
    }
    else if (strcmp(cmd, "CAL_LOAD") == 0) {
        cal_mgr.begin();
        CalibrationData cal;
        if (cal_mgr.load(cal)) {
            Serial.println("OK: Calibration loaded from NVS");
            cal_mgr.printAll();
        } else {
            Serial.println("ERROR: No valid calibration in NVS");
        }
        cal_mgr.end();
    }
    else if (strcmp(cmd, "CAL_RESET") == 0) {
        cal_mgr.begin();
        cal_mgr.reset();
        cal_mgr.end();
        Serial.println("OK: Calibration reset");
    }
    else if (strcmp(cmd, "CAL_INFO") == 0) {
        cal_mgr.begin();
        cal_mgr.printAll();
        cal_mgr.end();
    }
}
```

---

## References

- **ESP-IDF NVS Documentation**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/nvs_flash.html
- **Preferences Library**: Built-in to Arduino-ESP32
- **Wear Leveling White Paper**: Infineon/Kioxia SPI NOR specifications
- **Partition Manager**: Arduino IDE → Tools → Partition Scheme

---

## Summary

| Task | Best Approach | Code |
|---|---|---|
| Store calibration offsets | Preferences library | `nvs.putFloat()` / `getFloat()` |
| Multiple calibration sets | Namespaces | `nvs.begin("profile_a", false)` |
| Non-linear calibration curve | Float array as blob | `nvs.putBlob()` |
| Version tracking | Add version key | `nvs.putUInt("version", 1)` |
| Wear leveling | Automatic (NVS) | No action needed |
| Reset calibration | `nvs.clear()` | Call in reset handler |

**Next Steps**:
1. Integrate `CalibrationManager` class into your `SphericalSensor`
2. Add serial commands for `CAL_SAVE`, `CAL_LOAD`, `CAL_RESET`
3. Increase NVS partition to 32 KB if continuous recalibration expected
4. Test across power cycles

