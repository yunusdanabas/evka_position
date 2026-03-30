#include "SphericalSensor.h"
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

// ============================================================================
// ESP32 PLATFORMIO ENTRY POINT
// ============================================================================

SphericalPositioningSensor sensor;

// Update Frequency
#define UPDATE_PERIOD_MS  50  // 20 Hz position update rate

static String serial_buffer;

static void printStatusLine() {
    SystemStatus st = sensor.getStatus();
    char buf[128];
    snprintf(buf, sizeof(buf),
        "STATUS,%u,%lu,%lu,%.2f,%.3f,%.3f,%.2f,%.2f,%.2f",
        st.is_valid, (unsigned long)st.frame_count, (unsigned long)st.last_update_ms,
        st.spherical.r_mm, st.spherical.theta_deg, st.spherical.phi_deg,
        st.position.x_mm, st.position.y_mm, st.position.z_mm);
    Serial.println(buf);

#if ENABLE_BATTERY_MONITOR
    BatteryStatus bat = sensor.readBattery();
    Serial.print("BATT,");
    Serial.print(bat.voltage, 3);
    Serial.print(",");
    Serial.print(bat.percentage);
    Serial.print(",");
    Serial.println(bat.is_low ? 1 : 0);
#endif
}

// Returns the reply line (also printed to Serial). Empty string = no reply needed.
static String processCommand(const String& cmd) {
    if (cmd == "ZERO") {
        sensor.setZeroPoint();
        Serial.println("ACK:ZERO");
        return "ACK:ZERO";

    } else if (cmd == "PING") {
        Serial.println("ACK:PONG");
        return "ACK:PONG";

    } else if (cmd == "STATUS") {
        printStatusLine();
        return "";

    } else if (cmd == "ZERO_T") {
        sensor.zeroTheta();
        Serial.println("ACK:ZERO_T");
        return "ACK:ZERO_T";

    } else if (cmd == "ZERO_P") {
        sensor.zeroPhi();
        Serial.println("ACK:ZERO_P");
        return "ACK:ZERO_P";

    } else if (cmd == "ZERO_W") {
        sensor.zeroWire();
        Serial.println("ACK:ZERO_W");
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
        const float cur_mm_pp = DRUM_CIRCUM_MM / PPR_WIRE;  // use compile-time as base
        float measured_mm = (float)wc * cur_mm_pp;
        float factor = actual_mm / measured_mm;
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

    } else if (cmd == "GET_IP") {
        String reply;
        if (WiFi.status() == WL_CONNECTED) {
            reply = "STA_IP:" + WiFi.localIP().toString();
        } else {
            reply = "STA_IP:NOT_CONNECTED";
        }
        Serial.println(reply);
        return reply;

    } else if (cmd.startsWith("WIFI_SET:")) {
        String payload = cmd.substring(9);
        int commaIdx = payload.indexOf(',');
        if (commaIdx != -1) {
            String ssid = payload.substring(0, commaIdx);
            String pass = payload.substring(commaIdx + 1);
            Preferences prefs;
            prefs.begin("wifi_cfg", false);
            prefs.putString("ssid", ssid);
            prefs.putString("pass", pass);
            prefs.end();
            Serial.println("ACK:WIFI_SAVED");
            delay(500);
            ESP.restart();
        }
        return "ACK:WIFI_SAVED";

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

    return "";
}

static void handleSerialCommands() {
    while (Serial.available() > 0) {
        const char ch = (char)Serial.read();
        if (ch == '\n' || ch == '\r') {
            serial_buffer.trim();
            if (serial_buffer.length() > 0) {
                processCommand(serial_buffer);
            }
            serial_buffer = "";
        } else {
            serial_buffer += ch;
        }
    }
}

void setup() {
    Serial.begin(115200);
    // Wait for serial to settle
    delay(500);
    
    Serial.println("\n========================================");
    Serial.println("  Spherical 3D Positioning System");
    Serial.println("  Firmware v1.0");
    Serial.println("========================================\n");
    
    // Initialize sensor hardware
    sensor.begin();

#if ENABLE_WIFI
    dashboard.begin();
#if ENABLE_CMD_TCP
    cmdTcp.begin();
#endif
    // WiFi status LED
    pinMode(PIN_WIFI_LED, OUTPUT);
    digitalWrite(PIN_WIFI_LED, LOW);
#endif

    // CRITICAL: Set zero point when robot is at home position
    Serial.println("Waiting 2s before calibration...");
    delay(2000);
    Serial.println("Setting zero point... (Ensure robot is at MECHANICAL HOME!)");
    sensor.setZeroPoint();
    Serial.println("Calibration Complete.");
}

void loop() {
    static unsigned long last_update = 0;
    static unsigned long last_led_toggle = 0;
    static bool led_state = false;
    static bool sta_configured = false;

    // Non-blocking serial command handler
    handleSerialCommands();

#if ENABLE_WIFI
    // WebSocket command handler
    {
        String wsCmd = dashboard.takePendingCommand();
        if (wsCmd.length() > 0) {
            String reply = processCommand(wsCmd);
            if (reply.length() > 0) dashboard.broadcast(reply.c_str());
        }
    }

#if ENABLE_CMD_TCP
    // TCP server: accept connections, read commands
    cmdTcp.poll();
    {
        String tcpCmd = cmdTcp.takePendingCommand();
        if (tcpCmd.length() > 0) {
            String reply = processCommand(tcpCmd);
            if (reply.length() > 0) cmdTcp.sendToAllClients(reply.c_str());
        }
    }
#endif

    // WiFi status LED: blink=searching, solid=connected, off=no STA
    {
        // Check if STA credentials are configured (only once)
        static bool sta_checked = false;
        if (!sta_checked) {
            Preferences prefs;
            prefs.begin("wifi_cfg", true);
            sta_configured = prefs.getString("ssid", "").length() > 0;
            prefs.end();
            sta_checked = true;
        }

        if (!sta_configured) {
            digitalWrite(PIN_WIFI_LED, LOW);  // OFF — no STA config
        } else if (WiFi.status() == WL_CONNECTED) {
            digitalWrite(PIN_WIFI_LED, HIGH); // Solid ON — connected
        } else {
            // Blink 500ms — searching
            if (millis() - last_led_toggle >= 500) {
                last_led_toggle = millis();
                led_state = !led_state;
                digitalWrite(PIN_WIFI_LED, led_state ? HIGH : LOW);
            }
        }
    }
#endif // ENABLE_WIFI

    // Update position at fixed interval
    if (millis() - last_update >= UPDATE_PERIOD_MS) {
        last_update = millis();

        // Calculate new position from current sensor readings
        sensor.updatePosition();
        sensor.printPosition();

#if ENABLE_WIFI
        {
            SystemStatus st = sensor.getStatus();

            // Broadcast DATA line to WebSocket clients
            char buf[128];
            snprintf(buf, sizeof(buf),
                     "DATA,%.2f,%.2f,%.2f,%.2f,%.3f,%.3f,%u,%lu,%lu",
                     st.position.x_mm, st.position.y_mm, st.position.z_mm,
                     st.spherical.r_mm, st.spherical.theta_deg, st.spherical.phi_deg,
                     st.is_valid, (unsigned long)st.frame_count,
                     (unsigned long)st.last_update_ms);
            dashboard.broadcast(buf);

#if ENABLE_CMD_TCP
            // Broadcast CMD format to TCP clients
            cmdTcp.broadcastPosition(
                st.position.x_mm, st.position.y_mm, st.position.z_mm);
            cmdTcp.broadcastSensorData(
                st.spherical.r_mm, st.spherical.theta_deg,
                st.spherical.phi_deg, st.is_valid, st.frame_count);
#endif
        }
#endif
    }
}
