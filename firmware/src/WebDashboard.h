#ifndef WEB_DASHBOARD_H
#define WEB_DASHBOARD_H

#include "SphericalSensor.h"

#if ENABLE_WIFI

#include <WiFi.h>
#include <ESPAsyncWebServer.h>

class WebDashboard {
public:
    WebDashboard();
    void begin();
    void broadcast(const char* dataLine);
    String takePendingCommand();   // Poll from loop() to process WS commands

private:
    String _pendingCmd;
    AsyncWebServer _server;
    AsyncWebSocket _ws;

    void onWsEvent(AsyncWebSocket* server, AsyncWebSocketClient* client,
                   AwsEventType type, void* arg, uint8_t* data, size_t len);
    static void serveIndex(AsyncWebServerRequest* request);
};

#endif // ENABLE_WIFI
#endif // WEB_DASHBOARD_H
