"""Validated lightweight configuration contracts."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Mapping


@dataclass(frozen=True)
class RiskCalibrationConfig:
    overall_risk: float = 0.05
    class_risk: float = 0.10
    confidence: float = 0.95
    candidate_size: int = 32
    label_count: int = 7

    def __post_init__(self) -> None:
        for name in ("overall_risk", "class_risk"):
            value = getattr(self, name)
            if not 0.0 < value < 1.0:
                raise ValueError(f"{name} must lie strictly between zero and one")
        if not 0.0 < self.confidence < 1.0:
            raise ValueError("confidence must lie strictly between zero and one")
        if self.candidate_size < 1:
            raise ValueError("candidate_size must be positive")
        if self.label_count < 2:
            raise ValueError("label_count must be at least two")

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "RiskCalibrationConfig":
        allowed = {field.name for field in fields(cls)}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"unknown calibration settings: {sorted(unknown)}")
        return cls(**values)
