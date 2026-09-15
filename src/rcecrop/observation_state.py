"""Prefix-only observation state for irregular satellite trajectories."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .contracts import PrefixPredictions


@dataclass(frozen=True)
class ObservationState:
    season_progress: np.ndarray
    acquired_count: np.ndarray
    quality_valid_count: np.ndarray
    days_since_quality_valid: np.ndarray
    cumulative_invalid_fraction: np.ndarray
    confidence: np.ndarray
    predicted_class: np.ndarray
    predicted_group: np.ndarray
    available_mask: np.ndarray
    quality_valid_mask: np.ndarray

    def __post_init__(self) -> None:
        available = np.asarray(self.available_mask)
        quality = np.asarray(self.quality_valid_mask)
        shape = available.shape
        if len(shape) != 2:
            raise ValueError("observation-state arrays must have shape (samples, time)")
        for name in (
            "season_progress",
            "acquired_count",
            "quality_valid_count",
            "days_since_quality_valid",
            "cumulative_invalid_fraction",
            "confidence",
            "predicted_class",
            "predicted_group",
            "quality_valid_mask",
        ):
            if np.asarray(getattr(self, name)).shape != shape:
                raise ValueError(f"{name} must match the observation-state shape")
        if available.dtype != np.bool_ or quality.dtype != np.bool_:
            raise ValueError("observation-state masks must be boolean")
        if np.any(available.sum(axis=1) == 0) or np.any(quality & ~available):
            raise ValueError("each state requires an available prefix and valid quality mask")
        for name in (
            "season_progress",
            "days_since_quality_valid",
            "cumulative_invalid_fraction",
            "confidence",
        ):
            values = np.asarray(getattr(self, name))
            if not np.isfinite(values[available]).all():
                raise ValueError(f"{name} must be finite at every available prefix")
        if np.any(
            (self.season_progress[available] < 0.0)
            | (self.season_progress[available] > 1.0)
            | (self.cumulative_invalid_fraction[available] < 0.0)
            | (self.cumulative_invalid_fraction[available] > 1.0)
            | (self.confidence[available] < 0.0)
            | (self.confidence[available] > 1.0)
        ):
            raise ValueError("progress, invalid fraction, and confidence must lie in [0, 1]")
        if np.any(self.predicted_class[available] < 0) or np.any(
            self.predicted_group[available] < 0
        ):
            raise ValueError("available prefixes require class and group predictions")


def build_observation_state(
    predictions: PrefixPredictions,
    quality_valid_mask: np.ndarray,
    class_to_group: np.ndarray,
    season_days: int = 365,
) -> ObservationState:
    """Build state at each prefix without using future observations or length."""
    quality_valid_mask = np.asarray(quality_valid_mask)
    class_to_group = np.asarray(class_to_group)
    available = predictions.valid_mask
    shape = available.shape
    if quality_valid_mask.shape != shape or quality_valid_mask.dtype != np.bool_:
        raise ValueError("quality_valid_mask must be boolean with shape (samples, time)")
    if np.any(quality_valid_mask & ~available):
        raise ValueError("quality-valid observations must also be available")
    if class_to_group.shape != (predictions.class_count,) or np.any(class_to_group < 0):
        raise ValueError("class_to_group must map every class to a non-negative group")
    if season_days < 2:
        raise ValueError("season_days must be at least two")

    season_progress = np.zeros(shape, dtype=np.float64)
    acquired_count = np.zeros(shape, dtype=np.int32)
    quality_count = np.zeros(shape, dtype=np.int32)
    staleness = np.zeros(shape, dtype=np.float64)
    invalid_fraction = np.zeros(shape, dtype=np.float64)
    confidence = np.zeros(shape, dtype=np.float64)
    predicted_class = np.full(shape, -1, dtype=np.int64)
    predicted_group = np.full(shape, -1, dtype=np.int64)

    for sample in range(shape[0]):
        valid = np.flatnonzero(available[sample])
        times = predictions.timestamps[sample, valid].astype(np.int64)
        if np.any((times < 0) | (times >= season_days)) or np.any(np.diff(times) <= 0):
            raise ValueError("valid timestamps must be strictly increasing within the season")
        last_quality_time = 0
        quality_seen = 0
        for rank, time_index in enumerate(valid, start=1):
            time = int(predictions.timestamps[sample, time_index])
            if quality_valid_mask[sample, time_index]:
                quality_seen += 1
                last_quality_time = time
            current = predictions.class_probabilities[sample, time_index]
            current_class = int(np.argmax(current))
            season_progress[sample, time_index] = time / (season_days - 1)
            acquired_count[sample, time_index] = rank
            quality_count[sample, time_index] = quality_seen
            staleness[sample, time_index] = time - last_quality_time
            invalid_fraction[sample, time_index] = (rank - quality_seen) / rank
            confidence[sample, time_index] = float(current.max())
            predicted_class[sample, time_index] = current_class
            predicted_group[sample, time_index] = int(class_to_group[current_class])

    return ObservationState(
        season_progress=season_progress,
        acquired_count=acquired_count,
        quality_valid_count=quality_count,
        days_since_quality_valid=staleness,
        cumulative_invalid_fraction=invalid_fraction,
        confidence=confidence,
        predicted_class=predicted_class,
        predicted_group=predicted_group,
        available_mask=available.copy(),
        quality_valid_mask=quality_valid_mask.copy(),
    )
