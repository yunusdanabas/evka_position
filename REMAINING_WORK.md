# Remaining work

Open items as of **2026-07-29**, after the workspace health audit.
Last pushed commit: `9553b35`. Background: [docs/CI_PYTEST_SEGFAULT_LOG.md](docs/CI_PYTEST_SEGFAULT_LOG.md),
[AGENT_LOG.md](AGENT_LOG.md).

> **The working tree has uncommitted changes.** Seven files are modified and none
> of it is verified. Read step 1 before running anything.

---

## 1. Finish the segfault isolation — IN PROGRESS, UNVERIFIED

**Problem.** `pytest -q` intermittently segfaults (exit 139): 3/20 runs on Python
3.10, 0/20 on 3.12. Cause is pyqtgraph's process-global `ViewBox.AllViews`
registry being walked after windows are freed. This is why CI on `master` went
red on run `30454073693`.

**What is already decided (do not re-litigate):**

- Blanket `pytest --forked` fixes the crash (0/20) **but is rejected** — fault
  injection proved it silently swallows failing `unittest` subtests. Evidence is
  in the issue log. Do not reintroduce it.
- Four other fixes (`gc.collect()` teardown, `processEvents()` flush, clearing the
  registry, parenting the LED timer) were measured and reverted. Do not retry them.

**Uncommitted changes now in the tree:**

| File | Change |
|---|---|
| `requirements.txt` | added `pytest-forked>=1.6` |
| `tools/evka_gui/tests/test_calibration_report.py` | added `pytestmark = pytest.mark.forked` |
| `tools/evka_gui/tests/test_command_tracking.py` | same |
| `tools/evka_gui/tests/test_disconnect.py` | same |
| `tools/evka_gui/tests/test_ipt_panel.py` | same |
| `tools/evka_gui/tests/test_recording.py` | same |
| `tools/position_checker/tests/test_view3d.py` | same (+ `import pytest`) |

Idea: fork only the six modules that build pyqtgraph widgets, so subtest-bearing
modules keep normal reporting.

**Steps to finish:**

1. Confirm the suite passes at all: `QT_QPA_PLATFORM=offscreen pytest -q`.
   Expect 193 passed. This was never run after the markers were added.
2. Time one run. Blanket forking cost ~13 s vs ~5 s baseline; a 20-run loop
   exceeded a 10-minute timeout. If selective forking is still slow, reduce the
   measurement to 10 runs rather than 20.
3. Measure the segfault rate on **Python 3.10** (3.12 does not reproduce it).
   Target 0 failures; anything above 0/10 means the approach did not work.
4. Re-run the fault injection to prove subtests are still reported. Break an
   assertion in `tools/position_checker/tests/test_math_conventions.py` and
   confirm `rc=1`. **If this reports `rc=0`, the approach has failed** — that
   module must never run forked.
5. Add `pytest-forked` to the CI install step in `.github/workflows/ci.yml`
   (currently `pip install pytest platformio` — it does not install it).
6. Commit, push, and watch CI. Because the bug is intermittent, one green run is
   not proof; re-run the workflow a few times.

**If selective forking fails**, the fallback is two pytest invocations in CI: one
`--forked` pass over `tools/evka_gui/tests` and `tools/calibration/tests`, and one
normal pass over everything else.

A Python 3.10 repro environment matching CI (PyQt5 5.15.11, pyqtgraph 0.14.0) is
required — the bug does not appear on 3.12. It was built with
`conda create -p <path> python=3.10` then `pip install -e . pytest pytest-forked`.

---

## 2. Add tests for untested modules — APPROVED, NOT STARTED

No test file covers these:

| Module | Lines |
|---|---|
| `tools/ipt/gui.py` | 360 |
| `tools/position_checker/cmd_display.py` | 155 |
| `tools/position_checker/main.py` | 142 |
| `tools/calibration/calibrate.py` | 142 |
| `tools/position_checker/cmd_main.py` | 106 |
| `tools/evka_gui/transport.py` | 150 |
| `tools/evka_gui/wifi_window.py` | 80 |
| `tools/evka_gui/tokens.py` | 42 |
| `tools/evka_gui/remote_window.py` | 31 |

`tools/evka_gui/gui.py` has no dedicated test file but is covered indirectly by
`test_command_tracking`, `test_disconnect`, `test_recording`, and
`test_calibration_report`.

Note any new test that builds pyqtgraph widgets inherits the step-1 problem and
will need the same `pytestmark`.

---

## 3. Split the god files — APPROVED, NOT STARTED

| File | Lines |
|---|---|
| `firmware/src/WebDashboard.cpp` | 2174 |
| `tools/evka_gui/gui.py` | 2078 |

Cautions carried over from the audit:

- `WebDashboard.cpp` is large mostly because the dashboard HTML/CSS/JS is embedded
  as string literals. Separating the web asset from the C++ is the natural first
  cut. `tools/webdash_harness` extracts and drives that JS, so it is the
  regression check — run `npm test` after any change.
- This firmware has **not been hardware-validated** (Phase 5 still open). A
  refactor here cannot be verified beyond compiling. Keep changes mechanical.
- Verify with `pio run -e wemos_d1_r32` and `pio run -e esp32s3_v4` after each
  step; both currently build clean.

---

## 4. Bump deprecated CI actions — NOT STARTED

CI warns that `actions/checkout@v4`, `actions/setup-node@v4`, and
`actions/setup-python@v5` are forced onto Node 24 because Node 20 is deprecated.
Warning only today. Bump to current majors and confirm the workflow still passes.

---

## Closed — do not redo

- `npm test` hardcoded `python` → now `python3`.
- `PyQt5.QtWebSockets` import guarded so the GUI package imports on distro PyQt5.
- `compileall` + IPT solver added to CI.
- Trailing whitespace, empty `pcb_design/EVKA_position_v3/docs/` directory.
- `v0.2.0-prototype` retagged onto `33d837b` and pushed; `backup/pre-split-20260729`
  deleted after confirming identical trees.
- Commit `711abf3` says "Playwright" but the harness is jsdom. **Decided: leave
  it.** History is already pushed; the code and docs are correct.
- Root `.gitignore` has no global `node_modules/` rule — redundant with
  `tools/webdash_harness/.gitignore`. Deliberately skipped.
