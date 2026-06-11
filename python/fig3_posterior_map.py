# Requires: pip install rasterio cartopy

import numpy as np
import rasterio
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data"
FIG_DIR   = REPO_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
proj = ccrs.PlateCarree()

A_PATH = DATA_DIR / "A_NE_2009_posterior_statewide_with_boxes_latlon_twotoneBG.tif"
B_PATH = DATA_DIR / "B_NE_2009_inset_boxB_latlon.tif"
C_PATH = DATA_DIR / "C_NE_2009_inset_boxC_latlon.tif"

boxB = [(-101.3259258209168, 40.85180411967253), (-100.68665885314336, 40.85180411967253),
        (-100.68665885314336, 41.07631444129903), (-101.3259258209168, 41.07631444129903),
        (-101.3259258209168, 40.85180411967253)]
boxC = [(-101.13291799711288, 40.91673272070489), (-101.03833257841171, 40.91673272070489),
        (-101.03833257841171, 40.989723618469355), (-101.13291799711288, 40.989723618469355),
        (-101.13291799711288, 40.91673272070489)]

cmap = LinearSegmentedColormap.from_list("posterior", list(reversed([
    "#2c7bb6", "#00a6ca", "#00ccbc", "#90eb9d", "#ffffbf",
    "#f9d057", "#f29e2e", "#e76818", "#d7191c"])), N=256)

def read_rgb(path):
    with rasterio.open(path) as ds:
        rgb = np.transpose(ds.read()[:3], (1, 2, 0))
        extent = [ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top]
    return rgb, extent

def style_geo_axes(ax, extent):
    ax.set_extent(extent, crs=proj)
    gl = ax.gridlines(crs=proj, draw_labels=True, linewidth=0.5, color="0.6", alpha=0.6, linestyle="--")
    gl.top_labels = gl.right_labels = False
    gl.xformatter, gl.yformatter = LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    gl.xlabel_style = gl.ylabel_style = {"size": 10}

def plot_box(ax, coords):
    ax.plot([p[0] for p in coords], [p[1] for p in coords], transform=proj, color="black", linewidth=1.2)

A_rgb, A_ext = read_rgb(A_PATH)
B_rgb, B_ext = read_rgb(B_PATH)
C_rgb, C_ext = read_rgb(C_PATH)

fig = plt.figure(figsize=(7.8, 10.8))
gs = fig.add_gridspec(nrows=4, ncols=1, height_ratios=[1, 1, 1, 1], hspace=0.22)
axA = fig.add_subplot(gs[0, 0], projection=proj)
axB = fig.add_subplot(gs[1, 0], projection=proj)
axC = fig.add_subplot(gs[2, 0], projection=proj)
axCB = fig.add_subplot(gs[3, 0]); axCB.set_axis_off()

for ax, rgb, ext in [(axA, A_rgb, A_ext), (axB, B_rgb, B_ext), (axC, C_rgb, C_ext)]:
    ax.imshow(rgb, extent=ext, origin="upper", transform=proj)
    style_geo_axes(ax, ext)

for ax, lab in zip([axA, axB, axC], ["(a)", "(b)", "(c)"]):
    ax.text(0.01, 0.99, lab, transform=ax.transAxes, ha="left", va="top",
            fontsize=10, fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=2))

plot_box(axA, boxB); plot_box(axA, boxC)
plot_box(axB, boxB); plot_box(axB, boxC)
plot_box(axC, boxC)

sm = ScalarMappable(norm=mpl.colors.Normalize(vmin=0, vmax=1), cmap=cmap); sm.set_array([])
cax = axCB.inset_axes([0.26, 0.83, 0.48, 0.09])
cb = fig.colorbar(sm, cax=cax, orientation="horizontal", ticks=[0, 0.5, 1])
cb.ax.tick_params(labelsize=10)
cb.set_label("Posterior Irrigation Probability", fontsize=10)

fig.subplots_adjust(left=0.08, right=0.98, top=0.98, bottom=0.02)
out = FIG_DIR / "fig3_posterior_map.pdf"
fig.savefig(out)
plt.show()
print("Saved:", out)
