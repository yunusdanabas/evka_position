# micro-ROS ESP32 Integration Guide — Practical Implementation

This guide provides ready-to-use code templates and integration patterns for publishing sensor data from ESP32 to ROS 2 using micro-ROS.

---

## Part 1: Standalone Publisher Template

### File: `src/main_microros.cpp` (Serial Transport)

```cpp
#include <micro_ros_arduino.h>
#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/publisher.h>
#include <rcl/executor.h>
#include <std_msgs/msg/int32.h>
#include <std_msgs/msg/float32.h>

// ============================================================================
// Configuration
// ============================================================================

#define BAUD_RATE 115200
#define PUBLISH_INTERVAL_MS 50          // 20 Hz
#define MICROS_PER_SECOND 1000000UL

// ============================================================================
// RCL Objects
// ============================================================================

rcl_allocator_t allocator;
rclc_support_t support;
rcl_node_t node;
rcl_publisher_t encoder_theta_pub;
rcl_publisher_t encoder_phi_pub;
rcl_publisher_t encoder_wire_pub;

// ============================================================================
// Message Objects
// ============================================================================

std_msgs__msg__Int32 encoder_theta_msg;
std_msgs__msg__Int32 encoder_phi_msg;
std_msgs__msg__Int32 encoder_wire_msg;

// ============================================================================
// Timing
// ============================================================================

unsigned long last_publish_time = 0;

// ============================================================================
// Stub: Replace with actual sensor reading
// ============================================================================

int32_t read_encoder_theta() {
    // TODO: Implement quadrature encoder reading on GPIO 32/35
    return 0;
}

int32_t read_encoder_phi() {
    // TODO: Implement quadrature encoder reading on GPIO 14/12
    return 0;
}

int32_t read_encoder_wire() {
    // TODO: Implement quadrature encoder reading on GPIO 16/17
    return 0;
}

// ============================================================================
// Setup
// ============================================================================

void setup() {
    Serial.begin(BAUD_RATE);
    delay(2000);  // Wait for serial connection
    
    Serial.println("\n=== micro-ROS ESP32 Encoder Publisher ===");
    Serial.printf("Free heap: %d bytes\n", ESP.getFreeHeap());
    
    // Set micro-ROS transport
    set_microros_serial_transports(Serial);
    
    // Initialize allocator
    allocator = rcl_get_default_allocator();
    
    // Initialize support struct
    rcl_ret_t rc = rclc_support_init(&support, 0, NULL, &allocator);
    if (rc != RCL_RET_OK) {
        Serial.println("rclc_support_init failed!");
        return;
    }
    
    // Initialize node
    rc = rclc_node_init_default(&node, "esp32_encoder", "", &support);
    if (rc != RCL_RET_OK) {
        Serial.println("rclc_node_init_default failed!");
        return;
    }
    
    // Initialize publishers
    rc = rclc_publisher_init_default(
        &encoder_theta_pub,
        &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "encoder_theta");
    if (rc != RCL_RET_OK) {
        Serial.println("Failed to init theta publisher!");
    }
    
    rc = rclc_publisher_init_default(
        &encoder_phi_pub,
        &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "encoder_phi");
    if (rc != RCL_RET_OK) {
        Serial.println("Failed to init phi publisher!");
    }
    
    rc = rclc_publisher_init_default(
        &encoder_wire_pub,
        &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "encoder_wire");
    if (rc != RCL_RET_OK) {
        Serial.println("Failed to init wire publisher!");
    }
    
    Serial.println("micro-ROS initialization complete!");
}

// ============================================================================
// Loop
// ============================================================================

void loop() {
    unsigned long now = millis();
    
    // Publish at fixed interval
    if (now - last_publish_time >= PUBLISH_INTERVAL_MS) {
        // Read sensors
        encoder_theta_msg.data = read_encoder_theta();
        encoder_phi_msg.data = read_encoder_phi();
        encoder_wire_msg.data = read_encoder_wire();
        
        // Publish messages
        rcl_ret_t rc1 = rcl_publisher_publish(&encoder_theta_pub, &encoder_theta_msg, NULL);
        rcl_ret_t rc2 = rcl_publisher_publish(&encoder_phi_pub, &encoder_phi_msg, NULL);
        rcl_ret_t rc3 = rcl_publisher_publish(&encoder_wire_pub, &encoder_wire_msg, NULL);
        
        // Debug output
        if (rc1 != RCL_RET_OK || rc2 != RCL_RET_OK || rc3 != RCL_RET_OK) {
            Serial.printf("Publish failed: rc1=%d rc2=%d rc3=%d\n", rc1, rc2, rc3);
        }
        
        // Optional: Print to serial monitor (disable for production)
        // Serial.printf("Theta: %ld, Phi: %ld, Wire: %ld\n",
        //     encoder_theta_msg.data, encoder_phi_msg.data, encoder_wire_msg.data);
        
        last_publish_time = now;
    }
    
    // Optional: health check every 5 seconds
    static unsigned long last_health_check = 0;
    if (now - last_health_check > 5000) {
        Serial.printf("Heap free: %d bytes\n", ESP.getFreeHeap());
        last_health_check = now;
    }
    
    delay(10);  // Small delay to prevent watchdog issues
}
```

