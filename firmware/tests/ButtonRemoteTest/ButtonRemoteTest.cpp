// ============================================================================
// ButtonRemoteTest.cpp — ESP32-C3 Mini WiFi AP + TCP test firmware
// ============================================================================
// Purpose: Stand-alone test harness for the 5-button remote hardware.
//          Creates a WiFi AP ("REMOTE_TEST") and a TCP server so a PC can
//          connect directly — no main ESP32 / ESP-NOW required.
//
// Flash with:  pio run -e button_remote_test --target upload
// Monitor:     pio device monitor -e button_remote_test
//
// PC side: connect to WiFi REMOTE_TEST / remote1234 then run
//          python tools/remote_tester/remote_test_gui.py
// ============================================================================

#include <Arduino.h>
#include <WiFi.h>

// ============================================================================
// CONFIGURATION
// ============================================================================

#define AP_SSID               "REMOTE_TEST"
#define AP_PASSWORD           "remote1234"
#define TCP_PORT              8080
#define MAX_CLIENTS           2
#define AP_START_RETRIES      5
// Lower AP TX power reduces supply spikes on weak Type-C extension boards.
#define TEST_AP_WIFI_TX_POWER WIFI_POWER_8_5dBm

// GPIO 8 = built-in blue LED on ESP32-C3 SuperMini, active HIGH
#define PIN_LED               8

// 5 button inputs — active LOW with internal pull-up.
// Safe GPIOs on ESP32-C3: avoids strapping pins (2, 9), serial (6, 7), LED (8).
#define BTN_COUNT             5

// Timing
#define DEBOUNCE_MS           50
#define HEARTBEAT_INTERVAL_MS 5000
#define LED_BLINK_MS          100
// Ignore buttons for the first 500 ms: GPIO 0 is held LOW by the USB-JTAG
// bridge during flash mode and may still be transitioning at boot.
#define BOOT_GUARD_MS         500

// ============================================================================
// INTERNALS
// ============================================================================

// BTN0=GPIO4 (Green/SAVE_POINT), BTN1=GPIO5 (Red/DEL_POINT), BTN2=GPIO0,
// BTN3=GPIO1, BTN4=GPIO3
static const uint8_t BTN_PINS[BTN_COUNT] = {4, 5, 0, 1, 3};

struct ButtonState {
    uint8_t  pin;
    bool     last_raw;        // last raw digitalRead() result (true = pressed = LOW)
    bool     confirmed;       // debounce-settled state
    uint32_t last_change_ms;  // millis() of last raw edge
};

struct ClientSlot {
    WiFiClient client;
    bool       active;
};

static ButtonState g_buttons[BTN_COUNT];
static ClientSlot  g_clients[MAX_CLIENTS];
static WiFiServer  g_server(TCP_PORT);

static uint32_t g_last_hb_ms = 0;
static uint32_t g_led_off_ms = 0;
static bool     g_led_on     = false;

// ============================================================================
// HELPERS
// ============================================================================

static void ledBlink() {
    digitalWrite(PIN_LED, HIGH);
    g_led_on    = true;
    g_led_off_ms = millis() + LED_BLINK_MS;
}

static void pollLed() {
    if (g_led_on && millis() >= g_led_off_ms) {
        digitalWrite(PIN_LED, LOW);
        g_led_on = false;
    }
}

static void sendToAll(const char* msg) {
    for (uint8_t i = 0; i < MAX_CLIENTS; i++) {
        if (g_clients[i].active && g_clients[i].client.connected()) {
            g_clients[i].client.print(msg);
        }
    }
}

// ============================================================================
// INIT
// ============================================================================

static void initButtons() {
    for (uint8_t i = 0; i < BTN_COUNT; i++) {
        g_buttons[i].pin            = BTN_PINS[i];
        g_buttons[i].last_raw       = false;
        g_buttons[i].confirmed      = false;
        g_buttons[i].last_change_ms = 0;
        pinMode(BTN_PINS[i], INPUT_PULLUP);
    }
}

static void initWiFiAP() {
    // Force a clean radio state before AP start. Some ESP32-C3 boards can keep
    // stale station state across resets, which may cause softAP() to fail.
    WiFi.persistent(false);
    WiFi.mode(WIFI_MODE_NULL);
    delay(100);
    WiFi.softAPdisconnect(true);
    delay(100);
    WiFi.mode(WIFI_AP);
    if (!WiFi.setTxPower(TEST_AP_WIFI_TX_POWER)) {
        Serial.println("[TEST] WARN: setTxPower failed");
    } else {
        Serial.println("[TEST] TX power set to WIFI_POWER_8_5dBm");
    }
    delay(100);

    bool ok = false;
    for (uint8_t attempt = 1; attempt <= AP_START_RETRIES; attempt++) {
        ok = WiFi.softAP(AP_SSID, AP_PASSWORD, 1, false, MAX_CLIENTS);
        if (ok) break;
        Serial.printf("[TEST] AP start attempt %u/%u failed\n", attempt, AP_START_RETRIES);
        delay(300);
        WiFi.softAPdisconnect(true);
        delay(100);
    }

    if (!ok) {
        Serial.println("[TEST] AP start FAILED after retries");
        return;
    }

    delay(300);  // let AP + DHCP settle before accepting clients
    Serial.printf("[TEST] AP %s -> OK  IP: %s  CH:%d\n",
                  AP_SSID,
                  WiFi.softAPIP().toString().c_str(),
                  WiFi.channel());
}

