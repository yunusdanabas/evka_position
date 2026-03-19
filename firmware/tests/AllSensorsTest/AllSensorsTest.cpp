// AllSensorsTest.cpp
// All 3 encoders simultaneously: Theta (rotary), Phi (rotary), Wire (draw-wire)
//
// Target: ESP32 (Wemos D1 R32)
//
// Wiring (matches DrawWireTest + RotaryEncoderTest):
//   Theta A -> GPIO 14,  B -> GPIO 12
//   Phi   A -> GPIO 32,  B -> GPIO 35
//   Wire  A -> GPIO 16,  B -> GPIO 17
//
// Serial: 115200 baud, output every 200 ms.
//
// Commands (send with newline):
//   ZERO   — reset all encoder counts to 0
//   DIAG   — sample all GPIO pins for 1 s, report transition counts

#include <Arduino.h>
#include <Encoder.h>

// --- Pin definitions (match DrawWireTest + RotaryEncoderTest) ---
#define PIN_THETA_A  14
#define PIN_THETA_B  12
#define PIN_PHI_A    32
#define PIN_PHI_B    35
#define PIN_WIRE_A   16
#define PIN_WIRE_B   17

// --- Encoder constants ---
#define PPR_ROTARY      20000.0f
#define PPR_WIRE        8020.0f
#define DRUM_CIRCUM_MM   200.0f
#define DEG_PER_PULSE   (360.0f / PPR_ROTARY)
#define MM_PER_PULSE    (DRUM_CIRCUM_MM / PPR_WIRE)

Encoder* thetaEnc;
Encoder* phiEnc;
Encoder* wireEnc;

// ---------------------------------------------------------------------------
static void runDiagnostic() {
    Serial.println();
    Serial.println("=== GPIO DIAGNOSTIC (all 6 encoder pins) ===");

    const int pins[]   = {PIN_THETA_A, PIN_THETA_B, PIN_PHI_A, PIN_PHI_B, PIN_WIRE_A, PIN_WIRE_B};
    const char* names[] = {"THETA_A(14)", "THETA_B(12)", "PHI_A(32)", "PHI_B(35)", "WIRE_A(16)", "WIRE_B(17)"};

    for (int i = 0; i < 6; i++) {
        Serial.print("  "); Serial.print(names[i]);
        Serial.print(" = "); Serial.println(digitalRead(pins[i]));
    }

    Serial.println("  Sampling for 1 second — move all encoders now...");
    uint32_t transitions[6] = {0};
    uint8_t  prev[6];
    for (int i = 0; i < 6; i++) prev[i] = digitalRead(pins[i]);

    unsigned long t0 = millis();
    while (millis() - t0 < 1000) {
        for (int i = 0; i < 6; i++) {
            uint8_t v = digitalRead(pins[i]);
            if (v != prev[i]) { transitions[i]++; prev[i] = v; }
        }
    }

    Serial.println("  Transitions:");
    for (int i = 0; i < 6; i++) {
        Serial.print("    "); Serial.print(names[i]);
        Serial.print(" = "); Serial.println(transitions[i]);
    }

    // Per-encoder health check
    auto check = [](const char* axis, uint32_t ta, uint32_t tb) {
        Serial.print("  "); Serial.print(axis); Serial.print(": ");
        if (ta == 0 && tb == 0)   Serial.println("NO SIGNAL — check power and voltage dividers");
        else if (ta > 0 && tb == 0) Serial.println("B stuck — check B wire/divider");
        else if (tb > 0 && ta == 0) Serial.println("A stuck — check A wire/divider");
        else                        Serial.println("Quadrature OK");
    };
    check("Theta", transitions[0], transitions[1]);
    check("Phi",   transitions[2], transitions[3]);
    check("Wire",  transitions[4], transitions[5]);

    Serial.println("=============================================");
    Serial.println();
}

// ---------------------------------------------------------------------------
static void processCommand(const String& cmd) {
    if (cmd == "ZERO") {
        thetaEnc->write(0);
        phiEnc->write(0);
        wireEnc->write(0);
        Serial.println("ACK:ZERO — all encoders reset");
    } else if (cmd == "DIAG") {
        runDiagnostic();
    } else {
        Serial.print("Unknown command: "); Serial.println(cmd);
        Serial.println("  Available: ZERO | DIAG");
    }
}

// ---------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);

    thetaEnc = new Encoder(PIN_THETA_A, PIN_THETA_B);
    phiEnc   = new Encoder(PIN_PHI_A,   PIN_PHI_B);
    wireEnc  = new Encoder(PIN_WIRE_A,  PIN_WIRE_B);

    delay(500);
    Serial.println();
    Serial.println("========================================");
    Serial.println("  AllSensorsTest — ESP32 / 3 Encoders");
    Serial.println("========================================");
    Serial.println("  Theta: GPIO 14/12 (Autonics E40S6)");
    Serial.println("  Phi  : GPIO 32/35 (Autonics E40S6)");
    Serial.println("  Wire : GPIO 16/17 (OPKON DWE3000)");
    Serial.println("  Commands: ZERO | DIAG");
    Serial.println("========================================");
    runDiagnostic();
}

// ---------------------------------------------------------------------------
void loop() {
    static unsigned long last_print = 0;
    static String        serial_buf;

    // Serial command handler
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

    // Print all 3 encoders every 200 ms
    if (millis() - last_print >= 200) {
        last_print = millis();

        int32_t tc = thetaEnc->read();
        int32_t pc = phiEnc->read();
        int32_t wc = -wireEnc->read();   // negate so wire extension = positive (match DrawWireTest)

        float theta_deg = tc * DEG_PER_PULSE;
        float phi_deg   = pc * DEG_PER_PULSE;
        float dist_mm   = (float)wc * MM_PER_PULSE;

        Serial.print("T="); Serial.print(tc);
        Serial.print(" ("); Serial.print(theta_deg, 2); Serial.print(" deg)  ");

        Serial.print("P="); Serial.print(pc);
        Serial.print(" ("); Serial.print(phi_deg, 2); Serial.print(" deg)  ");

        Serial.print("W="); Serial.print(wc);
        Serial.print(" ("); Serial.print(dist_mm, 1); Serial.println(" mm)");
    }
}
