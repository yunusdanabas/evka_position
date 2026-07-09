# Bosch PLR 40 C — Integration Research

**Parent doc:** [`README.md`](README.md). Deep-dive on the Bosch PLR 40 C integration path — protocol, Bluetooth verification, and ESP32-S3 integration.

**Status:** Research complete (2026-07-09). Bluetooth type **confirmed**. Protocol **decrypted** from GLM family (not yet verified on physical PLR 40 C unit). No firmware implemented.

---

## 1. Bluetooth Type: CONFIRMED — BLE 4.2 GATT

**Resolved (2026-07-09):** Bosch's official PLR 30 C / PLR 40 C manual explicitly states **"Bluetooth 4.2 (Low Energy)"** and that compatible devices **"must support the GATT profile."** This is the strongest and most direct evidence.

**ESP32-S3 compatibility: confirmed.** The ESP32-S3 supports **BLE only** (no classic Bluetooth SPP). This is a perfect match for the PLR 40 C.

**Community evidence:** nRF Connect scans, WebBluetooth demos (PointerEvent/bosch-plr-demo), and Stack Overflow discussions all confirm BLE GATT for Bosch PLR/GLM devices.

**The archived philipptrenz/BOSCH-GLM-rangefinder library (classic SPP) is legacy evidence** — it was tested on older GLM100C/50C models. Bosch's current documentation and newer reverse-engineering confirm the PLR 40 C and newer GLM devices use BLE GATT, not SPP.

---

## 2. BLE GATT Profile (Confirmed)

### 2.1 Service and Characteristic UUIDs

| UUID Function | Identifier |
|---|---|
| **Service UUID** | `02a6c0d0-0451-4000-b000-fb3210111989` |
| **TX/Indicate Characteristic** | `02a6c0d1-0451-4000-b000-fb3210111989` |
| **RX/Write Characteristic** | (Often unified with TX characteristic) |

**Alternative UUID set** (older GLM devices):
- Service: `00005301-0000-0041-5253-534F46540000`
- TX: `00004301-0000-0041-5253-534F46540000`
- RX: `00004302-0000-0041-5253-534F46540000`

### 2.2 Connection Pattern

1. Scan for service UUID `02a6c0d0-0451-4000-b000-fb3210111989`
2. Connect to device
3. Discover characteristic `02a6c0d1-0451-4000-b000-fb3210111989`
4. Subscribe to **indications** (not notifications — requires acknowledgment)
5. Write commands to the same characteristic
6. Parse indication responses

---

## 3. Protocol (Decrypted from GLM Family)

**⚠ IMPORTANT:** The protocol below is reverse-engineered from Bosch GLM devices (GLM 50C/50CG/120C) and is **assumed to work across the GLM/PLR family**, but **has not been verified on a physical PLR 40 C unit**. The byte-level traces are from GLM devices, not PLR 40 C specifically. **One real-device capture session is required before firmware work.**

### 3.1 Frame Format

```
Send frame:    [0xC0][command][length][data...][CRC-8]
Receive frame: [0xC0][status][length][data...][CRC-8]
```

### 3.2 Command Table

| Command | Hex Payload | Description |
|---------|-------------|-------------|
| **Continuous Sync** | `C0 55 02 01 00 1A` | Enable continuous data streaming (~4 Hz) |
| **Single Measurement** | `C0 40 00 EE` | Trigger one distance measurement |
| **Laser On** | `C0 41 00 96` | Turn laser pointer on |
| **Laser Off** | `C0 42 00 1E` | Turn laser pointer off |
| **Backlight On** | `C0 47 00 20` | Turn display backlight on |
| **Backlight Off** | `C0 48 00 62` | Turn display backlight off |
| **Serial Number** | `C0 06 00 4A` | Request device serial number |

### 3.3 Response Parsing (Continuous Sync Mode)

In continuous sync mode, the device transmits **20-byte response arrays** via BLE indications.

**Example response:** `[192, 85, 16, 6, 0, 97, 0, 162, 180, 151, 62, 0, 0, 0, 0, 0, 0, 0, 0, 172]`

**Distance extraction:**
1. **Index identification:** Distance is at bytes **7, 8, 9, 10** (0-indexed)
2. **Endianness:** Little-endian (least significant byte first)
3. **Data type:** IEEE 754 Single-Precision (32-bit) Floating-Point

**Example decoding:**
```
Bytes [162, 180, 151, 62] → Hex [0xA2, 0xB4, 0x97, 0x3E]
Little-endian reconstruction: 0x3E97B4A2
IEEE 754 parse: 0.294 meters (294 mm)
```

