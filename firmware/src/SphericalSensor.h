#ifndef SPHERICAL_SENSOR_H
#define SPHERICAL_SENSOR_H

#include <Arduino.h>
#include <ESP32Encoder.h>
#include <math.h>
#include <stdint.h>

// ============================================================================
// CONFIGURATION SECTION
// ============================================================================

// Pin Definitions — board selected at build time (-DPCB_V4 for the ESP32-S3 v4 PCB)
#if defined(PCB_V4)
// EVKA_position_v4 — ESP32-S3-DevKitC-1. Encoders via on-board 10k/20k dividers
// straight to GPIO (no Schmitt buffer). Verified against the v4 schematic AND PCB
// pad-nets (THETA=DIVIDER_NODE_1/2, PHI=_3/4, WIRE=_5/6). GPIO17/18 are NOT wired.
#define PIN_THETA_A   7     // DIVIDER_NODE_1 (J1.1 theta A)
#define PIN_THETA_B   8     // DIVIDER_NODE_2 (J1.3 theta B)
#define PIN_PHI_A     4     // DIVIDER_NODE_3 (J2.2 phi A)
#define PIN_PHI_B     5     // DIVIDER_NODE_4 (J2.4 phi B)
#define PIN_WIRE_A    9     // DIVIDER_NODE_5 (J3.1 wire A)
#define PIN_WIRE_B    10    // DIVIDER_NODE_6 (J3.3 wire B)
#else
// Classic ESP32 (Wemos D1 R32). Must stay interrupt/PCNT-capable.
#define PIN_THETA_A   14    // Encoder pin (Theta azimuth axis)
#define PIN_THETA_B   12    // Strapping pin — add pull-down
#define PIN_PHI_A     32    // GPIO 32 — ADC1_CH4
#define PIN_PHI_B     35    // GPIO 35 — input-only
#define PIN_WIRE_A    16    // Draw-wire encoder quadrature A
#define PIN_WIRE_B    17    // Draw-wire encoder quadrature B
#endif

// Optional features
#define ENABLE_BATTERY_MONITOR 1  // 1: read 1S LiPo (v4) / battery divider on PIN_BATTERY_ADC

// 0 = 1S LiPo (100k+100k divider). 1 = 12V input PCB (120k+27k from V12_PROT to GPIO36).
#define BATTERY_ADC_12V_INPUT 0
#define ENABLE_WIFI            1  // 0: serial only, 1: serial + WiFi AP + web dashboard
#define ENABLE_CMD_TCP         1  // 0: disable CMD TCP server, 1: enable TCP on CMD_TCP_PORT
#define ENABLE_REMOTE_WIFI_CONFIG 1  // 0: block WIFI_SET/WIFI_AYAR over TCP, 1: allow remote WiFi config + reboot
#define ENABLE_ESPNOW_REMOTE   1  // 0: disable ESP-NOW button remote, 1: enable wireless button pendant
#define ESPNOW_CHANNEL         1  // WiFi channel for ESP-NOW (must match AP channel)
#define WIFI_AP_SSID           "CMDCNC_EVKA"
#define WIFI_AP_PASSWORD       "cmdcnc1234"  // min 8 chars for WPA2
#define WIFI_STA_DEFAULT_SSID  "ASMETAL"   // compile-time default STA network
#define WIFI_STA_DEFAULT_PASS  "AACC223344"
#define WIFI_STA_STATIC_IP_O1  192
#define WIFI_STA_STATIC_IP_O2  168
#define WIFI_STA_STATIC_IP_O3  1
#define WIFI_STA_STATIC_IP_O4  84
#define WIFI_STA_GW_O1         192
#define WIFI_STA_GW_O2         168
#define WIFI_STA_GW_O3         1
#define WIFI_STA_GW_O4         254
#define WIFI_STA_SN_O1         255
#define WIFI_STA_SN_O2         255
#define WIFI_STA_SN_O3         255
#define WIFI_STA_SN_O4         0
#define WIFI_STA_DNS_O1        8
#define WIFI_STA_DNS_O2        8
#define WIFI_STA_DNS_O3        8
#define WIFI_STA_DNS_O4        8
#define WIFI_CFG_VERSION       3               // increment this to reset STA creds on next flash
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

// Battery / supply monitoring (ADC1_CH0). v4: GPIO1 (1S divider); classic: GPIO36.
#if defined(PCB_V4)
#define PIN_BATTERY_ADC  1    // GPIO 1 (ADC1_CH0) — 100k/100k divider on 1S LiPo
#else
#define PIN_BATTERY_ADC  36   // GPIO 36 (ADC1_CH0, input-only)
#endif
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
#define PPR_WIRE        8000.0  // Theoretical — OPKON DWEM2 @ X4 quadrature (0.1 mm/pulse × 4 edges = 0.025 mm/count)
                                 // Calibrate: SET_PPR_WIRE 8000 → SAVE_PPR → ZERO_W → CAL_W <mm> → SET_PPR_WIRE <result> → SAVE_PPR
#define DRUM_CIRCUM_MM   200.0  // Drum circumference in mm (200 mm/rev)
#define DEG_PER_PULSE  (360.0 / PPR_ROTARY)          // ≈ 0.018 deg per pulse
#define MM_PER_PULSE   (DRUM_CIRCUM_MM / PPR_WIRE)   // = 0.025 mm/count (theoretical; NVS overrides after CAL_W)

// Encoder count → angle sign (mounting-dependent; tune at integration)
// Forward motion at home should increase +X (ENCODER_THETA_SIGN); lift should increase +Z (ENCODER_PHI_SIGN).
#define ENCODER_THETA_SIGN  (-1.0f)   // +1 or -1
#define ENCODER_PHI_SIGN    (+1.0f)   // was implicit -1; +1 for current rig (up → +Z)

// Mechanical Limits (safety constraints)
#define THETA_MIN_DEG    -180.0   // Min azimuth angle
#define THETA_MAX_DEG     180.0   // Max azimuth angle
#define PHI_MIN_DEG      -180.0   // Min elevation angle
#define PHI_MAX_DEG       180.0   // Max elevation angle
#define RADIUS_MIN_MM     0.0    // Min extension (home position = 0 mm relative)
#define RADIUS_MAX_MM   2950.0   // Max extension — DWEM2 travel range (4200 - 1250 mm)

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
    // Encoder objects (heap-allocated in begin() — PCNT/ISR service is not
    // ready during global construction)
    ESP32Encoder* thetaEncoder;
    ESP32Encoder* phiEncoder;
    ESP32Encoder* wireEncoder;

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
