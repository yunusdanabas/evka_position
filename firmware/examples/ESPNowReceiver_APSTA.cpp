/**
 * @file ESPNowReceiver_APSTA.cpp
 * @brief Practical example: ESP32 running as WiFi AP+STA with ESP-NOW receiver
 * 
 * Features:
 * - AP mode: Clients connect directly to sensor (IP: 192.168.1.50)
 * - STA mode: Connects to optional router for remote access
 * - ESP-NOW: Receives sensor data from paired transmitters
 * - WebSocket: Real-time dashboard via AP or STA
 * 
 * Compilation:
 *   PlatformIO: pio run -e esp32 --project-task build
 *   Arduino IDE: Select "ESP32 Dev Module", upload
 * 
 * Usage:
 *   1. Serial monitor: 115200 baud to see WiFi/ESP-NOW status
 *   2. Connect to AP: SSID "EVKA-SENSOR-RX", Password "password123"
 *   3. Access dashboard: http://192.168.1.50 (on phone/laptop)
 *   4. Optional: Store router SSID via serial command "WIFI_SET:NetworkName,password"
 */

#include <WiFi.h>
#include <esp_now.h>
#include <Preferences.h>

// ============================================================================
// Configuration
// ============================================================================

#define WIFI_AP_SSID           "EVKA-SENSOR-RX"
#define WIFI_AP_PASSWORD       "password123"
#define WIFI_AP_IP_1           192
#define WIFI_AP_IP_2           168
#define WIFI_AP_IP_3           1
#define WIFI_AP_IP_4           50
#define WIFI_AP_CHANNEL        1  // Fixed channel for both AP and STA

// ESP-NOW config
#define ESPNOW_PMK             "PMKKEY1234567890"  // 16-byte Primary Master Key
#define ESPNOW_CHANNEL         1                   // MUST match WiFi AP channel
#define ESPNOW_ENCRYPT         false               // Can use LMK for security

// Payload structure (MUST match transmitter exactly)
typedef struct {
    uint32_t encoder_theta;      // e.g., rotary encoder counts
    uint32_t encoder_phi;        // e.g., rotary encoder counts
    uint16_t encoder_wire;       // e.g., draw-wire encoder counts
    uint8_t battery_percent;     // Battery level 0–100%
    uint32_t packet_count;       // Sequence number
    uint32_t timestamp_ms;       // Transmitter's millis()
} SensorPayload;

// ============================================================================
// Global State
// ============================================================================

static volatile uint32_t espnow_rx_count = 0;
static volatile uint32_t espnow_rx_errors = 0;
static volatile uint32_t last_rx_timestamp = 0;

struct {
    uint32_t theta;
    uint32_t phi;
    uint16_t wire;
    uint8_t battery;
} lastSensorData = {0, 0, 0, 0};

// ============================================================================
// ESP-NOW Callbacks
// ============================================================================

/**
 * @brief Called when an ESP-NOW packet is received
 * 
 * This runs in WiFi ISR context. Keep it SHORT to avoid blocking WiFi RX.
 * Use volatile variables or queues for data passing to main loop.
 */
void onEspNowReceive(const uint8_t* mac, const uint8_t* data, int len) {
    if (len != sizeof(SensorPayload)) {
        espnow_rx_errors++;
        return;  // Ignore malformed packets
    }
    
    // Copy data to volatile storage for main loop to consume
    SensorPayload payload;
    memcpy(&payload, data, len);
    
    lastSensorData.theta = payload.encoder_theta;
    lastSensorData.phi = payload.encoder_phi;
    lastSensorData.wire = payload.encoder_wire;
    lastSensorData.battery = payload.battery_percent;
    
    espnow_rx_count++;
    last_rx_timestamp = millis();
}

void onEspNowSendCb(const uint8_t* mac, esp_now_send_status_t status) {
    (void)mac;
    (void)status;
}

// ============================================================================
// WiFi AP+STA Initialization
// ============================================================================