**C++ parsing code:**
```cpp
float parseDistance(const uint8_t* data, size_t length) {
    if (length < 11 || data[0] != 0xC0) return -1.0f;
    
    // Bytes 7-10 contain the distance as little-endian IEEE 754 float
    uint32_t raw = (uint32_t)data[10] << 24 |
                   (uint32_t)data[9]  << 16 |
                   (uint32_t)data[8]  << 8  |
                   (uint32_t)data[7];
    
    float distance_m;
    memcpy(&distance_m, &raw, sizeof(float));
    return distance_m * 1000.0f;  // convert to mm
}
```

### 3.4 CRC-8 Checksum (Bosch-Specific)

Bosch uses a custom CRC-8 algorithm (not standard CRC-8):
- **Initialization Vector (IV):** `0xAA`
- **Polynomial:** `0xA6`
- **Input Reflection:** False
- **Output Reflection:** False

**C++ implementation:**
```cpp
uint8_t calculateBoschCRC8(const uint8_t* data, size_t length) {
    uint8_t crc = 0xAA;  // Initialization vector
    for (size_t i = 0; i < length; i++) {
        uint8_t b = data[i];
        for (int j = 0; j < 8; j++) {
            uint8_t x = ((crc >> 7) ^ (b >> (7 - j))) & 1;
            crc = (crc << 1) & 0xFF;
            if (x) {
                crc ^= 0xA6;  // Bosch polynomial
            }
        }
    }
    return crc;
}
```

**Verification:**
- Command `C0 40 00` → CRC `0xEE` ✓
- Command `C0 55 02 01 00` → CRC `0x1A` ✓

### 3.5 Status Codes

| Code | Meaning |
|------|---------|
| 0 | OK |
| 1 | Communication timeout |
| 3 | Checksum error |
| 4 | Unknown command |
| 5 | Invalid access level |
| 8 | Hardware error |
| 10 | Device not ready |

---

## 4. USB Interface: NONE

**Confirmed:** The PLR 40 C has **no USB port** (no Micro-USB, Mini-USB, or USB-C). The device relies entirely on:
- 2× AAA alkaline batteries (internal)
- BLE radio (wireless only)

**Implication:** There is no wired fallback. BLE is the only data path.

**Power logistics for continuous operation:**
- Must modify the device to accept external 3.0V DC (solder to battery springs)
- Fragile modification — vibrations could fracture solder joints
- 5-minute auto-power-off timer (cannot be permanently disabled via software)

---

## 5. ESP32-S3 Integration (NimBLE Stack)

### 5.1 Why NimBLE?

The ESP32-S3 supports **BLE only** (no classic Bluetooth). The recommended stack is **NimBLE-Arduino** (not the default Bluedroid stack):
- **Faster initialization:** ~200 ms vs ~600 ms (Bluedroid)
- **Lower memory footprint:** Better for running alongside WiFi + WebSocket
- **Up to 9 concurrent BLE connections:** Future-proof for multi-sensor setups

### 5.2 WiFi + BLE Coexistence

The ESP32-S3 has a **single 2.4 GHz radio** shared between WiFi and Bluetooth. Time-division multiplexing (TDM) handles coexistence, but throughput degrades when both are active.

**Recommended configuration (sdkconfig):**
```
CONFIG_ESP_COEX_SW_COEXIST_ENABLE=y
CONFIG_BTDM_CTRL_PINNED_TO_CORE_0=y  # BLE on Core 0
CONFIG_ESP_WIFI_TASK_CORE_ID=1        # WiFi on Core 1
```

**Connection parameters:**
- Connection interval: 15 ms
- Timeout: 120 ms
- Balances high-frequency polling with WiFi throughput

### 5.3 Implementation State Machine

