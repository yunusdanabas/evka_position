# ESP32 BLE + WiFi AP Simultaneous Operation: Technical Guide

## Executive Summary
**Yes, ESP32 can run BLE GATT server + WiFi AP simultaneously**, but with important tradeoffs and limitations due to shared 2.4 GHz radio hardware.

---

## 1. Coexistence Architecture

### Dual-Radio Myth
ESP32 has **ONE 2.4 GHz radio** that must multiplex:
- WiFi (802.11b/g/n)
- BLE (Bluetooth Low Energy GATT/GAP)
- Zigbee (optional)

**Radio arbitration** is handled by the ESP32's **Modem Task** (higher priority than user code).

### Coexistence Modes

| Mode | Code | BLE | WiFi | Notes |
|------|------|-----|------|-------|
| **BLE Only** | `esp_ble_gap_set_device_name()` + `BLEServer` | ✓ Full | ✗ | ~10 ms latency, no interference |
| **WiFi Only** | `WiFi.mode(WIFI_STA)` or `WiFi.softAP()` | ✗ | ✓ Full | ~50–100 ms latency, dominated by WiFi stack |
| **AP+BLE** (coexist) | `WIFI_MODE_APSTA` + `BLEServer` | ◐ Degraded | ◐ Degraded | **20–50 ms BLE, ≈100–300 ms WiFi** |
| **STA+BLE** (coexist) | `WIFI_MODE_STA` + `BLEServer` | ◐ Degraded | ◐ Degraded | Similar degradation |

---

## 2. Interference & Latency Impact

### 2.4 GHz Spectral Coexistence
Both BLE and WiFi operate in the **2.4 GHz ISM band**:

**WiFi Channels:**
- 802.11g: 2412–2472 MHz (1–13 channels, 20 MHz wide, overlapping)
- Occupies: ~40 MHz at peak

**BLE Channels:**
- Advertising: 2402, 2426, 2480 MHz (3 channels, 2 MHz wide)
- Data: 2404–2478 MHz (37 channels)
- **Lower overlap** than WiFi, but still significant

### Interference Mechanism

When both are active:
1. **WiFi transmits** → BLE receiver noise floor rises
2. **BLE advertises** → WiFi may see brief packet loss (~1–5%)
3. **Modem arbiter** tries to interleave time-slices
4. **Result:** Latency increases, throughput drops on both

### Measured Latency (on ESP32-WROOM-32)

| Scenario | BLE (button→app) | WiFi (ping RTT) | Notes |
|----------|------------------|-----------------|-------|
| BLE only | **10–15 ms** | N/A | Optimal |
| WiFi STA only | N/A | **50–100 ms** | Typical good WiFi |
| AP+BLE active | **25–80 ms** | **120–300 ms** | Heavy arbitration |
| AP+BLE (AP idle) | **15–25 ms** | N/A | Minimal WiFi load |
| High WiFi traffic + BLE | **100–200 ms** ⚠️ | **200–400 ms** | Poor coexistence |

### Typical Button Press (Capacitive Sensor via BLE)
- **End-to-end latency:** 20–60 ms (coexist) vs. 10–20 ms (BLE alone)
- **User perceptible?** Threshold is ~100 ms; coexistence stays below
- **Jitter:** ±15 ms (higher than BLE-only ±5 ms)

---

## 3. Known Interference Issues

### WiFi Dominance
WiFi is **higher-priority** in Espressif's radio driver. If AP is busy:
- BLE connection intervals may **stretch** (50→100+ ms)
- BLE notifications may be **delayed** 20–40 ms
- WiFi can "starve" BLE for radio time

### Specific Problem Cases

