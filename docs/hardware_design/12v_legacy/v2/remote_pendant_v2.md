# Remote Pendant — V2 Upgrade Specification

> Upgraded wireless button remote for EVKA positioning system.  
> ESP32-C3 based, ESP-NOW protocol, **5 buttons**, extended command set.  
> Same hardware platform as V1 remote — only firmware and button layout changed.

---

## 1. Overview

| Feature | V1 Remote | V2 Remote (Upgrade) |
|---------|-----------|---------------------|
| MCU | ESP32-C3-WROOM-02 | **Same** |
| Protocol | ESP-NOW | **Same** |
| Buttons | 2 (ZERO, SAVE_POINT) | **5 (ZERO, SAVE, RECORD, STATUS, CALIBRATE)** |
| Display | None | **Same (none)** |
| Battery | 1S 500mAh LiPo + TP4056 | **Same** |
| Range | 50m indoor, 200m outdoor | **Same** |
| Battery life | ~14 months | **~12 months** (more wake-ups) |

---

## 2. Button Map

### 2a. Physical Layout

```
    Remote enclosure (handheld, 80×50×20mm):
    
    ┌─────────────────────────┐
    │                         │
    │    [0] RED    [1] GREEN │
    │      ZERO     SAVE_PT   │
    │                         │
    │   [2] YELLOW  [3] BLUE  │
    │     RECORD    STATUS    │
    │                         │
    │       [4] WHITE         │
    │       CALIBRATE         │
    │                         │
    │    (LED: Blue status)   │
    │                         │
    └─────────────────────────┘
```

### 2b. Button Functions

| Button | Color | GPIO | Command | Action on Main Unit |
|--------|-------|------|---------|---------------------|
| 0 | Red | GPIO 4 | `ZERO` | Reset all encoder counts to zero |
| 1 | Green | GPIO 5 | `SAVE_POINT` | Save current X/Y/Z position to buffer |
| 2 | Yellow | GPIO 6 | `TOGGLE_RECORD` | Start/stop continuous position logging |
| 3 | Blue | GPIO 7 | `REQUEST_STATUS` | Main unit responds with battery, WiFi status |
| 4 | White | GPIO 10 | `CALIBRATE` | Enter calibration mode (theta/phi/wire) |

### 2c. Command Protocol

ESP-NOW packet format (same as V1):
```
    Packet payload: 1 byte
    
    Value 0x00 → Button 0 pressed (ZERO)
    Value 0x01 → Button 1 pressed (SAVE_POINT)
    Value 0x02 → Button 2 pressed (TOGGLE_RECORD)
    Value 0x03 → Button 3 pressed (REQUEST_STATUS)
    Value 0x04 → Button 4 pressed (CALIBRATE)
    
    Heartbeat: 0xFF every 5 seconds (optional, for link monitoring)
```

**Main unit response (when applicable):**
```
    Serial/WebSocket: "REMOTE:ZERO_OK\n"
    Serial/WebSocket: "REMOTE:POINT_SAVED,<x>,<y>,<z>\n"
    Serial/WebSocket: "REMOTE:RECORD_<START|STOP>\n"
    Serial/WebSocket: "REMOTE:STATUS,BAT:<v>,WIFI:<sta|ap|none>\n"
    Serial/WebSocket: "REMOTE:CAL_ENTER\n"
```

---

## 3. Hardware

### 3a. Schematic (Unchanged from V1)

```
    ESP32-C3-WROOM-02
    ┌─────────────────────┐
    │                     │
    │  GPIO 4 ── Button 0 │
    │  GPIO 5 ── Button 1 │
    │  GPIO 6 ── Button 2 │
    │  GPIO 7 ── Button 3 │
    │  GPIO 10 ─ Button 4 │
    │                     │
    │  GPIO 8 ── Blue LED │
    │                     │
    │  3.3V ──── VCC      │
    │  GND ───── GND      │
    │                     │
    │  USB (programming)  │
    └─────────────────────┘
    
    Each button: GPIO ── Button ── GND (internal pull-up enabled)
    LED: GPIO 8 ── 1kΩ ── LED ── GND
    
    Power:
    1S LiPo (3.7V) ── TP4056 module (USB charging)
    TP4056 OUT+ ── 3.3V LDO ── ESP32 VCC
    TP4056 OUT- ── GND
```

### 3b. Button Wiring

```
    GPIO 4 ────┬───┬─── 3.3V (internal pull-up)
               │   │
          10kΩ│   │(internal weak pull-up sufficient, 
               │   │ but 10kΩ external recommended for reliability)
               │   │
          [Button 0] ── GND
    
    Repeat for GPIO 5/6/7/10 with buttons 1/2/3/4
```

**Why external 10kΩ pull-up?** ESP32-C3 internal pull-up is ~45kΩ. In noisy environments, a stronger external pull-up (10kΩ) prevents false triggers.

---

## 4. Firmware

### 4a. Wake Source Configuration

