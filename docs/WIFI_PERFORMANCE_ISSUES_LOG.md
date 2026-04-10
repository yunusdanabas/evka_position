# WiFi Performance & Connection Issues — Diagnostic Log

**Date**: 2026-04-08  
**Firmware commit at time of investigation**: `9405ac9` (latest: post-fix flash)  
**Board**: ESP32 Wemos D1 R32  
**Mode**: `WIFI_AP_STA` — AP `CMDCNC_EVKA` @ `192.168.1.50`, STA target `CMD-YAZILIM` (credentials stored in NVS; was `Yunusa` @ `10.78.137.252` at time of original investigation)

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
WiFi.setAutoReconnect(false);                // manual retry/backoff owns reconnect policy
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

### Issue 8 — AP Reachability Drops After STA Disconnect

| | |
|---|---|
| **Severity** | High |
| **Status** | Fixed in firmware, hardware test pending |
| **Files** | `firmware/src/WebDashboard.h`, `firmware/src/WebDashboard.cpp`, `firmware/src/EvkaPosition.cpp` |

**Root cause**: AP was configured once at startup, while STA reconnect behavior was left to background retries. During repeated STA disconnect/reconnect churn, AP availability could degrade, and there was no WiFi event-driven recovery path to reassert AP state.

**Fix applied**:
- Added WiFi event handling for STA lifecycle (`STA_CONNECTED`, `STA_GOT_IP`, `STA_DISCONNECTED`)
- Added AP health watchdog (`dashboard.tick()` + periodic AP verification)
- Added controlled STA reconnect backoff instead of unmanaged rapid retries
- Added AP reassertion path that verifies AP health on STA disconnect and only reruns `softAPConfig` + `softAP` if the AP is actually unhealthy
- Deduplicated the initial STA join attempt so boot performs one `WiFi.begin()` call and later retries remain backoff-driven

**Build verification**:
```bash
pio run -e wemos_d1_r32
```
Result: **SUCCESS** (firmware compiles with the new WiFi recovery flow).

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
| WiFi RSSI (STA → Yunusa) | -38 to -46 dBm (measured at time of investigation; STA now targets CMD-YAZILIM) |
| DATA frame rate | 20 Hz (50 ms intervals confirmed) |
| is_valid | 1 |
| TCP clients connected | 0 |
| PPR_ROTARY | 20000.00 |
| PPR_WIRE | 8020.00 |
| mm_per_pulse | 0.024938 |
| deg_per_pulse | 0.018000 |

**Network topology**:
```
ESP32 AP  : CMDCNC_EVKA   →  192.168.1.50  (dashboard + CMD TCP)
ESP32 STA : CMD-YAZILIM   →  DHCP (send GET_IP when connected)
Note: Original investigation used STA "Yunusa" @ 10.78.137.252 — now changed to CMD-YAZILIM
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

### D — AP persistence validation after upstream STA loss

Pending physical verification for the new recovery logic:
1. Boot with reachable `CMD-YAZILIM`
2. Confirm STA connected and AP reachable (`CMDCNC_EVKA`)
3. Power off router / disconnect `CMD-YAZILIM`
4. Confirm AP remains joinable and `http://192.168.1.50` still responds
5. Re-enable router and confirm STA rejoins without AP interruption

---

## Files Modified in This Session (2026-04-08)

| File | Changes |
|---|---|
| `firmware/src/WebDashboard.cpp` | Issues 1–6: modem sleep, AP channel pin, fast STA scan, WS buffer, cleanupClients, JS dirty flag |
| `firmware/src/SphericalSensor.h` | Issue 7: subnet conflict warning comment |
| `firmware/src/WebDashboard.h` | Added WiFi recovery state fields and periodic `tick()` API |
| `firmware/src/WebDashboard.cpp` | Issue 8: WiFi event handling, AP reassertion, STA retry backoff logic |
| `firmware/src/EvkaPosition.cpp` | Calls `dashboard.tick()` in main loop for non-blocking WiFi maintenance |
| `docs/WIFI_AP_STA_RECONNECT_PATTERNS.md` | NEW: Best practices for WiFi.begin() in AP+STA mode, safety analysis, reconnect patterns |

