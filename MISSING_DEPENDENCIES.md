# Deliberately excluded dependencies

This document describes interfaces that are unavailable in the public package. Nothing listed here is silently substituted or reconstructed.

| Public script or test group | Missing dependency | Effect | Recommended public documentation/interface |
| --- | --- | --- | --- |
| `src/rcecrop/stage29_make_fresh_calibration_split.py` | Excluded `rcecrop.eurocropsml` adapter and licensed EuroCropsML extraction under `data/eurocropsml/extracted` | Cannot create the original calibration split independently | Document the expected input manifest and let a user supply a licensed local data adapter. |
| `src/rcecrop/stage30_calibrate_selective_stopping.py` | Six per-cutoff calibration folders containing `run_metadata.json` and `calibration_predictions.npz` | Cannot reproduce the original selected threshold without user-provided calibration exports | Publish an input schema for aggregate or user-owned calibration predictions; do not release protected predictions. |
| `src/rcecrop/stage31_evaluate_frozen_policy.py` | Excluded `rcecrop.eurocropsml`, source normalisation arrays, target-adapted checkpoints, raw data, and protected test role | Intentionally cannot recreate the protected blind-test evaluation | Keep the protected role closed; provide only an interface specification and authorised evaluation procedure. |
| `src/rcecrop/stage35_diagnostics.py` | Archived test prediction exports (`.npz`) | Cannot regenerate post-hoc diagnostics | Provide aggregate diagnostic tables where permitted; this release does not publish parcel predictions. |
| `src/rcecrop/stage36_class_filter_feasibility.py` | Archived Stage 36 calibration prediction exports | Cannot rebuild the exploratory feasibility calculation | Use the included aggregate CSV files for transparent inspection, or document a user-supplied input contract. |
| `paper/ijaeog_r12/scripts/make_stage36_feasibility.py` | Hard-coded `artifacts/stage36/output_class_filter_feasibility` path | Cannot run in a clean public checkout despite related aggregate CSV files being present | Refactor only in a future authorised release to accept CSV arguments; no source logic is changed here. |
| `paper/ijaeog_r12/scripts/gen_fig_stage97_evidence.py` | Stage 30, 31, 75, and 95 archived aggregate JSON files | Cannot regenerate the evidence figures | Document the JSON schema or release approved aggregates if licence and protected-test constraints permit. |
| Full `tests/` collection | Many tests import intentionally excluded data adapters, baseline training code, exploratory stages, or artifacts | The complete test suite is not expected to collect in this trimmed package | Run protocol-core tests selectively; maintainers should add an explicit public-test marker before a public release. |

## Python-package note

`environment-local.yml` and `pyproject.toml` support the protocol core. The public plotting scripts require `matplotlib`, which is not declared in those frozen files; install it separately as documented in `README.md`. `verify_refs.py` additionally requires network access to Crossref.