```cpp
#include <NimBLEDevice.h>

class BoschPLR40C_BLE {
private:
    NimBLEClient* pClient;
    NimBLERemoteCharacteristic* pChar;
    bool connected = false;
    
    static const char* SERVICE_UUID = "02a6c0d0-0451-4000-b000-fb3210111989";
    static const char* CHAR_UUID = "02a6c0d1-0451-4000-b000-fb3210111989";
    
public:
    bool begin() {
        NimBLEDevice::init("");
        pClient = NimBLEDevice::createClient();
        
        // Set connection parameters
        pClient->setConnectionParams(15, 15, 0, 120);  // 15ms interval, 120ms timeout
        
        // Connect to PLR 40 C (need MAC address or name scan)
        if (pClient->connect(NimBLEAddress("xx:xx:xx:xx:xx:xx"))) {
            NimBLERemoteService* pService = pClient->getService(SERVICE_UUID);
            if (pService) {
                pChar = pService->getCharacteristic(CHAR_UUID);
                if (pChar && pChar->canIndicate()) {
                    // Subscribe to indications (requires acknowledgment)
                    pChar->subscribe(true, notifyCallback);
                    connected = true;
                    
                    // Enable continuous sync mode
                    uint8_t syncCmd[] = {0xC0, 0x55, 0x02, 0x01, 0x00, 0x1A};
                    pChar->writeValue(syncCmd, sizeof(syncCmd));
                    return true;
                }
            }
        }
        return false;
    }
    
    static void notifyCallback(NimBLERemoteCharacteristic* pChar, uint8_t* data, size_t length, bool isNotify) {
        // Parse 20-byte response
        if (length >= 11 && data[0] == 0xC0) {
            // Validate CRC
            uint8_t expectedCRC = calculateBoschCRC8(data, length - 1);
            if (data[length - 1] == expectedCRC) {
                // Extract distance (bytes 7-10, little-endian IEEE 754 float)
                uint32_t raw = (uint32_t)data[10] << 24 |
                               (uint32_t)data[9]  << 16 |
                               (uint32_t)data[8]  << 8  |
                               (uint32_t)data[7];
                float distance_m;
                memcpy(&distance_m, &raw, sizeof(float));
                float distance_mm = distance_m * 1000.0f;
                
                // Update global state (thread-safe)
                // ...
            }
        }
    }
    
    float measure() {
        if (!connected || !pChar) return -1.0f;
        
        // Send single measurement command
        uint8_t cmd[] = {0xC0, 0x40, 0x00, 0xEE};
        pChar->writeValue(cmd, sizeof(cmd));
        
        // Wait for indication response (non-blocking version needed for 20Hz loop)
        // ...
        return -1.0f;  // placeholder
    }
    
    void end() {
        if (pClient) {
            pClient->disconnect();
            NimBLEDevice::deinit();
        }
    }
};
```

---

## 6. Risks and Recommendation

### 6.1 Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Protocol not verified on PLR 40 C** | HIGH | One real-device capture session required before firmware work |
| **BLE latency jitter** | MEDIUM | 15ms connection interval + WiFi coexistence TDM = variable 15–100ms latency; unsuitable for closed-loop control |
| **Power supply fragility** | HIGH | No USB, must solder to battery springs; vibrations could fracture joints |
| **5-minute auto-power-off** | HIGH | Cannot be permanently disabled; device will shut down during operation |
| **BLE + WiFi coexistence** | MEDIUM | Single 2.4 GHz radio shared; throughput degrades when both active |
| **No wired fallback** | HIGH | If BLE fails, no alternative data path |

### 6.2 Recommendation

**Feasibility sprint:** The PLR 40 C is reasonable for a short, low-cost prototype:
1. Buy one unit (~3,865–4,275 TRY / ~$110–125)
2. Use nRF Connect to capture actual BLE traffic
3. Validate the GLM-family protocol on the physical PLR 40 C
4. Test on ESP32-S3 with NimBLE

**Production system:** **Do not use the PLR 40 C.** Switch to a wired industrial sensor:
- **Meskernel LDK-40 / LDL-T:** Wired UART TTL 3.3V, up to 100 Hz, ±1–2 mm accuracy, ~same price (~$70–87.50)
- **Dimetix D-Series:** Industrial-grade, documented protocol, ±1 mm accuracy, expensive (~$2,200–4,300+)

**Rationale:** The PLR 40 C is a consumer handheld meter designed for occasional human-driven measurements, not continuous automated tracking. BLE latency jitter, power supply fragility, and auto-power-off make it unsuitable for a production positioning system. Wired industrial sensors (Meskernel/Dimetix) provide deterministic, zero-latency data over a physical wire — the correct architecture for replacing a draw-wire encoder.

---

## 7. References

- **Bosch PLR 40 C manual:** Bluetooth 4.2 (Low Energy), GATT profile required
- **BLE UUIDs:** Confirmed via WebBluetooth demos (PointerEvent/bosch-plr-demo) and Stack Overflow discussions
- **Protocol reverse-engineering:** GLM 50C/50CG/120C (Stack Overflow, Nordic DevZone, GitHub Gists)
- **CRC-8 algorithm:** Custom Bosch CRC-8 (polynomial 0xA6, init 0xAA)
- **ESP32-S3 BLE:** NimBLE-Arduino recommended (lighter than Bluedroid)
- **Community library (legacy):** [philipptrenz/BOSCH-GLM-rangefinder](https://github.com/philipptrenz/BOSCH-GLM-rangefinder) (archived, classic SPP — not applicable to PLR 40 C)

---

*Document updated: 2026-07-09. Bluetooth type confirmed (BLE 4.2 GATT). Protocol decrypted from GLM family. Physical PLR 40 C verification still required before firmware work.*
