"""Split-agnostic evaluation of a frozen stopping policy."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .contracts import PrefixPredictions
from .policy import Policy, execute_policy


def valid_observation_progress(predictions: PrefixPredictions) -> np.ndarray:
    """Return each valid observation's one-based rank divided by trajectory length."""
    ranks = np.cumsum(predictions.valid_mask, axis=1, dtype=np.int32)
    progress = ranks / predictions.sequence_lengths[:, None]
    return np.where(predictions.valid_mask, progress, 0.0).astype(np.float64)


@dataclass(frozen=True)
class EvaluationClass:
    class_id: int
    trials: int
    errors: int
    empirical_risk: float
    f1: float


@dataclass(frozen=True)
class PolicyMetrics:
    samples: int
    accuracy: float
    macro_f1: float
    empirical_risk: float
    max_class_risk: float
    mean_normalized_stop: float
    earliness: float
    fallback_rate: float
    class_metrics: tuple[EvaluationClass, ...]


def evaluate_policy(
    predictions: PrefixPredictions,
    policy: Policy,
    progress: np.ndarray | None = None,
) -> PolicyMetrics:
    """Evaluate an already chosen policy without performing any selection."""
    if progress is None:
        progress = valid_observation_progress(predictions)
    outcome = execute_policy(predictions, policy, progress=progress)
    losses = outcome.labels != predictions.targets
    class_metrics: list[EvaluationClass] = []
    for class_id in range(predictions.class_count):
        truth = predictions.targets == class_id
        predicted = outcome.labels == class_id
        trials = int(truth.sum())
        errors = int(losses[truth].sum())
        true_positives = int(np.logical_and(truth, predicted).sum())
        false_positives = int(np.logical_and(~truth, predicted).sum())
        false_negatives = int(np.logical_and(truth, ~predicted).sum())
        denominator = 2 * true_positives + false_positives + false_negatives
        class_metrics.append(
            EvaluationClass(
                class_id=class_id,
                trials=trials,
                errors=errors,
                empirical_risk=errors / trials if trials else 1.0,
                f1=(2 * true_positives / denominator) if denominator else 0.0,
            )
        )

    normalized_stops = np.array(
        [
            predictions.valid_mask[index, : stop + 1].sum()
            / predictions.sequence_lengths[index]
            for index, stop in enumerate(outcome.stop_indices)
        ],
        dtype=float,
    )
    accuracy = float((~losses).mean())
    mean_stop = float(normalized_stops.mean())
    return PolicyMetrics(
        samples=int(losses.size),
        accuracy=accuracy,
        macro_f1=float(np.mean([item.f1 for item in class_metrics])),
        empirical_risk=1.0 - accuracy,
        max_class_risk=max(item.empirical_risk for item in class_metrics),
        mean_normalized_stop=mean_stop,
        earliness=1.0 - mean_stop,
        fallback_rate=float(outcome.used_fallback.mean()),
        class_metrics=tuple(class_metrics),
    )
