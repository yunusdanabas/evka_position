# Circuit Schematic — Wireless Button Remote

ESP-NOW 2-button pendant for the EvkaPosition positioning system.

## System Block Diagram

```
  +-----------+     ESP-NOW (2.4 GHz)     +-------------------+
  |  BUTTON   | ~~~~~~~~~~~~~~~~~~~~~~~~> |   MAIN ESP32      |
  |  REMOTE   |    1-5 ms latency         | (EvkaPosition)    |
  | (ESP32-C3)|    50m+ indoor range      | WiFi AP "CMDCNC"  |
  +-----------+                           +-------------------+
       |                                         |
    [LiPo]                                   [Encoders]
    500 mAh                                  [Web Dashboard]
  (via expansion
     board)
```

## Full Circuit Schematic

```
                  ESP32-C3 SuperMini + Expansion Board
                  +------------------------------------+
                  |                                    |
  3.3V ------+---| 3V3                         GPIO4 |----+----[BTN_0]----GND   ZERO (Red)
              |   |                                    |   |
              |   |                             GPIO5 |----+----[BTN_1]----GND   SAVE_POINT (Green)
              |   |                                    |
              |   |                             GPIO8 |---[330R]---[LED]---GND   (status LED, optional
              |   |                                    |                           built-in on SuperMini)
              |   |                             USB-C |  <-- Programming
              |   |                                    |
              |   | BAT+      (expansion board)  BAT- |---> LiPo 3.7V 500mAh
              |   +------------------------------------+
              |
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
      Debounce: handled in firmware (20 ms delay after wake-up)
      No hardware capacitor needed — short traces only.
```

## Pin Assignment Table

| GPIO | Function | Button Color | Command |
|------|----------|-------------|---------|
| GPIO 4 | BTN_ZERO | Red | `ZERO` |
| GPIO 5 | BTN_SAVE_POINT | Green | `SAVE_POINT` |
| GPIO 8 | LED feedback | — | Built-in blue LED (active HIGH) |

## Power Architecture

```
                    ESP32-C3 SuperMini + Expansion Board
                   +--------------------------------------+
  USB-C 5V -------| USB-C   Charge IC (TP4056)   BAT+/- |----> LiPo 3.7V 500 mAh
                   |                                      |
                   | LDO 3.3V ------> ESP32-C3 core       |
                   | VCC1/VCC2 = 3.3V (adjustable 3.7V)  |
                   +--------------------------------------+

  Power consumption:
    Deep sleep:    ~44 µA (ESP32-C3 + SuperMini regulators)
    Active send:   ~120 mA for ~10 ms per button press
    Average:       < 0.05 mA (assuming 100 presses/day)
    Battery life:  ~500 mAh / 0.05 mA = ~10,000 hours = ~14 months
```

## ESP-NOW Communication

```
  Button Remote (Sender)              Main ESP32 (Receiver)
  ========================           =========================

  [Deep Sleep]                        WiFi AP "CMDCNC" running
       |                              esp_now_init() active
  Button press → GPIO wake            esp_now_register_recv_cb()
       |                                     |
  esp_deep_sleep_enable_gpio_wakeup()        |
       |                                     |
  Wake (~300 µs)                             |
       |                                     |
  Read GPIO → button_id (0 or 1)            |
       |                                     |
  WiFi.mode(WIFI_STA)                       |
  esp_wifi_set_channel(1)                   |
  esp_now_init()                            |
  esp_now_send(broadcast, &button_id, 1)    |
       |                                     |
       +------------- 2.4 GHz ------------>  |
                    1-5 ms                   |
                                       onEspNowRecv() callback
                                       espnow_pending_button = btn
                                             |
  esp_now_deinit()                     loop() picks up pending button
  → Deep Sleep                         processCommand(REMOTE_BUTTON_CMD[btn])
                                             |
                                       Serial + WebSocket broadcast
```

## Strapping Pin Notes (ESP32-C3)

| GPIO | Strapping | Safe as Button? | Safe as Output? | Notes |
|------|----------|----------------|----------------|-------|
| 2 | SPI boot (HIGH/float required) | Yes | Yes | Internal pull-up keeps HIGH at boot |
| 3 | None | Yes | Yes | General purpose |
| **4** | None | **Yes — used for BTN_ZERO** | Yes | No constraints |
| **5** | None | **Yes — used for BTN_SAVE_POINT** | Yes | No constraints |
| 6 | None | Yes | Yes | General purpose |
| 8 | Flash voltage select | Avoid (input) | **Yes (output)** | Must be HIGH at boot; built-in LED — output use fine after boot |
| 9 | Boot mode select | **Avoid** | Avoid | LOW at reset → download mode |

## Assembly Notes

1. Solder 2 tactile switches to the expansion board header or a perfboard
2. Wire each button: one terminal to the GPIO pin (4 or 5), other terminal to GND
3. Connect LiPo battery to BAT+/BAT- pads on the expansion board
5. Optional: add slide switch in series with BAT+ for hard power cutoff
6. LED feedback is provided by the built-in GPIO 8 LED — no external LED needed

## Enclosure Recommendations

- **3D printed pendant**: 50 × 35 × 20 mm, 2 mm wall thickness
  - 2 × 12 mm holes for button caps on top face
  - Side cutout for USB-C charging
  - Bottom or side slot for LiPo
  - Wrist lanyard loop
- **Hammond 1551MBK**: 50 × 35 × 20 mm black ABS
- **Mounting**: Velcro strip on back or magnetic mount (10 mm neodymium disc)
