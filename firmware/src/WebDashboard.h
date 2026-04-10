#ifndef WEB_DASHBOARD_H
#define WEB_DASHBOARD_H

#include "SphericalSensor.h"

#if ENABLE_WIFI

#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <freertos/portmacro.h>

class WebDashboard {
public:
    WebDashboard();
    void begin();
    void tick();
    void broadcast(const char* dataLine);
    String takePendingCommand();   // Poll from loop() to process WS commands
    bool isStaConfigured() const { return _staConfigured; }

private:
    static constexpr uint32_t AP_HEALTH_CHECK_MS    = 2000;
    static constexpr uint32_t STA_RETRY_BASE_MS     = 3000;
    static constexpr uint32_t STA_RETRY_MAX_MS      = 60000;
    static constexpr uint32_t STA_CONNECT_TIMEOUT_MS = 15000; // watchdog: re-arm if IDF misses DISCONNECTED
    static constexpr uint32_t STA_LOST_IP_RECOVERY_MS = 45000; // DHCP watchdog while still associated
    static const uint8_t CMD_QUEUE_SIZE = 4;
    static const size_t CMD_MAX_LEN = 128;
    char _cmdQueue[CMD_QUEUE_SIZE][CMD_MAX_LEN + 1];
    uint8_t _cmdHead = 0;
    uint8_t _cmdTail = 0;
    uint8_t _cmdCount = 0;
    portMUX_TYPE _cmdMux = portMUX_INITIALIZER_UNLOCKED;
    AsyncWebServer _server;
    AsyncWebSocket _ws;
    String _staSsid;
    String _staPass;
    bool _staConfigured = false;
    volatile bool _staAssociated = false;
    volatile bool _staConnected = false;
    bool _apStarted = false;
    volatile bool _needApReassert = false;
    volatile bool _staRetryPending = false;
    volatile uint8_t _staDisconnectCount = 0;
    volatile uint32_t _nextStaRetryMs = 0;
    uint32_t _lastApHealthCheckMs = 0;
    volatile uint32_t _staConnectAttemptMs = 0; // timestamp of last startStaConnectAttempt() call
    volatile uint32_t _staLostIpMs = 0;         // first LOST_IP timestamp until recovery/GOT_IP

    bool enqueueCommand(const uint8_t* data, size_t len);
    void startStaConnectAttempt();
    void ensureApUp(bool forceRestart);
    void onWiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info);
    void onWsEvent(AsyncWebSocket* server, AsyncWebSocketClient* client,
                   AwsEventType type, void* arg, uint8_t* data, size_t len);
    static void serveIndex(AsyncWebServerRequest* request);
};

#endif // ENABLE_WIFI
#endif // WEB_DASHBOARD_H
