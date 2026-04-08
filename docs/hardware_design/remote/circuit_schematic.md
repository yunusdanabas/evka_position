# Circuit Schematic — Wireless Button Remote

ESP-NOW button pendant for the EvkaPosition positioning system.

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
```

## Full Circuit Schematic

```
                     XIAO ESP32-C3
                  +------------------+
                  |                  |
  +3.3V ----+----| 3V3         D0/2 |----+----[BTN_0]----GND     SAVE_POINT (Green)
             |    |                  |    |
             |    |            D1/3 |----+----[BTN_1]----GND     ZERO (Red)
             |    |                  |    |
             |    |            D2/4 |----+----[BTN_2]----GND     RECORD (Blue)
             |    |                  |    |
             |    |            D3/5 |----+----[BTN_3]----GND     ZERO_T (Yellow)
             |    |                  |    |
             |    |            D4/6 |----+----[BTN_4]----GND     ZERO_W (White)
             |    |                  |
             |    |         USB-C   |  <-- Programming + LiPo charging
             |    |                  |
             |    | BAT+        BAT-|
             |    +-----|---------|--+
             |          |         |
             |    +-----|---------|--+
             |    | +        SW    - |
             |    |    LiPo 500mAh   |
             |    +------------------+
             |
             +---[330R]---[LED]---GND    (optional status LED)
```

## Button Wiring Detail (per button)

```
        XIAO GPIO (D0-D4)
             |
             +--- Internal pull-up (enabled in firmware)
             |
     +-------+-------+
     |               |
  [100nF]        [BUTTON]
     |          (NO, tactile)
     |               |
    GND             GND

    State: Released = HIGH (pull-up), Pressed = LOW (to GND)
    100nF capacitor provides hardware debounce (RC tau ~ 1ms with 10k pull-up)
```

## Pin Assignment Table

| XIAO Pin | GPIO | Function | Button Color | Command |
|----------|------|----------|-------------|---------|
| D0 | GPIO 2 | BTN_SAVE_POINT | Green | `SAVE_POINT` |
| D1 | GPIO 3 | BTN_ZERO | Red | `ZERO` |
| D2 | GPIO 4 | BTN_RECORD | Blue | `RECORD_TOGGLE` |
| D3 | GPIO 5 | BTN_ZERO_THETA | Yellow | `ZERO_T` |
| D4 | GPIO 6 | BTN_ZERO_WIRE | White | `ZERO_W` |

## Power Architecture

```
                          XIAO ESP32-C3 (built-in charger)
                         +--------------------------------+
  USB-C 5V -----+-------| VUSB    Charge IC    BAT+/BAT-|----> LiPo 3.7V
                 |       |        (370 mA)                |     500 mAh
                 |       |                                |
                 |       | LDO 3.3V -----> ESP32-C3 core  |
                 |       +--------------------------------+
                 |
             (charging)

  Power consumption:
    Deep sleep:    ~44 uA (ESP32-C3 + XIAO regulators)
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
  Wake (~300 us)                             |
       |                                     |
  Read GPIO → button_id (0-4)               |
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

| GPIO | Strapping | Safe for Button? | Notes |
|------|----------|-----------------|-------|
| **2** | SPI boot (must be HIGH/float) | **Yes** | Internal pull-up keeps HIGH at boot |
| **3** | None | **Yes** | General purpose |
| **4** | None | **Yes** | General purpose |
| **5** | None | **Yes** | General purpose |
| **6** | None | **Yes** | General purpose |
| 8 | Flash voltage select | **Avoid** | Must be HIGH at boot for 3.3V flash |
| 9 | Boot mode select | **Avoid** | LOW = download mode |

## Assembly Notes

1. Solder 5 tactile switches to a perfboard or custom PCB
2. Wire each button: one terminal to the XIAO GPIO pin, other terminal to GND
3. Solder 100nF capacitor across each button (GPIO pad to GND pad)
4. Connect LiPo battery to BAT+/BAT- pads on XIAO bottom side
5. Optional: add slide switch in series with BAT+ for power cutoff
6. Optional: add LED + 330R resistor to a free GPIO
7. Mount in 3D printed enclosure with button caps protruding through top panel

## Enclosure Recommendations

- **3D printed pendant**: 80 x 45 x 25 mm, 2mm wall thickness
  - 5 x 12mm holes for button caps on top face
  - Side cutout for USB-C charging
  - Bottom battery compartment
  - Wrist lanyard loop
- **Hammond 1551KTBU**: 80 x 40 x 20 mm translucent blue ABS box
- **Mounting**: Velcro strip on back or magnetic mount (10mm neodymium disc)
