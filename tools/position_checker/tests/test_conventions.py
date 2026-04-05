import unittest

from tools.position_checker.cmd_main import (
    DATA_FIELDS,
    FIRMWARE_PHI_AUTHORITATIVE,
    PIN_MAP,
    SENSOR_FIELDS,
)


class ConventionTests(unittest.TestCase):
    def test_data_fields_follow_firmware_order(self) -> None:
        self.assertEqual(
            DATA_FIELDS,
            (
                "x_mm",
                "y_mm",
                "z_mm",
                "r_mm",
                "theta_deg",
                "phi_deg",
                "is_valid",
                "frame_count",
                "ts_ms",
            ),
        )

    def test_sensor_fields_follow_firmware_order(self) -> None:
        self.assertEqual(
            SENSOR_FIELDS,
            ("r_mm", "theta_deg", "phi_deg", "is_valid", "frame_count"),
        )

    def test_phi_authority_enabled(self) -> None:
        self.assertTrue(FIRMWARE_PHI_AUTHORITATIVE)

    def test_pin_map_matches_firmware_header(self) -> None:
        self.assertEqual(PIN_MAP["theta_a"], 14)
        self.assertEqual(PIN_MAP["theta_b"], 12)
        self.assertEqual(PIN_MAP["phi_a"], 32)
        self.assertEqual(PIN_MAP["phi_b"], 35)
        self.assertEqual(PIN_MAP["wire_a"], 16)
        self.assertEqual(PIN_MAP["wire_b"], 17)


if __name__ == "__main__":
    unittest.main()
