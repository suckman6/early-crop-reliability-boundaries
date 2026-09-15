import numpy as np

from rcecrop.stage36_class_filter_feasibility import assess_output_class_filter


def test_output_class_filter_conditions_on_emitted_label():
    samples = 4000
    probabilities = np.zeros((samples, 1, 2), dtype=float)
    probabilities[:, 0, 0] = 0.99
    probabilities[:, 0, 1] = 0.01
    targets = np.zeros(samples, dtype=np.int64)
    targets[:20] = 1
    cells, candidates, delta = assess_output_class_filter(
        probabilities,
        targets,
        ["3301010101", "3301010102"],
        [0.9],
        risk_target=0.1,
        minimum_coverage=0.2,
        confidence=0.95,
    )
    first = cells[0]
    assert first["emitted_count"] == samples
    assert first["errors"] == 20
    assert first["risk_certified"]
    assert not cells[1]["risk_certified"]
    assert candidates[0]["certified_output_classes"] == "3301010101"
    assert candidates[0]["feasible"]
    assert np.isclose(delta, 0.05 / 4)


def test_filter_does_not_certify_zero_emissions():
    probabilities = np.tile(np.array([[[0.99, 0.01]]]), (200, 1, 1))
    targets = np.zeros(200, dtype=np.int64)
    cells, candidates, _ = assess_output_class_filter(
        probabilities,
        targets,
        ["3301010101", "3301010102"],
        [0.9],
        risk_target=0.1,
        minimum_coverage=0.9,
        confidence=0.95,
    )
    assert cells[1]["emitted_count"] == 0
    assert not cells[1]["risk_certified"]
    assert candidates[0]["certified_output_class_count"] == 1


def test_simultaneous_coverage_is_sum_of_disjoint_cell_bounds():
    probabilities = np.zeros((4000, 1, 2), dtype=float)
    probabilities[:2000, 0] = [0.99, 0.01]
    probabilities[2000:, 0] = [0.01, 0.99]
    targets = np.repeat([0, 1], 2000)
    cells, candidates, _ = assess_output_class_filter(
        probabilities,
        targets,
        ["3301010101", "3301010102"],
        [0.9],
        risk_target=0.1,
        minimum_coverage=0.9,
        confidence=0.95,
    )
    expected = sum(row["coverage_contribution_lower"] for row in cells)
    assert candidates[0]["simultaneous_usable_coverage_lower"] == expected
    assert candidates[0]["feasible"]
