# Host Tools

The supported operator path is `tools/evka_gui`. Host tools are package version `0.2.1` and require
Python 3.10+. All current GUI telemetry, recordings, snapshots, and Quick IPT results are sensor-frame
values. No endpoint/world transform is accepted or applied by the canonical GUI.

## evka_gui: Canonical Operator GUI

```bash
python -m tools.evka_gui
python -m tools.evka_gui --serial /dev/ttyACM0 --baud 115200
python -m tools.evka_gui --tcp 192.168.1.50:8080
python -m tools.evka_gui --ws 192.168.1.50
python -m tools.evka_gui --replay frames.csv
```

It provides Serial/TCP/WebSocket/replay connections, 3D and 2D views, recording, snapshots,
saved-point events, diagnostics, zero-relative raw counts, Quick IPT, and calibration-session tools.

Coordinate rules:

- Software Zero is a display/session offset only.
- Hardware Zero sends a firmware `ZERO*` command.
- Recordings and calibration capture use raw sensor-frame telemetry, not software-zeroed display
  values.
- The calibration window can generate a candidate session JSON after report PASS, but that does not
  establish project acceptance or change the live GUI frame.

Full guide: [evka_gui/README.md](evka_gui/README.md).

## calibration

Candidate Kabsch sensor-to-world fitting with separate calibration and hold-out sets:

```bash
python -m tools.calibration.gui
python -m tools.calibration.report
```

Theta repeatability must pass before collecting endpoint pairs. No shared/default calibration JSON
is checked in or accepted.

Operator workflow: [../docs/calibration/report_workflow.md](../docs/calibration/report_workflow.md).
Tool details: [calibration/README.md](calibration/README.md).

## Quick IPT

Quick IPT is inline in `evka_gui`. A standalone UI remains available:

```bash
python -m tools.ipt --tcp 192.168.1.50:8080
python -m tools.ipt --serial /dev/ttyACM0 --baud 115200
python -m tools.ipt.solver
```

The recovered point is in the sensor frame. See [ipt/README.md](ipt/README.md).

## Remote Tester

Development-only direct TCP/serial tester for `button_remote_test` firmware:

```bash
python tools/remote_tester/remote_test_gui.py
```

It is also available from the canonical GUI's **Remote Tester...** action, using a separate test
connection. See [remote_tester/README.md](remote_tester/README.md).

## Legacy position_checker

`tools/position_checker` retains shared parsing/transport/view code and legacy standalone entry
points. New operator instructions should use `tools/evka_gui`.

A passing session JSON may be supplied explicitly only to the legacy visualizer:

```bash
python -m tools.position_checker.main --legacy-visualizer --port /dev/ttyUSB0 \
  --calibration docs/calibration/sessions/current/calibration.json
```

| Legacy command | Canonical replacement |
|---|---|
| `python -m tools.position_checker.main --legacy-visualizer --port ...` | `python -m tools.evka_gui --serial ...` |
| `python -m tools.position_checker.cmd_main` | `python -m tools.evka_gui --tcp ...` |

Historical migration documents may mention older GUI package names as archive history.

## Protocol and Security

[../docs/PROTOCOL.md](../docs/PROTOCOL.md) is the canonical protocol reference. Do not treat
`cmd_main.py`, a GUI parser, or a historical vendor application as the wire-contract source.

Current fixed credentials and unauthenticated state-changing commands are trusted-lab-only. Do not
expose the device's TCP/WebSocket services to an untrusted network.
