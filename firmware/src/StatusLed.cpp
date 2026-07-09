#include "StatusLed.h"

#if ENABLE_RGB_STATUS_LED
#include "esp32-hal-rgb-led.h"
#endif

namespace {

bool elapsedMs(uint32_t now, uint32_t since, uint32_t interval) {
    return (int32_t)(now - since) >= (int32_t)interval;
}

#if ENABLE_RGB_STATUS_LED
uint8_t scaleChannel(uint8_t v) {
#ifdef RGB_BRIGHTNESS
    return (uint8_t)((uint16_t)v * RGB_BRIGHTNESS / 255u);
#else
    return v;
#endif
}

uint8_t scaleColor(uint8_t base, uint8_t brightness) {
    return scaleChannel((uint8_t)((uint16_t)base * brightness / 255u));
}

uint8_t breatheBrightness(uint32_t now, uint32_t periodMs) {
    const uint32_t half = periodMs / 2u;
    if (half == 0) {
        return 255;
    }
    const uint32_t t = now % periodMs;
    if (t < half) {
        return (uint8_t)((uint16_t)255u * t / half);
    }
    return (uint8_t)((uint16_t)255u * (periodMs - t) / half);
}
#endif

}  // namespace

void StatusLed::begin() {
#if ENABLE_RGB_STATUS_LED
    applyOutput(255, 255, 255);
    delay(100);
    applyOutput(0, 0, 0);
#else
#if ENABLE_WIFI
    pinMode(PIN_WIFI_LED, OUTPUT);
    digitalWrite(PIN_WIFI_LED, LOW);
#endif
#endif
    _initialized = true;
}

void StatusLed::flashOverlay(uint8_t r, uint8_t g, uint8_t b, uint32_t ms) {
#if ENABLE_RGB_STATUS_LED
    _overlayR = r;
    _overlayG = g;
    _overlayB = b;
    _overlayUntil = millis() + ms;
    applyOutput(r, g, b);
#else
    (void)r;
    (void)g;
    (void)b;
#if ENABLE_WIFI
    _overlayUntil = millis() + ms;
    digitalWrite(PIN_WIFI_LED, HIGH);
#endif
#endif
}

void StatusLed::flashZeroAck() {
    flashOverlay(80, 80, 80, 100);
}

void StatusLed::flashRemoteButton() {
    flashOverlay(120, 0, 180, 100);
}

StatusLed::State StatusLed::resolveState(const StatusLedInputs& in) const {
    if (in.boot_calibrating) {
        return State::BootCalibrating;
    }
    if (in.espnow_fault) {
        return State::Fault;
    }
    if (!in.position_valid) {
        return State::PositionInvalid;
    }
    if (!in.wifi_enabled) {
        return State::Off;
    }
    if (in.sta_configured && !in.sta_connected) {
        return State::WifiReconnecting;
    }
    if (in.sta_configured && in.sta_connected) {
        return State::WifiConnected;
    }
    return State::ApOnly;
}

void StatusLed::computeColor(State state, uint32_t now, uint8_t& r, uint8_t& g, uint8_t& b) {
#if ENABLE_RGB_STATUS_LED
    r = 0;
    g = 0;
    b = 0;

    switch (state) {
        case State::BootCalibrating: {
            const uint8_t br = breatheBrightness(now, 2000);
            r = scaleColor(255, br);
            g = scaleColor(180, br);
            break;
        }
        case State::Fault:
            if (elapsedMs(now, _animMs, 125)) {
                _animMs = now;
                _phase = !_phase;
            }
            if (_phase) {
                r = scaleChannel(255);
                b = scaleChannel(255);
            }
            break;
        case State::PositionInvalid:
            if (elapsedMs(now, _animMs, 500)) {
                _animMs = now;
                _phase = !_phase;
            }
            if (_phase) {
                r = scaleChannel(255);
                g = scaleChannel(80);
            }
            break;
        case State::WifiReconnecting:
            if (elapsedMs(now, _animMs, 500)) {
                _animMs = now;
                _phase = !_phase;
            }
            if (_phase) {
                b = scaleChannel(255);
                g = scaleChannel(80);
            }
            break;
        case State::WifiConnected:
            g = scaleChannel(200);
            break;
        case State::ApOnly:
            g = scaleChannel(180);
            b = scaleChannel(180);
            break;
        case State::Off:
        default:
            break;
    }
#else
    (void)state;
    (void)now;
    r = 0;
    g = 0;
    b = 0;
#endif
}

void StatusLed::applyOutput(uint8_t r, uint8_t g, uint8_t b) {
#if ENABLE_RGB_STATUS_LED
    if (r != _lastR || g != _lastG || b != _lastB) {
        neopixelWrite(PIN_RGB_LED, r, g, b);
        _lastR = r;
        _lastG = g;
        _lastB = b;
    }
#endif
}

void StatusLed::updateClassicWifiLed(const StatusLedInputs& in, uint32_t now) {
#if ENABLE_WIFI && !ENABLE_RGB_STATUS_LED
    if (!in.wifi_enabled) {
        digitalWrite(PIN_WIFI_LED, LOW);
        return;
    }
    if (!in.sta_configured) {
        digitalWrite(PIN_WIFI_LED, LOW);
    } else if (in.sta_connected) {
        digitalWrite(PIN_WIFI_LED, HIGH);
    } else if (elapsedMs(now, _animMs, 500)) {
        _animMs = now;
        _phase = !_phase;
        digitalWrite(PIN_WIFI_LED, _phase ? HIGH : LOW);
    }
#endif
}

void StatusLed::update(const StatusLedInputs& in) {
    if (!_initialized) {
        begin();
    }

    const uint32_t now = millis();

#if ENABLE_RGB_STATUS_LED
    if (_overlayUntil != 0) {
        if ((int32_t)(now - _overlayUntil) < 0) {
            applyOutput(_overlayR, _overlayG, _overlayB);
            return;
        }
        _overlayUntil = 0;
    }

    uint8_t r = 0;
    uint8_t g = 0;
    uint8_t b = 0;
    const State state = resolveState(in);
    if (state != _lastState) {
        _lastState = state;
        _animMs = now;
        _phase = false;
    }
    computeColor(state, now, r, g, b);
    applyOutput(r, g, b);
#else
    if (_overlayUntil != 0) {
        if ((int32_t)(now - _overlayUntil) < 0) {
            digitalWrite(PIN_WIFI_LED, HIGH);
            return;
        }
        _overlayUntil = 0;
    }
    updateClassicWifiLed(in, now);
#endif
}
