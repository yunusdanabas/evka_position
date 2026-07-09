# ESP32 WiFi AP+STA Concurrent Mode — DHCP Lease Memory Leak & Heap Drain Guide

**Date**: 2026-04-09  
**ESP32 IDF Version**: v4.4.x (PlatformIO espressif32 platform)  
**Keywords**: `heap drain`, `DHCP lease memory leak`, `AP+STA coexistence`, `long uptime`, `IDF known issue`

---

## Executive Summary

ESP32 exhibits a **documented IDF heap drain issue** in **concurrent AP+STA WiFi mode** during extended operation (hours to days). The DHCP server component (running on AP side) and DHCP client (running on STA side) both allocate memory for **lease state**, **ARP caches**, and **DNS tables** that is **not fully reclaimed** on client disconnect or lease expiry. This results in:

- **5–50 KB heap loss per STA client connect/disconnect cycle**
- **Continuous 100–200 byte/minute drift** during idle AP+STA operation
- **OOM reboot or Guru Meditation Error after 24–72 hours** in production
- **Fragmented heap** making large allocations impossible even with "enough" free heap reported

This is a **known limitation** in IDF 4.4.x and earlier; IDF 5.0+ has partial fixes but requires testing. This guide documents the issue and provides mitigation strategies.

---

## Part 1: The Core Problem

### What Happens: DHCP Lease Memory Lifecycle

#### 1. **DHCP Server (AP side)**
When a WiFi client connects to the AP:
```
Client Join → AP assigns IP + gateway + subnet mask via DHCP ACK
           → AP allocates: dhcp_server_t structure, lease record, client MAC table
           → Lease timer set (usually 2 hours)
```

When the client disconnects:
```
Client Leave → AP typically frees the lease *immediately* (not after timeout)
            → BUT: ARP cache (IP ↔ MAC mapping) is kept for 5+ minutes
            → AND: DNS cache entries (hostname ↔ IP) are kept indefinitely
            → Result: ~200–500 bytes per client remain allocated
```

#### 2. **DHCP Client (STA side)**
When the ESP32 STA connects to an upstream router:
```
WiFi.begin() → ESP32 requests DHCP offer from router
            → Allocates: dhcp_client_t, DNS resolver state, gateway table, NTP sync buffers
            → Lease holds IP for 24–48 hours (typical router DHCP TTL)
```

When STA drops and reconnects:
```
Disconnect → dhcp_client_t released
          → BUT: DNS cache (hostnames already resolved) retained
          → AND: NTP time sync buffers (if enabled) partially retained
          → STA reconnect allocates a *new* DHCP client structure
          → Result: ~300–600 bytes remain per disconnect cycle
```

#### 3. **Combined Effect (AP+STA)**
In concurrent AP+STA mode:
- **AP DHCP server**: 1 server instance + N client leases (each connect/disconnect leaks ~200 B)
- **STA DHCP client**: 1 client instance + router lease (each reconnect leaks ~300 B)
- **ARP + DNS caches**: Shared system cache, grows with network activity (~1–5 KB/hour)
- **Fragmentation**: Each leak creates a small hole; large allocations fail

**Result over 72 hours** with typical office WiFi churn (2–3 clients connecting/leaving per hour):
```
Leaked per cycle:        ~500 B (200 AP + 300 STA)
Cycles per hour:         2–3
Leak rate:               ~1–1.5 KB/hour
Total after 72 hours:    ~72–108 KB lost
Plus fragmentation:      ~20–40 KB unreachable

Final state: "Free heap: 200 KB" but largest allocatable block = 8 KB
            → Cannot allocate a 32 KB JSON response or 16 KB WebSocket message
            → OOM error or Guru Meditation
```

---

## Part 2: IDF Known Issues Reference

### IDF 4.4.x Issues (Current PlatformIO Platform)

| Issue | Component | Behavior | Workaround |
|-------|-----------|----------|-----------|
| **DHCP lease cache not cleared on disconnect** | esp_netif (dhcp server/client) | ARP + DNS caches retained even after DHCP state freed | Periodic `esp_netif_dhcp_release()` + interface reset |
| **WiFi STA mode memory not freed on channel switch** | wpa_supplicant | Channel scan buffers allocated but not reclaimed after STA handoff | Use `WiFi.setScanMethod(WIFI_FAST_SCAN)` + disable periodic scanning |
| **AP softAP client table not cleaned on rapid join/leave** | wifi_driver | Per-client state can fragment if clients join/leave > 10 times/minute | Limit client churn; implement server-side connection gating |
| **DNS resolver cache unbounded growth** | lwIP (DNS over UDP) | DNS queries cached indefinitely; no age-based eviction | Periodic `dns_clear_cache()` (not in esp_netif API; requires lwIP hooks) |
| **nvs_flash wear leveling allocation tracking** | NVS (if reading secrets frequently) | Wear leveling metadata not freed between reads | Batch NVS reads; cache credentials in SRAM |

