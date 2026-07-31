# CI pytest segfault — open issue log

**Status:** OPEN — unresolved. CI on `master` is red because of this.
**First observed:** run [30454073693](https://github.com/yunusdanabas/evka_position/actions/runs/30454073693)
(commit `33d837b`, 2026-07-29), `Run Python tests` step, exit code **139**.
**Impact:** `pytest -q` intermittently dies with SIGSEGV. Individual tests do not
fail — the interpreter is killed mid-run, so the whole job fails.

## Symptom

```
Fatal Python error: Segmentation fault
Current thread (most recent call first):
  pyqtgraph/WidgetGroup.py, line 211 in acceptsType
  pyqtgraph/WidgetGroup.py, line 199 in autoAdd
  pyqtgraph/WidgetGroup.py, line 205 in autoAdd      <- recursing into children
  pyqtgraph/graphicsItems/PlotItem/PlotItem.py, line 241 in __init__
  pyqtgraph/widgets/PlotWidget.py, line 58 in __init__
  tools/evka_gui/gui.py, line 716 in _make_plot
  tools/evka_gui/gui.py, line 616 in _build_view_panel
  tools/evka_gui/gui.py, line 203 in _build_ui
  tools/evka_gui/gui.py, line 165 in __init__
  tools/evka_gui/tests/test_recording.py, line 29 in window
```

The crash happens while **constructing a new** `PlotWidget`, inside pyqtgraph's
recursive `WidgetGroup.autoAdd` walk, on an `isinstance()` call.

## Mechanism (understood)

Every `EvkaWindow` builds three `PlotWidget`s. Each `PlotWidget`'s `ViewBox`
registers itself in the **process-global** `ViewBox.AllViews` weak dictionary
(`pyqtgraph/graphicsItems/ViewBox/ViewBox.py:109`, registered at line 280).
`QWidget.close()` only hides a window — it does **not** unregister the ViewBox.

The GUI tests construct many windows (`test_command_tracking.py` alone creates 9).
Each is freed later, whenever CPython drops the last reference. Building any
subsequent plot calls `ViewBox.updateAllViewLists()` (line 1783), which iterates
that global registry and calls into every ViewBox still listed. If a window's C++
object has been destroyed while its Python wrapper is still reachable, the walk
dereferences freed memory.

Because it depends on garbage-collection timing, it is **flaky, not
deterministic**.

## Measured failure rates

Reproduced locally under CI's exact library versions (PyQt5 5.15.11,
pyqtgraph 0.14.0, `QT_QPA_PLATFORM=offscreen`). Note the machine was also running
firmware builds during some batches, so absolute rates carry noise — the
comparisons below are only trustworthy at coarse resolution.

| Variant | Python 3.10 | Python 3.12 |
|---|---|---|
| Repo as-is (baseline, idle machine) | **3 / 20** | **0 / 20** |
| Repo as-is (baseline, machine under load) | 2 / 20 | 0 / 15 |
| `gc.collect()` after each test | 0 / 8 | **8 / 8** |
| Clear `ViewBox.AllViews` after each test | 2 / 8 | 1 / 8 |
| Pin every window alive for the session | 0 / 10 | 3 / 15 |
| Parent the LED reset timer (`gui.py`) | 5 / 20 | — |

## Fixes attempted and rejected

All four were implemented, measured, and **reverted** — none is a fix, and the
first three are actively harmful:

1. **`gc.collect()` in an autouse teardown.** Eliminated the crash on 3.10 but
   made 3.12 fail every single run: forcing collection destroys widgets mid-suite,
   moving the use-after-free earlier rather than removing it.
2. **`app.processEvents()` in teardown.** Worse still — it dispatches queued timer
   callbacks, which then run against widgets the same teardown just freed.
3. **Clearing pyqtgraph's global registry between tests.** Reduced but did not
   remove the crash on either interpreter.
4. **Parenting the `_on_remote_btn` LED-reset `QTimer` to the window.** No
   measured improvement (5/20 vs 2/20 baseline — within noise, if anything worse).
   Note `QTimer.singleShot(msec, context, slot)` does **not** exist in PyQt5; that
   overload is Qt6/PySide only, and using it raises `TypeError` at runtime.

## Process isolation — measured 2026-07-29

`pytest-forked` runs each test in a forked child, so the global registry is never
shared. It **does** fix the crash:

| Variant | Python 3.10 | Runtime |
|---|---|---|
| Baseline | 3 / 20 segfaults | ~5 s |
| `pytest --forked` (blanket) | **0 / 20 segfaults** | ~13 s |

**But blanket `--forked` is unsafe and was rejected.** It silently discards
failing `unittest` subtests. Verified by fault injection — an assertion in
`tools/position_checker/tests/test_math_conventions.py` was deliberately broken:

```
without --forked :  rc=1   7 failed, 14 passed, 4 subtests passed   <- fault caught
with    --forked :  rc=0            14 passed                        <- fault SWALLOWED
```

A test setup that hides real regressions is worse than an intermittent crash, so
forking must not be applied to the whole suite.

**Current (unverified) approach:** fork only the six modules that build pyqtgraph
widgets, via `pytestmark = pytest.mark.forked`, leaving every other module —
including the subtest-bearing ones — running normally. See `REMAINING_WORK.md`;
this is implemented in the working tree but **not yet measured**.

## Recommended next step

Process isolation is the standard remedy for cross-test Qt/C++ state and is the
only approach not yet tried: run the GUI test modules in separate processes
(`pytest-forked`, or `pytest-xdist` with `--forked`). That removes the shared
global registry entirely rather than trying to keep it consistent.

Interim option if CI redness is blocking: mark the GUI suite non-blocking, or
retry the step once, while keeping the non-GUI tests gating.

## Related latent bug (separate from the segfault)

`tools/evka_gui/gui.py:1420` posts `QTimer.singleShot(400, lambda ...)` with no
owner. Nothing cancels it if the window closes inside those 400 ms, so it can fire
against destroyed widgets in the real application too. It is **not** the cause of
this segfault (measured above), but the ownerless timer is worth fixing on its own
merits — the PyQt5-correct form is a `QTimer` parented to the widget.
