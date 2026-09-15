import unittest

import numpy as np

from rcecrop.contracts import PrefixPredictions
from rcecrop.policy import Policy, _sobol_point, execute_policy, materialize_candidate_set


def prediction_fixture(probabilities, valid_mask=None):
    probabilities = np.asarray(probabilities, dtype=np.float32)
    samples, time_steps, _ = probabilities.shape
    if valid_mask is None:
        valid_mask = np.ones((samples, time_steps), dtype=bool)
    return PrefixPredictions(
        class_probabilities=probabilities,
        stop_probabilities=np.full((samples, time_steps), 0.6, dtype=np.float32),
        targets=np.zeros(samples, dtype=np.int64),
        sample_ids=tuple(f"s{index}" for index in range(samples)),
        calibration_unit_ids=tuple(f"u{index}" for index in range(samples)),
        timestamps=np.broadcast_to(np.arange(time_steps), (samples, time_steps)),
        valid_mask=valid_mask,
        sequence_lengths=valid_mask.sum(axis=1),
    )


class PolicyTests(unittest.TestCase):
    def test_probability_tie_uses_lowest_class(self):
        predictions = prediction_fixture([[[0.5, 0.5], [0.2, 0.8]]])
        outcome = execute_policy(predictions, Policy(name="tie", pmax_min=0.5))
        self.assertEqual(outcome.labels[0], 0)
        self.assertEqual(outcome.stop_indices[0], 0)

    def test_unsatisfied_policy_falls_back_to_last_valid_time(self):
        predictions = prediction_fixture(
            [[[0.6, 0.4], [0.7, 0.3], [0.8, 0.2], [0.9, 0.1]]],
            valid_mask=np.array([[True, False, True, False]]),
        )
        outcome = execute_policy(predictions, Policy(name="strict", pmax_min=0.99))
        self.assertEqual(outcome.stop_indices[0], 2)
        self.assertTrue(outcome.used_fallback[0])

    def test_full_sequence_is_planned_not_fallback(self):
        predictions = prediction_fixture([[[0.6, 0.4], [0.9, 0.1]]])
        outcome = execute_policy(
            predictions, Policy(name="full", full_sequence=True)
        )
        self.assertEqual(outcome.stop_indices[0], 1)
        self.assertFalse(outcome.used_fallback[0])

    def test_stability_counts_only_valid_observations(self):
        predictions = prediction_fixture(
            [[[0.8, 0.2], [0.1, 0.9], [0.7, 0.3], [0.9, 0.1]]],
            valid_mask=np.array([[True, False, True, True]]),
        )
        outcome = execute_policy(
            predictions, Policy(name="stable", pmax_min=0.7, stable_k=3)
        )
        self.assertEqual(outcome.stop_indices[0], 3)
        self.assertFalse(outcome.used_fallback[0])

    def test_combined_observation_and_uncertainty_gates(self):
        predictions = prediction_fixture(
            [[[0.70, 0.30], [0.75, 0.25], [0.90, 0.10]]]
        )
        outcome = execute_policy(
            predictions,
            Policy(
                name="combined",
                pmax_min=0.85,
                margin_min=0.70,
                entropy_max=0.50,
                entropy_drop_min=0.05,
                stable_k=3,
                elects_stop_min=0.50,
                min_valid_obs=3,
                earliest_progress=0.50,
            ),
        )
        self.assertEqual(outcome.stop_indices[0], 2)
        self.assertFalse(outcome.used_fallback[0])

    def test_elects_stop_gate_can_force_full_sequence_fallback(self):
        predictions = prediction_fixture(
            [[[0.90, 0.10], [0.90, 0.10], [0.90, 0.10]]]
        )
        outcome = execute_policy(
            predictions,
            Policy(name="stop_gate", pmax_min=0.8, elects_stop_min=0.7),
        )
        self.assertEqual(outcome.stop_indices[0], 2)
        self.assertTrue(outcome.used_fallback[0])

    def test_candidate_set_is_deterministic_and_unique(self):
        first = materialize_candidate_set(32)
        second = materialize_candidate_set(32)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 32)
        self.assertEqual(len({policy.canonical_key() for policy in first}), 32)
        self.assertTrue(first[0].full_sequence)

    def test_sobol_first_dimension_reference_values(self):
        observed = [_sobol_point(index)[0] for index in range(8)]
        expected = [0.0, 0.5, 0.75, 0.25, 0.375, 0.875, 0.625, 0.125]
        np.testing.assert_allclose(observed, expected)

    def test_progress_outside_unit_interval_is_rejected(self):
        predictions = prediction_fixture([[[0.8, 0.2]]])
        with self.assertRaisesRegex(ValueError, "lie in"):
            execute_policy(
                predictions,
                Policy(name="progress"),
                progress=np.array([[1.1]]),
            )


if __name__ == "__main__":
    unittest.main()
