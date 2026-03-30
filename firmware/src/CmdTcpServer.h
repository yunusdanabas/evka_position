#ifndef CMD_TCP_SERVER_H
#define CMD_TCP_SERVER_H

#include "SphericalSensor.h"

#if ENABLE_WIFI && ENABLE_CMD_TCP

#include <WiFi.h>

class CmdTcpServer {
public:
    CmdTcpServer();
    void begin();
    void poll();                    // Call from loop() — accept clients, read commands
    void broadcastPosition(float x, float y, float z);
    void broadcastSensorData(float r, float theta, float phi,
                             uint8_t valid, uint32_t frame);
    void sendToAllClients(const char* msg);
    String takePendingCommand();
    uint8_t clientCount();

private:
    static const uint8_t MAX_CLIENTS = 3;
    static const uint8_t CMD_RX_BUF_MAX = 128;  // Per-client rx buffer overflow guard
    WiFiServer _server;
    WiFiClient _clients[MAX_CLIENTS];
    String     _rxBuffers[MAX_CLIENTS];
    String     _pendingCmd;

    void handleLine(uint8_t clientIdx, const String& line);
};

#endif // ENABLE_WIFI && ENABLE_CMD_TCP
#endif // CMD_TCP_SERVER_H
