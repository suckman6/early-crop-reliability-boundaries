"""Generate the locked-data class-filter figure at native single-column size.

This R12.6-T script reads the archived Stage 36 aggregate artifacts only. It
does not rewrite tables, alter class ordering, or access parcel-level/test
labels.
"""

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROOT = Path(__file__).resolve().parents[1]
INPUT = PROJECT_ROOT / "artifacts" / "stage36" / "output_class_filter_feasibility"
FIGURES = ROOT / "figures"

candidates = pd.read_csv(INPUT / "candidate_feasibility.csv")
cells = pd.read_csv(INPUT / "output_class_cells.csv")

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7.5,
        "axes.labelsize": 7.5,
        "xtick.labelsize": 7.0,
        "ytick.labelsize": 7.0,
        "legend.fontsize": 7.0,
        "axes.linewidth": 0.7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }
)

colors = ("#2F5D8A", "#C65D3B", "#4E8B72")
markers = ("o", "s", "^")
threshold_ticks = sorted(candidates["threshold"].unique())

# Native single-column asset with a compact height while retaining readable
# class labels in the heat map.
fig, axes = plt.subplots(
    1,
    3,
    figsize=(3.35, 3.35),
    gridspec_kw={"width_ratios": (0.95, 0.75, 1.70), "wspace": 0.52},
)
fig.subplots_adjust(left=0.18, right=0.98, bottom=0.20, top=0.96)

ax = axes[0]
for ((seed, group), color, marker) in zip(candidates.groupby("seed"), colors, markers):
    ax.plot(
        group["threshold"],
        100 * group["simultaneous_usable_coverage_lower"],
        marker=marker,
        color=color,
        linewidth=1.1,
        markersize=3.5,
        label=f"Seed {seed}",
    )
ax.axhline(20, color="#555555", linestyle="--", linewidth=0.8)
ax.set_xlabel("Global threshold")
ax.set_ylabel("Usable coverage LCB (%)")
ax.set_xticks(threshold_ticks, [f"{value:g}" for value in threshold_ticks])
plt.setp(ax.get_xticklabels(), rotation=60, ha="right", rotation_mode="anchor")
ax.set_ylim(0, 30)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#E2E2E2", linewidth=0.5)
ax.legend(frameon=False, fontsize=6.5)
ax.text(-0.22, 1.03, "a", transform=ax.transAxes, fontweight="bold", fontsize=8)

ax = axes[1]
offsets = (-0.0025, 0.0, 0.0025)
for ((seed, group), color, marker, offset) in zip(candidates.groupby("seed"), colors, markers, offsets):
    ax.plot(
        group["threshold"] + offset,
        group["certified_output_class_count"],
        marker=marker,
        color=color,
        linewidth=1.0,
        markersize=3.8,
    )
ax.set_xlabel("Global threshold")
ax.set_ylabel("Certified labels")
ax.set_xticks(threshold_ticks, [f"{value:g}" for value in threshold_ticks])
plt.setp(ax.get_xticklabels(), rotation=60, ha="right", rotation_mode="anchor")
ax.set_ylim(0, 4)
ax.set_yticks(range(5))
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#E2E2E2", linewidth=0.5)
ax.text(-0.25, 1.03, "b", transform=ax.transAxes, fontweight="bold", fontsize=8)

ax = axes[2]
tau = cells[np.isclose(cells["threshold"], 0.85)]
matrix = tau.pivot(index="class_name", columns="seed", values="risk_upper")
order = matrix.max(axis=1).sort_values().index
matrix = matrix.loc[order]
mesh = ax.pcolormesh(
    np.arange(4),
    np.arange(len(order) + 1),
    100 * matrix.to_numpy(),
    cmap="magma_r",
    vmin=0,
    vmax=100,
    shading="flat",
    rasterized=False,
)
short_names = {
    "fallow land": "Fallow",
    "alfalfa": "Alfalfa",
    "spring common soft wheat": "Spring wheat",
    "fresh vegetables": "Vegetables",
    "rye": "Rye",
    "oats": "Oats",
    "potatoes": "Potatoes",
    "buckwheat": "Buckwheat",
    "beans": "Beans",
    "winter barley": "Winter barley",
    "spring barley": "Spring barley",
    "clover": "Clover",
    "grain maize": "Maize",
    "peas": "Peas",
    "winter rapeseed": "Winter rapeseed",
    "winter common soft wheat": "Winter wheat",
}
ax.set_xticks(np.arange(3) + 0.5, ["Seed 0", "Seed 1", "Seed 2"], fontsize=6.5)
ax.set_yticks(
    np.arange(len(order)) + 0.5,
    [short_names.get(str(name).lower(), str(name)) for name in order],
)
ax.set_ylim(len(order), 0)
ax.set_xlabel(r"Risk UCB at $\tau=0.85$")
ax.text(-0.2, 1.03, "c", transform=ax.transAxes, fontweight="bold", fontsize=8)
cbar = fig.colorbar(mesh, ax=ax, fraction=0.05, pad=0.04)
cbar.set_label("Risk upper bound (%)", fontsize=7.0)
cbar.ax.tick_params(labelsize=7.0)
if cbar.solids is not None:
    cbar.solids.set_rasterized(False)

FIGURES.mkdir(parents=True, exist_ok=True)
fig.savefig(FIGURES / "class_filter_feasibility_s3.pdf", bbox_inches="tight", pad_inches=0.02)
fig.savefig(FIGURES / "class_filter_feasibility_s3.png", dpi=600, bbox_inches="tight", pad_inches=0.02)
fig.savefig(FIGURES / "class_filter_feasibility_s3.svg", bbox_inches="tight", pad_inches=0.02)
fig.savefig(FIGURES / "class_filter_feasibility_s3.tiff", dpi=600, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
