#include "SphericalSensor.h"

#if ENABLE_WIFI
#include "WebDashboard.h"
WebDashboard dashboard;
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

static void processCommand(const String& cmd) {
    if (cmd == "ZERO") {
        sensor.setZeroPoint();
        Serial.println("ACK:ZERO");
    } else if (cmd == "PING") {
        Serial.println("ACK:PONG");
    } else if (cmd == "STATUS") {
        printStatusLine();
    }
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

    // Non-blocking serial command handler
    handleSerialCommands();

#if ENABLE_WIFI
    {
        String wsCmd = dashboard.takePendingCommand();
        if (wsCmd.length() > 0) {
            processCommand(wsCmd);   // handles sensor + Serial ACK
            // Also send ACK back to WebSocket clients
            if (wsCmd == "ZERO") dashboard.broadcast("ACK:ZERO");
            else if (wsCmd == "PING") dashboard.broadcast("ACK:PONG");
        }
    }
#endif

    // Update position at fixed interval
    if (millis() - last_update >= UPDATE_PERIOD_MS) {
        last_update = millis();

        // Calculate new position from current sensor readings
        sensor.updatePosition();
        sensor.printPosition();

#if ENABLE_WIFI
        // Broadcast DATA line to all WebSocket clients
        {
            SystemStatus st = sensor.getStatus();
            char buf[128];
            snprintf(buf, sizeof(buf),
                     "DATA,%.2f,%.2f,%.2f,%.2f,%.3f,%.3f,%u,%lu,%lu",
                     st.position.x_mm, st.position.y_mm, st.position.z_mm,
                     st.spherical.r_mm, st.spherical.theta_deg, st.spherical.phi_deg,
                     st.is_valid, (unsigned long)st.frame_count,
                     (unsigned long)st.last_update_ms);
            dashboard.broadcast(buf);
        }
#endif
    }
}
