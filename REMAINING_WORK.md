# Remaining work

Open items as of **2026-08-12**, after the pre-handoff polish pass.
Working tree is clean and everything below is committed and pushed.
Background: [docs/CI_PYTEST_SEGFAULT_LOG.md](docs/CI_PYTEST_SEGFAULT_LOG.md),
[AGENT_LOG.md](AGENT_LOG.md).

---

## 1. Segfault isolation — RESOLVED 2026-08-12

**Problem.** `pytest -q` intermittently segfaulted (exit 139): 3/20 runs on Python
3.10, 0/20 on 3.12. Cause is pyqtgraph's process-global `ViewBox.AllViews`
registry being walked after windows are freed. This is why CI on `master` went
red on run `30454073693`.

**What is decided (do not re-litigate):**

- Blanket `pytest --forked` over the whole suite is **rejected** — fault injection
  proved it silently swallows failing `unittest` subtests. Do not reintroduce it.
- Four other fixes (`gc.collect()` teardown, `processEvents()` flush, clearing the
  registry, parenting the LED timer) were measured and reverted. Do not retry them.
- `pytestmark = pytest.mark.forked` on the six Qt modules is **rejected and was
  removed**. It looked right but *deadlocks the run*: by the time those modules are
  reached, an earlier module (`tools/calibration/tests/test_gui.py`) has already
  built a QApplication in the parent process, and `os.fork()` from a live Qt parent
  hangs forever. Reproduced deterministically on Python 3.10 both in a ROS-flavoured
  conda env and in a clean CI-equivalent venv. This is why the marker approach was
  never actually green — the recorded pass predates `pytest-forked` being installed,
  so the markers were being silently ignored.

**Implemented fix — the two-invocation split** (the fallback this file predicted):

- The six Qt/pyqtgraph modules carry `pytestmark = pytest.mark.qt_heavy`
  (marker registered in `pyproject.toml`).
- CI runs `pytest -q -m qt_heavy --forked` and `pytest -q -m "not qt_heavy"` as two
  separate steps. The forked parent never builds a QApplication, so no deadlock; the
  subtest-bearing modules stay in the unforked pass, so no swallowed failures.

**Verified 2026-08-12** in a clean venv (Python 3.10.18, PyQt5 5.15.11,
pyqtgraph 0.14.0, numpy 1.26.4, `pytest-forked` 1.7.5):

- 44 passed forked + 160 passed & 11 subtests unforked = 204 total.
- 12 consecutive runs of each pass: **0 failures, 0 segfaults, 0 hangs**.
- Fault injection into a forked module returns `rc=1` and names the failing test —
  failures are not swallowed.

Remaining: watch the first few CI runs. The original bug was intermittent, so one
green run is not proof.

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
will need `pytestmark = pytest.mark.qt_heavy` (never `pytest.mark.forked`).

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
- Handoff polish (2026-08-12): stale 191/45 test counts corrected to 204/50 across
  README/HANDOFF/final_integration_validation; `numpy` capped `<2` for the Wine
  PyInstaller build; dead `.gitignore` rules (C# `bin/`/`obj/`/`*.dll`/`*.pdb`,
  `tools/analysis/`, `tools/web_server/`) removed and `build/`/`dist/` anchored;
  `tools/VISUALIZATION_GUIDE.md` deleted (gitignored, unreferenced, described
  Three.js/Plotly work never done); v3 DRC/backup debris removed from the v4 PCB
  workspace, clearing the last `/home/yunusdanabas` paths from tracked files.
