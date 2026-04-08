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
    void broadcast(const char* dataLine);
    String takePendingCommand();   // Poll from loop() to process WS commands

private:
    static const uint8_t CMD_QUEUE_SIZE = 4;
    static const size_t CMD_MAX_LEN = 128;
    char _cmdQueue[CMD_QUEUE_SIZE][CMD_MAX_LEN + 1];
    uint8_t _cmdHead = 0;
    uint8_t _cmdTail = 0;
    uint8_t _cmdCount = 0;
    portMUX_TYPE _cmdMux = portMUX_INITIALIZER_UNLOCKED;
    AsyncWebServer _server;
    AsyncWebSocket _ws;

    bool enqueueCommand(const uint8_t* data, size_t len);
    void onWsEvent(AsyncWebSocket* server, AsyncWebSocketClient* client,
                   AwsEventType type, void* arg, uint8_t* data, size_t len);
    static void serveIndex(AsyncWebServerRequest* request);
};

#endif // ENABLE_WIFI
#endif // WEB_DASHBOARD_H
