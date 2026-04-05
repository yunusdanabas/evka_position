// CalibrationTest.cpp
// All-in-one calibration sketch for Theta, Phi (rotary) and Wire (draw-wire) encoders.
//
// Target: ESP32 (Wemos D1 R32)
//
// Wiring (matches AllSensorsTest):
//   Theta: A -> GPIO 32,  B -> GPIO 35
//   Phi:   A -> GPIO 14,  B -> GPIO 12
//   Wire:  A -> GPIO 16,  B -> GPIO 17
//
// Serial: 115200 baud, output every 200 ms.
//
// Normal commands (send with newline):
//   ZERO          — reset all 3 encoders to 0
//   ZERO_T        — reset theta only
//   ZERO_P        — reset phi only
//   ZERO_W        — reset wire only
//   CAL_T         — start interactive theta calibration (press SPACE each full turn)
//   CAL_P         — start interactive phi calibration   (press SPACE each full turn)
//   CAL_W <mm>    — after ZERO_W + pulling wire known mm: compute MM_PER_PULSE & PPR_WIRE
//   STATUS        — print live readings (counts + converted units)
//   CONSTANTS     — print current calibration constants
//   DIAG          — GPIO diagnostic on all 6 encoder pins
//
// Interactive CAL_T / CAL_P mode:
//   SPACE         — mark one full turn (up to 20 turns)
//   DONE          — finalize: compute per-turn average PPR, update live values
//   CANCEL        — abort without saving

#include <Arduino.h>
#include <Encoder.h>

// --- Pin definitions ---
#define PIN_THETA_A  32
#define PIN_THETA_B  35
#define PIN_PHI_A    14
#define PIN_PHI_B    12
#define PIN_WIRE_A   16
#define PIN_WIRE_B   17

// --- Default calibration constants ---
#define DEFAULT_PPR_ROTARY   20000.0f   // E30S6-5000 @ X4 quadrature (5000 PPR × 4)
#define DEFAULT_PPR_WIRE      8020.0f   // Calibrated — OPKON DWE3000 @ X4 quadrature
#define DRUM_CIRCUM_MM        200.0f    // mm per revolution
#define MAX_CAL_TURNS         20

// --- Runtime calibration values (updated by CAL commands) ---
float ppr_t        = DEFAULT_PPR_ROTARY;
float ppr_p        = DEFAULT_PPR_ROTARY;
float ppr_w        = DEFAULT_PPR_WIRE;
float deg_per_t    = 360.0f / DEFAULT_PPR_ROTARY;
float deg_per_p    = 360.0f / DEFAULT_PPR_ROTARY;
float mm_per_pulse = DRUM_CIRCUM_MM / DEFAULT_PPR_WIRE;

Encoder* thetaEnc;
Encoder* phiEnc;
Encoder* wireEnc;

// ---------------------------------------------------------------------------
// Interactive calibration state
// ---------------------------------------------------------------------------
enum CalState { CAL_IDLE, CAL_T_ACTIVE, CAL_P_ACTIVE };
CalState  cal_state    = CAL_IDLE;
int32_t   cal_deltas[MAX_CAL_TURNS];
int       cal_turn_num = 0;
int32_t   cal_last     = 0;   // encoder count at last SPACE press

static Encoder* calEncoder() {
    return (cal_state == CAL_T_ACTIVE) ? thetaEnc : phiEnc;
}

static void startCal(CalState state) {
    cal_state    = state;
    cal_turn_num = 0;
    cal_last     = 0;
    calEncoder()->write(0);
    const char* axis = (state == CAL_T_ACTIVE) ? "THETA" : "PHI";
    Serial.println();
    Serial.print("--- Interactive "); Serial.print(axis); Serial.println(" calibration ---");
    Serial.println("  Rotate one full turn, then press SPACE.");
    Serial.println("  Repeat for each turn (up to 20).");
    Serial.println("  Send DONE to finalize, CANCEL to abort.");
    Serial.println("  (Periodic output suppressed during calibration)");
    Serial.println();
}

