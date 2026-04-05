"""test_math_conventions.py — verify spherical↔Cartesian math against firmware convention.

Authoritative convention (from SphericalSensor.cpp and CLAUDE.md):
    x = r * cos(phi) * cos(theta)
    y = r * cos(phi) * sin(theta)
    z = r * sin(phi)
    phi = -90° arm down, 0° horizontal, +90° arm up
    theta = azimuth from +X in XY-plane
"""

import math
import unittest

from tools.position_checker.transform import (
    cartesian_to_spherical,
    spherical_to_cartesian,
)


class SphericalToCartesianTests(unittest.TestCase):
    """Forward conversion: (r, theta, phi) → (x, y, z)."""

    def test_horizontal_along_x(self) -> None:
        """phi=0, theta=0 → arm points along +X."""
        x, y, z = spherical_to_cartesian(100.0, 0.0, 0.0)
        self.assertAlmostEqual(x, 100.0, places=6)
        self.assertAlmostEqual(y,   0.0, places=6)
        self.assertAlmostEqual(z,   0.0, places=6)

    def test_arm_up(self) -> None:
        """phi=+90 → arm points straight up (+Z)."""
        x, y, z = spherical_to_cartesian(100.0, 0.0, 90.0)
        self.assertAlmostEqual(x,   0.0, places=5)
        self.assertAlmostEqual(y,   0.0, places=5)
        self.assertAlmostEqual(z, 100.0, places=5)

    def test_arm_down(self) -> None:
        """phi=-90 → arm points straight down (-Z)."""
        x, y, z = spherical_to_cartesian(100.0, 0.0, -90.0)
        self.assertAlmostEqual(x,    0.0, places=5)
        self.assertAlmostEqual(y,    0.0, places=5)
        self.assertAlmostEqual(z, -100.0, places=5)

    def test_theta_90_horizontal(self) -> None:
        """phi=0, theta=+90 → arm points along +Y."""
        x, y, z = spherical_to_cartesian(100.0, 90.0, 0.0)
        self.assertAlmostEqual(x,   0.0, places=5)
        self.assertAlmostEqual(y, 100.0, places=5)
        self.assertAlmostEqual(z,   0.0, places=5)

    def test_theta_180_horizontal(self) -> None:
        """phi=0, theta=180 → arm points along -X."""
        x, y, z = spherical_to_cartesian(100.0, 180.0, 0.0)
        self.assertAlmostEqual(x, -100.0, places=5)
        self.assertAlmostEqual(y,    0.0, places=5)
        self.assertAlmostEqual(z,    0.0, places=5)

    def test_zero_radius(self) -> None:
        """r=0 → origin regardless of angles."""
        x, y, z = spherical_to_cartesian(0.0, 45.0, 30.0)
        self.assertAlmostEqual(x, 0.0, places=9)
        self.assertAlmostEqual(y, 0.0, places=9)
        self.assertAlmostEqual(z, 0.0, places=9)

    def test_matches_firmware_formula_general(self) -> None:
        """Spot-check against direct formula evaluation (r=500, θ=37, φ=25)."""
        r, theta_deg, phi_deg = 500.0, 37.0, 25.0
        theta_rad = math.radians(theta_deg)
        phi_rad   = math.radians(phi_deg)
        expected_x = r * math.cos(phi_rad) * math.cos(theta_rad)
        expected_y = r * math.cos(phi_rad) * math.sin(theta_rad)
        expected_z = r * math.sin(phi_rad)
        x, y, z = spherical_to_cartesian(r, theta_deg, phi_deg)
        self.assertAlmostEqual(x, expected_x, places=6)
        self.assertAlmostEqual(y, expected_y, places=6)
        self.assertAlmostEqual(z, expected_z, places=6)


