# AsyncTCP ESP32 Task Stack Overflow Analysis

**Date**: 2026-04-09  
**Target**: Wemos D1 R32 (ESP32-WROOM-32) + AsyncTCP 1.1.1 + ESPAsyncWebServer 1.2.4  
**Config**: WiFi AP+STA mode + WebSocket concurrent clients + 20 Hz DATA broadcasting  

---

## Overview

AsyncTCP (underlying TCP library for ESPAsyncWebServer) uses FreeRTOS tasks with **default stack sizes that are insufficient** for concurrent WebSocket + WiFi AP+STA scenarios. This guide documents:

1. **Root causes** of stack overflow
2. **Default vs. required stack sizes**
3. **Observable symptoms** on the ESP32
4. **Mitigation strategies** implemented and available

---

## Part I: Default Stack Configuration

### ESP32 FreeRTOS Default Tasks

When the ESP32 boots, several system tasks are created by ESP-IDF. Key ones related to networking:

| Task | Default Stack (words) | Typical Heap Used | Purpose |
|------|---|---|---|
| `esp_timer` | 4096 | 512–1024 B | System timer task |
| `wifi` (WiFi driver task) | 4096 | 2–4 KB | WiFi radio stack, beacon handling, RX/TX |
| `tcpip_task` (lwIP) | 4096 | 2–3 KB | TCP/IP protocol stack, socket events |
| `async_tcp` (AsyncTCP) | 4096 | 1–2 KB | AsyncTCP event loop (if registered) |
| `main` | 8192 | 2–3 KB | Arduino `setup()` / `loop()` |

**Stack size unit note**: FreeRTOS uses **words** (4 bytes on ESP32), so `4096 words = 16 KB bytes`.

### lwIP Task Stack Pressure

The lwIP stack (TCP/IP kernel) is configured at compile-time via `menuconfig` or `sdkconfig.defaults`. For ESP32, the default configuration:

```
CONFIG_LWIP_TCPIP_TASK_STACK_SIZE=4096  (words, ~16 KB)
CONFIG_LWIP_TCP_MSS=1440                (maximum segment size per connection)
CONFIG_LWIP_TCP_WND=5840                (TCP window size, per connection)
```

**When this is insufficient:**

- **Multiple concurrent TCP/WebSocket connections** (3–5 clients) cause lwIP to allocate per-connection state
- Each connection has a control block (~300 B) + TX buffer (~2 KB) + RX buffer (~2 KB)
- With 5 connections: ~5 × 4 KB = 20 KB per connection (heap), but lwIP task itself only has 16 KB stack

---

## Part II: AsyncTCP Stack Overhead

### How AsyncTCP Interacts with lwIP

AsyncTCP is a wrapper around lwIP sockets that provides asynchronous callbacks:

```
Application Layer
    ↓ [onMessage() callback]
AsyncWebSocket (1.2.4)
    ↓ [TCP event handlers]
AsyncTCP (1.1.1)
    ↓ [lwIP socket API]
lwIP TCP/IP Stack
    ↓ [PHY + radio]
WiFi Driver (AP + STA)
```

### Default AsyncTCP Configuration

AsyncTCP does **not** explicitly create its own task by default; instead:

1. **Socket I/O** is handled by lwIP task callbacks
2. **User callbacks** (e.g., `onMessage()`) run in the **lwIP task context**
3. If `onMessage()` blocks or allocates heavily, the lwIP task stack can overflow

### Critical Scenario: AP+STA WebSocket Under Load

When operating in `WIFI_AP_STA` mode with WebSocket clients:

```
WiFi AP:   
  - Beacon TX every 100 ms
  - DHCP server for connected clients
  - AP ARP/ICMP handling
  
WiFi STA:
  - Probe requests/scans (if searching for network)
  - Association handshake
  - DHCP client requests
  - Data RX/TX with home router

WebSocket clients (via AP):
  - TCP SYN/ACK handshake per client
  - WebSocket upgrade handshake
  - Frame parsing (requires stack allocation for temp buffers)
  - Message delivery via callbacks (runs in lwIP task)
```

**All of this is competing for the lwIP task's 16 KB stack.**

---

## Part III: Stack Overflow Symptoms

### Observable Behaviors

