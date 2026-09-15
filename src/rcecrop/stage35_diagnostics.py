"""Post hoc class- and decision-date diagnostics for frozen test outputs.

This module reports heterogeneity in already-produced predictions.  It does not
calibrate, select, or alter a policy, and its class-wise intervals are not
class-conditional guarantees.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


CUTOFFS = ("2021-04-15", "2021-05-15", "2021-06-15", "2021-07-15", "2021-08-15", "2021-09-15")
HCAT_NAMES = {
    "3301010101": "winter common soft wheat",
    "3301010102": "spring common soft wheat",
    "3301010300": "rye",
    "3301010401": "winter barley",
    "3301010402": "spring barley",
    "3301010500": "oats",
    "3301010600": "grain maize",
    "3301020100": "beans",
    "3301020600": "peas",
    "3301030000": "potatoes",
    "3301060401": "winter rapeseed",
    "3301070000": "fresh vegetables",
    "3301090301": "alfalfa",
    "3301090303": "clover",
    "3301110000": "fallow land",
    "3301150200": "buckwheat",
}


def wilson_interval(errors: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Return a two-sided Wilson interval for a binomial error proportion."""
    if total == 0:
        return math.nan, math.nan
    proportion = errors / total
    denominator = 1.0 + z * z / total
    centre = (proportion + z * z / (2.0 * total)) / denominator
    half_width = z * math.sqrt(proportion * (1.0 - proportion) / total + z * z / (4.0 * total * total)) / denominator
    return centre - half_width, centre + half_width


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_run(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        required = {"names", "targets", "labels", "stop_indices", "full_sequence_labels"}
        if set(archive.files) != required:
            raise ValueError(f"{path} has unexpected fields: {archive.files}")
        run = {key: archive[key].copy() for key in required}
    size = len(run["names"])
    if any(len(values) != size for values in run.values()):
        raise ValueError(f"{path} contains arrays with different lengths")
    if not np.isin(run["stop_indices"], np.arange(-1, len(CUTOFFS))).all():
        raise ValueError(f"{path} contains invalid stopping indices")
    return run


def analyse(runs: list[tuple[int, Path]], labels: list[str]) -> dict[str, list[dict[str, object]]]:
    loaded = [(seed, load_run(path)) for seed, path in runs]
    reference = loaded[0][1]
    for seed, run in loaded[1:]:
        if not np.array_equal(run["names"], reference["names"]) or not np.array_equal(run["targets"], reference["targets"]):
            raise ValueError(f"seed {seed} is not parcel-for-parcel aligned with seed {loaded[0][0]}")
    if set(np.unique(reference["targets"])) != set(range(len(labels))):
        raise ValueError("test targets do not contain exactly the frozen label indices")

    class_rows: list[dict[str, object]] = []
    date_rows: list[dict[str, object]] = []
    class_date_rows: list[dict[str, object]] = []
    sample_count = len(reference["targets"])
    for seed, run in loaded:
        accepted = run["stop_indices"] >= 0
        errors = run["labels"] != run["targets"]
        for class_index, code in enumerate(labels):
            class_mask = run["targets"] == class_index
            released = class_mask & accepted
            support = int(class_mask.sum())
            accepted_count = int(released.sum())
            error_count = int((released & errors).sum())
            lower, upper = wilson_interval(error_count, accepted_count)
            class_rows.append(
                {
                    "seed": seed,
                    "class_index": class_index,
                    "hcat_code": code,
                    "class_name": HCAT_NAMES.get(code, code),
                    "test_support": support,
                    "automatic_count": accepted_count,
                    "automatic_coverage": accepted_count / support,
                    "automatic_errors": error_count,
                    "automatic_risk": error_count / accepted_count if accepted_count else math.nan,
                    "risk_wilson95_lower": lower,
                    "risk_wilson95_upper": upper,
                }
            )
            for stop_index, cutoff in enumerate(CUTOFFS):
                count = int((class_mask & (run["stop_indices"] == stop_index)).sum())
                class_date_rows.append(
                    {
                        "seed": seed,
                        "class_index": class_index,
                        "hcat_code": code,
                        "class_name": HCAT_NAMES.get(code, code),
                        "disposition": cutoff,
                        "count": count,
                        "class_percent": 100.0 * count / support,
                    }
                )
            deferred_count = int((class_mask & ~accepted).sum())
            class_date_rows.append(
                {
                    "seed": seed,
                    "class_index": class_index,
                    "hcat_code": code,
                    "class_name": HCAT_NAMES.get(code, code),
                    "disposition": "Deferred",
                    "count": deferred_count,
                    "class_percent": 100.0 * deferred_count / support,
                }
            )
        for stop_index, cutoff in enumerate(CUTOFFS):
            stopped = run["stop_indices"] == stop_index
            count = int(stopped.sum())
            error_count = int((stopped & errors).sum())
            lower, upper = wilson_interval(error_count, count)
            date_rows.append(
                {
                    "seed": seed,
                    "cutoff": cutoff,
                    "automatic_count": count,
                    "all_sample_coverage_contribution": count / sample_count,
                    "automatic_errors": error_count,
                    "automatic_risk": error_count / count if count else math.nan,
                    "risk_wilson95_lower": lower,
                    "risk_wilson95_upper": upper,
                }
            )
    return {"class": class_rows, "date": date_rows, "class_date": class_date_rows}


def main() -> None:
    repository = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Describe class/date heterogeneity in already-frozen test predictions.")
    parser.add_argument("--protocol", type=Path, default=repository / "configs/experiments/stage29_fresh_calibration_protocol.json")
    parser.add_argument("--run", nargs=2, action="append", metavar=("SEED", "PREDICTIONS"), required=True)
    parser.add_argument("--output-dir", type=Path, default=repository / "artifacts/stage35/class_date_diagnostics")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("output directory already exists; preserve the immutable post hoc audit")
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    labels = protocol["class_rule"]["hcat_codes"]
    runs = [(int(seed), Path(path)) for seed, path in args.run]
    if [seed for seed, _ in runs] != [0, 1, 2]:
        raise ValueError("Stage 35 expects the frozen seed order 0, 1, 2")
    diagnostics = analyse(runs, labels)
    args.output_dir.mkdir(parents=True)
    write_csv(args.output_dir / "classwise_diagnostics.csv", diagnostics["class"])
    write_csv(args.output_dir / "datewise_diagnostics.csv", diagnostics["date"])
    write_csv(args.output_dir / "class_date_disposition.csv", diagnostics["class_date"])
    summary = {
        "stage": "35_posthoc_class_date_diagnostics",
        "status": "complete",
        "formal_claim_eligible": False,
        "diagnostic_only": True,
        "policy_or_threshold_selection_performed": False,
        "class_conditional_guarantee": False,
        "test_samples": len(load_run(runs[0][1])["targets"]),
        "seeds": [seed for seed, _ in runs],
        "prediction_files": [str(path) for _, path in runs],
        "alignment_verified": True,
        "taxonomy_source": "EuroCrops HCAT3.csv at commit 5c33a1133865ded9ec1a1438fc7708e84a895db5",
    }
    (args.output_dir / "diagnostic_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"status": "complete", "output": str(args.output_dir)}))


if __name__ == "__main__":
    main()
