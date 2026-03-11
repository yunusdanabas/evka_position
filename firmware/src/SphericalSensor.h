#ifndef SPHERICAL_SENSOR_H
#define SPHERICAL_SENSOR_H

#include <Arduino.h>
#include <Encoder.h>
#include <math.h>
#include <stdint.h>

// ============================================================================
// CONFIGURATION SECTION
// ============================================================================

// Pin Definitions (must be interrupt-capable pins)
#define PIN_THETA_A   14    // Encoder interrupt pin (Theta azimuth axis)
#define PIN_THETA_B   12    // Encoder complementary pin (strapping pin — add pull-down)
#define PIN_PHI_A     32    // GPIO 32 — interrupt-capable, ADC1_CH4
#define PIN_PHI_B     35    // GPIO 35 — input-only, interrupt-capable, ADC1_CH7
#define PIN_WIRE_A    16    // Draw-wire encoder quadrature A
#define PIN_WIRE_B    17    // Draw-wire encoder quadrature B

// Optional features
#define ENABLE_BATTERY_MONITOR 0  // 0: disable battery ADC path (prototype on 5V adapter)

// Battery monitoring (ADC via 100k+100k voltage divider)
#define PIN_BATTERY_ADC  36   // GPIO 36 (ADC1_CH0, input-only)
#define BATT_DIVIDER_RATIO 2.0  // 100k/(100k+100k) → multiply ADC voltage by 2
#define BATT_FULL_V    4.2    // LiPo full charge voltage
#define BATT_EMPTY_V   3.0    // LiPo empty voltage (safe cutoff)
#define BATT_LOW_THRESHOLD 15 // Battery low warning (percent)

// Encoder Specifications
#define PPR_ROTARY      1480.0  // Measured counts/rev (Autonics E40S6)
#define PPR_WIRE        2000.0  // Pulses per revolution — OPKON DWE3000
#define DRUM_CIRCUM_MM   200.0  // Drum circumference in mm (200 mm/rev)
#define DEG_PER_PULSE  (360.0 / PPR_ROTARY)          // ≈ 0.2432 deg per pulse
#define MM_PER_PULSE   (DRUM_CIRCUM_MM / PPR_WIRE)   // = 0.1 mm per pulse

// Mechanical Limits (safety constraints)
#define THETA_MIN_DEG    -180.0   // Min azimuth angle
#define THETA_MAX_DEG     180.0   // Max azimuth angle
#define PHI_MIN_DEG        0.0    // Min elevation angle (straight up)
#define PHI_MAX_DEG      180.0    // Max elevation angle (straight down)
#define RADIUS_MIN_MM    100.0    // Min extension (safety margin)
#define RADIUS_MAX_MM   3000.0    // Max extension — DWE3000 stroke limit

// ============================================================================
// DATA STRUCTURES
// ============================================================================

/**
 * Spherical coordinates (r, theta, phi)
 */
struct SphericalCoords {
    float r_mm;        ///< Radius in millimeters
    float theta_deg;   ///< Azimuth angle in degrees (-180 to 180)
    float phi_deg;     ///< Elevation angle in degrees (0 to 180)
};

/**
 * Cartesian coordinates (X, Y, Z)
 */
struct CartesianCoords {
    float x_mm;  ///< X coordinate in millimeters
    float y_mm;  ///< Y coordinate in millimeters
    float z_mm;  ///< Z coordinate in millimeters
};

/**
 * System status and diagnostic data
 */
struct SystemStatus {
    CartesianCoords position;      ///< Current 3D position
    SphericalCoords spherical;     ///< Current spherical coordinates
    uint8_t is_valid;              ///< 1 if position is within limits, 0 otherwise
    uint32_t frame_count;          ///< Number of processed frames
    uint32_t last_update_ms;       ///< Timestamp of last update
};

struct BatteryStatus {
    float voltage;       ///< Battery voltage (V)
    uint8_t percentage;  ///< Battery level (0-100%)
    bool is_low;         ///< True if below BATT_LOW_THRESHOLD
};

// ============================================================================
// SENSOR CLASS
// ============================================================================

class SphericalPositioningSensor {
private:
    // Encoder objects (heap-allocated in begin() — ESP32 GPIO ISR service
    // is not ready during global construction)
    Encoder* thetaEncoder;
    Encoder* phiEncoder;
    Encoder* wireEncoder;

    // Calibration offsets
    int32_t theta_offset;
    int32_t phi_offset;
    int32_t radius_offset;
    
    // Filtering parameters
    float position_filter_alpha;
    
    // System state
    SystemStatus system_state;

    // Internal Helpers
    SphericalCoords countsToSpherical(int32_t theta_counts, int32_t phi_counts, int32_t radius_counts);
    uint8_t validateLimits(const SphericalCoords& sph, const CartesianCoords& cart);

public:
    SphericalPositioningSensor();
    
    void begin();
    void setZeroPoint();
    void updatePosition();
    
    void readRawEncoders(int32_t& theta_counts, int32_t& phi_counts, int32_t& radius_counts);

    CartesianCoords getPosition();
    SphericalCoords getSphericalCoords();
    SystemStatus getStatus();
    BatteryStatus readBattery();

    void printPosition();
    
    // Math Helpers (Static)
    static CartesianCoords sphericalToCartesian(const SphericalCoords& spherical);
    static SphericalCoords cartesianToSpherical(const CartesianCoords& cartesian);
    static float normalizeAngle(float angle_deg);
    static float clamp(float value, float min_val, float max_val);
};

#endif // SPHERICAL_SENSOR_H