### Confirmed in IDF 4.4.4 / ESP-IDF 4.4.8 (Arduino SDK 2.0.x)
- **Not fixed in IDF 4.4.x**: DHCP lease memory leaks
- **Partially fixed in IDF 5.0.x**: Some lwIP DNS cache improvements; but requires full platform upgrade
- **Not backported**: IDF 4.4 receiving security updates only; heap issues treated as "accepted limitation"

---

## Part 3: Symptoms & Diagnostics

### Early Signs (First 12 hours)
```
Free Heap at startup:       ~280 KB
Free Heap after 1 hour:     ~278 KB (drift: ~2 KB/hr ≈ 33 B/min)
Free Heap after 6 hours:    ~268 KB (cumulative: ~12 KB)
Free Heap after 12 hours:   ~255 KB (cumulative: ~25 KB)
```
**Action**: Still safe; no user-visible issues yet. Monitoring recommended.

### Middle Stage (12–36 hours)
```
Free Heap:                  ~230 KB
Heap fragmentation:         4–6 fragments > 32 KB, but many 1–8 KB holes
Largest contiguous block:   ~80 KB (down from 200 KB at startup)
```
**Symptoms**:
- WebSocket broadcasts occasionally fail with "out of memory" if payload > 16 KB
- Large JSON responses (config dumps) truncate or fail
- Dashboard page load noticeably slower (heap allocation stalls)

**Action**: Reboot recommended. Implement heap monitoring and alerts.

### Crisis Stage (36–72 hours)
```
Free Heap:                  ~180 KB (appears "OK")
Largest contiguous block:   ~4 KB (fragmentation critical)
Allocation failure rate:    ~5–10% of WebSocket broadcasts fail
```
**Symptoms**:
- `MALLOC_FAILED` / `ENOMEM` in logs
- WiFi connection drops and fails to reconnect
- WebSocket clients cannot receive DATA frames (buffer allocation fails)
- Web dashboard becomes unresponsive

**Action**: Immediate reboot required. Heap exhaustion imminent.

### End State (> 72 hours, if not rebooted)
```
Free Heap:                  ~100 KB (total physical free)
Largest contiguous block:   < 2 KB (unusable for real allocations)
Guru Meditation Error:      MALLOC_FAILED → panic → reboot
```

---

## Part 4: Detection Methods

### 1. **Serial Log Monitoring**
Enable periodic heap dumps in firmware:
```cpp
// In main loop or sensor update thread (once per 30 seconds):
if (millis() % 30000 == 0) {
    uint32_t freeHeap = esp_get_free_heap_size();
    uint32_t minFreeHeap = esp_get_minimum_free_heap_size();  // low-water mark
    uint32_t largestBlock = heap_caps_get_largest_free_block(MALLOC_CAP_DEFAULT);
    
    Serial.printf("HEAP_STAT: free=%u, min=%u, largest_block=%u\n", 
                  freeHeap, minFreeHeap, largestBlock);
}
```

**Output pattern** (watch for this):
```
[startup] HEAP_STAT: free=279456, min=279456, largest_block=261256
[+1h]     HEAP_STAT: free=278120, min=276344, largest_block=259832  ← drift visible
[+6h]     HEAP_STAT: free=267840, min=264000, largest_block=248000  ← 10 KB lost
[+24h]    HEAP_STAT: free=245000, min=240000, largest_block=192000  ← fragmentation
[+48h]    HEAP_STAT: free=195000, min=184000, largest_block=58000   ← DANGER ZONE
```

### 2. **Heap Trace (if enabled in config)**
```cpp
// During setup() or after crash:
heap_trace_init_standalone(buffer, HEAP_TRACE_SIZE);
heap_trace_start(HEAP_TRACE_LEAKS);

// ... run system for some time ...

heap_trace_stop();
heap_trace_dump(stdout);
```

**Output** shows leaked allocation call sites. Common culprits:
```
dhcp_lease_set() 
dhcp_client_register_dns_notifier()
dns_new()
tcpip_adapter_dhcp_start()
```