### platformio.ini

```ini
[env:esp32_microros_serial]
platform = espressif32
board = esp32dev
framework = arduino

# Reduce monitor noise
monitor_speed = 115200
monitor_filters = colorize

# micro-ROS configuration
lib_deps =
    https://github.com/micro-ROS/micro_ros_platformio
    paulstoffregen/Encoder @ ^1.4.2

# Set micro-ROS build parameters
board_microros_distro = humble
board_microros_transport = serial
board_microros_extra_packages = ros2_std_msgs

# Memory optimization for ESP32
build_flags =
    -DNDEBUG
    -O2
```

---

## Part 2: WiFi Publisher with Connection Management

### File: `src/main_microros_wifi.cpp`

```cpp
#include <micro_ros_arduino.h>
#include <rcl/rcl.h>
#include <rcl/publisher.h>
#include <std_msgs/msg/int32.h>
#include <WiFi.h>

// ============================================================================
// WiFi Configuration
// ============================================================================

const char* SSID = "YOUR_SSID";
const char* PASSWORD = "YOUR_PASSWORD";
const char* AGENT_IP = "192.168.1.100";      // Your ROS 2 host machine
const uint16_t AGENT_PORT = 8888;

// ============================================================================
// Connection State Machine
// ============================================================================

enum ConnectionState {
    STATE_WIFI_DISCONNECTED,
    STATE_WIFI_CONNECTED,
    STATE_MICROROS_INITIALIZED,
    STATE_PUBLISHING,
    STATE_ERROR
};

ConnectionState current_state = STATE_WIFI_DISCONNECTED;

// ============================================================================
// RCL Objects
// ============================================================================

rcl_allocator_t allocator;
rclc_support_t support;
rcl_node_t node;
rcl_publisher_t sensor_pub;
std_msgs__msg__Int32 msg;

// ============================================================================
// Timing
// ============================================================================

unsigned long last_publish_time = 0;
unsigned long last_heartbeat = 0;
const unsigned long PUBLISH_INTERVAL_MS = 50;      // 20 Hz
const unsigned long HEARTBEAT_INTERVAL_MS = 5000;  // 5 seconds

// ============================================================================
// WiFi Connection Handler
// ============================================================================

void setup_wifi() {
    Serial.printf("\nConnecting to WiFi: %s\n", SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(SSID, PASSWORD);
    
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
        delay(500);
        Serial.print(".");
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected!");
        Serial.printf("IP: %s\n", WiFi.localIP().toString().c_str());
        current_state = STATE_WIFI_CONNECTED;
        return;
    }
    
    Serial.println("\nWiFi connection failed!");
    current_state = STATE_ERROR;
}

// ============================================================================
// micro-ROS Initialization
// ============================================================================

bool init_microros() {
    Serial.println("Initializing micro-ROS...");
    
    IPAddress agent_ip;
    agent_ip.fromString(AGENT_IP);
    
    set_microros_wifi_transports(SSID, PASSWORD, agent_ip, AGENT_PORT);
    
    allocator = rcl_get_default_allocator();
    
    rcl_ret_t rc = rclc_support_init(&support, 0, NULL, &allocator);
    if (rc != RCL_RET_OK) {
        Serial.println("rclc_support_init failed!");
        return false;
    }
    
    rc = rclc_node_init_default(&node, "esp32_sensor_wifi", "", &support);
    if (rc != RCL_RET_OK) {
        Serial.println("rclc_node_init failed!");
        return false;
    }
    
    rc = rclc_publisher_init_default(
        &sensor_pub,
        &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "sensor_data");
    if (rc != RCL_RET_OK) {
        Serial.println("Publisher init failed!");
        return false;
    }
    
    Serial.println("micro-ROS initialization complete!");
    return true;
}

// ============================================================================
// Setup
// ============================================================================

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    Serial.println("\n=== micro-ROS ESP32 WiFi Publisher ===");
    Serial.printf("Free heap: %d bytes\n", ESP.getFreeHeap());
    
    setup_wifi();
}

// ============================================================================
// Loop
// ============================================================================

void loop() {
    switch (current_state) {
        case STATE_WIFI_DISCONNECTED:
            if (millis() % 5000 == 0) setup_wifi();
            break;
            
        case STATE_WIFI_CONNECTED:
            if (init_microros()) {
                current_state = STATE_MICROROS_INITIALIZED;
            } else {
                current_state = STATE_ERROR;
            }
            break;
            
        case STATE_MICROROS_INITIALIZED:
            current_state = STATE_PUBLISHING;
            break;
            
        case STATE_PUBLISHING: {
            unsigned long now = millis();
            
            // Check WiFi still connected
            if (WiFi.status() != WL_CONNECTED) {
                Serial.println("WiFi connection lost!");
                current_state = STATE_WIFI_DISCONNECTED;
                break;
            }
            
            // Publish at interval
            if (now - last_publish_time >= PUBLISH_INTERVAL_MS) {
                msg.data = (int32_t)(rand() % 1000);  // TODO: Replace with sensor data
                
                rcl_ret_t rc = rcl_publisher_publish(&sensor_pub, &msg, NULL);
                if (rc != RCL_RET_OK) {
                    Serial.printf("Publish failed: %d\n", rc);
                    current_state = STATE_ERROR;
                } else {
                    last_publish_time = now;
                }
            }
            
            // Heartbeat log
            if (now - last_heartbeat > HEARTBEAT_INTERVAL_MS) {
                Serial.printf("Publishing... Heap: %d\n", ESP.getFreeHeap());
                last_heartbeat = now;
            }
            break;
        }
        
        case STATE_ERROR:
            Serial.println("Error state - resetting in 5 seconds...");
            delay(5000);
            ESP.restart();
            break;
    }
    
    delay(10);
}
```

