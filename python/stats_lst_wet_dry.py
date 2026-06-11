import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data"

df = pd.read_csv(DATA_DIR / "lst_wet_dry_contrast.csv")
df = df[(df["year"] >= 2003) & (df["year"] <= 2015)]

driest  = df.nsmallest(5, "precip_julaug_in")
wettest = df.nlargest(5, "precip_julaug_in")
print(f"Driest years:  {sorted(driest['year'])}")
print(f"Wettest years: {sorted(wettest['year'])}\n")

for label, col in [("Grassland", "mean_grass_lst_c"),
                   ("Rainfed corn", "mean_rainfed_lst_c"),
                   ("Irrigated corn", "mean_irrigated_lst_c")]:
    dm, wm = driest[col].mean(), wettest[col].mean()
    print(f"{label:15s} driest {dm:.1f}°C  wettest {wm:.1f}°C  diff {dm - wm:.1f}°C")
