import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data"
FIG_DIR   = REPO_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

acc = pd.read_csv(DATA_DIR / "annual_accuracy_2003_2015.csv").sort_values("year")
pct = pd.read_csv(DATA_DIR / "annual_percent_irrigated_2003_2023.csv").sort_values("year")

# Section 4.4: percent irrigated vs Jul-Aug precip
def corr(df, col, yhi=None):
    d = (df if yhi is None else df[df["year"] <= yhi])[["precip_julaug_in", col]].dropna()
    return np.corrcoef(d["precip_julaug_in"], d[col])[0, 1], len(d)

print("Percent irrigated vs Jul-Aug precip:")
for label, col, yhi in [("Posterior 2003-2023", "pct_posterior", None),
                        ("Posterior 2003-2017", "pct_posterior", 2017),
                        ("LANID 2003-2017",     "pct_lanid",     2017),
                        ("AIM-HPA 2003-2017",   "pct_aimhpa",    2017)]:
    r, n = corr(pct, col, yhi)
    print(f"  {label:22s} r = {r:+.3f}  (n={n})")

clim = ["precip_julaug_in", "tmax_julaug_c", "tmean_julaug_c"]
d = pct[["pct_posterior"] + clim].dropna()
y, X = d["pct_posterior"].to_numpy(float), d[clim].to_numpy(float)
yz = (y - y.mean()) / y.std(ddof=1)
Xz = (X - X.mean(0)) / X.std(0, ddof=1)
Xd = np.column_stack([np.ones(len(yz)), Xz])
beta = np.linalg.lstsq(Xd, yz, rcond=None)[0]
r2 = 1 - np.sum((yz - Xd @ beta)**2) / np.sum((yz - yz.mean())**2)
print(f"\nPct irrigated ~ precip + tmax + tmean  (n={len(d)}, R²={r2:.2f})")
for name, b in zip(clim, beta[1:]):
    print(f"  {name:18s} std beta = {b:+.2f}")

# Figure 6
def smart_ylim(vals, pad=0.06, lo=None, hi=None):
    v = np.asarray(vals, float); v = v[np.isfinite(v)]
    mn, mx = v.min(), v.max(); p = (mx - mn) * pad or 0.02
    a, b = mn - p, mx + p
    if lo is not None: a = max(a, lo)
    if hi is not None: b = min(b, hi)
    return a, b

def panel_label(ax, text, size=14):
    ax.text(-0.07, 1.02, text, transform=ax.transAxes, fontsize=size,
            fontweight="bold", va="bottom", ha="left")

pct15 = pct[pct["year"] <= 2015]
years = acc["year"].values
C_POST, C_LANID, C_AIM, C_PRECIP = "black", "#2ca02c", "#ff7f0e", "#1f77b4"
LABEL, TICK, LEG = 14, 13, 12

fig = plt.figure(figsize=(12.5, 7.5))
gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.1], hspace=0.30)

ax0 = fig.add_subplot(gs[0, 0])
for col, c, lab in [("posterior_acc", C_POST, "Posterior"), ("lanid_acc", C_LANID, "LANID"),
                    ("aimhpa_acc", C_AIM, "AIM-HPA")]:
    ax0.plot(acc["year"], acc[col], linewidth=2, color=c, label=lab, zorder=5)
ax0.set_ylim(*smart_ylim(acc[["posterior_acc", "lanid_acc", "aimhpa_acc"]].values.flatten(), 0.08, 0.0, 1.02))
ax0.set_ylabel("Accuracy", fontsize=LABEL)
ax0.tick_params(labelsize=TICK)
ax0.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=LEG)
panel_label(ax0, "(a)")

ax1 = fig.add_subplot(gs[1, 0], sharex=ax0)
ax1r = ax1.twinx()
for col, c, lab in [("pct_posterior", C_POST, "Posterior"), ("pct_lanid", C_LANID, "LANID"),
                    ("pct_aimhpa", C_AIM, "AIM-HPA")]:
    ax1.plot(pct15["year"], pct15[col], linewidth=2, color=c, label=lab, zorder=5)
ax1.set_ylim(*smart_ylim(pct15[["pct_posterior", "pct_lanid", "pct_aimhpa"]].values.flatten(), 0.06, 0.0, 100.0))
ax1.set_ylabel("Percent irrigated (%)", fontsize=LABEL)
ax1.tick_params(labelsize=TICK)

ax1r.plot(pct15["year"], pct15["precip_julaug_in"], linewidth=2, color=C_PRECIP, label="Jul–Aug precip (in)", zorder=3)
ax1r.set_ylim(*smart_ylim(pct15["precip_julaug_in"].values, 0.12, 0.0))
ax1r.set_ylabel("Jul–Aug precip (in)", color=C_PRECIP, fontsize=LABEL)
ax1r.tick_params(axis="y", labelcolor=C_PRECIP, labelsize=TICK)
ax1r.spines["right"].set_visible(True)

h, l = ax1.get_legend_handles_labels()
hr, lr = ax1r.get_legend_handles_labels()
ax1.legend(h + hr, l + lr, loc="center left", bbox_to_anchor=(1.08, 0.5), fontsize=LEG)
panel_label(ax1, "(b)")

ax1.set_xticks(years)
ax1.set_xticklabels([str(y) for y in years], rotation=45, fontsize=TICK)
ax1.set_xlabel("Year", fontsize=LABEL)

plt.subplots_adjust(top=0.96, bottom=0.10, left=0.08, right=0.78)
out = FIG_DIR / "fig6_accuracy_pct_precip.pdf"
fig.savefig(out, bbox_inches="tight", dpi=300)
plt.show()
print("Saved:", out)
