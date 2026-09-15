"""Create a deterministic, stratified fresh Estonia fit/calibration split."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from rcecrop.eurocropsml import hcat_code, split_names


def stable_rank(name: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}:{name}".encode("utf-8")).hexdigest()


def main() -> None:
    repository = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Create a fresh stratified target fit/calibration manifest.")
    parser.add_argument("--protocol", type=Path, default=repository / "configs/experiments/stage29_fresh_calibration_protocol.json")
    parser.add_argument("--data-root", type=Path, default=repository / "data/eurocropsml/extracted")
    parser.add_argument("--output", type=Path, default=repository / "artifacts/stage29/splits/estonia_target_fit_calibration_seed20260729.json")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("fresh split manifest already exists; do not overwrite it")
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    contract = protocol["fresh_split_contract"]
    labels = set(protocol["class_rule"]["hcat_codes"])
    split_file, part = contract["source_partition"].split(":", 1)
    names = split_names(args.data_root / "split" / split_file, part, labels)
    grouped: dict[str, list[str]] = defaultdict(list)
    for name in names:
        grouped[hcat_code(name)].append(name)
    calibration, target_fit = [], []
    for label in sorted(grouped):
        ranked = sorted(grouped[label], key=lambda name: stable_rank(name, contract["seed"]))
        calibration_count = max(1, round(len(ranked) * contract["calibration_fraction"]))
        calibration.extend(ranked[:calibration_count])
        target_fit.extend(ranked[calibration_count:])
    payload = {
        "stage": "29_fresh_target_calibration_split",
        "status": "complete",
        "formal_claim_eligible": True,
        "source_partition": contract["source_partition"],
        "stratification": contract["stratification"],
        "seed": contract["seed"],
        "calibration_fraction": contract["calibration_fraction"],
        "target_fit": sorted(target_fit),
        "target_risk_calibration": sorted(calibration),
        "class_counts": {
            label: {
                "target_fit": sum(hcat_code(name) == label for name in target_fit),
                "target_risk_calibration": sum(hcat_code(name) == label for name in calibration),
            }
            for label in sorted(grouped)
        },
        "roles_not_read": ["source_train", "source_development", "target_final_test"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"status": "complete", "output": str(args.output), "target_fit": len(target_fit), "target_risk_calibration": len(calibration)}))


if __name__ == "__main__":
    main()
