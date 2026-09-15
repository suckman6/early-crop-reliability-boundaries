# Public-release scope policy

This policy governs only the public code repository. The manuscript's journal
declarations (competing interests, funding, data availability, and authorship)
are separate author decisions.

## A.1 Allowed publication scope (ALLOWLIST)

Files not covered by this allowlist must not enter the public release.

| Category | Allowed paths | Rationale |
| --- | --- | --- |
| Protocol and evaluation core | `src/rcecrop/{__init__,policy,risk,selective_risk,selective_evaluation,contracts,matched_selective,bpp_policy,evaluation,io,config,observation_state}.py` | Core implementation of the published protocol. |
| Paper-number stage scripts | `src/rcecrop/stage{29_make_fresh_calibration_split,30_calibrate_selective_stopping,31_evaluate_frozen_policy,35_diagnostics,36_class_filter_feasibility}.py` | Scripts underlying reported tables and diagnostics. |
| Frozen protocol configuration | `configs/experiments/*.json` | Protocol definitions, subject to the local-path scan. |
| Figure reproduction scripts | `paper/ijaeog_r12/scripts/*.py` | Plotting from aggregate inputs only. |
| Aggregate source data | `paper/ijaeog_r12/source_data/*.csv` | Aggregate values; no parcel-level records. |
| Tests | `tests/*.py` confirmed runnable within this release | Regression checks for released modules only. |
| Environment and package metadata | `environment-local.yml`, `environment-elects-local.yml`, `pyproject.toml` | Reproducibility metadata. |
| Governance and user documentation | `README.md`, `LICENSE`, `CITATION.cff`, `.gitignore`, `.gitattributes`, `MANIFEST.md`, `MISSING_DEPENDENCIES.md`, `VALIDATION.md`, `PUBLISH_POLICY.md` | Scope, installation, and governance information. |
| Release validation | An allowlist checker maintained outside this release | Verifies the package before publication; it is not itself published. |
| Empty figure directory marker | `paper/ijaeog_r12/figures/.gitkeep` | Retains the documented output location without publishing figures. |

## A.2 Prohibited publication scope (DENYLIST)

| Category | Prohibited pattern | Rationale |
| --- | --- | --- |
| Licensed data | `data/**` | Third-party dataset licences. |
| Models and parcel-level artefacts | `artifacts/**`, `*.pt`, `*.h5`, `*.npz`, `*.parquet`, `*.tif` | Size and protected-test boundary. |
| Protected test material | Any parcel-level test labels or predictions | Evidence discipline. |
| Internal records | `reports/**`, `docs/**`, `*change_log*`, `*audit*.md`, `CITATION_AUDIT.*`, `SENSITIVE_SCAN.md` | Internal process material. |
| Upstream code | `third_party/**` | Not project-owned code. |
| Build and presentation residues | `r9_*/`, `submission*/`, `template_render/`, `ppt_assets/`, `tmp/`, `.tmp/`, `__pycache__/`, `.pytest_cache/`, `.tectonic-cache/`, `.idea/`, `.agents/`, `.aris/`, `.image2ppt_deps/` | Not release deliverables. |
| Other manuscript formats | `*.pptx`, `*.docx`, `*.zip` | Not code-repository content. |
| Internal process files | `HANDOFF.md`, `PROJECT_LOG.md`, `AGENTS.md` | Internal workflow records. |
| Local environment data | Any content containing a Windows absolute path, local username, or real email address | Privacy and portability. |
| Credentials | Any content containing credentials or secret-like values | Security. |

## A.3 Three-layer protection

1. **Independent repository.** Only `release/rcsl-public/` is versioned for public release; the monorepo root is never used for publication.
2. **Allowlist checker.** Run an allowlist checker maintained outside this release before every release and before committing.
3. **Defensive ignore rules.** `.gitignore` repeats the denylist for accidental-file protection; it does not replace the checker.

The external checker does not content-scan this policy document because the policy necessarily spells out the forbidden-pattern vocabulary. The policy remains path-allowlisted and is reviewed separately.

## A.4 Change process

Every new file must: (1) fall within an A.1 category; (2) pass the checker; and (3) be recorded in `MANIFEST.md`. Files that fail must be moved, not deleted, to `reports/release_quarantine/` outside this release repository.
