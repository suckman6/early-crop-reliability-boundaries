#!/usr/bin/env python3
"""Generate Stage 97 evidence figures from aggregate JSON artifacts only.

This script deliberately reads no parcel-level predictions.  Figure 4 uses
the five Estonia calibration assessments and the single frozen tau=0.85
blind-test result.  Figure 5 compares aggregate external boundary metrics.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PAPER_ROOT = Path(__file__).resolve().parents[1]
FIGURE_ROOT = PAPER_ROOT / "figures"

CALIBRATION_JSON = PROJECT_ROOT / "artifacts/stage30/selective_policy_seed0/calibration_result.json"
BLIND_JSON = PROJECT_ROOT / "artifacts/stage31/final_blind_test_seed0/test_result.json"
DENMARK_JSON = PROJECT_ROOT / "artifacts/stage75/denmark_external_temporal_blind_test/stage75_gate.json"
CATALONIA_JSON = PROJECT_ROOT / "artifacts/stage95/s4a_catalonia_protected_blind_test/stage95_protected_blind_test_summary.json"

COLORS = {
    "ink": "#263238",
    "blue": "#0072B2",
    "orange": "#D55E00",
    "green": "#009E73",
    "yellow": "#E69F00",
    "contract": "#4C956C",
    "grid": "#B0BEC5",
    "gray": "#6B7280",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def set_publication_style() -> None:
    plt.rcParams.update(
        {
            "font.family": ["Times New Roman", "Arial", "DejaVu Serif"],
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7.5,
            "axes.titlesize": 8.0,
            "axes.titleweight": "bold",
            "axes.labelsize": 7.5,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.5,
            "legend.frameon": False,
            "figure.dpi": 300,
            "savefig.dpi": 600,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.bbox": "tight",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.18,
            "grid.linewidth": 0.55,
            "lines.linewidth": 1.6,
            "lines.markersize": 4.5,
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_ROOT / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(FIGURE_ROOT / f"{stem}.svg", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(FIGURE_ROOT / f"{stem}.png", dpi=600, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(FIGURE_ROOT / f"{stem}.tiff", dpi=600, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def make_estonia_figure() -> None:
    calibration = load_json(CALIBRATION_JSON)
    blind = load_json(BLIND_JSON)
    assessments = calibration["assessments"]
    thresholds = np.array([row["threshold"] for row in assessments], dtype=float)
    risk_upper = 100.0 * np.array([row["risk_upper"] for row in assessments])
    coverage_lower = 100.0 * np.array([row["coverage_lower"] for row in assessments])
    selected = float(calibration["selected"]["threshold"])
    blind_risk = 100.0 * float(blind["selective_metrics"]["automatic_risk"])
    blind_coverage = 100.0 * float(blind["selective_metrics"]["automatic_coverage"])

    # Single-column figure: keep the two panels readable without reserving a
    # full-width float in the two-column manuscript layout.
    fig, axes = plt.subplots(1, 2, figsize=(3.55, 2.55), sharex=True)
    fig.subplots_adjust(left=0.16, right=0.99, bottom=0.30, top=0.82, wspace=0.52)
    for axis in axes:
        axis.axvline(selected, color=COLORS["gray"], lw=0.8, ls=":", zorder=0)
        axis.set_xticks(thresholds)
        axis.tick_params(axis="x", labelrotation=45, labelsize=6.5)
        for tick in axis.get_xticklabels():
            tick.set_ha("right")
        axis.set_xlim(0.785, 0.99)
        axis.grid(axis="y")

    risk_axis, coverage_axis = axes
    risk_axis.plot(thresholds, risk_upper, color=COLORS["blue"], marker="o", label="Calibration upper bound")
    risk_axis.axhline(10.0, color=COLORS["contract"], ls="--", lw=1.1, label="10% Risk target")
    risk_axis.scatter([selected], [blind_risk], color=COLORS["orange"], edgecolor="white", linewidth=0.8,
                      marker="*", s=115, zorder=5, label=r"Blind test ($\tau=0.85$ only)")
    risk_axis.annotate(f"{blind_risk:.2f}%", (selected, blind_risk), xytext=(7, -13),
                       textcoords="offset points", color=COLORS["orange"], fontsize=7)
    risk_axis.set_title("(a) Automatic-label risk", fontsize=8.0)
    risk_axis.set_ylabel("Risk (%)")
    risk_axis.set_ylim(0, 13.5)

    coverage_axis.plot(thresholds, coverage_lower, color=COLORS["blue"], marker="o", label="Calibration lower bound")
    coverage_axis.axhline(20.0, color=COLORS["contract"], ls="--", lw=1.1, label="20% Coverage target")
    coverage_axis.scatter([selected], [blind_coverage], color=COLORS["orange"], edgecolor="white", linewidth=0.8,
                          marker="*", s=115, zorder=5)
    coverage_axis.annotate(f"{blind_coverage:.2f}%", (selected, blind_coverage), xytext=(7, -13),
                           textcoords="offset points", color=COLORS["orange"], fontsize=7)
    coverage_axis.set_title("(b) Automatic coverage", fontsize=8.0)
    coverage_axis.set_ylabel("Coverage (%)")
    coverage_axis.set_ylim(0, 50)
    fig.supxlabel(r"Fixed threshold $\tau$", y=0.145, fontsize=7.5)

    handles = [
        Line2D([0], [0], color=COLORS["blue"], marker="o", lw=1.6, label="Calibration bound"),
        Line2D([0], [0], color=COLORS["contract"], ls="--", lw=1.1, label="Contract target"),
        Line2D([0], [0], color=COLORS["orange"], marker="*", lw=0, markersize=8, label=r"Blind test ($\tau=0.85$)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.025),
               handlelength=1.4, columnspacing=0.45, fontsize=6.2)
    save_figure(fig, "figure_03_estonia_calibration_vs_blind_singlecol")


def make_external_boundary_figure() -> None:
    blind = load_json(BLIND_JSON)
    denmark = load_json(DENMARK_JSON)["seed_metrics"]
    catalonia = load_json(CATALONIA_JSON)["seed_results"]
    routes = {
        "Estonia 2021": (
            [100.0 * blind["selective_metrics"]["automatic_coverage"]],
            [100.0 * blind["selective_metrics"]["automatic_risk"]],
            COLORS["blue"],
        ),
        "Denmark 2020": (
            [100.0 * denmark[str(seed)]["automatic_coverage"] for seed in range(3)],
            [100.0 * denmark[str(seed)]["automatic_label_risk"] for seed in range(3)],
            COLORS["orange"],
        ),
        "Catalonia 2020": (
            [100.0 * row["coverage"] for row in catalonia],
            [100.0 * row["empirical_risk"] for row in catalonia],
            COLORS["green"],
        ),
    }
    markers = ["o", "s", "^"]

    # Compact grouped bars follow the visual language of the paper's existing
    # seed/date diagnostics: small panel labels, fixed seed colours and no
    # decorative title. Estonia has only the seed-0 external reference; its
    # seed-1/2 slots remain blank rather than being treated as zeros.
    fig, axes = plt.subplots(1, 2, figsize=(3.50, 1.85), sharex=True)
    fig.subplots_adjust(left=0.12, right=0.99, bottom=0.34, top=0.86, wspace=0.34)
    route_names = ["Estonia\n2021", "Denmark\n2020", "Catalonia\n2020"]
    route_keys = ["Estonia 2021", "Denmark 2020", "Catalonia 2020"]
    seed_colors = [COLORS["blue"], COLORS["orange"], COLORS["green"]]
    x = np.arange(len(route_names), dtype=float)
    bar_width = 0.22

    risk_ax, coverage_ax = axes
    for axis, panel, ylabel, ylim, target in [
        (risk_ax, "a", "Automatic-label risk (%)", (0, 24), 10.0),
        (coverage_ax, "b", "Automatic coverage (%)", (0, 85), 20.0),
    ]:
        axis.text(-0.18, 1.07, panel, transform=axis.transAxes,
                  fontsize=8.0, fontweight="bold", va="bottom")
        axis.set_ylabel(ylabel, fontsize=6.5, labelpad=1)
        axis.set_ylim(*ylim)
        axis.set_xticks(x)
        axis.set_xticklabels(route_names, fontsize=5.3)
        axis.tick_params(axis="y", labelsize=5.5, length=2.5, width=0.6)
        axis.tick_params(axis="x", length=2.5, width=0.6)
        axis.grid(axis="y", color=COLORS["grid"], lw=0.45, alpha=0.55)
        axis.axhline(target, color=COLORS["contract"], ls="--", lw=0.8, zorder=0)
        axis.set_axisbelow(True)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

    for seed, color in enumerate(seed_colors):
        risk_values = []
        coverage_values = []
        for key in route_keys:
            coverages, risks, _ = routes[key]
            risk_values.append(100.0 * risks[seed] / 100.0 if seed < len(risks) else np.nan)
            coverage_values.append(100.0 * coverages[seed] / 100.0 if seed < len(coverages) else np.nan)
        offset = (seed - 1) * bar_width
        risk_ax.bar(x + offset, risk_values, width=bar_width, color=color,
                    label=f"Seed {seed}", zorder=2)
        coverage_ax.bar(x + offset, coverage_values, width=bar_width, color=color,
                        zorder=2)

    risk_ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.02), ncol=3,
                   frameon=False, fontsize=5.0, handlelength=1.0,
                   columnspacing=0.35, handletextpad=0.25)
    coverage_ax.text(0.98, 0.96, "20% minimum", transform=coverage_ax.transAxes,
                     color=COLORS["contract"], fontsize=5.0, ha="right", va="top")
    risk_ax.text(0.98, 0.96, "10% target", transform=risk_ax.transAxes,
                 color=COLORS["contract"], fontsize=5.0, ha="right", va="top")
    save_figure(fig, "figure_04_external_boundaries_singlecol")


def main() -> None:
    set_publication_style()
    make_estonia_figure()
    print("Wrote native-size Figure 3 output; Figure 8 remained locked")


if __name__ == "__main__":
    main()
