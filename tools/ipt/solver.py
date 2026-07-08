"""solver.py — Quick IPT hidden-point sphere-fit solver.

Ported from the reference ipt_solver.py. Physical model: while the operator holds
the pen TIP fixed on a hidden target P, evka_position measures the WIRE-SIDE point
M_i (offset L from the tip). Every M_i lies on a sphere of radius L centred on P,
so recovering P is a sphere fit (radius unknown → self-calibrates L) or a
known-radius trilateration. This is the patented Prodim method (US 9,267,794 B2)
and is mathematically identical to surgical pivot / robot TCP calibration.

Three estimators plus a single `solve_ipt()` entry point. Dependencies: numpy.
"""
import numpy as np
from numpy.linalg import lstsq, norm

MIN_POINTS = 8                  # 4 defines a sphere; 8 gives stable real-world fits

# ponytail: heuristic gates, tune against real sweeps. Wire encoder + EMA filter is
# coarser than the sub-mm trackers in the pivot-calibration literature
# (Yaniv 2015 reports 0.3-0.8 mm there), so these are deliberately generous.
RESIDUAL_ACCEPT_MM = 2.0        # rms below this = clean fit
RESIDUAL_REJECT_MM = 5.0        # rms above this = tip slipped / bad data
# Geometry gate uses the condition number of the GEOMETRIC Jacobian (outward unit
# vectors) — the dilution-of-precision indicator. NOTE: the Coope algebraic cond
# is useless here because centring the cloud removes its scale-driven part; the
# geometric Jacobian cond instead tracks target error directly (≈35 at a rich 35°
# sweep, ≈1700 at a poor 5° sweep). Thresholds calibrated against simulation.
COND_WARN = 150.0               # ~15° cap → ~2 mm error: "make a bigger movement"
COND_BLOCK = 1500.0             # ~5° cap → ~20 mm error: geometry too degenerate


def fit_sphere_algebraic(M):
    """[A] Coope linear least squares. Centre C (=P) and radius r (=L) unknown.

    The cloud is centred before solving so the constant column (~1) is comparable
    in scale to the coordinate columns (~10^3 mm in this workspace); otherwise the
    condition number is inflated purely by column scaling.
    Returns (C, r, cond).
    """
    M = np.asarray(M, dtype=float)
    mean = M.mean(axis=0)
    Mc = M - mean
    A = np.hstack([2 * Mc, np.ones((len(Mc), 1))])
    b = np.sum(Mc ** 2, axis=1)
    sol, _, _, sv = lstsq(A, b, rcond=None)
    Cc = sol[:3]
    C = Cc + mean
    r = np.sqrt(max(0.0, sol[3] + Cc @ Cc))     # guard against negative radicand
    cond = sv[0] / sv[-1] if sv[-1] > 0 else np.inf
    return C, r, cond


def trilaterate_fixed_radius(M):
    """[B] Known-radius solve by differencing. Subtracting sphere 0 from sphere i
    cancels the quadratic term and the (equal) radius, leaving a system linear in P:
        2 (M_i - M_0) . P = |M_i|^2 - |M_0|^2 .
    Removing the radius unknown makes this far better conditioned than [A] when the
    pen length is fixed. The radius value itself is not needed — only that it is the
    same for every point. Needs n >= 4. Returns (P, cond).
    """
    M = np.asarray(M, dtype=float)
    if len(M) < 4:
        raise ValueError("need >= 4 points for fixed-radius trilateration")
    M0 = M[0]
    A = 2 * (M[1:] - M0)
    d = np.sum(M[1:] ** 2, axis=1) - np.sum(M0 ** 2)
    p, _, _, sv = lstsq(A, d, rcond=None)
    cond = sv[0] / sv[-1] if sv[-1] > 0 else np.inf
    return p, cond


def refine_nonlinear(M, C0, r0=None, fixed_r=None, max_iter=50):
    """[C] Gauss-Newton on the geometric residual f_i = ||M_i - C|| - r.
    Jacobian row = [-u_i^T, -1] with u_i the outward unit vector. Pass `fixed_r`
    to hold the radius (known pen length) and solve for C only. Returns (C, r, rms).
    """
    M = np.asarray(M, dtype=float)
    C = np.asarray(C0, dtype=float).copy()
    if fixed_r is not None:
        r = float(fixed_r)
    elif r0 is not None:
        r = float(r0)
    else:
        r = float(np.mean(norm(M - C, axis=1)))

    for _ in range(max_iter):
        diff = M - C
        dist = np.maximum(norm(diff, axis=1), 1e-9)      # guard div-by-zero
        u = diff / dist[:, None]
        f = dist - r
        if fixed_r is not None:
            J = -u
            dx, _, _, _ = lstsq(J, -f, rcond=None)
            if norm(dx) > 1e4:                            # divergence guard
                break
            C = C + dx
            if norm(dx) < 1e-9:
                break
        else:
            J = np.hstack([-u, -np.ones((len(M), 1))])
            dx, _, _, _ = lstsq(J, -f, rcond=None)
            if norm(dx) > 1e4:
                break
            C = C + dx[:3]
            r = r + dx[3]
            if norm(dx) < 1e-9:
                break

    res = norm(M - C, axis=1) - r
    rms = float(np.sqrt(np.mean(res ** 2)))
    return C, r, rms


