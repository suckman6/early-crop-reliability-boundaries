# Public release manifest

This manifest records the intentional public boundary after policy enforcement. The package contains protocol code and aggregate reproduction inputs only; it contains no raw data, parcel-level material, checkpoints, or protected-test predictions.

## Package statistics

- Files: **109**
- Total size: **283,875 bytes**
- Largest permitted file: **26,778 bytes** (`paper/ijaeog_r12/source_data/stage36_output_class_cells.csv`)
- Policy status at assembly: **0 violations; 0 unclassified files**.
- Released tests: **15 files; 50 passed; 3 skipped**.
- Tests isolated because they require excluded modules or data interfaces: **69 files**.

## Frozen protocol hash

`configs/experiments/stage29_fresh_calibration_protocol.json` SHA-256:

```text
1F0D24810F8B24F6A7516739B7183A9DB6A331BAE79433497FF841113EB91404
```

`.gitattributes` marks JSON and CSV files as `-text` to preserve these bytes across checkout.

## File-by-file allowlist record

| Path | Bytes | Category | Policy basis |
| --- | ---: | --- | --- |
| `.gitattributes` | 26 | Governance/package metadata | A.1 governance/package metadata |
| `.gitignore` | 308 | Governance/package metadata | A.1 governance/package metadata |
| `CITATION.cff` | 369 | Governance/package metadata | A.1 governance/package metadata |
| `configs/experiments/stage13_eurocrops_temporal_protocol.json` | 1568 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage20_eurocropsml_transfer_protocol.json` | 1954 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage29_fresh_calibration_protocol.json` | 2423 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage37_tinyeurocrops_external_validation_gate.json` | 3643 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage38_tinyeurocrops_generic_hcat8_protocol.json` | 2398 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage39_tinyeurocrops_hdf5_preflight.json` | 1017 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage40_tinyeurocrops_generic_hcat8_protocol.json` | 2476 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage41_tinyeurocrops_scale_preprocessing.json` | 1417 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage42_tinyeurocrops_reader_preflight.json` | 1175 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage44_tinyeurocrops_target_fit.json` | 689 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage45_tinyeurocrops_risk_calibration_export.json` | 625 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage46_tinyeurocrops_selective_policy.json` | 899 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage46b_tinyeurocrops_negative_replication.json` | 785 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage61_matched_selective_comparator.json` | 2175 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage62b_spatial_block_calibration_protocol.json` | 982 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage62d_matched_baseline_contract_protocol.json` | 1158 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage63_agrisen_external_data_gate.json` | 2191 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage64_agrisen_role_freeze.json` | 1579 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage65_agrisen_external_protocol.json` | 2169 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage66_agrisen_external_calibration.json` | 1224 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage69_agrisen_spatial_role_freeze.json` | 1765 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage69b_agrisen_multitarget_role_freeze.json` | 2105 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage70_agrisen_multitarget_temporal_protocol.json` | 2146 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage71_external_temporal_calibration.json` | 908 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage72_external_temporal_blind_test.json` | 774 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage75_denmark_external_temporal_blind.json` | 1366 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage77_sen4agrinet_completed_tile_audit.json` | 861 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage78_s4a_catalonia_2020_resumable_download.json` | 715 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage78_s4a_resumable_download.json` | 884 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage79_s4a_catalonia_2020_tile_audit.json` | 748 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage79_s4a_unified_tile_audit.json` | 613 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage80_s4a_catalonia_2020_reader_preflight.json` | 630 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage80_s4a_reader_preflight.json` | 538 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage81_s4a_catalonia_2020_temporal_coverage.json` | 557 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage81_s4a_label_time_protocol.json` | 1950 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage82_s4a_five_class_protocol.json` | 1006 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage83_s4a_catalonia_support_audit.json` | 1073 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage84_s4a_catalonia_label_support_audit.json` | 419 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage85_s4a_catalonia_prefix_audit.json` | 552 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage86_s4a_catalonia_feature_materialization.json` | 678 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage87_s4a_catalonia_role_freeze.json` | 479 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage88_s4a_catalonia_source_training.json` | 1226 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage89_s4a_catalonia_target_fit_gate.json` | 361 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage90_s4a_catalonia_three_role_freeze.json` | 649 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage91_mainline_evidence_freeze.json` | 686 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage91_s4a_catalonia_source_training.json` | 1271 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage92_s4a_catalonia_target_fit.json` | 1137 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage93_s4a_catalonia_calibration_predictions.json` | 803 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage94_s4a_catalonia_selective_calibration.json` | 620 | Frozen protocol configuration | A.1 frozen configuration |
| `configs/experiments/stage95_s4a_catalonia_protected_blind_test.json` | 1131 | Frozen protocol configuration | A.1 frozen configuration |
| `environment-elects-local.yml` | 537 | Governance/package metadata | A.1 governance/package metadata |
| `environment-local.yml` | 132 | Governance/package metadata | A.1 governance/package metadata |
| `LICENSE` | 1075 | Governance/package metadata | A.1 governance/package metadata |
| `MANIFEST.md` | 30070 | Governance/package metadata | A.1 governance/package metadata |
| `MISSING_DEPENDENCIES.md` | 3105 | Governance/package metadata | A.1 governance/package metadata |
| `paper/ijaeog_r12/figures/.gitkeep` | 0 | Figure-output marker | A.1 figure marker |
| `paper/ijaeog_r12/scripts/check_chars.py` | 697 | Figure reproduction script | A.1 figure script |
| `paper/ijaeog_r12/scripts/check_pdf_holes.py` | 1578 | Figure reproduction script | A.1 figure script |
| `paper/ijaeog_r12/scripts/gen_fig_stage97_evidence.py` | 10236 | Figure reproduction script | A.1 figure script |
| `paper/ijaeog_r12/scripts/make_calibration_frontier.py` | 2827 | Figure reproduction script | A.1 figure script |
| `paper/ijaeog_r12/scripts/make_figure_03.py` | 2525 | Figure reproduction script | A.1 figure script |
| `paper/ijaeog_r12/scripts/make_seed_stability.py` | 3195 | Figure reproduction script | A.1 figure script |
| `paper/ijaeog_r12/scripts/make_stage36_feasibility.py` | 5157 | Figure reproduction script | A.1 figure script |
| `paper/ijaeog_r12/scripts/verify_refs.py` | 7913 | Figure reproduction script | A.1 figure script |
| `paper/ijaeog_r12/source_data/calibration_candidates.csv` | 549 | Aggregate source data | A.1 aggregate data |
| `paper/ijaeog_r12/source_data/final_test_stopping_counts.csv` | 169 | Aggregate source data | A.1 aggregate data |
| `paper/ijaeog_r12/source_data/stage34_multiseed_stopping_distribution.csv` | 608 | Aggregate source data | A.1 aggregate data |
| `paper/ijaeog_r12/source_data/stage34_multiseed_test_summary.csv` | 753 | Aggregate source data | A.1 aggregate data |
| `paper/ijaeog_r12/source_data/stage36_candidate_feasibility.csv` | 2732 | Aggregate source data | A.1 aggregate data |
| `paper/ijaeog_r12/source_data/stage36_output_class_cells.csv` | 26778 | Aggregate source data | A.1 aggregate data |
| `PUBLISH_POLICY.md` | 4163 | Governance/package metadata | A.1 governance/package metadata |
| `pyproject.toml` | 547 | Governance/package metadata | A.1 governance/package metadata |
| `README.md` | 4691 | Governance/package metadata | A.1 governance/package metadata |
| `src/rcecrop/__init__.py` | 602 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/bpp_policy.py` | 6509 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/config.py` | 1262 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/contracts.py` | 6218 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/evaluation.py` | 3133 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/io.py` | 3816 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/matched_selective.py` | 6762 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/observation_state.py` | 5955 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/policy.py` | 8431 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/risk.py` | 6131 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/selective_evaluation.py` | 2116 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/selective_risk.py` | 3613 | Protocol/evaluation core | A.1 protocol core |
| `src/rcecrop/stage29_make_fresh_calibration_split.py` | 3089 | Paper-number stage script | A.1 stage script |
| `src/rcecrop/stage30_calibrate_selective_stopping.py` | 4764 | Paper-number stage script | A.1 stage script |
| `src/rcecrop/stage31_evaluate_frozen_policy.py` | 6785 | Paper-number stage script | A.1 stage script |
| `src/rcecrop/stage35_diagnostics.py` | 8702 | Paper-number stage script | A.1 stage script |
| `src/rcecrop/stage36_class_filter_feasibility.py` | 10639 | Paper-number stage script | A.1 stage script |
| `tests/helpers.py` | 961 | Runnable released test | A.1 confirmed released test |
| `tests/test_config.py` | 671 | Runnable released test | A.1 confirmed released test |
| `tests/test_contracts.py` | 2334 | Runnable released test | A.1 confirmed released test |
| `tests/test_evaluation.py` | 1835 | Runnable released test | A.1 confirmed released test |
| `tests/test_io.py` | 1837 | Runnable released test | A.1 confirmed released test |
| `tests/test_matched_selective.py` | 2385 | Runnable released test | A.1 confirmed released test |
| `tests/test_observation_policy.py` | 4164 | Runnable released test | A.1 confirmed released test |
| `tests/test_policy.py` | 4653 | Runnable released test | A.1 confirmed released test |
| `tests/test_prefix_reliability_loss.py` | 2705 | Runnable released test | A.1 confirmed released test |
| `tests/test_risk.py` | 7337 | Runnable released test | A.1 confirmed released test |
| `tests/test_selective_evaluation.py` | 1024 | Runnable released test | A.1 confirmed released test |
| `tests/test_selective_risk.py` | 2041 | Runnable released test | A.1 confirmed released test |
| `tests/test_stage30_calibration_metadata.py` | 733 | Runnable released test | A.1 confirmed released test |
| `tests/test_stage35_diagnostics.py` | 2108 | Runnable released test | A.1 confirmed released test |
| `tests/test_stage36_class_filter_feasibility.py` | 2147 | Runnable released test | A.1 confirmed released test |
| `VALIDATION.md` | 1971 | Governance/package metadata | A.1 governance/package metadata |

## Excluded and retained outside this release

- One internal process-record file was moved, not deleted, because it is outside the public reproducibility scope.
- Sixty-nine tests requiring intentionally excluded modules were moved, not deleted, to the internal release quarantine.
- Source data, models, parcel-level outputs, upstream third-party code, build residues, and internal workflow records remain outside this public repository under `PUBLISH_POLICY.md`.

## Pending author decisions

1. Confirm the licence and replace the copyright-holder placeholder, or choose another licence.
2. Complete `CITATION.cff` with the author list, release date, and canonical repository URL.
3. Decide whether manuscript source files should be published in a future release; they are not part of this code release.

