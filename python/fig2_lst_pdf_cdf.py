import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data"
FIG_DIR   = REPO_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COLOR_GRASS = '#68b868'
COLOR_CORN  = '#f0b84a'
COLOR_CDF   = '#1f6b1f'

SCENES = [
    ('2006-08-26', 'Aug 26, 2006'),
    ('2011-07-07', 'Jul 07, 2011'),
    ('2015-07-18', 'Jul 18, 2015'),
    ('2022-08-22', 'Aug 22, 2022'),
]
PANEL_LABELS = ['(a)', '(b)', '(c)', '(d)']
FONTSIZE = 17

df_all = pd.read_csv(DATA_DIR / "lst_pierce_four_scenes.csv")

fig, axes = plt.subplots(2, 2, figsize=(14, 11.5))

for idx, (date, label) in enumerate(SCENES):
    row, col = divmod(idx, 2)
    ax_pdf = axes[row, col]
    ax_cdf = ax_pdf.twinx()

    sub   = df_all[df_all['date'] == date]
    corn  = sub[sub['land_cover'] == 'corn']['lst_c'].values
    grass = sub[sub['land_cover'] == 'grass']['lst_c'].values

    all_vals = np.concatenate([corn, grass])
    xmin = all_vals.min() - 1
    xmax = all_vals.max() + 1
    bins = np.linspace(xmin, xmax, 40)

    ax_pdf.hist(corn,  bins=bins, density=True, alpha=0.55,
                color=COLOR_CORN,  edgecolor='none')
    ax_pdf.hist(grass, bins=bins, density=True, alpha=0.55,
                color=COLOR_GRASS, edgecolor='none')
    ax_pdf.set_xlim(xmin, xmax)
    ax_pdf.set_ylim(bottom=0)

    for spine in ax_pdf.spines.values():
        spine.set_visible(True)
    ax_cdf.spines['top'].set_visible(False)
    ax_cdf.spines['left'].set_visible(False)
    ax_cdf.spines['bottom'].set_visible(False)

    tick_step = max(1, round((xmax - xmin) / 6))
    xticks = np.arange(np.ceil(xmin), np.floor(xmax) + 1, tick_step)
    ax_pdf.set_xticks(xticks)
    ax_pdf.set_xticklabels([f"{int(t)}" for t in xticks], fontsize=FONTSIZE - 2)
    ax_pdf.tick_params(axis='y', labelsize=FONTSIZE - 2)

    grass_sorted = np.sort(grass)
    cdf_vals = np.arange(1, len(grass_sorted) + 1) / len(grass_sorted)
    ax_cdf.plot(grass_sorted, cdf_vals, color=COLOR_CDF, linewidth=2.0)
    ax_cdf.set_ylim(0, 1)
    ax_cdf.tick_params(labelsize=FONTSIZE - 2)

    ax_pdf.set_title(label, fontsize=FONTSIZE, pad=6)
    ax_pdf.text(0.02, 0.98, PANEL_LABELS[idx], transform=ax_pdf.transAxes,
                fontsize=FONTSIZE + 2, fontweight='bold', va='top', ha='left')

    ax_pdf.set_ylabel('')
    ax_cdf.set_ylabel('')
    ax_pdf.set_xlabel('')
    if col != 0:
        ax_pdf.tick_params(axis='y', labelleft=False)
    if col != 1:
        ax_cdf.tick_params(axis='y', labelright=False)

plt.tight_layout(rect=[0.05, 0.05, 0.95, 0.97])

fig.text(0.5, 0.01, 'Land Surface Temperature (°C)',
         ha='center', va='bottom', fontsize=FONTSIZE + 1)
fig.text(0.01, 0.5, 'Likelihood',
         ha='left', va='center', rotation='vertical', fontsize=FONTSIZE + 1)
fig.text(0.99, 0.5, 'Cumulative Distribution Function',
         ha='right', va='center', rotation='vertical', fontsize=FONTSIZE + 1)

legend_elements = [
    mpatches.Patch(facecolor=COLOR_GRASS, alpha=0.65, label='Grassland pixel PDF'),
    mpatches.Patch(facecolor=COLOR_CORN,  alpha=0.65, label='Maize pixel PDF'),
    Line2D([0], [0], color=COLOR_CDF, linewidth=2.0, label='Grassland pixel CDF'),
]
fig.legend(handles=legend_elements, loc='upper center', ncol=3,
           fontsize=FONTSIZE, frameon=False, bbox_to_anchor=(0.5, 1.02))

out = FIG_DIR / "fig2_lst_pdf_cdf.pdf"
fig.savefig(out, bbox_inches='tight', dpi=300)
plt.show()
print("Saved:", out)
