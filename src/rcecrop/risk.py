"""Finite-policy risk calibration with exact binomial upper bounds."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np

from .config import RiskCalibrationConfig
from .contracts import PrefixPredictions
from .policy import Policy, execute_policy


def clopper_pearson_upper(errors: int, trials: int, delta: float) -> float:
    if trials < 0 or errors < 0 or errors > trials:
        raise ValueError("require 0 <= errors <= trials")
    if not 0.0 < delta < 1.0:
        raise ValueError("delta must lie strictly between zero and one")
    if trials == 0 or errors == trials:
        return 1.0
    if errors == 0:
        return 1.0 - delta ** (1.0 / trials)

    log_combinations = np.array(
        [
            math.lgamma(trials + 1)
            - math.lgamma(successes + 1)
            - math.lgamma(trials - successes + 1)
            for successes in range(errors + 1)
        ]
    )
    successes = np.arange(errors + 1, dtype=float)

    def cdf(probability: float) -> float:
        terms = (
            log_combinations
            + successes * math.log(probability)
            + (trials - successes) * math.log1p(-probability)
        )
        maximum = float(terms.max())
        return math.exp(maximum) * float(np.exp(terms - maximum).sum())

    lower = errors / trials
    upper = 1.0 - np.finfo(float).eps
    for _ in range(60):
        midpoint = (lower + upper) / 2.0
        if cdf(midpoint) > delta:
            lower = midpoint
        else:
            upper = midpoint
    return upper


@dataclass(frozen=True)
class ClassRisk:
    class_id: int
    trials: int
    errors: int
    empirical_risk: float
    upper_bound: float


@dataclass(frozen=True)
class PolicyAssessment:
    policy: Policy
    trials: int
    errors: int
    empirical_risk: float
    upper_bound: float
    class_risks: tuple[ClassRisk, ...]
    mean_normalized_stop: float
    feasible: bool

    @property
    def max_empirical_class_risk(self) -> float:
        return max(item.empirical_risk for item in self.class_risks)


@dataclass(frozen=True)
class CalibrationResult:
    status: str
    selected: PolicyAssessment
    assessments: tuple[PolicyAssessment, ...]
    test_count: int
    adjusted_delta: float


def calibrate_policies(
    predictions: PrefixPredictions,
    policies: Sequence[Policy],
    config: RiskCalibrationConfig,
    split: str = "calibration",
    progress: np.ndarray | None = None,
) -> CalibrationResult:
    if split != "calibration":
        raise ValueError("policy calibration requires the calibration split")
    if not policies:
        raise ValueError("at least one policy is required")
    if len(policies) != config.candidate_size:
        raise ValueError("candidate_size differs from the materialized policy count")
    if predictions.class_count != config.label_count:
        raise ValueError("configured label_count differs from prefix predictions")
    if len(set(predictions.calibration_unit_ids)) != len(predictions.calibration_unit_ids):
        raise ValueError("calibration_unit_ids must be independent and unique")
    full_policies = [policy for policy in policies if policy.full_sequence]
    if len(full_policies) != 1:
        raise ValueError("candidate set must contain exactly one full-sequence policy")

    test_count = len(policies) * (1 + config.label_count)
    adjusted_delta = (1.0 - config.confidence) / test_count
    assessments: list[PolicyAssessment] = []
    for policy in policies:
        outcome = execute_policy(predictions, policy, progress=progress)
        losses = outcome.labels != predictions.targets
        errors = int(losses.sum())
        trials = losses.size
        upper = clopper_pearson_upper(errors, trials, adjusted_delta)
        class_risks = []
        for class_id in range(config.label_count):
            selected = predictions.targets == class_id
            class_trials = int(selected.sum())
            class_errors = int(losses[selected].sum())
            class_risks.append(
                ClassRisk(
                    class_id=class_id,
                    trials=class_trials,
                    errors=class_errors,
                    empirical_risk=class_errors / class_trials if class_trials else 1.0,
                    upper_bound=clopper_pearson_upper(
                        class_errors, class_trials, adjusted_delta
                    ),
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
        feasible = upper <= config.overall_risk and all(
            item.upper_bound <= config.class_risk for item in class_risks
        )
        assessments.append(
            PolicyAssessment(
                policy=policy,
                trials=trials,
                errors=errors,
                empirical_risk=errors / trials,
                upper_bound=upper,
                class_risks=tuple(class_risks),
                mean_normalized_stop=float(normalized_stops.mean()),
                feasible=feasible,
            )
        )

    feasible = [assessment for assessment in assessments if assessment.feasible]
    if feasible:
        selected = min(
            feasible,
            key=lambda item: (
                item.mean_normalized_stop,
                item.empirical_risk,
                item.max_empirical_class_risk,
                item.policy.canonical_key(),
            ),
        )
        status = "CERTIFIED_FULL_SEQUENCE" if selected.policy.full_sequence else "CERTIFIED_EARLY"
    else:
        selected = next(item for item in assessments if item.policy.full_sequence)
        status = "NO_CERTIFIED_POLICY"
    return CalibrationResult(
        status=status,
        selected=selected,
        assessments=tuple(assessments),
        test_count=test_count,
        adjusted_delta=adjusted_delta,
    )