static void recordTurn() {
    if (cal_turn_num >= MAX_CAL_TURNS) {
        Serial.println("  Max turns (20) reached — send DONE to finalize.");
        return;
    }
    int32_t current = calEncoder()->read();
    int32_t delta   = abs(current - cal_last);
    cal_last        = current;
    cal_turn_num++;
    cal_deltas[cal_turn_num - 1] = delta;

    Serial.print("  Turn "); Serial.print(cal_turn_num);
    Serial.print(": "); Serial.print(delta); Serial.print(" counts");
    if (cal_turn_num > 1) {
        // running average so far
        int32_t sum = 0;
        for (int i = 0; i < cal_turn_num; i++) sum += cal_deltas[i];
        float avg = (float)sum / cal_turn_num;
        Serial.print("  (avg so far: "); Serial.print(avg, 1); Serial.print(")");
    }
    Serial.println();
}

static void finalizeCal() {
    if (cal_turn_num == 0) {
        Serial.println("ERR: No turns recorded. Press SPACE at each full turn first.");
        return;
    }

    float sum = 0;
    for (int i = 0; i < cal_turn_num; i++) sum += (float)cal_deltas[i];
    float avg_ppr = sum / cal_turn_num;
    float avg_dpp = 360.0f / avg_ppr;
    const char* axis = (cal_state == CAL_T_ACTIVE) ? "T" : "P";

    Serial.println();
    Serial.print("=== CAL_"); Serial.print(axis); Serial.println(" RESULT ===");
    Serial.print("  Turns recorded : "); Serial.println(cal_turn_num);
    Serial.println("  Per-turn counts:");
    for (int i = 0; i < cal_turn_num; i++) {
        Serial.print("    Turn "); Serial.print(i + 1);
        Serial.print(": "); Serial.print(cal_deltas[i]); Serial.println(" counts");
    }
    Serial.print("  Average PPR    : "); Serial.println(avg_ppr, 2);
    Serial.print("  deg/pulse      : "); Serial.println(avg_dpp, 6);
    Serial.println("  Live values updated. To make permanent: update firmware constants.");
    Serial.println("==========================");
    Serial.println();

    if (cal_state == CAL_T_ACTIVE) {
        ppr_t     = avg_ppr;
        deg_per_t = avg_dpp;
        thetaEnc->write(0);
    } else {
        ppr_p     = avg_ppr;
        deg_per_p = avg_dpp;
        phiEnc->write(0);
    }
    cal_state    = CAL_IDLE;
    cal_turn_num = 0;
}

static void cancelCal() {
    const char* axis = (cal_state == CAL_T_ACTIVE) ? "THETA" : "PHI";
    Serial.print("Calibration "); Serial.print(axis); Serial.println(" cancelled. Values unchanged.");
    cal_state    = CAL_IDLE;
    cal_turn_num = 0;
}

// ---------------------------------------------------------------------------
// Calibration helper — wire (distance, non-interactive)
// ---------------------------------------------------------------------------
static void calWire(float actual_mm) {
    if (actual_mm <= 0.0f) {
        Serial.println("ERR: CAL_W requires a positive distance in mm. Example: CAL_W 500");
        return;
    }
    int32_t raw_count = -wireEnc->read();
    if (raw_count == 0) {
        Serial.println("ERR: Count is 0. Send ZERO_W, pull wire, then CAL_W <mm>.");
        return;
    }
    float measured_mm      = (float)raw_count * mm_per_pulse;
    float correction       = actual_mm / measured_mm;
    float new_mm_per_pulse = mm_per_pulse * correction;
    float new_ppr_wire     = DRUM_CIRCUM_MM / new_mm_per_pulse;

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
    ppr_w        = new_ppr_wire;
    wireEnc->write(0);
}

