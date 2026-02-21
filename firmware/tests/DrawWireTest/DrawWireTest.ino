// DrawWireTest.ino
// Phase 1 validation: OPKON DWE3000 draw-wire encoder — quadrature A/B + Z index
//
// Target: Wemos D1 R32 (ESP32-WROOM-32)
//
// ⚠️  VOLTAGE WARNING: DWE3000 outputs swing 0–5 V.
//     ESP32 GPIO max is 3.3 V.  Use a 10 kΩ / 20 kΩ voltage divider
//     (or 74AHCT125 buffer) on every encoder line before the ESP32.
//
// Wiring (safe GPIOs — avoids flash-reserved GPIO 6–11):
//   PIN_WIRE_A (16) — Quadrature A output
//   PIN_WIRE_B (17) — Quadrature B output
//   PIN_WIRE_Z (18) — Index / Z channel (1 pulse per revolution = every 200 mm)
//
// Encoder specs (OPKON DWE3000 HLD P2000 Z V3):
//   PPR  = 2000 pulses / revolution
//   Drum = 200 mm / revolution
//   → MM_PER_PULSE = 0.1 mm / pulse
//
// Expected behaviour:
//   Pulling wire out  → COUNT increases
//   Pushing wire back → COUNT decreases
//   Pull 200 mm → COUNT ≈ +2000, DIST_mm ≈ 200.0, Z_ticks increments by 1
//
// Serial: 115200 baud, output every 200 ms
// Format: COUNT=<n>  DIST_mm=<n * 0.1>  Z_ticks=<z_count>

#include <Arduino.h>
#include <Encoder.h>

#define PIN_WIRE_A   16      // Quadrature A (safe on ESP32-WROOM-32)
#define PIN_WIRE_B   17      // Quadrature B
#define PIN_WIRE_Z   18      // Index channel (1 pulse per 200 mm)

#define PPR_WIRE        2000.0
#define DRUM_CIRCUM_MM   200.0
#define MM_PER_PULSE    (DRUM_CIRCUM_MM / PPR_WIRE)   // = 0.1 mm/pulse

Encoder wireEnc(PIN_WIRE_A, PIN_WIRE_B);

volatile uint32_t z_count = 0;

// IRAM_ATTR keeps the ISR in fast IRAM on ESP32
void IRAM_ATTR zISR() {
    z_count++;
}

void setup() {
    Serial.begin(115200);
    // Non-blocking wait for USB-CDC serial; give up after 3 s
    unsigned long t0 = millis();
    while (!Serial && millis() - t0 < 3000) {}

    pinMode(PIN_WIRE_Z, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_WIRE_Z), zISR, RISING);

    Serial.println("DrawWireTest ready. (ESP32 / OPKON DWE3000 quadrature)");
    Serial.println("Pull wire to increase count, push to decrease.");
    Serial.println("200 mm pull -> COUNT ~2000, Z_ticks +1");
    Serial.println("--------------------------------------------");
}

void loop() {
    static unsigned long last_print = 0;

    if (millis() - last_print >= 200) {
        last_print = millis();

        int32_t count = wireEnc.read();

        noInterrupts();
        uint32_t z = z_count;
        interrupts();

        float dist_mm = (float)count * MM_PER_PULSE;

        Serial.print("COUNT=");
        Serial.print(count);
        Serial.print("  DIST_mm=");
        Serial.print(dist_mm, 1);
        Serial.print("  Z_ticks=");
        Serial.println(z);
    }
}