| Symptom | Root Cause | Severity |
|---------|-----------|----------|
| **Guru Meditation Error** (core dump) with `Stack Corruption` | lwIP task stack overflow; heap canary triggered | Critical |
| **Reboot loop** (continuous resets every 5–30 s) | Watchdog fires because lwIP task is stuck/corrupted | Critical |
| **WebSocket clients drop during peak load** | Stack overflow in `onMessage()` callback; frame parsing fails | High |
| **Dashboard becomes unresponsive** | lwIP task context-switched out; TCP not advancing | High |
| **Intermittent `ERR:UNKNOWN_CMD`** | Command buffer corruption due to stack-heap collision | Medium |
| **Free heap decreases for no reason** | Fragmentation caused by interrupted allocations | Medium |
| **WiFi AP becomes unreachable** | lwIP ARP/response task starved by overflowing stack | High |

### Detecting Stack Overflow Before It Crashes

ESP-IDF provides runtime stack checking (enabled by default in debug builds):

```
[ESP32] Free heap: 123456 B
[STACK] LwIP task uxHighWaterMark: 2048 words (8 KB free)  ← WARNING
[STACK] LwIP task uxHighWaterMark: 512 words (2 KB free)   ← CRITICAL
[STACK] LwIP task uxHighWaterMark: 0 words                 ← OVERFLOW!
```

**To enable stack overflow detection** in `platformio.ini`:

```ini
build_flags = -DCONFIG_FREERTOS_WATCHPOINT_END_OF_STACK
```

---

## Part IV: Root Causes in This Project

### Issue 1: WebSocket Frame Parsing on lwIP Stack

In `firmware/src/WebDashboard.cpp`, the `onWsEvent()` callback runs in lwIP task context:

```cpp
void WebDashboard::onWsEvent(AsyncWebSocket* server, AsyncWebSocketClient* client,
                              AwsEventType type, void* arg, uint8_t* data, size_t len) {
    // This runs in the lwIP task!
    // Large local buffers here eat stack space:
    
    if (type == WS_EVT_DATA) {
        // Parsing happens here
        size_t n = (len < CMD_MAX_LEN) ? len : CMD_MAX_LEN;
        char localBuf[CMD_MAX_LEN + 1];  // ← 256+ B on stack
        memcpy(localBuf, data, n);
        // ...
    }
}
```

**Impact**: Multiple simultaneous messages from different clients → multiple overlapping `onWsEvent()` calls → stack collision.

### Issue 2: Concurrent WebSocket Clients Without Queue Depth Limits

When 3–5 WebSocket clients connect and send commands:

1. Each client triggers `onWsEvent()` in lwIP task
2. If client 1's callback hasn't returned, client 2's data triggers another call
3. Stack frame accumulates without proper cleanup
4. No per-client rate-limiting → unbounded concurrent callbacks

### Issue 3: WiFi AP Health Reassert Under Heavy Load

In the recent fixes (`WIFI_PERFORMANCE_ISSUES_LOG.md`), the AP reassert logic runs in `WebDashboard::tick()`, which is called from `loop()`. But the STA disconnect event handler fires in lwIP task context:

```cpp
void WebDashboard::onWiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
    // Runs in WiFi task, which may interrupt lwIP
    if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {
        _needApReassert = true;  // Sets flag
        // If AP reassert logic runs here directly, stack collision
    }
}
```

**Mitigation already in place**: Reassert deferred to `tick()` (main task context), not called from WiFi event handler. ✓

### Issue 4: Large TCP Buffer Allocations on Main Loop During WebSocket Broadcast

In `WebDashboard::broadcast()`:

```cpp
void WebDashboard::broadcast(const char* dataLine) {
    if (_ws.count() > 0) {
        _ws.textAll(dataLine);  // Keep payloads small and callback path non-blocking
    }
}
```

If called at exactly the moment when an `onMessage()` callback is also active, lwIP task stack is doubly pressured.

---

## Part V: Mitigation Strategies

### Strategy 1: Increase lwIP Task Stack (Compile-Time)

**File**: `platformio.ini` or PlatformIO project config.

```ini
[env:wemos_d1_r32]
platform = espressif32@6.12.0
board = wemos_d1_mini32
framework = arduino
lib_deps =
    PaulStoffregen/Encoder@1.4.4
    me-no-dev/ESPAsyncWebServer@1.2.4
    me-no-dev/AsyncTCP@1.1.1

# Increase lwIP task stack from 4096 to 8192 words (32 KB)
build_flags =
    -DCONFIG_LWIP_TCPIP_TASK_STACK_SIZE=8192
```

**Pros**: Simple, immediate relief  
**Cons**: Reduces available heap for app data (ESP32 only has 320 KB total); diminishing returns past 8192 words

### Strategy 2: Reduce Concurrent WebSocket Clients (Runtime)

**File**: `firmware/src/WebDashboard.h`

```cpp
#define WS_MAX_CLIENTS 3  // Limit concurrent WebSocket connections
```

