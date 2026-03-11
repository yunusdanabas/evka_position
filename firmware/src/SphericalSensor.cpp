#include "SphericalSensor.h"

// Constructor
SphericalPositioningSensor::SphericalPositioningSensor()
    : thetaEncoder(nullptr),
      phiEncoder(nullptr),
      wireEncoder(nullptr),
      theta_offset(0),
      phi_offset(0),
      radius_offset(0),
      position_filter_alpha(0.2)
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
    Serial.println("[SphericalSensor] Initialized");
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
}

void SphericalPositioningSensor::readRawEncoders(int32_t& theta_counts, int32_t& phi_counts, int32_t& radius_counts) {
    theta_counts = thetaEncoder->read() - theta_offset;
    phi_counts   = phiEncoder->read() - phi_offset;
    radius_counts = wireEncoder->read() - radius_offset;
}

SphericalCoords SphericalPositioningSensor::countsToSpherical(int32_t theta_counts, int32_t phi_counts, int32_t radius_counts) {
    SphericalCoords sph;
    
    sph.theta_deg = theta_counts * DEG_PER_PULSE;
    sph.phi_deg   = phi_counts * DEG_PER_PULSE;
    sph.r_mm      = radius_counts * MM_PER_PULSE;
    
    sph.theta_deg = normalizeAngle(sph.theta_deg);
    sph.phi_deg   = clamp(sph.phi_deg, PHI_MIN_DEG, PHI_MAX_DEG);
    sph.r_mm      = clamp(sph.r_mm, RADIUS_MIN_MM, RADIUS_MAX_MM);
    
    return sph;
}

CartesianCoords SphericalPositioningSensor::sphericalToCartesian(const SphericalCoords& spherical) {
    float theta_rad = spherical.theta_deg * M_PI / 180.0;
    float phi_rad   = spherical.phi_deg * M_PI / 180.0;
    
    float sin_phi = sin(phi_rad);
    float cos_phi = cos(phi_rad);
    float sin_theta = sin(theta_rad);
    float cos_theta = cos(theta_rad);
    
    CartesianCoords cart;
    cart.x_mm = spherical.r_mm * sin_phi * cos_theta;
    cart.y_mm = spherical.r_mm * sin_phi * sin_theta;
    cart.z_mm = spherical.r_mm * cos_phi;
    
    return cart;
}

SphericalCoords SphericalPositioningSensor::cartesianToSpherical(const CartesianCoords& cartesian) {
    SphericalCoords sph;
    sph.r_mm = sqrt(cartesian.x_mm * cartesian.x_mm +
                    cartesian.y_mm * cartesian.y_mm +
                    cartesian.z_mm * cartesian.z_mm);
    
    sph.theta_deg = atan2(cartesian.y_mm, cartesian.x_mm) * 180.0 / M_PI;
    
    if (sph.r_mm > 0.001) {
        sph.phi_deg = acos(cartesian.z_mm / sph.r_mm) * 180.0 / M_PI;
    } else {
        sph.phi_deg = 0.0;
    }
    
    return sph;
}

float SphericalPositioningSensor::normalizeAngle(float angle_deg) {
    while (angle_deg > 180.0) angle_deg -= 360.0;
    while (angle_deg < -180.0) angle_deg += 360.0;
    return angle_deg;
}

float SphericalPositioningSensor::clamp(float value, float min_val, float max_val) {
    if (value < min_val) return min_val;
    if (value > max_val) return max_val;
    return value;
}

uint8_t SphericalPositioningSensor::validateLimits(const SphericalCoords& sph, const CartesianCoords& cart) {
    if (sph.r_mm < RADIUS_MIN_MM || sph.r_mm > RADIUS_MAX_MM) return 0;
    if (sph.phi_deg < PHI_MIN_DEG || sph.phi_deg > PHI_MAX_DEG) return 0;
    
    if (isnan(cart.x_mm) || isnan(cart.y_mm) || isnan(cart.z_mm)) return 0;
    if (isinf(cart.x_mm) || isinf(cart.y_mm) || isinf(cart.z_mm)) return 0;
    
    return 1;
}

void SphericalPositioningSensor::updatePosition() {
    int32_t theta_raw, phi_raw, radius_raw;
    readRawEncoders(theta_raw, phi_raw, radius_raw);
    
    SphericalCoords sph = countsToSpherical(theta_raw, phi_raw, radius_raw);
    CartesianCoords cart = sphericalToCartesian(sph);
    
    // Low-pass filter
    if (system_state.frame_count > 0) {
        cart.x_mm = position_filter_alpha * cart.x_mm + (1.0 - position_filter_alpha) * system_state.position.x_mm;
        cart.y_mm = position_filter_alpha * cart.y_mm + (1.0 - position_filter_alpha) * system_state.position.y_mm;
        cart.z_mm = position_filter_alpha * cart.z_mm + (1.0 - position_filter_alpha) * system_state.position.z_mm;
    }
    
    uint8_t is_valid = validateLimits(sph, cart);
    
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

void SphericalPositioningSensor::printPosition() {
    if (!system_state.is_valid) {
        Serial.println("! INVALID POSITION (out of bounds)");
        return;
    }

    Serial.print("Cartesian: X="); Serial.print(system_state.position.x_mm, 1);
    Serial.print(" Y="); Serial.print(system_state.position.y_mm, 1);
    Serial.print(" Z="); Serial.print(system_state.position.z_mm, 1);
    Serial.print(" mm | Spherical: R="); Serial.print(system_state.spherical.r_mm, 1);
    Serial.print(" mm, Theta="); Serial.print(system_state.spherical.theta_deg, 2);
    Serial.print(" deg, Phi="); Serial.print(system_state.spherical.phi_deg, 2);
    Serial.println(" deg");

    // Machine-readable CSV line for Python parser
    // Format: DATA,<x>,<y>,<z>,<r>,<theta>,<phi>,<is_valid>,<frame_count>,<ts_ms>
    Serial.print("DATA,");
    Serial.print(system_state.position.x_mm, 2);   Serial.print(",");
    Serial.print(system_state.position.y_mm, 2);   Serial.print(",");
    Serial.print(system_state.position.z_mm, 2);   Serial.print(",");
    Serial.print(system_state.spherical.r_mm, 2);  Serial.print(",");
    Serial.print(system_state.spherical.theta_deg, 3); Serial.print(",");
    Serial.print(system_state.spherical.phi_deg, 3);   Serial.print(",");
    Serial.print(system_state.is_valid);           Serial.print(",");
    Serial.print(system_state.frame_count);        Serial.print(",");
    Serial.println(system_state.last_update_ms);
}
