# Evka Position: Spherical 3D Positioning System

## Overview
Evka Position is a hardware and firmware project capable of calculating the 3D position $(X, Y, Z)$ of a target object in real-time. It utilizes a **Spherical Coordinate System** derived from three sensor inputs:
1.  **$\theta$ (Theta):** Azimuth angle (Horizontal rotation)
2.  **$\phi$ (Phi):** Polar/Elevation angle (Vertical tilt)
3.  **$r$ (Radius):** Linear distance (Extension)

The system uses industrial-grade sensors and an **ESP32 (Wemos D1 R32)** controller.

## Features
*   **Real-time 3D Tracking:** Converts raw sensor data to Cartesian coordinates $(X, Y, Z)$ instantly.
*   **High Precision:** Autonics E40S6 rotary encoders (5000 PPR) and OPKON DWE3000 draw-wire sensor (2000 PPR, 0.1 mm/pulse).
*   **Robust Firmware:** Quadrature decoding via the PaulStoffregen Encoder library on ESP32.
*   **Python Visualiser:** Real-time 3D scatter plot of position data.

## Directory Structure

*   **`firmware/`**: Microcontroller source code.
    *   `EvkaPosition/`: Main sketch and `SphericalSensor` class.
    *   `tests/`: Standalone test sketches for individual encoders.
*   **`hardware/`**: Sensor datasheets and system architecture documentation.
    *   `System_Architecture.md`: Kinematic math and error analysis.
    *   `Rotary_Encoder_E40S6/`: Autonics E40S6 docs and PDFs.
    *   `Draw_Wire_Encoder/`: OPKON DWE3000 specs.
*   **`tools/`**: Python utilities (position_checker visualiser).
*   **`docs/`**: Setup guides, hardware notes, and rework logs.

## Getting Started

1.  **Setup Toolchain:** Follow [`docs/setup_test_guide.md`](docs/setup_test_guide.md) for arduino-cli installation, ESP32 board support, and library setup.
2.  **Connect Hardware:** Wire encoders per pin definitions in `firmware/EvkaPosition/SphericalSensor.h`. All encoder signal lines require 5V-to-3.3V voltage dividers (see [`docs/DWE3000_hardware_notes.md`](docs/DWE3000_hardware_notes.md)).
3.  **Flash Firmware:** Compile and upload for ESP32 (Wemos D1 R32).
4.  **Calibrate:** On startup, the system assumes the arm is at mechanical home ($\theta=0, \phi=0, r=0$). Ensure the device is homed before powering on.

## Mathematical Model
The system uses standard spherical-to-cartesian conversion:

$$
\begin{align*}
X &= r \cdot \sin(\phi) \cdot \cos(\theta) \\
Y &= r \cdot \sin(\phi) \cdot \sin(\theta) \\
Z &= r \cdot \cos(\phi)
\end{align*}
$$

For inverse kinematics and detailed error analysis, see [System Architecture](hardware/System_Architecture.md).

## Resources
*   [CLAUDE.md](CLAUDE.md) - Project configuration reference for AI assistants.
*   [Setup & Test Guide](docs/setup_test_guide.md) - Step-by-step build and test instructions.
*   [Research Resources](docs/resources.md) - External libraries and learning materials.
