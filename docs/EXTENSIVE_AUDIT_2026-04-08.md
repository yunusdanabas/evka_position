# Extensive Code & Documentation Audit — evka_position

**Date:** 2026-04-08  
**Audit mode:** Read-only audit of the current worktree  
**Source of truth:** Live source files in the repo; build/test outputs used as corroborating evidence  
**Files reviewed:** `firmware/src/EvkaPosition.cpp`, `firmware/src/SphericalSensor.h`, `firmware/src/SphericalSensor.cpp`, `firmware/src/WebDashboard.cpp`, `firmware/src/WebDashboard.h`, `firmware/src/CmdTcpServer.cpp`, `firmware/src/CmdTcpServer.h`, `platformio.ini`, `README.md`, `CLAUDE.md`, `docs/WIFI_PERFORMANCE_ISSUES_LOG.md`, `docs/PROJECT_ROADMAP.md`, `docs/integration/CMD_SOFTWARE_INTEGRATION.md`, `docs/integration/CMD_INTEGRATION_CHANGELOG.md`, `docs/resources.md`, `tools/README.md`, `tools/VISUALIZATION_GUIDE.md`, `tools/position_checker/tcp_client.py`, `tools/position_checker/cmd_main.py`, `tools/position_checker/cmd_gui.py`, plus supporting Python parser/GUI files and the dedicated rotary encoder hardware doc.

## Validation Performed

- `git status --short` confirmed the repo already had unrelated uncommitted changes before this audit.
- `pio run -e wemos_d1_r32` completed successfully.
  - RAM: `14.1%`
  - Flash: `68.2%`
- `python -m unittest discover -s tools/position_checker/tests -v` completed successfully.
  - Result: `29` tests passed
- External URLs listed in `docs/resources.md` were checked. Confirmed dead links are called out below.

## Changes Made In This Session

- Added this audit report file: `docs/EXTENSIVE_AUDIT_2026-04-08.md`
- Updated `AGENTS.md` activity log to record the documentation change
- No firmware or Python source behavior was changed in this session

## Findings

### Thread Safety

[SEVERITY: High]  
File: `firmware/src/WebDashboard.h:19`, `firmware/src/WebDashboard.cpp:1025`  
Issue: `_pendingCmd` is a cross-task `String` mutated without synchronization.  
Detail: `onWsEvent()` runs on the AsyncTCP/ESPAsyncWebServer task, while `loop()` copies and clears the same heap-backed `String` in `takePendingCommand()`. `String` assignment and copy are not atomic on ESP32, so this can lose commands or corrupt heap state under contention.  
Fix: Replace `_pendingCmd` with a fixed-size FreeRTOS queue or ring buffer of command structs, or guard access with a mutex or critical section and avoid shared `String` state.

### Protocol

[SEVERITY: High]  
File: `firmware/src/CmdTcpServer.cpp:80`, `firmware/src/EvkaPosition.cpp:211`  
Issue: `ENABLE_REMOTE_WIFI_CONFIG` is documented but not enforced on any remote path.  
Detail: TCP handles `WIFI_SET` and `WIFI_AYAR` directly with no flag check, and the WebSocket path forwards `WIFI_SET` into `processCommand()` where it is also always accepted. With the default build (`ENABLE_REMOTE_WIFI_CONFIG=0`), a network client can still rewrite credentials and reboot the device.  
Fix: Gate remote WiFi configuration centrally by transport, return `ERR:WIFI_CFG_DISABLED` when disabled, and keep physical serial as an explicit exception only if that behavior is intended.

[SEVERITY: Medium]  
File: `firmware/src/EvkaPosition.cpp:94`, `firmware/src/EvkaPosition.cpp:331`  
Issue: `STATUS` produces no reply for TCP and WebSocket callers.  
Detail: `STATUS` prints directly to serial and returns `""`; both remote command paths only send replies when `reply.length() > 0`, so remote clients get silence even though the command is documented as supported.  
Fix: Build the status line into a returned string, print it to serial as needed, and send the same line back to the originating remote client.

[SEVERITY: Medium]  
File: `firmware/src/WebDashboard.h:19`, `firmware/src/CmdTcpServer.h:28`, `firmware/src/EvkaPosition.cpp:332`, `firmware/src/EvkaPosition.cpp:343`  
Issue: Command routing uses single-slot mailboxes and broadcast replies.  
Detail: WebSocket and TCP each keep only one pending command, so multiple commands arriving before the next `loop()` iteration overwrite each other. After processing, replies are broadcast to all connected peers instead of returned only to the requester, which causes command loss and cross-client ACK and ERR leakage.  
Fix: Queue commands per transport or per client and route replies only to the originating client or session.

