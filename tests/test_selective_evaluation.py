import unittest

import numpy as np

from rcecrop.selective_evaluation import evaluate_selective_policy


class SelectiveEvaluationTests(unittest.TestCase):
    def test_reports_automatic_and_deferred_outcomes_separately(self):
        probabilities = np.array([
            [[0.91, 0.09], [0.95, 0.05]],
            [[0.60, 0.40], [0.70, 0.30]],
            [[0.10, 0.90], [0.20, 0.80]],
        ])
        metrics, labels, stops = evaluate_selective_policy(
            probabilities, np.array([0, 0, 1]), 0.9
        )
        self.assertEqual(metrics.samples, 3)
        self.assertEqual(metrics.automatic_samples, 2)
        self.assertEqual(metrics.deferred_samples, 1)
        self.assertAlmostEqual(metrics.automatic_coverage, 2 / 3)
        self.assertAlmostEqual(metrics.automatic_accuracy, 1.0)
        self.assertEqual(metrics.stop_counts, (2, 0))
        np.testing.assert_array_equal(labels, [0, -1, 1])
        np.testing.assert_array_equal(stops, [0, -1, 0])


if __name__ == "__main__":
    unittest.main()