---

## Part 3: Custom Message Type Publisher

### File: `include/sensor_state.hpp` (Custom Message Type)

```cpp
#ifndef SENSOR_STATE_HPP
#define SENSOR_STATE_HPP

#include <std_msgs/msg/header.h>
#include <geometry_msgs/msg/vector3.h>

typedef struct {
    std_msgs__msg__Header header;
    int32_t encoder_theta;
    int32_t encoder_phi;
    int32_t encoder_wire;
    float accel_x;
    float accel_y;
    float accel_z;
} SensorState;

#endif
```

### File: `src/main_custom_msg.cpp`

```cpp
#include <micro_ros_arduino.h>
#include <rcl/rcl.h>
#include <rcl/publisher.h>
#include "sensor_state.hpp"

// RCL Objects
rcl_allocator_t allocator;
rclc_support_t support;
rcl_node_t node;
rcl_publisher_t sensor_state_pub;
SensorState sensor_msg;

unsigned long last_publish_time = 0;
const unsigned long PUBLISH_INTERVAL_MS = 50;

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    set_microros_serial_transports(Serial);
    
    allocator = rcl_get_default_allocator();
    rclc_support_init(&support, 0, NULL, &allocator);
    rclc_node_init_default(&node, "esp32_custom_sensor", "", &support);
    
    // Custom publisher for SensorState message
    // NOTE: This requires custom message generation or use of rosidl_typesupport
    // For now, use standard types as shown in previous examples
    
    Serial.println("Custom message publisher initialized!");
}

void loop() {
    unsigned long now = millis();
    
    if (now - last_publish_time >= PUBLISH_INTERVAL_MS) {
        // Populate message
        sensor_msg.header.stamp.sec = now / 1000;
        sensor_msg.header.stamp.nanosec = (now % 1000) * 1000000;
        sensor_msg.header.frame_id.data = "sensor_link";
        
        sensor_msg.encoder_theta = 1000;
        sensor_msg.encoder_phi = 2000;
        sensor_msg.encoder_wire = 3000;
        
        sensor_msg.accel_x = 9.81f;
        sensor_msg.accel_y = 0.0f;
        sensor_msg.accel_z = 0.0f;
        
        // Publish (when using standard types)
        // rcl_publisher_publish(&sensor_state_pub, &sensor_msg, NULL);
        
        last_publish_time = now;
    }
    
    delay(10);
}
```

