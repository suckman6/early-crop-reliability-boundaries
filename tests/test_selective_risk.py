import json
import unittest
from dataclasses import asdict

import numpy as np

from rcecrop.selective_risk import calibrate_selective_thresholds, earliest_selective_predictions


class SelectiveRiskTests(unittest.TestCase):
    def test_stops_at_the_first_eligible_date_and_defers_the_rest(self):
        probabilities = np.array([
            [[0.6, 0.4], [0.91, 0.09], [0.99, 0.01]],
            [[0.5, 0.5], [0.7, 0.3], [0.8, 0.2]],
        ])
        labels, stops = earliest_selective_predictions(probabilities, 0.9)
        np.testing.assert_array_equal(labels, [0, -1])
        np.testing.assert_array_equal(stops, [1, -1])

    def test_candidate_selection_uses_risk_and_coverage_certificates(self):
        targets = np.zeros(200, dtype=np.int64)
        probabilities = np.zeros((200, 2, 2), dtype=float)
        probabilities[:, :, 0] = 0.99
        probabilities[:, :, 1] = 0.01
        assessments = calibrate_selective_thresholds(
            probabilities, targets, (0.8, 0.95), 0.1, 0.2, 0.95
        )
        self.assertTrue(all(item.certified for item in assessments))
        self.assertEqual(assessments[0].accepted, 200)
        self.assertEqual(assessments[0].errors, 0)

    def test_low_coverage_candidate_is_not_certified(self):
        targets = np.zeros(20, dtype=np.int64)
        probabilities = np.full((20, 2, 2), 0.5)
        probabilities[0, 0] = [0.99, 0.01]
        assessment = calibrate_selective_thresholds(
            probabilities, targets, (0.9,), 0.1, 0.2, 0.95
        )[0]
        self.assertFalse(assessment.certified)

    def test_assessments_are_json_serializable(self):
        targets = np.zeros(200, dtype=np.int64)
        probabilities = np.zeros((200, 2, 2), dtype=float)
        probabilities[:, :, 0] = 0.99
        probabilities[:, :, 1] = 0.01
        assessments = calibrate_selective_thresholds(
            probabilities, targets, (0.8, 0.95), 0.1, 0.2, 0.95
        )
        json.dumps([asdict(item) for item in assessments])


if __name__ == "__main__":
    unittest.main()
