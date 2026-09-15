"""Create Figure 3 from frozen Stage 31 counts copied into source_data/."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "source_data" / "final_test_stopping_counts.csv"
OUTPUT_PDF = ROOT / "figures" / "figure_03_stopping_distribution.pdf"
OUTPUT_PNG = ROOT / "figures" / "figure_03_stopping_distribution.png"


def main() -> None:
    with INPUT.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    labels = [row["disposition"] for row in rows]
    display_labels = [
        "15 Apr", "15 May", "15 Jun", "15 Jul", "15 Aug", "15 Sep", "Deferred"
    ]
    values = [float(row["fraction_percent"]) for row in rows]
    counts = [int(row["count"]) for row in rows]
    colors = ["#2A6FBB"] * 6 + ["#7A7A7A"]

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 7.5,
            "axes.labelsize": 7.5,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    # Native single-column asset; the slightly taller canvas preserves space
    # for the six date annotations and the deferred count.
    figure, axis = plt.subplots(figsize=(3.35, 2.05), constrained_layout=True)
    bars = axis.bar(display_labels, values, color=colors, width=0.68, edgecolor="white", linewidth=0.8)
    axis.set_ylabel("Fraction of all final-test parcels (%)")
    axis.set_ylim(0, 66)
    axis.set_yticks(range(0, 61, 10))
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color="#D9D9D9", linewidth=0.6)
    axis.set_axisbelow(True)
    axis.tick_params(axis="x", labelrotation=0, pad=3)
    # Separate the two nearly equal April/May annotations at native width.
    x_offsets = (-0.12, 0.12, 0.0, 0.0, 0.0, 0.0, 0.0)
    for bar, value, count, x_offset in zip(bars, values, counts, x_offsets):
        axis.text(
            bar.get_x() + bar.get_width() / 2 + x_offset,
            value + 1.0,
            f"{value:.2f}%\n(n={count:,})",
            ha="center",
            va="bottom",
            fontsize=6.5,
            linespacing=1.05,
            clip_on=False,
        )
    figure.savefig(OUTPUT_PDF, bbox_inches="tight", pad_inches=0.02)
    figure.savefig(OUTPUT_PNG, dpi=600, bbox_inches="tight", pad_inches=0.02)


if __name__ == "__main__":
    main()