---

## 2026-04-09 — Code Review Session: WiFi Bug Fixes + Reliability Audit

**Reviewers**: Gemini (code review) + Copilot (ESP32 library internals research)
**Build**: SUCCESS — Flash 895,149 bytes (−260 bytes from 2026-04-08 baseline)

---

### WiFi Code Review Fixes (8 bugs)

These bugs were found by Gemini after reviewing the Issue 8 WiFi recovery implementation.

| # | Severity | Bug | Fix |
|---|---|---|---|
| W1 | Low | `_needApReassert` not cleared in `ensureApUp()` early-return → repeated `softAP()` calls when AP was healthy | Added `_needApReassert = false` before early-return |
| W2 | Medium | Backoff formula mismatch: `onWiFiEvent` used `count−1` as shift; `tick()` used `count` — diverging schedules | Removed backoff recalc from `tick()`; `onWiFiEvent` solely owns the schedule |
| W3 | Medium | No `volatile` on 5 cross-task flags (`_staConnected`, `_needApReassert`, `_staRetryPending`, `_staDisconnectCount`, `_nextStaRetryMs`) written from WiFi event callback | Added `volatile` to all 5 fields in `WebDashboard.h` |
| W4 | Low | `now >= _nextStaRetryMs` unsafe at millis() 49.7-day rollover | Changed to `(int32_t)(now - _nextStaRetryMs) >= 0` (standard Arduino idiom) |
| W5 | Low | Default `WiFi.setAutoReconnect(true)` — IDF auto-retry running in parallel with manual backoff, bypassing `_staDisconnectCount` | Added `WiFi.setAutoReconnect(false)` in `begin()` |
| W6 | Low | `WiFi.mode()` called on every forced AP reassert even if already in correct mode | Guard: `if (WiFi.getMode() != targetMode)` before calling `WiFi.mode()` |
| W7 | Medium | Slow DHCP after `STA_CONNECTED` still looked disconnected to the watchdog, so `tick()` could restart a valid join with a delayed IP lease | Added separate `_staAssociated` state and disarmed the watchdog on association; retry/watchdog now only run while the STA is actually unassociated |
| W8 | Low | `_staDisconnectCount` was a `uint8_t` incremented without saturation, so after 255 disconnects the backoff schedule reset to the 3 s base interval | Saturated the counter before increment so the capped 60 s backoff remains stable during long outages |
| W9 | Medium | `STA_LOST_IP` cleared `_staConnected` but did not trigger recovery while association remained up, allowing a potential associated/no-IP stall when auto-reconnect is disabled | Added `STA_LOST_IP_RECOVERY_MS` watchdog window (45 s): on prolonged `LOST_IP`, force controlled reconnect via existing manual retry path without reintroducing slow-DHCP reconnect loops |

---

### Follow-up hardening for W7/W8 review (2026-04-09)

**Scope**: closed the residual `STA_LOST_IP` edge case discovered after W7/W8.

**State-machine behavior now**
- `STA_CONNECTED`: marks `_staAssociated=true`, disarms connect-attempt watchdog.
- `STA_GOT_IP`: marks `_staConnected=true`, clears `_staLostIpMs`, resets disconnect counter.
- `STA_LOST_IP`: marks `_staConnected=false`, starts `_staLostIpMs` timer (first event only).
- `tick()`: if associated/no-IP persists for `STA_LOST_IP_RECOVERY_MS` (45 s), calls `WiFi.disconnect(false, false)` and reuses existing retry scheduler/backoff.

**Verification performed**
- Firmware build: `pio run -e wemos_d1_r32` (PASS)
- Python tests: `pytest -q` (29 passed)
- Scenario checks by state-path review:
  - Slow DHCP after association does **not** re-enter reconnect loop (W7 preserved).
  - Long outage keeps capped retry behavior (W8 preserved).
  - `LOST_IP` without immediate disassociation now exits via timed, controlled reconnect (W9 fixed).

### Reliability & Optimization Fixes (7 fixes + 2 follow-ups)

These bugs were found by Gemini (full code audit) + Copilot (library internals).

