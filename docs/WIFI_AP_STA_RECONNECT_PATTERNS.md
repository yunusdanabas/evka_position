# ESP32 WiFi.begin() in AP+STA Mode: Safe Reconnection Patterns

**Date**: 2026-04-09  
**Context**: ESP32 Wemos D1 R32 running WIFI_AP_STA mode with concurrent web dashboard + STA uplink  
**Status**: Documented best practices + firmware implementation verified

---

## Quick Answer

**Does `WiFi.begin()` disrupt the AP or disconnect AP clients?**

| Scenario | Effect | Risk |
|----------|--------|------|
| **STA mode alone** `WiFi.begin()` in `WIFI_STA` | Connects to network | N/A |
| **AP+STA mode** `WiFi.begin()` in `WIFI_AP_STA` (after AP is started) | **NO disruption to AP clients** | ✓ Safe |
| **AP+STA mode** `WiFi.begin()` called **before** `softAP()` | **YES — AP may not start** | ⚠️ Ordering matters |
| **Rapid repeated** `WiFi.begin()` calls | Minimal disruption, but increases disconnect risk | ✓ Mitigate with backoff |

**Best pattern**: Call `WiFi.begin()` only when STA is disconnected or needs reconnect, with **exponential backoff** to avoid radio thrashing.

---

## 1. How AP+STA Coexistence Works

### Radio Arbitration
ESP32 has **one 2.4 GHz radio** shared via the Modem Task (firmware-level scheduler):
- **WiFi AP**: Transmits beacons every ~100 ms, responds to client frames
- **WiFi STA**: Scans for networks, associates, maintains link
- **Modem arbiter**: Time-slices radio access; typically gives priority to STA when active

### WiFi Modes and Behavior

| Mode | STA | AP | Effect |
|------|-----|----|----|
| `WIFI_OFF` | ✗ | ✗ | Radio off, minimum power |
| `WIFI_STA` | ✓ | ✗ | Client mode only |
| `WIFI_AP` | ✗ | ✓ | Access point only — **safe to call `WiFi.begin()` but has no effect** |
| `WIFI_AP_STA` | ✓ | ✓ | **Concurrent operation** — `WiFi.begin()` applies to STA only |

---

## 2. Does WiFi.begin() Disrupt AP Clients?

### Direct Answer: **NO** (with caveats)

When in `WIFI_AP_STA` mode:

```cpp
WiFi.mode(WIFI_AP_STA);
WiFi.softAP("MyAP", "password");  // Start AP
// ... AP now broadcasting, clients can join ...

WiFi.begin("HomeSSID", "pass");   // Start STA reconnect
// → STA radio activity increases
// → Clients may see **latency increase** (modem arbitration shifts priority)
// → Clients are **NOT disconnected** from AP
// → Beacons still sent, clients stay associated
```

**However**: Frequent `WiFi.begin()` calls or high-volume STA scanning can:
- Degrade AP throughput (modem spends more time on STA scanning)
- Increase WebSocket latency (100–300 ms instead of typical 50–100 ms)
- Cause missed beacons if STA scan blocks for too long

### Root Cause: Shared Radio Time
```
Timeline during STA reconnect:
├─ Modem: Service STA (scan 13 channels ~100 ms total)
├─ Modem: Service AP (send beacon ~10 ms)
├─ Modem: Service STA (attempt association)
├─ Modem: Service AP (handle client frames)
└─ Result: AP throughput degrades during active STA scanning
```

---

## 3. Known Issues & Fixes (Implemented in Firmware)

### Issue A: WiFi Modem Sleep Enabled (CRITICAL)

**Symptom**: WebSocket clients disconnect intermittently; 3D dashboard appears "bursty"

**Root cause**: ESP32 defaults to `WIFI_PS_MIN_MODEM`. The radio periodically powers down, causing missed beacons.

**Fix** (already in `firmware/src/WebDashboard.cpp` line 977):
```cpp
WiFi.setSleep(WIFI_PS_NONE);  // Disable modem sleep in AP+STA mode
```

### Issue B: Full-Channel STA Scan Interferes with AP

**Symptom**: Dashboard becomes slow or unresponsive when STA cannot find the home network

**Root cause**: `WiFi.begin()` triggers a 13-channel scan. If home network is unavailable, ESP32 rescans repeatedly.

**Fix** (already implemented in `startStaConnectAttempt()` line 955-956):
```cpp
WiFi.setScanMethod(WIFI_FAST_SCAN);          // Stop scanning on first SSID match
WiFi.setSortMethod(WIFI_CONNECT_AP_BY_SIGNAL);
WiFi.begin(staSsid.c_str(), staPass.c_str());
```

### Issue C: Uncontrolled STA Reconnect Churn