---

## Part 4: Integration with Existing SphericalSensor Code

### File: `src/main_integrated.cpp` (With SphericalSensor.h)

```cpp
#include <micro_ros_arduino.h>
#include <rcl/rcl.h>
#include <rcl/publisher.h>
#include <std_msgs/msg/int32.h>
#include <SphericalSensor.h>
#include <Encoder.h>

// ============================================================================
// Initialize sensors from SphericalSensor.h constants
// ============================================================================

// Theta encoder
Encoder encoder_theta(GPIO_THETA_A, GPIO_THETA_B);

// Phi encoder
Encoder encoder_phi(GPIO_PHI_A, GPIO_PHI_B);

// Wire encoder (quadrature channels A, B)
Encoder encoder_wire(GPIO_WIRE_A, GPIO_WIRE_B);

// ============================================================================
// RCL Objects
// ============================================================================

rcl_allocator_t allocator;
rclc_support_t support;
rcl_node_t node;

rcl_publisher_t pub_theta;
rcl_publisher_t pub_phi;
rcl_publisher_t pub_wire;

std_msgs__msg__Int32 msg_theta;
std_msgs__msg__Int32 msg_phi;
std_msgs__msg__Int32 msg_wire;

// ============================================================================
// Sensor Reading (Convert PPR to pulses or degrees)
// ============================================================================

int32_t read_theta_ticks() {
    return (int32_t)encoder_theta.read();
}

int32_t read_phi_ticks() {
    return (int32_t)encoder_phi.read();
}

int32_t read_wire_ticks() {
    return (int32_t)encoder_wire.read();
}

// Optional: Convert to degrees
float read_theta_degrees() {
    long ticks = encoder_theta.read();
    return (ticks / PPR_ROTARY) * 360.0f;
}

float read_phi_degrees() {
    long ticks = encoder_phi.read();
    return (ticks / PPR_ROTARY) * 360.0f;
}

float read_wire_distance() {
    long ticks = encoder_wire.read();
    return (ticks / PPR_WIRE) * 1000.0f;  // Convert to mm
}

// ============================================================================
// Setup
// ============================================================================

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    Serial.println("\n=== micro-ROS SphericalSensor Integration ===");
    Serial.printf("PPR_ROTARY: %.1f\n", PPR_ROTARY);
    Serial.printf("PPR_WIRE: %.1f\n", PPR_WIRE);
    Serial.printf("Free heap: %d bytes\n", ESP.getFreeHeap());
    
    // Initialize micro-ROS
    set_microros_serial_transports(Serial);
    
    allocator = rcl_get_default_allocator();
    rcl_ret_t rc = rclc_support_init(&support, 0, NULL, &allocator);
    if (rc != RCL_RET_OK) {
        Serial.println("ERROR: rclc_support_init failed!");
        return;
    }
    
    rc = rclc_node_init_default(&node, "spherical_sensor", "", &support);
    if (rc != RCL_RET_OK) {
        Serial.println("ERROR: node init failed!");
        return;
    }
    
    // Create publishers
    rclc_publisher_init_default(&pub_theta, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "theta_ticks");
    
    rclc_publisher_init_default(&pub_phi, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "phi_ticks");
    
    rclc_publisher_init_default(&pub_wire, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "wire_ticks");
    
    Serial.println("Setup complete - publishing at 20 Hz");
}

// ============================================================================
// Loop
// ============================================================================

unsigned long last_publish = 0;

void loop() {
    unsigned long now = millis();
    
    if (now - last_publish >= 50) {  // 20 Hz
        msg_theta.data = read_theta_ticks();
        msg_phi.data = read_phi_ticks();
        msg_wire.data = read_wire_ticks();
        
        rcl_publisher_publish(&pub_theta, &msg_theta, NULL);
        rcl_publisher_publish(&pub_phi, &msg_phi, NULL);
        rcl_publisher_publish(&pub_wire, &msg_wire, NULL);
        
        // Debug every 1 second
        static unsigned long last_debug = 0;
        if (now - last_debug > 1000) {
            Serial.printf("Theta: %ld | Phi: %ld | Wire: %ld\n",
                msg_theta.data, msg_phi.data, msg_wire.data);
            last_debug = now;
        }
        
        last_publish = now;
    }
    
    delay(10);
}
```

