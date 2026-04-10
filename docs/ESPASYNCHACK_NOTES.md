# ESPAsyncWebServer Stability Notes

Reference for `ESPAsyncWebServer@1.2.4` + `AsyncTCP@1.1.1` as used in this project.

Firmware context: `WebDashboard.h/cpp` + `EvkaPosition.cpp`. Broadcast: 20 Hz DATA frames (~85 bytes). AP+STA concurrent mode.

---

## Issue Summary

| # | Category | Issue | Severity | Current Mitigation |
|---|---|---|---|---|
| 1 | Memory | Broadcast allocation pressure (`textAll`) | Medium | 20 Hz cap + small payloads |
| 2 | Memory | Client disconnect cleanup behavior | Medium | Cleanup on WS connect/disconnect events |
| 3 | Robustness | Malformed/oversized WS input | Medium | Queue bounds + frame completeness checks |
| 4 | Stability | STA loss and AP reachability | High | Event-driven AP reassert + retry backoff |
| 5 | Stability | Async callback blocking/re-entrancy | Medium | Enqueue commands; process in `loop()` |
| 6 | Memory | Slow-client outbound queue pressure | Medium | Rate limiting + soak-test monitoring |
| 7 | Stability | AsyncTCP/lwIP stack pressure | High | Keep callbacks short; see `ASYNCTCP_STACK_OVERFLOW_ANALYSIS.md` |
| 8 | Stability | AP degradation during STA churn | High | `dashboard.tick()` + AP health checks |

---

## What Is Implemented

**Cleanup policy** — event-based, not periodic:
```cpp
void WebDashboard::onWsEvent(...) {
    if (type == WS_EVT_CONNECT)    _ws.cleanupClients();
    else if (type == WS_EVT_DISCONNECT) _ws.cleanupClients();
    else if (type == WS_EVT_DATA)  enqueueCommand(data, len);
}
```
Do NOT add `cleanupClients()` on every DATA frame — that adds avoidable CPU overhead.

**Command queue** — bounded, mutex-protected:
- `CMD_MAX_LEN = 128`, `CMD_QUEUE_SIZE = 4`
- Oversized/invalid payloads dropped before queueing
- Business logic processed in `loop()` via `takePendingCommand()`

**AP/STA stability**:
- `WiFi.setAutoReconnect(false)` — manual controlled backoff
- AP reassert via `ensureApUp()` called from `tick()`
- STA retry watchdog (15 s) + DHCP watchdog (45 s) in `tick()`

**Observability**:
- `SYSINFO` command returns RSSI, free heap, uptime, TCP client count

---

## Symptoms → Quick Actions

| Symptom | Action |
|---------|--------|
| Heap drift over long uptime | Check payload size; verify 20 Hz cap; monitor `SYSINFO` heap trend |
| AP at `192.168.1.50` unreachable after router drop | Verify `dashboard.tick()` runs in `loop()`; check Issue 8 fix |
| Commands delayed under load | Keep WS callbacks minimal; ensure `loop()` processes queue |
| Malformed WS message behavior | Verify `CMD_MAX_LEN` guard is enforced before enqueue |
| Guru Meditation under networking load | See `ASYNCTCP_STACK_OVERFLOW_ANALYSIS.md` for stack sizing |

---

## Millis() Overflow Safety

`uint32_t millis()` wraps at ~49.71 days. All timer patterns in this firmware are safe:

- **Periodic work** (position updates, LED): `millis() - last_update >= PERIOD` — unsigned subtraction, safe.
- **Retry scheduling deadlines**: `(int32_t)(now - _nextStaRetryMs) >= 0` — signed delta, safe.
- **Watchdog timeouts**: `(int32_t)(now - _staConnectAttemptMs) >= (int32_t)STA_CONNECT_TIMEOUT_MS` — safe form; avoids addition overflow near rollover.
- **AP health intervals**: `now - _lastApHealthCheckMs >= AP_HEALTH_CHECK_MS` — unsigned subtraction, safe.

Keep these idioms when adding new timers. Do not use `now >= (timestamp + delta)` — the addition can overflow near 49.7-day rollover.

---

## Production Checklist

- [ ] Payload size well below 2 KB (current: ~85 bytes ✅)
- [ ] Broadcast rate ≤ 20 Hz ✅
- [ ] WS callbacks non-blocking ✅
- [ ] AP reachable during upstream STA outages ✅ (Issue 8 fix)
- [ ] 2-hour soak test before deployment with expected client count

---

## Related Docs

- `ASYNCTCP_STACK_OVERFLOW_ANALYSIS.md` — lwIP/AsyncTCP stack sizing and Guru Meditation root cause
- `WIFI_PERFORMANCE_ISSUES_LOG.md` — full chronological fix log (Issues 1–8 + W/R series)
- `WIFI_AP_STA_RECONNECT_PATTERNS.md` — WiFi.begin() safety and reconnect best practices
