"""Calibrate a fixed family of selective early-stopping policies on fresh data."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from rcecrop.selective_risk import calibrate_selective_thresholds


def load_run(path: Path, cutoff: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    metadata = json.loads((path / "run_metadata.json").read_text(encoding="utf-8"))
    if metadata["status"] != "complete" or metadata["cutoff"] != cutoff:
        raise ValueError(f"{path} is not a complete calibration export for {cutoff}")
    if metadata["roles_read"] != ["target_risk_calibration"]:
        raise ValueError(f"{path} did not exclusively read the fresh calibration role")
    if "target_final_test" not in metadata["roles_not_read"]:
        raise ValueError(f"{path} lacks the final-test isolation record")
    with np.load(path / "calibration_predictions.npz", allow_pickle=False) as data:
        return data["probabilities"], data["targets"], data["names"]


def main() -> None:
    repository = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Calibrate selective early stopping using fresh target calibration data only.")
    parser.add_argument("--protocol", type=Path, default=repository / "configs/experiments/stage29_fresh_calibration_protocol.json")
    parser.add_argument("--calibration-run", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--formal-claim-eligible",
        choices=("true", "false"),
        default="true",
        help="mark the result as eligible for the formal claim; use false for sensitivity-only runs",
    )
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("output directory already exists; do not overwrite a calibration result")
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    cutoffs = protocol["early_decision_cutoffs"]
    if len(args.calibration_run) != len(cutoffs):
        raise ValueError("provide exactly one fresh calibration run for every frozen cutoff")
    loaded = [load_run(path, cutoff) for path, cutoff in zip(args.calibration_run, cutoffs)]
    probabilities, targets, names = zip(*loaded)
    if not all(np.array_equal(names[0], value) for value in names[1:]):
        raise ValueError("fresh calibration sample names are not aligned across cutoffs")
    if not all(np.array_equal(targets[0], value) for value in targets[1:]):
        raise ValueError("fresh calibration targets are not aligned across cutoffs")
    contract = protocol["selective_risk_contract"]
    formal_claim_eligible = args.formal_claim_eligible == "true"
    assessments = calibrate_selective_thresholds(
        np.stack(probabilities, axis=1),
        targets[0],
        tuple(contract["candidate_pmax_thresholds"]),
        contract["overall_error_risk_target"],
        contract["minimum_automatic_coverage"],
        contract["confidence"],
    )
    certified = [item for item in assessments if item.certified]
    selected = min(
        certified,
        key=lambda item: (item.mean_stop_index, -item.coverage, item.threshold),
    ) if certified else None
    result = {
        "stage": "30_selective_risk_calibration",
        "formal_claim_eligible": formal_claim_eligible,
        "status": "CERTIFIED_SELECTIVE_POLICY" if selected else "NO_CERTIFIED_POLICY",
        "protocol": str(args.protocol),
        "cutoffs": cutoffs,
        "calibration_runs": [str(path) for path in args.calibration_run],
        "calibration_samples": len(targets[0]),
        "roles_read": ["target_risk_calibration"],
        "roles_not_read": ["source_train", "source_development", "target_adaptation", "target_final_test"],
        "contract": contract,
        "assessments": [asdict(item) for item in assessments],
        "selected": asdict(selected) if selected else None,
    }
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "calibration_result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    if selected:
        (args.output_dir / "frozen_policy.json").write_text(
            json.dumps(
                {
                    "threshold": selected.threshold,
                    "cutoffs": cutoffs,
                    "defer_unaccepted": True,
                    "formal_claim_eligible": formal_claim_eligible,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    print(json.dumps({"status": result["status"], "output": str(args.output_dir)}))


if __name__ == "__main__":
    main()
