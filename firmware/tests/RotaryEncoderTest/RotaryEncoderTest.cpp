// RotaryEncoderTest.cpp
// Dual quadrature rotary encoder count + angle with per-axis live calibration.
//
// Target: ESP32 (Wemos D1 R32 — all GPIO pins are interrupt-capable)
// Encoder: Autonics E40S6 (push-pull 0-5 V output)
//
// Wiring:
//   Theta: A (black) → GPIO 14, B (white) → GPIO 12
//   Phi:   A (black) → GPIO 32, B (white) → GPIO 35
//
// Serial: 115200 baud, output every 200 ms.
//
// Commands (send with newline):
//   ZERO      — reset both theta and phi counts to 0
//   ZERO_T    — reset theta count only
//   ZERO_P    — reset phi count only
//   CAL_T <n> — calibrate theta: ZERO_T, rotate n full turns, send CAL_T n
//   CAL_P <n> — calibrate phi:   ZERO_P, rotate n full turns, send CAL_P n
//   DIAG      — sample all 4 pins for 1 s and report transitions
//   VERBOSE   — toggle per-sample A/B pin levels in output

#include <Arduino.h>
#include <Encoder.h>

// Pin assignments — must match SphericalSensor.h
#define PIN_THETA_A  14
#define PIN_THETA_B  12
#define PIN_PHI_A    32
#define PIN_PHI_B    35

// Runtime calibration values — E30S6-5000 @ X4 quadrature = 20000 counts/rev
float ppr_theta       = 20000.0f;
float ppr_phi         = 20000.0f;
float deg_per_pulse_t = 360.0f / 20000.0f;
float deg_per_pulse_p = 360.0f / 20000.0f;

Encoder* thetaEnc;
Encoder* phiEnc;
bool verbose_mode = false;

// ---------------------------------------------------------------------------
// Calibration helper — shared by CAL_T and CAL_P
// ---------------------------------------------------------------------------
void runCal(Encoder* e, int n, float& ppr_out, float& dpp_out, const char* name) {
    if (n <= 0) {
        Serial.print("ERR: CAL_"); Serial.print(name);
        Serial.println(" requires a positive integer. Example: CAL_T 3");
        return;
    }
    int32_t total = e->read();
    if (total == 0) {
        Serial.print("ERR: "); Serial.print(name);
        Serial.println(" count is 0. Send ZERO_T/ZERO_P, rotate, then CAL.");
        return;
    }
    float measured_ppr = (float)total / (float)n;
    float measured_dpp = 360.0f / measured_ppr;

    Serial.println();
    Serial.print("=== CAL_"); Serial.print(name); Serial.println(" RESULT ===");
    Serial.print("  Rotations    : "); Serial.println(n);
    Serial.print("  Total counts : "); Serial.println(total);
    Serial.print("  counts/rev   : "); Serial.println(measured_ppr, 2);
    Serial.print("  deg/pulse    : "); Serial.println(measured_dpp, 4);
    Serial.println("  Live values updated. To make permanent: update ppr in firmware.");
    Serial.println("=========================");
    Serial.println();

    ppr_out = measured_ppr;
    dpp_out = measured_dpp;
    e->write(0);
}

// ---------------------------------------------------------------------------
// GPIO diagnostic — static levels then 1-second transition count
// ---------------------------------------------------------------------------
void runDiagnostic() {
    Serial.println();
    Serial.println("=== GPIO DIAGNOSTIC ===");
    Serial.print("  Theta A (GPIO "); Serial.print(PIN_THETA_A);
    Serial.print(") = "); Serial.println(digitalRead(PIN_THETA_A));
    Serial.print("  Theta B (GPIO "); Serial.print(PIN_THETA_B);
    Serial.print(") = "); Serial.println(digitalRead(PIN_THETA_B));
    Serial.print("  Phi   A (GPIO "); Serial.print(PIN_PHI_A);
    Serial.print(") = "); Serial.println(digitalRead(PIN_PHI_A));
    Serial.print("  Phi   B (GPIO "); Serial.print(PIN_PHI_B);
    Serial.print(") = "); Serial.println(digitalRead(PIN_PHI_B));

    Serial.println("  Sampling pins for 1 second (rotate both shafts now)...");

    uint32_t ta = 0, tb = 0, pa = 0, pb = 0;
    uint8_t pt_a = digitalRead(PIN_THETA_A);
    uint8_t pt_b = digitalRead(PIN_THETA_B);
    uint8_t pp_a = digitalRead(PIN_PHI_A);
    uint8_t pp_b = digitalRead(PIN_PHI_B);

    unsigned long start = millis();
    while (millis() - start < 1000) {
        uint8_t c;
        if ((c = digitalRead(PIN_THETA_A)) != pt_a) { ta++; pt_a = c; }
        if ((c = digitalRead(PIN_THETA_B)) != pt_b) { tb++; pt_b = c; }
        if ((c = digitalRead(PIN_PHI_A))   != pp_a) { pa++; pp_a = c; }
        if ((c = digitalRead(PIN_PHI_B))   != pp_b) { pb++; pp_b = c; }
    }

    Serial.print("  Transitions:  THETA_A="); Serial.print(ta);
    Serial.print("  THETA_B=");               Serial.print(tb);
    Serial.print("  |  PHI_A=");              Serial.print(pa);
    Serial.print("  PHI_B=");                 Serial.println(pb);

    auto interpret = [](uint32_t a, uint32_t b, const char* name) {
        Serial.print("  -> "); Serial.print(name); Serial.print(": ");
        if (a == 0 && b == 0)       Serial.println("No signal. Check power and dividers.");
        else if (a > 0 && b == 0)   Serial.println("B stuck — check B wire and divider.");
        else if (b > 0 && a == 0)   Serial.println("A stuck — check A wire and divider.");
        else { Serial.print("Quadrature OK (A="); Serial.print(a);
               Serial.print(", B="); Serial.print(b); Serial.println(" edges)."); }
    };
    interpret(ta, tb, "THETA");
    interpret(pa, pb, "PHI");
    Serial.println("=======================");
    Serial.println();
}