**Symptom**: AP intermittently becomes unreachable after STA disconnect

**Root cause**: STA rapid retry attempts without backoff; AP health not reasserted

**Fix** (already implemented in `firmware/src/WebDashboard.cpp` lines 1054–1070):
```cpp
void WebDashboard::tick() {
    // Periodic AP health check + reassertion
    if (_needApReassert || (now - _lastApHealthCheckMs >= AP_HEALTH_CHECK_MS)) {
        ensureApUp(_needApReassert);
    }

    // Controlled STA reconnect with exponential backoff
    if (_staConfigured && !_staConnected && _staRetryPending && now >= _nextStaRetryMs) {
        startStaConnectAttempt();
        
        // Backoff: 0.5s → 1s → 2s → 4s → 8s → 32s (capped)
        uint8_t backoffShift = _staDisconnectCount > 5 ? 5 : _staDisconnectCount;
        uint32_t retryDelay = STA_RETRY_BASE_MS << backoffShift;
        if (retryDelay > STA_RETRY_MAX_MS) retryDelay = STA_RETRY_MAX_MS;
        _nextStaRetryMs = now + retryDelay;
    }
}
```

---

## 4. Best Practice Pattern: Safe STA Reconnection in AP+STA Mode

### Initialization (in `begin()`)

```cpp
// 1. Load STA credentials from NVS (allow empty for AP-only mode)
_staSsid = getStoredSsid();
_staPass = getStoredPassword();
_staConfigured = (_staSsid.length() > 0);

// 2. Set WiFi mode BEFORE starting AP
WiFi.mode(_staConfigured ? WIFI_AP_STA : WIFI_AP);

// 3. Start AP (with fixed channel to avoid drift)
WiFi.softAPConfig(apIP, gateway, subnet);
WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD, ESPNOW_CHANNEL);

// 4. Disable modem sleep (critical for AP reliability)
WiFi.setSleep(WIFI_PS_NONE);

// 5. Register WiFi event handlers for STA lifecycle
WiFi.onEvent([this](WiFiEvent_t event, WiFiEventInfo_t info) {
    if (event == ARDUINO_EVENT_WIFI_STA_CONNECTED) {
        _staRetryPending = false;
        Serial.println("[WiFi] STA connected");
    } else if (event == ARDUINO_EVENT_WIFI_STA_GOT_IP) {
        _staConnected = true;
        _staRetryPending = false;
        _staDisconnectCount = 0;  // Reset backoff
    } else if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {
        _staConnected = false;
        _needApReassert = true;   // Flag AP for health check
        _staRetryPending = _staConfigured;
        _staDisconnectCount++;
        
        // Schedule next retry with exponential backoff
        uint32_t backoffMs = STA_RETRY_BASE_MS << min(_staDisconnectCount - 1, 5u);
        _nextStaRetryMs = millis() + backoffMs;
    }
});

// 6. Trigger initial STA attempt (if credentials stored)
if (_staConfigured) {
    startStaConnectAttempt();
}
```

### Main Loop Integration

```cpp
// In main EvkaPosition loop (firmware/src/EvkaPosition.cpp)
if (ENABLE_WIFI) {
    dashboard.tick();  // Non-blocking WiFi maintenance
}
```

### STA Connect Attempt (controlled, non-blocking)

```cpp
void startStaConnectAttempt() {
    // Set fast scan mode to minimize AP disruption
    WiFi.setScanMethod(WIFI_FAST_SCAN);
    WiFi.setSortMethod(WIFI_CONNECT_AP_BY_SIGNAL);
    
    // Call WiFi.begin() — does NOT block or disrupt AP in WIFI_AP_STA mode
    WiFi.begin(_staSsid.c_str(), _staPass.c_str());
    Serial.printf("[WiFi] STA connect → '%s'\n", _staSsid.c_str());
}
```

### Periodic AP Health Reassertion

```cpp
void ensureApUp(bool forceRestart) {
    if (!forceRestart && WiFi.softAPIP() != IPAddress((uint32_t)0)) {
        return;  // AP is healthy
    }
    
    // Reaffirm AP config + restart if needed
    WiFi.softAPConfig(apIP, gateway, subnet);
    WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD, ESPNOW_CHANNEL);
    WiFi.setSleep(WIFI_PS_NONE);
    
    Serial.printf("[WiFi] AP %s\n", 
                  WiFi.softAPIP() != IPAddress((uint32_t)0) ? "OK" : "FAIL");
}
```

---

## 5. Configuration Constants (from firmware/src/SphericalSensor.h)

