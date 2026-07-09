#include "SphericalSensor.h"
#include "StatusLed.h"
#include <Preferences.h>

#if ENABLE_WIFI
#include <WiFi.h>
#include "WebDashboard.h"
WebDashboard dashboard;
#endif

#if ENABLE_WIFI && ENABLE_CMD_TCP
#include "CmdTcpServer.h"
CmdTcpServer cmdTcp;
#endif

#if ENABLE_WIFI && ENABLE_ESPNOW_REMOTE
#include <esp_now.h>
#include <esp_wifi.h>

// ---- ESP-NOW wireless button remote receiver ----
static volatile int8_t espnow_pending_button    = -1;
static volatile bool   espnow_pending_heartbeat = false;

static const char* const REMOTE_BUTTON_CMD[] = {
    "SAVE_POINT",  // Button 0 — Green — GPIO 4
    "DEL_POINT",   // Button 1 — Red   — GPIO 5
    nullptr,       // Button 2 — GPIO 0 — unassigned
    nullptr,       // Button 3 — GPIO 1 — unassigned
    nullptr,       // Button 4 — GPIO 3 — unassigned
};
static constexpr uint8_t REMOTE_BUTTON_COUNT = 5;

#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 0, 0)
static void onEspNowRecv(const esp_now_recv_info_t* info, const uint8_t* data, int len) {
#else
static void onEspNowRecv(const uint8_t* mac, const uint8_t* data, int len) {
#endif
    if (len >= 1) {
        if (data[0] == 0xFE) {
            espnow_pending_heartbeat = true;
        } else if (data[0] < REMOTE_BUTTON_COUNT) {
            espnow_pending_button = (int8_t)data[0];
        }
    }
}

static bool initEspNow() {
    // Print the channel the AP is actually on so we can verify it matches
    // the remote's ESPNOW_CHANNEL define.
    uint8_t primary; wifi_second_chan_t second;
    esp_wifi_get_channel(&primary, &second);
    Serial.printf("[ESP-NOW] AP channel: %u (remote must match)\n", primary);

    if (esp_now_init() != ESP_OK) {
        Serial.println("[ESP-NOW] Init FAILED");
        return false;
    }
    esp_now_register_recv_cb(onEspNowRecv);
    Serial.println("[ESP-NOW] Remote receiver ready");
    return true;
}
#endif // ENABLE_WIFI && ENABLE_ESPNOW_REMOTE

// ============================================================================
// ESP32 PLATFORMIO ENTRY POINT
// ============================================================================

SphericalPositioningSensor sensor;
StatusLed statusLed;

static bool g_boot_calibrating = false;
#if ENABLE_WIFI && ENABLE_ESPNOW_REMOTE
static bool g_espnow_fault = false;
#endif

// Update Frequency
#define UPDATE_PERIOD_MS  50  // 20 Hz position update rate

static String serial_buffer;

static StatusLedInputs buildStatusLedInputs() {
    StatusLedInputs in = {};
#if ENABLE_WIFI
    in.wifi_enabled = true;
    in.sta_configured = dashboard.isStaConfigured();
    in.sta_connected = dashboard.isStaConnected();
#else
    in.wifi_enabled = false;
#endif
    in.boot_calibrating = g_boot_calibrating;
#if ENABLE_WIFI && ENABLE_ESPNOW_REMOTE
    in.espnow_fault = g_espnow_fault;
#endif
    in.position_valid = (sensor.getStatus().is_valid != 0);
    return in;
}

static void tickStatusLed() {
    statusLed.update(buildStatusLedInputs());
}

static void waitWithStatusLed(uint32_t ms) {
    const uint32_t start = millis();
    while ((int32_t)(millis() - start) < (int32_t)ms) {
        tickStatusLed();
        delay(10);
    }
}

static String buildStatusLine() {
    SystemStatus st = sensor.getStatus();
    char buf[128];
    snprintf(buf, sizeof(buf),
        "STATUS,%u,%lu,%lu,%.2f,%.3f,%.3f,%.2f,%.2f,%.2f",
        st.is_valid, (unsigned long)st.frame_count, (unsigned long)st.last_update_ms,
        st.spherical.r_mm, st.spherical.theta_deg, st.spherical.phi_deg,
        st.position.x_mm, st.position.y_mm, st.position.z_mm);
    return String(buf);
}

#if ENABLE_BATTERY_MONITOR
static String buildBatteryLine() {
    BatteryStatus bat = sensor.readBattery();
    char buf[40];
    snprintf(buf, sizeof(buf), "BATT,%.3f,%u,%u",
             bat.voltage, bat.percentage, bat.is_low ? 1 : 0);
    return String(buf);
}
#endif

static String printStatusLine() {
    String statusLine = buildStatusLine();
    Serial.println(statusLine);

#if ENABLE_BATTERY_MONITOR
    Serial.println(buildBatteryLine());
#endif
    return statusLine;
}

static void sendBatteryLineToWireless() {
#if ENABLE_WIFI && ENABLE_BATTERY_MONITOR
    String batt = buildBatteryLine();
    dashboard.broadcast(batt.c_str());
#if ENABLE_CMD_TCP
    cmdTcp.sendToAllClients(batt.c_str());
#endif
#endif
}

// Returns the reply line (also printed to Serial). Empty string = no reply needed.
static String processCommand(String cmd) {
    cmd.trim();
    static uint32_t pt_idx = 0;  // shared across SAVE_POINT and DEL_POINT
    if (cmd == "ZERO") {
        sensor.setZeroPoint();
        Serial.println("ACK:ZERO");
        statusLed.flashZeroAck();
        return "ACK:ZERO";

    } else if (cmd == "PING") {
        Serial.println("ACK:PONG");
        return "ACK:PONG";

    } else if (cmd == "BLINK") {
        // Connection test: flash the status LED bright white for ~700 ms so the
        // operator can visually confirm the ESP32 received a command (works over
        // serial, TCP, and WebSocket). No-op on boards without the RGB LED.
        statusLed.flashOverlay(255, 255, 255, 700);
        Serial.println("ACK:BLINK");
        return "ACK:BLINK";

    } else if (cmd == "STATUS") {
        return printStatusLine();

    } else if (cmd == "ZERO_T") {
        sensor.zeroTheta();
        Serial.println("ACK:ZERO_T");
        statusLed.flashZeroAck();
        return "ACK:ZERO_T";

    } else if (cmd == "ZERO_P") {
        sensor.zeroPhi();
        Serial.println("ACK:ZERO_P");
        statusLed.flashZeroAck();
        return "ACK:ZERO_P";

    } else if (cmd == "ZERO_W") {
        sensor.zeroWire();
        Serial.println("ACK:ZERO_W");
        statusLed.flashZeroAck();
        return "ACK:ZERO_W";

    } else if (cmd == "CONSTANTS") {
        char buf[96];
        sensor.getConstants(buf, sizeof(buf));
        Serial.println(buf);
        return String(buf);

    } else if (cmd.startsWith("CAL_W ")) {
        float actual_mm = cmd.substring(6).toFloat();
        if (actual_mm <= 0) return "ERR:CAL_W bad value";
        int32_t tc, pc, wc;
        sensor.readRawEncoders(tc, pc, wc);
        if (wc == 0) return "ERR:CAL_W zero counts";
        const float cur_mm_pp = DRUM_CIRCUM_MM / sensor.getPPRWire();  // use runtime-calibrated value
        float measured_mm = (float)wc * cur_mm_pp;
        float factor = actual_mm / measured_mm;
        if (factor < 0.1f || factor > 10.0f) return "ERR:CAL_W factor out of range";
        float new_mm_pp = cur_mm_pp * factor;
        float new_ppr_w = DRUM_CIRCUM_MM / new_mm_pp;
        char buf[96];
        snprintf(buf, sizeof(buf), "CAL:WIRE,%.4f,%.6f,%.2f", factor, new_mm_pp, new_ppr_w);
        Serial.println(buf);
        return String(buf);

    } else if (cmd.startsWith("CAL_T ")) {
        int n_turns = cmd.substring(6).toInt();
        if (n_turns <= 0) return "ERR:CAL_T bad turns";
        int32_t tc, pc, wc;
        sensor.readRawEncoders(tc, pc, wc);
        if (abs(tc) < 100) return "ERR:CAL_T too few counts";
        float ppr = (float)abs(tc) / (float)n_turns;
        char buf[64];
        snprintf(buf, sizeof(buf), "CAL:THETA,%ld,%.2f", (long)tc, ppr);
        Serial.println(buf);
        return String(buf);

    } else if (cmd.startsWith("CAL_P ")) {
        int n_turns = cmd.substring(6).toInt();
        if (n_turns <= 0) return "ERR:CAL_P bad turns";
        int32_t tc, pc, wc;
        sensor.readRawEncoders(tc, pc, wc);
        if (abs(pc) < 100) return "ERR:CAL_P too few counts";
        float ppr = (float)abs(pc) / (float)n_turns;
        char buf[64];
        snprintf(buf, sizeof(buf), "CAL:PHI,%ld,%.2f", (long)pc, ppr);
        Serial.println(buf);
        return String(buf);

    } else if (cmd.startsWith("SET_PPR_ROTARY ")) {
        float v = cmd.substring(15).toFloat();
        if (v <= 0) return "ERR:SET_PPR_ROTARY bad value";
        sensor.setPPRRotary(v);
        char buf[48];
        snprintf(buf, sizeof(buf), "ACK:PPR_ROTARY,%.2f", v);
        Serial.println(buf);
        return String(buf);

    } else if (cmd.startsWith("SET_PPR_WIRE ")) {
        float v = cmd.substring(13).toFloat();
        if (v <= 0) return "ERR:SET_PPR_WIRE bad value";
        sensor.setPPRWire(v);
        char buf[48];
        snprintf(buf, sizeof(buf), "ACK:PPR_WIRE,%.2f", v);
        Serial.println(buf);
        return String(buf);

    } else if (cmd == "SAVE_PPR") {
        sensor.savePPRToNVS();
        Serial.println("ACK:SAVE_PPR");
        return "ACK:SAVE_PPR";

    } else if (cmd == "SAVE_POINT") {
        SystemStatus st = sensor.getStatus();
        char buf[128];
        snprintf(buf, sizeof(buf),
            "POINT,%u,%.2f,%.2f,%.2f,%.2f,%.3f,%.3f",
            pt_idx++,
            st.position.x_mm, st.position.y_mm, st.position.z_mm,
            st.spherical.r_mm, st.spherical.theta_deg, st.spherical.phi_deg);
        Serial.println(buf);
        return String(buf);

    } else if (cmd == "DEL_POINT") {
        if (pt_idx == 0) {
            Serial.println("ERR:NO_POINTS");
            return "ERR:NO_POINTS";
        }
        pt_idx--;
        char buf[32];
        snprintf(buf, sizeof(buf), "DEL_POINT,%u", pt_idx);
        Serial.println(buf);
        return String(buf);

    } else if (cmd == "GET_IP") {
#if ENABLE_WIFI
        String reply;
        if (WiFi.status() == WL_CONNECTED) {
            reply = "STA_IP:" + WiFi.localIP().toString();
        } else {
            reply = "STA_IP:NOT_CONNECTED";
        }
        Serial.println(reply);
        return reply;
#else
        return "ERR:WIFI_DISABLED";
#endif

    } else if (cmd.startsWith("WIFI_SET:") || cmd.startsWith("WIFI_AYAR:")) {
#if !ENABLE_REMOTE_WIFI_CONFIG
        return "ERR:WIFI_CFG_DISABLED";
#else
        int colonIdx = cmd.indexOf(':');
        String payload = cmd.substring(colonIdx + 1);
        int commaIdx = payload.indexOf(',');
        if (commaIdx == -1) {
            return "ERR:WIFI_INVALID";
        }

        String ssid = payload.substring(0, commaIdx);
        String pass = payload.substring(commaIdx + 1);
        // Allow explicit clear request: WIFI_SET:, (empty SSID + empty password)
        bool clear_request = (ssid.length() == 0 && pass.length() == 0);
        if (!clear_request && (ssid.length() == 0 || ssid.length() > 32)) return "ERR:SSID_INVALID";
        if (pass.length() > 0 && pass.length() < 8) return "ERR:PASS_TOO_SHORT";
        Preferences prefs;
        prefs.begin("wifi_cfg", false);
        prefs.putString("ssid", ssid);
        prefs.putString("pass", pass);
        prefs.end();
        Serial.println("ACK:WIFI_SAVED");
#if ENABLE_WIFI
        dashboard.broadcast("ACK:WIFI_SAVED");
#if ENABLE_CMD_TCP
        cmdTcp.sendToAllClients("ACK:WIFI_SAVED");
#endif
#endif
        delay(500);  // allow async sends to flush before restart
        ESP.restart();
        return "ACK:WIFI_SAVED";  // unreachable
#endif

    } else if (cmd == "SYSINFO") {
#if ENABLE_WIFI
        int32_t rssi = (WiFi.status() == WL_CONNECTED) ? WiFi.RSSI() : 0;
#if ENABLE_CMD_TCP
        uint8_t tcpCount = cmdTcp.clientCount();
#else
        uint8_t tcpCount = 0;
#endif
        char buf[64];
        snprintf(buf, sizeof(buf), "SYSINFO,%ld,%lu,%lu,%u",
                 (long)rssi, (unsigned long)ESP.getFreeHeap(),
                 (unsigned long)(millis() / 1000), tcpCount);
        Serial.println(buf);
        return String(buf);
#else
        return "";
#endif
    }

    Serial.println("ERR:UNKNOWN_CMD");
    return "ERR:UNKNOWN_CMD";
}

static void handleSerialCommands() {
    static bool serial_overflow = false;
    while (Serial.available() > 0) {
        const char ch = (char)Serial.read();
        if (ch == '\n' || ch == '\r') {
            if (!serial_overflow) {
                serial_buffer.trim();
                if (serial_buffer.length() > 0) {
                    processCommand(serial_buffer);
                }
            }
            serial_buffer = "";
            serial_overflow = false;
        } else {
            serial_buffer += ch;
            if (serial_buffer.length() > 128) {
                Serial.println("ERR:CMD_TOO_LONG");
                serial_buffer = "";
                serial_overflow = true;
            }
        }
    }
}

void setup() {
    Serial.begin(115200);
    // Wait for serial to settle
    delay(500);
    
    Serial.println("\n========================================");
    Serial.println("  Spherical 3D Positioning System");
    Serial.println("  Firmware v1.1  (BLINK connection test)");
#if defined(PCB_V4)
    Serial.println("  Board: EVKA v4 / ESP32-S3");
#else
    Serial.println("  Board: classic ESP32");
#endif
    Serial.println("========================================\n");
    
    // Initialize sensor hardware
    sensor.begin();
    statusLed.begin();

#if ENABLE_WIFI
    dashboard.begin();
    delay(200);  // let AP come fully up before ESP-NOW init
#if ENABLE_CMD_TCP
    cmdTcp.begin();
#endif
#if ENABLE_ESPNOW_REMOTE
    g_espnow_fault = !initEspNow();
#endif
#endif

    // CRITICAL: Set zero point when robot is at home position
    g_boot_calibrating = true;
    Serial.println("Waiting 2s before calibration...");
    waitWithStatusLed(2000);
    Serial.println("Setting zero point... (Ensure robot is at MECHANICAL HOME!)");
    sensor.setZeroPoint();
    g_boot_calibrating = false;
    tickStatusLed();
    Serial.println("Calibration Complete.");
}

void loop() {
    static unsigned long last_update = 0;

    // Non-blocking serial command handler
    handleSerialCommands();

#if ENABLE_WIFI
    // ESP-NOW remote button handler
#if ENABLE_ESPNOW_REMOTE
    if (espnow_pending_button >= 0) {
        int8_t btn = espnow_pending_button;
        espnow_pending_button = -1;
        if (btn < REMOTE_BUTTON_COUNT) {
            // Broadcast button event for web UI, TCP, and serial indicator
            char btn_msg[24];
            snprintf(btn_msg, sizeof(btn_msg), "REMOTE_BTN:%d", btn);
            Serial.println(btn_msg);
            dashboard.broadcast(btn_msg);
#if ENABLE_CMD_TCP
            cmdTcp.sendToAllClients(btn_msg);
#endif

            const char* cmd = REMOTE_BUTTON_CMD[btn];
            if (cmd == nullptr) return;  // unassigned button — ignore silently
            Serial.printf("[ESP-NOW] Button %d -> %s\n", btn, cmd);
            statusLed.flashRemoteButton();
            String reply = processCommand(String(cmd));
            if (reply.length() > 0) {
                dashboard.broadcast(reply.c_str());
#if ENABLE_CMD_TCP
                cmdTcp.sendToAllClients(reply.c_str());
#endif
            }
        }
    }
    // Heartbeat — rebroadcast to WebSocket, TCP, and serial so GUIs can track link status
    if (espnow_pending_heartbeat) {
        espnow_pending_heartbeat = false;
        Serial.println("REMOTE_HB");
        dashboard.broadcast("REMOTE_HB");
#if ENABLE_CMD_TCP
        cmdTcp.sendToAllClients("REMOTE_HB");
#endif
    }
#endif
    // Non-blocking WiFi maintenance:
    // keep AP available and schedule controlled STA retries after disconnects.
    dashboard.tick();

    // WebSocket command handler
    {
        String wsCmd = dashboard.takePendingCommand();
        if (wsCmd.length() > 0) {
            String reply = processCommand(wsCmd);
            if (reply.length() > 0) {
                dashboard.broadcast(reply.c_str());
                if (wsCmd == "STATUS") sendBatteryLineToWireless();
#if ENABLE_CMD_TCP
                // POINT/DEL_POINT must reach TCP clients too (keeps all UIs in sync)
                if (reply.startsWith("POINT,") || reply.startsWith("DEL_POINT,"))
                    cmdTcp.sendToAllClients(reply.c_str());
#endif
            }
        }
    }

#if ENABLE_CMD_TCP
    // TCP server: accept connections, read commands
    cmdTcp.poll();
    {
        String tcpCmd = cmdTcp.takePendingCommand();
        if (tcpCmd.length() > 0) {
            String reply = processCommand(tcpCmd);
            if (reply.length() > 0) {
                cmdTcp.sendToAllClients(reply.c_str());
                if (tcpCmd == "STATUS") sendBatteryLineToWireless();
                // POINT/DEL_POINT must reach WebSocket dashboard too
                if (reply.startsWith("POINT,") || reply.startsWith("DEL_POINT,"))
                    dashboard.broadcast(reply.c_str());
            }
        }
    }
#endif

#endif // ENABLE_WIFI

    tickStatusLed();

    // Update position at fixed interval
    if (millis() - last_update >= UPDATE_PERIOD_MS) {
        last_update = millis();

        // Calculate new position from current sensor readings
        sensor.updatePosition();
        sensor.printPosition();  // human-readable debug line to serial

        // Format DATA once; send to serial + WiFi (avoids duplicate snprintf)
        {
            SystemStatus st = sensor.getStatus();
            char buf[128];
            snprintf(buf, sizeof(buf),
                     "DATA,%.2f,%.2f,%.2f,%.2f,%.3f,%.3f,%u,%lu,%lu",
                     st.position.x_mm, st.position.y_mm, st.position.z_mm,
                     st.spherical.r_mm, st.spherical.theta_deg, st.spherical.phi_deg,
                     st.is_valid, (unsigned long)st.frame_count,
                     (unsigned long)st.last_update_ms);
            Serial.println(buf);

#if ENABLE_WIFI
            dashboard.broadcast(buf);
#endif

#if ENABLE_WIFI && ENABLE_CMD_TCP
            cmdTcp.broadcastPosition(
                st.position.x_mm, st.position.y_mm, st.position.z_mm);
            cmdTcp.broadcastSensorData(
                st.spherical.r_mm, st.spherical.theta_deg,
                st.spherical.phi_deg, st.is_valid, st.frame_count);
#endif
        }
    }
}
