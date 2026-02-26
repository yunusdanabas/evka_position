// DrawWireTest.cpp
// Phase 1 validation: OPKON DWE3000 draw-wire encoder — quadrature A/B + Z index
// Enhanced with GPIO diagnostics and calibration workflow.
//
// Target: Wemos D1 R32 (ESP32-WROOM-32)
//
// Voltage WARNING: DWE3000 outputs swing 0-5 V.
//     ESP32 GPIO max is 3.3 V.  Use a 10k / 20k voltage divider
//     (or 74AHCT125 buffer) on every encoder line before the ESP32.
//
// Wiring (safe GPIOs — avoids flash-reserved GPIO 6-11):
//   PIN_WIRE_A (16) — Quadrature A output
//   PIN_WIRE_B (17) — Quadrature B output
//   PIN_WIRE_Z (18) — Index / Z channel
//
// Encoder specs (OPKON DWE3000 HLD P2000 Z V3):
//   PPR  = 2000 pulses / revolution
//   Drum = 200 mm / revolution
//   -> MM_PER_PULSE = 0.1 mm / pulse
//
// Expected behaviour:
//   Pulling wire out  -> COUNT increases
//   Pushing wire back -> COUNT decreases
//   Pull 200 mm -> COUNT ~ +2000, DIST_mm ~ 200.0, Z_ticks increments by 1
//
// Serial: 115200 baud, output every 200 ms
//
// Commands:
//   ZERO — reset encoder count, Z ticks, and raw edge counter
//   CAL  — enter calibration mode (records start count)
//   DONE — exit calibration mode (prints delta, measured mm, correction factor)
//   DIAG — re-run startup GPIO diagnostic

#include <Arduino.h>
#include <Encoder.h>

#define PIN_WIRE_A   16      // Quadrature A
#define PIN_WIRE_B   17      // Quadrature B
#define PIN_WIRE_Z   18      // Index channel

#define PPR_WIRE        2000.0
#define DRUM_CIRCUM_MM   200.0
#define MM_PER_PULSE    (DRUM_CIRCUM_MM / PPR_WIRE)   // = 0.1 mm/pulse

Encoder* wireEnc;

volatile uint32_t z_count = 0;

// Polled edge counter — detects A-pin transitions independent of Encoder library
volatile uint32_t raw_a_transitions = 0;
uint8_t prev_a_state = 0;

// Calibration state
enum Mode { MODE_NORMAL, MODE_CAL };
Mode currentMode = MODE_NORMAL;
int32_t cal_start_count = 0;

// IRAM_ATTR keeps the ISR in fast IRAM on ESP32
void IRAM_ATTR zISR() {
    z_count++;
}

// ---------------------------------------------------------------------------
// Startup GPIO diagnostic — reads pin states and counts transitions over 1 s
// ---------------------------------------------------------------------------
void runStartupDiagnostic() {
    Serial.println();
    Serial.println("=== GPIO DIAGNOSTIC ===");

    // Read static pin states
    uint8_t a_state = digitalRead(PIN_WIRE_A);
    uint8_t b_state = digitalRead(PIN_WIRE_B);
    uint8_t z_state = digitalRead(PIN_WIRE_Z);

    Serial.print("  Pin A (GPIO ");
    Serial.print(PIN_WIRE_A);
    Serial.print(") = ");
    Serial.println(a_state);
    Serial.print("  Pin B (GPIO ");
    Serial.print(PIN_WIRE_B);
    Serial.print(") = ");
    Serial.println(b_state);
    Serial.print("  Pin Z (GPIO ");
    Serial.print(PIN_WIRE_Z);
    Serial.print(") = ");
    Serial.println(z_state);

    // Rapid-sample all 3 pins for 1 second, count transitions
    Serial.println("  Sampling pins for 1 second (wiggle wire now)...");

    uint32_t a_trans = 0, b_trans = 0, z_trans = 0;
    uint8_t prev_a = a_state, prev_b = b_state, prev_z = z_state;
    unsigned long start = millis();

    while (millis() - start < 1000) {
        uint8_t cur_a = digitalRead(PIN_WIRE_A);
        uint8_t cur_b = digitalRead(PIN_WIRE_B);
        uint8_t cur_z = digitalRead(PIN_WIRE_Z);
        if (cur_a != prev_a) { a_trans++; prev_a = cur_a; }
        if (cur_b != prev_b) { b_trans++; prev_b = cur_b; }
        if (cur_z != prev_z) { z_trans++; prev_z = cur_z; }
    }

    Serial.print("  Transitions in 1 s:  A=");
    Serial.print(a_trans);
    Serial.print("  B=");
    Serial.print(b_trans);
    Serial.print("  Z=");
    Serial.println(z_trans);

    // Interpretation
    Serial.print("  -> ");
    if (a_trans == 0 && b_trans == 0 && z_trans >= 4) {
        Serial.println("Likely Z wired where B expected.");
    } else if (a_trans == 0 && b_trans == 0 && z_trans == 0) {
        Serial.println("No signal activity. Check encoder power, wiring, and dividers.");
    } else if (a_trans > 0 && b_trans == 0) {
        Serial.println("B channel stuck or wrong pin mapping.");
    } else if (b_trans > 0 && a_trans == 0) {
        Serial.println("A channel stuck or wrong pin mapping.");
    } else if (a_trans == 0 && b_trans == 0) {
        Serial.println("No quadrature activity on A/B. Check A/B wiring and dividers.");
    } else {
        Serial.print("Signals arriving (A=");
        Serial.print(a_trans);
        Serial.print(", B=");
        Serial.print(b_trans);
        Serial.println(" edges). Encoder appears OK.");
    }

    Serial.println("=======================");
    Serial.println();
}

