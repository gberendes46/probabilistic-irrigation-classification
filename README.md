# probabilistic-irrigation-classification

Bayesian framework for mapping field-scale irrigation probabilities using Landsat-derived
land surface temperature and county-level priors, with the code to reproduce every figure
and statistic in the paper.

**Paper:**
*"Probabilistic Estimates of Irrigation using Land Surface Temperature"*
Greta F. Berendes, Patricio Grassini, Peter Huybers

---

## Repository structure

- `gee/` — Google Earth Engine scripts that generate the annual posterior irrigation
  probability maps. `01_make_annual_maps.js` is the entry point; `02_export_tifs.js`
  exports the final statewide assets to Google Drive as GeoTIFFs.
- `python/` — scripts that reproduce paper figures and in-text statistic from the
  CSVs in `data/`.
- `data/` — aggregated CSVs behind the figures and statistics, the county-year NASS
  irrigation prior table, and the three GeoTIFF panels used in Figure 3. Column-level
  documentation is in `data/README_data.md`.
- `LICENSE` — MIT license.

The maps are produced in `gee/`; the figures and statistics are produced in `python/` from
`data/`. 

---

## Generating the maps (Google Earth Engine)

The GEE scripts produce annual, 30 m irrigation probability maps using a Bayesian framework
that combines:

1. Landsat-derived Land Surface Temperature (LST) during peak season
2. Region-level (e.g., county-year) priors on irrigation prevalence

The key output is a raster with values in **[0,1]** representing the posterior probability
that each target crop pixel (e.g., maize) is irrigated in a given year and region. Unlike
binary irrigation maps, this framework produces continuous probabilities, allowing
uncertainty and partial irrigation to be represented explicitly.

The method does not require labeled training data:

- The likelihood is derived from within-scene LST distributions (relative thermal position
  of crop pixels vs. non-irrigated reference land cover).
- The prior is derived from aggregated statistics (e.g., USDA/NASS percent irrigated).

### Scripts

`01_make_annual_maps.js` generates annual posterior irrigation probability maps per region
and exports them to a user-specified GEE Asset collection.

`02_export_tifs.js` reads the statewide assets produced by `01_make_annual_maps.js` and
exports each year as a GeoTIFF to Google Drive. Run after all export tasks from
`01_make_annual_maps.js` have completed.

### Required user inputs

In `01_make_annual_maps.js`, there is a **USER SETTINGS** block at the top that you must
edit before running.

**1) Regions to process.**
Option A (recommended): a custom FeatureCollection of regions.

```js
ee.FeatureCollection('users/YOUR_USERNAME/your_regions')
```

Each feature must have geometry and a unique id/name field; the id/name is used in export
filenames. Option B: use TIGER counties for selected U.S. states.

```js
STATES = ['NEBRASKA','KANSAS',...]
```

In this mode, all counties in the listed states are processed.

**2) Years.** Provide matching, equal-length, aligned arrays:

```js
YEAR_STRINGS = ['2003','2004',...]   // date filtering
YEARS_INT    = [2003,2004,...]       // matching against the prior table
```

**3) Peak-season window.** Default July 1 to Aug 31. Adjust for other climates or crops.

**4) Export destination.** An output Asset collection path that already exists in GEE.

```js
OUTPUT_ASSET_COLLECTION = 'projects/ee-gfb46/assets/annual_maps'
```

Each region-year generates one exported image in this collection.

**5) Prior table.** Either provide an Asset FeatureCollection of region-year irrigation
fractions, or replace `getRegionYearIrrFraction()` with your own logic. The template expects
columns Year (int), Percent Irrigated (0–100), and optionally State/County in TIGER mode.
A Nebraska prior table derived from USDA/NASS interpolated county irrigation statistics is
provided in `data/nass_percent_irrigated_nebraska.csv`.

### Datasets used (public GEE catalog unless noted)

- **Landsat LST** via the Ermida et al. (2020) single-channel algorithm
  (`users/sofiaermida/landsat_smw_lst`), using Landsat 5, 7, 8, and 9 for temporal sampling.
- **Cropland mask:** USDA/NASS Cropland Data Layer (CDL), used to define target crop pixels
  (e.g., maize = class 1) and reference non-irrigated land cover (e.g., grassland = class 176).
- **Administrative boundaries (optional):** TIGER/2016/Counties, used only in TIGER mode.
- **Prior information:** region-year percent irrigated from USDA/NASS interpolated statistics,
  used to construct the Beta prior. Nebraska prior table provided in `data/`.

### Methodology summary

