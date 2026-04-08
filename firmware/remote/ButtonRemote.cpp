// ============================================================================
// EvkaPosition — Wireless Button Remote (ESP-NOW Sender)
// ============================================================================
// Target: ESP32-C3 (Seeed XIAO ESP32-C3 or ESP32-C3 SuperMini)
// Sends button press as ESP-NOW packet to the main positioning ESP32.
// Deep sleeps between presses for months of battery life.
//
// Button wiring: Each button connects GPIO → GND (internal pull-up enabled).
// Power: 3.7V LiPo via built-in charger (XIAO) or TP4056 (SuperMini).
// ============================================================================

#include <Arduino.h>
#include <esp_now.h>
#include <esp_sleep.h>
#include <esp_wifi.h>
#include <WiFi.h>

// ============================================================================
// CONFIGURATION
// ============================================================================

// Button GPIO pins (active LOW with internal pull-up)
// XIAO ESP32-C3: D0=GPIO2, D1=GPIO3, D2=GPIO4, D3=GPIO5, D4=GPIO6
#define BTN_SAVE_POINT    2   // D0 — Green  — Save current position
#define BTN_ZERO          3   // D1 — Red    — Re-zero all encoders
#define BTN_RECORD        4   // D2 — Blue   — Toggle recording
#define BTN_ZERO_THETA    5   // D3 — Yellow — Zero theta encoder
#define BTN_ZERO_WIRE     6   // D4 — White  — Zero wire encoder

// LED feedback pin (-1 to disable)
#define PIN_LED           -1

// WiFi channel — MUST match the main ESP32 AP channel
#define ESPNOW_CHANNEL    1

// Debug mode: set to 1 to keep device awake with serial output (for testing)
#define DEBUG_MODE        0

// ============================================================================
// INTERNALS
// ============================================================================

static const uint8_t BTN_PINS[] = {
    BTN_SAVE_POINT, BTN_ZERO, BTN_RECORD, BTN_ZERO_THETA, BTN_ZERO_WIRE
};
static const uint8_t BTN_COUNT = sizeof(BTN_PINS) / sizeof(BTN_PINS[0]);

// Broadcast address — no MAC pairing needed
static uint8_t broadcast_addr[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

static volatile bool send_done = false;
static volatile bool send_ok   = false;

static void onSendDone(const uint8_t* mac, esp_now_send_status_t status) {
    send_ok   = (status == ESP_NOW_SEND_SUCCESS);
    send_done = true;
}

static void ledOn()  { if (PIN_LED >= 0) digitalWrite(PIN_LED, HIGH); }
static void ledOff() { if (PIN_LED >= 0) digitalWrite(PIN_LED, LOW);  }

// Read which button is currently pressed (first LOW wins). Returns -1 if none.
static int8_t readPressedButton() {
    for (uint8_t i = 0; i < BTN_COUNT; i++) {
        if (digitalRead(BTN_PINS[i]) == LOW) return (int8_t)i;
    }
    return -1;
}

// Send button ID via ESP-NOW. Returns true on success.
static bool sendButtonPress(uint8_t button_id) {
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    esp_wifi_set_channel(ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);

    if (esp_now_init() != ESP_OK) return false;

    esp_now_register_send_cb(onSendDone);

    esp_now_peer_info_t peer = {};
    memcpy(peer.peer_addr, broadcast_addr, 6);
    peer.channel = ESPNOW_CHANNEL;
    peer.encrypt = false;
    esp_now_add_peer(&peer);

    // Payload: single byte = button index (0-4)
    uint8_t payload = button_id;
    send_done = false;
    send_ok   = false;
    esp_now_send(broadcast_addr, &payload, 1);

    // Wait for send callback (max 100 ms)
    unsigned long t0 = millis();
    while (!send_done && (millis() - t0) < 100) {
        delay(1);
    }

    esp_now_deinit();
    return send_ok;
}

// Enter deep sleep with all buttons as wake sources
static void enterDeepSleep() {
    uint64_t wake_mask = 0;
    for (uint8_t i = 0; i < BTN_COUNT; i++) {
        wake_mask |= (1ULL << BTN_PINS[i]);
    }
    esp_deep_sleep_enable_gpio_wakeup(wake_mask, ESP_GPIO_WAKEUP_GPIO_LOW);
    esp_deep_sleep_start();
    // Never returns
}

// ============================================================================
// SETUP — runs once per wake cycle
// ============================================================================

void setup() {
    // Configure all button pins
    for (uint8_t i = 0; i < BTN_COUNT; i++) {
        pinMode(BTN_PINS[i], INPUT_PULLUP);
    }
    if (PIN_LED >= 0) pinMode(PIN_LED, OUTPUT);

#if DEBUG_MODE
    Serial.begin(115200);
    delay(500);
    Serial.println("\n[ButtonRemote] DEBUG MODE — awake, press buttons to test");
    Serial.println("Buttons: 0=SAVE_POINT, 1=ZERO, 2=RECORD, 3=ZERO_T, 4=ZERO_W");
    return;  // Skip sleep — stay in loop()
#endif

    // Debounce delay after wake
    delay(20);

    int8_t pressed = readPressedButton();

    if (pressed >= 0) {
        ledOn();
        bool ok = sendButtonPress((uint8_t)pressed);
        // Brief LED flash: solid = success, quick blink = fail
        if (!ok && PIN_LED >= 0) {
            ledOff(); delay(50); ledOn(); delay(50); ledOff();
        }
        delay(30);
        ledOff();
    }

    // Wait for button release to avoid repeated triggers
    while (readPressedButton() >= 0) {
        delay(10);
    }
    delay(50);  // Extra debounce after release

    enterDeepSleep();
}

// ============================================================================
// LOOP — only used in DEBUG_MODE
// ============================================================================

void loop() {
#if DEBUG_MODE
    static int8_t last_btn = -1;
    int8_t btn = readPressedButton();

    if (btn >= 0 && btn != last_btn) {
        Serial.printf("[ButtonRemote] Button %d pressed — sending...\n", btn);
        ledOn();
        bool ok = sendButtonPress((uint8_t)btn);
        Serial.printf("[ButtonRemote] Send %s\n", ok ? "OK" : "FAILED");
        ledOff();
    }
    last_btn = btn;
    delay(50);
#endif
}
