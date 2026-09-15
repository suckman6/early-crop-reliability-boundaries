"""Deterministic stopping policies and finite candidate materialization."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math

import numpy as np

from .contracts import PrefixPredictions


@dataclass(frozen=True)
class Policy:
    name: str
    full_sequence: bool = False
    pmax_min: float | None = None
    margin_min: float | None = None
    entropy_max: float | None = None
    entropy_drop_min: float | None = None
    stable_k: int = 1
    elects_stop_min: float | None = None
    min_valid_obs: int = 1
    earliest_progress: float = 0.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("policy name cannot be empty")
        for name in ("pmax_min", "margin_min", "entropy_max", "elects_stop_min"):
            value = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.entropy_drop_min is not None and self.entropy_drop_min < 0.0:
            raise ValueError("entropy_drop_min cannot be negative")
        if self.stable_k < 1 or self.min_valid_obs < 1:
            raise ValueError("stable_k and min_valid_obs must be positive")
        if not 0.0 <= self.earliest_progress <= 1.0:
            raise ValueError("earliest_progress must lie in [0, 1]")

    def canonical_key(self) -> str:
        parameters = {key: value for key, value in asdict(self).items() if key != "name"}
        return json.dumps(parameters, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class PolicyOutcome:
    labels: np.ndarray
    stop_indices: np.ndarray
    used_fallback: np.ndarray


def _normalized_entropy(probabilities: np.ndarray) -> float:
    positive = probabilities > 0.0
    entropy = -float(np.sum(probabilities[positive] * np.log(probabilities[positive])))
    return entropy / math.log(probabilities.size)


def execute_policy(
    predictions: PrefixPredictions,
    policy: Policy,
    progress: np.ndarray | None = None,
) -> PolicyOutcome:
    probabilities = predictions.class_probabilities
    if progress is None:
        progress = np.broadcast_to(
            (np.arange(probabilities.shape[1], dtype=float) + 1.0) / probabilities.shape[1],
            probabilities.shape[:2],
        )
    else:
        progress = np.asarray(progress, dtype=float)
        if progress.shape != probabilities.shape[:2] or not np.isfinite(progress).all():
            raise ValueError("progress must be finite with shape (samples, time)")
        if np.any((progress < 0.0) | (progress > 1.0)):
            raise ValueError("progress must lie in [0, 1]")

    labels = np.empty(probabilities.shape[0], dtype=np.int64)
    stop_indices = np.empty(probabilities.shape[0], dtype=np.int64)
    fallback = np.zeros(probabilities.shape[0], dtype=bool)

    for sample in range(probabilities.shape[0]):
        valid = np.flatnonzero(predictions.valid_mask[sample])
        chosen: int | None = int(valid[-1]) if policy.full_sequence else None
        if chosen is None:
            for position, time_index in enumerate(valid):
                history = valid[: position + 1]
                current = probabilities[sample, time_index]
                order = np.sort(current)
                predicted_history = probabilities[sample, history].argmax(axis=1)
                if position + 1 < policy.min_valid_obs:
                    continue
                if progress[sample, time_index] < policy.earliest_progress:
                    continue
                if policy.pmax_min is not None and current.max() < policy.pmax_min:
                    continue
                if policy.margin_min is not None and order[-1] - order[-2] < policy.margin_min:
                    continue
                entropy = _normalized_entropy(current)
                if policy.entropy_max is not None and entropy > policy.entropy_max:
                    continue
                if predicted_history.size < policy.stable_k or not np.all(
                    predicted_history[-policy.stable_k :] == predicted_history[-1]
                ):
                    continue
                if policy.entropy_drop_min is not None:
                    if history.size < 3:
                        continue
                    previous = _normalized_entropy(probabilities[sample, history[-3]])
                    entropy_drop = (previous - entropy) / 2.0
                    if entropy_drop < policy.entropy_drop_min:
                        continue
                if (
                    policy.elects_stop_min is not None
                    and predictions.stop_probabilities[sample, time_index]
                    < policy.elects_stop_min
                ):
                    continue
                chosen = int(time_index)
                break
        if chosen is None:
            chosen = int(valid[-1])
            fallback[sample] = True
        stop_indices[sample] = chosen
        labels[sample] = int(np.argmax(probabilities[sample, chosen]))

    return PolicyOutcome(labels=labels, stop_indices=stop_indices, used_fallback=fallback)


_SOBOL_PARAMETERS = (
    (0, 0, ()),
    (1, 0, (1,)),
    (2, 1, (1, 3)),
    (3, 1, (1, 3, 1)),
    (3, 2, (1, 1, 1)),
    (4, 1, (1, 3, 5, 13)),
    (4, 4, (1, 1, 5, 5)),
    (5, 2, (1, 3, 3, 9, 7)),
)


def _sobol_point(index: int, dimensions: int = 8, bits: int = 32) -> np.ndarray:
    if index < 0 or not 1 <= dimensions <= len(_SOBOL_PARAMETERS):
        raise ValueError("unsupported Sobol index or dimensionality")
    directions = np.zeros((dimensions, bits), dtype=np.uint32)
    directions[0] = np.array([1 << (bits - j - 1) for j in range(bits)], dtype=np.uint32)
    for dimension in range(1, dimensions):
        degree, coefficient, initial = _SOBOL_PARAMETERS[dimension]
        for j in range(degree):
            directions[dimension, j] = initial[j] << (bits - j - 1)
        for j in range(degree, bits):
            value = directions[dimension, j - degree] ^ (
                directions[dimension, j - degree] >> degree
            )
            for k in range(1, degree):
                if (coefficient >> (degree - 1 - k)) & 1:
                    value ^= directions[dimension, j - k]
            directions[dimension, j] = value
    gray = index ^ (index >> 1)
    values = np.zeros(dimensions, dtype=np.uint32)
    bit = 0
    while gray:
        if gray & 1:
            values ^= directions[:, bit]
        gray >>= 1
        bit += 1
    return values.astype(np.float64) / float(1 << bits)


def materialize_candidate_set(size: int = 32) -> tuple[Policy, ...]:
    if size < 8:
        raise ValueError("candidate set must contain at least eight policies")
    policies = [Policy(name="full_sequence", full_sequence=True)]
    for threshold in (0.50, 0.60, 0.70, 0.80, 0.90, 0.95):
        policies.append(Policy(name=f"pmax_{threshold:.2f}", pmax_min=threshold))
    policies.append(
        Policy(name="observation_anchor", pmax_min=0.80, stable_k=3, min_valid_obs=3)
    )

    grids = (
        (0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95),
        (None, 0.05, 0.10, 0.20, 0.30),
        (None, 0.50, 0.65, 0.80, 0.95),
        (None, 0.00, 0.01, 0.03),
        (1, 2, 3, 4),
        (None, 0.30, 0.50, 0.70),
        (1, 2, 3, 5),
        (0.00, 0.10, 0.20, 0.30),
    )
    index = 1
    while len(policies) < size:
        point = _sobol_point(index)
        values = [grid[min(int(value * len(grid)), len(grid) - 1)] for grid, value in zip(grids, point)]
        policy = Policy(
            name=f"sobol_{index:04d}",
            pmax_min=values[0],
            margin_min=values[1],
            entropy_max=values[2],
            entropy_drop_min=values[3],
            stable_k=values[4],
            elects_stop_min=values[5],
            min_valid_obs=values[6],
            earliest_progress=values[7],
        )
        parameter_key = json.dumps(
            {key: value for key, value in asdict(policy).items() if key != "name"},
            sort_keys=True,
        )
        existing = {
            json.dumps(
                {key: value for key, value in asdict(item).items() if key != "name"},
                sort_keys=True,
            )
            for item in policies
        }
        if parameter_key not in existing:
            policies.append(policy)
        index += 1
    return tuple(policies)
