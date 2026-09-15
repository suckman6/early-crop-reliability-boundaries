import numpy as np

from rcecrop.contracts import PrefixPredictions


def make_predictions(samples=400, time_steps=3, classes=2):
    targets = np.arange(samples, dtype=np.int64) % classes
    probabilities = np.full((samples, time_steps, classes), 0.1 / (classes - 1))
    for sample, target in enumerate(targets):
        probabilities[sample, :, target] = 0.9
    stopping = np.full((samples, time_steps), 0.5, dtype=np.float32)
    valid = np.ones((samples, time_steps), dtype=bool)
    return PrefixPredictions(
        class_probabilities=probabilities,
        stop_probabilities=stopping,
        targets=targets,
        sample_ids=tuple(f"sample-{index}" for index in range(samples)),
        calibration_unit_ids=tuple(f"unit-{index}" for index in range(samples)),
        timestamps=np.broadcast_to(np.arange(time_steps), (samples, time_steps)),
        valid_mask=valid,
        sequence_lengths=np.full(samples, time_steps, dtype=np.int32),
    )
