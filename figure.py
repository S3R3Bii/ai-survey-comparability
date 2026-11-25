"""Show how the uncertainty in common-item change varies with enterprise size."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
with (ROOT / "results/changes.csv").open() as f:
    changes = [row for row in csv.DictReader(f) if row["constraints"] == "all_published_counts"]
labels = {
    "GE10": "All (10+)",
    "10-49": "Small (10–49)",
    "50-249": "Medium (50–249)",
    "GE250": "Large (250+)",
}
fig, ax = plt.subplots(figsize=(9.4, 4.7))
fig.subplots_adjust(left=0.205, right=0.96, top=0.78, bottom=0.25)
fig.text(
    0.055,
    0.935,
    "How much did reported AI use change?",
    fontsize=19,
    weight="bold",
    color="#19384a",
)
fig.text(
    0.055,
    0.86,
    "EU enterprises, 2024 to 2025. Lines show the feasible change across six comparable items.",
    fontsize=10.6,
)
ax.axvline(0, color="#516373", linewidth=1, linestyle="--")
for i, row in enumerate(changes):
    lo, hi, headline = (
        float(row[k]) for k in ("common_low_pp", "common_high_pp", "headline_change_pp")
    )
    color = "#0e655e" if i == 0 else "#629d95"
    ax.plot([lo, hi], [i, i], linewidth=5, color=color, solid_capstyle="butt")
    ax.scatter(
        headline, i, marker="D", s=52, color="#973c15", zorder=4, edgecolors="white", linewidth=0.7
    )
ax.set_yticks(range(len(changes)), [labels[r["size"]] for r in changes])
ax.set_ylim(len(changes) - 0.4, -0.6)
ax.set_xlim(-8, 28)
ax.set_xlabel("Change in percentage points")
ax.grid(axis="x", color="#e4e9ec", linewidth=0.7)
ax.set_axisbelow(True)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0, pad=8)
ax.scatter(
    [],
    [],
    marker="D",
    color="#973c15",
    label="Headline change using each year's full questionnaire",
)
ax.legend(
    loc="upper left", bbox_to_anchor=(-0.01, -0.26), frameon=False, fontsize=9, borderaxespad=0
)
fig.text(
    0.055,
    0.025,
    "Source: Eurostat, isoc_eb_ai. Intervals reflect unknown overlap. Sampling error is additional.",
    fontsize=9,
)
fig.savefig(ROOT / "results/adoption-change.png", dpi=150)
