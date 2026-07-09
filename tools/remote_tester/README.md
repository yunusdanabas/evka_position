# tools/remote_tester — wireless pendant test GUI

A minimal PyQt5 GUI for bench-testing the **ESP32-C3 button remote** in its standalone test mode.
It shows live press events for all 5 buttons plus the heartbeat, so you can confirm the pendant
hardware and firmware work before pairing it (via ESP-NOW) with the main sensor board.

## What it talks to

The **`button_remote_test`** firmware env (`firmware/tests/ButtonRemoteTest/`). That firmware makes
its own WiFi access point and a TCP server (it does **not** use ESP-NOW — that's the point: it's a
direct, observable link for testing):

- AP: `REMOTE_TEST` / `remote1234`
- Default IP/port: `192.168.4.1:8080`

(The production pendant, `firmware/remote/`, uses ESP-NOW broadcast instead and needs no GUI.)

## Run

```bash
# 1. Flash the test firmware:
pio run -e button_remote_test --target upload
# 2. Join WiFi "REMOTE_TEST", then:
python tools/remote_tester/remote_test_gui.py
```

Button map (test firmware): BTN0 = ADD POINT, BTN1 = DEL POINT, BTN2–4 = raw GPIO 0/1/3.

See also: `docs/hardware_design/remote/` (pendant hardware) and the `button_remote` env (production
firmware).
