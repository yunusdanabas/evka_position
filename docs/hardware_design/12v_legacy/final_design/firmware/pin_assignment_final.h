#pragma once

// EVKA Position final hardware pin assignment
// Target board: ESP32-S3-DevKitC-1, final 12V external-charge-only carrier
// This header is documentation support for the future ESP32-S3 firmware migration.

// Encoder inputs
#define EVKA_FINAL_PIN_THETA_A 4
#define EVKA_FINAL_PIN_THETA_B 5
#define EVKA_FINAL_PIN_PHI_A 6
#define EVKA_FINAL_PIN_PHI_B 7
#define EVKA_FINAL_PIN_WIRE_A 15
#define EVKA_FINAL_PIN_WIRE_B 16
#define EVKA_FINAL_PIN_WIRE_Z 17

// Supply monitor
#define EVKA_FINAL_PIN_SUPPLY_ADC 1
#define EVKA_FINAL_SUPPLY_ADC_CHANNEL 0

// Optional user indicators
#define EVKA_FINAL_PIN_LED_WIFI 8

// ADC divider: BUCK_VIN -> 120k -> ADC node -> 27k -> GND
#define EVKA_FINAL_SUPPLY_ADC_R_TOP_OHM 120000.0f
#define EVKA_FINAL_SUPPLY_ADC_R_BOT_OHM 27000.0f
#define EVKA_FINAL_SUPPLY_ADC_RATIO 5.444444f

// 3S LiPo thresholds for final hardware
#define EVKA_FINAL_BATT_FULL_V 12.60f
#define EVKA_FINAL_BATT_LOW_WARN_V 10.50f
#define EVKA_FINAL_BATT_SHUTDOWN_V 9.90f
#define EVKA_FINAL_BATT_ABSOLUTE_MIN_V 9.00f

// Encoder constants retained from current project configuration
#define EVKA_FINAL_PPR_ROTARY 20000.0f
#define EVKA_FINAL_PPR_WIRE 8000.0f

// Pins intentionally unused on final core board:
// GPIO 0: boot strap
// GPIO 3: strapping / JTAG related
// GPIO 9,10: reserved for future LED/watchdog daughterboard
// GPIO 11,12: reserved for future I2C daughterboard
// GPIO 13,14,18: reserved for future RS-485 daughterboard
// GPIO 19,20: native USB
// GPIO 21,38,39,40: reserved for future expansion
// GPIO 26-37: flash/PSRAM risk area on many ESP32-S3 modules
// GPIO 45,46: strapping/internal-use risk