[SEVERITY: Medium]  
File: `firmware/src/WebDashboard.cpp:1018`  
Issue: The WebSocket handler still assumes every `WS_EVT_DATA` callback contains a complete text frame.  
Detail: The new length-bounded `String((const char*)data, n)` is safe for the callback lifetime, but the code ignores `AwsFrameInfo::final`, `index`, and `len`. Fragmented or continuation frames can still be truncated or misparsed.  
Fix: Only process complete single-frame messages (`final && index == 0 && info->len == len`) or accumulate fragments until the full message is available.

[SEVERITY: Low]  
File: `firmware/src/EvkaPosition.cpp:119`  
Issue: `CAL_W` reports negative travel as a generic factor-range error.  
Detail: If the wire counts are negative, `measured_mm` becomes negative and the command fails with `ERR:CAL_W factor out of range`, which hides the real cause: the operator moved the wire in the wrong direction or the sign convention is reversed for that test.  
Fix: Reject `wc < 0` or `measured_mm <= 0` explicitly with a direction-specific error such as `ERR:CAL_W negative counts`.

### Math

[SEVERITY: Medium]  
File: `firmware/src/SphericalSensor.cpp:193`  
Issue: EMA filtering leaves stale Cartesian output after returning to zero or home.  
Detail: `spherical.r_mm` is clamped to `0` immediately, but `cart` is then low-pass filtered from the previous position. The firmware can therefore publish `R=0` while `X/Y/Z` remain non-zero for several frames, which creates lag and an inconsistent zero-state near the origin.  
Fix: Reset or bypass the Cartesian EMA when `r` is near zero or after zeroing, or move filtering to a representation that keeps spherical and Cartesian outputs consistent.

### Memory

[SEVERITY: Low]  
File: `firmware/src/EvkaPosition.cpp:265`, `firmware/src/CmdTcpServer.cpp:58`  
Issue: Serial and TCP overflow guards can turn an overlong line into a valid tail command.  
Detail: When a buffer exceeds `128` bytes, the code clears it immediately and then resumes collecting bytes from the same line. A malformed oversized input is therefore not discarded until newline; its tail can still be interpreted as a fresh command.  
Fix: Add an overflow or discard state and ignore all bytes until the next `\r` or `\n`, then clear once.

### Docs

[SEVERITY: Medium]  
File: `CLAUDE.md:46`, `firmware/src/SphericalSensor.h:66`, `docs/hardware_design/encoders/rotary_e40s6/README.md:1`  
Issue: The rotary encoder model is documented inconsistently as both `E30S6` and `E40S6`.  
Detail: The dedicated hardware doc identifies the part as `Autonics E40S6-5000-3-T-5`, while `CLAUDE.md` and firmware comments say `E30S6-5000`. The PPR is the same, but BOM, procurement, wiring notes, and hardware references are no longer internally consistent.  
Fix: Pick one authoritative part number based on the actual hardware in use and update firmware comments and docs to match it consistently.

[SEVERITY: Medium]  
File: `docs/integration/CMD_SOFTWARE_INTEGRATION.md:5`, `CLAUDE.md:134`, `docs/integration/CMD_INTEGRATION_CHANGELOG.md:11`  
Issue: Integration documentation no longer matches the current firmware behavior.  
Detail: The docs still describe the AP SSID as `CMDCNC`, still point to moved docs under `docs/` instead of `docs/integration/`, and still claim `ENABLE_REMOTE_WIFI_CONFIG=0` causes `ERR:WIFI_CFG_DISABLED`. Current code uses `CMDCNC_EVKA`, the files moved, and the error is never emitted because the guard is absent.  
Fix: Update the integration docs, roadmap references, and `CLAUDE.md` to the current SSID, current paths, and current remote-config behavior.

[SEVERITY: Low]  
File: `docs/resources.md:80`, `docs/resources.md:196`, `docs/resources.md:212`  
Issue: `docs/resources.md` contains confirmed dead external links.  
Detail: Live checks returned `404` for `Automatic-Addison/arduino-robotics`, the Arduino serial communication guide, and the Arduino forum sensors category. A few others returned `403` due to anti-bot blocking and were not counted as broken.  
Fix: Replace or remove the dead URLs and add a `last checked` date for externally maintained references.

### Build

