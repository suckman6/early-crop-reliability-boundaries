import unittest

import numpy as np

from rcecrop.matched_selective import (
    calibrate_score_family,
    release_from_score,
    score_values,
    select_earliest_certified,
    summarize_release,
)


class MatchedSelectiveTests(unittest.TestCase):
    def test_margin_and_entropy_scores_are_bounded(self):
        probabilities = np.array(
            [[[[0.7, 0.2, 0.1], [0.2, 0.5, 0.3]]]], dtype=float
        ).reshape(1, 2, 3)
        for family in ("pmax", "margin", "entropy_confidence"):
            scores = score_values(probabilities, family)
            self.assertEqual(scores.shape, (1, 2))
            self.assertTrue(np.all(scores >= 0.0))
            self.assertTrue(np.all(scores <= 1.0))

    def test_first_crossing_uses_score_family(self):
        probabilities = np.array(
            [
                [[0.55, 0.30, 0.15], [0.80, 0.10, 0.10]],
                [[0.40, 0.35, 0.25], [0.45, 0.40, 0.15]],
            ],
            dtype=float,
        )
        labels, stops = release_from_score(probabilities, "margin", 0.25)
        np.testing.assert_array_equal(labels, [0, -1])
        np.testing.assert_array_equal(stops, [0, -1])

    def test_calibration_uses_simultaneous_contract_and_selects(self):
        probabilities = np.tile(
            np.array([[[0.95, 0.03, 0.02], [0.96, 0.02, 0.02]]]),
            (200, 1, 1),
        )
        targets = np.zeros(200, dtype=np.int64)
        assessments = calibrate_score_family(
            probabilities,
            targets,
            "pmax",
            (0.8, 0.9),
            overall_risk_target=0.1,
            minimum_coverage=0.2,
            confidence=0.95,
        )
        selected = select_earliest_certified(assessments)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.threshold, 0.8)
        self.assertEqual(selected.accepted, 200)

    def test_summary_reports_deferred_samples(self):
        probabilities = np.array(
            [
                [[0.9, 0.1], [0.95, 0.05]],
                [[0.6, 0.4], [0.7, 0.3]],
            ],
            dtype=float,
        )
        targets = np.array([0, 1], dtype=np.int64)
        summary = summarize_release(probabilities, targets, "pmax", 0.8)
        self.assertEqual(summary["automatic_samples"], 1)
        self.assertEqual(summary["deferred_samples"], 1)


if __name__ == "__main__":
    unittest.main()