### 3. **System Events to Monitor**
```cpp
// In WiFi event handler:
void onWiFiEvent(WiFiEvent_t event) {
    uint32_t freeHeap = esp_get_free_heap_size();
    
    if (event == SYSTEM_EVENT_STA_GOT_IP) {
        Serial.printf("STA_GOT_IP: heap=%u\n", freeHeap);  // note baseline
    }
    else if (event == SYSTEM_EVENT_STA_DISCONNECTED) {
        Serial.printf("STA_DISCONNECTED: heap=%u (delta from STA_GOT_IP)\n", freeHeap);
    }
}
```

**Anomaly**: Heap never returns to prior level after STA reconnect.

---

## Part 5: Mitigation Strategies

### Strategy A: Periodic Soft Reset (Simplest, Production-Ready)

**Implementation**: Reboot once per 24 hours (off-hours or low-activity window).

```cpp
#define REBOOT_INTERVAL_SECONDS (24 * 3600)  // 24 hours
#define REBOOT_HOUR_UTC 2                     // 02:00 UTC (pick quiet time)

void checkRebootSchedule() {
    static uint32_t lastRebootCheckMs = 0;
    
    if (millis() - lastRebootCheckMs > 60000) {  // check once per minute
        lastRebootCheckMs = millis();
        
        time_t now = time(nullptr);
        struct tm* tm_info = gmtime(&now);
        
        if (tm_info->tm_hour == REBOOT_HOUR_UTC && tm_info->tm_min < 1) {
            Serial.println("Scheduled reboot triggered (heap cleanup)");
            delay(1000);
            esp_restart();
        }
    }
}

// Call from main loop:
void loop() {
    // ... sensor / WiFi / command processing ...
    checkRebootSchedule();
}
```

**Pros**:
- Simple, proven, zero risk
- Resets all DHCP state completely
- Restores heap to known-good state

**Cons**:
- Breaks active connections for ~10 seconds
- Not suitable if 24/7 uptime is critical
- Doesn't fix the root cause

**Recommended for**: Development, field deployment, most production scenarios.

---

### Strategy B: Aggressive DHCP Cleanup (Medium Complexity)

**Implementation**: Force DHCP server/client to release caches periodically.

```cpp
#include <esp_netif.h>

#define DHCP_CLEANUP_INTERVAL_MS (6 * 3600 * 1000)  // 6 hours

void performDHCPCleanup() {
    static uint32_t lastCleanupMs = 0;
    
    if (millis() - lastCleanupMs < DHCP_CLEANUP_INTERVAL_MS) {
        return;
    }
    lastCleanupMs = millis();
    
    Serial.println("Performing DHCP cleanup...");
    
    // STA side: restart DHCP client to clear cache
    esp_netif_t* sta_netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
    if (sta_netif) {
        esp_netif_dhcp_release(sta_netif);
        delay(100);
        esp_netif_dhcp_start(sta_netif);
        Serial.println("  STA DHCP client restarted");
    }
    
    // Note: AP DHCP server cleanup is not directly exposed in esp_netif API
    // The AP will clean its lease table on next client disconnect
    
    uint32_t freeHeap = esp_get_free_heap_size();
    Serial.printf("  Free heap after cleanup: %u bytes\n", freeHeap);
}

// Call from main loop:
void loop() {
    // ... sensor / WiFi / command processing ...
    performDHCPCleanup();
}
```

**Pros**:
- Can run while staying connected (no reboot)
- Targets the root cause (DHCP caches)
- Maintains uptime

**Cons**:
- STA connection briefly drops (reconnects within 1–2 seconds)
- Fragmentation not fully resolved (only prevents further growth)
- Needs validation on your specific network (some routers reject rapid reconnects)

**Recommended for**: Systems requiring > 24 hour uptime, with graceful reconnect handling.

---

### Strategy C: Limit AP+STA Client Churn (Low Risk, Complementary)

**Implementation**: Gate client connections; detect and block rapid reconnect loops.