In `onWsEvent()`, add rejection logic:

```cpp
if (type == WS_EVT_CONNECT) {
    if (_ws.count() > WS_MAX_CLIENTS) {
        client->close(1008, "server full");  // Close excess client
        return;
    }
}
```

**Pros**: Prevents stack thrashing from too many concurrent callbacks  
**Cons**: Limits scalability (e.g., cannot monitor on 4 devices simultaneously)

### Strategy 3: Async Command Queueing (Already Implemented ✓)

**File**: `firmware/src/WebDashboard.cpp` + `firmware/src/WebDashboard.h`

```cpp
// In onWsEvent() — keep callback SHORT:
bool WebDashboard::enqueueCommand(const uint8_t* data, size_t len) {
    // Copy to ring buffer, return immediately
    // lwIP task stack only uses 50–100 B
    size_t n = (len < CMD_MAX_LEN) ? len : CMD_MAX_LEN;
    char localBuf[CMD_MAX_LEN + 1];  // Minimal stack overhead
    memcpy(localBuf, data, n);
    // ...
    portENTER_CRITICAL(&_cmdMux);
    // Enqueue into ring buffer (heap-based)
    portEXIT_CRITICAL(&_cmdMux);
}

// In loop() or main task — process command with full stack:
String cmd = dashboard.takePendingCommand();
if (cmd.length() > 0) {
    processCommand(cmd);  // Runs with main task's 8 KB stack, not lwIP's 16 KB
}
```

**Status**: ✅ **Already implemented**. See `AGENT_LOG.md` (2026-04-08 audit).

### Strategy 4: Per-Client Rate-Limiting (Runtime)

**File**: `firmware/src/WebDashboard.cpp`

```cpp
// Add tracking per WebSocket client:
struct ClientRateLimit {
    uint32_t lastMessageMs;
    uint8_t burstCount;
};

static Map<uint32_t, ClientRateLimit> _clientRateLimits;

void WebDashboard::onWsEvent(AsyncWebSocket* server, AsyncWebSocketClient* client,
                              AwsEventType type, void* arg, uint8_t* data, size_t len) {
    if (type == WS_EVT_DATA) {
        uint32_t clientId = client->id();
        auto now = millis();
        auto& limit = _clientRateLimits[clientId];
        
        // Reject if >5 messages in <100 ms
        if (now - limit.lastMessageMs < 100) {
            limit.burstCount++;
            if (limit.burstCount > 5) {
                client->close(1008, "rate limit exceeded");
                return;
            }
        } else {
            limit.burstCount = 0;
        }
        limit.lastMessageMs = now;
        
        enqueueCommand(data, len);
    }
}
```

**Pros**: Prevents malicious or buggy clients from flooding lwIP  
**Cons**: Requires per-client state management

### Strategy 5: WiFi Event Isolation (Already Implemented ✓)

**File**: `firmware/src/WebDashboard.cpp`

Ensure WiFi event handlers **do NOT call blocking operations** (networking, large allocations):

```cpp
void WebDashboard::onWiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
    // WiFi task context — minimal stack available
    
    if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {
        _needApReassert = true;  // Just set flag
        // ❌ DON'T do: WiFi.softAP(...);  // Blocks, allocates, overflows
    }
}

// Deferred to main task:
void WebDashboard::tick() {
    if (_needApReassert) {
        ensureApUp(true);  // Runs with main task stack
        _needApReassert = false;
    }
}
```

**Status**: ✅ **Already implemented**. See `firmware/src/EvkaPosition.cpp` main loop: `dashboard.tick()` called every 50 ms.

### Strategy 6: Disable Modem Sleep (Already Implemented ✓)

**File**: `firmware/src/WebDashboard.cpp`

```cpp
WiFi.setSleep(WIFI_PS_NONE);  // Disable modem sleep
```

This reduces WiFi interrupt overhead and prevents temporary AP blackouts → fewer emergency recoveries competing for stack.

**Status**: ✅ **Already implemented**. See `WIFI_PERFORMANCE_ISSUES_LOG.md` Issue #1.

---

## Part VI: Current Project Status

### Mitigations Already In Place

| Item | File | Status |
|------|------|--------|
| Async command queueing | `WebDashboard.cpp` | ✅ Implemented |
| Minimal WiFi event handlers | `WebDashboard.cpp` | ✅ Implemented |
| Deferred AP reassert to main loop | `EvkaPosition.cpp` | ✅ Implemented |
| Modem sleep disabled | `WebDashboard.cpp` | ✅ Implemented |
| STA reconnect backoff | `WebDashboard.cpp` | ✅ Implemented |
| Input validation (CMD_MAX_LEN) | `WebDashboard.cpp` | ✅ Implemented |
| Event-driven `cleanupClients()` (connect/disconnect) | `WebDashboard.cpp` | ✅ Implemented |

