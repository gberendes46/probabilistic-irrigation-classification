# Data

Derived, aggregated data behind the figures and in-text statistics of *Probabilistic
Estimates of Irrigation using Land Surface Temperature* (Berendes, Grassini, Huybers).
Each file is the minimal input needed to reproduce one figure or reported statistic; the
matching scripts are in `python/`. Also included is the county-year irrigation prior table
used as input to the Bayesian classification framework (`nass_percent_irrigated_nebraska.csv`)
and the three GeoTIFF panels used in Figure 3 (`A_NE_2009_*.tif`, `B_NE_2009_*.tif`,
`C_NE_2009_*.tif`). Annual statewide posterior maps (2003–2023) are archived separately
on HydroShare (see the manuscript Data and Code Availability statement).

All files are aggregates (per year, per bin, per decile, or ROC points). No field-level
Nebraska Natural Resources District (NRD) records are included; those are restricted and
were provided under data-sharing agreements (see the manuscript Data and Code Availability
statement).

## Conventions

- Column-name suffixes carry units: `_in` = inches, `_c` = degrees Celsius. `julaug` =
  summed (precipitation) or averaged (temperature) over July–August.
- `pct_*` columns are percentages on a 0–100 scale. `frac_*`, `share_*`, and
  `pixel_agreement` are fractions on a 0–1 scale.
- "top decile" means posterior irrigation probability > 0.9; "bottom decile" means < 0.1.
- LANIDv2 and AIM-HPA columns are blank (NaN) after 2017, the last year those products cover.
- "Provenance" notes whether a file is reproducible from public data or derived (in
  aggregate) from restricted NRD records.

---

## Figure 3 GeoTIFFs
Three RGB-rendered GeoTIFF panels used in Figure 3. These are display renders, not
analysis data. Band ordering is R/G/B; CRS is EPSG:4326.

| File | Description |
|---|---|
| `A_NE_2009_posterior_statewide_with_boxes_latlon_twotoneBG.tif` | Statewide 2009 posterior map with inset box outlines and two-tone background |
| `B_NE_2009_inset_boxB_latlon.tif` | Inset B zoom |
| `C_NE_2009_inset_boxC_latlon.tif` | Inset C zoom |

---
## lst_pierce_four_scenes.csv
Feeds Figure 2. Pixel-level land surface temperature for grassland and maize in Pierce
County, Nebraska for four Landsat scenes spanning the study period. Provenance: public.

| Column | Description |
|---|---|
| `date` | Scene date (YYYY-MM-DD) |
| `satellite` | Landsat satellite (e.g. Landsat 5, Landsat 8) |
| `land_cover` | Land cover type: `corn` or `grass` |
| `lst_c` | Land surface temperature (°C) |

## reference_consistency_deciles.csv
Feeds Figure S2. Provenance: public.

| Column | Description |
|---|---|
| `prob_bin_lo` | Lower edge of the posterior-probability decile bin (0–1) |
| `prob_bin_hi` | Upper edge of the bin (0–1) |
| `prob_bin_mid` | Bin midpoint (0–1) |
| `frac_irrigated_aimhpa` | Fraction of Nebraska maize pixels in this bin labeled irrigated by AIM-HPA, averaged 2003–2017 (0–1) |
| `frac_irrigated_lanid` | Same, for LANIDv2 (0–1) |

## roc_points.csv
Feeds Figure S3. Field-level posterior validation against NRD records, pooled 2003–2015.
AUC is the trapezoidal area under these points (≈ 0.703). Provenance: NRD-derived (aggregated).

| Column | Description |
|---|---|
| `fpr` | False positive rate (0–1) |
| `tpr` | True positive rate (0–1) |
| `posterior_threshold` | Field-mean posterior probability defining the operating point (0–1) |

## accuracy_by_waterbin.csv
Feeds Figure 5. Pooled across 2003–2015. Provenance: NRD-derived (aggregated).

| Column | Description |
|---|---|
| `water_lo_in` | Lower edge of the applied-water bin (inches) |
| `water_hi_in` | Upper edge of the bin (inches; 9999 denotes the open-ended 25+ bin) |
| `water_bin` | Bin label, e.g. `0.1-2`, `25+` |
| `accuracy` | Fraction of fields in the bin correctly classified at a 0.5 posterior threshold (0–1) |
| `mean_posterior` | Mean field-mean posterior probability in the bin (0–1) |
| `posterior_q10`…`posterior_q90` | 10th/25th/50th/75th/90th percentiles of field-mean posterior probability within the bin (0–1) |

