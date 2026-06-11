import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data"
FIG_DIR   = REPO_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False})

df = pd.read_csv(DATA_DIR / "annual_accuracy_2003_2015.csv")

drivers = [
    ("precip_julaug_in", "Jul–Aug Precipitation (inches)"),
    ("tmax_julaug_c",    "Maximum Temperature (°C)"),
    ("tmean_julaug_c",   "Mean Temperature (°C)"),
]

# Section 4.4: accuracy ~ precip + tmax + tmean, standardized betas
cols = [c for c, _ in drivers]
d = df[["posterior_acc"] + cols].dropna()
y  = d["posterior_acc"].to_numpy(float)
X  = d[cols].to_numpy(float)
yz = (y - y.mean()) / y.std(ddof=1)
Xz = (X - X.mean(0)) / X.std(0, ddof=1)
Xd = np.column_stack([np.ones(len(yz)), Xz])
beta = np.linalg.lstsq(Xd, yz, rcond=None)[0]
r2 = 1 - np.sum((yz - Xd @ beta)**2) / np.sum((yz - yz.mean())**2)

print(f"Accuracy ~ precip + tmax + tmean   (n={len(d)}, R²={r2:.2f})")
for name, b in zip(cols, beta[1:]):
    r = np.corrcoef(d[name], y)[0, 1]
    print(f"  {name:18s} std beta = {b:+.2f}   pearson r = {r:+.2f}")

# Figure S4
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
for ax, (col, xlabel), label in zip(axes, drivers, ["(a)", "(b)", "(c)"]):
    ax.scatter(df[col], df["posterior_acc"], s=40, color="black", alpha=0.85)
    ax.set_xlabel(xlabel, fontsize=16)
    ax.set_ylabel("Accuracy", fontsize=16)
    ax.tick_params(axis="both", labelsize=16)
    ax.text(0.02, 1.02, label, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=16, fontweight="bold", clip_on=False)
fig.tight_layout()

out = FIG_DIR / "figS4_accuracy_climate.pdf"
fig.savefig(out, bbox_inches="tight")
plt.show()
print("Saved:", out)
