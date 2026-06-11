import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Paths — edit these if your local layout differs
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data"
FIG_DIR   = REPO_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_DIR / "reference_consistency_deciles.csv").sort_values("prob_bin_mid")

fig, ax = plt.subplots(figsize=(7.5, 5))
ax.plot(df["prob_bin_mid"], df["frac_irrigated_aimhpa"], linewidth=2, color="#ff7f0e", label="AIM-HPA")
ax.plot(df["prob_bin_mid"], df["frac_irrigated_lanid"],  linewidth=2, color="#2ca02c", label="LANIDv2")

ax.set_xlabel("Posterior Probability", fontsize=12)
ax.set_ylabel("Fraction of Pixels Labeled Irrigated", fontsize=12)
ax.set_xlim(0, 1)
ax.set_xticks(np.arange(0, 1.1, 0.1))
ax.set_ylim(0.1, 0.9)
ax.legend(fontsize=11)
plt.tight_layout()

out = FIG_DIR / "figS2_reference_consistency.pdf"
fig.savefig(out, bbox_inches="tight")
plt.show()
print("Saved:", out)
