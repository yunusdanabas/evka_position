# CMD Protocol Integration — Changelog & Rationale

> **Archive / implementation history.** This file records the original integration and contains
> dated statements that are not the current handoff contract. The vendor C# application has been
> deleted; paths below into `firmware/src/CMD Soft/` are historical and no longer exist. The TCP
> protocol remains. Current main firmware uses `ESP32Encoder`, the canonical GUI is
> `tools/evka_gui`, and the current protocol reference is [../PROTOCOL.md](../PROTOCOL.md).

This document explains every change made to integrate the third-party CMD firmware/GUI protocol into the EvkaPosition system, and why each change was necessary.

For a short operational guide, see `docs/integration/CMD_SOFTWARE_INTEGRATION.md`.

## Background

At the time of integration, a third-party firm (CMD) provided ESP32 firmware
(`firmware/src/CMD Soft/main.cpp`) and a Windows C# GUI (`firmware/src/CMD Soft/gui.cs`). Those paths
are now deleted. Their system used:

- **WiFi AP**: SSID `CMDCNC`, password `cmdcnc1234`, static IP `192.168.1.50`
- **Raw TCP server** on port `8080`
- **Data format**: `X<val>,Y<val>,Z<val>\n` (e.g. `X123.45,Y-67.89,Z0.12\n`)
- **Commands**: `ZERO`, `GET_IP`, `WIFI_AYAR:<ssid>,<pass>` (Turkish)
- **Responses**: `SIFIRLANDI` (Turkish for "zeroed"), `STA_IP:<ip>`, `WIFI_KAYDEDILDI_REBOOT` (Turkish)
- **Encoder library**: ESP32Encoder (hardware PCNT)
- **NVS namespace**: `ayarlar` (Turkish for "settings")
- **Blocking architecture**: single-client, `while (client.connected())` loop with `delay(50)`

Our goal: make our hardware speak the same TCP protocol so the CMD GUI works with our device **unchanged**, while keeping our existing WebSocket dashboard and all its features.

---

## Firmware Changes

### 1. `firmware/src/SphericalSensor.h` — New Constants

| Constant | Value | Why |
|---|---|---|
| `ENABLE_CMD_TCP` | `1` | Feature flag — compile TCP server in/out without touching other code |
| `CMD_TCP_PORT` | `8080` | Must match CMD GUI's hardcoded port |
| `WIFI_AP_SSID` | `"CMDCNC_EVKA"` | Uses current project AP SSID while retaining CMD TCP/IP compatibility (`192.168.1.50:8080`) |
| `WIFI_AP_PASSWORD` | `"cmdcnc1234"` | Changed from `"evka1234"` to match CMD protocol |
| `WIFI_AP_IP_O1..O4` | `192.168.1.50` | CMD firmware uses `192.168.1.50` (we used `192.168.4.1`). Their GUI hardcodes this IP |
| `PIN_WIFI_LED` | `2` | GPIO 2 = built-in LED on most ESP32 boards, used for WiFi status indication |

**Why not just change the GUI?** The CMD GUI may be distributed to end users who won't update it. Matching their protocol means zero changes on the client side.

### 2. `firmware/src/CmdTcpServer.h` + `CmdTcpServer.cpp` — New Files

A dedicated TCP server class that runs alongside the existing HTTP+WebSocket server.

**Key design decisions:**

| Decision | Why |
|---|---|
| **Separate class** (not inline in `loop()`) | Keeps `EvkaPosition.cpp` clean; TCP server logic is self-contained |
| **Non-blocking `poll()` pattern** | CMD's original code used a blocking `while(client.connected())` loop — this freezes the entire MCU. Our non-blocking approach lets WebSocket, serial, and TCP all run concurrently |
| **Max 3 clients** | ESP32's lwIP stack has ~16 sockets total. HTTP+WS already use several. 3 TCP clients is a safe budget |
| **`setNoDelay(true)`** | Disables Nagle's algorithm (200ms batching). Without this, position data arrives in delayed bursts instead of real-time |
| **Per-client rx buffer with 128-byte limit** | Prevents a misbehaving client from consuming all heap with an endless string |

**Protocol compatibility — what CmdTcpServer sends:**

| Message | Format | Purpose |
|---|---|---|
| Position | `X<val>,Y<val>,Z<val>\n` | Identical to CMD format — their GUI parses this |
| Sensor data | `SENSOR,<r>,<theta>,<phi>,<valid>,<frame>\n` | **New** — our addition for richer GUIs. CMD GUI ignores lines not starting with `X` or `STA_IP:`, so this is safe |

**Commands handled directly by TCP server (not forwarded to main loop):**

| Command | Response | Why handled here |
|---|---|---|
| `GET_IP` | `STA_IP:<ip>` or `STA_IP:NOT_CONNECTED` | Matches CMD protocol. Response goes only to the requesting client |
| `WIFI_SET:<ssid>,<pass>` | `ACK:WIFI_SAVED` + reboot | NVS save + ESP restart. Also accepts `WIFI_AYAR:` for backward compat with original CMD GUI |

