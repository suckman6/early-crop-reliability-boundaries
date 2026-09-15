"""Render the fixed-candidate calibration frontier from frozen Stage 30 values."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "source_data" / "calibration_candidates.csv"


def main() -> None:
    with INPUT.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    x = [100 * float(row["coverage_lower"]) for row in rows]
    y = [100 * float(row["risk_upper"]) for row in rows]
    thresholds = [float(row["threshold"]) for row in rows]

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 7.5,
            "axes.labelsize": 7.5,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    # Author the asset at approximately its final single-column physical size.
    figure, axis = plt.subplots(figsize=(3.35, 2.62), constrained_layout=True)
    axis.add_patch(Rectangle((20, 0), 35, 10, facecolor="#DCEFE2", edgecolor="none", zorder=0))
    axis.plot(x, y, color="#5D6D7E", linewidth=1.2, zorder=1)
    for row, xi, yi, tau in zip(rows, x, y, thresholds):
        selected = row["selected"].lower() == "true"
        certified = row["certified"].lower() == "true"
        color = "#18794E" if certified else "#B23A2B"
        marker = "*" if selected else "o"
        size = 150 if selected else 48
        axis.scatter(xi, yi, s=size, marker=marker, color=color, edgecolor="white", linewidth=0.7, zorder=3)
        offset = (5, 7) if tau != 0.975 else (5, -14)
        axis.annotate(f"$\\tau={tau:g}$", (xi, yi), xytext=offset, textcoords="offset points", fontsize=7)
    axis.axhline(10, color="#B23A2B", linestyle="--", linewidth=1, label="Risk target (10%)")
    axis.axvline(20, color="#2A6FBB", linestyle=":", linewidth=1, label="Coverage target (20%)")
    axis.set_xlabel("Coverage lower bound (%)")
    axis.set_ylabel("Risk upper bound (%)")
    axis.set_xlim(18, 47)
    axis.set_ylim(0, 13)
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(color="#E4E4E4", linewidth=0.6)
    axis.set_axisbelow(True)
    axis.legend(loc="upper left", frameon=False, fontsize=6.5)
    axis.text(0.98, 0.04, "Certified region", transform=axis.transAxes, ha="right", va="bottom", fontsize=6.5, color="#18794E")
    figure.savefig(ROOT / "figures" / "figure_02_calibration_frontier.pdf", bbox_inches="tight", pad_inches=0.02)
    figure.savefig(ROOT / "figures" / "figure_02_calibration_frontier.png", dpi=600, bbox_inches="tight", pad_inches=0.02)


if __name__ == "__main__":
    main()
