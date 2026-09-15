import unittest

import numpy as np

from rcecrop.bpp_policy import (
    ObservationPolicy,
    execute_observation_policy,
    materialize_observation_candidates,
)
from rcecrop.contracts import PrefixPredictions
from rcecrop.observation_state import build_observation_state


def _predictions(probabilities, timestamps):
    probabilities = np.asarray(probabilities, dtype=np.float32)
    timestamps = np.asarray(timestamps, dtype=np.int32)
    samples, time_steps, _ = probabilities.shape
    valid = np.ones((samples, time_steps), dtype=bool)
    return PrefixPredictions(
        class_probabilities=probabilities,
        stop_probabilities=np.zeros((samples, time_steps), dtype=np.float32),
        targets=np.zeros(samples, dtype=np.int64),
        sample_ids=tuple(f"s{index}" for index in range(samples)),
        calibration_unit_ids=tuple(f"u{index}" for index in range(samples)),
        timestamps=timestamps,
        valid_mask=valid,
        sequence_lengths=valid.sum(axis=1),
    )


class ObservationStatePolicyTests(unittest.TestCase):
    def test_state_is_invariant_to_future_values_and_trajectory_end(self):
        prefix = np.array([[[0.7, 0.3], [0.8, 0.2]]], dtype=np.float32)
        first = _predictions(
            np.concatenate([prefix, [[[0.9, 0.1], [0.95, 0.05]]]], axis=1),
            [[10, 20, 30, 40]],
        )
        second = _predictions(
            np.concatenate([prefix, [[[0.1, 0.9], [0.2, 0.8]]]], axis=1),
            [[10, 20, 100, 200]],
        )
        quality = np.array([[True, False, True, True]])
        mapping = np.array([0, 1])
        state_a = build_observation_state(first, quality, mapping)
        state_b = build_observation_state(second, quality, mapping)
        for name in (
            "season_progress",
            "acquired_count",
            "quality_valid_count",
            "days_since_quality_valid",
            "cumulative_invalid_fraction",
            "confidence",
            "predicted_group",
        ):
            np.testing.assert_array_equal(
                getattr(state_a, name)[:, :2], getattr(state_b, name)[:, :2]
            )

    def test_calendar_progress_does_not_divide_by_trajectory_length(self):
        predictions = _predictions([[[0.8, 0.2], [0.9, 0.1]]], [[0, 182]])
        state = build_observation_state(
            predictions, np.ones((1, 2), dtype=bool), np.array([0, 1])
        )
        self.assertAlmostEqual(state.season_progress[0, 1], 0.5)

    def test_policy_uses_quality_count_and_predicted_group_threshold(self):
        predictions = _predictions(
            [[[0.80, 0.20], [0.90, 0.10], [0.95, 0.05]]], [[10, 20, 30]]
        )
        state = build_observation_state(
            predictions,
            np.array([[False, True, True]]),
            np.array([0, 1]),
        )
        policy = ObservationPolicy(
            name="test",
            group_pmax_min=(0.85, 0.70),
            min_quality_valid_observations=1,
        )
        result = execute_observation_policy(state, policy)
        self.assertEqual(result.stop_indices[0], 1)
        self.assertFalse(result.used_fallback[0])

    def test_unsatisfied_state_policy_falls_back_to_last_acquisition(self):
        predictions = _predictions([[[0.8, 0.2], [0.9, 0.1]]], [[10, 20]])
        state = build_observation_state(
            predictions, np.zeros((1, 2), dtype=bool), np.array([0, 1])
        )
        policy = ObservationPolicy(
            name="strict",
            group_pmax_min=(0.99, 0.99),
            min_quality_valid_observations=2,
        )
        result = execute_observation_policy(state, policy)
        self.assertEqual(result.stop_indices[0], 1)
        self.assertTrue(result.used_fallback[0])

    def test_candidate_family_is_bounded_deterministic_and_unique(self):
        first = materialize_observation_candidates()
        second = materialize_observation_candidates()
        self.assertEqual(first, second)
        self.assertEqual(len(first), 16)
        self.assertEqual(len({item.canonical_key() for item in first}), 16)
        self.assertTrue(first[0].full_sequence)


if __name__ == "__main__":
    unittest.main()
