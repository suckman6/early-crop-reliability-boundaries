import unittest

import numpy as np

from rcecrop.contracts import PrefixPredictions
from rcecrop.evaluation import evaluate_policy, valid_observation_progress
from rcecrop.policy import Policy


def variable_predictions() -> PrefixPredictions:
    probabilities = np.array(
        [
            [[0.8, 0.2], [0.9, 0.1], [0.9, 0.1], [0.9, 0.1]],
            [[0.2, 0.8], [0.2, 0.8], [0.1, 0.9], [0.1, 0.9]],
        ],
        dtype=np.float32,
    )
    valid = np.array([[True, True, False, False], [True, True, True, True]])
    return PrefixPredictions(
        class_probabilities=probabilities,
        stop_probabilities=np.ones((2, 4), dtype=np.float32),
        targets=np.array([0, 1], dtype=np.int64),
        sample_ids=("s0", "s1"),
        calibration_unit_ids=("u0", "u1"),
        timestamps=np.broadcast_to(np.arange(4), (2, 4)),
        valid_mask=valid,
        sequence_lengths=valid.sum(axis=1),
    )


class EvaluationTests(unittest.TestCase):
    def test_progress_is_relative_to_each_trajectory(self):
        observed = valid_observation_progress(variable_predictions())
        np.testing.assert_allclose(observed[0], [0.5, 1.0, 0.0, 0.0])
        np.testing.assert_allclose(observed[1], [0.25, 0.5, 0.75, 1.0])

    def test_metrics_for_correct_halfway_stops(self):
        predictions = variable_predictions()
        metrics = evaluate_policy(
            predictions,
            Policy(name="halfway", pmax_min=0.0, earliest_progress=0.5),
        )
        self.assertEqual(metrics.samples, 2)
        self.assertEqual(metrics.accuracy, 1.0)
        self.assertEqual(metrics.macro_f1, 1.0)
        self.assertEqual(metrics.mean_normalized_stop, 0.5)
        self.assertEqual(metrics.earliness, 0.5)
        self.assertEqual(metrics.fallback_rate, 0.0)


if __name__ == "__main__":
    unittest.main()
