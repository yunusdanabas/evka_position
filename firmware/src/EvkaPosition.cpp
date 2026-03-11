#include "SphericalSensor.h"

// ============================================================================
// ESP32 PLATFORMIO ENTRY POINT
// ============================================================================

SphericalPositioningSensor sensor;

// Update Frequency
#define UPDATE_PERIOD_MS  50  // 20 Hz position update rate

static String serial_buffer;

static void printStatusLine() {
    SystemStatus st = sensor.getStatus();
    Serial.print("STATUS,");
    Serial.print(st.is_valid);
    Serial.print(",");
    Serial.print(st.frame_count);
    Serial.print(",");
    Serial.print(st.last_update_ms);
    Serial.print(",");
    Serial.print(st.spherical.r_mm, 2);
    Serial.print(",");
    Serial.print(st.spherical.theta_deg, 3);
    Serial.print(",");
    Serial.print(st.spherical.phi_deg, 3);
    Serial.print(",");
    Serial.print(st.position.x_mm, 2);
    Serial.print(",");
    Serial.print(st.position.y_mm, 2);
    Serial.print(",");
    Serial.println(st.position.z_mm, 2);

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
    Serial.println("  Firmware v1.0.1 (Refactored)");
    Serial.println("========================================\n");
    
    // Initialize sensor hardware
    sensor.begin();
    
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

    // Update position at fixed interval
    if (millis() - last_update >= UPDATE_PERIOD_MS) {
        last_update = millis();

        // Calculate new position from current sensor readings
        sensor.updatePosition();

        // Print position every ~500 ms
        static unsigned long last_print = 0;
        if (millis() - last_print >= 500) {
            last_print = millis();
            sensor.printPosition();
        }
    }
}
