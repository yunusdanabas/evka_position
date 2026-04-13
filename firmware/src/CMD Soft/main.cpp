#include <Arduino.h>
#include <WiFi.h>
#include <Preferences.h>
#include <ESP32Encoder.h>
#include <math.h>

Preferences hafiza;

const char* apSsid = "CMDCNC";      
const char* apPassword = "cmdcnc1234";  
IPAddress local_IP(192, 168, 1, 50);   
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);

String staSsid = "";
String staPassword = "";
WiFiServer server(8080);

ESP32Encoder encTheta;
ESP32Encoder encPhi;
ESP32Encoder encR;

const float PULSE_TO_RAD  = (2.0 * PI) / 20000.0; 
const float PULSE_TO_MM_R = 0.02500;              
const float R_OFFSET      = 0.0;                

float smoothX = 0, smoothY = 0, smoothZ = 0;
const float alpha = 0.2;

void setup() {
  Serial.begin(115200);

  ESP32Encoder::useInternalWeakPullResistors = puType::up; 
  encTheta.attachHalfQuad(14, 12);
  encPhi.attachHalfQuad(32, 35);
  encR.attachHalfQuad(16, 17);

  encTheta.clearCount();
  encPhi.clearCount();
  encR.clearCount();

  hafiza.begin("ayarlar", false);
  staSsid = hafiza.getString("ssid", "");
  staPassword = hafiza.getString("pass", "");

  WiFi.mode(WIFI_AP_STA); 
  WiFi.softAPConfig(local_IP, gateway, subnet);
  WiFi.softAP(apSsid, apPassword);
  
  if (staSsid != "") {
    WiFi.begin(staSsid.c_str(), staPassword.c_str());
  }

  server.begin();
  Serial.println("Sistem Hazir! TCP Port 8080 Dinleniyor...");
}

void loop() {
  WiFiClient client = server.available(); 
  
  if (client) {
    while (client.connected()) {
      
      if (client.available()) {
        String komut = client.readStringUntil('\n');
        komut.trim();

        if (komut.startsWith("WIFI_AYAR:")) {
          String veri = komut.substring(10);
          int virgulIndex = veri.indexOf(',');
          if (virgulIndex != -1) {
            hafiza.putString("ssid", veri.substring(0, virgulIndex));
            hafiza.putString("pass", veri.substring(virgulIndex + 1));
            client.println("WIFI_KAYDEDILDI_REBOOT");
            delay(500);
            ESP.restart();
          }
        }
        else if (komut == "ZERO") {
          encTheta.clearCount();
          encPhi.clearCount();
          encR.clearCount();
          smoothX = 0; smoothY = 0; smoothZ = 0; 
          client.println("SIFIRLANDI");
        }
        else if (komut == "GET_IP") {
          if (WiFi.status() == WL_CONNECTED) {
            client.println("STA_IP:" + WiFi.localIP().toString());
          } else {
            client.println("STA_IP:BAGLI_DEGIL");
          }
        }
      }

      float theta = encTheta.getCount() * PULSE_TO_RAD;
      float phi   = encPhi.getCount() * PULSE_TO_RAD;
      float r     = (encR.getCount() * PULSE_TO_MM_R) + R_OFFSET; // R_OFFSET artık 0

      float rawX = r * cos(phi) * cos(theta);
      float rawY = r * cos(phi) * sin(theta);
      float rawZ = r * sin(phi);

      smoothX = (alpha * rawX) + ((1.0 - alpha) * smoothX);
      smoothY = (alpha * rawY) + ((1.0 - alpha) * smoothY);
      smoothZ = (alpha * rawZ) + ((1.0 - alpha) * smoothZ);

      String veri = "X" + String(smoothX, 2) + ",Y" + String(smoothY, 2) + ",Z" + String(smoothZ, 2) + "\n";
      client.print(veri);
      
      delay(50); 
    }
    client.stop();
  }
}
