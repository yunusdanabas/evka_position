# WiFi Performance & Connection Issues — Diagnostic Log

**Date**: 2026-04-08  
**Firmware commit at time of investigation**: `9405ac9` (latest: post-fix flash)  
**Board**: ESP32 Wemos D1 R32  
**Mode**: `WIFI_AP_STA` — AP `CMDCNC_EVKA` @ `192.168.1.50`, STA connected to `Yunusa` @ `10.78.137.252`

---

## Reported Symptoms

- Web dashboard at `http://192.168.1.50` was noticeably slower than before recent commits
- Intermittent WebSocket disconnections — dashboard data appeared "bursty" instead of smooth 20 Hz
- Could not reach dashboard at all in some network configurations
- `WIFI_SET` command silently corrupted (command sent, no acknowledgment)

---

## Issues Found and Fixed

### Issue 1 — WiFi Modem Sleep Enabled (PRIMARY CAUSE of slowness)

| | |
|---|---|
| **Severity** | Critical |
| **Status** | Fixed |
| **File** | `firmware/src/WebDashboard.cpp` |

**Root cause**: ESP32 defaults to `WIFI_PS_MIN_MODEM`. The radio periodically powers down between DTIM beacons (~100 ms gaps). In AP+STA mode this causes:
- AP clients miss beacons → WebSocket drops and reconnect cycles
- DATA messages queue then flush in bursts instead of a steady 20 Hz stream
- Dashboard appears "jumpy" or completely stalled between bursts

**Fix applied**:
```cpp
// After WiFi.softAP(...)
WiFi.setSleep(WIFI_PS_NONE);  // disable modem sleep
```

---

### Issue 2 — No Explicit AP Channel (Channel Drift)

| | |
|---|---|
| **Severity** | High |
| **Status** | Fixed |
| **File** | `firmware/src/WebDashboard.cpp` |

**Root cause**: `WiFi.softAP(SSID, PASS)` picks a channel automatically. Background STA scanning for home/office networks can cause the AP to shift channels mid-session, momentarily disappearing for connected clients.

**Fix applied**:
```cpp
WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD, ESPNOW_CHANNEL);  // pin to ch 1
```
Reuses the existing `ESPNOW_CHANNEL 1` constant — ESP-NOW remote (when enabled) requires the same channel as the AP.

---

### Issue 3 — STA Full-Channel Scan Interferes with AP

| | |
|---|---|
| **Severity** | Medium |
| **Status** | Fixed |
| **File** | `firmware/src/WebDashboard.cpp` |

**Root cause**: When STA credentials are stored but the target network is not reachable, the WiFi driver runs continuous 13-channel scans. This consumes radio time shared with the AP, degrading AP throughput.

**Fix applied**:
```cpp
WiFi.setScanMethod(WIFI_FAST_SCAN);          // stop on first SSID match
WiFi.setSortMethod(WIFI_CONNECT_AP_BY_SIGNAL);
WiFi.setAutoReconnect(true);
WiFi.begin(staSsid.c_str(), staPass.c_str());
```

---

### Issue 4 — WebSocket Command Buffer Truncated at 32 Bytes

| | |
|---|---|
| **Severity** | High |
| **Status** | Fixed |
| **File** | `firmware/src/WebDashboard.cpp`, `onWsEvent()` |

**Root cause**: `char cmd[32]` silently truncated any WebSocket command longer than 31 bytes. `WIFI_SET:CMD-YAZILIM,cmd20165544` is 35 characters — the tail was cut, making the command unrecognizable, which returned `ERR:UNKNOWN_CMD` with no indication of truncation.

**Fix applied**: Replaced the fixed buffer with a direct `String` construction from raw WebSocket bytes, capped at 128 bytes (matching the serial buffer limit).
```cpp
size_t n = (len < 128) ? len : 128;
String cmdStr((const char*)data, n);
cmdStr.trim();
_pendingCmd = cmdStr;
```

---

### Issue 5 — `cleanupClients()` Called on Every DATA Event (60×/sec)

| | |
|---|---|
| **Severity** | Medium |
| **Status** | Fixed |
| **File** | `firmware/src/WebDashboard.cpp`, `onWsEvent()` |

**Root cause**: `_ws.cleanupClients()` was called at the end of `onWsEvent()` unconditionally, including on `WS_EVT_DATA` events. With 3 clients at 20 Hz this means ~60 client-list iterations per second for no reason — cleanup is only meaningful when clients join or leave.

**Fix applied**: Moved `_ws.cleanupClients()` exclusively to `WS_EVT_CONNECT` and `WS_EVT_DISCONNECT` event branches.

---

### Issue 6 — 3D Canvas Redraws at 60 Hz with No Dirty Flag

| | |
|---|---|
| **Severity** | Low–Medium (CPU / battery on client device) |
| **Status** | Fixed |
| **File** | `firmware/src/WebDashboard.cpp` (embedded JS) |