| # | Severity | Bug | Fix | File |
|---|---|---|---|---|
| R1 | High | `normalizeAngle()` used while-loops — O(N) CPU block at large encoder counts (107K iterations at max int32 range) | Replaced with O(1) `fmodf` | `SphericalSensor.cpp:161` |
| R2 | High | STA retry dead-stop: `tick()` cleared `_staRetryPending` but if IDF never fires `DISCONNECTED`, retries stop forever | Added `_staConnectAttemptMs` deadline watchdog (15 s) in `tick()` | `WebDashboard.cpp/h` |
| R3 | Medium | `validateLimits()` only checked NaN/Inf on Cartesian fields — NaN in spherical coords (e.g. from zero-PPR NVS corruption) passed as valid | Added `isnan`/`isinf` guards on `sph.r_mm`, `sph.theta_deg`, `sph.phi_deg` | `SphericalSensor.cpp:173` |
| R4 | Medium | Double-precision literals (`1.0`, `180.0`) in EMA filter and trig — ESP32 Xtensa has no hardware double FPU, forces software emulation (10–20× slower) | Changed to `1.0f`, `180.0f`; trig: `sin/cos/asin/atan2` → `sinf/cosf/asinf/atan2f/sqrtf` | `SphericalSensor.cpp:127–204` |
| R5 | Medium | `printPosition()` formatted and printed the DATA line to serial; `loop()` also formatted the same DATA line for WebSocket — two snprintf calls per tick | Removed DATA snprintf from `printPosition()`; `loop()` formats once → `Serial.println()` + `dashboard.broadcast()` | `SphericalSensor.cpp:252`, `EvkaPosition.cpp:407` |
| R6 | Minor | `_staConnectAttemptMs` written from `onWiFiEvent(GOT_IP)` callback but not declared `volatile` | Added `volatile` keyword | `WebDashboard.h:44` |
| R7 | Minor | `cartesianToSpherical()` used `sqrt()` (double) instead of `sqrtf()` (float) | Changed to `sqrtf()` | `SphericalSensor.cpp:145` |

---

### ESPAsyncWebServer v1.2.4 — Clarified Behavior (Copilot Library Research)

Copilot read the installed library source at `.pio/libdeps/wemos_d1_r32/ESP Async WebServer/src/` and found the v1.2.4 behavior differs from what was documented in prior session notes:

| Concern | Prior documentation | Actual v1.2.4 behavior |
|---|---|---|
| `textAll()` heap allocation | "Per-client copy — N clients = N mallocs" | **Shared buffer model**: one `malloc` per broadcast regardless of client count. Bounded leak risk. |
| `cleanupClients()` zombie cleanup | "Required to free disconnected client slots" | v1.2.4 auto-frees in `_handleDisconnect()` via `remove_first()`. `cleanupClients()` is a max-client enforcer only. |
| TCP RST client accumulation | "Zombie clients accumulate without cleanup" | **Not true in v1.2.4**: RST triggers `_onDisconnect()` → `_handleDisconnect()` → client removed from LinkedList immediately. |

**Practical impact**: The memory pressure from `textAll()` at 20 Hz is significantly lower than documented. The shared buffer pattern means at most 2 heap allocations per broadcast cycle (one for the buffer struct, one for the payload), both freed after TCP ACK. Long-term heap stability risk is low for this firmware.

---

### Updated Files (2026-04-09)

| File | Changes |
|---|---|
| `firmware/src/WebDashboard.h` | W3, W6, W7, R2, R6: volatile fields, watchdog constant + association state |
| `firmware/src/WebDashboard.cpp` | W1–W8, R2: ensureApUp guard, backoff dedup, setAutoReconnect, watchdog; post-review fixes: no forced AP restart on STA disconnect, no duplicate boot `WiFi.begin()`, no DHCP-pending watchdog restart, no backoff reset after counter wrap |
| `firmware/src/SphericalSensor.cpp` | R1–R5, R7: fmodf, NaN guards, float literals, sinf/cosf/sqrtf, DATA dedup |
| `firmware/src/EvkaPosition.cpp` | R5: DATA line consolidated here (serial + WiFi broadcast) |