// ---------------------------------------------------------------------------
// GPIO diagnostic
// ---------------------------------------------------------------------------
static void runDiagnostic() {
    Serial.println();
    Serial.println("=== GPIO DIAGNOSTIC (all 6 encoder pins) ===");

    const int    pins[]  = {PIN_THETA_A, PIN_THETA_B, PIN_PHI_A, PIN_PHI_B, PIN_WIRE_A, PIN_WIRE_B};
    const char* names[]  = {"THETA_A(14)", "THETA_B(12)", "PHI_A(32)", "PHI_B(35)", "WIRE_A(16)", "WIRE_B(17)"};

    for (int i = 0; i < 6; i++) {
        Serial.print("  "); Serial.print(names[i]);
        Serial.print(" = "); Serial.println(digitalRead(pins[i]));
    }

    Serial.println("  Sampling for 1 second — move all encoders now...");
    uint32_t trans[6] = {0};
    uint8_t  prev[6];
    for (int i = 0; i < 6; i++) prev[i] = digitalRead(pins[i]);

    unsigned long t0 = millis();
    while (millis() - t0 < 1000) {
        for (int i = 0; i < 6; i++) {
            uint8_t v = digitalRead(pins[i]);
            if (v != prev[i]) { trans[i]++; prev[i] = v; }
        }
    }

    Serial.println("  Transitions:");
    for (int i = 0; i < 6; i++) {
        Serial.print("    "); Serial.print(names[i]);
        Serial.print(" = "); Serial.println(trans[i]);
    }

    auto check = [](const char* axis, uint32_t a, uint32_t b) {
        Serial.print("  "); Serial.print(axis); Serial.print(": ");
        if (a == 0 && b == 0)     Serial.println("NO SIGNAL — check power and voltage dividers");
        else if (a > 0 && b == 0) Serial.println("B stuck — check B wire/divider");
        else if (b > 0 && a == 0) Serial.println("A stuck — check A wire/divider");
        else                      Serial.println("Quadrature OK");
    };
    check("Theta", trans[0], trans[1]);
    check("Phi",   trans[2], trans[3]);
    check("Wire",  trans[4], trans[5]);

    Serial.println("=============================================");
    Serial.println();
}

// ---------------------------------------------------------------------------
// Print current calibration constants
// ---------------------------------------------------------------------------
static void printConstants() {
    Serial.println();
    Serial.println("=== CALIBRATION CONSTANTS ===");
    Serial.print("  ppr_theta    : "); Serial.println(ppr_t, 2);
    Serial.print("  ppr_phi      : "); Serial.println(ppr_p, 2);
    Serial.print("  ppr_wire     : "); Serial.println(ppr_w, 2);
    Serial.print("  deg_per_T    : "); Serial.println(deg_per_t, 6);
    Serial.print("  deg_per_P    : "); Serial.println(deg_per_p, 6);
    Serial.print("  mm_per_pulse : "); Serial.println(mm_per_pulse, 6);
    Serial.println("  Defaults: PPR_ROTARY=20000  PPR_WIRE=8020  MM_PER_PULSE=0.02494");
    Serial.println("==============================");
    Serial.println();
}

// ---------------------------------------------------------------------------
// Print live STATUS
// ---------------------------------------------------------------------------
static void printStatus() {
    int32_t tc = thetaEnc->read();
    int32_t pc = phiEnc->read();
    int32_t wc = -wireEnc->read();

    Serial.println();
    Serial.println("=== STATUS ===");
    Serial.print("  Theta : "); Serial.print(tc);
    Serial.print(" counts  -> "); Serial.print((float)tc * deg_per_t, 3); Serial.println(" deg");
    Serial.print("  Phi   : "); Serial.print(pc);
    Serial.print(" counts  -> "); Serial.print((float)pc * deg_per_p, 3); Serial.println(" deg");
    Serial.print("  Wire  : "); Serial.print(wc);
    Serial.print(" counts  -> "); Serial.print((float)wc * mm_per_pulse, 2); Serial.println(" mm");
    Serial.println("==============");
    Serial.println();
}

