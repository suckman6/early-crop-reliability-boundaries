import os
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "source_data"
os.chdir(ROOT)
FIGURES = Path("figures")

distribution = pd.read_csv(DATA / "stage34_multiseed_stopping_distribution.csv")
summary = pd.read_csv(DATA / "stage34_multiseed_test_summary.csv")

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 7.5,
        "axes.labelsize": 7.5,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5,
        "axes.linewidth": 0.7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)

colors = ("#3B5B92", "#D65F4A", "#4C956C")
seeds = sorted(summary["seed"].astype(int).unique())
fig, axes = plt.subplots(
    1,
    2,
    figsize=(3.35, 3.85),
    gridspec_kw={"width_ratios": (1.35, 1.0), "wspace": 0.50},
)
fig.subplots_adjust(left=0.17, right=0.99, bottom=0.22, top=0.84)

ax = axes[0]
x = np.arange(len(distribution))
width = 0.24
offsets = np.linspace(-width, width, len(seeds))
for offset, seed, color in zip(offsets, seeds, colors):
    ax.bar(
        x + offset,
        distribution[f"seed{seed}_percent"],
        width,
        color=color,
        label=f"Seed {seed}",
    )
ax.set_xticks(x, distribution["category"], rotation=35, ha="right")
ax.set_ylabel("Test parcels (%)")
ax.set_ylim(0, 66)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#D9D9D9", linewidth=0.5, alpha=0.7)
ax.set_axisbelow(True)
ax.text(-0.13, 1.03, "a", transform=ax.transAxes, fontweight="bold", fontsize=8)

ax = axes[1]
metric_labels = ["Coverage", "Risk", "Accepted acc.", "Accepted macro F1"]
metric_columns = [
    "automatic_coverage",
    "automatic_risk",
    "automatic_accuracy",
    "automatic_macro_f1",
]
y = np.arange(len(metric_labels))
metric_values = [
    100 * summary.loc[summary["seed"] == seed, metric_columns].iloc[0].to_numpy()
    for seed in seeds
]
for yi, values in zip(y, np.asarray(metric_values).T):
    ax.plot([values.min(), values.max()], [yi, yi], color="#B7B7B7", linewidth=1.2, zorder=1)
for seed, values, color in zip(seeds, metric_values, colors):
    ax.scatter(values, y, color=color, s=28, label=f"Seed {seed}", zorder=2)
ax.set_yticks(y, metric_labels)
ax.invert_yaxis()
ax.set_xlabel("Metric value (%)")
ax.set_xlim(0, 100)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color="#D9D9D9", linewidth=0.5, alpha=0.7)
ax.set_axisbelow(True)
ax.text(-0.18, 1.03, "b", transform=ax.transAxes, fontweight="bold", fontsize=8)

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    frameon=False,
    ncol=3,
    loc="upper center",
    bbox_to_anchor=(0.50, 0.985),
    fontsize=6.5,
    handlelength=1.2,
    columnspacing=0.45,
)

FIGURES.mkdir(parents=True, exist_ok=True)
fig.savefig(FIGURES / "seed_stability_s1.pdf", bbox_inches="tight", pad_inches=0.02)
fig.savefig(
    FIGURES / "seed_stability_s1.png",
    dpi=600,
    bbox_inches="tight",
    pad_inches=0.02,
)
plt.close(fig)
