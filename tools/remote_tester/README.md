# tools/remote_tester — wireless pendant test GUI

A minimal PyQt5 GUI for bench-testing the **ESP32-C3 button remote** in its standalone test mode.
It shows live press events for all 5 buttons plus the heartbeat, and can request a
`PINS` snapshot for the readable ESP32-C3 GPIOs so you can confirm the pendant
hardware and firmware work before pairing it (via ESP-NOW) with the main sensor board.

## What it talks to

The **`button_remote_test`** firmware env (`firmware/tests/ButtonRemoteTest/`). That firmware makes
its own WiFi access point and a TCP server (it does **not** use ESP-NOW — that's the point: it's a
direct, observable link for testing):

- AP: `REMOTE_TEST` / `remote1234`
- Default IP/port: `192.168.4.1:8080`

(The main pendant firmware, `firmware/remote/`, uses ESP-NOW broadcast instead and needs no GUI.)

## Run

```bash
# 1. Flash the test firmware:
pio run -e button_remote_test --target upload
# 2. Join WiFi "REMOTE_TEST", then:
python tools/remote_tester/remote_test_gui.py
```

Same UI is also in the unified GUI: **Remote Tester…** toolbar action
(`python -m tools.evka_gui`).

Button map (test firmware): BTN0 = ADD POINT, BTN1 = DEL POINT, BTN2–4 = raw GPIO 0/1/3.

Commands accepted by the test firmware over TCP or USB serial:

| Command | Response |
|---|---|
| `PING` | `ACK:PONG` |
| `PINS` | `PINS,GPIO0=...,GPIO1=...` for GPIO `0,1,2,3,4,5,6,7,8,9,10,20,21` |
| `HELP` | `HELP:PING,PINS,HELP` |

The GUI's **READ PINS** button sends `PINS` over the TCP test connection. The
firmware also accepts `PINS\n` on `/dev/ttyACM0` at 115200 baud for USB-only checks.

See also: `docs/hardware_design/remote/` (pendant hardware) and the `button_remote` main firmware
environment.
