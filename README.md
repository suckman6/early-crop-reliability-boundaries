# Reliability Boundaries of Confidence-Based Early-Season Crop Mapping across Regions and Years

This repository releases the protocol and evaluation code used to study when an early-season parcel-level crop prediction may be released automatically under a predeclared risk--coverage contract.

## What this release contains

The public package contains the selective-release policy, finite-candidate risk and coverage calculations, matched-score evaluation utilities, frozen JSON configurations, paper plotting scripts, aggregate plotting tables, and the project test suite. It is deliberately a protocol-and-evaluation release rather than a redistribution of the full experimental environment.

The package does **not** contain raw satellite data, parcel labels, parcel-level predictions, checkpoints, or protected-test predictions. These materials are excluded because of dataset licences, large size, and the need to preserve the protected-test boundary. Requests for any non-public derived asset should be discussed with the prospective maintainers after the applicable source-dataset licence has been reviewed; this release itself cannot grant access to third-party data.

## Installation

```powershell
conda env create -f environment-local.yml
conda activate rcecrop
python -m pip install -e .
```

The plotting scripts additionally require Matplotlib, which is intentionally not added to the frozen environment files:

```powershell
conda install -c conda-forge matplotlib
```

## Released-test status

The public package retains 15 tests that exercise released modules. In the recorded release check, `pytest -q` completed with **50 passed** and **3 skipped**. Sixty-nine tests that require intentionally excluded data adapters, upstream baselines, or non-released stage modules were moved to the internal quarantine; they are not represented as runnable public tests.

## Frozen protocol configuration

The paper cites `configs/experiments/stage29_fresh_calibration_protocol.json`. Its required SHA-256 digest is:

```text
1F0D24810F8B24F6A7516739B7183A9DB6A331BAE79433497FF841113EB91404
```

Verify the copied bytes with:

```powershell
(Get-FileHash configs/experiments/stage29_fresh_calibration_protocol.json -Algorithm SHA256).Hash
```

`.gitattributes` disables text conversion for JSON and CSV files so that a Git checkout does not change the frozen configuration bytes.

## Reproducing public plotting assets

Run commands from the repository root. Each command writes its output to `paper/ijaeog_r12/figures/`.

| Command | Public input | Status in this release |
| --- | --- | --- |
| `python paper/ijaeog_r12/scripts/make_calibration_frontier.py` | `source_data/calibration_candidates.csv` | Independently runnable |
| `python paper/ijaeog_r12/scripts/make_figure_03.py` | `source_data/final_test_stopping_counts.csv` | Independently runnable |
| `python paper/ijaeog_r12/scripts/make_seed_stability.py` | `source_data/stage34_multiseed_stopping_distribution.csv`, `source_data/stage34_multiseed_test_summary.csv` | Independently runnable |
| `python paper/ijaeog_r12/scripts/make_stage36_feasibility.py` | Archived Stage 36 artifact paths hard-coded in the script | Not independently runnable; see `MISSING_DEPENDENCIES.md` |
| `python paper/ijaeog_r12/scripts/gen_fig_stage97_evidence.py` | Archived Stage 30/31/75/95 aggregate JSON artifacts | Not independently runnable; see `MISSING_DEPENDENCIES.md` |

`check_chars.py`, `check_pdf_holes.py`, and `verify_refs.py` are production utilities. The latter queries Crossref and therefore requires network access when it is used.

## Data access

No original data are redistributed. Obtain each dataset from its official provider and comply with its licence and access requirements:

- [EuroCropsML](https://github.com/dida-do/eurocropsml)
- [TinyEuroCrops](https://mediatum.ub.tum.de/node?id=1615987)
- [AgriSen-COG](https://github.com/tselea/agrisen-cog)
- [S4A](https://github.com/Orion-AI-Lab/S4A)

The repository contains neither parcel-level test labels nor protected-test predictions.

## Scope and limitations

The released numerical protocol can be reused with new, lawfully obtained data. Running the original stage scripts end to end requires data adapters, licensed data, trained checkpoints, and/or stored prediction exports that are intentionally excluded here. `MISSING_DEPENDENCIES.md` records these interfaces explicitly rather than silently substituting data or weakening the protected-test design.

`paper/ijaeog_r12/` is retained as a historical development/provenance directory from an earlier manuscript version and does not represent the current article title.

## Citation and licence

Use `CITATION.cff` to cite the software and its associated manuscript; it records the current article title, author order, release date, and repository URL. The MIT license text retains a copyright-holder placeholder pending the authors' explicit choice.
