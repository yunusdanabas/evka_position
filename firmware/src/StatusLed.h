#ifndef STATUS_LED_H
#define STATUS_LED_H

#include "SphericalSensor.h"
#include <stdint.h>

struct StatusLedInputs {
    bool wifi_enabled;
    bool sta_configured;
    bool sta_connected;
    bool boot_calibrating;
    bool espnow_fault;
    bool position_valid;
};

class StatusLed {
public:
    void begin();
    void update(const StatusLedInputs& in);
    void flashOverlay(uint8_t r, uint8_t g, uint8_t b, uint32_t ms = 100);
    void flashZeroAck();
    void flashRemoteButton();

private:
    enum class State : uint8_t {
        Off = 0,
        ApOnly,
        WifiConnected,
        WifiReconnecting,
        PositionInvalid,
        Fault,
        BootCalibrating,
    };

    State resolveState(const StatusLedInputs& in) const;
    void computeColor(State state, uint32_t now, uint8_t& r, uint8_t& g, uint8_t& b);
    void applyOutput(uint8_t r, uint8_t g, uint8_t b);
    void updateClassicWifiLed(const StatusLedInputs& in, uint32_t now);

    uint32_t _animMs = 0;
    bool _phase = false;
    uint8_t _lastR = 0;
    uint8_t _lastG = 0;
    uint8_t _lastB = 0;
    uint32_t _overlayUntil = 0;
    uint8_t _overlayR = 0;
    uint8_t _overlayG = 0;
    uint8_t _overlayB = 0;
    bool _initialized = false;
    State _lastState = State::Off;
};

#endif
