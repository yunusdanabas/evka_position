# Documentation Index

Everything in `docs/` (and the key root docs), grouped by purpose. Start at the top and go as
deep as you need.

> Lost? The absolute entry points are **[../HANDOFF.md](../HANDOFF.md)** (project tour) and
> **[../CONTRIBUTING.md](../CONTRIBUTING.md)** (get your machine set up).

---

## Getting started

| Doc | What it gives you |
|---|---|
| [../HANDOFF.md](../HANDOFF.md) | Project tour, status, repo map, reading order |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Dev setup for Ubuntu **and** Windows |
| [../README.md](../README.md) | Overview, quickstart, WiFi, protocol summary |
| [ARCHITECTURE.md](ARCHITECTURE.md) | **How the system works**: pipeline, config, pin maps, commands |
| [../pcb_design/EVKA_position_v4/FIRMWARE.md](../pcb_design/EVKA_position_v4/FIRMWARE.md) | Current board pin map + bring-up |
| [integration/setup_test_guide.md](integration/setup_test_guide.md) | Bench wiring + first-run test guide |

## Architecture & firmware reference

| Doc | Topic |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Coordinate pipeline, config `#define`s, pin maps, command reference |
| [hardware_design/system_architecture.md](hardware_design/system_architecture.md) | Kinematics + coordinate math |
| [firmware/CODE_WALKTHROUGH.md](firmware/CODE_WALKTHROUGH.md) | Guided tour of `firmware/src/` |
| [firmware/firmware_rework_log.md](firmware/firmware_rework_log.md) | History of firmware changes |
| [firmware/ESP32_PCNT_REFERENCE.md](firmware/ESP32_PCNT_REFERENCE.md) | Hardware pulse-counter (encoder) reference |
| [firmware/ESP32_NVS_CALIBRATION_GUIDE.md](firmware/ESP32_NVS_CALIBRATION_GUIDE.md) | Persisting calibration to flash |
| [firmware/FreeRTOS_Dual_Core_Architecture.md](firmware/FreeRTOS_Dual_Core_Architecture.md) · [firmware/QUICK_REFERENCE_DualCore.md](firmware/QUICK_REFERENCE_DualCore.md) | Task/core layout |

## Calibration

| Doc | Topic |
|---|---|
| [calibration/README.md](calibration/README.md) | Calibration overview + encoder-sign check |
| [calibration/calibration_guide.md](calibration/calibration_guide.md) | End-to-end calibration procedure |
| [calibration/draw_wire_calibration.md](calibration/draw_wire_calibration.md) | Radius (draw-wire) PPR calibration |
| [calibration/theta_rotary_calibration.md](calibration/theta_rotary_calibration.md) · [calibration/phi_rotary_calibration.md](calibration/phi_rotary_calibration.md) | Angle PPR calibration |

## CMD software integration

| Doc | Topic |
|---|---|
| [integration/CMD_SOFTWARE_INTEGRATION.md](integration/CMD_SOFTWARE_INTEGRATION.md) | TCP protocol quick reference for the CMD app |
| [integration/CMD_INTEGRATION_CHANGELOG.md](integration/CMD_INTEGRATION_CHANGELOG.md) | Why each integration change was made |
| [integration/final_integration_validation.md](integration/final_integration_validation.md) | Integration validation record |

## Hardware & PCB

| Doc | Topic |
|---|---|
| [hardware_design/system_architecture.md](hardware_design/system_architecture.md) | System-level hardware architecture |
| [hardware_design/PCB_EMI_LAYOUT_GUIDE.md](hardware_design/PCB_EMI_LAYOUT_GUIDE.md) | EMI-aware PCB layout guidance |
| [hardware_design/5v/](hardware_design/5v/) | Original 5V board schematic/BOM/layout |
| [hardware_design/remote/](hardware_design/remote/) | ESP-NOW pendant hardware |
| [hardware_design/encoders/](hardware_design/encoders/) | E40S6 + DWEM2 encoder datasheets/specs |
| [hardware_design/assembly/](hardware_design/assembly/) | Assembly + individual hardware test plans |
| [hardware_design/12v_legacy/](hardware_design/12v_legacy/) | Archived 12V/v2/v3 hardware docs (superseded) |
| `../pcb_design/EVKA_position_v4/` | **Current** KiCad workspace (+ FIRMWARE.md) |

## Troubleshooting — WiFi & stability

Read these **before** touching the WiFi/WebSocket/async code — they document hard-won fixes.

| Doc | Topic |
|---|---|
| [WIFI_PERFORMANCE_ISSUES_LOG.md](WIFI_PERFORMANCE_ISSUES_LOG.md) | 8 documented WiFi issues + fixes |
| [WIFI_AP_STA_RECONNECT_PATTERNS.md](WIFI_AP_STA_RECONNECT_PATTERNS.md) | AP+STA reconnect recovery patterns |
| [ASYNCTCP_STACK_OVERFLOW_ANALYSIS.md](ASYNCTCP_STACK_OVERFLOW_ANALYSIS.md) | AsyncTCP/lwIP stack-overflow analysis |
| [ESPASYNCHACK_NOTES.md](ESPASYNCHACK_NOTES.md) | ESPAsyncWebServer allocation notes |
| [ESP32_WIFI_AP_STA_HEAP_DRAIN_GUIDE.md](ESP32_WIFI_AP_STA_HEAP_DRAIN_GUIDE.md) | Heap-drain guide |
| [ESP32_WDT_20HZ_QUICK_REFERENCE.md](ESP32_WDT_20HZ_QUICK_REFERENCE.md) | Watchdog @ 20 Hz reference |
| [BLE_WIFI_COEXISTENCE.md](BLE_WIFI_COEXISTENCE.md) | BLE/WiFi coexistence notes |

## Host tools

| Doc | Topic |
|---|---|
| [../tools/README.md](../tools/README.md) | Overview of the Python tools |
| [../tools/position_checker/README.md](../tools/position_checker/README.md) | Live 3D visualizer + CMD GUI |
| [../tools/ipt/README.md](../tools/ipt/README.md) | Hidden-point ("Inverted Pen") tool |
| [../tools/calibration/README.md](../tools/calibration/README.md) | Kabsch world↔sensor calibration |
| [../tools/remote_tester/README.md](../tools/remote_tester/README.md) | Pendant test GUI |

## Research & planning

| Doc | Topic |
|---|---|
| [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) | Phase plan + current status |
| [research/laser_radius_research.md](research/laser_radius_research.md) · [../laser_radius/](../laser_radius/) | Laser-based radius alternative (exploratory) |
| [research/hardware_redesign_research.md](research/hardware_redesign_research.md) · [research/improvement_research.md](research/improvement_research.md) | Redesign/improvement studies |
| [resources.md](resources.md) | External links & references |
