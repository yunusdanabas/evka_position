// ============================================================================
// EvkaPosition — Wireless Button Remote (ESP-NOW Sender)
// ============================================================================
// Target: ESP32-C3 (Seeed XIAO ESP32-C3 or ESP32-C3 SuperMini)
// Always-awake mode: ESP-NOW initialised once at startup.
// Sends a single byte (button index 0–4) on each confirmed press edge.
//
// Button wiring: Each button connects GPIO → GND (internal pull-up enabled).
// ============================================================================

#include <Arduino.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <WiFi.h>

// ============================================================================
// CONFIGURATION
// ============================================================================

// Number of buttons and GPIO assignments.
// Safe GPIOs on ESP32-C3: avoids strapping pins (2, 9), serial (6, 7), LED (8).
#define BTN_COUNT     5

// LED feedback pin — GPIO 8 = built-in blue LED on ESP32-C3 SuperMini
#define PIN_LED       8

// WiFi channel — fallback if AP scan fails
#define ESPNOW_CHANNEL   1
// Main ESP32 AP SSID — scanned at startup to find the actual WiFi channel
#define MAIN_AP_SSID    "CMDCNC_EVKA"
#define SCAN_RETRIES     3

// Heartbeat
#define HEARTBEAT_INTERVAL_MS  10000
#define HEARTBEAT_BYTE         0xFE

// Debounce
#define DEBOUNCE_MS   50
// Ignore buttons for the first 500 ms: GPIO 0 may read LOW while the
// USB-JTAG bridge is still settling after reset.
#define BOOT_GUARD_MS 500

// ============================================================================
// INTERNALS
// ============================================================================

// BTN0=GPIO4 (Red/ZERO), BTN1=GPIO5 (Green/SAVE_POINT),
// BTN2=GPIO0, BTN3=GPIO1, BTN4=GPIO3
static const uint8_t BTN_PINS[BTN_COUNT] = {4, 5, 0, 1, 3};

struct ButtonState {
    bool     last_raw;        // last raw digitalRead() result (true = pressed = LOW)
    bool     confirmed;       // debounce-settled state
    uint32_t last_change_ms;  // millis() of last raw edge
};
static ButtonState g_buttons[BTN_COUNT];

static uint8_t broadcast_addr[] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };

static volatile bool send_done = false;
static volatile bool send_ok   = false;

static void onSendDone(const uint8_t* mac, esp_now_send_status_t status) {
    send_ok   = (status == ESP_NOW_SEND_SUCCESS);
    send_done = true;
}

static void ledOn()  { digitalWrite(PIN_LED, HIGH); }
static void ledOff() { digitalWrite(PIN_LED, LOW);  }

static void initButtons() {
    for (uint8_t i = 0; i < BTN_COUNT; i++) {
        pinMode(BTN_PINS[i], INPUT_PULLUP);
        g_buttons[i] = {false, false, 0};
    }
}

// ============================================================================
// SETUP — runs once at power-on
// ============================================================================

