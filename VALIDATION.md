# Assembly validation

## E1. Frozen configuration integrity

`configs/experiments/stage29_fresh_calibration_protocol.json`

```text
SHA-256  1F0D24810F8B24F6A7516739B7183A9DB6A331BAE79433497FF841113EB91404
Expected 1F0D24810F8B24F6A7516739B7183A9DB6A331BAE79433497FF841113EB91404
Result   MATCH
```

`.gitattributes` contains `*.json -text` and `*.csv  -text`.

## E2. Package size

The final file count and physical size are recorded in `MANIFEST.md` after all generated reports have been added. The assembled directory is below the 5 MiB limit.

## E3. Restricted-content absence

No `*.pt`, `*.h5`, `*.npz`, `*.parquet`, or `*.tif` file is present. No physical `data/` or `artifacts/` directory is present. Relative interfaces retained in released scripts are described in `MISSING_DEPENDENCIES.md`; they do not represent included data or artifacts.

## E4. Required public content

All 16 required A1--A2 Python files are present, as are all three environment/package files. The package contains 50 configuration JSON files (the actual repository count; the requested planning count of 54 was not present), 8 paper scripts, 6 aggregate CSV files, and 84 test-source files.

## E5. Plot-script attempt

Attempted command, from this public package:

```powershell
<available-python> paper/ijaeog_r12/scripts/make_calibration_frontier.py
```

Result: not independently runnable in the available runtime because `matplotlib` is not installed:

```text
ModuleNotFoundError: No module named 'matplotlib'
```

No figure output was generated. This is a dependency-only blocker, not an absent data-input blocker: `make_calibration_frontier.py` reads the included `source_data/calibration_candidates.csv`. Install Matplotlib as shown in `README.md`, then rerun the command.

## Sensitive-information scan

The release checker performs the current text and path scan. Intentional relative data interfaces are not bundled content and are described in `MISSING_DEPENDENCIES.md`.
