"""sim_study.py — accuracy study for the detailed IPT report.

Runs the *existing* solver (tools/ipt/solver.py) on synthetic golden-spiral
clouds and reports how target error, self-calibrated length error, sphere-fit
RMS, and the geometric condition number depend on:

  1. sweep half-angle   (geometry / dilution of precision)
  2. measurement noise  (sensor sigma)
  3. number of points   (averaging, ~1/sqrt(n))

Prints (a) booktabs table rows and (b) pgfplots `coordinates{...}` blocks that
are pasted verbatim into the detailed report (detailed/main.tex), then runs a
self-check assert.

Reproducible: fixed ground truth + fixed seed set. Regenerate the report numbers
with:  python docs/reports/ipt/detailed/sim_study.py
Dependencies: numpy only (solver is pure numpy).
"""
import os
import sys

import numpy as np

# this file: docs/reports/ipt/detailed/ -> repo root is four levels up
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO_ROOT)
from tools.ipt.solver import sample_directions, solve_ipt  # noqa: E402

P_TRUE = np.array([1200.0, -450.0, 300.0])
L_TRUE = 400.0
SEEDS = range(16)  # average each configuration over 16 noise realisations


def _cloud(n, half_angle_deg, sigma, seed):
    """One synthetic sweep: attachment points on a sphere of radius L_TRUE."""
    rng = np.random.default_rng(seed)
    dirs = sample_directions(n, half_angle_deg)
    M = P_TRUE + L_TRUE * dirs
    if sigma > 0:
        M = M + rng.normal(0.0, sigma, M.shape)
    return M


def _trial(n, half_angle_deg, sigma):
    """Mean over SEEDS of (target err, L_hat err, rms, cond) — self-calibrating."""
    errs, lerrs, rmss, conds = [], [], [], []
    for s in SEEDS:
        out = solve_ipt(_cloud(n, half_angle_deg, sigma, s))
        if not out["ok"]:
            continue
        errs.append(float(np.linalg.norm(out["P"] - P_TRUE)))
        lerrs.append(abs(out["L_hat"] - L_TRUE))
        rmss.append(out["rms_resid"])
        conds.append(out["cond"])
    return (float(np.mean(errs)), float(np.mean(lerrs)),
            float(np.mean(rmss)), float(np.mean(conds)))


def _pgf(pairs):
    """Format (x, y) pairs as a pgfplots coordinate list."""
    return " ".join(f"({x:g},{y:.4g})" for x, y in pairs)


def main():
    angles = [2, 3, 5, 8, 12, 18, 25, 35, 50, 70]
    sigmas = [0.0, 0.05, 0.1, 0.2, 0.5, 1.0]
    ns = [8, 10, 12, 16, 20, 30, 40]

    # --- Sweep 1: geometry (half-angle), n=12, sigma=0.1 -------------------
    print("=" * 72)
    print("SWEEP 1  error & cond vs sweep half-angle   (n=12, sigma=0.1 mm)")
    print("=" * 72)
    print(f"{'angle':>6} {'cond':>10} {'rms_mm':>10} {'err_mm':>10} {'L_err_mm':>10}")
    g_err, g_cond = [], []
    for a in angles:
        err, lerr, rms, cond = _trial(12, a, 0.1)
        g_err.append((a, err))
        g_cond.append((a, cond))
        print(f"{a:>6} {cond:>10.1f} {rms:>10.4f} {err:>10.4f} {lerr:>10.4f}")
        # booktabs row for the report
        print(f"    LaTeX:  {a}$^\\circ$ & {cond:.0f} & {rms:.3f} & {err:.3f} & {lerr:.3f} \\\\")

    # --- Sweep 2: noise sigma, angle=35, n=12 ------------------------------
    print("\n" + "=" * 72)
    print("SWEEP 2  error vs noise sigma   (half-angle=35 deg, n=12)")
    print("=" * 72)
    print(f"{'sigma':>6} {'err_mm':>10}")
    s_err = []
    for sg in sigmas:
        err, _, _, _ = _trial(12, 35, sg)
        s_err.append((sg, err))
        print(f"{sg:>6.2f} {err:>10.4f}")

    # --- Sweep 3: point count n, angle=35, sigma=0.1 -----------------------
    print("\n" + "=" * 72)
    print("SWEEP 3  error vs point count n   (half-angle=35 deg, sigma=0.1 mm)")
    print("=" * 72)
    print(f"{'n':>6} {'err_mm':>10} {'1/sqrt(n) ref':>14}")
    n_err = []
    ref0 = None
    for nn in ns:
        err, _, _, _ = _trial(nn, 35, 0.1)
        if ref0 is None:
            ref0 = err * np.sqrt(nn)
        n_err.append((nn, err))
        print(f"{nn:>6} {err:>10.4f} {ref0 / np.sqrt(nn):>14.4f}")

    # --- pgfplots coordinate blocks (paste into detailed/main.tex) ---------
    print("\n" + "=" * 72)
    print("PGFPLOTS coordinate blocks")
    print("=" * 72)
    print("% error vs half-angle (log y)\n\\addplot coordinates {" + _pgf(g_err) + "};")
    print("% cond vs half-angle\n\\addplot coordinates {" + _pgf(g_cond) + "};")
    print("% error vs sigma\n\\addplot coordinates {" + _pgf(s_err) + "};")
    print("% error vs n\n\\addplot coordinates {" + _pgf(n_err) + "};")

    # --- self-check: solver + numbers must not regress ---------------------
    err35, _, _, cond35 = _trial(12, 35, 0.1)
    out = solve_ipt(_cloud(12, 35, 0.1, 7))
    assert err35 < 2.0, f"35deg mean target error regressed: {err35:.3f} mm"
    assert cond35 < 60.0, f"35deg cond regressed: {cond35:.1f}"
    assert out["slip_warning"] == "ok" and out["geom_warning"] == "ok", out
    print(f"\nself-check OK: 35deg mean err={err35:.3f} mm, cond={cond35:.0f}, "
          f"flags ok/ok")


if __name__ == "__main__":
    main()