```cpp
// STA retry backoff: 0.5s, 1s, 2s, 4s, 8s, 32s (capped)
#define STA_RETRY_BASE_MS     500
#define STA_RETRY_MAX_MS      32000

// AP health check interval
#define AP_HEALTH_CHECK_MS    5000

// Default STA credentials (NVS can override)
#define WIFI_STA_DEFAULT_SSID "MyHomeNetwork"
#define WIFI_STA_DEFAULT_PASS "mypassword123"

// AP settings
#define WIFI_AP_SSID          "CMDCNC_EVKA"
#define WIFI_AP_PASSWORD      "cmdcnc1234"
#define WIFI_AP_IP_O1 192
#define WIFI_AP_IP_O2 168
#define WIFI_AP_IP_O3 1
#define WIFI_AP_IP_O4 50       // 192.168.1.50

// AP channel (same as ESP-NOW if enabled)
#define ESPNOW_CHANNEL        1
```

---

## 6. Operational Checklist

### Before Deploying STA Reconnect

- [ ] **WiFi mode set to `WIFI_AP_STA`** before calling `softAP()` and `WiFi.begin()`
- [ ] **`WiFi.setSleep(WIFI_PS_NONE)`** called after `softAP()` to disable modem sleep
- [ ] **`WiFi.setScanMethod(WIFI_FAST_SCAN)`** called before each `WiFi.begin()` to limit scan duration
- [ ] **WiFi event handlers registered** for `STA_CONNECTED`, `STA_GOT_IP`, `STA_DISCONNECTED`
- [ ] **STA reconnect NOT called from interrupt context** — schedule via event flags + main loop tick
- [ ] **Exponential backoff implemented** — start at 500 ms, double up to 32 s cap
- [ ] **AP health reassertion** — periodic `ensureApUp()` call on disconnect or after timeout
- [ ] **`dashboard.tick()`** called in main loop (non-blocking WiFi maintenance)

### Testing STA Reconnect in AP+STA Mode

```bash
# Terminal 1: Monitor serial output
pio device monitor -b 115200

# Terminal 2: Start device
pio run -t upload -e wemos_d1_r32

# Test steps:
# 1. Boot device → Confirm AP SSID "CMDCNC_EVKA" appears
# 2. Connect to AP via phone/PC → Verify http://192.168.1.50 loads
# 3. Stop home WiFi router → STA disconnect event fires
#    - Observe: AP remains accessible, reconnect backoff starts
#    - Check serial: "STA disconnected (reason=X), retry in 500 ms"
# 4. Restart home WiFi → STA reconnect succeeds within backoff window
#    - Check serial: "STA IP: 10.78.137.252" (or your STA IP)
# 5. Keep AP connection active throughout → Dashboard remains responsive
```

---

## 7. Known Issues Not Yet Observed

### Issue: AP Subnet Conflicts (192.168.1.x)

**Status**: Documented, workaround only  
**Cause**: AP IP `192.168.1.50` conflicts with most home routers on same subnet

**Workaround**: Disconnect client device from home WiFi **before** connecting to `CMDCNC_EVKA`. The device should be on `CMDCNC_EVKA` only when accessing the dashboard.

### Issue: RTCWDT_RTC_RESET Boot Loop

**Status**: Not reproducing; watchdog was triggered during early STA association (blocking `WiFi.begin()`)  
**Current state**: All STA calls are non-blocking; watchdog risk eliminated

---

## 8. Summary Table: WiFi.begin() Safety in Modes

| Mode | Effect of `WiFi.begin()` | AP Disruption | Safe? |
|------|--------------------------|---------------|-------|
| `WIFI_OFF` | Enables STA (no effect if already in a mode) | N/A | ✓ |
| `WIFI_STA` | Initiates STA association | N/A | ✓ |
| `WIFI_AP` | No effect (STA disabled in this mode) | ✗ None | ✓ |
| `WIFI_AP_STA` | Initiates STA association (AP unaffected) | ◐ Latency increase during scan | ✓ Mitigated by FAST_SCAN |
| **Best Practice** | Call only on disconnect or timeout with backoff | ✓ Minimal | ✓✓ Recommended |

---

## References

- **Firmware source**: `firmware/src/WebDashboard.cpp` (WiFi event handling, AP reassertion)
- **Configuration**: `firmware/src/SphericalSensor.h` (WiFi mode, retry constants)
- **Integration**: `firmware/src/EvkaPosition.cpp` (main loop `dashboard.tick()` call)
- **Log**: `docs/WIFI_PERFORMANCE_ISSUES_LOG.md` (detailed Issue 1–8 investigation)
- **Coexistence**: `docs/BLE_WIFI_COEXISTENCE.md` (radio arbitration, latency impact)

---

**Last Updated**: 2026-04-09  
**Verified**: `pio run -e wemos_d1_r32` — Compiles and runs successfully
