"""Calibration-only feasibility audit for an output-class release filter.

The audit is post hoc and never creates a deployable frozen policy.  It asks
whether a conservative filter on the model's emitted class could, in principle,
satisfy simultaneous output-class risk bounds while retaining the original
overall coverage target.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from rcecrop.risk import clopper_pearson_upper
from rcecrop.selective_risk import earliest_selective_predictions, lower_binomial_bound
from rcecrop.stage35_diagnostics import HCAT_NAMES


def load_seed_runs(paths: list[Path], cutoffs: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if len(paths) != len(cutoffs):
        raise ValueError("provide one calibration run for every cutoff")
    probabilities, targets, names = [], [], []
    for path, cutoff in zip(paths, cutoffs):
        metadata = json.loads((path / "run_metadata.json").read_text(encoding="utf-8"))
        if metadata["status"] != "complete" or metadata["cutoff"] != cutoff:
            raise ValueError(f"{path} is not a complete export for {cutoff}")
        if metadata["roles_read"] != ["target_risk_calibration"]:
            raise ValueError(f"{path} did not exclusively read target_risk_calibration")
        if "target_final_test" not in metadata["roles_not_read"]:
            raise ValueError(f"{path} lacks the final-test isolation record")
        with np.load(path / "calibration_predictions.npz", allow_pickle=False) as archive:
            if set(archive.files) != {"probabilities", "targets", "names"}:
                raise ValueError(f"{path} has unexpected calibration fields")
            probabilities.append(archive["probabilities"].copy())
            targets.append(archive["targets"].copy())
            names.append(archive["names"].copy())
    if not all(np.array_equal(names[0], value) for value in names[1:]):
        raise ValueError("calibration names are not aligned across cutoffs")
    if not all(np.array_equal(targets[0], value) for value in targets[1:]):
        raise ValueError("calibration targets are not aligned across cutoffs")
    return np.stack(probabilities, axis=1), targets[0], names[0]


def assess_output_class_filter(
    probabilities: np.ndarray,
    targets: np.ndarray,
    labels: list[str],
    thresholds: list[float],
    risk_target: float,
    minimum_coverage: float,
    confidence: float,
) -> tuple[list[dict[str, object]], list[dict[str, object]], float]:
    """Assess all fixed threshold/output-class cells with simultaneous bounds."""
    family_size = 2 * len(thresholds) * len(labels)
    adjusted_delta = (1.0 - confidence) / family_size
    cells: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    for threshold in thresholds:
        predicted, stops = earliest_selective_predictions(probabilities, threshold)
        accepted = predicted >= 0
        threshold_cells = []
        for class_index, code in enumerate(labels):
            emitted = accepted & (predicted == class_index)
            count = int(emitted.sum())
            errors = int((targets[emitted] != class_index).sum())
            risk_upper = clopper_pearson_upper(errors, count, adjusted_delta)
            coverage_lower = lower_binomial_bound(count, len(targets), adjusted_delta)
            row = {
                "threshold": threshold,
                "output_class_index": class_index,
                "hcat_code": code,
                "class_name": HCAT_NAMES.get(code, code),
                "emitted_count": count,
                "errors": errors,
                "empirical_risk": errors / count if count else None,
                "risk_upper": risk_upper,
                "coverage_contribution": count / len(targets),
                "coverage_contribution_lower": coverage_lower,
                "risk_certified": bool(count > 0 and risk_upper <= risk_target),
            }
            cells.append(row)
            threshold_cells.append(row)
        certified = [row for row in threshold_cells if row["risk_certified"]]
        certified_indices = [int(row["output_class_index"]) for row in certified]
        usable = accepted & np.isin(predicted, certified_indices)
        usable_count = int(usable.sum())
        usable_errors = int((predicted[usable] != targets[usable]).sum())
        coverage_lower = float(sum(float(row["coverage_contribution_lower"]) for row in certified))
        candidates.append(
            {
                "threshold": threshold,
                "certified_output_class_count": len(certified),
                "certified_output_classes": "|".join(str(row["hcat_code"]) for row in certified),
                "certified_output_class_names": "|".join(str(row["class_name"]) for row in certified),
                "usable_count": usable_count,
                "usable_errors": usable_errors,
                "empirical_usable_risk": usable_errors / usable_count if usable_count else None,
                "empirical_usable_coverage": usable_count / len(targets),
                "simultaneous_usable_coverage_lower": coverage_lower,
                "mean_stop_index": float(stops[usable].mean()) if usable_count else None,
                "feasible": bool(certified and coverage_lower >= minimum_coverage),
            }
        )
    return cells, candidates, adjusted_delta


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    repository = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Audit an output-class filter using calibration data only.")
    parser.add_argument("--protocol", type=Path, default=repository / "configs/experiments/stage29_fresh_calibration_protocol.json")
    parser.add_argument("--seed0-run", type=Path, action="append", required=True)
    parser.add_argument("--seed1-run", type=Path, action="append", required=True)
    parser.add_argument("--seed2-run", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=repository / "artifacts/stage36/output_class_filter_feasibility")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("output directory already exists; preserve the immutable feasibility audit")

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    cutoffs = protocol["early_decision_cutoffs"]
    labels = protocol["class_rule"]["hcat_codes"]
    contract = protocol["selective_risk_contract"]
    thresholds = contract["candidate_pmax_thresholds"]
    seed_paths = [args.seed0_run, args.seed1_run, args.seed2_run]
    loaded = [load_seed_runs(paths, cutoffs) for paths in seed_paths]
    reference_targets, reference_names = loaded[0][1], loaded[0][2]
    for seed, (_, targets, names) in enumerate(loaded[1:], start=1):
        if not np.array_equal(names, reference_names) or not np.array_equal(targets, reference_targets):
            raise ValueError(f"seed {seed} is not aligned with seed 0")

    cell_rows: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []
    adjusted_delta = None
    selected_by_seed = {}
    for seed, (probabilities, targets, _) in enumerate(loaded):
        cells, candidates, current_delta = assess_output_class_filter(
            probabilities,
            targets,
            labels,
            thresholds,
            contract["overall_error_risk_target"],
            contract["minimum_automatic_coverage"],
            contract["confidence"],
        )
        adjusted_delta = current_delta
        for row in cells:
            cell_rows.append({"seed": seed, **row})
        for row in candidates:
            candidate_rows.append({"seed": seed, **row})
        feasible = [row for row in candidates if row["feasible"]]
        selected = min(
            feasible,
            key=lambda row: (row["mean_stop_index"], -row["empirical_usable_coverage"], row["threshold"]),
        ) if feasible else None
        selected_by_seed[str(seed)] = selected

    common_threshold = None
    selected_thresholds = {row["threshold"] for row in selected_by_seed.values() if row is not None}
    if len(selected_thresholds) == 1 and len(selected_by_seed) == 3 and all(selected_by_seed.values()):
        common_threshold = selected_thresholds.pop()
    args.output_dir.mkdir(parents=True)
    write_csv(args.output_dir / "output_class_cells.csv", cell_rows)
    write_csv(args.output_dir / "candidate_feasibility.csv", candidate_rows)
    manifest = {
        "stage": "36_calibration_only_output_class_filter_feasibility",
        "status": "POSTHOC_CLASS_FILTER_FEASIBLE" if common_threshold is not None else "NO_STABLE_FEASIBLE_CLASS_FILTER",
        "formal_claim_eligible": False,
        "diagnostic_only": True,
        "calibration_only": True,
        "final_test_read": False,
        "policy_file_written": False,
        "policy_definition": "apply the global earliest-threshold rule, then release only output labels certified for that threshold; all other outcomes are terminally deferred",
        "conditioning": "model-emitted output class, not unknown true class",
        "confidence": contract["confidence"],
        "risk_target": contract["overall_error_risk_target"],
        "minimum_coverage": contract["minimum_automatic_coverage"],
        "candidate_thresholds": thresholds,
        "class_count": len(labels),
        "simultaneous_bound_count_per_seed": 2 * len(thresholds) * len(labels),
        "adjusted_delta_per_bound": adjusted_delta,
        "calibration_samples": len(reference_targets),
        "seeds": [0, 1, 2],
        "alignment_verified": True,
        "selected_by_seed": selected_by_seed,
        "stable_feasible_threshold": common_threshold,
        "limitations": [
            "The protocol change was motivated after the Estonia test had been opened.",
            "No final-test prediction was read and no new policy was frozen or evaluated.",
            "Output-label-conditional risk does not guarantee equal protection for each true crop class.",
        ],
    }
    (args.output_dir / "feasibility_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps({"status": manifest["status"], "output": str(args.output_dir)}))


if __name__ == "__main__":
    main()
