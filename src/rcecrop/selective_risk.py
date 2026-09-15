"""Finite-candidate risk certificates for selective early classification."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .risk import clopper_pearson_upper


@dataclass(frozen=True)
class SelectiveAssessment:
    threshold: float
    accepted: int
    errors: int
    empirical_risk: float | None
    risk_upper: float
    coverage: float
    coverage_lower: float
    mean_stop_index: float | None
    certified: bool


def lower_binomial_bound(successes: int, trials: int, delta: float) -> float:
    """Exact one-sided lower bound, derived from the upper bound on failures."""
    return 1.0 - clopper_pearson_upper(trials - successes, trials, delta)


def earliest_selective_predictions(probabilities: np.ndarray, threshold: float) -> tuple[np.ndarray, np.ndarray]:
    probabilities = np.asarray(probabilities, dtype=float)
    if probabilities.ndim != 3 or probabilities.shape[2] < 2:
        raise ValueError("probabilities must have shape (samples, dates, classes>=2)")
    if not 0.0 < threshold <= 1.0:
        raise ValueError("threshold must lie in (0, 1]")
    confidence = probabilities.max(axis=2)
    eligible = confidence >= threshold
    accepted = eligible.any(axis=1)
    stops = np.full(len(probabilities), -1, dtype=np.int64)
    stops[accepted] = eligible[accepted].argmax(axis=1)
    labels = np.full(len(probabilities), -1, dtype=np.int64)
    rows = np.flatnonzero(accepted)
    labels[rows] = probabilities[rows, stops[rows]].argmax(axis=1)
    return labels, stops


def calibrate_selective_thresholds(
    probabilities: np.ndarray,
    targets: np.ndarray,
    thresholds: tuple[float, ...],
    overall_risk_target: float,
    minimum_coverage: float,
    confidence: float,
) -> tuple[SelectiveAssessment, ...]:
    probabilities = np.asarray(probabilities, dtype=float)
    targets = np.asarray(targets, dtype=np.int64)
    if probabilities.shape[0] != len(targets):
        raise ValueError("probabilities and targets disagree on sample count")
    if not thresholds or len(set(thresholds)) != len(thresholds):
        raise ValueError("thresholds must be unique and non-empty")
    if not 0.0 < overall_risk_target < 1.0 or not 0.0 < minimum_coverage < 1.0:
        raise ValueError("risk target and coverage must lie strictly between zero and one")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie strictly between zero and one")
    delta = (1.0 - confidence) / (2 * len(thresholds))
    assessments = []
    for threshold in thresholds:
        labels, stops = earliest_selective_predictions(probabilities, threshold)
        accepted = labels >= 0
        count = int(accepted.sum())
        errors = int((labels[accepted] != targets[accepted]).sum())
        risk_upper = clopper_pearson_upper(errors, count, delta)
        coverage_lower = lower_binomial_bound(count, len(targets), delta)
        assessments.append(
            SelectiveAssessment(
                threshold=threshold,
                accepted=count,
                errors=errors,
                empirical_risk=(errors / count if count else None),
                risk_upper=risk_upper,
                coverage=count / len(targets),
                coverage_lower=coverage_lower,
                mean_stop_index=(float(stops[accepted].mean()) if count else None),
                certified=bool(
                    count > 0
                    and risk_upper <= overall_risk_target
                    and coverage_lower >= minimum_coverage
                ),
            )
        )
    return tuple(assessments)