**Root cause**: `drawScene()` called `requestAnimationFrame()` unconditionally and always executed the full canvas repaint — expensive matrix transforms + draw calls — at 60 FPS. Data arrives at 20 Hz, so 3 out of every 4 frames were wasted redraws of an unchanged scene.

**Fix applied**: Added `_dirty3d` boolean flag. `drawScene()` only repaints when `_dirty3d` is true or a touch gesture is active. `_dirty3d` is set to `true` when new DATA arrives, and in `toggleAxes()`, `clearTrail()`, `saveOrigin()`, and `savePoint()`.

---

### Issue 7 — 192.168.1.x AP Subnet Conflicts with Home/Office Routers

| | |
|---|---|
| **Severity** | Low (operational, cannot be fixed in firmware) |
| **Status** | Documented |
| **File** | `firmware/src/SphericalSensor.h` |

**Root cause**: The AP static IP `192.168.1.50` is in the same subnet used by most home/office routers (`192.168.1.0/24`). If a client device is simultaneously connected to a home router on the same subnet, the OS routes `192.168.1.50` to the home router instead of the ESP32, making the dashboard unreachable.

**Cannot change**: CMD CNC software is hardcoded to `192.168.1.50:8080`.

**Workaround**: Disconnect the client device from the home/office WiFi before connecting to `CMDCNC_EVKA`. The device should be connected **only** to `CMDCNC_EVKA` when accessing the dashboard.

**Documentation added** in `SphericalSensor.h` at the `WIFI_AP_IP_*` defines.

---

## Operational Issue — Stale Serial RX Buffer Corrupts First Command

| | |
|---|---|
| **Severity** | Low (affects development workflow only) |
| **Status** | Workaround documented |

**Symptom**: After closing `pio device monitor`, the Linux USB-serial driver retains bytes in the RX buffer. The next command sent via Python `serial.Serial` prepends those stale bytes, making the command unrecognizable → `ERR:UNKNOWN_CMD`.

**Workaround**: Always call `reset_input_buffer()` + `reset_output_buffer()` before the first write in any serial session:
```python
s = serial.Serial('/dev/ttyUSB0', 115200, timeout=3)
s.reset_input_buffer()
s.reset_output_buffer()
```

---

## Current System State (post-fix, verified via serial)

| Parameter | Value |
|---|---|
| Uptime | 265 s (stable, no watchdog reset since flashing) |
| Free heap | 231,792 bytes (zero drift across 5 samples over 15 s — no leak) |
| WiFi RSSI (STA → Yunusa) | -38 to -46 dBm (excellent, normal variation) |
| DATA frame rate | 20 Hz (50 ms intervals confirmed) |
| is_valid | 1 |
| TCP clients connected | 0 |
| PPR_ROTARY | 20000.00 |
| PPR_WIRE | 8020.00 |
| mm_per_pulse | 0.024938 |
| deg_per_pulse | 0.018000 |

**Network topology**:
```
ESP32 AP  : CMDCNC_EVKA  →  192.168.1.50  (dashboard + CMD TCP)
ESP32 STA : Yunusa        →  10.78.137.252 (internet uplink / remote access)
Laptop    : Yunusa        →  10.78.137.69
```

---

## Open Items / Pending Verification

### A — Dashboard connectivity not yet confirmed post-fix

The performance fixes have been flashed and are running, but **no client has connected to `CMDCNC_EVKA` yet** to verify the WebSocket data flow is smooth. The next test step:

1. On phone or laptop: disconnect from current WiFi
2. Connect to `CMDCNC_EVKA` (password: `cmdcnc1234`)
3. Open `http://192.168.1.50`
4. Observe: page load < 2 s, 3D trail updating smoothly, no WebSocket drops over 2+ minutes

### B — `RTCWDT_RTC_RESET` watchdog resets observed

Earlier serial output showed `RTCWDT_RTC_RESET` in the boot log, indicating the ESP32 watchdog fired during a previous run. This is likely related to a long blocking operation during `setup()` (most probable candidate: `delay(2000)` + `WiFi.begin()` blocking during STA association).

**Impact**: If the watchdog fires repeatedly, the firmware enters a reboot loop. Currently not reproducing — the device has been stable for 160+ s.

**To investigate if it recurs**: Check if `WiFi.begin()` blocks longer than expected. Consider moving the 2 s zero-calibration delay to use a non-blocking `millis()` check, or calling `esp_task_wdt_reset()` before the delay.

### C — Theta residual of 0.02° after zero

`DATA` frames show `Theta=0.018` (≈ 1 encoder count) after `setZeroPoint()`. This is within 1 PPR count of true zero and is not a real error — it reflects the `DEG_PER_PULSE = 0.018°` quantization step. No fix needed unless sub-count accuracy is required.

---

## Files Modified in This Session

| File | Changes |
|---|---|
| `firmware/src/WebDashboard.cpp` | Issues 1–6: modem sleep, AP channel pin, fast STA scan, WS buffer, cleanupClients, JS dirty flag |
| `firmware/src/SphericalSensor.h` | Issue 7: subnet conflict warning comment |