void setup() {
    Serial.begin(115200);
    delay(500);

    initButtons();
    pinMode(PIN_LED, OUTPUT);
    ledOff();

    // Initialise WiFi in STA mode, prevent any auto-scan/reconnect,
    // then pin to the ESP-NOW channel before initialising the stack.
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(false);
    WiFi.disconnect(false, true);   // disconnect + erase stored AP credentials
    delay(100);                     // let WiFi stack settle before channel change

    // Scan for the main ESP32's AP to discover its current WiFi channel.
    // When the main board's STA connects to a home router on channel != 1,
    // its AP silently moves to that channel — hardcoding ch1 would break ESP-NOW.
    uint8_t active_channel = ESPNOW_CHANNEL;  // fallback
    for (int attempt = 0; attempt < SCAN_RETRIES; attempt++) {
        if (attempt > 0) delay(1000);
        Serial.printf("[ButtonRemote] Scanning for '%s'... (attempt %d/%d)\n",
                      MAIN_AP_SSID, attempt + 1, SCAN_RETRIES);
        int n = WiFi.scanNetworks(false, false, false, 200);
        for (int i = 0; i < n; i++) {
            if (WiFi.SSID(i) == MAIN_AP_SSID) {
                active_channel = (uint8_t)WiFi.channel(i);
                Serial.printf("[ButtonRemote] Found on ch%u (RSSI %d dBm)\n",
                              active_channel, WiFi.RSSI(i));
                break;
            }
        }
        WiFi.scanDelete();
        if (active_channel != ESPNOW_CHANNEL) break;  // found
    }
    if (active_channel == ESPNOW_CHANNEL) {
        Serial.printf("[ButtonRemote] AP not found — using fallback ch%u\n", active_channel);
    }

    esp_err_t ch_err = esp_wifi_set_channel(active_channel, WIFI_SECOND_CHAN_NONE);
    Serial.printf("[ButtonRemote] Channel set ch%u -> %s\n",
                  active_channel, ch_err == ESP_OK ? "OK" : "FAIL");

    // Initialise ESP-NOW once — stays active for the lifetime of the device
    if (esp_now_init() != ESP_OK) {
        Serial.println("[ButtonRemote] ESP-NOW init FAILED");
        return;
    }
    esp_now_register_send_cb(onSendDone);

    esp_now_peer_info_t peer = {};
    memcpy(peer.peer_addr, broadcast_addr, 6);
    peer.channel = active_channel;
    peer.encrypt = false;
    esp_now_add_peer(&peer);

    Serial.println("[ButtonRemote] ESP-NOW ready");
    Serial.println("[ButtonRemote] Waiting for button press...");
    Serial.println("  BTN0 GPIO4 -> ZERO");
    Serial.println("  BTN1 GPIO5 -> SAVE_POINT");
    Serial.println("  BTN2 GPIO0 -> (unassigned)");
    Serial.println("  BTN3 GPIO1 -> (unassigned)");
    Serial.println("  BTN4 GPIO3 -> (unassigned)");
}

// ============================================================================
// LOOP — runs continuously
// ============================================================================

void loop() {
    // Heartbeat — keeps the link-status indicator alive on the host GUIs.
    // Sends 0xFE every HEARTBEAT_INTERVAL_MS; main ESP32 rebroadcasts as REMOTE_HB.
    static unsigned long last_hb_ms = 0;
    if (millis() - last_hb_ms >= HEARTBEAT_INTERVAL_MS) {
        last_hb_ms = millis();
        uint8_t hb = HEARTBEAT_BYTE;
        send_done = false; send_ok = false;
        esp_now_send(broadcast_addr, &hb, 1);
        unsigned long t0 = millis();
        while (!send_done && (millis() - t0) < 100) delay(1);
        Serial.printf("[ButtonRemote] Heartbeat -> %s\n", send_ok ? "OK" : "FAIL");
    }

    // Per-button debounce — fires exactly once per confirmed press edge.
    // Boot guard prevents false triggers from GPIO 0 floating LOW at reset.
    if (millis() >= BOOT_GUARD_MS) {
        for (uint8_t i = 0; i < BTN_COUNT; i++) {
            bool raw = (digitalRead(BTN_PINS[i]) == LOW);  // true = pressed

            // Detect raw edge and restart settle timer
            if (raw != g_buttons[i].last_raw) {
                g_buttons[i].last_raw       = raw;
                g_buttons[i].last_change_ms = millis();
            }

            // Commit only when raw has been stable for DEBOUNCE_MS
            if ((millis() - g_buttons[i].last_change_ms) >= DEBOUNCE_MS) {
                if (raw != g_buttons[i].confirmed) {
                    g_buttons[i].confirmed = raw;

                    if (raw) {
                        // Confirmed press edge — send button index via ESP-NOW
                        Serial.printf("[ButtonRemote] Button %d pressed — sending...\n", i);
                        ledOn();

                        uint8_t payload = i;
                        send_done = false;
                        send_ok   = false;
                        esp_now_send(broadcast_addr, &payload, 1);

                        // Wait for send callback (max 100 ms)
                        unsigned long t0 = millis();
                        while (!send_done && (millis() - t0) < 100) {
                            delay(1);
                        }

                        if (send_ok) {
                            Serial.println("[ButtonRemote] Send OK");
                            delay(80);   // brief solid LED = success
                        } else {
                            // Quick blink = fail
                            ledOff(); delay(50); ledOn(); delay(50); ledOff(); delay(50);
                            Serial.println("[ButtonRemote] Send FAILED");
                        }
                        ledOff();
                    }
                }
            }
        }
    }
}
