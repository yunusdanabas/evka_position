// DrawWireTest.cpp
// OPKON DWEM2 draw-wire encoder — distance readout + wire calibration
//
// Target: ESP32-WROOM-32
//
// Wiring:
//   PIN_WIRE_A (16) — Quadrature A
//   PIN_WIRE_B (17) — Quadrature B
//
// Encoder specs (OPKON DWEM2 P2000):
//   PPR  = 2000 mechanical pulses / revolution
//   X4 quadrature -> PPR_WIRE = 8000 counts / revolution
//   Drum = 200 mm / revolution
//   -> MM_PER_PULSE = 0.025 mm / count
//
// Serial: 115200 baud
// Commands:
//   ZERO_W           — reset wire encoder to 0
//   ZERO             — alias for ZERO_W
//   CAL_W <actual_mm> — calibrate: ZERO_W, pull wire known distance, send CAL_W <mm>

#include <Arduino.h>
#include <Encoder.h>

#define PIN_WIRE_A   16
#define PIN_WIRE_B   17

#define PPR_WIRE        8000.0
#define DRUM_CIRCUM_MM   200.0

// Runtime calibration values
float mm_per_pulse = DRUM_CIRCUM_MM / PPR_WIRE;   // 0.025 mm/count

Encoder* wireEnc;

void setup() {
    Serial.begin(115200);
    unsigned long t0 = millis();
    while (!Serial && millis() - t0 < 3000) {}

    pinMode(PIN_WIRE_A, INPUT_PULLUP);
    pinMode(PIN_WIRE_B, INPUT_PULLUP);

    wireEnc = new Encoder(PIN_WIRE_A, PIN_WIRE_B);

    Serial.println("DrawWireTest ready.");
    Serial.print  ("  MM_PER_PULSE="); Serial.println(mm_per_pulse, 4);
    Serial.println("  Commands: ZERO_W | ZERO | CAL_W <actual_mm>");
    Serial.println("  Calibrate: ZERO_W -> pull wire known distance -> CAL_W <mm>");
    Serial.println("--------------------------------------------");
}

static void processCommand(const String& cmd) {
    if (cmd == "ZERO" || cmd == "ZERO_W") {
        wireEnc->write(0);
        Serial.println("ACK:ZERO_W");

    } else if (cmd.startsWith("CAL_W ")) {
        float actual_mm = cmd.substring(6).toFloat();
        if (actual_mm <= 0.0f) {
            Serial.println("ERR: CAL_W requires a positive distance in mm. Example: CAL_W 500");
            return;
        }
        int32_t raw_count = -wireEnc->read();   // negate: extension = positive
        if (raw_count == 0) {
            Serial.println("ERR: Count is 0. Send ZERO_W, pull wire, then CAL_W <mm>.");
            return;
        }
        float measured_mm     = (float)raw_count * mm_per_pulse;
        float correction      = actual_mm / measured_mm;
        float new_mm_per_pulse = mm_per_pulse * correction;
        float new_ppr_wire    = DRUM_CIRCUM_MM / new_mm_per_pulse;

        Serial.println();
        Serial.println("=== CAL_W RESULT ===");
        Serial.print("  Actual distance   : "); Serial.print(actual_mm, 2); Serial.println(" mm");
        Serial.print("  Measured distance : "); Serial.print(measured_mm, 2); Serial.println(" mm");
        Serial.print("  Correction factor : "); Serial.println(correction, 6);
        Serial.print("  New MM_PER_PULSE  : "); Serial.println(new_mm_per_pulse, 6);
        Serial.print("  New PPR_WIRE      : "); Serial.println(new_ppr_wire, 2);
        Serial.println("  Live values updated. To make permanent: update firmware constants.");
        Serial.println("====================");
        Serial.println();

        mm_per_pulse = new_mm_per_pulse;
        wireEnc->write(0);

    } else {
        Serial.print("Unknown command: "); Serial.println(cmd);
        Serial.println("  Available: ZERO_W | ZERO | CAL_W <actual_mm>");
    }
}

void loop() {
    static unsigned long last_print = 0;
    static String serial_buf;

    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            serial_buf.trim();
            if (serial_buf.length() > 0) processCommand(serial_buf);
            serial_buf = "";
        } else {
            serial_buf += c;
        }
    }

    if (millis() - last_print >= 200) {
        last_print = millis();

        // Negate so wire extension (pull-out) gives positive distance
        int32_t count = -wireEnc->read();
        float dist_mm = (float)count * mm_per_pulse;

        Serial.print("DIST=");
        Serial.print(dist_mm, 1);
        Serial.print(" mm  (count=");
        Serial.print(count);
        Serial.println(")");
    }
}
