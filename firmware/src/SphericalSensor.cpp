#include "SphericalSensor.h"
#include <Preferences.h>

// Constructor
SphericalPositioningSensor::SphericalPositioningSensor()
    : thetaEncoder(nullptr),
      phiEncoder(nullptr),
      wireEncoder(nullptr),
      theta_offset(0),
      phi_offset(0),
      radius_offset(0),
      position_filter_alpha(0.2),
      position_filter_primed(false),
      _ppr_rotary(PPR_ROTARY),
      _ppr_wire(PPR_WIRE)
{
    // Initialize state
    system_state.position = {0.0, 0.0, 0.0};
    system_state.spherical = {0.0, 0.0, 0.0};
    system_state.is_valid = 0;
    system_state.frame_count = 0;
    system_state.last_update_ms = 0;
}

void SphericalPositioningSensor::begin() {
    // Construct Encoders here (not in constructor) — ESP32 GPIO ISR service
    // is not ready during global construction.
    thetaEncoder = new Encoder(PIN_THETA_A, PIN_THETA_B);
    phiEncoder   = new Encoder(PIN_PHI_A, PIN_PHI_B);
    wireEncoder  = new Encoder(PIN_WIRE_A, PIN_WIRE_B);

#if ENABLE_BATTERY_MONITOR
    // Battery ADC pin (input-only, no pull-up)
    pinMode(PIN_BATTERY_ADC, INPUT);
    analogSetAttenuation(ADC_11db);  // Full range 0-3.3V
#endif

    loadPPRFromNVS();
    Serial.println("[SphericalSensor] Initialized");
}

void SphericalPositioningSensor::loadPPRFromNVS() {
    Preferences prefs;
    prefs.begin("evka_cal", true);
    _ppr_rotary = prefs.getFloat("ppr_rotary", PPR_ROTARY);
    _ppr_wire   = prefs.getFloat("ppr_wire",   PPR_WIRE);
    prefs.end();
    if (!isfinite(_ppr_rotary) || _ppr_rotary < 100.0f || _ppr_rotary > 500000.0f) {
        Serial.println("[Cal] NVS: bad PPR_ROTARY, reset to default");
        _ppr_rotary = PPR_ROTARY;
    }
    if (!isfinite(_ppr_wire) || _ppr_wire < 100.0f || _ppr_wire > 500000.0f) {
        Serial.println("[Cal] NVS: bad PPR_WIRE, reset to default");
        _ppr_wire = PPR_WIRE;
    }
    Serial.printf("[Cal] NVS load: PPR_R=%.2f PPR_W=%.2f\n", _ppr_rotary, _ppr_wire);
}

void SphericalPositioningSensor::savePPRToNVS() {
    Preferences prefs;
    prefs.begin("evka_cal", false);
    prefs.putFloat("ppr_rotary", _ppr_rotary);
    prefs.putFloat("ppr_wire",   _ppr_wire);
    prefs.end();
    Serial.printf("[Cal] NVS save: PPR_R=%.2f PPR_W=%.2f\n", _ppr_rotary, _ppr_wire);
}

void SphericalPositioningSensor::setZeroPoint() {
    theta_offset = thetaEncoder->read();
    phi_offset = phiEncoder->read();
    radius_offset = wireEncoder->read();

    Serial.print("[Calibration] Zero point set at T:");
    Serial.print(theta_offset);
    Serial.print(" P:");
    Serial.print(phi_offset);
    Serial.print(" R:");
    Serial.println(radius_offset);
    position_filter_primed = false;
}

void SphericalPositioningSensor::zeroTheta() {
    theta_offset = thetaEncoder->read();
    position_filter_primed = false;
}

void SphericalPositioningSensor::zeroPhi() {
    phi_offset = phiEncoder->read();
    position_filter_primed = false;
}

void SphericalPositioningSensor::zeroWire() {
    radius_offset = wireEncoder->read();
    position_filter_primed = false;
}

void SphericalPositioningSensor::readRawEncoders(int32_t& theta_counts, int32_t& phi_counts, int32_t& radius_counts) {
    theta_counts = thetaEncoder->read() - theta_offset;
    phi_counts   = phiEncoder->read() - phi_offset;
    // Wire encoder counts increase when rope extends — direct mapping
    radius_counts = wireEncoder->read() - radius_offset;
}