def geometry_cond(M, C):
    """Condition number of the geometric Jacobian J = [u_i | 1] (u_i = outward unit
    vectors from centre C). High → poor angular spread → the centre is poorly
    constrained (dilution of precision). This, not the algebraic fit's condition
    number, is the meaningful "make a bigger movement" indicator.

    The 4-column (unknown-radius) Jacobian is used for BOTH the self-calibrating
    and known-L paths so the COND_WARN/COND_BLOCK thresholds stay consistent; it is
    monotone with angular spread in both cases.
    """
    M = np.asarray(M, dtype=float)
    diff = M - np.asarray(C, dtype=float)
    u = diff / np.maximum(norm(diff, axis=1), 1e-9)[:, None]
    J = np.hstack([u, np.ones((len(M), 1))])
    return float(np.linalg.cond(J))


def solve_ipt(M, L=None,
              residual_accept_mm=RESIDUAL_ACCEPT_MM,
              residual_reject_mm=RESIDUAL_REJECT_MM,
              cond_warn=COND_WARN, cond_block=COND_BLOCK):
    """Recover the hidden target P from measured attachment points M (n x 3, mm).

    L=None  → self-calibrating sphere fit (radius/pen length unknown); default.
              L_hat is the independently fitted radius.
    L given → use the better-conditioned differencing seed and hold the radius at L.
              L_hat equals L (the fixed value used). L_fit is the independent
              algebraic sphere-fit radius — compare L_fit vs L to sanity-check
              the entered pen length against the data.

    Returns a dict:
      {ok, P, L_hat, L_fit, rms_resid, cond, n_points, slip_warning, geom_warning}
    or {ok: False, error, n_points} when there are too few points.
    `slip_warning` ∈ {"ok","warn","reject"}; `geom_warning` ∈ {"ok","warn","block"}.
    P is in the same frame as the input (sensor origin / boot zero-point), in mm.
    """
    M = np.asarray(M, dtype=float).reshape(-1, 3)
    n = len(M)
    if n < MIN_POINTS:
        return {"ok": False,
                "error": f"need >= {MIN_POINTS} points, have {n}",
                "n_points": n}

    C_seed, r_seed, _ = fit_sphere_algebraic(M)
    L_fit = float(r_seed)
    if L is not None:
        # n >= MIN_POINTS (8) here, so the >= 4 precondition always holds.
        P_seed, _ = trilaterate_fixed_radius(M)
        P, L_hat, rms = refine_nonlinear(M, P_seed, fixed_r=float(L))
    else:
        P, L_hat, rms = refine_nonlinear(M, C_seed, r0=r_seed)

    cond = geometry_cond(M, P)

    if rms > residual_reject_mm:
        slip = "reject"
    elif rms > residual_accept_mm:
        slip = "warn"
    else:
        slip = "ok"

    if cond > cond_block:
        geom = "block"
    elif cond > cond_warn:
        geom = "warn"
    else:
        geom = "ok"

    return {
        "ok": True,
        "P": P,
        "L_hat": float(L_hat),
        "L_fit": L_fit,
        "rms_resid": rms,
        "cond": float(cond),
        "n_points": n,
        "slip_warning": slip,
        "geom_warning": geom,
    }


def sample_directions(n, half_angle_deg, axis=(0.3, 0.2, 1.0)):
    """Unit vectors tip→attachment over a spherical cap of the given half-angle,
    arranged on a golden/Fermat spiral — a faithful model of the operator's spiral
    hand motion. Used by the demo and the tests to synthesise clouds.
    """
    axis = np.asarray(axis, dtype=float)
    axis = axis / norm(axis)
    tmp = np.array([1.0, 0, 0]) if abs(axis[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = np.cross(axis, tmp); e1 /= norm(e1)
    e2 = np.cross(axis, e1)
    ha = np.radians(half_angle_deg)
    golden = np.pi * (3 - np.sqrt(5))
    dirs = []
    for i in range(n):
        t = ha * np.sqrt((i + 0.5) / n)       # polar angle, area-uniform on cap
        phi = i * golden                      # spiral azimuth
        d = np.cos(t) * axis + np.sin(t) * (np.cos(phi) * e1 + np.sin(phi) * e2)
        dirs.append(d)
    return np.array(dirs)


if __name__ == "__main__":
    rng = np.random.default_rng(7)
    P_true = np.array([1200.0, -450.0, 300.0])
    L_true = 400.0
    M = P_true + L_true * sample_directions(12, 35.0)
    M = M + rng.normal(0, 0.1, M.shape)
    out = solve_ipt(M)
    print("P_hat =", np.round(out["P"], 3), " L_hat = %.3f mm" % out["L_hat"],
          " rms = %.4f mm" % out["rms_resid"], " cond = %.0f" % out["cond"],
          " slip =", out["slip_warning"], " geom =", out["geom_warning"])
    print("target error = %.3f mm" % norm(out["P"] - P_true))