---

## Part 5: Subscriber Example (Receiving Commands from ROS 2)

### File: `src/main_sub_pub.cpp` (Publisher + Subscriber)

```cpp
#include <micro_ros_arduino.h>
#include <rcl/rcl.h>
#include <rcl/subscription.h>
#include <rcl/publisher.h>
#include <rcl/executor.h>
#include <std_msgs/msg/int32.h>
#include <std_msgs/msg/string.h>

// ============================================================================
// RCL Objects
// ============================================================================

rcl_allocator_t allocator;
rclc_support_t support;
rcl_node_t node;
rclc_executor_t executor;

// Publisher: Sensor data
rcl_publisher_t pub_sensor;
std_msgs__msg__Int32 pub_msg;

// Subscriber: Commands
rcl_subscription_t sub_command;
std_msgs__msg__Int32 sub_msg;

// ============================================================================
// Subscription Callback
// ============================================================================

void command_callback(const void* msgin) {
    const std_msgs__msg__Int32* msg = (const std_msgs__msg__Int32*)msgin;
    
    Serial.printf("Received command: %ld\n", msg->data);
    
    // Process command
    switch (msg->data) {
        case 0:
            Serial.println("STOP");
            break;
        case 1:
            Serial.println("START");
            break;
        case 2:
            Serial.println("RESET");
            break;
        default:
            Serial.printf("Unknown command: %ld\n", msg->data);
    }
}

// ============================================================================
// Setup
// ============================================================================

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    set_microros_serial_transports(Serial);
    
    allocator = rcl_get_default_allocator();
    rclc_support_init(&support, 0, NULL, &allocator);
    
    rclc_node_init_default(&node, "esp32_sub_pub", "", &support);
    
    // Initialize executor
    rclc_executor_init(&executor, &support.context, 2, &allocator);
    
    // Publisher
    rclc_publisher_init_default(&pub_sensor, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "sensor_data");
    
    // Subscriber
    rclc_subscription_init_default(&sub_command, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "command");
    
    // Add subscription to executor
    rclc_executor_add_subscription(&executor, &sub_command, &sub_msg,
        &command_callback, ON_NEW_DATA);
    
    Serial.println("Setup complete!");
}

// ============================================================================
// Loop
// ============================================================================

unsigned long last_publish = 0;

void loop() {
    unsigned long now = millis();
    
    // Spin executor (check for incoming messages)
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(100));
    
    // Publish sensor data at 20 Hz
    if (now - last_publish >= 50) {
        pub_msg.data = (int32_t)(rand() % 1000);
        rcl_publisher_publish(&pub_sensor, &pub_msg, NULL);
        last_publish = now;
    }
    
    delay(10);
}
```

