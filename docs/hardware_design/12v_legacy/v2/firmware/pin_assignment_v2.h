/**
 * @file pin_assignment_v2.h
 * @brief GPIO pin definitions for EVKA Position V2 hardware
 * @details ESP32-S3-DevKitC-1 on carrier PCB with LPKF S63 compatible layout
 * @version 2.0.0
 * @date 2026-04-23
 * 
 * HARDWARE: EVKA Position V2
 *   - MCU: ESP32-S3-DevKitC-1-N8R2 (8MB flash, 2MB PSRAM, native USB-C)
 *   - Power: 12V input, no onboard charging (external balance charger), MP1584EN buck
 *   - Encoders: 2× E40S6 rotary + 1× DWEM2 draw-wire
 *   - Interfaces: RS-485/Modbus RTU, I2C expansion, 4 spare GPIOs
 *   - Watchdog: MAX813L external supervisor
 * 
 * MIGRATION from V1:
 *   - Changed from ESP32 Wemos D1 R32 to ESP32-S3-DevKitC-1
 *   - Remapped all encoder pins (GPIO 32/35/36 reserved on S3)
 *   - Added RS-485, I2C, watchdog, spare GPIO definitions
 *   - Battery ADC moved from GPIO 36 to GPIO 1 (ADC1_CH0)
 * 
 * USAGE:
 *   Copy this file to firmware/src/pin_assignment.h (or include directly)
 *   Update platformio.ini: board = esp32-s3-devkitc-1
 */

#ifndef PIN_ASSIGNMENT_V2_H
#define PIN_ASSIGNMENT_V2_H

// ENCODER LIBRARY: Use ESP32Encoder (madhephaestus/ESP32Encoder, PCNT-based) for ESP32-S3.
// PaulStoffregen Encoder needs IRAM_ATTR fixes on ESP32-S3 with arduino-esp32 core 2.x.

// =============================================================================
// ENCODER INPUTS
// =============================================================================

/**
 * @brief Theta encoder (azimuth rotation)
 * E40S6-5000 rotary encoder, quadrature A/B output
 * Mounted on base platform
 */
#define PIN_THETA_A     4   ///< Theta channel A (quadrature)
#define PIN_THETA_B     5   ///< Theta channel B (quadrature)

/**
 * @brief Phi encoder (elevation tilt)
 * E40S6-5000 rotary encoder, quadrature A/B output
 * Mounted on arm/tilting mechanism
 */
#define PIN_PHI_A       6   ///< Phi channel A (quadrature)
#define PIN_PHI_B       7   ///< Phi channel B (quadrature)

/**
 * @brief Wire encoder (linear distance)
 * DWEM2-P2000 draw-wire encoder, quadrature A/B + index Z
 * Mounted on sensor housing
 */
#define PIN_WIRE_A      15  ///< Wire channel A (quadrature)
#define PIN_WIRE_B      16  ///< Wire channel B (quadrature)
#define PIN_WIRE_Z      17  ///< Wire index pulse (once per drum revolution)

// =============================================================================
// ANALOG INPUTS
// =============================================================================

/**
 * @brief Battery / 12V supply monitoring
 * Connected to 120k/27k voltage divider from V12_PROT
 * ADC1_CH0 is safe to use when WiFi is active (unlike ADC2)
 * 
 * Scale factor: (120k + 27k) / 27k = 5.444
 * Voltage = ADC_reading * 3.3 / 4095 * 5.444
 */
#define PIN_BATT_ADC    1   ///< Battery/12V ADC input (ADC1_CH0)

// =============================================================================
// STATUS LEDs
// =============================================================================

/**
 * @brief Power indicator LED
 * Hardwired from 5V_RAIL through 1kΩ resistor
 * Always on when board has power
 * 
 * NOTE: GPIO 2 also has onboard LED on DevKitC-1
 */
#define PIN_LED_POWER   2   ///< Power LED (green, also DevKitC-1 onboard LED)

/**
 * @brief WiFi status LED
 * Blue LED indicates WiFi connection state:
 *   - OFF: No WiFi active
 *   - Slow blink (1Hz): AP mode active
 *   - Solid ON: STA connected to router
 */
#define PIN_LED_WIFI    8   ///< WiFi status LED (blue)

/**
 * @brief Activity heartbeat LED
 * Yellow LED blinks briefly every 50ms control loop cycle
 * Useful for verifying firmware is running without serial monitor
 * 
 * NOTE: This pin is also connected to MAX813L WDI (watchdog input)
 * The LED will blink at 20Hz as a brief 100µs pulse — visible as a fast heartbeat.
 */
#define PIN_LED_ACTIVITY 9  ///< Activity LED (yellow), also WDI to MAX813L

/**
 * @brief Fault/alarm LED
 * Red LED indicates error conditions:
 *   - OFF: Normal operation, position valid
 *   - Solid ON: Invalid position, encoder error, or system fault
 */