SphericalCoords SphericalPositioningSensor::countsToSpherical(int32_t theta_counts, int32_t phi_counts, int32_t radius_counts) {
    SphericalCoords sph;

    const float deg_pp = 360.0f / _ppr_rotary;
    const float mm_pp  = DRUM_CIRCUM_MM / _ppr_wire;

    sph.theta_deg = theta_counts * deg_pp;
    sph.phi_deg   = -phi_counts * deg_pp;  // Phi encoder counts positive when arm drops
    sph.r_mm      = radius_counts * mm_pp;

    sph.theta_deg = normalizeAngle(sph.theta_deg);

    return sph;
}

void SphericalPositioningSensor::setPPRRotary(float ppr) {
    if (ppr > 0) _ppr_rotary = ppr;
}

void SphericalPositioningSensor::setPPRWire(float ppr) {
    if (ppr > 0) _ppr_wire = ppr;
}

void SphericalPositioningSensor::getConstants(char* buf, size_t n) {
    const float mm_pp  = DRUM_CIRCUM_MM / _ppr_wire;
    const float deg_pp = 360.0f / _ppr_rotary;
    snprintf(buf, n, "CONSTANTS,%.2f,%.2f,%.6f,%.6f",
             _ppr_rotary, _ppr_wire, mm_pp, deg_pp);
}

CartesianCoords SphericalPositioningSensor::sphericalToCartesian(const SphericalCoords& spherical) {
    float theta_rad = spherical.theta_deg * ((float)M_PI / 180.0f);
    float phi_rad   = spherical.phi_deg   * ((float)M_PI / 180.0f);

    float sin_phi   = sinf(phi_rad);
    float cos_phi   = cosf(phi_rad);
    float sin_theta = sinf(theta_rad);
    float cos_theta = cosf(theta_rad);

    CartesianCoords cart;
    cart.x_mm = spherical.r_mm * cos_phi * cos_theta;
    cart.y_mm = spherical.r_mm * cos_phi * sin_theta;
    cart.z_mm = spherical.r_mm * sin_phi;

    return cart;
}

SphericalCoords SphericalPositioningSensor::cartesianToSpherical(const CartesianCoords& cartesian) {
    SphericalCoords sph;
    sph.r_mm = sqrtf(cartesian.x_mm * cartesian.x_mm +
                     cartesian.y_mm * cartesian.y_mm +
                     cartesian.z_mm * cartesian.z_mm);
    
    sph.theta_deg = atan2f(cartesian.y_mm, cartesian.x_mm) * (180.0f / (float)M_PI);

    if (sph.r_mm > 0.001f) {
        float ratio = clamp(cartesian.z_mm / sph.r_mm, -1.0f, 1.0f);
        sph.phi_deg = asinf(ratio) * (180.0f / (float)M_PI);
    } else {
        sph.phi_deg = 0.0f;
    }
    
    return sph;
}

float SphericalPositioningSensor::normalizeAngle(float angle_deg) {
    // O(1) — fmodf handles any magnitude without looping
    float a = fmodf(angle_deg, 360.0f);
    if (a > 180.0f)  a -= 360.0f;
    if (a < -180.0f) a += 360.0f;
    return a;
}

float SphericalPositioningSensor::clamp(float value, float min_val, float max_val) {
    if (value < min_val) return min_val;
    if (value > max_val) return max_val;
    return value;
}

uint8_t SphericalPositioningSensor::validateLimits(const SphericalCoords& sph, const CartesianCoords& cart) {
    // Reject NaN/Inf in spherical coords first (e.g. from zero-PPR NVS corruption)
    if (isnan(sph.r_mm) || isnan(sph.theta_deg) || isnan(sph.phi_deg)) return 0;
    if (isinf(sph.r_mm) || isinf(sph.theta_deg) || isinf(sph.phi_deg)) return 0;

    // Allow small startup/zero jitter so near-home noise does not flip validity.
    const float radius_tol_mm = 2.0f;
    const float angle_tol_deg = 1.0f;
    if (sph.r_mm < (RADIUS_MIN_MM - radius_tol_mm) || sph.r_mm > (RADIUS_MAX_MM + radius_tol_mm)) return 0;
    if (sph.phi_deg < (PHI_MIN_DEG - angle_tol_deg) || sph.phi_deg > (PHI_MAX_DEG + angle_tol_deg)) return 0;
    if (sph.theta_deg < (THETA_MIN_DEG - angle_tol_deg) || sph.theta_deg > (THETA_MAX_DEG + angle_tol_deg)) return 0;

    if (isnan(cart.x_mm) || isnan(cart.y_mm) || isnan(cart.z_mm)) return 0;
    if (isinf(cart.x_mm) || isinf(cart.y_mm) || isinf(cart.z_mm)) return 0;

    return 1;
}

