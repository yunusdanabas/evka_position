# EvkaPosition Integration Guide

Hey, this doc covers everything you need to understand what this system does and how to pull data from it into your own software. 
I'll walk through the hardware, how data flows, and the different ways you can connect — including a WebSocket path and a .NET bridge approach I'd recommend for your use case.

---

## What Is This?

EvkaPosition measures where the tip of a our device is in 3D space — X, Y, Z in millimeters — using three encoders attached to the arm's joints. An ESP32 microcontroller reads all three sensors, computes the position 20 times per second, and sends it out over USB serial and/or WiFi. No external PC required to run the measurement itself.

---

## The Hardware

Three sensors, one microcontroller:

| Sensor | Model | What it measures |
|---|---|---|
| Theta encoder | Autonics E40S6 | Horizontal rotation angle |
| Phi encoder | Autonics E40S6 | Vertical tilt angle |
| Draw-wire encoder | OPKON DWE3000 | Arm extension distance (mm) |
| Microcontroller | ESP32 (Wemos D1 R32) | Reads sensors, computes position, sends data |

---

## How the Position Is Computed

Every 50 ms the firmware runs through this pipeline:

```
Raw encoder pulses (3 sensors)
        |
        | pulses × scale factor → angles and distance
        v
  r     = arm extension in mm
  theta = horizontal angle in degrees
  phi   = vertical angle in degrees
        |
        | x = r · cos(phi) · cos(theta)
        | y = r · cos(phi) · sin(theta)
        | z = r · sin(phi)
        v
  X, Y, Z in millimeters
        |
        | EMA low-pass filter (alpha = 0.2) to smooth noise
        v
  Final output — valid or flagged if outside physical limits
```

Resolution is about 0.018° per pulse on the rotary encoders and ~0.025 mm per pulse on the draw-wire. On power-up the firmware waits 2 seconds then snapshots all encoder positions as the zero point — the robot has to be at its home position at that moment.

---

## Getting Data Out

There are two physical paths. The data format is identical on both.

### USB Serial

Plug in a USB cable, open the port at **115200 baud**. Every 50 ms you get:

```
DATA,x,y,z,r,theta,phi,is_valid,frame,timestamp_ms
```

Real example:
```
DATA,123.45,67.89,-12.34,140.00,28.500,-5.120,1,1042,52100
```

`is_valid` is `1` if the position is within the physical limits of the arm, `0` if something is out of range. You can also send text commands:

| Send | Response | Effect |
|---|---|---|
| `PING\n` | `ACK:PONG` | Connectivity check |
| `ZERO\n` | `ACK:ZERO` | Re-zero the position |
| `STATUS\n` | `STATUS,...` | One-shot full status line |

### WiFi WebSocket

With `ENABLE_WIFI=1` in the firmware, the ESP32 creates its own WiFi access point — no router needed.

| | |
|---|---|
| SSID | `EvkaPosition` |
| Password | `evka1234` |
| WebSocket | `ws://192.168.4.1/ws` |

Connect to the network, open the WebSocket, and you get the same `DATA,` lines at 20 Hz. Commands (`ZERO`, `PING`) work the same way — send them as text messages, get `ACK:...` back.

---

## Visualization (What I Already Built)

Three options are already in the repo:

**Browser dashboard (zero install):** With WiFi enabled, connect to `EvkaPosition` and open `http://192.168.4.1` in any browser. Live 3D view, XY/XZ/YZ projections, session logging, CSV export. Works on phones too.

**Python desktop app** (`tools/position_checker/`): PyQt5 + pyqtgraph, reads from USB serial or replays saved CSV files. 3D and 2D projection views.

```bash
cd tools/position_checker
pip install -r requirements.txt
python main.py
```

**Python web server** (`tools/web_server/`): Flask + Socket.IO + Three.js, reads from USB serial and re-broadcasts to multiple browser clients on the local network.

---

## How You Can Connect

Options are split into two groups: things the ESP32 can do directly after a firmware update, and things that go through a bridge PC. Both groups require no hardware changes.

### Direct from ESP32 (firmware additions)

**Option A — WebSocket (works today):** Connect to the `EvkaPosition` WiFi, open `ws://192.168.4.1/ws`, parse `DATA,` lines. Nothing to change on my end. Works in any language that supports WebSocket.

**Option B — REST polling (~10 lines of firmware):** I can add a `GET /api/position` endpoint that returns the latest position as JSON. Good if you prefer polling over a persistent connection.

```json
{ "x": 123.45, "y": 67.89, "z": -12.34, "r": 140.0, "theta": 28.5, "phi": -5.1, "valid": true }
```

**Option C — MQTT publish (moderate firmware change):** The ESP32 connects to an MQTT broker on your network and publishes every position update to a topic like `evka/position`. Any language has a client library, and multiple subscribers can receive the same stream simultaneously. The broker can be Mosquitto (free, runs on any PC) or a cloud broker if you need remote access.

