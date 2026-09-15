import unittest

import numpy as np

from helpers import make_predictions
from rcecrop.config import RiskCalibrationConfig
from rcecrop.contracts import PrefixPredictions
from rcecrop.policy import Policy
from rcecrop.risk import calibrate_policies, clopper_pearson_upper


class RiskTests(unittest.TestCase):
    def test_exact_binomial_known_values(self):
        self.assertEqual(clopper_pearson_upper(0, 0, 0.05), 1.0)
        self.assertEqual(clopper_pearson_upper(10, 10, 0.05), 1.0)
        self.assertAlmostEqual(clopper_pearson_upper(0, 100, 0.05), 0.029513, places=5)
        self.assertAlmostEqual(clopper_pearson_upper(2, 10, 0.05), 0.506901, places=5)

    def test_bonferroni_counts_policies_and_classes(self):
        predictions = make_predictions()
        policies = (Policy(name="full", full_sequence=True), Policy(name="early", pmax_min=0.8))
        config = RiskCalibrationConfig(
            overall_risk=0.10, class_risk=0.10, label_count=2, candidate_size=2
        )
        result = calibrate_policies(predictions, policies, config)
        self.assertEqual(result.test_count, 6)
        self.assertAlmostEqual(result.adjusted_delta, 0.05 / 6)

    def test_earliest_feasible_policy_is_selected(self):
        predictions = make_predictions()
        policies = (
            Policy(name="full", full_sequence=True),
            Policy(name="early", pmax_min=0.8),
        )
        config = RiskCalibrationConfig(
            overall_risk=0.10, class_risk=0.10, label_count=2, candidate_size=2
        )
        result = calibrate_policies(predictions, policies, config)
        self.assertEqual(result.status, "CERTIFIED_EARLY")
        self.assertEqual(result.selected.policy.name, "early")

    def test_duplicate_calibration_units_are_rejected(self):
        source = make_predictions(samples=2)
        duplicated = PrefixPredictions(
            class_probabilities=source.class_probabilities,
            stop_probabilities=source.stop_probabilities,
            targets=source.targets,
            sample_ids=source.sample_ids,
            calibration_unit_ids=("same", "same"),
            timestamps=source.timestamps,
            valid_mask=source.valid_mask,
            sequence_lengths=source.sequence_lengths,
        )
        with self.assertRaisesRegex(ValueError, "independent and unique"):
            calibrate_policies(
                duplicated,
                (Policy(name="full", full_sequence=True),),
                RiskCalibrationConfig(label_count=2, candidate_size=1),
            )

    def test_full_sequence_is_safe_fallback_when_early_policy_fails(self):
        predictions = make_predictions()
        probabilities = predictions.class_probabilities.copy()
        probabilities[:, 0] = probabilities[:, 0, ::-1]
        mixed = PrefixPredictions(
            class_probabilities=probabilities,
            stop_probabilities=predictions.stop_probabilities,
            targets=predictions.targets,
            sample_ids=predictions.sample_ids,
            calibration_unit_ids=predictions.calibration_unit_ids,
            timestamps=predictions.timestamps,
            valid_mask=predictions.valid_mask,
            sequence_lengths=predictions.sequence_lengths,
        )
        result = calibrate_policies(
            mixed,
            (
                Policy(name="full", full_sequence=True),
                Policy(name="risky_early", pmax_min=0.8),
            ),
            RiskCalibrationConfig(
                overall_risk=0.10, class_risk=0.10, label_count=2, candidate_size=2
            ),
        )
        self.assertEqual(result.status, "CERTIFIED_FULL_SEQUENCE")
        self.assertTrue(result.selected.policy.full_sequence)

    def test_no_feasible_policy_returns_uncertified_full_sequence(self):
        predictions = make_predictions(samples=20)
        probabilities = predictions.class_probabilities.copy()
        probabilities[:, -1] = probabilities[:, -1, ::-1]
        risky = PrefixPredictions(
            class_probabilities=probabilities,
            stop_probabilities=predictions.stop_probabilities,
            targets=predictions.targets,
            sample_ids=predictions.sample_ids,
            calibration_unit_ids=predictions.calibration_unit_ids,
            timestamps=predictions.timestamps,
            valid_mask=predictions.valid_mask,
            sequence_lengths=predictions.sequence_lengths,
        )
        result = calibrate_policies(
            risky,
            (Policy(name="full", full_sequence=True),),
            RiskCalibrationConfig(
                overall_risk=0.05, class_risk=0.10, label_count=2, candidate_size=1
            ),
        )
        self.assertEqual(result.status, "NO_CERTIFIED_POLICY")
        self.assertTrue(result.selected.policy.full_sequence)

    def test_non_calibration_split_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "calibration split"):
            calibrate_policies(
                make_predictions(),
                (Policy(name="full", full_sequence=True),),
                RiskCalibrationConfig(label_count=2, candidate_size=1),
                split="test",
            )

    def test_candidate_count_must_match_config(self):
        with self.assertRaisesRegex(ValueError, "candidate_size"):
            calibrate_policies(
                make_predictions(),
                (Policy(name="full", full_sequence=True),),
                RiskCalibrationConfig(label_count=2, candidate_size=2),
            )

    def test_calibration_uses_explicit_sample_relative_progress(self):
        predictions = make_predictions()
        policies = (
            Policy(name="full", full_sequence=True),
            Policy(name="late", pmax_min=0.8, earliest_progress=0.8),
        )
        config = RiskCalibrationConfig(
            overall_risk=0.10, class_risk=0.10, label_count=2, candidate_size=2
        )
        progress = np.broadcast_to(
            np.array([0.4, 0.8, 1.0]), predictions.valid_mask.shape
        )
        result = calibrate_policies(
            predictions, policies, config, progress=progress
        )
        late = next(item for item in result.assessments if item.policy.name == "late")
        self.assertAlmostEqual(late.mean_normalized_stop, 2.0 / 3.0)

    def test_absent_declared_class_prevents_certification(self):
        source = make_predictions()
        probabilities = np.concatenate(
            [source.class_probabilities * 0.99, np.full((400, 3, 1), 0.01)], axis=2
        )
        predictions = PrefixPredictions(
            class_probabilities=probabilities,
            stop_probabilities=source.stop_probabilities,
            targets=source.targets,
            sample_ids=source.sample_ids,
            calibration_unit_ids=source.calibration_unit_ids,
            timestamps=source.timestamps,
            valid_mask=source.valid_mask,
            sequence_lengths=source.sequence_lengths,
        )
        result = calibrate_policies(
            predictions,
            (Policy(name="full", full_sequence=True),),
            RiskCalibrationConfig(label_count=3, candidate_size=1),
        )
        self.assertEqual(result.status, "NO_CERTIFIED_POLICY")
        self.assertEqual(result.assessments[0].class_risks[2].trials, 0)


if __name__ == "__main__":
    unittest.main()
