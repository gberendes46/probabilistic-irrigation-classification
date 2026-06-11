import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data"
FIG_DIR   = REPO_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_DIR / "accuracy_by_waterbin.csv").sort_values("water_lo_in").reset_index(drop=True)
x = np.arange(len(df))
labels = df["water_bin"].tolist()

stats = [dict(med=r.posterior_q50, q1=r.posterior_q25, q3=r.posterior_q75,
              whislo=r.posterior_q10, whishi=r.posterior_q90)
         for r in df.itertuples()]

LABEL_SIZE, TICK_SIZE, LEGEND_SIZE = 15, 14, 13
fig, ax1 = plt.subplots(figsize=(12, 5))

ax1.plot(x, df["accuracy"], linewidth=2, color="#1f77b4", label="Accuracy", zorder=5)
ax1.set_ylabel("Accuracy", color="#1f77b4", fontsize=LABEL_SIZE)
ax1.tick_params(axis="y", labelcolor="#1f77b4", labelsize=TICK_SIZE)
ax1.set_ylim(0, 1.05)
ax1.spines["right"].set_visible(False)

ax2 = ax1.twinx()
ax2.bxp(stats, positions=x, widths=0.5, patch_artist=True, showfliers=False,
        medianprops=dict(color="darkgreen", linewidth=2),
        boxprops=dict(facecolor="#2ca02c", alpha=0.25, linewidth=1.2),
        whiskerprops=dict(color="#2ca02c", linewidth=1.2),
        capprops=dict(color="#2ca02c", linewidth=1.2), zorder=3)
ax2.set_ylabel("Posterior Probability Distribution", color="#2ca02c", fontsize=LABEL_SIZE)
ax2.tick_params(axis="y", labelcolor="#2ca02c", labelsize=TICK_SIZE)
ax2.set_ylim(0, 1.05)
ax2.spines["right"].set_visible(True)
ax2.spines["right"].set_color("black")

legend_elements = [
    plt.Line2D([0], [0], color="#1f77b4", linewidth=2, label="Accuracy"),
    Patch(facecolor="#2ca02c", alpha=0.25, label="IQR Probability"),
    plt.Line2D([0], [0], color="darkgreen", linewidth=2, label="Median Probability"),
]
ax1.legend(handles=legend_elements, loc="lower right", fontsize=LEGEND_SIZE)

ax1.set_xticks(x)
ax1.set_xticklabels(labels, rotation=45, fontsize=TICK_SIZE)
ax1.set_xlim(-0.5, len(df) - 0.5)
ax1.set_xlabel("Amount Water Applied (inches)", fontsize=LABEL_SIZE)
plt.tight_layout()

out = FIG_DIR / "fig5_accuracy_vs_water_applied.pdf"
fig.savefig(out, dpi=300, bbox_inches="tight")
plt.show()
print("Saved:", out)
