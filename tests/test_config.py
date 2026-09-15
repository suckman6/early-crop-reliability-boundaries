import unittest

from rcecrop.config import RiskCalibrationConfig


class ConfigTests(unittest.TestCase):
    def test_mapping_is_strict(self):
        config = RiskCalibrationConfig.from_mapping({"label_count": 9})
        self.assertEqual(config.label_count, 9)
        with self.assertRaisesRegex(ValueError, "unknown"):
            RiskCalibrationConfig.from_mapping({"typo": 1})

    def test_invalid_risk_is_rejected(self):
        with self.assertRaises(ValueError):
            RiskCalibrationConfig(overall_risk=0.0)
        with self.assertRaises(ValueError):
            RiskCalibrationConfig(candidate_size=0)


if __name__ == "__main__":
    unittest.main()
