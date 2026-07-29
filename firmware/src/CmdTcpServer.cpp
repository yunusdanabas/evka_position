// CmdTcpServer.cpp — raw TCP command server on port 8080 for the Python clients
// under tools/evka_gui/ and tools/position_checker/. Accepts up to MAX_CLIENTS,
// queues command lines for the main loop, and broadcasts the 20 Hz X/Y/Z + SENSOR
// stream. Canonical protocol: docs/PROTOCOL.md.
#include "CmdTcpServer.h"

#if ENABLE_WIFI && ENABLE_CMD_TCP

CmdTcpServer::CmdTcpServer()
    : _server(CMD_TCP_PORT) {
    for (uint8_t i = 0; i < MAX_CLIENTS; i++) _rxOverflow[i] = false;
}

void CmdTcpServer::begin() {
    _server.begin();
    _server.setNoDelay(true);
    Serial.printf("[TCP] Server started on port %d\n", CMD_TCP_PORT);
}

void CmdTcpServer::poll() {
    // Accept new clients
    WiFiClient newClient = _server.available();
    if (newClient) {
        bool accepted = false;
        for (uint8_t i = 0; i < MAX_CLIENTS; i++) {
            if (!_clients[i] || !_clients[i].connected()) {
                _clients[i].stop();   // release any stale socket
                _clients[i] = newClient;
                _clients[i].setNoDelay(true);
                _rxBuffers[i] = "";
                _rxOverflow[i] = false;
                Serial.printf("[TCP] Client #%u connected\n", i);
                accepted = true;
                break;
            }
        }
        if (!accepted) {
            newClient.println("ERR:MAX_CLIENTS");
            newClient.stop();
            Serial.println("[TCP] Rejected client — max reached");
        }
    }

    // Read from connected clients
    for (uint8_t i = 0; i < MAX_CLIENTS; i++) {
        if (!_clients[i] || !_clients[i].connected()) {
            if (_clients[i]) {
                _clients[i].stop();
                _rxBuffers[i] = "";
                _rxOverflow[i] = false;
            }
            continue;
        }

        while (_clients[i].available()) {
            char ch = (char)_clients[i].read();
            if (ch == '\n' || ch == '\r') {
                if (!_rxOverflow[i]) {
                    _rxBuffers[i].trim();
                    if (_rxBuffers[i].length() > 0) {
                        handleLine(i, _rxBuffers[i]);
                    }
                }
                _rxBuffers[i] = "";
                _rxOverflow[i] = false;
            } else {
                _rxBuffers[i] += ch;
                if (_rxBuffers[i].length() > CMD_RX_BUF_MAX) {
                    _clients[i].println("ERR:CMD_TOO_LONG");
                    _rxBuffers[i] = "";
                    _rxOverflow[i] = true;
                }
            }
        }
    }
}

void CmdTcpServer::handleLine(uint8_t clientIdx, const String& line) {
    // Commands handled directly by TCP server (not forwarded)

    if (line == "GET_IP") {
        if (WiFi.status() == WL_CONNECTED) {
            _clients[clientIdx].println("STA_IP:" + WiFi.localIP().toString());
        } else {
            _clients[clientIdx].println("STA_IP:NOT_CONNECTED");
        }
        return;
    }

    // Forward all other commands to main loop via queue.
    // This centralizes command policy (including WIFI_SET/WIFI_AYAR gating)
    // in processCommand().
    if (!enqueueCommand(line)) {
        _clients[clientIdx].println("ERR:CMD_QUEUE_FULL");
    }
}

void CmdTcpServer::broadcastPosition(float x, float y, float z) {
    char buf[64];
    snprintf(buf, sizeof(buf), "X%.2f,Y%.2f,Z%.2f", x, y, z);
    for (uint8_t i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i] && _clients[i].connected()) {
            _clients[i].println(buf);
        }
    }
}

void CmdTcpServer::broadcastSensorData(float r, float theta, float phi,
                                        uint8_t valid, uint32_t frame) {
    char buf[96];
    snprintf(buf, sizeof(buf), "SENSOR,%.2f,%.3f,%.3f,%u,%lu",
             r, theta, phi, valid, (unsigned long)frame);
    for (uint8_t i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i] && _clients[i].connected()) {
            _clients[i].println(buf);
        }
    }
}

void CmdTcpServer::sendToAllClients(const char* msg) {
    for (uint8_t i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i] && _clients[i].connected()) {
            _clients[i].println(msg);
        }
    }
}

bool CmdTcpServer::enqueueCommand(const String& line) {
    if (_cmdCount >= CMD_QUEUE_SIZE) return false;
    size_t copyLen = line.length();
    if (copyLen > CMD_MAX_LEN) copyLen = CMD_MAX_LEN;
    memcpy(_cmdQueue[_cmdTail], line.c_str(), copyLen);
    _cmdQueue[_cmdTail][copyLen] = '\0';
    _cmdTail = (uint8_t)((_cmdTail + 1) % CMD_QUEUE_SIZE);
    _cmdCount++;
    return true;
}

String CmdTcpServer::takePendingCommand() {
    if (_cmdCount == 0) return String();
    String cmd(_cmdQueue[_cmdHead]);
    _cmdQueue[_cmdHead][0] = '\0';
    _cmdHead = (uint8_t)((_cmdHead + 1) % CMD_QUEUE_SIZE);
    _cmdCount--;
    return cmd;
}

uint8_t CmdTcpServer::clientCount() {
    uint8_t count = 0;
    for (uint8_t i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i] && _clients[i].connected()) {
            count++;
        }
    }
    return count;
}

#endif // ENABLE_WIFI && ENABLE_CMD_TCP