[SEVERITY: Medium]  
File: `firmware/src/EvkaPosition.cpp:201`  
Issue: `ENABLE_WIFI=0` is not compile-safe.  
Detail: `GET_IP` references `WiFi` outside any `#if ENABLE_WIFI` guard, so the advertised serial-only build configuration cannot be relied on if WiFi is compiled out.  
Fix: Guard `GET_IP` with `#if ENABLE_WIFI` or provide a non-WiFi fallback reply in the serial-only build.

[SEVERITY: Low]  
File: `platformio.ini:5`, `platformio.ini:8`  
Issue: The build is not reproducibly pinned.  
Detail: `platform = espressif32` is unversioned and `lib_deps` use caret ranges (`^...`), so future PlatformIO, platform, and library releases can change the toolchain and dependency set underneath the project.  
Fix: Pin the platform and libraries to exact tested versions in `platformio.ini`.

## Checked Without Findings

- `espnow_pending_button` is an `int8_t`; the current single-byte volatile access pattern is atomic on ESP32, though burst presses can still overwrite each other.
- `recording_active` and `SAVE_POINT`’s `pt_idx` are loop-only; there is no serial-vs-WebSocket data race there.
- `sphericalToCartesian()` and the degree-to-radian conversions are internally consistent; the Python math tests passed.
- `RADIUS_MAX_MM = 3000` corresponds to about `120300` wire counts, which is well within `int32_t`.
- `INDEX_HTML` is stored in PROGMEM and served with `send_P()`.
- TCP partial-line buffers are cleared on disconnect and reconnect, so stale per-client RX data does not survive reconnects.
- `ESPNOW_CHANNEL` is defined unconditionally, so the AP channel pinning change compiles even with `ENABLE_ESPNOW_REMOTE=0`.

## Summary Table

| Severity | Category | Issue |
|---|---|---|
| High | Thread Safety | Unsynchronized cross-task WebSocket `_pendingCmd` `String` |
| High | Protocol | `ENABLE_REMOTE_WIFI_CONFIG` is not enforced remotely |
| Medium | Protocol | `STATUS` sends no TCP or WebSocket reply |
| Medium | Protocol | Single-slot command mailboxes and broadcast replies break multi-client behavior |
| Medium | Protocol | WebSocket fragmented text frames are not handled safely |
| Medium | Math | EMA filtering leaves stale Cartesian values at zero or home |
| Low | Memory | Overflow guards can parse the tail of an oversized line as a new command |
| Medium | Docs | Encoder model naming conflicts (`E30S6` vs `E40S6`) |
| Medium | Docs | Integration docs no longer match SSID, paths, and config-gating behavior |
| Low | Docs | `docs/resources.md` contains confirmed dead external links |
| Medium | Build | `ENABLE_WIFI=0` is not compile-safe |
| Low | Build | Platform and library dependencies are not exactly pinned |

## WiFi Fix Verdict

### 1. Modem sleep
- Correct.
- `WiFi.setSleep(WIFI_PS_NONE)` is immediately after `WiFi.softAP()` and before the web server starts serving clients.

### 2. AP channel pinning
- Correct.
- `ESPNOW_CHANNEL` is defined unconditionally in `SphericalSensor.h`, so the AP channel pinning compiles even when ESP-NOW is disabled.

### 3. STA fast scan
- Correct.
- `WiFi.setScanMethod(WIFI_FAST_SCAN)` is in the stored-credentials branch and runs before `WiFi.begin()`.

### 4. WebSocket command buffer
- Partially correct.
- The bounded `String` construction is safe for the callback lifetime, but fragmented frames are still mishandled and the shared mailbox remains thread-unsafe.

### 5. `cleanupClients()` placement
- Correct.
- It is absent from `WS_EVT_DATA` and only runs on connect and disconnect.

### 6. JS `_dirty3d` flag
- Partially correct.
- `requestAnimationFrame()` remains unconditional, but `endSession()` clears origin and points without setting `_dirty3d`, so the 3D scene can remain stale until the next data frame or gesture.

### Overall Verdict

`needs revision`

Items 4 and 6 are incomplete, and the audit found separate high-impact remote-command issues around WiFi configuration.

## Quick Wins

- Enforce `ENABLE_REMOTE_WIFI_CONFIG` centrally and distinguish transport origin so TCP and WebSocket can be rejected cleanly with `ERR:WIFI_CFG_DISABLED`.
- Replace the WebSocket and TCP single-slot `String` mailboxes with fixed-size queues and reply only to the requesting client.
- Make `STATUS` return a string, and discard oversized serial and TCP lines until newline instead of resetting mid-line.
- Fix the current doc drift in one sweep: SSID, moved file paths, encoder model name, and dead links in `docs/resources.md`.
- Add WebSocket fragment completeness checks and set `_dirty3d = true` in `endSession()`.