---

## Part 6: Agent Setup & Testing

### Launching Agent (Docker)

**Serial (recommended for development):**
```bash
docker run -it --rm \
    -v /dev:/dev \
    --privileged \
    --net=host \
    microros/micro-ros-agent:rolling \
    serial --dev /dev/ttyUSB0 -v6
```

**UDP/WiFi:**
```bash
docker run -it --rm \
    --net=host \
    microros/micro-ros-agent:rolling \
    udp4 --port 8888 -v6
```

### Verify Data Flowing

```bash
# Terminal 1: Run agent (see above)

# Terminal 2: List active topics
ros2 topic list

# Terminal 3: Echo a topic
ros2 topic echo /encoder_theta

# Terminal 4: Publish test command (if using subscriber)
ros2 topic pub --once /command std_msgs/msg/Int32 "data: 1"
```

### Performance Monitoring

```bash
# Monitor message frequency
ros2 topic hz /encoder_theta

# Check message size
ros2 topic info -v /encoder_theta

# Monitor ROS 2 graph
rqt_graph
```

---

## Part 7: Troubleshooting Checklist

| Symptom | Solution |
|---------|----------|
| **"Agent not connecting"** | 1. Check USB cable, 2. Verify port: `ls /dev/ttyUSB*`, 3. Check baud rate in agent (use 115200) |
| **"Publish failed: rc=-1"** | Node not properly initialized or lost connection; check rclc_support_init return code |
| **"Out of memory"** | Reduce message frequency, use Int32 instead of custom types, limit publishers to 3-4 |
| **Serial garbage/corruption** | Baud rate mismatch; verify 115200 in both firmware and agent, try 460800 if supported |
| **WiFi latency spikes** | WiFi interference; test with 5 GHz router, add small delay between publishes (100 ms) |
| **Executor hangs** | Set reasonable timeout in rclc_executor_spin_some(), add watchdog timer |

---

## Quick Reference: Minimal Working Example

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
    rclc_node_init_default(&node, "minimal", "", &support);
    rclc_publisher_init_default(&pub, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "topic");
}

void loop() {
    static unsigned long t = 0;
    if (millis() - t > 50) {
        msg.data++;
        rcl_publisher_publish(&pub, &msg, NULL);
        t = millis();
    }
    delay(10);
}
```

---

## Advanced Topics

### Timer-based Publishing (Higher Accuracy)

```cpp
void setup_timer() {
    // ESP32 hardware timer for precise 20 Hz intervals
    // Use esp_timer.h for microsecond precision
}
```

### Multi-threaded Publishing (FreeRTOS)

```cpp
void publisher_task(void* param) {
    while (true) {
        msg.data++;
        rcl_publisher_publish(&pub, &msg, NULL);
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

void setup() {
    // ... init code ...
    xTaskCreate(publisher_task, "pub", 4096, NULL, 1, NULL);
}
```

### Quality of Service (QoS) Configuration

```cpp
// Configure publisher QoS for reliability
rcl_publisher_options_t pub_options = rcl_publisher_get_default_options();
pub_options.qos = rmw_qos_profile_sensor_data;  // Or sensor_data, best_effort
```

---

## References

- [micro_ros_arduino examples](https://github.com/micro-ROS/micro_ros_arduino/tree/main/examples)
- [RCL API docs](https://docs.ros.org/en/humble/API-Overview.html)
- [ROS 2 Message Types](https://docs.ros.org/en/humble/Concepts/Basic/About-ROS-2-Messages.html)

