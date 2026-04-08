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
#define PIN_THETA_B   12    // Strapping pin — add pull-down
#define PIN_PHI_A     32    // GPIO 32 — interrupt-capable, ADC1_CH4
#define PIN_PHI_B     35    // GPIO 35 — input-only, interrupt-capable
#define PIN_WIRE_A    16    // Draw-wire encoder quadrature A
#define PIN_WIRE_B    17    // Draw-wire encoder quadrature B

// Optional features
#define ENABLE_BATTERY_MONITOR 0  // 0: disable battery ADC path (prototype on 5V adapter)

// 0 = 1S LiPo (100k+100k divider). 1 = 12V input PCB (120k+27k from V12_PROT to GPIO36).
#define BATTERY_ADC_12V_INPUT 0
#define ENABLE_WIFI            1  // 0: serial only, 1: serial + WiFi AP + web dashboard
#define ENABLE_CMD_TCP         1  // 0: disable CMD TCP server, 1: enable TCP on CMD_TCP_PORT
#define ENABLE_REMOTE_WIFI_CONFIG 0  // 0: block WIFI_SET/WIFI_AYAR over TCP, 1: allow remote WiFi config + reboot
#define ENABLE_ESPNOW_REMOTE   0  // 0: disable ESP-NOW button remote, 1: enable wireless button pendant
#define ESPNOW_CHANNEL         1  // WiFi channel for ESP-NOW (must match AP channel)
#define WIFI_AP_SSID           "CMDCNC_EVKA"
#define WIFI_AP_PASSWORD       "cmdcnc1234"  // min 8 chars for WPA2
#define WIFI_STA_DEFAULT_SSID  "CMD-YAZILIM"   // compile-time default STA network
#define WIFI_STA_DEFAULT_PASS  "cmd20165544"
#define WIFI_CFG_VERSION       1               // increment this to reset STA creds on next flash
#define WIFI_WEB_PORT          80
#define CMD_TCP_PORT           8080

// WiFi AP static IP — DO NOT CHANGE: CMD CNC software is hardcoded to 192.168.1.50:8080.
// KNOWN SUBNET CONFLICT: 192.168.1.x collides with most home/office routers.
// If the dashboard is unreachable after connecting to CMDCNC_EVKA, disconnect from
// your home/office WiFi first — the OS may be routing 192.168.1.50 to the home
// router instead of the ESP32.
#define WIFI_AP_IP_O1    192
#define WIFI_AP_IP_O2    168
#define WIFI_AP_IP_O3    1
#define WIFI_AP_IP_O4    50

// WiFi status LED
#define PIN_WIFI_LED     2   // GPIO 2 = built-in LED on most ESP32 boards

// Battery / supply monitoring on GPIO36 (see docs/hardware_design/12v/circuit_schematic_12v.md)
#define PIN_BATTERY_ADC  36   // GPIO 36 (ADC1_CH0, input-only)
#if BATTERY_ADC_12V_INPUT
#define BATT_DIVIDER_RATIO (147.0f / 27.0f)  // (120k+27k)/27k → V12 at divider input
#define BATT_FULL_V    15.0f   // STATUS % mapping: "high" side of 12V adapter window
#define BATT_EMPTY_V   10.8f   // STATUS % mapping: "low" warning (~9V bus class)
#else
#define BATT_DIVIDER_RATIO 2.0f  // 100k/(100k+100k) → multiply ADC voltage by 2
#define BATT_FULL_V    4.2f    // LiPo full charge voltage
#define BATT_EMPTY_V   3.0f    // LiPo empty voltage (safe cutoff)
#endif
#define BATT_LOW_THRESHOLD 15 // Low warning when calculated percentage below this

// Encoder Specifications
#define PPR_ROTARY      20000.0  // E40S6-5000 @ X4 quadrature (5000 PPR × 4)
#define PPR_WIRE        8020.0  // Calibrated — OPKON DWE3000 @ X4 quadrature (actual 400mm → firmware read 1604mm)
#define DRUM_CIRCUM_MM   200.0  // Drum circumference in mm (200 mm/rev)
#define DEG_PER_PULSE  (360.0 / PPR_ROTARY)          // ≈ 0.018 deg per pulse
#define MM_PER_PULSE   (DRUM_CIRCUM_MM / PPR_WIRE)   // ≈ 0.02494 mm per pulse

// Mechanical Limits (safety constraints)
#define THETA_MIN_DEG    -180.0   // Min azimuth angle
#define THETA_MAX_DEG     180.0   // Max azimuth angle
#define PHI_MIN_DEG      -180.0   // Min elevation angle
#define PHI_MAX_DEG       180.0   // Max elevation angle
#define RADIUS_MIN_MM     0.0    // Min extension (home position = 0 mm)
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
    float phi_deg;     ///< Elevation angle from horizontal in degrees (-90=down, 0=horizontal, +90=up)
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
    bool position_filter_primed;

    // Runtime-adjustable calibration values (initialised from compile-time constants)
    float _ppr_rotary;
    float _ppr_wire;

    // System state
    SystemStatus system_state;

    // Internal Helpers
    SphericalCoords countsToSpherical(int32_t theta_counts, int32_t phi_counts, int32_t radius_counts);
    uint8_t validateLimits(const SphericalCoords& sph, const CartesianCoords& cart);

public:
    SphericalPositioningSensor();
    
    void begin();
    void setZeroPoint();
    void zeroTheta();
    void zeroPhi();
    void zeroWire();
    void updatePosition();

    void readRawEncoders(int32_t& theta_counts, int32_t& phi_counts, int32_t& radius_counts);

    // Runtime PPR adjustment (RAM only — update SphericalSensor.h #defines to persist)
    void setPPRRotary(float ppr);
    void setPPRWire(float ppr);
    float getPPRWire() const { return _ppr_wire; }
    float getPPRRotary() const { return _ppr_rotary; }
    void getConstants(char* buf, size_t buf_size);
    void savePPRToNVS();
    void loadPPRFromNVS();

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
