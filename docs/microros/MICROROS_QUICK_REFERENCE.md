# micro-ROS ESP32 Quick Reference Card

**TL;DR version** for busy developers working with ESP32 sensor data publishing to ROS 2.

---

## 1. Installation (2 minutes)

### PlatformIO Setup
```bash
# platformio.ini
[env:esp32_microros]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps = https://github.com/micro-ROS/micro_ros_platformio

board_microros_distro = humble
board_microros_transport = serial
```

### Build & Upload
```bash
pio run -e esp32_microros --target upload
```

---

## 2. Minimal Publisher (Copy-Paste Ready)

```cpp
#include <micro_ros_arduino.h>
#include <std_msgs/msg/int32.h>

rcl_allocator_t allocator;
rclc_support_t support;
rcl_node_t node;
rcl_publisher_t pub;
std_msgs__msg__Int32 msg;

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    set_microros_serial_transports(Serial);
    allocator = rcl_get_default_allocator();
    rclc_support_init(&support, 0, NULL, &allocator);
    rclc_node_init_default(&node, "my_node", "", &support);
    
    rclc_publisher_init_default(&pub, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "my_topic");
    
    Serial.println("Ready!");
}

void loop() {
    static unsigned long last = 0;
    if (millis() - last > 50) {  // 20 Hz
        msg.data++;
        rcl_publisher_publish(&pub, &msg, NULL);
        last = millis();
    }
    delay(10);
}
```

---

## 3. Launch Agent (Pick One)

### Docker (No ROS 2 install needed)
```bash
docker run -it --rm -v /dev:/dev --privileged --net=host \
    microros/micro-ros-agent:rolling \
    serial --dev /dev/ttyUSB0 -v6
```

### Direct (Requires ROS 2 Humble)
```bash
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -v6
```

---

## 4. Verify It Works

```bash
# Terminal A: Agent running (see section 3)

# Terminal B: Check topics
ros2 topic list
# Should show: /my_topic

# Terminal C: Echo data
ros2 topic echo /my_topic
# Should show: data: 1, data: 2, data: 3, ...

# Terminal D: Check frequency
ros2 topic hz /my_topic
# Should show: ~20 Hz
```

---

## 5. Common Patterns

### Multiple Publishers (Encoders)
```cpp
rcl_publisher_t pub_theta, pub_phi, pub_wire;

void setup() {
    // ... init code ...
    rclc_publisher_init_default(&pub_theta, &node, 
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "theta");
    rclc_publisher_init_default(&pub_phi, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "phi");
    rclc_publisher_init_default(&pub_wire, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "wire");
}

void loop() {
    msg.data = encoder_theta.read();
    rcl_publisher_publish(&pub_theta, &msg, NULL);
    
    msg.data = encoder_phi.read();
    rcl_publisher_publish(&pub_phi, &msg, NULL);
    
    msg.data = encoder_wire.read();
    rcl_publisher_publish(&pub_wire, &msg, NULL);
    
    delay(50);
}
```

### WiFi Transport
```cpp
void setup() {
    IPAddress agent_ip(192, 168, 1, 100);  // Your host PC
    set_microros_wifi_transports("SSID", "PASSWORD", agent_ip, 8888);
    // ... rest of init ...
}
```

### Subscriber (Receive Commands)
```cpp
rcl_subscription_t sub;
std_msgs__msg__Int32 sub_msg;

void callback(const void* msgin) {
    const std_msgs__msg__Int32* msg = (std_msgs__msg__Int32*)msgin;
    Serial.printf("Received: %ld\n", msg->data);
}

void setup() {
    rclc_subscription_init_default(&sub, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "command");
    
    rclc_executor_init(&executor, &support.context, 1, &allocator);
    rclc_executor_add_subscription(&executor, &sub, &sub_msg,
        &callback, ON_NEW_DATA);
}

void loop() {
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(100));
    delay(10);
}
```

---

## 6. Troubleshooting in 30 Seconds

