"""test_solver.py — IPT sphere-fit solver checks (offline, no hardware)."""

import numpy as np
import pytest

from tools.ipt.solver import MIN_POINTS, sample_directions, solve_ipt

P_TRUE = np.array([1200.0, -450.0, 300.0])
L_TRUE = 400.0


def make_cloud(n=12, half_angle_deg=35.0, sigma=0.1, slip=0.0, P=P_TRUE, L=L_TRUE,
               seed=7):
    """Synthesise a measured attachment-point cloud for a known target/pen."""
    rng = np.random.default_rng(seed)
    M = P + L * sample_directions(n, half_angle_deg)
    if slip > 0:
        M = M + rng.normal(0, slip, M.shape)        # tip wander = model violation
    M = M + rng.normal(0, sigma, M.shape)           # base measurement noise
    return M


def test_recovers_target_and_self_calibrates_length():
    out = solve_ipt(make_cloud())
    assert out["ok"]
    assert np.linalg.norm(out["P"] - P_TRUE) < 2.0
    assert abs(out["L_hat"] - L_TRUE) < 1.0
    assert out["slip_warning"] == "ok"
    assert out["geom_warning"] == "ok"


def test_known_radius_path_matches():
    out = solve_ipt(make_cloud(), L=L_TRUE)
    assert out["ok"]
    assert np.linalg.norm(out["P"] - P_TRUE) < 2.0


def test_slip_warning_fires_on_tip_wander():
    clean = solve_ipt(make_cloud(slip=0.0))
    slipped = solve_ipt(make_cloud(slip=5.0))   # ~3.6 mm rms — clears the 2 mm gate
    assert clean["slip_warning"] == "ok"
    assert slipped["slip_warning"] in ("warn", "reject")


def test_tiny_sweep_flags_poor_geometry():
    out = solve_ipt(make_cloud(half_angle_deg=2.0))
    assert out["geom_warning"] in ("warn", "block")


def test_too_few_points_returns_error_not_crash():
    out = solve_ipt(make_cloud(n=MIN_POINTS - 1))
    assert out["ok"] is False
    assert out["n_points"] == MIN_POINTS - 1


def test_centering_handles_large_offset():
    """A cloud far from the origin must fit as accurately as one near it
    (regression for the Coope column-scale / centering fix)."""
    near = solve_ipt(make_cloud(P=np.array([5.0, -3.0, 4.0])))
    far = solve_ipt(make_cloud(P=np.array([3000.0, -2500.0, 1800.0])))
    near_err = np.linalg.norm(near["P"] - np.array([5.0, -3.0, 4.0]))
    far_err = np.linalg.norm(far["P"] - np.array([3000.0, -2500.0, 1800.0]))
    assert far_err < 2.0
    assert far_err < near_err * 5 + 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
