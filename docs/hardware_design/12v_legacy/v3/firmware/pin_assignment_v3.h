/**
 * @file pin_assignment_v3.h
 * @brief Core GPIO pin definitions for EVKA Position V3 hardware
 * @details ESP32-S3-DevKitC-1 carrier with simple 12V power and 3 encoder inputs
 * @version 3.0.0-docs
 * @date 2026-04-27
 *
 * Hardware target:
 *   - MCU: ESP32-S3-DevKitC-1 on female headers
 *   - Power: 12V/15V input, internal 3S LiPo backup via Q_BATT (IRF4905) active load-sharing
 *   - Charging: V3-A external only; V3-B CN3722 onboard; V3-C XL4016 CC/CV onboard
 *   - Encoders: 2x E40S6 rotary + 1x DWEM2 draw-wire
 *   - Scope: core-only, no RS-485/I2C/watchdog by default
 *
 * This file is documentation support for future firmware migration.
 * The active firmware still targets Wemos D1 R32 until explicitly migrated.
 */

#ifndef PIN_ASSIGNMENT_V3_H
#define PIN_ASSIGNMENT_V3_H

// =============================================================================
// Encoder inputs
// =============================================================================

#define PIN_THETA_A        4
#define PIN_THETA_B        5

#define PIN_PHI_A          6
#define PIN_PHI_B          7

#define PIN_WIRE_A         15
#define PIN_WIRE_B         16
#define PIN_WIRE_Z         17

// =============================================================================
// Analog input
// =============================================================================

// 120k/27k divider from BUCK_VIN or V12_PROT.
// Scale factor: (120k + 27k) / 27k = 5.444444...
#define PIN_BATTERY_ADC    1
#define BATT_DIVIDER_RATIO_V3  (147.0f / 27.0f)

// =============================================================================
// Minimal LEDs
// =============================================================================

// Power LED is hardwired from 5V_RAIL and has no GPIO.
#define PIN_WIFI_LED       8

// GPIO9 and GPIO10 are intentionally unused in the V3 core board unless optional
// activity/fault LEDs are added later.

// =============================================================================
// Pins intentionally not used by the V3 core board
// =============================================================================

#define PIN_V3_UNUSED_I2C_SDA     11
#define PIN_V3_UNUSED_I2C_SCL     12
#define PIN_V3_UNUSED_RS485_TX    13
#define PIN_V3_UNUSED_RS485_RX    14
#define PIN_V3_UNUSED_RS485_DE    18

// =============================================================================
// Compile-time checks
// =============================================================================

#if (PIN_THETA_A == PIN_THETA_B) || (PIN_PHI_A == PIN_PHI_B) || (PIN_WIRE_A == PIN_WIRE_B)
#error "Encoder A and B pins must be different"
#endif

#if (PIN_BATTERY_ADC == PIN_THETA_A) || (PIN_BATTERY_ADC == PIN_THETA_B) || \
    (PIN_BATTERY_ADC == PIN_PHI_A) || (PIN_BATTERY_ADC == PIN_PHI_B) || \
    (PIN_BATTERY_ADC == PIN_WIRE_A) || (PIN_BATTERY_ADC == PIN_WIRE_B)
#error "Battery ADC pin conflicts with an encoder pin"
#endif

#endif  // PIN_ASSIGNMENT_V3_H