| Symptom | Fix |
|---------|-----|
| Agent won't connect | Check `/dev/ttyUSB0` exists: `ls /dev/tty*` |
| Can't build | Run `pio run --target clean_microros` then rebuild |
| No topics appear | Check agent shows "connected" and is still running |
| Latency >20ms | Serial @ 115200 is normal; try 460800 if supported |
| Out of memory | Reduce publishers (limit to 4-5), reduce message frequency |
| Garbage data | Baud rate mismatch; verify 115200 in code + agent |

---

## 7. Performance Expectations

### Serial @ 115200 baud
- **Latency:** 5 ms (±2 ms)
- **Bandwidth:** 10 KB/s usable
- **Max frequency:** 100 Hz (small messages)
- **Best for:** Real-time control, 3-5 sensors @ 20-50 Hz

### WiFi (2.4 GHz)
- **Latency:** 20 ms (±15 ms)
- **Bandwidth:** 50 MB/s
- **Max frequency:** 1000+ Hz
- **Best for:** Monitoring dashboards, wireless convenience

### Ethernet
- **Latency:** 2 ms (±1 ms)
- **Bandwidth:** 100 MB/s
- **Best for:** High-precision robotics, lab environments

**For evka_position:** Use Serial for deterministic encoder reading.

---

## 8. WiFi + Serial Comparison

```
Need wireless?  →  Use WiFi
                    Expected latency: 20 ms

Need <10 ms latency?  →  Use Serial (115200 baud)
                          Expected latency: 5 ms

Performance critical (robotics, control)?  →  Serial
Telemetry/monitoring?  →  WiFi
Lab with cables?  →  Ethernet
```

---

## 9. Key File Locations

- **Library:** `~/.platformio/lib/micro_ros_platformio/`
- **Agent Docker:** `microros/micro-ros-agent:rolling`
- **Examples:** https://github.com/micro-ROS/micro_ros_arduino/tree/main/examples
- **Docs:** https://micro.ros.org/

---

## 10. Common Message Types

```cpp
#include <std_msgs/msg/int32.h>
#include <std_msgs/msg/float32.h>
#include <std_msgs/msg/string.h>
#include <sensor_msgs/msg/imu.h>
#include <geometry_msgs/msg/twist.h>

// All publishers use same pattern:
rclc_publisher_init_default(&pub, &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(PACKAGE, msg, TYPE), "topic");
```

---

## 11. Single-Command Cheatsheet

```bash
# Build firmware
pio run -e esp32_microros --target upload

# Run agent (Docker)
docker run -it --rm -v /dev:/dev --privileged --net=host \
    microros/micro-ros-agent:rolling serial --dev /dev/ttyUSB0

# Watch data
ros2 topic echo /my_topic

# Measure frequency
ros2 topic hz /my_topic

# Publish test command
ros2 topic pub --once /cmd std_msgs/msg/Int32 "data: 42"
```

---

## 12. Integration Checklist

- [ ] Firmware builds without errors
- [ ] Device flashes successfully
- [ ] USB/serial cable connected
- [ ] Agent running (docker or native)
- [ ] `ros2 topic list` shows publisher topics
- [ ] `ros2 topic echo` displays data (20 Hz expected)
- [ ] No "publish failed" errors in serial monitor
- [ ] Heap doesn't drop below 50 KB (check `ESP.getFreeHeap()`)

---

## Next Steps

1. **Basic:** Copy minimal example above, customize sensor reading
2. **Advanced:** Add WiFi transport for wireless development
3. **Production:** Switch to Ethernet for deterministic latency
4. **Integration:** Read `MICROROS_ESP32_INTEGRATION.md` for full patterns

---

## Links

- [micro-ROS docs](https://micro.ros.org/)
- [Micro-ROS Arduino lib](https://github.com/micro-ROS/micro_ros_arduino)
- [Micro-ROS PlatformIO](https://github.com/micro-ROS/micro_ros_platformio)
- [ROS 2 Message Types](https://docs.ros.org/en/humble/Concepts/Basic/About-ROS-2-Messages.html)

---

**Estimated time to working publisher:** 5-10 minutes with this guide.