// ---------------------------------------------------------------------------
// Process serial commands: ZERO, CAL, DONE, DIAG
// ---------------------------------------------------------------------------
void processSerialCommand(const String& cmd) {
    if (cmd == "ZERO") {
        wireEnc->write(0);
        noInterrupts();
        z_count = 0;
        interrupts();
        raw_a_transitions = 0;
        currentMode = MODE_NORMAL;
        Serial.println("ACK:ZERO  (count, Z ticks, raw edges reset)");

    } else if (cmd == "CAL") {
        cal_start_count = wireEnc->read();
        currentMode = MODE_CAL;
        Serial.print("ACK:CAL  start_count=");
        Serial.println(cal_start_count);
        Serial.println("  Pull wire a known distance, then send DONE.");

    } else if (cmd == "DONE") {
        if (currentMode != MODE_CAL) {
            Serial.println("ERR: not in calibration mode. Send CAL first.");
            return;
        }
        int32_t end_count = wireEnc->read();
        int32_t delta = end_count - cal_start_count;
        float measured_mm = (float)delta * MM_PER_PULSE;
        currentMode = MODE_NORMAL;

        Serial.println("=== CALIBRATION RESULT ===");
        Serial.print("  start_count = ");
        Serial.println(cal_start_count);
        Serial.print("  end_count   = ");
        Serial.println(end_count);
        Serial.print("  delta       = ");
        Serial.println(delta);
        Serial.print("  measured_mm = ");
        Serial.println(measured_mm, 1);
        Serial.println();
        Serial.println("  To compute correction factor:");
        Serial.println("    factor = actual_mm / measured_mm");
        Serial.println("    new_MM_PER_PULSE = MM_PER_PULSE * factor");
        Serial.println("==========================");

    } else if (cmd == "DIAG") {
        runStartupDiagnostic();

    } else {
        Serial.print("Unknown command: ");
        Serial.println(cmd);
        Serial.println("  Available: ZERO, CAL, DONE, DIAG");
    }
}

// ---------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    // Non-blocking wait for USB-CDC serial; give up after 3 s
    unsigned long t0 = millis();
    while (!Serial && millis() - t0 < 3000) {}

    // Configure pins as inputs before Encoder library takes over A/B
    pinMode(PIN_WIRE_A, INPUT_PULLUP);
    pinMode(PIN_WIRE_B, INPUT_PULLUP);
    pinMode(PIN_WIRE_Z, INPUT_PULLUP);

    // Capture initial A state for polled edge counter
    prev_a_state = digitalRead(PIN_WIRE_A);

    // Construct Encoder here (not as global) — ESP32 GPIO ISR service
    // is not ready during global constructors.
    wireEnc = new Encoder(PIN_WIRE_A, PIN_WIRE_B);

    attachInterrupt(digitalPinToInterrupt(PIN_WIRE_Z), zISR, RISING);

    Serial.println("DrawWireTest ready. (ESP32 / OPKON DWE3000 quadrature)");
    Serial.println("Pull wire to increase count, push to decrease.");
    Serial.println("200 mm pull -> COUNT ~2000, Z_ticks +1");
    Serial.println("Commands: ZERO | CAL | DONE | DIAG");
    Serial.println("--------------------------------------------");

    runStartupDiagnostic();
}

void loop() {
    static unsigned long last_print = 0;
    static String serial_buf;

    // --- Poll A-pin for raw edge counting (independent of Encoder library) ---
    uint8_t cur_a = digitalRead(PIN_WIRE_A);
    if (cur_a != prev_a_state) {
        raw_a_transitions++;
        prev_a_state = cur_a;
    }

    // --- Process incoming serial commands ---
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            serial_buf.trim();
            if (serial_buf.length() > 0) {
                processSerialCommand(serial_buf);
            }
            serial_buf = "";
        } else {
            serial_buf += c;
        }
    }

    // --- Periodic output (every 200 ms) ---
    if (millis() - last_print >= 200) {
        last_print = millis();

        int32_t count = wireEnc->read();

        noInterrupts();
        uint32_t z = z_count;
        interrupts();

        float dist_mm = (float)count * MM_PER_PULSE;

        uint8_t a_pin = digitalRead(PIN_WIRE_A);
        uint8_t b_pin = digitalRead(PIN_WIRE_B);
        uint8_t z_pin = digitalRead(PIN_WIRE_Z);

        if (currentMode == MODE_CAL) {
            int32_t delta = count - cal_start_count;
            float cal_mm = (float)delta * MM_PER_PULSE;
            Serial.print("[CAL] delta=");
            Serial.print(delta);
            Serial.print("  dist=");
            Serial.print(cal_mm, 1);
            Serial.print(" mm  A=");
            Serial.print(a_pin);
            Serial.print(" B=");
            Serial.print(b_pin);
            Serial.print(" Z=");
            Serial.println(z_pin);
        } else {
            Serial.print("COUNT=");
            Serial.print(count);
            Serial.print("  DIST_mm=");
            Serial.print(dist_mm, 1);
            Serial.print("  Z_ticks=");
            Serial.print(z);
            Serial.print("  A=");
            Serial.print(a_pin);
            Serial.print(" B=");
            Serial.print(b_pin);
            Serial.print(" Z=");
            Serial.print(z_pin);
            Serial.print("  raw_edges=");
            Serial.println(raw_a_transitions);
        }
    }
}