void SphericalPositioningSensor::updatePosition() {
    int32_t theta_raw, phi_raw, radius_raw;
    readRawEncoders(theta_raw, phi_raw, radius_raw);

    // Use one consistent state for reporting, validity checks, and Cartesian
    // conversion. Out-of-limit values remain visible to tooling via is_valid=0.
    SphericalCoords sph = countsToSpherical(theta_raw, phi_raw, radius_raw);
    CartesianCoords cart_raw = sphericalToCartesian(sph);
    uint8_t is_valid = validateLimits(sph, cart_raw);

    CartesianCoords cart = cart_raw;
    // Low-pass filter only while valid. Invalid frames bypass EMA and reset
    // filter priming so recovery to home does not drag stale values.
    if (is_valid) {
        if (position_filter_primed) {
            cart.x_mm = position_filter_alpha * cart_raw.x_mm + (1.0f - position_filter_alpha) * system_state.position.x_mm;
            cart.y_mm = position_filter_alpha * cart_raw.y_mm + (1.0f - position_filter_alpha) * system_state.position.y_mm;
            cart.z_mm = position_filter_alpha * cart_raw.z_mm + (1.0f - position_filter_alpha) * system_state.position.z_mm;
        } else {
            position_filter_primed = true;
        }
    } else {
        position_filter_primed = false;
    }
    
    system_state.position = cart;
    system_state.spherical = sph;
    system_state.is_valid = is_valid;
    system_state.frame_count++;
    system_state.last_update_ms = millis();
}

CartesianCoords SphericalPositioningSensor::getPosition() {
    return system_state.position;
}

SphericalCoords SphericalPositioningSensor::getSphericalCoords() {
    return system_state.spherical;
}

SystemStatus SphericalPositioningSensor::getStatus() {
    return system_state;
}

BatteryStatus SphericalPositioningSensor::readBattery() {
    BatteryStatus bat;
#if ENABLE_BATTERY_MONITOR
    int raw = analogRead(PIN_BATTERY_ADC);
    float adc_voltage = (raw / 4095.0f) * 3.3f;
    bat.voltage = adc_voltage * BATT_DIVIDER_RATIO;

    // Linear mapping: 3.0V = 0%, 4.2V = 100%
    float pct = (bat.voltage - BATT_EMPTY_V) / (BATT_FULL_V - BATT_EMPTY_V) * 100.0f;
    if (pct < 0.0f) pct = 0.0f;
    if (pct > 100.0f) pct = 100.0f;
    bat.percentage = (uint8_t)pct;
    bat.is_low = (bat.percentage < BATT_LOW_THRESHOLD);
#else
    bat.voltage = 0.0f;
    bat.percentage = 0;
    bat.is_low = false;
#endif
    return bat;
}

void SphericalPositioningSensor::printPosition() {
    static uint32_t last_invalid_log_ms = 0;
    if (!system_state.is_valid) {
        uint32_t now = millis();
        if ((now - last_invalid_log_ms) >= 1000) {
            last_invalid_log_ms = now;
            Serial.println("! INVALID POSITION (out of bounds)");
        }
    }

    // Human-readable debug line
    char buf[128];
    snprintf(buf, sizeof(buf),
        "X=%.1f Y=%.1f Z=%.1f mm | R=%.1f mm Th=%.2f Ph=%.2f deg",
        system_state.position.x_mm, system_state.position.y_mm, system_state.position.z_mm,
        system_state.spherical.r_mm, system_state.spherical.theta_deg,
        system_state.spherical.phi_deg);
    Serial.println(buf);
    // DATA line (machine-readable) is formatted once in loop() and goes to both
    // serial and WebSocket — no second snprintf needed here.
}
