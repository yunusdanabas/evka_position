# Research Resources: Spherical 3D Positioning Systems

> Workflow note: this file is a broad reference catalog across ecosystems. Project build/flash operations are PlatformIO on ESP32 only (see `platformio.ini` and `docs/setup_test_guide.md`).

This document consolidates open-source projects, libraries, documentation, and academic resources relevant to spherical coordinate positioning systems using rotary and linear encoders.

---

## 1. Encoder Libraries & Hardware Integration

### **PaulStoffregen/Encoder** ⭐ PRIMARY
- **URL:** https://github.com/PaulStoffregen/Encoder
- **Language:** C++ (Arduino)
- **Why Relevant:** Industry-standard for high-speed pulse counting on Arduino/Teensy/ESP32
- **Features:**
  - Hardware interrupt-driven quadrature decoding
  - Supports 5000+ PPR encoders
  - Optimized for AVR, ARM, ESP32, STM32 architectures
  - No external dependencies
- **Licensing:** MIT
- **Status:** Actively maintained

### **Arduino Core Libraries**
- **Encoder Examples:** https://docs.arduino.cc/built-in-examples/
- **Why Relevant:** Native `attachInterrupt()` API for ISR-based pulse detection
- **Best For:** Understanding interrupt-driven sensor input fundamentals

### **LibModbus** (Advanced: EtherCAT/Modbus Encoders)
- **URL:** https://github.com/stephane/libmodbus
- **Language:** C
- **Why Relevant:** If using Modbus-protocol encoders instead of quadrature
- **Status:** Production-ready, actively maintained

---

## 2. Robotics Kinematics & Math Libraries

### **KDL (Kinematics and Dynamics Library)** ⭐ REFERENCE
- **URL:** https://github.com/orocos/orocos_kinematics_dynamics
- **Language:** C++
- **Why Relevant:** Mature library for forward/inverse kinematics in robotic manipulators
- **Features:**
  - Rigid body dynamics
  - Chain-based manipulator structure (similar to your Theta→Phi→Wire setup)
  - Frame transformations
  - Jacobian calculations
- **Status:** Actively maintained by OROCOS project

### **Eigen (Linear Algebra)** ⭐ DEPENDENCY
- **URL:** https://eigen.tuxfamily.org/
- **Language:** C++ (Header-only)
- **Why Relevant:** Efficient matrix/vector math for coordinate transformations
- **Features:**
  - Dense and sparse matrix operations
  - Geometry module (rotations, translations, quaternions)
  - No external dependencies
- **Licensing:** Open-source

