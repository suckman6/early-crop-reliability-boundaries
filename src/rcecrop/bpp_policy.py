"""Finite observation-state policy family for the B++ development route."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json

import numpy as np

from .observation_state import ObservationState
from .policy import PolicyOutcome


@dataclass(frozen=True)
class ObservationPolicy:
    name: str
    group_pmax_min: tuple[float, ...]
    full_sequence: bool = False
    min_season_progress: float = 0.0
    min_quality_valid_observations: int = 1
    max_invalid_fraction: float = 1.0
    max_staleness_days: float = float("inf")
    stable_k: int = 1

    def __post_init__(self) -> None:
        if not self.name or not self.group_pmax_min:
            raise ValueError("policy name and group thresholds are required")
        if any(not 0.0 <= value <= 1.0 for value in self.group_pmax_min):
            raise ValueError("group confidence thresholds must lie in [0, 1]")
        if not 0.0 <= self.min_season_progress <= 1.0:
            raise ValueError("min_season_progress must lie in [0, 1]")
        if self.min_quality_valid_observations < 1 or self.stable_k < 1:
            raise ValueError("observation and stability counts must be positive")
        if not 0.0 <= self.max_invalid_fraction <= 1.0:
            raise ValueError("max_invalid_fraction must lie in [0, 1]")
        if self.max_staleness_days < 0.0:
            raise ValueError("max_staleness_days cannot be negative")

    def canonical_key(self) -> str:
        values = {key: value for key, value in asdict(self).items() if key != "name"}
        return json.dumps(values, sort_keys=True, separators=(",", ":"))


def execute_observation_policy(
    state: ObservationState, policy: ObservationPolicy
) -> PolicyOutcome:
    samples = state.available_mask.shape[0]
    labels = np.empty(samples, dtype=np.int64)
    stops = np.empty(samples, dtype=np.int64)
    fallback = np.zeros(samples, dtype=bool)
    group_count = len(policy.group_pmax_min)

    for sample in range(samples):
        valid = np.flatnonzero(state.available_mask[sample])
        chosen = int(valid[-1]) if policy.full_sequence else None
        if chosen is None:
            for position, time_index in enumerate(valid):
                group = int(state.predicted_group[sample, time_index])
                if not 0 <= group < group_count:
                    raise ValueError("predicted group lies outside policy thresholds")
                if (
                    state.confidence[sample, time_index]
                    < policy.group_pmax_min[group]
                ):
                    continue
                if (
                    state.season_progress[sample, time_index]
                    < policy.min_season_progress
                ):
                    continue
                if (
                    state.quality_valid_count[sample, time_index]
                    < policy.min_quality_valid_observations
                ):
                    continue
                if (
                    state.cumulative_invalid_fraction[sample, time_index]
                    > policy.max_invalid_fraction
                ):
                    continue
                if (
                    state.days_since_quality_valid[sample, time_index]
                    > policy.max_staleness_days
                ):
                    continue
                history = valid[: position + 1]
                predicted = state.predicted_class[sample, history]
                if predicted.size < policy.stable_k or not np.all(
                    predicted[-policy.stable_k :] == predicted[-1]
                ):
                    continue
                chosen = int(time_index)
                break
        if chosen is None:
            chosen = int(valid[-1])
            fallback[sample] = True
        stops[sample] = chosen
        labels[sample] = int(state.predicted_class[sample, chosen])
    return PolicyOutcome(labels=labels, stop_indices=stops, used_fallback=fallback)


def materialize_observation_candidates(size: int = 16) -> tuple[ObservationPolicy, ...]:
    """Return the prospectively bounded, deterministic Stage 8 family."""
    if not 2 <= size <= 16:
        raise ValueError("B++ candidate count must lie between 2 and 16")
    uniform = (1.0,) * 5
    candidates = [
        ObservationPolicy(
            name="full_sequence", group_pmax_min=uniform, full_sequence=True
        )
    ]
    for confidence in (0.65, 0.75, 0.85):
        for progress in (0.15, 0.30):
            for valid_count in (2, 3):
                candidates.append(
                    ObservationPolicy(
                        name=(
                            f"uniform_c{confidence:.2f}_p{progress:.2f}"
                            f"_q{valid_count}"
                        ),
                        group_pmax_min=(confidence,) * 5,
                        min_season_progress=progress,
                        min_quality_valid_observations=valid_count,
                        max_invalid_fraction=0.75,
                        max_staleness_days=90.0,
                        stable_k=2,
                    )
                )
    candidates.extend(
        (
            ObservationPolicy(
                name="group_aware_balanced",
                group_pmax_min=(0.75, 0.75, 0.80, 0.80, 0.78),
                min_season_progress=0.20,
                min_quality_valid_observations=2,
                max_invalid_fraction=0.75,
                max_staleness_days=75.0,
                stable_k=2,
            ),
            ObservationPolicy(
                name="group_aware_early",
                group_pmax_min=(0.68, 0.68, 0.75, 0.75, 0.72),
                min_season_progress=0.15,
                min_quality_valid_observations=2,
                max_invalid_fraction=0.80,
                max_staleness_days=90.0,
                stable_k=2,
            ),
            ObservationPolicy(
                name="group_aware_conservative",
                group_pmax_min=(0.82, 0.82, 0.88, 0.88, 0.85),
                min_season_progress=0.30,
                min_quality_valid_observations=3,
                max_invalid_fraction=0.60,
                max_staleness_days=60.0,
                stable_k=3,
            ),
        )
    )
    selected = tuple(candidates[:size])
    if len({candidate.canonical_key() for candidate in selected}) != len(selected):
        raise RuntimeError("B++ candidate family contains duplicate parameterizations")
    return selected
