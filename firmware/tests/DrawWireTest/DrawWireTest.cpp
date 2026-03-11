// DrawWireTest.cpp
// OPKON DWE3000 draw-wire encoder — distance readout
//
// Target: ESP32-WROOM-32
//
// Wiring:
//   PIN_WIRE_A (16) — Quadrature A
//   PIN_WIRE_B (17) — Quadrature B
//
// Encoder specs:
//   PPR  = 2000 pulses / revolution
//   Drum = 200 mm / revolution
//   -> MM_PER_PULSE = 0.1 mm / pulse
//
// Serial: 115200 baud
// Commands:
//   ZERO — reset distance to 0

#include <Arduino.h>
#include <Encoder.h>

#define PIN_WIRE_A   16
#define PIN_WIRE_B   17

#define PPR_WIRE        2000.0
#define DRUM_CIRCUM_MM   200.0
#define MM_PER_PULSE    (DRUM_CIRCUM_MM / PPR_WIRE)   // 0.1 mm/pulse

Encoder* wireEnc;

void setup() {
    Serial.begin(115200);
    unsigned long t0 = millis();
    while (!Serial && millis() - t0 < 3000) {}

    pinMode(PIN_WIRE_A, INPUT_PULLUP);
    pinMode(PIN_WIRE_B, INPUT_PULLUP);

    wireEnc = new Encoder(PIN_WIRE_A, PIN_WIRE_B);

    Serial.println("DrawWireTest ready. Send ZERO to reset.");
    Serial.println("--------------------------------------------");
}

void loop() {
    static unsigned long last_print = 0;
    static String serial_buf;

    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            serial_buf.trim();
            if (serial_buf == "ZERO") {
                wireEnc->write(0);
                Serial.println("ACK:ZERO");
            }
            serial_buf = "";
        } else {
            serial_buf += c;
        }
    }

    if (millis() - last_print >= 200) {
        last_print = millis();

        // Negate so wire extension (pull-out) gives positive distance
        int32_t count = -wireEnc->read();
        float dist_mm = (float)count * MM_PER_PULSE;

        Serial.print("DIST=");
        Serial.print(dist_mm, 1);
        Serial.print(" mm  (count=");
        Serial.print(count);
        Serial.println(")");
    }
}
