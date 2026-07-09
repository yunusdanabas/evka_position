# Circuit Schematic — Wireless Button Remote

ESP-NOW 2-button pendant for the EvkaPosition positioning system.

## System Block Diagram

```
  +-----------+     ESP-NOW (2.4 GHz)     +-------------------+
  |  BUTTON   | ~~~~~~~~~~~~~~~~~~~~~~~~> |   MAIN ESP32      |
  |  REMOTE   |    1-5 ms latency         | (EvkaPosition)    |
  | (ESP32-C3)|    50m+ indoor range      | WiFi AP           |
  +-----------+                           | "CMDCNC_EVKA"     |
       |                                  +-------------------+
    [LiPo]                                       |
    500 mAh                                  [Encoders]
  (via expansion                               [Web Dashboard]
     board)
```

## Full Circuit Schematic

```
                  ESP32-C3 SuperMini + Expansion Board
                  +------------------------------------+
                  |                                    |
  3.3V ------+---| 3V3                         GPIO4 |----+----[BTN_0]----GND   SAVE_POINT (Green)
              |   |                                    |   |
              |   |                             GPIO5 |----+----[BTN_1]----GND   DEL_POINT (Red)
              |   |                                    |
              |   |                             GPIO8 |--- built-in blue LED (send feedback)
              |   |                             USB-C |  <-- Programming / charging
              |   |                                    |
              |   | BAT+      (expansion board)  BAT- |---> LiPo 3.7V 500mAh
              |   +------------------------------------+
              |
  Optional future: GPIO2 <-- 100k/100k divider <-- BAT+ (battery voltage sense)
```

## Button Wiring Detail (per button)

```
        ESP32-C3 GPIO (4 or 5)
               |
               +--- Internal pull-up (enabled in firmware)
               |
           [BUTTON]
           (NO, tactile)
               |
              GND

      State: Released = HIGH (pull-up), Pressed = LOW (to GND)
      Debounce: 50 ms in firmware (always-awake loop)
      No hardware capacitor needed — short traces only.
```

## Pin Assignment Table

| GPIO | Function | Button Color | Main-board command |
|------|----------|-------------|-------------------|
| GPIO 4 | BTN0 | Green | `SAVE_POINT` |
| GPIO 5 | BTN1 | Red | `DEL_POINT` |
| GPIO 8 | LED feedback | — | Built-in blue LED (active HIGH) |
| GPIO 2 | (optional) | — | Future battery ADC (100k/100k divider) |

## Power Architecture

```
                    ESP32-C3 SuperMini + Expansion Board
                   +--------------------------------------+
  USB-C 5V -------| USB-C   Charge IC (TP4056)   BAT+/- |----> LiPo 3.7V 500 mAh
                   |                                      |
                   | LDO 3.3V ------> ESP32-C3 core       |
                   +--------------------------------------+

  Current firmware: always-awake with 10 s ESP-NOW heartbeat.
  Expect shorter battery life than deep-sleep designs (~days to weeks on 500 mAh,
  depending on supply and WiFi activity). USB charging between sessions is typical.
```

## ESP-NOW Communication

```
  Button Remote (Sender)              Main ESP32 (Receiver)
  ========================           =========================

  Boot: scan CMDCNC_EVKA SSID         WiFi AP "CMDCNC_EVKA" running
        set WiFi channel                      esp_now_init() active
        esp_now_init() once                   esp_now_register_recv_cb()
        add broadcast peer                          |
             |                                      |
  Loop: heartbeat 0xFE every 10 s ----------------> REMOTE_HB (TCP/WS)
             |                                      |
  Button press → send index 0-4 -------------------> REMOTE_BTN:n
                                             processCommand(SAVE/DEL_POINT)
                                             Serial + WebSocket + TCP
```

## Strapping Pin Notes (ESP32-C3)

| GPIO | Strapping | Safe as Button? | Safe as Output? | Notes |
|------|----------|----------------|----------------|-------|
| 2 | SPI boot (HIGH/float required) | Yes (ADC input OK) | Yes | Optional battery sense |
| 3 | None | Yes | Yes | BTN4 in test wiring |
| **4** | None | **Yes — BTN0** | Yes | Green / SAVE_POINT |
| **5** | None | **Yes — BTN1** | Yes | Red / DEL_POINT |
| 8 | Flash voltage select | Avoid (input) | **Yes (output)** | Built-in LED |
| 9 | Boot mode select | **Avoid** | Avoid | LOW at reset → download mode |

## Assembly Notes

1. Solder 2 tactile switches to the expansion board header or a perfboard
2. Wire each button: one terminal to GPIO 4 or 5, other terminal to GND
3. Connect LiPo battery to BAT+/BAT- pads on the expansion board
4. Optional: slide switch in series with BAT+ for hard power cutoff
5. LED feedback uses the built-in GPIO 8 LED — no external LED needed

## Enclosure Recommendations

- **3D printed pendant**: 50 × 35 × 20 mm, 2 mm wall thickness
- **Hammond 1551MBK**: 50 × 35 × 20 mm black ABS
- Side cutout for USB-C charging; wrist lanyard loop optional
