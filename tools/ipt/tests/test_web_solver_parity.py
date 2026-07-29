"""The web dashboard's IPT solver is a hand port of solver.py into JavaScript.

Nothing else keeps the two honest, so this test extracts the JS straight out of the
PROGMEM blob in WebDashboard.cpp, runs it under node, and compares it against the
Python on the *same* clouds (generated once, in Python — so there is no RNG-parity
question).

Three layers:
  1. the linear-algebra kernel, vs numpy
  2. the full solver, vs solve_ipt()
  3. a no-node guard that always runs: markers present, region DOM-free, thresholds
     equal. Threshold drift is the likeliest long-term divergence and it needs no node.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from tools.ipt import capture, solver

REPO = Path(__file__).resolve().parents[3]
BLOB = REPO / "firmware" / "src" / "WebDashboard.cpp"
BEGIN = "// ===== IPT-SOLVER-BEGIN ====="
END = "// ===== IPT-SOLVER-END ====="

# Anything DOM-ish in the solver region would make it unextractable — and would mean
# the numerics had quietly grown a dependency on the page.
BANNED = ("document.", "getElementById", "window.", "canvas", "setText")

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

DRIVER = """
const req = JSON.parse(require("fs").readFileSync(0, "utf8"));
let out;
if (req.mode === "solve")      out = iptSolve(req.M, req.L === undefined ? null : req.L);
else if (req.mode === "lstsq") out = { x: Array.from(iptLstsq(req.A, req.b, req.k)) };
else if (req.mode === "cond")  out = { cond: iptGeometryCond(req.M, req.C) };
if (out && out.P) out.P = Array.from(out.P);
process.stdout.write(JSON.stringify(out));
"""


def extract_js() -> str:
    src = BLOB.read_text(encoding="utf-8")
    m = re.search(re.escape(BEGIN) + r"(.*?)" + re.escape(END), src, re.S)
    assert m, f"IPT solver markers missing from {BLOB}"
    js = m.group(1)
    for banned in BANNED:
        assert banned not in js, f"solver region must stay DOM-free (found {banned!r})"
    return js


def run_js(tmp_path: Path, payload: dict) -> dict:
    harness = tmp_path / "ipt_harness.cjs"      # .cjs: no package.json, plain require()
    harness.write_text(extract_js() + DRIVER, encoding="utf-8")
    proc = subprocess.run(
        ["node", str(harness)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, f"node failed: {proc.stderr}"
    return json.loads(proc.stdout)


def make_cloud(n, half_angle, P=(1200.0, -450.0, 300.0), L=400.0, sigma=0.1, seed=7):
    rng = np.random.default_rng(seed)
    M = np.asarray(P) + L * solver.sample_directions(n, half_angle)
    return M + rng.normal(0, sigma, M.shape)


# ---------------------------------------------------------------- layer 3 (no node)
def test_solver_region_is_present_and_dom_free():
    js = extract_js()
    for fn in ("iptLstsq", "iptCholSolve", "iptJacobiEig4", "iptFitSphereAlgebraic",
               "iptTrilaterateFixedRadius", "iptRefineNonlinear", "iptGeometryCond",
               "iptSolve"):
        assert f"function {fn}(" in js, f"{fn} missing from the JS solver"


def test_thresholds_match_python():
    """The likeliest long-term divergence, and it needs no node to catch."""
    js = extract_js()

    def const(name: str) -> float:
        m = re.search(rf"{name}\s*=\s*([0-9.]+)", js)
        assert m, f"{name} not found in the JS solver"
        return float(m.group(1))

    assert const("IPT_MIN_POINTS") == solver.MIN_POINTS
    assert const("IPT_RESIDUAL_ACCEPT_MM") == solver.RESIDUAL_ACCEPT_MM
    assert const("IPT_RESIDUAL_REJECT_MM") == solver.RESIDUAL_REJECT_MM
    assert const("IPT_COND_WARN") == solver.COND_WARN
    assert const("IPT_COND_BLOCK") == solver.COND_BLOCK
    assert const("IPT_MIN_DISP_MM") == capture.DEFAULT_MIN_DISP_MM


# ---------------------------------------------------------------- layer 1 (kernel)
@needs_node
@pytest.mark.parametrize("n,k", [(10, 4), (9, 3), (40, 4)])
def test_lstsq_matches_numpy(tmp_path, n, k):
    rng = np.random.default_rng(11)
    A = rng.normal(size=(n, k))
    b = rng.normal(size=n)
    got = run_js(tmp_path, {"mode": "lstsq", "A": A.tolist(), "b": b.tolist(), "k": k})
    want, *_ = np.linalg.lstsq(A, b, rcond=None)
    np.testing.assert_allclose(got["x"], want, rtol=1e-9, atol=1e-9)


@needs_node
@pytest.mark.parametrize("half_angle", [45.0, 20.0, 8.0])
def test_geometry_cond_matches_numpy(tmp_path, half_angle):
    M = make_cloud(14, half_angle)
    C = np.array([1200.0, -450.0, 300.0])
    got = run_js(tmp_path, {"mode": "cond", "M": M.tolist(), "C": C.tolist()})
    want = solver.geometry_cond(M, C)
    assert got["cond"] == pytest.approx(want, rel=1e-9)


# ---------------------------------------------------------------- layer 2 (solver)
@needs_node
@pytest.mark.parametrize(
    "name,kwargs,L",
    [
        ("nominal self-cal", dict(n=12, half_angle=35.0), None),
        ("known L", dict(n=12, half_angle=35.0), 400.0),
        ("dense", dict(n=60, half_angle=45.0), None),
        ("far from origin", dict(n=12, half_angle=35.0, P=(3000.0, -2500.0, 1800.0)), None),
        ("far from origin, known L", dict(n=12, half_angle=35.0, P=(3000.0, -2500.0, 1800.0)), 400.0),
        ("marginal geometry", dict(n=12, half_angle=8.0), None),
        ("tip slip", dict(n=12, half_angle=35.0, sigma=5.0), None),
    ],
)
def test_full_solver_matches_python(tmp_path, name, kwargs, L):
    M = make_cloud(**kwargs)
    payload = {"mode": "solve", "M": M.tolist()}
    if L is not None:
        payload["L"] = L
    got = run_js(tmp_path, payload)
    want = solver.solve_ipt(M, L=L)

    assert got["ok"] is True and want["ok"] is True
    np.testing.assert_allclose(got["P"], want["P"], atol=1e-6)
    assert got["L_hat"] == pytest.approx(want["L_hat"], abs=1e-6)
    assert got["L_fit"] == pytest.approx(want["L_fit"], abs=1e-6)
    assert got["rms_resid"] == pytest.approx(want["rms_resid"], abs=1e-9)
    assert got["cond"] == pytest.approx(want["cond"], rel=1e-6)
    # The gates are what the operator actually acts on — they must agree exactly.
    assert got["slip_warning"] == want["slip_warning"]
    assert got["geom_warning"] == want["geom_warning"]


@needs_node
def test_too_few_points_is_rejected_the_same_way(tmp_path):
    M = make_cloud(n=7, half_angle=35.0)
    got = run_js(tmp_path, {"mode": "solve", "M": M.tolist()})
    want = solver.solve_ipt(M)
    assert got["ok"] is False and want["ok"] is False
    assert got["n_points"] == want["n_points"] == 7


@needs_node
def test_degenerate_cloud_is_blocked_by_both(tmp_path):
    """A straight pull, not a spiral.

    numpy's lstsq takes a min-norm solution where our Cholesky takes a ridge, so the
    two legitimately disagree on the numbers here. What must agree is the verdict:
    both have to say the geometry is unusable, because that is what stops the operator
    trusting a garbage point.
    """
    t = np.linspace(0, 1, 12)
    M = np.stack([1200 + 400 * t, -450 + 0.02 * t, 300 + 0.02 * t], axis=1)
    got = run_js(tmp_path, {"mode": "solve", "M": M.tolist()})
    want = solver.solve_ipt(M)
    if got.get("ok") and want.get("ok"):
        assert got["geom_warning"] == "block"
        assert want["geom_warning"] == "block"
    else:
        assert not got.get("ok") and not want.get("ok")
