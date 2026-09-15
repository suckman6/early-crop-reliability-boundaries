import numpy as np

from rcecrop.stage35_diagnostics import analyse, wilson_interval


def _write_run(path, labels, stops):
    targets = np.array([0, 0, 1, 1])
    np.savez_compressed(
        path,
        names=np.array(["a", "b", "c", "d"]),
        targets=targets,
        labels=np.array(labels),
        stop_indices=np.array(stops),
        full_sequence_labels=np.array(labels),
    )


def test_wilson_interval_handles_empty_and_observed_counts():
    assert all(np.isnan(wilson_interval(0, 0)))
    lower, upper = wilson_interval(1, 10)
    assert 0.0 < lower < 0.1 < upper < 1.0


def test_analysis_reports_true_class_and_date_conditionals(tmp_path):
    paths = []
    for seed in range(3):
        path = tmp_path / f"seed{seed}.npz"
        _write_run(path, [0, 1, 1, 1], [0, -1, 1, 1])
        paths.append((seed, path))
    output = analyse(paths, ["3301010101", "3301010102"])
    first_class = output["class"][0]
    assert first_class["test_support"] == 2
    assert first_class["automatic_count"] == 1
    assert first_class["automatic_coverage"] == 0.5
    assert first_class["automatic_errors"] == 0
    second_date = output["date"][1]
    assert second_date["automatic_count"] == 2
    assert second_date["automatic_errors"] == 0
    deferred = [row for row in output["class_date"] if row["seed"] == 0 and row["class_index"] == 0 and row["disposition"] == "Deferred"]
    assert deferred[0]["count"] == 1


def test_analysis_rejects_misaligned_runs(tmp_path):
    paths = []
    for seed in range(3):
        path = tmp_path / f"seed{seed}.npz"
        _write_run(path, [0, 1, 1, 1], [0, -1, 1, 1])
        if seed == 2:
            with np.load(path) as data:
                values = {key: data[key] for key in data.files}
            values["names"] = values["names"][::-1]
            np.savez_compressed(path, **values)
        paths.append((seed, path))
    try:
        analyse(paths, ["3301010101", "3301010102"])
    except ValueError as error:
        assert "parcel-for-parcel aligned" in str(error)
    else:
        raise AssertionError("misalignment was not rejected")
