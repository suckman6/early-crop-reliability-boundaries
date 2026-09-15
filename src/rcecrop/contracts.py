"""Array contracts shared by data adapters, exporters, and calibration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


def _string_tuple(values: Sequence[str], name: str, samples: int) -> tuple[str, ...]:
    result = tuple(str(value) for value in values)
    if len(result) != samples or any(not value for value in result):
        raise ValueError(f"{name} must contain one non-empty value per sample")
    return result


def _validate_metadata(
    sample_ids: Sequence[str],
    calibration_unit_ids: Sequence[str],
    targets: np.ndarray,
    timestamps: np.ndarray,
    valid_mask: np.ndarray,
    sequence_lengths: np.ndarray,
    samples: int,
    time_steps: int,
) -> tuple[tuple[str, ...], tuple[str, ...], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    sample_ids = _string_tuple(sample_ids, "sample_ids", samples)
    calibration_unit_ids = _string_tuple(
        calibration_unit_ids, "calibration_unit_ids", samples
    )
    if len(set(sample_ids)) != samples:
        raise ValueError("sample_ids must be unique")

    targets = np.asarray(targets)
    timestamps = np.asarray(timestamps)
    valid_mask = np.asarray(valid_mask)
    sequence_lengths = np.asarray(sequence_lengths)
    if targets.shape != (samples,) or not np.issubdtype(targets.dtype, np.integer):
        raise ValueError("targets must be an integer array with shape (samples,)")
    if timestamps.shape != (samples, time_steps):
        raise ValueError("timestamps must have shape (samples, time)")
    if valid_mask.shape != (samples, time_steps) or valid_mask.dtype != np.bool_:
        raise ValueError("valid_mask must be a boolean array with shape (samples, time)")
    if sequence_lengths.shape != (samples,) or not np.issubdtype(
        sequence_lengths.dtype, np.integer
    ):
        raise ValueError("sequence_lengths must be an integer array with shape (samples,)")
    observed = valid_mask.sum(axis=1)
    if np.any(observed == 0):
        raise ValueError("every trajectory must contain at least one valid observation")
    if not np.array_equal(observed, sequence_lengths):
        raise ValueError("sequence_lengths must equal valid observation counts")
    return (
        sample_ids,
        calibration_unit_ids,
        targets.astype(np.int64, copy=False),
        timestamps.astype(np.int32, copy=False),
        valid_mask,
        sequence_lengths.astype(np.int32, copy=False),
    )


@dataclass(frozen=True)
class TrajectoryBatch:
    features: np.ndarray
    targets: np.ndarray
    sample_ids: Sequence[str]
    calibration_unit_ids: Sequence[str]
    timestamps: np.ndarray
    valid_mask: np.ndarray
    sequence_lengths: np.ndarray

    def __post_init__(self) -> None:
        features = np.asarray(self.features)
        if features.ndim != 3 or features.shape[0] == 0 or features.shape[1] == 0:
            raise ValueError("features must have shape (samples, time, dimensions)")
        if not np.issubdtype(features.dtype, np.floating) or not np.isfinite(features).all():
            raise ValueError("features must be a finite floating-point array")
        metadata = _validate_metadata(
            self.sample_ids,
            self.calibration_unit_ids,
            self.targets,
            self.timestamps,
            self.valid_mask,
            self.sequence_lengths,
            features.shape[0],
            features.shape[1],
        )
        object.__setattr__(self, "features", features.astype(np.float32, copy=False))
        for name, value in zip(
            ("sample_ids", "calibration_unit_ids", "targets", "timestamps", "valid_mask", "sequence_lengths"),
            metadata,
        ):
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class PrefixPredictions:
    class_probabilities: np.ndarray
    stop_probabilities: np.ndarray
    targets: np.ndarray
    sample_ids: Sequence[str]
    calibration_unit_ids: Sequence[str]
    timestamps: np.ndarray
    valid_mask: np.ndarray
    sequence_lengths: np.ndarray

    def __post_init__(self) -> None:
        probabilities = np.asarray(self.class_probabilities)
        stopping = np.asarray(self.stop_probabilities)
        if probabilities.ndim != 3 or probabilities.shape[2] < 2:
            raise ValueError("class_probabilities must have shape (samples, time, classes>=2)")
        samples, time_steps, classes = probabilities.shape
        if samples == 0 or time_steps == 0:
            raise ValueError("prefix predictions cannot have empty sample or time axes")
        if not np.isfinite(probabilities).all() or np.any(
            (probabilities < 0.0) | (probabilities > 1.0)
        ):
            raise ValueError("class probabilities must be finite values in [0, 1]")
        if not np.allclose(probabilities.sum(axis=2), 1.0, atol=1e-5):
            raise ValueError("class probabilities must sum to one")
        if stopping.shape != (samples, time_steps) or not np.isfinite(stopping).all():
            raise ValueError("stop_probabilities must have shape (samples, time)")
        if np.any((stopping < 0.0) | (stopping > 1.0)):
            raise ValueError("stop probabilities must lie in [0, 1]")
        metadata = _validate_metadata(
            self.sample_ids,
            self.calibration_unit_ids,
            self.targets,
            self.timestamps,
            self.valid_mask,
            self.sequence_lengths,
            samples,
            time_steps,
        )
        targets = metadata[2]
        if np.any((targets < 0) | (targets >= classes)):
            raise ValueError("targets contain an invalid class index")
        object.__setattr__(
            self, "class_probabilities", probabilities.astype(np.float32, copy=False)
        )
        object.__setattr__(self, "stop_probabilities", stopping.astype(np.float32, copy=False))
        for name, value in zip(
            ("sample_ids", "calibration_unit_ids", "targets", "timestamps", "valid_mask", "sequence_lengths"),
            metadata,
        ):
            object.__setattr__(self, name, value)

    @property
    def class_count(self) -> int:
        return int(self.class_probabilities.shape[2])