class CartesianToSphericalTests(unittest.TestCase):
    """Inverse conversion: (x, y, z) → (r, theta, phi)."""

    def test_along_x_axis(self) -> None:
        """Point on +X → r=distance, theta=0, phi=0."""
        r, theta, phi = cartesian_to_spherical(200.0, 0.0, 0.0)
        self.assertAlmostEqual(r,     200.0, places=6)
        self.assertAlmostEqual(theta,   0.0, places=6)
        self.assertAlmostEqual(phi,     0.0, places=6)

    def test_along_z_axis_positive(self) -> None:
        """Point on +Z → phi=+90."""
        r, theta, phi = cartesian_to_spherical(0.0, 0.0, 150.0)
        self.assertAlmostEqual(r,   150.0, places=5)
        self.assertAlmostEqual(phi,  90.0, places=5)

    def test_along_z_axis_negative(self) -> None:
        """Point on -Z → phi=-90."""
        r, theta, phi = cartesian_to_spherical(0.0, 0.0, -150.0)
        self.assertAlmostEqual(r,   150.0, places=5)
        self.assertAlmostEqual(phi, -90.0, places=5)

    def test_origin_returns_zeros(self) -> None:
        """Origin → (0, 0, 0) without NaN."""
        r, theta, phi = cartesian_to_spherical(0.0, 0.0, 0.0)
        self.assertAlmostEqual(r,     0.0, places=9)
        self.assertAlmostEqual(theta, 0.0, places=9)
        self.assertAlmostEqual(phi,   0.0, places=9)


class RoundTripTests(unittest.TestCase):
    """Verify spherical_to_cartesian and cartesian_to_spherical are mutual inverses."""

    _CASES = [
        (100.0,    0.0,   0.0),
        (200.0,   45.0,  30.0),
        (350.0,  -60.0, -45.0),
        (500.0,  180.0,  90.0),
        (500.0,  180.0, -90.0),
        (  1.0,   37.0,  25.0),
        (999.0, -135.0,  15.0),
    ]

    def test_spherical_to_cartesian_to_spherical(self) -> None:
        """Forward then inverse returns original (r, theta, phi)."""
        for r, theta_deg, phi_deg in self._CASES:
            with self.subTest(r=r, theta=theta_deg, phi=phi_deg):
                x, y, z = spherical_to_cartesian(r, theta_deg, phi_deg)
                r2, theta2, phi2 = cartesian_to_spherical(x, y, z)
                self.assertAlmostEqual(r2,   r,       places=5)
                self.assertAlmostEqual(phi2, phi_deg, places=5)
                # theta is degenerate at poles (phi=±90); skip it there.
                if abs(phi_deg) < 89.9:
                    self.assertAlmostEqual(theta2, theta_deg, places=5)

    def test_cartesian_to_spherical_to_cartesian(self) -> None:
        """Inverse then forward returns original (x, y, z)."""
        cartesian_cases = [
            (100.0,  0.0,   0.0),
            ( 50.0, 80.0,  30.0),
            (-70.0, 40.0, -20.0),
            (  0.0,  0.0, 200.0),
        ]
        for x, y, z in cartesian_cases:
            with self.subTest(x=x, y=y, z=z):
                r, theta_deg, phi_deg = cartesian_to_spherical(x, y, z)
                x2, y2, z2 = spherical_to_cartesian(r, theta_deg, phi_deg)
                self.assertAlmostEqual(x2, x, places=5)
                self.assertAlmostEqual(y2, y, places=5)
                self.assertAlmostEqual(z2, z, places=5)

    def test_software_zero_r_equals_xyz_magnitude(self) -> None:
        """After software zero: r_display must equal sqrt(x²+y²+z²).

        This is the core bug that was fixed. If XYZ is zeroed relative to an
        offset and R/θ/φ are re-derived from the zeroed Cartesian, then
        r_display == sqrt(x_display² + y_display² + z_display²).
        """
        raw_x, raw_y, raw_z = 300.0, 100.0, 50.0
        # User zeros at current position.
        offset_x, offset_y, offset_z = raw_x, raw_y, raw_z
        # Arm moves to a new position.
        new_x, new_y, new_z = 320.0, 115.0, 45.0
        # Display Cartesian (zeroed).
        disp_x = new_x - offset_x   # 20.0
        disp_y = new_y - offset_y   # 15.0
        disp_z = new_z - offset_z   # -5.0
        # Display spherical derived from display Cartesian.
        disp_r, _, _ = cartesian_to_spherical(disp_x, disp_y, disp_z)
        expected_r = math.sqrt(disp_x**2 + disp_y**2 + disp_z**2)
        self.assertAlmostEqual(disp_r, expected_r, places=6)


if __name__ == "__main__":
    unittest.main()
