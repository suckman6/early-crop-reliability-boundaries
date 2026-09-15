import unittest

import numpy as np

from rcecrop.contracts import PrefixPredictions, TrajectoryBatch
from helpers import make_predictions


class ContractTests(unittest.TestCase):
    def test_valid_prefix_contract(self):
        predictions = make_predictions(samples=3)
        self.assertEqual(predictions.class_count, 2)
        self.assertEqual(predictions.class_probabilities.dtype, np.float32)

    def test_empty_valid_observations_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one valid"):
            TrajectoryBatch(
                features=np.zeros((1, 2, 3), dtype=np.float32),
                targets=np.array([0]),
                sample_ids=("a",),
                calibration_unit_ids=("a",),
                timestamps=np.zeros((1, 2), dtype=np.int32),
                valid_mask=np.zeros((1, 2), dtype=bool),
                sequence_lengths=np.array([0]),
            )

    def test_sequence_length_must_match_mask(self):
        predictions = make_predictions(samples=1)
        with self.assertRaisesRegex(ValueError, "equal valid"):
            PrefixPredictions(
                class_probabilities=predictions.class_probabilities,
                stop_probabilities=predictions.stop_probabilities,
                targets=predictions.targets,
                sample_ids=predictions.sample_ids,
                calibration_unit_ids=predictions.calibration_unit_ids,
                timestamps=predictions.timestamps,
                valid_mask=predictions.valid_mask,
                sequence_lengths=np.array([2]),
            )

    def test_probabilities_must_sum_to_one(self):
        predictions = make_predictions(samples=1)
        with self.assertRaisesRegex(ValueError, "sum to one"):
            PrefixPredictions(
                class_probabilities=np.full_like(predictions.class_probabilities, 0.8),
                stop_probabilities=predictions.stop_probabilities,
                targets=predictions.targets,
                sample_ids=predictions.sample_ids,
                calibration_unit_ids=predictions.calibration_unit_ids,
                timestamps=predictions.timestamps,
                valid_mask=predictions.valid_mask,
                sequence_lengths=predictions.sequence_lengths,
            )


if __name__ == "__main__":
    unittest.main()
