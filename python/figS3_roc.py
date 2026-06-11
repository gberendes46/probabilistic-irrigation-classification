import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data"
FIG_DIR   = REPO_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

roc = pd.read_csv(DATA_DIR / "roc_points.csv").sort_values("fpr").reset_index(drop=True)
auc = np.trapz(roc["tpr"], roc["fpr"])

fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(roc["fpr"], roc["tpr"], linewidth=2, color="#1f77b4", label=f"Pooled ROC (AUC={auc:.3f})")
ax.plot([0, 1], [0, 1], linestyle="--", linewidth=1, color="#2ca02c", label="Random Chance")
ax.set_xlabel("False Positive Rate")
ax.set_ylabel("True Positive Rate")
ax.legend()
ax.grid(False)
plt.tight_layout()

out = FIG_DIR / "figS3_roc.pdf"
fig.savefig(out, bbox_inches="tight")
plt.show()
print(f"Saved: {out}  (AUC={auc:.3f})")