1. **Scene filtering.** For each region-year, Landsat scenes are restricted to the
   peak-season window and to those with sufficient cloud-free coverage (e.g., ≥ 50% of region).
2. **Thermal offset correction (optional).** A constant offset can be applied to the target
   crop LST before comparison: `lstShifted = lstCorn.add(DELTA_T_OFFSET_C)`. Set
   `DELTA_T_OFFSET_C = 0` to disable, use a constant estimated from validation data, or
   implement region/year-specific offsets.
3. **Per-scene likelihood (unsupervised).** `L_i = P_grass(LST <= x_i')`, where `P_grass` is
   the grassland LST CDF and `x_i'` the adjusted crop LST. Cooler-than-expected crop pixels
   receive lower rainfed likelihood.
4. **Combine across scenes.** `L_rain = Π_i L_i`, `L_irr = Π_i (1 - L_i)`, computed in
   log-space for numerical stability.
5. **Region-year prior.** `prior(f) ∝ f^(α-1)(1-f)^(β-1)`, a Beta prior centered on the
   region-year irrigation fraction; a concentration parameter S controls tightness.
6. **Posterior over irrigation fraction.** For `f ∈ {0.01,...,0.99}`, compute the marginal
   likelihood, multiply by the prior, and normalize.
7. **Pixel-level posterior.** `P(irrigated | data) = Σ_f w(f) · P(irrigated | data, f)`,
   yielding `posterior_mean`, a continuous probability in [0,1].

### Outputs

Each exported image contains `posterior_mean` (the primary product), `likelihood`,
`log_likelihood`, `likelihood_rain`, and `log_likelihood_rain`.

### Running

1. Open `01_make_annual_maps.js` in Google Earth Engine.
2. Edit the USER SETTINGS block.
3. Run the script and start export tasks in the Tasks tab.
4. Once all tasks are complete, run `02_export_tifs.js` to export statewide GeoTIFFs to Drive.

Start with one region and one year to test configuration before scaling.

### Performance notes

- The script uses some client-side loops (`getInfo()` / `evaluate()`), which are simple but
  may be slow at scale.

---

## Reproducing the figures and statistics (Python)

The scripts in `python/` regenerate the paper's figures and reported numbers from the CSVs
in `data/`. Each is self-contained and reads from `data/` relative to the repo root.

| Script | Produces |
|---|---|
| `fig2_lst_pdf_cdf.py` | Figure 2, LST pixel distributions for four Pierce County scenes |
| `fig3_posterior_map.py` | Figure 3, the 2009 posterior map (reads GeoTIFFs in `data/`) |
| `fig4_water_applied_by_year.py` | Figure 4, applied water and precipitation by year |
| `fig5_accuracy_vs_water_applied.py` | Figure 5, accuracy and posterior spread by applied-water bin |
| `fig6_interannual.py` | Figure 6, interannual accuracy and percent irrigated, plus §4.4 percent-irrigated stats |
| `figS2_reference_consistency.py` | Figure S2, reference-product consistency curves |
| `figS3_roc.py` | Figure S3, pooled ROC |
| `figS4_accuracy_climate.py` | Figure S4 and the §4.4 accuracy regression |
| `stats_maptomap.py` | §4.5 map-to-map agreement numbers |
| `stats_lst_wet_dry.py` | §4.3 wet/dry LST contrast |

Most scripts require only `numpy`, `pandas`, and `matplotlib`. `fig2_lst_pdf_cdf.py` additionally requires `scipy` (`pip install scipy`). `fig3_posterior_map.py` additionally requires `rasterio` and `cartopy` (`pip install rasterio cartopy`).

See `data/README.md` for the column-level dictionary of every input CSV.

---

## Data and code availability

- **Posterior maps (Nebraska, 2003–2023, 30 m):** archived on HydroShare,
  DOI `http://www.hydroshare.org/resource/214a74d3d1694cc29c07f2d3da14a2b2`.
- **Code:** this repository, archived at Zenodo, DOI `10.5281/zenodo.20648900`.
- **Aggregated figure/statistic data and prior table:** in `data/` (see `data/README.md`).
- **Landsat LST, USDA CDL, and USDA/NASS statistics:** publicly available through their
  respective providers.
- **Nebraska NRD field-level irrigation records:** contain landowner-identifiable
  information and were provided under data-sharing agreements that prohibit public
  distribution. Access requests should be directed to the relevant NRDs.

---

## License

Released under the MIT License. See `LICENSE`.

---

## Citation

If you use this code or the posterior maps, please cite the paper and the archived code
release. The Zenodo DOI above is the
preferred citation for the software.

---

## Contact

Greta F. Berendes
gretaberendes@fas.harvard.edu