#define PIN_LED_FAULT   10  ///< Fault LED (red)

// =============================================================================
// COMMUNICATION INTERFACES
// =============================================================================

/**
 * @brief I2C bus for expansion modules
 * SDA/SCL with 4.7kΩ pull-ups to 3.3V
 * Supported modules: DS3231 RTC, ADS1115 ADC, SSD1306 OLED
 */
#define PIN_I2C_SDA     11  ///< I2C data line (SDA)
#define PIN_I2C_SCL     12  ///< I2C clock line (SCL)

/**
 * @brief RS-485 / Modbus RTU interface
 * Half-duplex RS-485 via MAX485 transceiver
 * UART2 mapped to GPIO 13/14 via ESP32-S3 GPIO matrix
 * DE/RE tied together for direction control
 */
#define PIN_RS485_TX    13  ///< RS-485 transmit (DI on MAX485)
#define PIN_RS485_RX    14  ///< RS-485 receive (RO on MAX485)
#define PIN_RS485_DE    18  ///< RS-485 direction control (DE+RE on MAX485)

// =============================================================================
// WATCHDOG
// =============================================================================

/**
 * @brief External watchdog toggle pin
 * Connected to MAX813L WDI (watchdog input)
 * Must toggle every <1.6 seconds or ESP32 will be reset
 * 
 * NOTE: Same pin as PIN_LED_ACTIVITY. The LED current is negligible
 * compared to MAX813L input current.
 */
#define PIN_WDI         9   ///< Watchdog input toggle (shared with LED activity)

// =============================================================================
// SPARE GPIOs
// =============================================================================

/**
 * @brief Spare bidirectional GPIO
 * Available for limit switches, relays, or auxiliary outputs
 * Can be used as input or output
 */
#define PIN_SPARE_1     21  ///< Spare GPIO 1 (bidirectional)

/**
 * @brief Spare input-only GPIOs
 * These pins are input-only on ESP32-S3
 * Ideal for limit switches, home sensors, emergency stop
 */
#define PIN_SPARE_2     38  ///< Spare GPIO 2 (input-only)
#define PIN_SPARE_3     39  ///< Spare GPIO 3 (input-only)
#define PIN_SPARE_4     40  ///< Spare GPIO 4 (input-only)

// =============================================================================
// DEVKITC-1 SPECIAL PINS
// =============================================================================

// ESP32 EN (reset) is a dedicated hardware pin — not addressable as GPIO.
// Controlled by MAX813L RESET output and the manual reset button.
// Do NOT define PIN_ESP_EN as a GPIO number — the EN pin has no GPIO number.

/**
 * @brief USB data pins
 * Native USB-OTG on DevKitC-1
 * Do NOT use for general purpose I/O
 */
#define PIN_USB_DMINUS  19  ///< USB D- (reserved for USB)
#define PIN_USB_DPLUS   20  ///< USB D+ (reserved for USB)

// =============================================================================
// LEGACY ALIASES (for backward compatibility during migration)
// =============================================================================

/** @deprecated Use PIN_THETA_A instead */
#define PIN_ENCODER_THETA_A     PIN_THETA_A
/** @deprecated Use PIN_THETA_B instead */
#define PIN_ENCODER_THETA_B     PIN_THETA_B
/** @deprecated Use PIN_PHI_A instead */
#define PIN_ENCODER_PHI_A       PIN_PHI_A
/** @deprecated Use PIN_PHI_B instead */
#define PIN_ENCODER_PHI_B       PIN_PHI_B
/** @deprecated Use PIN_WIRE_A instead */
#define PIN_ENCODER_WIRE_A      PIN_WIRE_A
/** @deprecated Use PIN_WIRE_B instead */
#define PIN_ENCODER_WIRE_B      PIN_WIRE_B
/** @deprecated Use PIN_WIRE_Z instead */
#define PIN_ENCODER_WIRE_Z      PIN_WIRE_Z

// =============================================================================
// VALIDATION MACROS
// =============================================================================

/**
 * @brief Compile-time pin conflict check
 * Ensures no two functions share the same GPIO
 */
#if (PIN_THETA_A == PIN_THETA_B) || (PIN_PHI_A == PIN_PHI_B) || (PIN_WIRE_A == PIN_WIRE_B)
#error "Encoder A and B pins must be different"
#endif

#if (PIN_LED_ACTIVITY != PIN_WDI)
#error "LED activity and WDI must share the same pin (GPIO 9)"
#endif

#if (PIN_BATT_ADC == 0) || (PIN_BATT_ADC == 3) || (PIN_BATT_ADC == 45) || (PIN_BATT_ADC == 46)
#error "Battery ADC cannot use strapping pins"
#endif

// =============================================================================
// END OF FILE
// =============================================================================

#endif // PIN_ASSIGNMENT_V2_H
