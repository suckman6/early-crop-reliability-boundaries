"""Prefix manifest and optional HDF5 persistence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .contracts import PrefixPredictions


@dataclass(frozen=True)
class PrefixManifest:
    schema_version: str
    dataset: str
    split: str
    class_names: tuple[str, ...]
    checkpoint_sha256: str
    config_sha256: str
    parent_commit: str
    elects_commit: str
    seed: int
    input_dim: int
    time_semantics: str
    perturbation: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.split not in {"train", "calibration", "test"}:
            raise ValueError("split must be train, calibration, or test")
        if not self.dataset or not self.schema_version or not self.class_names:
            raise ValueError("dataset, schema_version, and class_names are required")
        if self.input_dim < 1 or self.seed < 0:
            raise ValueError("input_dim must be positive and seed cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> "PrefixManifest":
        values = dict(values)
        values["class_names"] = tuple(values["class_names"])
        return cls(**values)


def write_manifest(path: str | Path, manifest: PrefixManifest) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def read_manifest(path: str | Path) -> PrefixManifest:
    return PrefixManifest.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _h5py():
    try:
        return importlib.import_module("h5py")
    except ModuleNotFoundError as error:
        raise RuntimeError("HDF5 I/O requires the optional 'h5py' dependency") from error


def write_prefixes_h5(path: str | Path, predictions: PrefixPredictions) -> None:
    h5py = _h5py()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    string_type = h5py.string_dtype(encoding="utf-8")
    with h5py.File(path, "w") as handle:
        handle.create_dataset("sample_id", data=predictions.sample_ids, dtype=string_type)
        handle.create_dataset(
            "calibration_unit_id", data=predictions.calibration_unit_ids, dtype=string_type
        )
        for name, values in (
            ("y_true", predictions.targets),
            ("class_probabilities", predictions.class_probabilities),
            ("stop_probabilities", predictions.stop_probabilities),
            ("valid_mask", predictions.valid_mask),
            ("timestamps", predictions.timestamps),
            ("sequence_length", predictions.sequence_lengths),
        ):
            handle.create_dataset(name, data=values, compression="gzip", shuffle=True)


def read_prefixes_h5(path: str | Path) -> PrefixPredictions:
    h5py = _h5py()
    with h5py.File(path, "r") as handle:
        strings = lambda name: tuple(
            value.decode("utf-8") if isinstance(value, bytes) else str(value)
            for value in handle[name][...]
        )
        return PrefixPredictions(
            class_probabilities=handle["class_probabilities"][...],
            stop_probabilities=handle["stop_probabilities"][...],
            targets=handle["y_true"][...],
            sample_ids=strings("sample_id"),
            calibration_unit_ids=strings("calibration_unit_id"),
            timestamps=handle["timestamps"][...],
            valid_mask=handle["valid_mask"][...],
            sequence_lengths=handle["sequence_length"][...],
        )
