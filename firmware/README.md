# Evka Position Firmware

ESP32 firmware for the Spherical 3D Positioning System.

## Project Structure

*   `src/`: Production firmware (PlatformIO build target `wemos_d1_r32`).
    *   `EvkaPosition.cpp`: Entry point (`setup()` / `loop()`).
    *   `SphericalSensor.h`: Configuration defines, structs, class declaration.
    *   `SphericalSensor.cpp`: Coordinate math, filtering, validation.
*   `tests/`: Standalone test sketches, each compiled independently.
    *   `DrawWireTest/`: Standalone test for the OPKON DWE3000 draw-wire encoder.
    *   `RotaryEncoderTest/`: Standalone test for the Autonics E40S6 rotary encoder (theta + phi).
    *   `SingleRotaryTest/`: Single rotary encoder test (theta or phi independently).
    *   `AllSensorsTest/`: All three encoders together, without position math.

## Dependencies

*   **Encoder** by Paul Stoffregen (v1.4.4+) — automatically installed by PlatformIO via `platformio.ini`.

## Build & Flash

Supported workflow policy: use PlatformIO on ESP32 only. Arduino IDE and `arduino-cli` are not part of this firmware workflow.

See [`docs/setup_test_guide.md`](../docs/setup_test_guide.md) for full toolchain setup and step-by-step instructions.

Quick compile check:
```bash
pio run -e wemos_d1_r32
```

## Configuration

Edit `src/SphericalSensor.h` to change pin assignments, encoder resolution, or safety limits. See [`CLAUDE.md`](../CLAUDE.md) for a summary of all constants.