All other commands (`ZERO`, `PING`, `STATUS`, calibration commands, etc.) are forwarded to `processCommand()` in the main loop via `_pendingCmd`, and the reply is broadcast to all TCP clients.

### 3. `firmware/src/WebDashboard.cpp` — WiFi Init + HTML Additions

**WiFi initialization rewritten:**

```
Before:  WiFi.mode(WIFI_AP);  WiFi.softAP(ssid, pass);  // AP only, default 192.168.4.1
After:   WiFi.mode(WIFI_AP_STA);                         // AP + STA simultaneously
         WiFi.softAPConfig(192.168.1.50, ...);            // Static IP matching CMD
         WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD);
         // Load STA credentials from NVS "wifi_cfg" → WiFi.begin() if present
```

**Why AP+STA?** The device acts as an access point (clients connect directly) AND can join an existing WiFi network (for remote access, OTA, etc.). CMD's original firmware did this too.

**Why AP config before STA?** If STA init runs first and gets a DHCP address, the AP's DHCP server can conflict. AP-first avoids this.

**HTML/JS additions to the web dashboard** (all client-side, no firmware commands needed):

| Feature | What it does | Why |
|---|---|---|
| Per-axis software zero (X=0, Y=0, Z=0) | Subtracts current value as offset — display shows relative position | Matches CMD C# GUI behavior. Distinct from `ZERO` which resets encoder hardware |
| Min/Max tracking | Shows min and max values for each axis during the session | Useful for measuring travel range without external tools |
| Position snapshots | CAPTURE button logs X,Y,Z + timestamp to a table; export as CSV | Quick measurement recording without the full calibration workflow |
| WiFi settings | SSID/password inputs, SAVE & REBOOT, FORGET buttons | Lets users configure STA connection from the web dashboard |
| System info | RSSI, free heap, uptime, TCP client count | Diagnostic info; polls via `SYSINFO` command every 5 seconds |

### 4. `firmware/src/EvkaPosition.cpp` — Main Loop Integration

**New commands added to `processCommand()`:**

| Command | Response | Why |
|---|---|---|
| `GET_IP` | `STA_IP:<ip>` or `STA_IP:NOT_CONNECTED` | Needed by both GUIs and web dashboard to show router IP |
| `WIFI_SET:<ssid>,<pass>` | `ACK:WIFI_SAVED` + reboot | WiFi credential management from serial/WebSocket |
| `SYSINFO` | `SYSINFO,<rssi>,<heap>,<uptime_s>,<tcp_clients>` | System diagnostics for GUIs and web dashboard |

**WiFi LED logic (GPIO 2):**

| LED State | Meaning |
|---|---|
| OFF | No STA credentials configured (AP-only mode) |
| Blinking (500ms) | STA credentials exist but not yet connected (searching) |
| Solid ON | STA connected to router |

**TCP integration in `loop()`:**

```cpp
cmdTcp.poll();                    // Accept clients, read commands
String tcpCmd = cmdTcp.takePendingCommand();
if (tcpCmd.length() > 0) {
    String reply = processCommand(tcpCmd);
    if (reply.length() > 0) cmdTcp.sendToAllClients(reply.c_str());
}
// In the 50ms update block:
cmdTcp.broadcastPosition(x, y, z);      // X,Y,Z format
cmdTcp.broadcastSensorData(r, theta, phi, valid, frame);  // SENSOR format
```

### 5. `platformio.ini` — Build Filter

```
build_src_filter = +<src/> -<src/CMD Soft/>
```

**Historical reason:** The `CMD Soft/` folder contained reference code that used
`ESP32Encoder.h` (not then in the dependencies). Without this exclusion, PlatformIO attempted to
compile it and failed. The folder has since been deleted.

---

## GUI Changes

### C# GUI (`firmware/src/CMD Soft/gui.cs`) — Full Rewrite (Historical, Deleted)

The original CMD GUI was in Turkish with minimal features. We rewrote it in English with feature parity to our web dashboard.

**What changed and why:**

| Aspect | Original (CMD) | New | Why |
|---|---|---|---|
| Language | Turkish (SIFIRLA, BAĞLAN, etc.) | English | Project standard — all code and UI in English |
| Settings file | `ayarlar.txt` | `settings.txt` | English naming convention |
| WiFi command | `WIFI_AYAR:` | `WIFI_SET:` | English. Firmware accepts both for backward compatibility |
| Position display | X, Y, Z only | X, Y, Z + R, theta, phi + valid + frame | Richer diagnostic info using new `SENSOR,` message |
| Min/Max tracking | None | Per-axis min/max with reset button | Matches web dashboard feature |
| System info | None | RSSI, heap, uptime (polls `SYSINFO` every 5s) | Diagnostics without opening the web dashboard |
| WiFi settings | None visible | SSID/Password/SAVE/FORGET section | Configure STA connection from the GUI |
| Per-axis zero | None | X=0, Y=0, Z=0 buttons | Software zero with offset subtraction (client-side) |
| Hardware zero | "SIFIRLA" button | "Hardware Zero (Encoder)" with confirmation dialog | Prevents accidental encoder reset |