```cpp
#include <esp_now.h>
#include <WiFi.h>
#include <esp_sleep.h>

#define BTN_ZERO      GPIO_NUM_4
#define BTN_SAVE      GPIO_NUM_5
#define BTN_RECORD    GPIO_NUM_6
#define BTN_STATUS    GPIO_NUM_7
#define BTN_CALIBRATE GPIO_NUM_10
#define PIN_LED       GPIO_NUM_8

// All buttons are wake sources
static const gpio_num_t WAKE_BUTTONS[] = {
    BTN_ZERO, BTN_SAVE, BTN_RECORD, BTN_STATUS, BTN_CALIBRATE
};

void setup() {
    // Configure buttons with pull-ups
    for (auto pin : WAKE_BUTTONS) {
        pinMode(pin, INPUT_PULLUP);
        esp_sleep_enable_ext0_wakeup(pin, LOW);  // Wake on button press (LOW)
    }
    
    pinMode(PIN_LED, OUTPUT);
    
    // If woke from deep sleep, send command immediately
    if (esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_EXT0) {
        sendButtonCommand();
    }
    
    // Go back to deep sleep
    esp_deep_sleep_start();
}

void sendButtonCommand() {
    // Determine which button was pressed
    uint8_t buttonId = 0xFF;
    if (digitalRead(BTN_ZERO) == LOW)      buttonId = 0;
    else if (digitalRead(BTN_SAVE) == LOW)      buttonId = 1;
    else if (digitalRead(BTN_RECORD) == LOW)    buttonId = 2;
    else if (digitalRead(BTN_STATUS) == LOW)    buttonId = 3;
    else if (digitalRead(BTN_CALIBRATE) == LOW) buttonId = 4;
    
    if (buttonId == 0xFF) return;  // Spurious wake
    
    // Initialize WiFi/ESP-NOW
    WiFi.mode(WIFI_STA);
    if (esp_now_init() == ESP_OK) {
        // Add peer (main unit MAC address)
        esp_now_peer_info_t peer = {};
        memcpy(peer.peer_addr, MAIN_UNIT_MAC, 6);
        peer.channel = 1;
        peer.encrypt = false;
        esp_now_add_peer(&peer);
        
        // Send command
        esp_now_send(peer.peer_addr, &buttonId, 1);
        
        // Blink LED to confirm
        digitalWrite(PIN_LED, HIGH);
        delay(50);
        digitalWrite(PIN_LED, LOW);
        
        // Wait for send completion (max 100ms)
        delay(100);
    }
}

void loop() {
    // Never reached — deep sleep immediately after setup
}
```

### 4b. Power Consumption

| State | Current | Duration | Per Event |
|-------|---------|----------|-----------|
| Deep sleep | ~10µA | 99.9% of time | — |
| Wake + ESP-NOW init | ~80mA | ~300ms | ~24µAh |
| LED blink | ~3mA | ~50ms | ~0.04µAh |
| **Total per button press** | | **~350ms** | **~24µAh** |

**Battery life estimate:**
```
    500mAh battery
    Usable capacity (80%): 400mAh
    Self-discharge (LiPo): ~2%/month → ~10mAh/month
    
    Presses per day: 50
    Daily consumption: 50 × 24µAh = 1.2mAh
    Monthly consumption: 36mAh + 10mAh self-discharge = 46mAh
    
    Battery life: 400mAh / 46mAh/month = ~8.7 months
    
    With 50 presses/day and 500mAh: ~9 months
    With 20 presses/day and 500mAh: ~18 months
```

---

## 5. Main Unit Receiver

### 5a. ESP-NOW Receiver (in main firmware)

```cpp
// In EvkaPosition.cpp or WebDashboard.cpp

#define ENABLE_ESPNOW_REMOTE 1

static const char* const REMOTE_BUTTON_CMD[] = {
    "ZERO",           // Button 0
    "SAVE_POINT",     // Button 1
    "TOGGLE_RECORD",  // Button 2
    "REQUEST_STATUS", // Button 3
    "CALIBRATE",      // Button 4
};

void onEspNowReceive(const uint8_t *mac, const uint8_t *data, int len) {
    if (len != 1) return;
    
    uint8_t buttonId = data[0];
    if (buttonId > 4) return;  // Unknown button
    
    const char* cmd = REMOTE_BUTTON_CMD[buttonId];
    processCommand(cmd);  // Reuse existing command processor
    
    // Acknowledge via serial/WebSocket
    char msg[64];
    snprintf(msg, sizeof(msg), "REMOTE:%s_OK\n", cmd);
    serialPrint(msg);
    if (ENABLE_WIFI) webSocket.broadcast(msg);
}
```

### 5b. Command Implementations

**ZERO (Button 0):**
```cpp
if (strcmp(cmd, "ZERO") == 0) {
    encTheta.write(0);
    encPhi.write(0);
    encWire.write(0);
    // Broadcast acknowledgment
}
```