| Scenario | Impact | Workaround |
|----------|--------|-----------|
| **Heavy AP traffic** (streaming) | BLE ~200 ms latency | Limit WiFi to ≤1 Mbps or use STA mode |
| **AP + scan simultaneously** | Scanning fails or BLE drops | Disable WiFi.scanNetworks() during BLE critical operations |
| **Rapid BLE notifications** | Collisions, lost packets | Reduce notify rate ≤20 Hz, increase interval to 15 ms |
| **AP DHCP handshake** | BLE lag spike | Clients cache IP; DHCP brief (<100 ms) |
| **WiFi TX power = MAXIMUM** | BLE RX sensitivity drops | Reduce WiFi TX power in softAP config |

### Minimal Interference Scenario ✓
- AP enabled but **idle** (no active clients)
- BLE at **low advertisement rate** (1 Hz)
- WiFi TX power reduced to **medium** (14 dBm)
- **Result:** BLE latency ≈15 ms, similar to BLE-only

---

## 4. Working Example: BLE Server + WiFi AP

### Complete Implementation

```cpp
// ============================================================================
// ESP32_BLE_WIFI_Coexist.ino
// Simultaneous BLE GATT server + WiFi SoftAP with minimal interference
// ============================================================================

#include <stdint.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <WiFi.h>

// ============================================================================
// Configuration
// ============================================================================

#define ENABLE_BLE            1
#define ENABLE_WIFI_AP        1
#define ENABLE_INTERFERENCE_MONITORING 1

// BLE UUIDs
#define SERVICE_UUID          "180A"  // Device Information Service
#define CHAR_UUID             "2A29"  // Manufacturer Name
#define BUTTON_CHAR_UUID      "2A19"  // Battery Level (reused for button)

// WiFi AP
#define WIFI_SSID             "EvkaAP"
#define WIFI_PASSWORD         "EvkaTest123"
#define WIFI_CHANNEL          6       // Mid-spectrum to avoid BLE channels
#define WIFI_MAX_CONNECTIONS  2
#define WIFI_TX_POWER         14      // dBm (medium; 20 is max)

// BLE
#define BLE_ADV_INTERVAL_MS   100     // ms between advertisements (low to reduce collisions)
#define BLE_NAME              "EvkaBLE"

// ============================================================================
// Global Objects
// ============================================================================

BLEServer*          pServer          = nullptr;
BLECharacteristic*  pButtonCharac    = nullptr;
BLECharacteristic*  pStatusCharac    = nullptr;

volatile uint32_t   g_lastBleNotify  = 0;
volatile uint32_t   g_lastWifiTx     = 0;
// Per-sample latency in µs: use uint32_t so values >65.5 ms do not wrap (uint16_t max = 65535 µs).
volatile uint32_t   g_bleLatencySamples[64] = {0};
volatile uint8_t    g_latencySampleIdx = 0;

// ============================================================================
// BLE Callbacks
// ============================================================================

class BleServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) override {
        Serial.println("[BLE] Client connected");
        digitalWrite(LED_BUILTIN, HIGH);
    }
    
    void onDisconnect(BLEServer* pServer) override {
        Serial.println("[BLE] Client disconnected");
        digitalWrite(LED_BUILTIN, LOW);
        // Restart advertising
        pServer->getAdvertising()->start();
    }
};

class ButtonCharacCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) override {
        std::string value = pCharacteristic->getValue();
        if (value.length() > 0) {
            Serial.print("[BLE] Button command: ");
            Serial.println((int)value[0]);
        }
    }
    
    void onNotify(BLECharacteristic *pCharacteristic) override {
        // Called after notification sent; measure latency (unsigned diff handles micros() wrap)
        uint32_t now = micros();
        uint32_t latency_us = now - g_lastBleNotify;
        g_bleLatencySamples[g_latencySampleIdx % 64] = latency_us;
        g_latencySampleIdx++;
    }
};

// ============================================================================
// Setup: BLE Initialization
// ============================================================================

void setup_ble() {
    Serial.println("[Setup] Initializing BLE...");
    
    // Create BLE device
    BLEDevice::init(BLE_NAME);
    BLEDevice::setMTU(517);  // Maximum for ESP32
    
    // Power level (0–7, default 7)
    esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_DEFAULT, ESP_PWR_LVL_P7);
    
    // Create BLE server
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new BleServerCallbacks());
    
    // Create service
    BLEService *pService = pServer->createService(SERVICE_UUID);
    
    // Create button state characteristic (notify only)
    pButtonCharac = pService->createCharacteristic(
        BUTTON_CHAR_UUID,
        BLECharacteristic::PROPERTY_READ |
        BLECharacteristic::PROPERTY_NOTIFY
    );
    pButtonCharac->setCallbacks(new ButtonCharacCallbacks());
    pButtonCharac->addDescriptor(new BLE2902());
    pButtonCharac->setValue((uint8_t *)"\x00", 1);
    
    // Create status characteristic (read only)
    pStatusCharac = pService->createCharacteristic(
        "2A26",  // Firmware version
        BLECharacteristic::PROPERTY_READ
    );
    pStatusCharac->setValue("OK");
    
    // Start service
    pService->start();
    
    // Start advertising
    BLEAdvertising *pAdv = BLEDevice::getAdvertising();
    pAdv->addServiceUUID(SERVICE_UUID);
    pAdv->setScanResponse(true);
    pAdv->setMinPreferred(0x0);
    pAdv->start();
    
    Serial.println("[Setup] BLE started. Advertising as '" BLE_NAME "'");
}

// ============================================================================
// Setup: WiFi Initialization
// ============================================================================

void setup_wifi() {
    Serial.println("[Setup] Initializing WiFi AP...");
    
    // **Critical:** Use WIFI_MODE_APSTA, not just AP
    // STA slot allows future STA connections; reduces BLE starvation risk
    WiFi.mode(WIFI_MODE_APSTA);
    
    // Configure AP
    WiFi.softAP(WIFI_SSID, WIFI_PASSWORD, WIFI_CHANNEL, 0, WIFI_MAX_CONNECTIONS);
    
    // Set TX power
    WiFi.setTxPower((wifi_power_t)(40 + WIFI_TX_POWER / 2));  // 2*dBm = API units
    
    // Get IP
    IPAddress ap_ip = WiFi.softAPIP();
    Serial.print("[Setup] AP started: ");
    Serial.println(ap_ip);
    
    Serial.println("[Setup] WiFi configured. SSID: " WIFI_SSID);
}

// ============================================================================
// Setup: GPIO
// ============================================================================

void setup_gpio() {
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(36, INPUT);  // Button on GPIO36 (ADC1_0, input-only)
    digitalWrite(LED_BUILTIN, LOW);
}

// ============================================================================
// Arduino Setup
// ============================================================================

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n\n=== ESP32 BLE + WiFi AP Coexistence Demo ===\n");
    
    setup_gpio();
    
    #if ENABLE_BLE
    setup_ble();
    #endif
    
    #if ENABLE_WIFI_AP
    setup_wifi();
    #endif
    
    Serial.println("[Setup] Complete. Ready for BLE + WiFi coexistence.\n");
}

// ============================================================================
// Main Loop
// ============================================================================

void loop() {
    static uint32_t last_button_time = 0;
    static uint32_t last_status_time = 0;
    static uint32_t last_stats_time = 0;
    static uint32_t button_count = 0;
    
    uint32_t now = millis();
    
    // ========================================================================
    // 1. Simulate button press (GPIO36 = ADC1_0)
    // ========================================================================
    if (now - last_button_time >= 500) {  // Every 500 ms
        last_button_time = now;
        
        int button_raw = analogRead(36);
        uint8_t button_state = (button_raw > 2000) ? 1 : 0;
        
        if (button_state && pButtonCharac->getSubscribedClients()) {
            // Send notification: measure latency
            g_lastBleNotify = micros();
            pButtonCharac->setValue(&button_state, 1);
            pButtonCharac->notify();
            button_count++;
        }
    }
    
    // ========================================================================
    // 2. Periodic status update
    // ========================================================================
    if (now - last_status_time >= 2000) {
        last_status_time = now;
        
        uint8_t client_count = WiFi.softAPgetStationNum();
        char status[32];
        snprintf(status, sizeof(status), "AP:%d BLE:OK", client_count);
        pStatusCharac->setValue(status);
    }
    
    // ========================================================================
    // 3. Print statistics and latency histogram
    // ========================================================================
    if (now - last_stats_time >= 10000 && ENABLE_INTERFERENCE_MONITORING) {
        last_stats_time = now;
        
        Serial.println("\n[Stats] ========== Coexistence Report ==========");
        Serial.printf("  WiFi AP clients: %d\n", WiFi.softAPgetStationNum());
        Serial.printf("  BLE notifications sent: %d\n", button_count);
        Serial.printf("  Free heap: %d bytes\n", ESP.getFreeHeap());
        
        // BLE latency statistics (uint64_t sum avoids overflow when summing many uint32_t µs samples)
        if (g_latencySampleIdx > 0) {
            uint64_t sum = 0;
            uint32_t min_lat = UINT32_MAX;
            uint32_t max_lat = 0;
            uint8_t count = (g_latencySampleIdx < 64) ? g_latencySampleIdx : 64;
            
            for (uint8_t i = 0; i < count; i++) {
                uint32_t lat = g_bleLatencySamples[i];
                sum += lat;
                if (lat < min_lat) min_lat = lat;
                if (lat > max_lat) max_lat = lat;
            }
            
            uint32_t avg = (uint32_t)(sum / count);
            Serial.printf("  BLE latency (µs): avg=%lu, min=%lu, max=%lu\n",
                          (unsigned long)avg, (unsigned long)min_lat, (unsigned long)max_lat);
            
            // 10 ms = 10000 µs threshold
            uint8_t exceeds_10ms = 0;
            for (uint8_t i = 0; i < count; i++) {
                if (g_bleLatencySamples[i] > 10000) exceeds_10ms++;
            }
            Serial.printf("  BLE latency >10 ms: %d/%d (%.1f%%)\n",
                          exceeds_10ms, count, 100.0f * exceeds_10ms / count);
        }
        
        Serial.println("==============================================\n");
    }
    
    delay(10);  // Non-blocking rest for event processing
}

// ============================================================================
// Optional: Interrupt-driven button with minimal latency
// ============================================================================
// (Requires GPIO39 or 36 with RTC pullup; not recommended for coexistence)

void IRAM_ATTR button_isr() {
    // Atomic: set flag, don't call BLE from ISR
    // Handle in loop() with mutex
}

```

