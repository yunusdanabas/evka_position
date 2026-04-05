#include "CmdTcpServer.h"

#if ENABLE_WIFI && ENABLE_CMD_TCP

#include <Preferences.h>

CmdTcpServer::CmdTcpServer()
    : _server(CMD_TCP_PORT) {}

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
            }
            continue;
        }

        while (_clients[i].available()) {
            char ch = (char)_clients[i].read();
            if (ch == '\n' || ch == '\r') {
                _rxBuffers[i].trim();
                if (_rxBuffers[i].length() > 0) {
                    handleLine(i, _rxBuffers[i]);
                }
                _rxBuffers[i] = "";
            } else {
                _rxBuffers[i] += ch;
                // Prevent buffer overflow from misbehaving clients
                if (_rxBuffers[i].length() > CMD_RX_BUF_MAX) {
                    _rxBuffers[i] = "";
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

    if (line.startsWith("WIFI_SET:") || line.startsWith("WIFI_AYAR:")) {
        // Accept both English and CMD-legacy command names
        int colonIdx = line.indexOf(':');
        String payload = line.substring(colonIdx + 1);
        int commaIdx = payload.indexOf(',');
        if (commaIdx != -1) {
            String ssid = payload.substring(0, commaIdx);
            String pass = payload.substring(commaIdx + 1);
            if (ssid.length() == 0 || ssid.length() > 32) {
                _clients[clientIdx].println("ERR:SSID_INVALID");
                return;
            }
            if (pass.length() > 0 && pass.length() < 8) {
                _clients[clientIdx].println("ERR:PASS_TOO_SHORT");
                return;
            }

            Preferences prefs;
            prefs.begin("wifi_cfg", false);
            prefs.putString("ssid", ssid);
            prefs.putString("pass", pass);
            prefs.end();

            _clients[clientIdx].println("ACK:WIFI_SAVED");
            Serial.printf("[TCP] WiFi credentials saved (SSID: %s), rebooting...\n", ssid.c_str());
            delay(500);
            ESP.restart();
        } else {
            _clients[clientIdx].println("ERR:WIFI_INVALID");
        }
        return;
    }

    // Forward all other commands to main loop via pendingCmd
    _pendingCmd = line;
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

String CmdTcpServer::takePendingCommand() {
    String cmd = _pendingCmd;
    _pendingCmd = "";
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
