"""test_cmd_gui_zero.py — regression tests for CMD GUI display-offset logic."""

import math
import unittest

from tools.position_checker.cmd_display import (
    CmdDisplayState,
    process_sensor_line,
    process_xyz_frame,
    sta_ip_display,
    sta_ip_is_connected,
)


class ApplyOffsetsTests(unittest.TestCase):
    def test_no_offset_when_inactive(self) -> None:
        state = CmdDisplayState()
        self.assertEqual(state.apply_offsets(100.0, 200.0, 50.0), (100.0, 200.0, 50.0))

    def test_full_software_zero(self) -> None:
        state = CmdDisplayState(
            offset_x=300.0,
            offset_y=100.0,
            offset_z=50.0,
            relative_zero_active=True,
        )
        self.assertEqual(state.apply_offsets(320.0, 115.0, 45.0), (20.0, 15.0, -5.0))


class ProcessXyzFrameTests(unittest.TestCase):
    def test_software_zero_r_equals_xyz_magnitude(self) -> None:
        state = CmdDisplayState()
        process_xyz_frame(state, 300.0, 100.0, 50.0)
        state.offset_x, state.offset_y, state.offset_z = 300.0, 100.0, 50.0
        state.relative_zero_active = True
        pos2 = process_xyz_frame(state, 320.0, 115.0, 45.0)
        expected_r = math.sqrt(20.0 ** 2 + 15.0 ** 2 + (-5.0) ** 2)
        self.assertAlmostEqual(pos2.r, expected_r, places=6)
        self.assertTrue(pos2.update_spherical)

    def test_at_zero_origin_after_soft_zero(self) -> None:
        state = CmdDisplayState()
        process_xyz_frame(state, 500.0, 100.0, 50.0)
        state.offset_x = 500.0
        state.offset_y = 100.0
        state.offset_z = 50.0
        state.relative_zero_active = True
        pos = process_xyz_frame(state, 500.0, 100.0, 50.0, track_minmax=False)
        self.assertAlmostEqual(pos.x, 0.0, places=6)
        self.assertAlmostEqual(pos.y, 0.0, places=6)
        self.assertAlmostEqual(pos.z, 0.0, places=6)
        self.assertAlmostEqual(pos.r, 0.0, places=6)
        self.assertAlmostEqual(pos.theta, 0.0, places=6)
        self.assertAlmostEqual(pos.phi, 0.0, places=6)

    def test_sensor_after_xyz_does_not_change_spherical_when_active(self) -> None:
        """Simulate event order: X line zeroes display, SENSOR must not restore firmware R."""
        state = CmdDisplayState()
        process_xyz_frame(state, 900.0, 0.0, 0.0)
        state.offset_x, state.offset_y, state.offset_z = 900.0, 0.0, 0.0
        state.relative_zero_active = True
        pos = process_xyz_frame(state, 900.0, 0.0, 0.0, track_minmax=False)
        self.assertAlmostEqual(pos.r, 0.0, places=6)

        r_theta_phi, _, _ = process_sensor_line(state, 900.0, 0.0, 0.0, 1, 42)
        self.assertIsNone(r_theta_phi)

    def test_sensor_updates_spherical_when_inactive(self) -> None:
        state = CmdDisplayState()
        r_theta_phi, is_valid, frame = process_sensor_line(state, 500.0, 45.0, 10.0, 1, 7)
        self.assertEqual(r_theta_phi, (500.0, 45.0, 10.0))
        self.assertTrue(is_valid)
        self.assertEqual(frame, 7)


class SavedPointFormatTests(unittest.TestCase):
    def test_world_frame_label(self) -> None:
        state = CmdDisplayState()
        text = state.format_point_entry("0", 100.0, 200.0, 50.0)
        self.assertIn("(world)", text)
        self.assertIn("100.0", text)

    def test_display_frame_label_when_sw_zero(self) -> None:
        state = CmdDisplayState(
            offset_x=100.0,
            offset_y=200.0,
            offset_z=50.0,
            relative_zero_active=True,
        )
        text = state.format_point_entry("1", 110.0, 215.0, 45.0)
        self.assertIn("(display)", text)
        self.assertIn("10.00", text)


class StaIpTests(unittest.TestCase):
    def test_not_connected_variants(self) -> None:
        self.assertEqual(sta_ip_display("NOT_CONNECTED"), "Not Connected")
        self.assertEqual(sta_ip_display("BAGLI_DEGIL"), "Not Connected")
        self.assertFalse(sta_ip_is_connected("NOT_CONNECTED"))
        self.assertTrue(sta_ip_is_connected("192.168.1.84"))


if __name__ == "__main__":
    unittest.main()