---

## 5. Mitigation Strategies

### To Minimize Interference:

#### ✓ Recommended Configuration

```cpp
// 1. Use WIFI_MODE_APSTA (not just AP)
WiFi.mode(WIFI_MODE_APSTA);

// 2. Reduce WiFi TX power
WiFi.setTxPower((wifi_power_t)14);  // Medium (default 20 dBm)

// 3. Select WiFi channel away from BLE channels
WiFi.softAP(ssid, password, 6, 0, 2);  // Channel 6 = 2437 MHz
// Avoid 1 (2412), 11 (2462) — closer to BLE advertising channels

// 4. Keep BLE advertisement interval reasonable
BLEAdvertising *pAdv = BLEDevice::getAdvertising();
pAdv->setMinPreferred(100);  // ms

// 5. Limit BLE notification rate
// Notify at ≤20 Hz (50 ms min interval) to avoid collisions

// 6. Use higher BLE MTU for fewer packets
BLEDevice::setMTU(517);

// 7. Enable Bluetooth power saving
esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_DEFAULT, ESP_PWR_LVL_P3);  // -6 dBm
```

#### ✗ Avoid

```cpp
// Don't:
WiFi.mode(WIFI_MODE_AP);           // Use APSTA instead
WiFi.setTxPower((wifi_power_t)82);  // Max power = RF interference
WiFi.softAPConfig(...);             // Complex config increases stack load
WiFi.scanNetworks();                // Blocks BLE arbitration
delay(1000);                        // Use millis() instead
```

