# micro-ROS ESP32 Support 2024 — Complete Reference

## Executive Summary

micro-ROS (micro Robot Operating System) enables ROS 2 connectivity on resource-constrained microcontrollers including ESP32. As of 2024, **two main libraries** support this:

1. **micro_ros_arduino** — Precompiled library (Arduino IDE)
2. **micro_ros_platformio** — Full build system (recommended for ESP32)

Both support ESP32 with serial, WiFi, and Ethernet transports.

---

## 1. Quick Start: Library Setup

### Option A: Arduino IDE + micro_ros_arduino

```bash
# 1. Download from https://github.com/micro-ROS/micro_ros_arduino/releases
# 2. In Arduino IDE: Sketch → Include Library → Add .ZIP Library
# 3. Select Examples from micro-ROS library
```

**ESP32 Requirements:**
- Arduino ESP32 Core: v2.0.2 or later
- Baud rate: 115200 (serial transport)

### Option B: PlatformIO + micro_ros_platformio (Recommended)

**platformio.ini configuration:**

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
    https://github.com/micro-ROS/micro_ros_platformio

board_microros_distro = humble      ; or jazzy, kilted, rolling
board_microros_transport = serial    ; or wifi, ethernet

# ROS 2 message types (examples)
board_microros_extra_packages =
    ros2_geometry_msgs
    ros2_std_msgs
```

**Build workflow:**

```bash
pio lib install              # Install dependencies
pio run                      # Build firmware
pio run --target upload      # Flash to device
pio run --target clean_microros  # Rebuild library if config changed
```

---

## 2. ESP32 Hardware Configuration

### Supported Boards

| Board | Platform | Transports | Meta File | State |
|-------|----------|-----------|-----------|-------|
| ESP32 Dev Module | espressif32 | serial, wifi, ethernet | `colcon.meta` | ✅ Supported |
| ESP32-S3 | espressif32 | serial, wifi | `colcon.meta` | ✅ (community) |
| ESP32-C3 | espressif32 | serial, wifi | `colcon.meta` | ✅ (community) |

### Transport Selection

**Serial (115200 baud):**
```cpp
Serial.begin(115200);
set_microros_serial_transports(Serial);
```

**WiFi:**
```cpp
IPAddress agent_ip(192, 168, 1, 113);
size_t agent_port = 8888;
char ssid[] = "SSID";
char password[] = "PASSWORD";

set_microros_wifi_transports(ssid, password, agent_ip, agent_port);
```

**Ethernet:**
```cpp
set_microros_ethernet_transports();
```

---

## 3. Publishing Sensor Data (Encoder/IMU Example)

### Basic Publisher Pattern

```cpp
#include <micro_ros_arduino.h>
#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/publisher.h>
#include <std_msgs/msg/int32.h>
#include <std_msgs/msg/float32.h>

rcl_publisher_t publisher;
std_msgs__msg__Int32 msg;

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    set_microros_serial_transports(Serial);
    
    // Initialize RCL
    rcl_allocator_t allocator = rcl_get_default_allocator();
    rclc_support_t support;
    rcl_node_t node;
    
    rclc_support_init(&support, 0, NULL, &allocator);
    rclc_node_init_default(&node, "esp32_encoder", "", &support);
    
    // Create publisher for encoder ticks
    rclc_publisher_init_default(
        &publisher,
        &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "encoder_ticks");
    
    msg.data = 0;
}

void loop() {
    // Read sensor (example: quadrature encoder)
    int encoder_ticks = read_encoder();
    msg.data = encoder_ticks;
    
    // Publish message
    rcl_ret_t ret = rcl_publisher_publish(&publisher, &msg, NULL);
    if (ret != RCL_RET_OK) {
        Serial.println("Publish failed");
    }
    
    delay(50);  // 20 Hz publication rate
}
```

### Multi-Sensor Publisher (Encoder + IMU)

```cpp
#include <geometry_msgs/msg/twist.h>
#include <sensor_msgs/msg/imu.h>

