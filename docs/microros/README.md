# micro-ROS ESP32 Documentation

Complete reference for publishing sensor data from ESP32 to ROS 2 using micro-ROS (2024 update). This is a **planned future feature** — not yet in production firmware.

---

## Documents

| Document | Size | Read Time | Purpose |
|----------|------|-----------|---------|
| [MICROROS_QUICK_REFERENCE.md](MICROROS_QUICK_REFERENCE.md) | 7 KB | 5 min | Copy-paste examples, troubleshooting table |
| [MICROROS_ESP32_2024.md](MICROROS_ESP32_2024.md) | 15 KB | 20 min | Library comparison, overview, API reference |
| [MICROROS_ESP32_INTEGRATION.md](MICROROS_ESP32_INTEGRATION.md) | 25 KB | 45 min | 7 complete code examples, SphericalSensor.h integration |
| [MICROROS_PERFORMANCE_ANALYSIS.md](MICROROS_PERFORMANCE_ANALYSIS.md) | 20 KB | 30 min | Latency/bandwidth analysis, optimization |

---

## Reading Paths

**Quick (10 min):** `MICROROS_QUICK_REFERENCE.md` → copy minimal example → upload → done

**Balanced (45 min):** Quick reference → `MICROROS_ESP32_2024.md` sections 1–5 → `MICROROS_ESP32_INTEGRATION.md` Part 1

**evka_position integration (30 min):** Quick reference → `MICROROS_ESP32_INTEGRATION.md` Part 4 → adapt pins → test

**Thorough (2 h):** All 4 docs in order above

---

## Task Navigation

| I want to... | Go to |
|---|---|
| Get something working in 5 minutes | MICROROS_QUICK_REFERENCE.md |
| Understand what micro-ROS is | MICROROS_ESP32_2024.md sections 1–3 |
| Publish encoder data to ROS 2 | MICROROS_QUICK_REFERENCE.md → encoder pattern |
| Integrate with SphericalSensor.h | MICROROS_ESP32_INTEGRATION.md Part 4 |
| Use WiFi instead of serial | MICROROS_ESP32_INTEGRATION.md Part 2 |
| Understand latency/bandwidth | MICROROS_PERFORMANCE_ANALYSIS.md sections 1–3 |
| Troubleshoot a problem | MICROROS_QUICK_REFERENCE.md section 6 |
| Optimize for real-time | MICROROS_PERFORMANCE_ANALYSIS.md section 5 |

---

## Key Metrics

### Latency

| Transport | Latency | Jitter | Best For |
|-----------|---------|--------|----------|
| Serial @ 115200 | 5 ms | ±2 ms | Real-time control |
| WiFi 2.4 GHz | 20 ms | ±15 ms | Telemetry/monitoring |
| Ethernet | 2 ms | ±1 ms | Best overall |

### Bandwidth — 3 encoders @ 20 Hz

| Transport | Available | Used | % |
|-----------|-----------|------|----|
| Serial @ 115200 | 10 KB/s | 1.68 KB/s | 16% |
| WiFi | 50 MB/s | 1.68 KB/s | 0.003% |

**Recommended for evka_position:** Serial @ 115200 — 5 ms latency, 20 Hz update rate.

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Agent won't connect | Check `/dev/ttyUSB0` exists |
| `rcl_publish` failed | Check heap (`getFreeHeap()`), reduce publishers |
| High latency (>20 ms) | Increase baud rate, verify transport |
| Garbage data | Baud rate mismatch — verify both sides are 115200 |
| Build errors | Run `pio run --target clean_microros` |

---

## Implementation Checklist

- [ ] Read MICROROS_QUICK_REFERENCE.md
- [ ] Choose transport (serial recommended)
- [ ] Copy example from MICROROS_ESP32_INTEGRATION.md
- [ ] Adjust encoder pins (`SphericalSensor.h` pin map)
- [ ] `pio run -e esp32dev --target upload`
- [ ] `docker run microros/micro-ros-agent:rolling serial --dev /dev/ttyUSB0`
- [ ] `ros2 topic hz /theta_ticks` — expect 20.0 ± 0.1 Hz
- [ ] Monitor heap: stays above 50 KB during operation

---

## External Links

- [micro-ROS site](https://micro.ros.org/)
- [micro_ros_platformio GitHub](https://github.com/micro-ROS/micro_ros_platformio)
- [ROS 2 Humble docs](https://docs.ros.org/en/humble/)