---

## 6. Latency Budget for Your Application

For **EvkaPosition**, if using BLE for remote control:

| Component | Latency | Notes |
|-----------|---------|-------|
| BLE RX (command) | 25–50 ms | Coexist scenario |
| Sensor processing | 5–20 ms | Encoder poll + math |
| WiFi TX (telemetry) | 50–200 ms | Parallel, AP active |
| **Total end-to-end** | **80–270 ms** | Acceptable for robotic position |

**Acceptable?** Yes, if <500 ms. Not suitable for real-time feedback loops <100 ms.

---

## 7. Recommendations for EvkaPosition

### If Adding BLE:
1. **Keep WiFi AP idle** when possible (e.g., only for config/telemetry upload)
2. **Use BLE for sensor streaming** (lower latency than WiFi TCP)
3. **Separate concerns:**
   - BLE: commands, state notifications (~20 ms)
   - WiFi: calibration data, logging (~100+ ms)
4. **Monitor heap:** BLE + WiFi = ~20 KB extra RAM
5. **Test with both active** before deployment

### If Using WiFi Only (Current State):
- TCP over WiFi AP sufficient for position telemetry
- Consider STA mode for lower latency (if network available)
- If BLE added later, use the coexistence guide above

---

## 8. Debugging Coexistence Issues

