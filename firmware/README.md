# Evka Position Firmware

ESP32 firmware for the Spherical 3D Positioning System.

## Project Structure

*   `EvkaPosition/`: Main Arduino/PlatformIO project.
    *   `EvkaPosition.ino`: Sketch entry point (`setup()` / `loop()`).
    *   `SphericalSensor.h`: Configuration defines, structs, class declaration.
    *   `SphericalSensor.cpp`: Coordinate math, filtering, validation.
*   `tests/`: Standalone test sketches.
    *   `DrawWireTest/`: Tests the OPKON DWE3000 draw-wire encoder alone.
    *   `RotaryEncoderTest/`: Tests the Autonics E40S6 rotary encoder alone.

## Dependencies

*   **Encoder** by Paul Stoffregen (v1.4.1+) — install via Arduino Library Manager or PlatformIO.

## Build & Flash

See [`docs/setup_test_guide.md`](../docs/setup_test_guide.md) for full toolchain setup and step-by-step instructions.

Quick compile check:
```bash
arduino-cli compile --fqbn esp32:esp32:d1_r32 firmware/EvkaPosition
```

## Configuration

Edit `SphericalSensor.h` to change pin assignments, encoder resolution, or safety limits. See [`CLAUDE.md`](../CLAUDE.md) for a summary of all constants.
