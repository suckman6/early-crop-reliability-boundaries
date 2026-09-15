import importlib.util
import tempfile
from pathlib import Path
import unittest

import numpy as np

from rcecrop.io import (
    PrefixManifest,
    read_manifest,
    read_prefixes_h5,
    write_manifest,
    write_prefixes_h5,
)
from helpers import make_predictions


class IoTests(unittest.TestCase):
    def test_manifest_round_trip(self):
        manifest = PrefixManifest(
            schema_version="1.0",
            dataset="bavaria",
            split="calibration",
            class_names=("a", "b"),
            checkpoint_sha256="checkpoint",
            config_sha256="config",
            parent_commit="parent",
            elects_commit="a11a9937985bf88599b9d644009e47f5f02e78a1",
            seed=0,
            input_dim=13,
            time_semantics="index",
            perturbation={"kind": "clean"},
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            write_manifest(path, manifest)
            self.assertEqual(read_manifest(path), manifest)

    def test_hdf5_reports_missing_optional_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prefixes.h5"
            predictions = make_predictions(2)
            if importlib.util.find_spec("h5py") is None:
                with self.assertRaisesRegex(RuntimeError, "h5py"):
                    write_prefixes_h5(path, predictions)
            else:
                write_prefixes_h5(path, predictions)
                restored = read_prefixes_h5(path)
                np.testing.assert_allclose(
                    restored.class_probabilities, predictions.class_probabilities
                )
                self.assertEqual(restored.sample_ids, predictions.sample_ids)


if __name__ == "__main__":
    unittest.main()
