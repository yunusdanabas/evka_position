// SingleRotaryTest.cpp
// Single quadrature rotary encoder count + angle readout with live calibration.
//
// Target : ESP32 (Wemos D1 R32)
// Encoder: Autonics E40S6  (push-pull 0-5 V output)
//
// VOLTAGE WARNING: E40S6 outputs swing 0-5 V.
//   ESP32 GPIO max is 3.3 V.  Use a 10k/20k voltage divider
//   on both A and B lines before the ESP32 GPIO pins.
//
// Wiring (theta):
//   A signal  →  10k/20k divider  →  GPIO 32
//   B signal  →  10k/20k divider  →  GPIO 35  (input-only, no internal pull-up)
//   GND → GND,  +5 V → external 5 V supply
//
// Serial: 115200 baud, output every 200 ms.
//
// Commands (send with newline):
//   ZERO      — reset encoder count to 0
//   CAL <n>   — calibrate: send ZERO, rotate n full turns, then send CAL <n>
//               firmware computes counts/rev and deg/pulse from current count
//   DIAG      — sample GPIO for 1 s and report transitions
//   VERBOSE   — toggle per-sample A/B pin levels in output

#include <Arduino.h>
#include <Encoder.h>

#define PIN_ENC_A  32
#define PIN_ENC_B  35

// Runtime calibration values — update with CAL command or set measured PPR here
float ppr           = 1480.0f;   // measured counts per revolution
float deg_per_pulse = 360.0f / 1480.0f;

Encoder* enc;
bool verbose_mode = false;

// ---------------------------------------------------------------------------
// GPIO diagnostic — static levels then 1-second transition count
// ---------------------------------------------------------------------------
void runDiagnostic() {
    Serial.println();
    Serial.println("=== GPIO DIAGNOSTIC ===");
    Serial.print("  A (GPIO "); Serial.print(PIN_ENC_A);
    Serial.print(") = "); Serial.println(digitalRead(PIN_ENC_A));
    Serial.print("  B (GPIO "); Serial.print(PIN_ENC_B);
    Serial.print(") = "); Serial.println(digitalRead(PIN_ENC_B));

    Serial.println("  Sampling for 1 second — rotate shaft now...");

    uint32_t ca = 0, cb = 0;
    uint8_t pa = digitalRead(PIN_ENC_A);
    uint8_t pb = digitalRead(PIN_ENC_B);
    unsigned long start = millis();
    while (millis() - start < 1000) {
        uint8_t v;
        if ((v = digitalRead(PIN_ENC_A)) != pa) { ca++; pa = v; }
        if ((v = digitalRead(PIN_ENC_B)) != pb) { cb++; pb = v; }
    }

    Serial.print("  Transitions:  A="); Serial.print(ca);
    Serial.print("  B=");              Serial.println(cb);

    if (ca == 0 && cb == 0) {
        Serial.println("  -> No signal. Check encoder power and voltage dividers.");
    } else if (ca > 0 && cb == 0) {
        Serial.println("  -> B channel stuck — check B wire and divider.");
    } else if (cb > 0 && ca == 0) {
        Serial.println("  -> A channel stuck — check A wire and divider.");
    } else {
        Serial.println("  -> Quadrature OK.");
    }

    Serial.println("=======================");
    Serial.println();
}

// ---------------------------------------------------------------------------
// Serial command handler
// ---------------------------------------------------------------------------
void processCommand(const String& cmd) {
    if (cmd == "ZERO") {
        enc->write(0);
        Serial.println("ACK:ZERO");

    } else if (cmd.startsWith("CAL ")) {
        // CAL <n>  — n = number of full rotations performed since last ZERO
        int n = cmd.substring(4).toInt();
        if (n <= 0) {
            Serial.println("ERR: CAL requires a positive integer. Example: CAL 3");
            return;
        }
        int32_t total_counts = enc->read();
        if (total_counts == 0) {
            Serial.println("ERR: Count is 0. Send ZERO, rotate, then CAL <n>.");
            return;
        }
        float measured_ppr      = (float)total_counts / (float)n;
        float measured_deg_pp   = 360.0f / measured_ppr;

        Serial.println();
        Serial.println("=== CALIBRATION RESULT ===");
        Serial.print("  Rotations     : "); Serial.println(n);
        Serial.print("  Total counts  : "); Serial.println(total_counts);
        Serial.print("  counts/rev    : "); Serial.println(measured_ppr, 2);
        Serial.print("  deg/pulse     : "); Serial.println(measured_deg_pp, 4);
        Serial.println();
        Serial.println("  Updating live values — verify output below.");
        Serial.println("  To make permanent: set ppr = above value in firmware.");
        Serial.println("==========================");
        Serial.println();

        ppr           = measured_ppr;
        deg_per_pulse = measured_deg_pp;
        enc->write(0);   // re-zero after calibration

    } else if (cmd == "DIAG") {
        runDiagnostic();

    } else if (cmd == "VERBOSE") {
        verbose_mode = !verbose_mode;
        Serial.print("Verbose mode: "); Serial.println(verbose_mode ? "ON" : "OFF");

    } else {
        Serial.print("Unknown command: "); Serial.println(cmd);
        Serial.println("  Available: ZERO | CAL <n> | DIAG | VERBOSE");
    }
}

// ---------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    enc = new Encoder(PIN_ENC_A, PIN_ENC_B);
}

// ---------------------------------------------------------------------------
void loop() {
    static unsigned long last_print  = 0;
    static unsigned long boot_ms     = millis();
    static bool          banner_done = false;
    static String        serial_buf;

    // --- One-time startup banner (5 s after first loop() call) ---
    if (!banner_done && millis() - boot_ms >= 5000) {
        banner_done = true;
        enc->write(0);
        Serial.println();
        Serial.println("SingleRotaryTest ready.  (ESP32 / Autonics E40S6)");
        Serial.print  ("Encoder: A -> GPIO "); Serial.print(PIN_ENC_A);
        Serial.print  (", B -> GPIO "); Serial.println(PIN_ENC_B);
        Serial.print  ("PPR (current): "); Serial.print(ppr, 1);
        Serial.print  ("  deg/pulse: ");  Serial.println(deg_per_pulse, 4);
        Serial.println("To calibrate: ZERO -> rotate N full turns -> CAL N");
        Serial.println("Commands: ZERO | CAL <n> | DIAG | VERBOSE");
        Serial.println("---------------------------------------------------");
        runDiagnostic();
    }

    // --- Process serial commands ---
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

    // --- Periodic output (every 200 ms) ---
    if (millis() - last_print >= 200) {
        last_print = millis();
        int32_t cnt = enc->read();
        float   deg = cnt * deg_per_pulse;

        if (verbose_mode) {
            Serial.print("counts="); Serial.print(cnt);
            Serial.print("  deg=");  Serial.print(deg, 2);
            Serial.print("  A=");    Serial.print(digitalRead(PIN_ENC_A));
            Serial.print("  B=");    Serial.println(digitalRead(PIN_ENC_B));
        } else {
            Serial.print("counts="); Serial.print(cnt);
            Serial.print("  deg=");  Serial.println(deg, 2);
        }
    }
}
