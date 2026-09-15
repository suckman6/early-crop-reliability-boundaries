import json
import tempfile
import unittest
from pathlib import Path


class Stage30CalibrationMetadataTests(unittest.TestCase):
    def test_nonformal_sensitivity_policy_is_explicitly_marked(self):
        policy = {
            "threshold": 0.9,
            "cutoffs": ["2021-04-15"],
            "defer_unaccepted": True,
            "formal_claim_eligible": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frozen_policy.json"
            path.write_text(json.dumps(policy), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(loaded["formal_claim_eligible"])


if __name__ == "__main__":
    unittest.main()