## nrd_water_applied_by_year.csv
Feeds Figure 4 and the applied-water vs precipitation correlation (r = −0.77). Aggregated
across center-pivot irrigated maize fields. Provenance: NRD-derived (aggregated).

| Column | Description |
|---|---|
| `year` | Calendar year (2003–2015) |
| `mean_water_applied_in` | Mean seasonal applied water across fields (inches) |
| `water_q25_in` | 25th percentile of applied water across fields (inches) |
| `water_q75_in` | 75th percentile of applied water across fields (inches) |
| `precip_julaug_in` | Statewide July–August precipitation (inches) |

## annual_accuracy_2003_2015.csv
Feeds Figure 6a, Figure S4, and the §4.4 accuracy regression. Provenance: accuracy columns
NRD-derived (aggregated); climate public.

| Column | Description |
|---|---|
| `year` | Calendar year (2003–2015) |
| `posterior_acc` | Posterior classification accuracy vs NRD records (0–1) |
| `lanid_acc` | LANIDv2 accuracy vs NRD records (0–1) |
| `aimhpa_acc` | AIM-HPA accuracy vs NRD records (0–1) |
| `precip_julaug_in` | Statewide July–August precipitation (inches) |
| `tmax_julaug_c` | Mean July–August daily maximum temperature (°C) |
| `tmean_julaug_c` | Mean July–August temperature (°C) |

## annual_percent_irrigated_2003_2023.csv
Feeds Figure 6b and the §4.4 percent-irrigated regression and correlations. Provenance: public.

| Column | Description |
|---|---|
| `year` | Calendar year (2003–2023) |
| `pct_posterior` | Percent of maize area classified irrigated by the posterior, within Nebraska (%) |
| `pct_lanid` | Percent of maize area classified irrigated by LANIDv2 (%) on overlap with posterior; blank after 2017 |
| `pct_aimhpa` | Percent of maize area classified irrigated by AIM-HPA (%) on overlap with posterior; blank after 2017 |
| `precip_julaug_in` | Statewide July–August precipitation (inches) |
| `tmax_julaug_c` | Mean July–August daily maximum temperature (°C) |
| `tmean_julaug_c` | Mean July–August temperature (°C) |

## maptomap_agreement.csv
Feeds the §4.5 map-to-map statistics, averaged over 2003–2017. Provenance: public.

| Column | Description |
|---|---|
| `product` | Reference product: `AIM-HPA` or `LANIDv2` |
| `pixel_agreement` | Fraction of overlapping maize pixels where the posterior thresholded at 0.5 agrees with the product's binary label (0–1) |
| `mean_posterior_over_irrigated` | Mean posterior probability over pixels the product labels irrigated (0–1) |
| `mean_posterior_over_dryland` | Mean posterior probability over pixels the product labels dryland (0–1) |
| `irrigated_share_top_decile` | Fraction of the product's irrigated pixels with posterior > 0.9 (0–1) |
| `irrigated_share_bottom_decile` | Fraction of the product's irrigated pixels with posterior < 0.1 (0–1) |
| `dryland_share_top_decile` | Fraction of the product's dryland pixels with posterior > 0.9 (0–1) |
| `dryland_share_bottom_decile` | Fraction of the product's dryland pixels with posterior < 0.1 (0–1) |

## nass_percent_irrigated_nebraska.csv
County-year irrigation prevalence used as the prior in the Bayesian classification
framework. Derived from USDA/NASS county-level irrigation statistics, interpolated to
annual values. Provenance: public (USDA/NASS).

| Column | Description |
|---|---|
| `state` | State name (uppercase); all rows are NEBRASKA |
| `county` | County name (uppercase) |
| `year` | Calendar year |
| `pct_irrigated` | Percent of maize area irrigated in that county-year (0–100); NaN where data are missing |

## lst_wet_dry_contrast.csv
Feeds the §4.3 wet/dry LST contrast (5 wettest vs 5 driest years over 2003–2015).
Provenance: public.

| Column | Description |
|---|---|
| `year` | Calendar year |
| `mean_grass_lst_c` | Mean July–August grassland land surface temperature across counties and scenes (°C) |
| `mean_rainfed_lst_c` | Mean July–August rainfed maize LST (°C) |
| `mean_irrigated_lst_c` | Mean July–August irrigated maize LST (°C) |
| `precip_julaug_in` | Statewide July–August precipitation (inches) |
