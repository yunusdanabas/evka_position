#include "SphericalSensor.h"

// ============================================================================
// ARDUINO SKETCH
// ============================================================================

SphericalPositioningSensor sensor;

// Update Frequency
#define UPDATE_PERIOD_MS  50  // 20 Hz position update rate

void setup() {
    Serial.begin(115200);
    // Wait for serial to settle
    delay(500);
    
    Serial.println("
========================================");
    Serial.println("  Spherical 3D Positioning System");
    Serial.println("  Firmware v1.0.1 (Refactored)");
    Serial.println("========================================
");
    
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
    if (Serial.available() > 0) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        if (cmd == "ZERO") {
            sensor.setZeroPoint();
            Serial.println("ACK:ZERO");
        }
    }

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