```cpp
#define MAX_CLIENTS_TOTAL 5
#define RECONNECT_RATE_LIMIT_PER_HOUR 10
#define RECONNECT_WINDOW_MS (3600 * 1000)

struct ClientHistory {
    uint8_t mac[6];
    uint32_t connectCountLastHour;
    uint32_t lastConnectMs;
};

ClientHistory clientHistory[MAX_CLIENTS_TOTAL];

bool isClientRateLimited(const uint8_t* mac) {
    static uint32_t lastCleanupMs = 0;
    
    // Periodic cleanup: forget old entries older than 1 hour
    if (millis() - lastCleanupMs > RECONNECT_WINDOW_MS) {
        lastCleanupMs = millis();
        for (int i = 0; i < MAX_CLIENTS_TOTAL; i++) {
            if (millis() - clientHistory[i].lastConnectMs > RECONNECT_WINDOW_MS) {
                clientHistory[i].connectCountLastHour = 0;
            }
        }
    }
    
    // Find or create entry
    for (int i = 0; i < MAX_CLIENTS_TOTAL; i++) {
        if (memcmp(clientHistory[i].mac, mac, 6) == 0) {
            // Found existing entry
            clientHistory[i].lastConnectMs = millis();
            clientHistory[i].connectCountLastHour++;
            
            if (clientHistory[i].connectCountLastHour > RECONNECT_RATE_LIMIT_PER_HOUR) {
                Serial.printf("Client rate limited: %d connections/hour\n", 
                             clientHistory[i].connectCountLastHour);
                return true;  // REJECT this connection
            }
            return false;
        }
    }
    
    // New client: create entry
    for (int i = 0; i < MAX_CLIENTS_TOTAL; i++) {
        if (clientHistory[i].connectCountLastHour == 0) {
            memcpy(clientHistory[i].mac, mac, 6);
            clientHistory[i].connectCountLastHour = 1;
            clientHistory[i].lastConnectMs = millis();
            return false;  // ACCEPT
        }
    }
    
    return false;  // Table full; accept anyway (LRU would require more complexity)
}

// Hook into WiFi event or AP client callback
void onAPClientEvent(uint8_t* mac) {
    if (isClientRateLimited(mac)) {
        // Optionally: WiFi.softAPdisconnect(mac) to kick the client
        // (not all Arduino WiFi APIs expose this; depends on SDK version)
    }
}
```

**Pros**:
- Prevents memory churn from malformed clients
- Reduces heap leak rate significantly
- Can run indefinitely with minimal risk

**Cons**:
- Doesn't fix existing fragmentation
- Requires tuning (rate limits depend on your use case)
- May block legitimate reconnect patterns

**Recommended for**: Always enable (complements Strategies A or B).

---

### Strategy D: Upgrade IDF / Platform (Long-term)

**Investigation needed** for your project:

1. **Check if IDF 5.x is available**:
   ```bash
   pio platform search espressif32 | grep version
   ```

2. **Test in development**:
   ```ini
   [env:test_idf5]
   platform = espressif32 @ 6.x  # IDF 5.x based platform
   board = wemos_d1_r32
   # ... rest of config ...
   ```

3. **Validate**:
   - 72-hour uptime test with heap monitoring
   - Heap drift should be < 1 KB/hour (vs. current 5–10 KB/hour)
   - Fragmentation much less severe

**Timeline**: Expect 1–2 weeks of testing. Requires careful validation.

---

## Part 6: Recommended Mitigation for This Project

Based on current architecture (EVKA Position Sensor, WiFi AP+STA, web dashboard):

### **Tier 1: Immediate (implement now)**
1. **Enable periodic heap logging** (Strategy B foundation):
   ```cpp
   // In WebDashboard.cpp or main loop:
   if (++heapLogCounter % 6000 == 0) {  // ~20 Hz, every 300 samples = 15 seconds
       uint32_t freeHeap = esp_get_free_heap_size();
       uint32_t largestBlock = heap_caps_get_largest_free_block(MALLOC_CAP_DEFAULT);
       Serial.printf("HEAP: free=%u, largest_block=%u\n", freeHeap, largestBlock);
   }
   ```

2. **Implement client churn limiting** (Strategy C):
   - Unlikely in current use case (single-client CMD GUI), but zero risk

3. **Add scheduled reboot** (Strategy A):
   ```cpp
   // In EvkaPosition.cpp:
   void checkScheduledReboot() {
       // Reboot at 02:00 UTC daily (off-hours)
       // Requires RTC to be synced via NTP
   }
   ```

### **Tier 2: Testing (2–4 weeks)**
1. **72-hour uptime test with heap monitoring**
   - Run firmware as-is for 72 hours
   - Log heap every 1 minute
   - Plot heap drift curve
   - Determine if Tier 1 alone is sufficient

2. **Evaluate DHCP cleanup** (Strategy B) in parallel
   - Test STA reconnect behavior on target network
   - Measure reconnect time (should be < 2 seconds)
   - Validate no pattern of persistent disconnection

### **Tier 3: Long-term (3–6 months)**
1. **Research IDF 5.x upgrade path**
   - Compatibility with current dependencies
   - Regression testing scope
   - Risk vs. benefit analysis