**What stayed the same:**

- TCP connection to port 8080
- Parsing of `X<val>,Y<val>,Z<val>\n` position data
- Parsing of `STA_IP:` responses
- Software zero offset subtraction approach (same logic as original)
- WinForms architecture and namespace (`CMDScanner`)

### Python GUI (`tools/position_checker/cmd_gui.py`) — New File

A Linux-native PyQt5 equivalent of the C# GUI, since the C# GUI only runs on Windows.

**Architecture:**

| Component | File | Purpose |
|---|---|---|
| `tcp_client.py` | `tools/position_checker/tcp_client.py` | Threaded TCP client with line-based receive loop |
| `cmd_gui.py` | `tools/position_checker/cmd_gui.py` | PyQt5 GUI — identical features to C# version |
| `cmd_main.py` | `tools/position_checker/cmd_main.py` | Entry point: `python -m tools.position_checker.cmd_main` |

**Why a separate TCP client class?** Qt's `QTcpSocket` requires the event loop to be running and has quirks with threading. A plain `socket` + `threading.Thread` with a callback queue is simpler and more reliable.

**Why PyQt5?** The existing `position_checker` tool already uses PyQt5 (via pyqtgraph). No new dependency.

---

## Protocol Compatibility Matrix

| Feature | CMD Original | Our Firmware | Notes |
|---|---|---|---|
| AP SSID/Password | `CMDCNC` / `cmdcnc1234` | `CMDCNC_EVKA` / `cmdcnc1234` | Password and IP/port are compatible; SSID string differs by project naming |
| AP IP | `192.168.1.50` | `192.168.1.50` | Matched |
| TCP Port | `8080` | `8080` | Matched |
| Data format | `X<v>,Y<v>,Z<v>\n` | `X<v>,Y<v>,Z<v>\n` | Identical |
| ZERO command | `ZERO` → `SIFIRLANDI` | `ZERO` → `ACK:ZERO` | Response differs but CMD GUI doesn't parse it |
| GET_IP | `GET_IP` → `STA_IP:<ip>` | `GET_IP` → `STA_IP:<ip>` | Identical |
| WiFi save | `WIFI_AYAR:` → `WIFI_KAYDEDILDI_REBOOT` | `WIFI_SET:` or `WIFI_AYAR:` → `ACK:WIFI_SAVED` | Both accepted; response differs but CMD GUI doesn't parse it |
| Sensor data | N/A | `SENSOR,r,theta,phi,valid,frame\n` | New — CMD GUI ignores it (no `X` prefix) |
| System info | N/A | `SYSINFO,rssi,heap,uptime,tcp_clients\n` | New — CMD GUI ignores it |
| NVS namespace | `ayarlar` | `wifi_cfg` | Different namespace but same keys (`ssid`, `pass`) |
| Encoder library | ESP32Encoder (PCNT) | PaulStoffregen Encoder (ISR) | Same quadrature math, different driver |
| Blocking model | Single client, blocking loop | Multi-client, non-blocking poll | CMD GUI sees no difference |

**Historical bottom line:** The original CMD C# GUI connected to the retained protocol. The vendor
application has since been deleted; current clients use `tools/evka_gui`.

---

## NVS Namespace Changes

| Purpose | CMD Original | Our Firmware | Keys |
|---|---|---|---|
| WiFi credentials | `ayarlar` | `wifi_cfg` | `ssid`, `pass` |
| Encoder calibration | N/A | `evka_cal` | `ppr_rotary`, `ppr_wire` |

**Why different namespace?** The CMD firmware stored WiFi credentials in `ayarlar` ("settings" in Turkish). We use `wifi_cfg` for clarity. This means WiFi credentials saved by the CMD firmware won't carry over — a one-time re-entry after flashing our firmware.

---

## What We Did NOT Change

| Item | Why kept as-is |
|---|---|
| Encoder library (PaulStoffregen) | Works correctly at our PPR. ESP32Encoder (PCNT) is safer at high PPR under WiFi load but would require testing all calibration values |
| WebSocket dashboard features | All existing features (3D trail, 2D projections, calibration tabs, CSV export) remain unchanged |
| Serial command protocol | All serial commands work identically — TCP is an additional interface |
| Coordinate math | Same spherical-to-Cartesian conversion, same EMA filter (alpha=0.2) |
| Update rate | 20 Hz (50ms period) — same as CMD's `delay(50)` |
| `CMD Soft/main.cpp` | Was kept as reference code during integration and was later deleted |

---

## Build Verification

```
$ pio run -e wemos_d1_r32
RAM:   [=         ]  14.1% (used 46256 bytes from 327680 bytes)
Flash: [=======   ]  68.1% (used 892069 bytes from 1310720 bytes)
========================= [SUCCESS] =========================
```

Both servers (HTTP+WS on :80 and raw TCP on :8080) fit comfortably within ESP32's resources.