// ---------------------------------------------------------------------------
// Serial command handler (full-line commands)
// ---------------------------------------------------------------------------
static void processCommand(const String& cmd) {
    // DONE / CANCEL are only valid during interactive cal
    if (cmd == "DONE") {
        if (cal_state == CAL_IDLE) { Serial.println("ERR: No active calibration."); return; }
        finalizeCal();
        return;
    }
    if (cmd == "CANCEL") {
        if (cal_state == CAL_IDLE) { Serial.println("ERR: No active calibration."); return; }
        cancelCal();
        return;
    }

    // If a cal session is active, only allow DONE/CANCEL/STATUS
    if (cal_state != CAL_IDLE) {
        if (cmd == "STATUS") { printStatus(); return; }
        Serial.println("  Active calibration in progress. Send DONE or CANCEL first.");
        return;
    }

    if (cmd == "ZERO") {
        thetaEnc->write(0); phiEnc->write(0); wireEnc->write(0);
        Serial.println("ACK:ZERO — all encoders reset");
    } else if (cmd == "ZERO_T") {
        thetaEnc->write(0);
        Serial.println("ACK:ZERO_T");
    } else if (cmd == "ZERO_P") {
        phiEnc->write(0);
        Serial.println("ACK:ZERO_P");
    } else if (cmd == "ZERO_W") {
        wireEnc->write(0);
        Serial.println("ACK:ZERO_W");
    } else if (cmd == "CAL_T") {
        startCal(CAL_T_ACTIVE);
    } else if (cmd == "CAL_P") {
        startCal(CAL_P_ACTIVE);
    } else if (cmd.startsWith("CAL_W ")) {
        calWire(cmd.substring(6).toFloat());
    } else if (cmd == "STATUS") {
        printStatus();
    } else if (cmd == "CONSTANTS") {
        printConstants();
    } else if (cmd == "DIAG") {
        runDiagnostic();
    } else {
        Serial.print("Unknown command: "); Serial.println(cmd);
        Serial.println("  Commands: ZERO[_T/_P/_W]");
        Serial.println("            CAL_T | CAL_P | CAL_W <mm>");
        Serial.println("            STATUS | CONSTANTS | DIAG");
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
    Serial.println("=====================================================");
    Serial.println("  CalibrationTest — ESP32 / All 3 Encoders");
    Serial.println("=====================================================");
    Serial.println("  Theta: GPIO 32/35  |  Phi: GPIO 14/12  |  Wire: GPIO 16/17");
    Serial.print  ("  PPR_ROTARY=");   Serial.print(ppr_t, 0);
    Serial.print  ("  PPR_WIRE=");     Serial.print(ppr_w, 0);
    Serial.print  ("  MM_PER_PULSE="); Serial.println(mm_per_pulse, 4);
    Serial.println();
    Serial.println("  Rotary cal : CAL_T or CAL_P -> SPACE each full turn -> DONE");
    Serial.println("  Wire cal   : ZERO_W -> pull known mm -> CAL_W <mm>");
    Serial.println("  Other      : STATUS | CONSTANTS | DIAG | CANCEL");
    Serial.println("=====================================================");
    runDiagnostic();
}

// ---------------------------------------------------------------------------
void loop() {
    static unsigned long last_print = 0;
    static String        serial_buf;

    while (Serial.available()) {
        char c = (char)Serial.read();

        // SPACE triggers a turn mark immediately — no newline needed
        if (c == ' ' && cal_state != CAL_IDLE) {
            recordTurn();
            continue;
        }

        if (c == '\n' || c == '\r') {
            serial_buf.trim();
            if (serial_buf.length() > 0) processCommand(serial_buf);
            serial_buf = "";
        } else {
            serial_buf += c;
        }
    }

    // Suppress periodic output during active calibration to keep turns readable
    if (cal_state != CAL_IDLE) return;

    if (millis() - last_print >= 200) {
        last_print = millis();

        int32_t tc = thetaEnc->read();
        int32_t pc = phiEnc->read();
        int32_t wc = -wireEnc->read();

        Serial.print("T="); Serial.print(tc);
        Serial.print(" ("); Serial.print((float)tc * deg_per_t, 3); Serial.print(" deg)  ");
        Serial.print("P="); Serial.print(pc);
        Serial.print(" ("); Serial.print((float)pc * deg_per_p, 3); Serial.print(" deg)  ");
        Serial.print("W="); Serial.print(wc);
        Serial.print(" ("); Serial.print((float)wc * mm_per_pulse, 2); Serial.println(" mm)");
    }
}
