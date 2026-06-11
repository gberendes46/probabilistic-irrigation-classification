import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data"
FIG_DIR   = REPO_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_DIR / "nrd_water_applied_by_year.csv").sort_values("year")
years = df["year"].values

m = df[["mean_water_applied_in", "precip_julaug_in"]].dropna()
r = np.corrcoef(m["mean_water_applied_in"], m["precip_julaug_in"])[0, 1]
print(f"Applied water vs Jul-Aug precip: r = {r:.2f}  (n={len(m)})")

COLOR_WATER, COLOR_PRECIP = "#2ca02c", "#1f77b4"
fig, ax = plt.subplots(figsize=(8, 5))

ax.fill_between(years, df["water_q25_in"], df["water_q75_in"], alpha=0.15, color=COLOR_WATER)
ax.plot(years, df["mean_water_applied_in"], "-", color=COLOR_WATER, linewidth=2, label="Mean water applied")
ax.set_xlabel("Year", fontsize=12)
ax.set_ylabel("Mean water applied (inches)", fontsize=12, color=COLOR_WATER)
ax.tick_params(axis="y", labelcolor=COLOR_WATER)
ax.set_xticks(years)
ax.tick_params(axis="x", rotation=45)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax2 = ax.twinx()
ax2.plot(years, df["precip_julaug_in"], "-", color=COLOR_PRECIP, linewidth=1.8, alpha=0.8, label="Jul–Aug precip")
ax2.set_ylabel("Jul–Aug precipitation (inches)", fontsize=12, color=COLOR_PRECIP)
ax2.tick_params(axis="y", labelcolor=COLOR_PRECIP)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(True)

plt.tight_layout()
out = FIG_DIR / "fig4_water_applied_by_year.pdf"
fig.savefig(out, bbox_inches="tight", dpi=300)
plt.show()
print("Saved:", out)
