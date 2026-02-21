// RotaryEncoderTest.ino
// Phase 2 validation: dual quadrature encoder count + angle
//
// Target: ESP32 (Wemos D1 R32 — all GPIO pins are interrupt-capable)
//
// Requires: "Encoder" library by Paul Stoffregen (Library Manager)
//
// Wiring:
//   Theta encoder: A → GPIO 2,  B → GPIO 4
//   Phi   encoder: A → GPIO 3,  B → GPIO 5
//
// Expected behaviour:
//   One full CW shaft rotation → +5000 counts, +360.0 deg
//   One full CCW rotation     → -5000 counts, -360.0 deg
//   (swap A/B wires if direction is inverted)
//
// Serial: 115200 baud, output every 200 ms
// Format: THETA_counts=<n>  THETA_deg=<n*0.072>  |  PHI_counts=<n>  PHI_deg=<n*0.072>

#include <Arduino.h>
#include <Encoder.h>

// Pin assignments — must match SphericalSensor.h
#define PIN_THETA_A  2
#define PIN_THETA_B  4
#define PIN_PHI_A    3
#define PIN_PHI_B    5

// Resolution
#define PPR_ROTARY    5000.0
#define DEG_PER_PULSE (360.0 / PPR_ROTARY)  // = 0.072 deg/pulse

Encoder thetaEnc(PIN_THETA_A, PIN_THETA_B);
Encoder phiEnc(PIN_PHI_A,   PIN_PHI_B);

void setup() {
    Serial.begin(115200);
    // Non-blocking wait for USB serial (ESP32 CDC); give up after 3 s
    unsigned long t0 = millis();
    while (!Serial && millis() - t0 < 3000) {}

    Serial.println("RotaryEncoderTest ready. (ESP32)");
    Serial.println("Rotate theta shaft one full turn → ±5000 counts.");
    Serial.println("------------------------------------------------------");
}

void loop() {
    static unsigned long last_print = 0;

    if (millis() - last_print >= 200) {
        last_print = millis();

        int32_t theta_cnt = thetaEnc.read();
        int32_t phi_cnt   = phiEnc.read();

        float theta_deg = theta_cnt * DEG_PER_PULSE;
        float phi_deg   = phi_cnt   * DEG_PER_PULSE;

        Serial.print("THETA_counts=");
        Serial.print(theta_cnt);
        Serial.print("  THETA_deg=");
        Serial.print(theta_deg, 2);
        Serial.print("  |  PHI_counts=");
        Serial.print(phi_cnt);
        Serial.print("  PHI_deg=");
        Serial.println(phi_deg, 2);
    }
}