### **cmath / math.h** (Standard C++)
- **Documentation:** [cppreference.com/math](https://en.cppreference.com/w/cpp/header/cmath)
- **Why Relevant:** Built-in trigonometric and vector operations for spherical math
- **Relevant Functions:**
  - `sin()`, `cos()`, `atan2()`, `acos()` for spherical conversions
  - `sqrt()` for Cartesian distance

---

## 3. Related Open-Source Projects

### **ROS (Robot Operating System)** ⭐ ECOSYSTEM
- **URL:** https://www.ros.org/
- **Language:** C++/Python
- **Why Relevant:** Industry-standard framework for robotics systems
- **Relevant Components:**
  - `geometry_msgs` for 3D point representation
  - `tf2` library for coordinate frame transformations
  - Serial/sensor integration examples
- **Status:** Widely adopted in robotics community

### **Arduino-Robotics-Examples**
- **URL:** https://github.com/Automatic-Addison/arduino-robotics
- **Language:** C++ (Arduino)
- **Why Relevant:** Practical examples of encoder-based position tracking
- **Content:** PWM motor control, PID loops, sensor fusion

### **OpenDynamicsEngine (ODE)**
- **URL:** https://github.com/ode/ode
- **Language:** C++
- **Why Relevant:** Rigid body dynamics engine; useful for simulation/testing before hardware
- **Status:** Open-source, production-ready

### **CasADi** (Optimization & Control)
- **URL:** https://github.com/casadi/casadi
- **Language:** C++/Python
- **Why Relevant:** For advanced inverse kinematics with constraints
- **Use Case:** Motion planning to specific 3D points

---

## 4. Hardware-Specific Resources

### **Autonics E40S6 Encoder Datasheets**
- **Manufacturer:** Autonics
- **Datasheet:** [Included in `hardware/Rotary_Encoder_E40S6/`]
- **Relevant Specs:**
  - 5000 PPR datasheet (1480 counts/rev measured)
  - ~0.2432° resolution (measured)
  - Quadrature output (TTL)
  - Operating frequency up to ~1 MHz

### **Draw-Wire Encoder (Cable Extension Transducer)**
- **Manufacturers:** Sensata, BEI Sensors, Unipulse
- **Why Relevant:** Converts cable extension to electrical pulses
- **Integration:** Single-axis linear equivalent; treated as rotary with 1:1 spool mapping
- **Calibration:** Requires spool diameter specification

### **Teensy Microcontrollers** (Recommended over Arduino Uno)
- **URL:** https://www.pjrc.com/teensy/
- **Why Relevant:** Higher clock speed (120+ MHz), more interrupts, better for high-PPR encoders
- **Compatible Libraries:** Same PaulStoffregen/Encoder library

### **ESP32 Development Board**
- **URL:** https://github.com/espressif/esp-idf
- **Why Relevant:** Dual-core 240 MHz, WiFi for remote monitoring
- **Integration:** Full PaulStoffregen/Encoder library support

---

## 5. Coordinate Transformation & Math References

### **Wolfram MathWorld - Spherical Coordinates**
- **URL:** https://mathworld.wolfram.com/SphericalCoordinates.html
- **Why Relevant:** Authoritative reference for spherical ↔ Cartesian conversions
- **Formulas Covered:** All conventions, derivatives, applications

### **3Blue1Brown - Essence of Linear Algebra**
- **URL:** https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab
- **Why Relevant:** Visual intuition for coordinate transformations
- **Duration:** ~4 hours

### **"Introduction to Robotics" by John J. Craig** (Textbook)
- **Why Relevant:** Standard robotics kinematics reference
- **Chapters:** Forward/inverse kinematics, Denavit-Hartenberg convention
- **ISBN:** 978-0137033928

---

## 6. Simulation & Testing Tools

### **Wokwi Simulator** ⭐ PROTOTYPING
- **URL:** https://wokwi.com/
- **Language:** Web-based
- **Why Relevant:** Simulate Arduino/ESP32 + encoder behavior without hardware
- **Features:**
  - Virtual oscilloscope
  - Breadboard simulation
  - Logic level simulations
  - PaulStoffregen/Encoder library compatible

### **Python NumPy + Matplotlib** (For Verification)
- **Libraries:** NumPy, SciPy, Matplotlib
- **Why Relevant:** Quickly verify spherical-to-cartesian math before embedding
- **Example:**
  ```python
  import numpy as np
  
  def spherical_to_cartesian(r, theta, phi):
      x = r * np.sin(phi) * np.cos(theta)
      y = r * np.sin(phi) * np.sin(theta)
      z = r * np.cos(phi)
      return np.array([x, y, z])
  ```

### **MATLAB/Simulink** (Professional)
- **Why Relevant:** Model complex kinematics, generate C++ code
- **Cost:** Expensive; consider open alternatives (Octave, Julia)

### **GNU Octave** (Free MATLAB Alternative)
- **URL:** https://www.gnu.org/software/octave/
- **Why Relevant:** Free, MATLAB-compatible syntax
- **Use:** Verify equations before implementation

---

## 7. Educational & Reference Documentation

### **Last Minute Engineers - Rotary Encoder Tutorial**
- **URL:** https://lastminuteengineers.com/rotary-encoder-arduino-tutorial/
- **Why Relevant:** Practical guide to quadrature signals, debouncing, interrupts
- **Best For:** Hardware integration beginners

### **Arduino Serial Communication Guide**
- **URL:** https://docs.arduino.cc/tutorials/communication/serial-communication
- **Why Relevant:** Transmit position data to PC/dashboard
- **Protocols:** Serial (USB), I2C, SPI variants

### **PID Control for Motorized Systems**
- **Library:** https://github.com/br3ttb/Arduino-PID-Library
- **Why Relevant:** If system includes motors to move axes to target positions
- **Concept:** Feedback loop to reach setpoint angles/distance

---

## 8. Community & Forums

| Platform | URL | Best For |
|----------|-----|----------|
| **Arduino Forum** | https://forum.arduino.cc/c/using-arduino/sensors | Encoder troubleshooting, interrupt issues |
| **Reddit: r/Arduino** | https://reddit.com/r/Arduino | Community advice, project showcase |
| **Reddit: r/Robotics** | https://reddit.com/r/Robotics | Kinematics theory, design feedback |
| **GitHub Discussions** | Various repos | Library-specific issues |
| **OROCOS Community** | https://github.com/orocos | Advanced kinematics & frame transformations |

---

## 9. Standards & Best Practices

### **IEC 61076 (Connector Standards)**
- **Why Relevant:** Encoder signal integrity, shielding requirements
- **Applications:** Cable selection for quadrature signals

### **ISO 7498 (OSI Model)**
- **Why Relevant:** Serial communication protocol layers
- **Applications:** RS-485 multiaxis systems

### **IEEE 1451 (Smart Sensor Interface)**
- **Why Relevant:** Standardized sensor data formats
- **Applications:** Multi-sensor integration

---

## 10. Recommended Learning Path

1. **Fundamentals** (Week 1-2)
   - Read: CLAUDE.md & System_Architecture.md (this project)
   - Watch: 3Blue1Brown Linear Algebra series
   - Code: Basic quadrature decoder on Wokwi

2. **Encoder Integration** (Week 2-3)
   - Install: PaulStoffregen/Encoder library
   - Read: Last Minute Engineers tutorial
   - Experiment: Dual-encoder setup on Arduino

3. **Kinematics** (Week 3-4)
   - Study: Spherical coordinate math
   - Implement: Spherical → Cartesian converter
   - Verify: Python prototype first, then embedded C++

4. **Advanced** (Week 4+)
   - Explore: KDL library for complex systems
   - Implement: Inverse kinematics
   - Optimize: Real-time performance on ESP32

---

## Document Metadata

| Field | Value |
|-------|-------|
| **Last Updated** | 2026-02-01 |
| **Curator** | Evka Position Project |
| **Scope** | Spherical 3D positioning with rotary + linear encoders |
| **License** | References are external; this compilation is open-source |