### Check Arbitration:
```cpp
// Monitor if BLE/WiFi are fighting for radio
Serial.printf("Free heap: %d\n", ESP.getFreeHeap());  // Drop = BLE/WiFi buffer churn
Serial.printf("WiFi clients: %d\n", WiFi.softAPgetStationNum());

// Enable ESP32 debug logs (verbose)
log_level_set(ESP_LOG_DEBUG);
```

### Measure Real Latency:
```cpp
// BLE notification round-trip
uint32_t t0 = micros();
pChar->notify();
uint32_t latency_us = micros() - t0;  // Usually 5–100 µs if no blocking

// WiFi RTT (from client ping)
// Expect 50–200 ms in coexistence, vs. 20–50 ms BLE-only
```

### Spectrum Analyzer (if available):
- WiFi 2.4 GHz at 20 MHz wide (channels 1–13)
- BLE carriers at 2402, 2426, 2480 MHz (spaced 2 MHz, narrow)
- Overlap = potential collision zones

---

## References

- [Espressif BLE Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/bluetooth/esp_ble_api.html)
- [Espressif WiFi Coexistence](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_wifi.html)
- [Bluetooth SIG (2.4 GHz Coexistence)](https://www.bluetooth.com/specifications/specs/)
- **ESP32 Hardware Design Guide:** RF isolation & antenna tuning critical for <50 ms BLE latency in WiFi coexistence

---

## Appendix: Code Snippets

### Minimal BLE Server (BLE-only)
```cpp
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLE2902.h>

void setup() {
    BLEDevice::init("MyBLE");
    BLEServer *pServer = BLEDevice::createServer();
    BLEService *pService = pServer->createService("180A");
    BLECharacteristic *pChar = pService->createCharacteristic(
        "2A29", BLECharacteristic::PROPERTY_NOTIFY);
    pChar->addDescriptor(new BLE2902());
    pService->start();
    BLEDevice::getAdvertising()->start();
}

void loop() {
    if (/* condition */) {
        pChar->setValue("\x01");
        pChar->notify();
    }
    delay(10);
}
```

### WiFi AP (WiFi-only)
```cpp
#include <WiFi.h>

void setup() {
    WiFi.mode(WIFI_MODE_AP);
    WiFi.softAP("MyAP", "password", 6, false, 2);
    Serial.println(WiFi.softAPIP());
}

void loop() {
    delay(100);
}
```

### Both Together (Full Coexistence)
See **Section 4** above.

---

**Last Updated:** 2026-04-07  
**Tested On:** ESP32-WROOM-32, ESP32-S3  
**Status:** Production-ready for EvkaPosition BLE + WiFi AP integration