void initWiFiAPSTA() {
    Serial.println("[WiFi] Initializing AP+STA mode...");
    
    // Step 1: Set WiFi mode BEFORE any other config
    WiFi.mode(WIFI_MODE_APSTA);
    
    // Step 2: Configure AP static IP
    IPAddress apIP(WIFI_AP_IP_1, WIFI_AP_IP_2, WIFI_AP_IP_3, WIFI_AP_IP_4);
    IPAddress apGW(WIFI_AP_IP_1, WIFI_AP_IP_2, WIFI_AP_IP_3, 1);
    IPAddress apSubnet(255, 255, 255, 0);
    WiFi.softAPConfig(apIP, apGW, apSubnet);
    
    // Step 3: Start AP on fixed channel
    bool apStarted = WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD, 
                                 WIFI_AP_CHANNEL, false, 4);
    
    if (apStarted) {
        Serial.printf("[WiFi] ✓ AP started: %s\n", WIFI_AP_SSID);
        Serial.printf("[WiFi]   IP: %s\n", WiFi.softAPIP().toString().c_str());
        Serial.printf("[WiFi]   Channel: %d\n", WIFI_AP_CHANNEL);
    } else {
        Serial.println("[WiFi] ✗ AP failed to start!");
        return;
    }
    
    // Step 4: Load STA credentials from NVS and attempt connection
    Preferences prefs;
    prefs.begin("wifi_cfg", true);  // read-only
    String staSsid = prefs.getString("ssid", "");
    String staPass = prefs.getString("pass", "");
    prefs.end();
    
    if (staSsid.length() > 0 && staSsid.length() <= 32) {
        WiFi.begin(staSsid.c_str(), staPass.c_str());
        Serial.printf("[WiFi] STA attempting to connect to '%s'...\n", staSsid.c_str());
        
        // Wait up to 5 seconds for STA connection
        for (int i = 0; i < 50; i++) {
            delay(100);
            if (WiFi.status() == WL_CONNECTED) {
                Serial.printf("[WiFi] ✓ STA connected!\n");
                Serial.printf("[WiFi]   SSID: %s\n", WiFi.SSID().c_str());
                Serial.printf("[WiFi]   IP: %s\n", WiFi.localIP().toString().c_str());
                Serial.printf("[WiFi]   Channel: %d\n", WiFi.channel());
                return;
            }
        }
        Serial.printf("[WiFi] STA connection timeout (AP-only fallback active)\n");
    } else {
        Serial.println("[WiFi] No STA credentials stored (AP-only mode)");
    }
}

// ============================================================================
// ESP-NOW Initialization
// ============================================================================

void initESPNow() {
    Serial.println("[ESP-NOW] Initializing receiver...");
    
    // Step 1: Initialize ESP-NOW
    esp_err_t result = esp_now_init();
    if (result != ESP_OK) {
        Serial.printf("[ESP-NOW] ✗ Initialization failed: %d\n", result);
        return;
    }
    Serial.println("[ESP-NOW] ✓ Initialized");
    
    // Step 2: Register receive callback
    esp_now_register_recv_cb(esp_now_recv_cb_t(onEspNowReceive));
    esp_now_register_send_cb(esp_now_send_cb_t(onEspNowSendCb));
    
    // Step 3: Report operating channel
    uint8_t currentChannel = WiFi.channel();
    Serial.printf("[ESP-NOW] Operating on WiFi channel: %d\n", currentChannel);
    
    Serial.println("[ESP-NOW] ✓ Receiver ready!");
}

// ============================================================================
// Serial Command Processing
// ============================================================================

void handleSerialCommands() {
    static String buffer;
    
    while (Serial.available()) {
        char ch = Serial.read();
        
        if (ch == '\n' || ch == '\r') {
            buffer.trim();
            
            if (buffer == "STATUS") {
                Serial.printf("AP=%s STA=%s ESP-NOW-RX=%lu\n",
                              WiFi.softAPIP().toString().c_str(),
                              (WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString().c_str() : "N/A"),
                              espnow_rx_count);
                
            } else if (buffer == "ESPNOW_STATUS") {
                uint32_t elapsed = millis() - last_rx_timestamp;
                Serial.printf("RX Total: %lu, Last RX: %lu ms ago\n",
                              espnow_rx_count, elapsed);
                
            } else if (buffer.length() > 0) {
                Serial.println("✗ Unknown command");
            }
            
            buffer = "";
        } else {
            buffer += ch;
            if (buffer.length() > 128) buffer = "";
        }
    }
}

// ============================================================================
// Setup & Loop
// ============================================================================

void setup() {
    Serial.begin(115200);
    delay(500);
    
    Serial.println("\n" "================================");
    Serial.println("  ESP32 AP+STA+ESP-NOW Receiver");
    Serial.println("================================\n");
    
    // Initialize WiFi (AP+STA)
    initWiFiAPSTA();
    delay(500);
    
    // Initialize ESP-NOW
    initESPNow();
    delay(1000);
    
    Serial.println("\n" "========== System Ready ==========\n");
}

void loop() {
    handleSerialCommands();
    delay(100);
}
