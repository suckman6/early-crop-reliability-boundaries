"""Metrics for a frozen selective early-classification policy."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .selective_risk import earliest_selective_predictions


@dataclass(frozen=True)
class SelectiveTestMetrics:
    samples: int
    automatic_samples: int
    automatic_coverage: float
    automatic_accuracy: float | None
    automatic_risk: float | None
    automatic_macro_f1: float | None
    deferred_samples: int
    mean_stop_index: float | None
    stop_counts: tuple[int, ...]


def macro_f1(targets: np.ndarray, labels: np.ndarray, classes: int) -> float:
    scores = []
    for class_id in range(classes):
        truth = targets == class_id
        predicted = labels == class_id
        true_positive = int(np.logical_and(truth, predicted).sum())
        denominator = int(2 * true_positive + np.logical_xor(truth, predicted).sum())
        scores.append(2 * true_positive / denominator if denominator else 0.0)
    return float(np.mean(scores))


def evaluate_selective_policy(
    probabilities: np.ndarray, targets: np.ndarray, threshold: float
) -> tuple[SelectiveTestMetrics, np.ndarray, np.ndarray]:
    labels, stops = earliest_selective_predictions(probabilities, threshold)
    targets = np.asarray(targets, dtype=np.int64)
    accepted = labels >= 0
    count = int(accepted.sum())
    classes = int(probabilities.shape[2])
    correct = labels[accepted] == targets[accepted]
    metrics = SelectiveTestMetrics(
        samples=len(targets),
        automatic_samples=count,
        automatic_coverage=count / len(targets),
        automatic_accuracy=(float(correct.mean()) if count else None),
        automatic_risk=(float((~correct).mean()) if count else None),
        automatic_macro_f1=(macro_f1(targets[accepted], labels[accepted], classes) if count else None),
        deferred_samples=int((~accepted).sum()),
        mean_stop_index=(float(stops[accepted].mean()) if count else None),
        stop_counts=tuple(int((stops == index).sum()) for index in range(probabilities.shape[1])),
    )
    return metrics, labels, stops
