# Project Handoff — evka_position

Welcome. This document is the **starting point for the new maintainer**. Read it top to
bottom once; it explains what the project is, what state it's in, where everything lives,
and the order to read the rest of the docs.

> New to the repo? Set up your machine first with **[CONTRIBUTING.md](CONTRIBUTING.md)**
> (Ubuntu **and** Windows), then come back here for the tour.

---

## 1. What this is

**evka_position** is an ESP32 firmware system that measures the **3D position (X, Y, Z in mm)**
of a target using three encoders in a spherical arrangement:

- **Theta (θ)** — azimuth, an Autonics E40S6 rotary encoder
- **Phi (φ)** — elevation, a second Autonics E40S6 rotary encoder
- **Radius (r)** — an OPKON DWEM2 draw-wire encoder

The firmware reads quadrature pulses, converts **counts → (r, θ, φ) → (X, Y, Z)**, smooths the
result, and streams it over serial, a WiFi web dashboard, and a raw TCP protocol that a
third-party Windows CNC app ("CMD") consumes.

```
   ┌─────────────┐   ┌─────────────┐   ┌──────────────┐
   │ θ  E40S6    │   │ φ  E40S6    │   │ r  DWEM2     │   3 quadrature encoders
   │ rotary      │   │ rotary      │   │ draw-wire    │
   └──────┬──────┘   └──────┬──────┘   └──────┬───────┘
          └──────────────┬──┴─────────────────┘
                         ▼  (dividers / v4 PCB → 3.3 V)
            ┌───────────────────────────────┐
            │  ESP32 firmware (PlatformIO)   │
            │  counts → (r,θ,φ) → (X,Y,Z)mm  │
            │  20 Hz, EMA-filtered           │
            └───┬───────────┬───────────┬────┘
     Serial 115200│   WiFi AP │           │ ESP-NOW
                  ▼   192.168.1.50        ▼
        pio monitor /   ├─ Web dashboard (browser)   2-button pendant
        Python tools    └─ TCP :8080 ──► CMD C# GUI  (ESP32-C3)
                                          + Python tools
```

## 2. Current status (as of handoff)

| Area | State |
|---|---|
| Firmware — classic ESP32 (Wemos D1 R32) | ✅ Working, builds (`wemos_d1_r32`) |
| Firmware — **v4 PCB (ESP32-S3)** | ✅ **Ported & builds** (`esp32s3_v4`); **hardware bring-up pending** |
| v4 PCB | ✅ **Fabricated**; assembly + bring-up not yet done |
| WiFi dashboard + TCP CMD protocol | ✅ Working, hardened (see troubleshooting docs) |
| ESP-NOW wireless pendant | ✅ Working (`button_remote`, verified on ESP32-C3 USB) |
| Python tools (evka_gui, position_checker shims, ipt) | ✅ Working |
| CMD C# Windows app | ✅ Builds (`CMDScanner.csproj`, .NET 8) |
| Full 3-encoder hardware integration test | ⬜ **Next milestone** (Phase 5) |

**The single most important next task** is bringing up the fabricated v4 board: flash
`esp32s3_v4`, verify each encoder counts in the right direction, read the battery, and confirm
the dashboard. See `pcb_design/EVKA_position_v4/FIRMWARE.md` for the step-by-step.

Roadmap detail: **[docs/PROJECT_ROADMAP.md](docs/PROJECT_ROADMAP.md)**.

## 3. Repo map

```
evka_position/
├── HANDOFF.md              ← you are here
├── README.md               Project overview + quickstart
├── README_TR.md            Turkish end-user WiFi guide (for operators, not devs)
├── CONTRIBUTING.md         Dev environment setup (Ubuntu + Windows) — read this first
├── platformio.ini          Firmware build environments (classic ESP32 + v4 S3 + tests)
├── pyproject.toml / requirements.txt   Python tool dependencies
│
├── firmware/
│   ├── src/                Production firmware (main sensor board)
│   │   ├── EvkaPosition.cpp     setup()/loop(), 20 Hz, command dispatch
│   │   ├── SphericalSensor.*    coordinate math, filtering, calibration, config
│   │   ├── WebDashboard.cpp     WiFi AP + web dashboard + WebSocket
│   │   ├── CmdTcpServer.cpp     raw TCP CMD protocol server
│   │   └── CMD Soft/            third-party Windows C# CNC app (CMDScanner.csproj)
│   ├── remote/             ESP-NOW wireless pendant (ESP32-C3)
│   └── tests/              Standalone encoder test sketches
│
├── tools/                  Python host-side tools (see docs/README.md → Tools)
│   ├── position_checker/   Live 3D visualizer + CMD-protocol GUI
│   ├── evka_gui/           Unified control + 3D GUI (canonical)
│   ├── evka_gui_v2/        Deprecated shim
│   ├── ipt/                Hidden-point ("Inverted Pen") measurement tool
│   ├── calibration/        Kabsch world↔sensor calibration (calibrate.py)
│   └── remote_tester/      Pendant test GUI
│
├── pcb_design/             KiCad workspaces: v2, v3, v4 (current/fabricated), v5
│   └── EVKA_position_v4/    ← current board (+ FIRMWARE.md quickstart)
│
├── docs/                   All documentation — start at docs/README.md (index)
│   └── gui_unification/     GUI consolidation plan + implementation log
└── laser_radius/           Research: laser-based radius alternative (exploratory)
```

## 4. Reading order

1. **[CONTRIBUTING.md](CONTRIBUTING.md)** — get your machine building & running.
2. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — how the system works: pipeline, config,
   pin maps, coordinate convention, command reference.
3. **[README.md](README.md)** — overview + quickstart, WiFi, protocol summary.
4. **[docs/README.md](docs/README.md)** — the documentation index; find any topic from here.
5. **[pcb_design/EVKA_position_v4/FIRMWARE.md](pcb_design/EVKA_position_v4/FIRMWARE.md)** —
   the current board's pin map + bring-up.
6. **[docs/firmware/CODE_WALKTHROUGH.md](docs/firmware/CODE_WALKTHROUGH.md)** — a guided tour of
   the firmware source.

## 5. Known issues & gotchas

- **WiFi/networking** were the hardest part historically — all fixed, but read
  `docs/WIFI_PERFORMANCE_ISSUES_LOG.md` and `docs/ASYNCTCP_STACK_OVERFLOW_ANALYSIS.md` before
  touching the WiFi/WebSocket code.
- **AP IP `192.168.1.50` is hardcoded** and collides with common home routers — the CMD app
  depends on it. See the subnet-conflict note in README/ARCHITECTURE.
- **v4 pin map differs from earlier boards** and was verified against the schematic + PCB
  (not the old v2 netlist, which is NOT a valid proxy). Trust `SphericalSensor.h` / FIRMWARE.md.
- **The best working notes used to live in `CLAUDE.md`/`AGENTS.md`** (AI-assistant guides,
  git-ignored). Their content has been mirrored into tracked docs (ARCHITECTURE, this file,
  CONTRIBUTING); those two files remain only as assistant hints.

## 6. Ownership & license

This repository currently carries **no license file** — it is unlicensed ("all rights reserved"
by default). The incoming owner should decide on a license. Third-party components (the "CMD"
C# app and its original ESP32 firmware under `firmware/src/CMD Soft/`) originate from an external
vendor; confirm their terms before redistribution.