// ---------------------------------------------------------------------------
// Serial command handler
// ---------------------------------------------------------------------------
void processCommand(const String& cmd) {
    if (cmd == "ZERO") {
        thetaEnc->write(0); phiEnc->write(0);
        Serial.println("ACK:ZERO  (theta + phi reset to 0)");
    } else if (cmd == "ZERO_T") {
        thetaEnc->write(0);
        Serial.println("ACK:ZERO_T");
    } else if (cmd == "ZERO_P") {
        phiEnc->write(0);
        Serial.println("ACK:ZERO_P");
    } else if (cmd.startsWith("CAL_T ")) {
        runCal(thetaEnc, cmd.substring(6).toInt(), ppr_theta, deg_per_pulse_t, "T");
    } else if (cmd.startsWith("CAL_P ")) {
        runCal(phiEnc,   cmd.substring(6).toInt(), ppr_phi,   deg_per_pulse_p, "P");
    } else if (cmd == "DIAG") {
        runDiagnostic();
    } else if (cmd == "VERBOSE") {
        verbose_mode = !verbose_mode;
        Serial.print("Verbose mode: "); Serial.println(verbose_mode ? "ON" : "OFF");
    } else {
        Serial.print("Unknown command: "); Serial.println(cmd);
        Serial.println("  Available: ZERO | ZERO_T | ZERO_P | CAL_T <n> | CAL_P <n> | DIAG | VERBOSE");
    }
}

// ---------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    thetaEnc = new Encoder(PIN_THETA_A, PIN_THETA_B);
    phiEnc   = new Encoder(PIN_PHI_A,   PIN_PHI_B);
}

// ---------------------------------------------------------------------------
void loop() {
    static unsigned long last_print  = 0;
    static unsigned long boot_ms     = millis();
    static bool          banner_done = false;
    static String        serial_buf;

    if (!banner_done && millis() - boot_ms >= 5000) {
        banner_done = true;
        thetaEnc->write(0);
        phiEnc->write(0);
        Serial.println();
        Serial.println("RotaryEncoderTest ready. (ESP32 / Autonics E40S6)");
        Serial.println("  Theta: A (black) -> GPIO 14, B (white) -> GPIO 12");
        Serial.println("  Phi:   A (black) -> GPIO 32, B (white) -> GPIO 35");
        Serial.print  ("  PPR theta="); Serial.print(ppr_theta, 1);
        Serial.print  ("  phi=");       Serial.println(ppr_phi, 1);
        Serial.println("  Calibrate: ZERO_T -> rotate N turns -> CAL_T N  (same for PHI)");
        Serial.println("  Commands: ZERO | ZERO_T | ZERO_P | CAL_T <n> | CAL_P <n> | DIAG | VERBOSE");
        Serial.println("------------------------------------------------------");
        runDiagnostic();
    }

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

        int32_t theta_cnt = thetaEnc->read();
        int32_t phi_cnt   = phiEnc->read();
        float   theta_deg = theta_cnt * deg_per_pulse_t;
        float   phi_deg   = phi_cnt   * deg_per_pulse_p;

        if (verbose_mode) {
            uint8_t ta = digitalRead(PIN_THETA_A), tb = digitalRead(PIN_THETA_B);
            uint8_t pa = digitalRead(PIN_PHI_A),   pb = digitalRead(PIN_PHI_B);
            Serial.print("THETA_counts="); Serial.print(theta_cnt);
            Serial.print("  THETA_deg=");  Serial.print(theta_deg, 2);
            Serial.print("  A="); Serial.print(ta); Serial.print(" B="); Serial.print(tb);
            Serial.print("  |  PHI_counts="); Serial.print(phi_cnt);
            Serial.print("  PHI_deg=");    Serial.print(phi_deg, 2);
            Serial.print("  A="); Serial.print(pa); Serial.print(" B="); Serial.println(pb);
        } else {
            Serial.print("THETA_deg="); Serial.print(theta_deg, 2);
            Serial.print("  |  PHI_deg="); Serial.println(phi_deg, 2);
        }
    }
}