rcl_publisher_t encoder_pub;
rcl_publisher_t imu_pub;

std_msgs__msg__Int32 encoder_msg;
sensor_msgs__msg__Imu imu_msg;

void setup() {
    // ... initialization code ...
    
    // Encoder publisher
    rclc_publisher_init_default(
        &encoder_pub,
        &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "encoder");
    
    // IMU publisher
    rclc_publisher_init_default(
        &imu_pub,
        &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs, msg, Imu),
        "imu/data");
}

void loop() {
    // Publish encoder
    encoder_msg.data = read_encoder();
    rcl_publisher_publish(&encoder_pub, &encoder_msg, NULL);
    
    // Publish IMU
    read_imu(&imu_msg);
    rcl_publisher_publish(&imu_pub, &imu_msg, NULL);
    
    delay(50);
}
```

---

## 4. Latency Characteristics

### Publication Latency

| Transport | Typical Latency | Bandwidth | Notes |
|-----------|-----------------|-----------|-------|
| **Serial** | 5-15 ms | 115.2 kbps | Deterministic, low jitter |
| **WiFi** | 10-50 ms | ~50 Mbps | Subject to congestion, ~5-10% packet loss typical |
| **Ethernet** | 1-5 ms | 100 Mbps | Most reliable, requires hardware |

### Message Publication Rate

Practical limits (ESP32):
- **Serial @ 115200 baud**: ~50-100 messages/sec (depending on message size)
- **WiFi**: ~100-500 messages/sec
- **Ethernet**: ~1000+ messages/sec

**Typical sensor data example (encoder + IMU):**
- Message size: ~100 bytes
- Serial rate: ~115 Kbps ÷ 100 bytes = ~115 messages/sec theoretical max
- Practical: 20-50 Hz recommended (50-200 ms interval)

---

## 5. rcl_publisher_publish API

```cpp
rcl_ret_t rcl_publisher_publish(
    rcl_publisher_t * publisher,
    const void * ros_message,
    rmw_subscription_allocator_t * allocator
);
```

**Parameters:**
- `publisher` — Initialized publisher handle
- `ros_message` — Pointer to populated ROS message (e.g., `&msg`)
- `allocator` — Memory allocator (usually NULL for default)

**Return values:**
- `RCL_RET_OK` — Success
- `RCL_RET_PUBLISHER_INVALID` — Invalid publisher
- `RCL_RET_INVALID_ARGUMENT` — NULL arguments

**Key points:**
- Non-blocking call
- Best-effort delivery (UDP-like semantics for WiFi/Ethernet)
- Serial is more reliable due to TCP-like behavior

---

## 6. micro-ROS Agent Setup

### Host Machine (Linux/macOS)

#### Installation

```bash
source /opt/ros/humble/setup.bash
mkdir microros_ws && cd microros_ws
git clone -b humble https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup

rosdep install --from-paths src --ignore-src -y
colcon build
source install/local_setup.bash
```

#### Run Agent (Serial)

```bash
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -v6
```

#### Run Agent (UDP/WiFi)

```bash
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888 -v6
```

#### Docker Alternative (Recommended)

```bash
# Serial
docker run -it --rm -v /dev:/dev --privileged --net=host \
    microros/micro-ros-agent:rolling \
    serial --dev /dev/ttyUSB0 -v6

# UDP
docker run -it --rm --net=host \
    microros/micro-ros-agent:rolling \
    udp4 --port 8888 -v6