**SAVE_POINT (Button 1):**
```cpp
if (strcmp(cmd, "SAVE_POINT") == 0) {
    savePointToBuffer(currentX, currentY, currentZ);
    // Broadcast: "REMOTE:POINT_SAVED,1234,567,890\n"
}
```

**TOGGLE_RECORD (Button 2):**
```cpp
if (strcmp(cmd, "TOGGLE_RECORD") == 0) {
    recordingActive = !recordingActive;
    // Broadcast: "REMOTE:RECORD_START\n" or "REMOTE:RECORD_STOP\n"
}
```

**REQUEST_STATUS (Button 3):**
```cpp
if (strcmp(cmd, "REQUEST_STATUS") == 0) {
    float battVoltage = readBatteryVoltage();
    const char* wifiStatus = getWifiStatusString();
    // Broadcast: "REMOTE:STATUS,BAT:11.2,WIFI:STA\n"
}
```

**CALIBRATE (Button 4):**
```cpp
if (strcmp(cmd, "CALIBRATE") == 0) {
    enterCalibrationMode();
    // Broadcast: "REMOTE:CAL_ENTER\n"
    // User then uses buttons to select axis and set zero
}
```

---

## 6. Enclosure & Mechanical

### 6a. Recommended Enclosure

```
    Handheld enclosure: 80×50×20mm ABS
    
    Front panel:
    ┌─────────────────────────┐
    │  ○ RED    ○ GREEN      │  ← 5mm LED indicators (optional)
    │  [ZERO]   [SAVE]        │  ← 12×12mm tactile buttons
    │                         │
    │  ○ YELLOW ○ BLUE       │
    │  [RECORD] [STATUS]      │
    │                         │
    │     ○ WHITE            │
    │     [CALIBRATE]         │
    │                         │
    └─────────────────────────┘
    
    Side: USB-C or micro-USB for charging (TP4056 access)
    Back: Battery compartment or sealed (if LiPo internal)
```

### 6b. Button Feel

| Button | Tactile Feedback | Actuation Force |
|--------|-----------------|-----------------|
| 0–4 | Mechanical click | ~200g |
| Travel | ~0.5mm | — |
| Life | >100,000 cycles | — |

**Recommendation:** Use 12×12mm × 7.3mm tactile buttons (Omron B3F or clone). Cheap, reliable, easy to mount on perfboard.

---

## 7. Pairing Procedure

### 7a. Factory Pairing

```
    1. On main unit: Enter pairing mode (hold reset button 5 sec)
    2. Main unit broadcasts its MAC address via AP mode
    3. On remote: Press and hold BUTTON_0 + BUTTON_4 for 3 seconds
    4. Remote scans for main unit AP, saves MAC to NVS
    5. Both units blink LED 3× to confirm pairing
```

### 7b. Manual MAC Configuration

```cpp
// In remote firmware, hardcode main unit MAC:
uint8_t MAIN_UNIT_MAC[6] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};

// Or read from NVS:
preferences.begin("remote", true);
preferences.getBytes("peer_mac", MAIN_UNIT_MAC, 6);
preferences.end();
```

---

## 8. Testing

| Test | Procedure | Pass Criteria |
|------|-----------|---------------|
| Button wake | Press any button | Remote wakes, LED blinks, ESP-NOW sends |
| Range test | Walk away from main unit | Commands work at 50m line-of-sight |
| Battery life | Leave remote for 1 week | Still responds after 7 days |
| Deep sleep current | Measure with multimeter | <50µA in deep sleep |
| Pairing | Factory reset both, re-pair | Successful within 30 seconds |
| All buttons | Press each button 10× | Correct command received on main unit |

---

## 9. Bill of Materials (Remote)

| Ref | Qty | Part | Spec | Est. Cost |
|-----|-----|------|------|-----------|
| U1 | 1 | ESP32-C3-WROOM-02 | Module | ~60₺ |
| SW0–4 | 5 | Tactile button | 12×12mm, THT | ~5₺ |
| LED1 | 1 | LED | 3mm Blue | ~1₺ |
| R_LED | 1 | Resistor | 1kΩ | ~0.5₺ |
| R_PU0–4 | 5 | Resistor | 10kΩ | ~2.5₺ |
| U_CHG | 1 | TP4056 module | With DW01A protection | ~15₺ |
| BAT | 1 | LiPo battery | 1S 500mAh | ~30₺ |
| J_BAT | 1 | JST-PH 2P | 2.0mm | ~2₺ |
| PCB | 1 | Custom or perfboard | 50×40mm | ~5₺ |
| Enclosure | 1 | ABS handheld | 80×50×20mm | ~20₺ |
| **Total** | | | | **~140₺** |

---

## 10. Related Documents

- [Main V2 README](../README.md) — System overview
- [MCU Subsystem](subsystems/mcu_subsystem_v2.md) — ESP32-S3 main unit
- Legacy remote: [`../../remote/README.md`](../../remote/README.md) — V1 remote reference
