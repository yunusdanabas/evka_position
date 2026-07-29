# Documentation Status Index

This index separates the active v4 prototype handoff from historical material and research. A file
in the repository is not automatically a current requirement.

## Active Prototype Handoff

| Document | Role |
|---|---|
| [../AGENTS.md](../AGENTS.md) | Shared agent guide: working rules, safety boundaries, validation commands |
| [../AGENT_LOG.md](../AGENT_LOG.md) | Historical multi-agent activity log |
| [../HANDOFF.md](../HANDOFF.md) | Approved existing-repository status, blockers, and reading order |
| [ONBOARDING.md](ONBOARDING.md) | Self-contained workstation, safety, and first-session baseline |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Supported toolchain and contribution boundaries |
| [../README.md](../README.md) | Short project and operator overview |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Runtime design, coordinate frames, pins, LED, and battery behavior |
| [PROTOCOL.md](PROTOCOL.md) | **Canonical source-derived telemetry and command/reply contract** |
| [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) | Remaining prototype gates in approved order |
| [firmware/CODE_WALKTHROUGH.md](firmware/CODE_WALKTHROUGH.md) | Guided map of current firmware source |
| [../pcb_design/EVKA_position_v4/FIRMWARE.md](../pcb_design/EVKA_position_v4/FIRMWARE.md) | v4 PCB-derived pin map and firmware quickstart |
| [../README_TR.md](../README_TR.md) | Turkish operator guide |

## Active Calibration

Theta count loss is unresolved and there is no accepted endpoint/world transform. Treat generated
transforms as candidates until the required repeatability, calibration, and hold-out gates pass.

| Document | Role |
|---|---|
| [calibration/README.md](calibration/README.md) | Calibration order and current stop conditions |
| [calibration/calibration_guide.md](calibration/calibration_guide.md) | Encoder-scale and candidate endpoint workflow |
| [calibration/report_workflow.md](calibration/report_workflow.md) | CSV/report workflow and acceptance thresholds |
| [calibration/sessions/README.md](calibration/sessions/README.md) | Session inputs, candidate outputs, and archiving |
| [calibration/sessions/2026-07-17_repeatability.md](calibration/sessions/2026-07-17_repeatability.md) | Current theta count-loss evidence |
| [calibration/draw_wire_calibration.md](calibration/draw_wire_calibration.md) | Draw-wire scale procedure |
| [calibration/theta_rotary_calibration.md](calibration/theta_rotary_calibration.md) | Theta procedure and repeatability gate |
| [calibration/phi_rotary_calibration.md](calibration/phi_rotary_calibration.md) | Phi procedure and J2 mapping |

## Active Integration and Operations

| Document | Role |
|---|---|
| [integration/CMD_SOFTWARE_INTEGRATION.md](integration/CMD_SOFTWARE_INTEGRATION.md) | Retained TCP compatibility integration; vendor C# app has been deleted |
| [integration/final_integration_validation.md](integration/final_integration_validation.md) | Pending prototype acceptance checklist |
| [integration/setup_test_guide.md](integration/setup_test_guide.md) | Classic-board bench reference plus v4 routing notice |
| [WIFI_PERFORMANCE_ISSUES_LOG.md](WIFI_PERFORMANCE_ISSUES_LOG.md) | Historical WiFi fixes and open validation notes |
| [WIFI_AP_STA_RECONNECT_PATTERNS.md](WIFI_AP_STA_RECONNECT_PATTERNS.md) | AP/STA implementation reference |
| [ASYNCTCP_STACK_OVERFLOW_ANALYSIS.md](ASYNCTCP_STACK_OVERFLOW_ANALYSIS.md) | AsyncTCP implementation risk reference |
| [ESPASYNCHACK_NOTES.md](ESPASYNCHACK_NOTES.md) | Installed ESPAsyncWebServer behavior notes |

## Hardware Reference

| Document | Status |
|---|---|
| [../pcb_design/README.md](../pcb_design/README.md) | PCB workspace index; v4 is the current assembled prototype |
| [hardware_design/encoders/](hardware_design/encoders/) | Active encoder references |
| [hardware_design/remote/](hardware_design/remote/) | ESP-NOW pendant reference |
| [hardware_design/assembly/](hardware_design/assembly/) | Bench/assembly reference; verify revision before use |
| [hardware_design/5v/](hardware_design/5v/) | Older classic-board design reference |
| [hardware_design/12v_legacy/](hardware_design/12v_legacy/) | **Archive:** superseded 12 V/v2/v3 designs, not the v4 baseline |

## Host Tools

| Document | Status |
|---|---|
| [../tools/evka_gui/README.md](../tools/evka_gui/README.md) | **Active canonical GUI**, sensor-frame-only |
| [../tools/calibration/README.md](../tools/calibration/README.md) | Active candidate transform/report tooling |
| [../tools/ipt/README.md](../tools/ipt/README.md) | Active Quick IPT tooling; result remains sensor-frame |
| [../tools/remote_tester/README.md](../tools/remote_tester/README.md) | Development-only pendant tester |
| [../tools/position_checker/README.md](../tools/position_checker/README.md) | Legacy standalone tools plus shared libraries |

## Archive and History

These explain how the current repository evolved; they are not current acceptance statements:

- [integration/CMD_INTEGRATION_CHANGELOG.md](integration/CMD_INTEGRATION_CHANGELOG.md)
- [firmware/firmware_rework_log.md](firmware/firmware_rework_log.md)
- [gui_unification/](gui_unification/)
- [superpowers/specs/](superpowers/specs/)

Historical mentions of `tools/evka_gui_v2` or the deleted vendor C# application remain historical
only; referenced vendor paths no longer exist in the worktree.
The supported GUI is `tools/evka_gui`; the retained protocol is [PROTOCOL.md](PROTOCOL.md).

## Research

Research documents describe alternatives, not implemented or accepted hardware:

- [research/](research/)
- [../laser_radius/](../laser_radius/)
- [BLE_WIFI_COEXISTENCE.md](BLE_WIFI_COEXISTENCE.md)
- [resources.md](resources.md)

## Legal and Security Boundary

The repository has no redistribution license and makes no public production-readiness claim. The
current fixed credentials and unauthenticated TCP/WebSocket commands are trusted-lab-only. See
[PROTOCOL.md](PROTOCOL.md#security-boundary).
