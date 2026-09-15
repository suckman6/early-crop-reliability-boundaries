"""Manual-only final blind evaluation of the frozen selective policy."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from rcecrop.eurocropsml import materialize_prefix_features, split_names
from rcecrop.selective_evaluation import evaluate_selective_policy, macro_f1


def load_model(source_run: Path, target_run: Path, labels: list[str], device: object):
    import torch
    from torch import nn

    checkpoint = torch.load(target_run / "target_adapted.pt", map_location="cpu", weights_only=True)
    if checkpoint["labels"] != labels:
        raise ValueError(f"{target_run} labels differ from the frozen protocol")
    with np.load(source_run / "source_prefix_features.npz") as source_features:
        mean, std = source_features["mean"], source_features["std"]
    model = nn.Sequential(nn.Linear(int(checkpoint["feature_dimension"]), 128), nn.ReLU(), nn.Linear(128, len(labels)))
    model.load_state_dict(checkpoint["model_state"])
    return model.to(device).eval(), mean, std, checkpoint["cutoff"]


def predict(model: object, features: np.ndarray, device: object, batch_size: int) -> np.ndarray:
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    outputs = []
    with torch.no_grad():
        for (batch,) in DataLoader(TensorDataset(torch.from_numpy(features)), batch_size=batch_size, shuffle=False, num_workers=0):
            outputs.append(torch.softmax(model(batch.to(device)), dim=1).cpu().numpy())
    return np.concatenate(outputs)


def main() -> None:
    repository = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Evaluate one frozen selective policy on official Estonia test data only.")
    parser.add_argument("--protocol", type=Path, default=repository / "configs/experiments/stage29_fresh_calibration_protocol.json")
    parser.add_argument("--frozen-policy", type=Path, required=True)
    parser.add_argument("--calibration-result", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, action="append", required=True)
    parser.add_argument("--target-run", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, default=repository / "data/eurocropsml/extracted")
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("output directory already exists; do not overwrite a blind test")
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    labels = protocol["class_rule"]["hcat_codes"]
    cutoffs = protocol["early_decision_cutoffs"]
    if len(args.source_run) != len(cutoffs) or len(args.target_run) != len(cutoffs):
        raise ValueError("provide one source run and one target run for every frozen cutoff")
    policy = json.loads(args.frozen_policy.read_text(encoding="utf-8"))
    calibration = json.loads(args.calibration_result.read_text(encoding="utf-8"))
    if calibration["status"] != "CERTIFIED_SELECTIVE_POLICY" or calibration["selected"] is None:
        raise ValueError("final evaluation requires a certified calibration result")
    if policy["threshold"] != calibration["selected"]["threshold"] or policy["cutoffs"] != cutoffs or not policy["defer_unaccepted"]:
        raise ValueError("frozen policy does not match the certified calibration result")
    import torch
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is required by default; pass --device cpu only for an intentional CPU run")
    device = torch.device(args.device)
    split_file, part = protocol["target_domain"]["official_test_split"].split(":", 1)
    test_names = split_names(args.data_root / "split" / split_file, part, set(labels))
    label_to_index = {label: index for index, label in enumerate(labels)}
    probabilities, targets = [], None
    for cutoff, source_run, target_run in zip(cutoffs, args.source_run, args.target_run):
        model, mean, std, checkpoint_cutoff = load_model(source_run, target_run, labels, device)
        if checkpoint_cutoff != cutoff:
            raise ValueError(f"{target_run} cutoff does not match {cutoff}")
        print(json.dumps({"status": "materializing_target_final_test", "cutoff": cutoff, "samples": len(test_names)}), flush=True)
        features, current_targets = materialize_prefix_features(
            args.data_root / "preprocess", test_names, label_to_index, np.datetime64(cutoff),
            progress=lambda complete, total, date=cutoff: print(json.dumps({"status": "materializing_target_final_test", "cutoff": date, "complete": complete, "total": total}), flush=True),
        )
        if targets is None:
            targets = current_targets
        elif not np.array_equal(targets, current_targets):
            raise ValueError("test labels differ across frozen cutoffs")
        probabilities.append(predict(model, (features - mean) / std, device, args.batch_size))
    stacked = np.stack(probabilities, axis=1)
    metrics, predicted_labels, stop_indices = evaluate_selective_policy(stacked, targets, policy["threshold"])
    full_labels = stacked[:, -1].argmax(axis=1)
    full_sequence = {
        "accuracy": float((full_labels == targets).mean()),
        "macro_f1": macro_f1(targets, full_labels, len(labels)),
    }
    result = {
        "stage": "31_final_blind_test",
        "status": "complete",
        "formal_claim_eligible": True,
        "protocol": str(args.protocol),
        "frozen_policy": str(args.frozen_policy),
        "calibration_result": str(args.calibration_result),
        "source_runs": [str(value) for value in args.source_run],
        "target_runs": [str(value) for value in args.target_run],
        "roles_read": ["target_final_test"],
        "roles_not_read": ["source_train", "source_development", "target_adaptation", "target_risk_calibration"],
        "cutoffs": cutoffs,
        "threshold": policy["threshold"],
        "defer_unaccepted": True,
        "selective_metrics": asdict(metrics),
        "full_sequence_reference": full_sequence,
    }
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "test_result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    np.savez_compressed(args.output_dir / "test_policy_predictions.npz", names=np.asarray(test_names), targets=targets, labels=predicted_labels, stop_indices=stop_indices, full_sequence_labels=full_labels)
    print(json.dumps({"status": "complete", "output": str(args.output_dir)}))


if __name__ == "__main__":
    main()