```

### Verify Connection

```bash
# In another terminal (agent must be running)
ros2 topic list
ros2 node list
ros2 topic echo /encoder_ticks
```

---

## 7. Bandwidth Limits & Constraints

### Serial Transport
- **Max baud rate:** 115200 (standard on ESP32)
- **Effective bandwidth:** ~100 Kbps (accounting for start/stop bits)
- **MTU:** ~256 bytes typical
- **Latency:** Deterministic, <10 ms

### WiFi Transport
- **Bandwidth:** ~50 Mbps (practical)
- **Latency:** 10-50 ms average, can spike to 200+ ms
- **Packet loss:** 1-5% typical home WiFi
- **Network overhead:** ROS 2 + micro-ROS protocol adds ~50-100 bytes per message

### Memory Constraints (ESP32)
- **SRAM:** 520 KB (limited for complex message types)
- **Flash:** 4 MB typical
- **Recommended RCL config:**
  - Use `colcon.meta` standard config (not `colcon_verylowmem.meta`)
  - 4-8 publishers/subscribers maximum
  - Single-threaded executor

---

## 8. Real-World Examples from GitHub

### A. Simple Encoder Publisher (PlatformIO)

Repository: `hippo5329/micro_ros_arduino_examples_platformio`

```cpp
// Adapted encoder example
#include <micro_ros_arduino.h>
#include <std_msgs/msg/int32.h>

rcl_publisher_t publisher;
std_msgs__msg__Int32 msg;
Encoder myenc(33, 34);  // ESP32 pins

void setup() {
    Serial.begin(115200);
    set_microros_serial_transports(Serial);
    
    rcl_allocator_t allocator = rcl_get_default_allocator();
    rclc_support_t support;
    rclc_support_init(&support, 0, NULL, &allocator);
    
    rcl_node_t node;
    rclc_node_init_default(&node, "encoder_pub", "", &support);
    rclc_publisher_init_default(
        &publisher,
        &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "encoder_position");
}

void loop() {
    msg.data = myenc.read();
    rcl_publisher_publish(&publisher, &msg, NULL);
    delay(50);
}
```

### B. IMU Sensor Publisher (ROS 2 Sensor Messages)

```cpp
#include <sensor_msgs/msg/imu.h>

rcl_publisher_t imu_pub;
sensor_msgs__msg__Imu imu_msg;

void publish_imu() {
    imu_msg.linear_acceleration.x = accel_x;
    imu_msg.linear_acceleration.y = accel_y;
    imu_msg.linear_acceleration.z = accel_z;
    
    imu_msg.angular_velocity.x = gyro_x;
    imu_msg.angular_velocity.y = gyro_y;
    imu_msg.angular_velocity.z = gyro_z;
    
    // Set header with timestamp
    imu_msg.header.stamp.sec = get_time_sec();
    imu_msg.header.stamp.nanosec = get_time_nsec();
    imu_msg.header.frame_id.data = "imu_link";
    
    rcl_publisher_publish(&imu_pub, &imu_msg, NULL);
}
```

---

## 9. Complete Minimal Example

### platformio.ini

```ini
[env:esp32dev_microros]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
    https://github.com/micro-ROS/micro_ros_platformio
    paulstoffregen/Encoder @ ^1.4.2

board_microros_distro = humble
board_microros_transport = serial
```

### src/main.cpp

```cpp
#include <micro_ros_arduino.h>
#include <rcl/rcl.h>
#include <rcl/publisher.h>
#include <std_msgs/msg/int32.h>
#include <Encoder.h>

rcl_publisher_t publisher;
std_msgs__msg__Int32 msg;
Encoder encoder(32, 35);  // Example pins

const unsigned long PUBLISH_INTERVAL = 50;  // 20 Hz
unsigned long last_publish = 0;

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    set_microros_serial_transports(Serial);
    
    rcl_allocator_t allocator = rcl_get_default_allocator();
    rclc_support_t support;
    rclc_support_init(&support, 0, NULL, &allocator);
    
    rcl_node_t node;
    rclc_node_init_default(&node, "esp32_encoder", "", &support);
    
    rclc_publisher_init_default(
        &publisher,
        &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "encoder_ticks");
}

void loop() {
    if (millis() - last_publish > PUBLISH_INTERVAL) {
        msg.data = (int32_t)encoder.read();
        rcl_publisher_publish(&publisher, &msg, NULL);
        last_publish = millis();
    }
    delay(10);
}
```

### Build & Deploy

```bash
pio run -e esp32dev_microros --target upload