```
ESP32 ──[WiFi]──> MQTT Broker ──[subscribe]──> your app
                               ──[subscribe]──> logging service
                               ──[subscribe]──> dashboard
```

Payload per message:
```json
{ "x": 123.45, "y": 67.89, "z": -12.34, "valid": true, "ts": 52100 }
```

**Option D — UDP broadcast (~5 lines of firmware):** The ESP32 broadcasts a UDP packet to `255.255.255.255` every 50 ms. Any device on the same WiFi network can listen without establishing a connection. Lowest possible latency, fire-and-forget. Good for real-time control systems that need the data fast and can tolerate an occasional dropped packet. Packet format is the same `DATA,x,y,z,...` string.

```
ESP32 ──[UDP broadcast]──> any listener on the network
```

**Option E — Raw TCP socket (~15 lines of firmware):** The ESP32 opens a TCP server (e.g. port 9000) and streams `DATA,` lines to any client that connects. Persistent connection, reliable delivery, works in any language with a socket API.

```python
import socket
s = socket.create_connection(("192.168.4.1", 9000))
for line in s.makefile():
    print(line.strip())
```

---

### Via a Bridge PC (no firmware changes needed)

These options sit between the ESP32 and your application. The bridge reads from USB serial or WebSocket and re-exposes the data in whatever protocol you need. The ESP32 doesn't change at all.

**Option F — ASP.NET Core + SignalR (what I'd recommend for your stack):** A Windows PC runs an ASP.NET Core server that reads from USB serial, then broadcasts via SignalR to your C# clients and exposes a REST API. Full detail in the section below.

```
ESP32 ──[USB or WiFi]──> ASP.NET Core server ──[SignalR]──> your C# clients
                                              ──[REST API]──> any HTTP client
                                              ──[SQLite]──> position history
```

**Option G — OPC UA bridge:** If you're integrating with industrial automation systems (PLCs, SCADA, MES), OPC UA is the standard they all speak. A bridge server (e.g. using `node-opcua` or `python-opcua`) reads from USB serial and exposes the position as OPC UA nodes. Any OPC UA client — Siemens, Beckhoff, Kepware, whatever your PLC uses — can subscribe directly.

```
ESP32 ──[USB serial]──> OPC UA server ──[OPC UA]──> PLC / SCADA / MES
```

**Option H — gRPC:** If your backend is microservice-based and you're already using gRPC elsewhere, a bridge can expose a `GetPosition` RPC and a `StreamPositions` server-streaming call. Strongly typed via protobuf, works across languages, and integrates cleanly into Kubernetes/service mesh setups if that's your environment.

```protobuf
service PositionService {
  rpc GetPosition(Empty) returns (Position);
  rpc StreamPositions(Empty) returns (stream Position);
}
```

---

## .NET Integration Detail

The ASP.NET Core server reads the serial port using `System.IO.Ports.SerialPort`, parses each `DATA,` line, and broadcasts via a SignalR hub. On your end, receiving live data is about 10 lines of C#:

```csharp
var connection = new HubConnectionBuilder()
    .WithUrl("http://localhost:5000/positionHub")
    .WithAutomaticReconnect()
    .Build();

connection.On<float, float, float>("PositionUpdate", (x, y, z) => {
    Console.WriteLine($"X={x:F1}mm  Y={y:F1}mm  Z={z:F1}mm");
});

await connection.StartAsync();
await Task.Delay(Timeout.Infinite);
```

`PositionUpdate` fires 20 times per second. Adding a REST endpoint, a WinForms view, or a database write is straightforward from there.

Packages you'll need on your side:

| Package | Purpose |
|---|---|
| `Microsoft.AspNetCore.SignalR.Client` | Connect to the hub |
| `Microsoft.EntityFrameworkCore.Sqlite` | Local DB if you want history (optional) |

On the server side (what I'd build or you can build):

| Package | Purpose |
|---|---|
| `Microsoft.AspNetCore.SignalR` | Hub |
| `System.IO.Ports` | USB serial on Windows |

---

## Key Files

| File | What's in it |
|---|---|
| `firmware/src/EvkaPosition.cpp` | Main loop, DATA output, serial command handler |
| `firmware/src/SphericalSensor.h` | Pin map, all config constants, data structs |
| `firmware/src/SphericalSensor.cpp` | Coordinate math, filter, validation |
| `firmware/src/WebDashboard.cpp` | WiFi AP, WebSocket server, embedded browser dashboard |
| `tools/position_checker/` | Python desktop visualizer |
| `tools/web_server/` | Flask multi-client server |
| `docs/hardware_design/system_architecture.md` | Full system architecture |
| `docs/hardware_design/circuit_schematic.md` | Circuit schematic with voltage dividers and protection |

---