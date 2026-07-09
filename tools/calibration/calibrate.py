#!/usr/bin/env python3
"""calibrate.py — Compute sensor-to-world rigid body transform using the Kabsch algorithm.

Finds the best-fit rotation R (3x3) and translation t (3,) such that:
    world_point ≈ R @ sensor_point + t

Usage (from project root):
    python -m tools.calibration.calibrate
    python -m tools.calibration.calibrate --out tools/calibration/calibration.json
"""

import argparse
import json
import math
import os

import numpy as np

# ---------------------------------------------------------------------------
# Measured calibration data — 2026-03-25 full 3D session v2 (12 points)
# 3-layer grid: Z=0, Z=160, Z=260 with XY corners
# ---------------------------------------------------------------------------
LABELS = ["ORIGIN","P1","P2","P3","P4","P5","P6","P7","P8","P9","P10","P11"]

SENSOR_PTS = np.array([
    [1106.28,  25.38, -160.68],  # ORIGIN → (  0,   0,   0)
    [1163.11, 526.04, -185.84],  # P1     → (  0, 600,   0)
    [1641.86, 551.78, -119.46],  # P2     → (500, 600,   0)
    [1603.38,  56.94, -126.27],  # P3     → (500,   0,   0)
    [1092.65,  69.78,   -7.57],  # P4     → (  0,   0, 160)
    [1142.91, 547.05,  -48.19],  # P5     → (  0, 600, 160)
    [1634.69, 531.71,    6.49],  # P6     → (500, 600, 160)
    [1586.25,  68.81,  -48.90],  # P7     → (500,   0, 160)
    [1093.09,  59.81,  -31.65],  # P8     → (  0,   0, 260)
    [1155.65, 522.67,   84.31],  # P9     → (  0, 600, 260)
    [1622.95, 563.08,   52.91],  # P10    → (500, 600, 260)
    [1593.27,  69.62,  -23.55],  # P11    → (500,   0, 260)
], dtype=float)

WORLD_PTS = np.array([
    [  0,   0,   0],
    [  0, 600,   0],
    [500, 600,   0],
    [500,   0,   0],
    [  0,   0, 160],
    [  0, 600, 160],
    [500, 600, 160],
    [500,   0, 160],
    [  0,   0, 260],
    [  0, 600, 260],
    [500, 600, 260],
    [500,   0, 260],
], dtype=float)


def kabsch(P: np.ndarray, Q: np.ndarray):
    """Kabsch algorithm: find R, t that minimises sum||Q_i - (R@P_i + t)||^2.

    Args:
        P: (N, 3) source points (sensor frame)
        Q: (N, 3) target points (world frame)

    Returns:
        R: (3, 3) rotation matrix
        t: (3,)  translation vector
    """
    Pc = P.mean(axis=0)
    Qc = Q.mean(axis=0)
    Pp = P - Pc
    Qp = Q - Qc

    H = Pp.T @ Qp
    U, _, Vt = np.linalg.svd(H)

    # Correct for reflection (ensure proper rotation, det=+1)
    d = np.linalg.det(Vt.T @ U.T)
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    t = Qc - R @ Pc
    return R, t


def main():
    parser = argparse.ArgumentParser(
        description="Compute sensor→world calibration transform and save to JSON."
    )
    default_out = os.path.join(
        os.path.dirname(__file__), "calibration.json"
    )
    parser.add_argument(
        "--out", default=default_out,
        help=f"Output path for calibration JSON (default: {default_out})",
    )
    args = parser.parse_args()

    R, t = kabsch(SENSOR_PTS, WORLD_PTS)

    print("=== Kabsch Calibration Result ===\n")
    print("Rotation matrix R (sensor → world):")
    for row in R:
        print(f"  [{row[0]:+.6f}  {row[1]:+.6f}  {row[2]:+.6f}]")
    print(f"\nTranslation t (mm): [{t[0]:+.3f}  {t[1]:+.3f}  {t[2]:+.3f}]")

    # --- Per-point residuals ---
    errors = []
    print("\n--- Per-point residuals ---")
    print(f"{'Label':8s}  {'Computed world (mm)':42s}  {'Known world (mm)':35s}  {'Error mm':>8s}")
    for i, label in enumerate(LABELS):
        computed = R @ SENSOR_PTS[i] + t
        known = WORLD_PTS[i]
        err = math.sqrt(((computed - known) ** 2).sum())
        errors.append(err)
        cx, cy, cz = computed
        kx, ky, kz = known
        print(
            f"{label:8s}  ({cx:+8.2f}, {cy:+8.2f}, {cz:+8.2f})"
            f"  ({kx:+8.2f}, {ky:+8.2f}, {kz:+8.2f})"
            f"  {err:8.2f}"
        )

    rmse = math.sqrt(sum(e**2 for e in errors) / len(errors))
    print(f"\nRMSE: {rmse:.2f} mm")
    print(f"Max error: {max(errors):.2f} mm  (at {LABELS[errors.index(max(errors))]})")

    # --- Save calibration ---
    calib = {
        "R": R.tolist(),
        "t": t.tolist(),
        "rmse_mm": round(rmse, 3),
        "n_points": len(LABELS),
    }
    with open(args.out, "w") as f:
        json.dump(calib, f, indent=2)
    print(f"\nCalibration saved to: {args.out}")


if __name__ == "__main__":
    main()