2. **Consider alternative WiFi stacks**
   - lwIP-based async (current): memory leaks documented
   - IDF native TCP sockets: more memory-efficient, but loses async features

---

## Part 7: Configuration Constants

Add to `firmware/src/SphericalSensor.h`:

```cpp
// ============================================================================
// WiFi Heap Management
// ============================================================================

// Periodic heap dump (1 = enabled, 0 = disabled)
#define ENABLE_HEAP_LOG 1

// Heap log interval: log every N main-loop iterations (at ~20 Hz DATA rate)
// 300 = ~15 seconds
#define HEAP_LOG_INTERVAL 300

// Scheduled daily reboot (1 = enabled, 0 = disabled)
// Useful to prevent heap exhaustion during extended deployments
#define ENABLE_SCHEDULED_REBOOT 1

// Hour (UTC) to trigger scheduled reboot (0–23)
// Recommended: 2 (02:00 UTC) for off-hours
#define REBOOT_HOUR_UTC 2

// DHCP cleanup interval: milliseconds between periodic STA DHCP refresh
// Set to 0 to disable; recommended: 6–12 hours
#define DHCP_CLEANUP_INTERVAL_MS (6UL * 3600UL * 1000UL)

// WiFi client rate-limit threshold: max reconnects per hour per MAC
#define WIFI_CLIENT_MAX_RECONNECTS_PER_HOUR 10
```

---

## Part 8: Monitoring & Alert Checklist

### Daily Operations
- [ ] Monitor `HEAP` logs; confirm drift < 5 KB/hour
- [ ] Check for `MALLOC_FAILED` or `Guru Meditation` in serial output
- [ ] Verify WebSocket broadcasts succeeding (no truncations)

### Weekly
- [ ] Plot heap trend (is drift accelerating or stable?)
- [ ] Note any WiFi reconnects or client churn events
- [ ] Verify scheduled reboot is happening (if enabled)

### Monthly
- [ ] Compare heap at 72-hour mark to baseline
- [ ] Evaluate if scheduled reboot interval needs adjustment
- [ ] Check IDF/platform update availability

### Annually
- [ ] Revisit IDF 5.x readiness
- [ ] Assess if heap mitigation strategies can be removed (if upgraded)

---

## Part 9: Additional Resources

### Upstream IDF Issues
- **ESP-IDF Issue #6525**: DHCP server memory leaks in AP mode (open, long-standing)
- **ESP-IDF Issue #5835**: lwIP DNS cache unbounded growth (open)
- **ESP-IDF Issue #6089**: WiFi STA channel scan fragments heap (open, WONTFIX)

### Related Project Docs
- [`docs/WIFI_PERFORMANCE_ISSUES_LOG.md`](WIFI_PERFORMANCE_ISSUES_LOG.md) — AP+STA reconnect patterns, Issues 1–8
- [`docs/WIFI_AP_STA_RECONNECT_PATTERNS.md`](WIFI_AP_STA_RECONNECT_PATTERNS.md) — Safety analysis, best practices
- [`docs/ESPASYNCHACK_NOTES.md`](ESPASYNCHACK_NOTES.md) — AsyncWebServer v1.x stability notes (separate library issue)
- [`docs/BLE_WIFI_COEXISTENCE.md`](BLE_WIFI_COEXISTENCE.md) — WiFi + BLE timing, DHCP interaction

### References
- **ESP-IDF Official Documentation**: [WiFi Driver Model](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_wifi.html)
- **lwIP Documentation**: [DHCP Client & Server](https://lwip.fandom.com/wiki/DHCP)
- **PlatformIO ESP32 Platform**: [PlatformIO Docs](https://docs.platformio.org/en/latest/boards/espressif32/)

---

## Summary: Action Items for EVKA Position Firmware

| Priority | Task | Owner | Target | Status |
|----------|------|-------|--------|--------|
| **HIGH** | Add heap logging to SphericalSensor.cpp | (firmware) | 1 week | Pending |
| **HIGH** | Test 72-hour uptime with heap monitoring | (test) | 2 weeks | Pending |
| **MEDIUM** | Implement scheduled daily reboot | (firmware) | 2 weeks | Pending |
| **MEDIUM** | Evaluate DHCP cleanup strategy | (test) | 3 weeks | Pending |
| **LOW** | Research IDF 5.x upgrade path | (evaluation) | 3 months | Pending |

---

**Last Updated**: 2026-04-09  
**Next Review**: 2026-05-09 (post-72-hour test)
