"""Matched score-based selective stopping diagnostics.

This module keeps the data protocol fixed and changes only the confidence score
used for first-crossing release.  Calibration is performed on the fresh
target-risk-calibration role; final-test evaluation is descriptive because the
official test was already opened by Stage 31.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .risk import clopper_pearson_upper
from .selective_evaluation import macro_f1
from .selective_risk import lower_binomial_bound


SCORE_FAMILIES = ("pmax", "margin", "entropy_confidence")


@dataclass(frozen=True)
class MatchedAssessment:
    score_family: str
    threshold: float
    accepted: int
    errors: int
    empirical_risk: float | None
    risk_upper: float
    coverage: float
    coverage_lower: float
    mean_stop_index: float | None
    certified: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _validate_probabilities(probabilities: np.ndarray) -> np.ndarray:
    values = np.asarray(probabilities, dtype=float)
    if values.ndim != 3 or values.shape[2] < 2:
        raise ValueError("probabilities must have shape (samples, dates, classes>=2)")
    if not np.isfinite(values).all() or np.any(values < 0.0):
        raise ValueError("probabilities must be finite and non-negative")
    return values


def score_values(probabilities: np.ndarray, score_family: str) -> np.ndarray:
    """Return one confidence score in [0, 1] per sample and date."""
    values = _validate_probabilities(probabilities)
    if score_family not in SCORE_FAMILIES:
        raise ValueError(f"unknown score family: {score_family}")
    if score_family == "pmax":
        return values.max(axis=2)
    if score_family == "margin":
        top_two = np.partition(values, -2, axis=2)[..., -2:]
        return top_two[..., 1] - top_two[..., 0]
    class_count = values.shape[2]
    safe = np.clip(values, np.finfo(float).tiny, 1.0)
    entropy = -(safe * np.log(safe)).sum(axis=2) / np.log(class_count)
    return np.clip(1.0 - entropy, 0.0, 1.0)


def release_from_score(
    probabilities: np.ndarray, score_family: str, threshold: float
) -> tuple[np.ndarray, np.ndarray]:
    """Apply first-crossing release and return labels/stopping indices."""
    values = _validate_probabilities(probabilities)
    if not 0.0 < threshold <= 1.0:
        raise ValueError("threshold must lie in (0, 1]")
    scores = score_values(values, score_family)
    eligible = scores >= float(threshold)
    accepted = eligible.any(axis=1)
    stops = np.full(values.shape[0], -1, dtype=np.int64)
    labels = np.full(values.shape[0], -1, dtype=np.int64)
    rows = np.flatnonzero(accepted)
    stops[rows] = eligible[rows].argmax(axis=1)
    labels[rows] = values[rows, stops[rows]].argmax(axis=1)
    return labels, stops


def calibrate_score_family(
    probabilities: np.ndarray,
    targets: np.ndarray,
    score_family: str,
    thresholds: tuple[float, ...],
    overall_risk_target: float,
    minimum_coverage: float,
    confidence: float,
) -> tuple[MatchedAssessment, ...]:
    """Calibrate a fixed score family with the same simultaneous contract."""
    values = _validate_probabilities(probabilities)
    targets = np.asarray(targets, dtype=np.int64)
    if values.shape[0] != len(targets):
        raise ValueError("probabilities and targets disagree on sample count")
    if not thresholds or len(set(thresholds)) != len(thresholds):
        raise ValueError("thresholds must be unique and non-empty")
    if not 0.0 < overall_risk_target < 1.0:
        raise ValueError("overall_risk_target must lie strictly between zero and one")
    if not 0.0 < minimum_coverage < 1.0:
        raise ValueError("minimum_coverage must lie strictly between zero and one")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie strictly between zero and one")
    delta = (1.0 - confidence) / (2 * len(thresholds))
    assessments: list[MatchedAssessment] = []
    for threshold in thresholds:
        labels, stops = release_from_score(values, score_family, float(threshold))
        accepted = labels >= 0
        count = int(accepted.sum())
        errors = int((labels[accepted] != targets[accepted]).sum())
        assessments.append(
            MatchedAssessment(
                score_family=score_family,
                threshold=float(threshold),
                accepted=count,
                errors=errors,
                empirical_risk=(errors / count if count else None),
                risk_upper=clopper_pearson_upper(errors, count, delta),
                coverage=count / len(targets),
                coverage_lower=lower_binomial_bound(count, len(targets), delta),
                mean_stop_index=(float(stops[accepted].mean()) if count else None),
                certified=bool(
                    count > 0
                    and clopper_pearson_upper(errors, count, delta) <= overall_risk_target
                    and lower_binomial_bound(count, len(targets), delta) >= minimum_coverage
                ),
            )
        )
    return tuple(assessments)


def select_earliest_certified(
    assessments: tuple[MatchedAssessment, ...],
) -> MatchedAssessment | None:
    certified = [item for item in assessments if item.certified]
    if not certified:
        return None
    return min(
        certified,
        key=lambda item: (item.mean_stop_index, -item.coverage, item.threshold),
    )


def summarize_release(
    probabilities: np.ndarray,
    targets: np.ndarray,
    score_family: str,
    threshold: float,
) -> dict[str, object]:
    """Summarize a frozen score rule without using labels for selection."""
    values = _validate_probabilities(probabilities)
    targets = np.asarray(targets, dtype=np.int64)
    labels, stops = release_from_score(values, score_family, threshold)
    accepted = labels >= 0
    count = int(accepted.sum())
    correct = labels[accepted] == targets[accepted]
    return {
        "score_family": score_family,
        "threshold": float(threshold),
        "samples": int(len(targets)),
        "automatic_samples": count,
        "automatic_coverage": float(count / len(targets)),
        "automatic_accuracy": (float(correct.mean()) if count else None),
        "automatic_risk": (float((~correct).mean()) if count else None),
        "automatic_macro_f1": (
            macro_f1(targets[accepted], labels[accepted], values.shape[2]) if count else None
        ),
        "deferred_samples": int((~accepted).sum()),
        "mean_stop_index": (float(stops[accepted].mean()) if count else None),
        "stop_counts": [int((stops == index).sum()) for index in range(values.shape[1])],
    }

