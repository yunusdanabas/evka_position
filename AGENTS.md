# AGENTS.md — Shared Agent Guide

Universal guide for all agents (Claude, Codex, Copilot, Cursor, OpenCode, …).
Tracked in Git so it transfers on clone. Canonical human docs are tracked
alongside: **HANDOFF.md**, **CONTRIBUTING.md**, **docs/ARCHITECTURE.md**,
**docs/PROTOCOL.md**, **docs/README.md**, and **docs/ONBOARDING.md**.
Agent activity history is in [AGENT_LOG.md](AGENT_LOG.md).

## Reading order

1. This file
2. [HANDOFF.md](HANDOFF.md) — current status, blockers, boundaries
3. [docs/ONBOARDING.md](docs/ONBOARDING.md) — first-session baseline
4. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — runtime design and pins
5. [docs/PROTOCOL.md](docs/PROTOCOL.md) — command/reply contract

## Working rules

- Read [AGENT_LOG.md](AGENT_LOG.md) before starting work to avoid conflicts.
- Log every change there. Format: `date | agent | summary` (most recent first).
- Canonical source of truth for firmware pins/config is
  `firmware/src/SphericalSensor.h`; do not trust this file for exact pin
  numbers. Update the tracked docs above (not just this file) when pins,
  constants, or architecture change.
- Follow [CONTRIBUTING.md](CONTRIBUTING.md) for the supported PlatformIO-only
  workflow, Python tooling, and pull-request style.

## Hardware and safety boundaries

- Do not modify `.kicad_sch`, `.kicad_pcb`, or other PCB sources without a task
  scoped to the PCB owner. Touching them in software/docs work breaks history.
- Do not flash firmware, run hardware checks, or commit live device data as
  part of documentation-only work. Deferred hardware validation is acceptable.
- The repository has no redistribution license and no public production claim.
  Treat the checked-in AP/STA credentials and TCP/WebSocket commands as
  trusted-lab-only; see [HANDOFF.md](HANDOFF.md) and
  [docs/PROTOCOL.md](docs/PROTOCOL.md#security-boundary).

## Validation commands

| Check | Command |
|---|---|
| Python tests (Qt-heavy) | `QT_QPA_PLATFORM=offscreen pytest -q -m qt_heavy --forked` |
| Python tests (rest) | `QT_QPA_PLATFORM=offscreen pytest -q -m "not qt_heavy"` |
| Compile all tools | `python -m compileall tools -q` |
| IPT solver self-check | `python -m tools.ipt.solver` |
| Firmware build (all envs) | `pio run` |
| Firmware build (classic) | `pio run -e wemos_d1_r32` |
| Firmware build (v4) | `pio run -e esp32s3_v4` |
| Dashboard harness | `npm ci && npm test` (in `tools/webdash_harness`) |
| Doc sanity | `git diff --check` + verify changed relative Markdown links |

## Logging policy

When you finish a unit of work, add one row to the top of the table in
[AGENT_LOG.md](AGENT_LOG.md) with:

- `Date` — `YYYY-MM-DD`
- `Agent` — tool and model (e.g. `OpenCode (GPT-5.6)`)
- `Changes` — concise summary, including files touched, verification run, and
  anything explicitly deferred. Preserve previous rows unchanged.