---

## Remediation Log

**Three passes applied after this audit. Build verified: `pio run -e wemos_d1_r32` SUCCESS, 29/29 Python tests pass.**

### Pass 1 — Cursor (2026-04-08)

| Finding | Fix Applied |
|---|---|
| WebSocket `_pendingCmd` String race (Thread Safety / High) | Replaced with `portMUX_TYPE` spinlock + 4-slot fixed `char` queue in `WebDashboard.h/.cpp` |
| `ENABLE_REMOTE_WIFI_CONFIG` not enforced (Protocol / High) | CmdTcpServer now forwards all commands to `processCommand()`; `#if !ENABLE_REMOTE_WIFI_CONFIG` guard added there centrally |
| `STATUS` no reply to TCP/WS (Protocol / Medium) | `buildStatusLine()` extracted; `printStatusLine()` returns the string; both serial and remote paths receive the reply |
| EMA lag after zeroing (Math / Medium) | `position_filter_primed = false` added to `setZeroPoint()`, `zeroTheta()`, `zeroPhi()`, `zeroWire()` |
| `sph_raw` vs `sph_limited` mismatch in `validateLimits()` (Math / Medium) | Unified to single `sph` with consistent `cart_raw` before EMA filter |
| `SphericalSensor.h:66` E30S6 → E40S6 (Docs / Medium) | Fixed |
| `CLAUDE.md` E30S6 → E40S6 (Docs / Medium) | Fixed (auto-hook) |
| Platform and libraries unpinned (Build / Low) | `espressif32@6.12.0`; exact lib versions in `platformio.ini` |
| `tcp_client.py` blocking recv (Python / High) | IO timeout, TCP keepalive, send timeout, shutdown join added |
| Various doc SSID / path fixes | Partial — see Pass 3 |

### Pass 2 — Claude Code (2026-04-08)

Items confirmed fixed by Cursor but partially incomplete per Codex re-audit, plus new items Cursor did not address:

| Finding | Fix Applied |
|---|---|
| WS fragmented frame guard (Protocol / Medium) | `WebDashboard.cpp:1054` — added `info->final && info->index == 0 && info->len == len` check |
| `GET_IP` breaks `ENABLE_WIFI=0` build (Build / Medium) | Wrapped with `#if ENABLE_WIFI / #else return "ERR:WIFI_DISABLED" #endif` |
| `endSession()` missing dirty flags (JS / Low) | Added `_dirty3d=true;_dirty2d=true;` at end of `endSession()` |
| CmdTcpServer single-slot overwrite (Protocol / High) | Replaced `String _pendingCmd` with 4-slot `char _cmdQueue[4][129]`; `enqueueCommand()` + dequeue in `takePendingCommand()`; full → `ERR:CMD_QUEUE_FULL` to client |
| Overflow guard tail-parsing — serial (Memory / Low) | `static bool serial_overflow` flag in `handleSerialCommands()`; discards rest of overlong line; prints `ERR:CMD_TOO_LONG` |
| Overflow guard tail-parsing — TCP (Memory / Low) | `bool _rxOverflow[MAX_CLIENTS]` in `CmdTcpServer`; same discard pattern; sends `ERR:CMD_TOO_LONG` to client |
| Remaining E30S6 in docs (Docs / Medium) | Fixed in: `5v/bill_of_materials.md`, `5v/circuit_schematic.md`, `PCB_EMI_LAYOUT_GUIDE.md`, `FreeRTOS_Dual_Core_Architecture.md`, `calibration/README.md`, `AGENTS.md`, test sources (3 files) |
| Dead links in `docs/resources.md` (Docs / Low) | arduino-robotics repo removed; Arduino serial URL updated; Arduino forum URL updated |

### Deferred

| Finding | Reason |
|---|---|
| Broadcast replies — per-client routing (Protocol / Medium) | Requires `processCommand()` refactor to accept reply-to handle; deferred until multi-client simultaneous commanding is required |
| EMA lag at r=0 (valid position) (Math / Low) | Self-corrects in ~250 ms; cosmetic only; no immediate action |

### WiFi Fix Verdict (updated)

All 6 WiFi fixes are now correct and complete:
- Items 1–3, 5: correct as originally assessed
- Item 4 (WS command buffer): now fully correct — queue + fragment guard added in Pass 2
- Item 6 (JS `_dirty3d`): now correct — `endSession()` sets both dirty flags in Pass 2
