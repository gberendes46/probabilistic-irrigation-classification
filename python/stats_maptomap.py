import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data"

df = pd.read_csv(DATA_DIR / "maptomap_agreement.csv").set_index("product")

for prod, r in df.iterrows():
    print(f"{prod}: pixel agreement {r['pixel_agreement']*100:.0f}%, "
          f"mean posterior over irrigated pixels {r['mean_posterior_over_irrigated']:.2f}, "
          f"over dry pixels {r['mean_posterior_over_dryland']:.2f}; "
          f"{r['irrigated_share_top_decile']*100:.0f}% in P>0.9 decile, "
          f"{r['irrigated_share_bottom_decile']*100:.0f}% in P<0.1 decile.")