static void initTcpServer() {
    g_server.begin();
    g_server.setNoDelay(true);
    Serial.printf("[TEST] TCP server listening on port %d\n", TCP_PORT);
}

// ============================================================================
// POLL FUNCTIONS (called every loop iteration)
// ============================================================================

static void reapDeadClients() {
    for (uint8_t i = 0; i < MAX_CLIENTS; i++) {
        if (g_clients[i].active && !g_clients[i].client.connected()) {
            Serial.printf("[TEST] Client slot %d disconnected\n", i);
            g_clients[i].client.stop();
            g_clients[i].active = false;
        }
    }
}

static void pollClients() {
    WiFiClient incoming = g_server.available();
    if (!incoming) return;

    // Find a free slot
    for (uint8_t i = 0; i < MAX_CLIENTS; i++) {
        if (!g_clients[i].active) {
            g_clients[i].client = incoming;
            g_clients[i].client.setNoDelay(true);
            g_clients[i].active = true;
            g_clients[i].client.print("HELLO:REMOTE_TEST\n");
            Serial.printf("[TEST] Client slot %d connected from %s\n",
                          i, incoming.remoteIP().toString().c_str());
            return;
        }
    }

    // No free slot — reject
    incoming.print("ERR:MAX_CLIENTS\n");
    incoming.stop();
    Serial.println("[TEST] Rejected client: MAX_CLIENTS reached");
}

static void drainClientRx() {
    // Discard all inbound bytes to prevent WiFiClient rx buffer overflow.
    for (uint8_t i = 0; i < MAX_CLIENTS; i++) {
        if (g_clients[i].active) {
            while (g_clients[i].client.available()) {
                g_clients[i].client.read();
            }
        }
    }
}

static void pollButtons() {
    // Boot guard: GPIO 0 may read LOW until USB-JTAG bridge settles.
    if (millis() < BOOT_GUARD_MS) return;

    for (uint8_t i = 0; i < BTN_COUNT; i++) {
        bool raw = (digitalRead(g_buttons[i].pin) == LOW);  // true = pressed

        // Track raw edge for debounce timer
        if (raw != g_buttons[i].last_raw) {
            g_buttons[i].last_raw       = raw;
            g_buttons[i].last_change_ms = millis();
        }

        // Settle check: raw has been stable for at least DEBOUNCE_MS
        if ((millis() - g_buttons[i].last_change_ms) >= DEBOUNCE_MS) {
            if (raw != g_buttons[i].confirmed) {
                g_buttons[i].confirmed = raw;
                if (raw) {
                    // Falling edge = confirmed press
                    char msg[12];
                    snprintf(msg, sizeof(msg), "BTN:%d\n", i);
                    sendToAll(msg);
                    ledBlink();
                    Serial.printf("[TEST] BTN%d pressed (GPIO%d)\n", i, g_buttons[i].pin);
                }
            }
        }
    }
}

static void pollHeartbeat() {
    if (millis() - g_last_hb_ms >= HEARTBEAT_INTERVAL_MS) {
        g_last_hb_ms = millis();
        sendToAll("HB\n");
        Serial.println("[TEST] HB");
    }
}

// ============================================================================
// SETUP / LOOP
// ============================================================================

void setup() {
    Serial.begin(115200);
    // Wait up to 3 s for the USB-Serial/JTAG host connection so startup
    // messages are not lost before the monitor opens.
    delay(3000);

    pinMode(PIN_LED, OUTPUT);
    digitalWrite(PIN_LED, LOW);

    initButtons();
    initWiFiAP();
    initTcpServer();

    Serial.println("[TEST] Ready — waiting for TCP clients...");
    Serial.println("[TEST] Buttons:");
    Serial.println("  BTN0 GPIO4  BTN1 GPIO5  BTN2 GPIO0  BTN3 GPIO1  BTN4 GPIO3");
}

void loop() {
    reapDeadClients();
    pollClients();
    drainClientRx();
    pollButtons();
    pollHeartbeat();
    pollLed();
}
