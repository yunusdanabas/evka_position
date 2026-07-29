# webdash_harness — run the firmware web dashboard without hardware

The dashboard is ~1,100 lines of HTML/CSS/JS living inside a PROGMEM string in
`firmware/src/WebDashboard.cpp`. `pio run` proves it *compiles*; it proves nothing
about whether the JavaScript **runs**. This harness executes it.

It extracts the blob, stubs the WebSocket the page expects, and drives the real page
under jsdom — so a broken DOM id, a typo'd handler, or a mis-wired button fails here
instead of on a phone in the field.

```bash
cd tools/webdash_harness
npm ci                     # installs the pinned dev-only jsdom version
npm test                   # extracts WebDashboard.cpp and runs the UI checks
```

What it checks: page loads clean, IPT mode + ARM/STOP/SOLVE recovering a known hidden
target, degenerate sweeps being blocked rather than trusted, recording surviving a
FREEZE, the protocol log, `RAW_COUNTS`, and that calibration APPLY + SAVE (NVS)
actually sends `SAVE_PPR` while APPLY (RAM) does not.

`window.__sweep(P, L, n, halfAngleDeg)` synthesises the operator's spiral hand motion
around a hidden target, which is what makes the IPT path testable at all.

**The numerics are covered separately** and with no npm dependency, by
`tools/ipt/tests/test_web_solver_parity.py` — that one runs in normal `pytest`, slices
the solver out of the blob, and asserts it agrees with `tools/ipt/solver.py` under
node. This harness covers the *UI wiring*; that test covers the *math*.