# On host machine (Ubuntu):
docker run -it --rm -v /dev:/dev --privileged --net=host \
    microros/micro-ros-agent:rolling \
    serial --dev /dev/ttyUSB0 -v6

# In another terminal:
ros2 topic echo /encoder_ticks
```

---

## 10. Performance Tips

### Optimization Checklist

1. **Publication rate:** 20-50 Hz optimal for most sensors
   - Reduce jitter with fixed interval (use `millis()` + threshold)
   - Avoid variable message sizes if possible

2. **Message size:** Keep <200 bytes
   - Smaller messages = lower latency
   - Serial @ 115200: ~100 bytes/msg = 1.15 ms per message

3. **WiFi:** Use 5 GHz if available
   - 2.4 GHz is congested (WiFi, Bluetooth, Zigbee)
   - Expected loss: 2.4 GHz ~5%, 5 GHz ~1-2%

4. **Serial:** Prefer serial for determinism
   - Best for real-time sensor fusion applications
   - No network jitter

5. **Memory:** Monitor SRAM
   - `Serial.printf("Free: %d\n", ESP.getFreeHeap());`
   - Keep below 150 KB for headroom

---

## 11. Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| **Agent not connecting** | Serial port mismatch | Check `ls /dev/ttyUSB*` or use PlatformIO device monitor |
| **Publish timeouts** | Buffer overflow | Reduce message frequency or size |
| **WiFi latency spikes** | Channel interference | Switch to 5 GHz or use Ethernet |
| **Out of memory** | Too many publishers | Limit to 4-6 topics max |
| **Message corruption** | Serial framing error | Increase baud rate to 460800 if supported |

---

## 12. 2024 Improvements & Status

✅ **Supported:**
- Full RCL/RMW stack on ESP32
- Multiple transport types (serial, WiFi, Ethernet)
- ROS 2 distributions: Humble, Jazzy, Kilted, Rolling
- Custom message types via library rebuilding

⚠️ **Limitations:**
- ESP32 SRAM (~520 KB) limits complex message types
- No hardware acceleration for time-sensitive operations
- WiFi throughput capped by chipset (~50 Mbps effective)

🔄 **Recent additions:**
- Ethernet support (community-contributed)
- Pre-built binaries for common configurations
- Docker-based agent (no local ROS 2 install needed)

---

## 13. References & Links

**Official:**
- [micro_ros_arduino GitHub](https://github.com/micro-ROS/micro_ros_arduino)
- [micro_ros_platformio GitHub](https://github.com/micro-ROS/micro_ros_platformio)
- [micro-ROS Documentation](https://micro.ros.org/)

**Examples:**
- [micro-ROS demos](https://github.com/micro-ROS/micro-ROS-demos/tree/humble/rclc)
- [Community PlatformIO examples](https://github.com/hippo5329/micro_ros_arduino_examples_platformio/wiki)

**Tools:**
- [ROS 2 Message Reference](https://docs.ros.org/en/humble/Concepts/Basic/About-ROS-2-Messages.html)
- [rcl API Reference](https://docs.ros.org/en/humble/API-Overview.html)

---

## Integration with Your Project

For the **evka_position** spherical sensor system:

### Recommended Setup

**Transport:** Serial (115200 baud) for determinism
- Publish encoder ticks @ 20 Hz
- Low jitter critical for dead-reckoning

**Message type:** Custom `SphericalState` or standard `Int32` for each encoder

**Architecture:**
```
ESP32 (firmware) → Serial (115200 baud) → micro-ROS Agent (host) → ROS 2 ecosystem
Theta encoder     ↓
Phi encoder       → rcl_publisher_publish() → /theta_ticks, /phi_ticks
Draw-wire encoder ↓
```

**Expected performance:**
- ~5 ms publication latency
- ~50 KB/s bandwidth (3 publishers × ~20 bytes/msg × 20 Hz)
- Single-threaded FreeRTOS task sufficient

Would you like a specific example integrated with your SphericalSensor.h constants and encoder pinouts?