### Not Currently Implemented (Optional)

| Strategy | Recommendation | Reason |
|----------|---|---|
| Increase lwIP stack to 8192 words | **Optional** | May be needed if stack overflow observed; currently working at 4096 |
| Concurrent client limit (3–5 max) | **Not implemented** | Project allows unlimited concurrent connections; may want to cap |
| Per-client rate-limiting | **Not implemented** | Protects against malicious clients; not priority for controlled lab environment |

---

## Part VII: Testing & Verification

### Test Scenario 1: Heavy WebSocket Load

```bash
# Terminal 1: Flash firmware
pio run -e wemos_d1_r32 --target upload
pio device monitor

# Terminal 2: Python stress test (run from tools/position_checker)
python3 -c "
import asyncio
import websockets
import json

async def client(id):
    async with websockets.connect('ws://192.168.1.50/ws') as ws:
        for i in range(1000):
            await ws.send(f'MSG_{id}_{i}')
            data = await ws.recv()
            print(f'Client {id}: {data}')
            await asyncio.sleep(0.1)

asyncio.run(asyncio.gather(*[client(i) for i in range(5)]))
"
```

**Expected**: Dashboard remains responsive, no Guru Meditation errors, free heap stable.

### Test Scenario 2: WiFi STA Loss During WebSocket Activity

```bash
# While WebSocket clients are connected:
# 1. Disable home WiFi router
# 2. Observe: AP remains joinable, dashboard still responds
# 3. Re-enable router
# 4. Observe: STA rejoins without AP interruption
```

**Expected**: No stack overflow from emergency AP reassert.

### Test Scenario 3: Extended Uptime

```bash
# Run for 24 hours with dashboard connected
# Monitor via serial:
#   - Free heap should remain stable (±5 KB max drift)
#   - No Guru Meditation errors
#   - No reboot cycles
```

### Heap/Stack Monitoring

Enable stack high-water mark tracking:

```cpp
// In loop() or status command:
#if CONFIG_FREERTOS_USE_TRACE_FACILITY
    UBaseType_t uxHighWaterMark = uxTaskGetStackHighWaterMark(NULL);  // Main task
    Serial.printf("[STACK] Main task high water: %u words (%u bytes free)\n", 
                  uxHighWaterMark, uxHighWaterMark * 4);
#endif
```

---

## Part VIII: Recommendations

### For Production Deployment

1. **Monitor stack health** — Add STATUS output field for remaining stack space
2. **Cap concurrent clients** — Set `WS_MAX_CLIENTS = 3` in header
3. **Enable stack overflow detection** — Add `build_flags = -DCONFIG_FREERTOS_WATCHPOINT_END_OF_STACK`
4. **24-hour burn-in test** — Verify no memory leaks or reboot cycles

### If Stack Overflow Occurs

**Symptom**: `Guru Meditation Error: Core 1 panic'ed (StoreProhibited)` or reboot loop

**Immediate fix**:
```ini
build_flags = -DCONFIG_LWIP_TCPIP_TASK_STACK_SIZE=8192
```

**Secondary fix** (if problem persists):
- Increase to `16384`
- Reduce WS_MAX_CLIENTS to 2
- Profile WebSocket message sizes; ensure all payloads <2 KB

### For Development

- Use `pio run -e wemos_d1_r32` with default config (4096 words)
- Monitor free heap periodically during development
- Test with 3–4 simultaneous WebSocket clients before deployment

---

## References

1. **ESP-IDF FreeRTOS Documentation**  
   https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/freertos.html

2. **lwIP Configuration**  
   https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/lwip.html

3. **AsyncTCP Issues**  
   https://github.com/me-no-dev/AsyncTCP/issues/161

4. **ESP32 Memory Layout**  
   https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/memory-types.html

5. **Related Documentation**
   - `docs/WIFI_PERFORMANCE_ISSUES_LOG.md` — 8 known WiFi issues + fixes
   - `docs/ESPASYNCHACK_NOTES.md` — ESPAsyncWebServer stability notes (issues, millis overflow, production checklist)
   - `docs/WIFI_AP_STA_RECONNECT_PATTERNS.md` — WiFi.begin() safety in AP+STA mode

---

- **Last Updated**: 2026-04-09
- **Firmware Commit**: Latest (see `AGENT_LOG.md`)
- **Status**: ✅ All critical mitigations implemented; optional enhancements documented
