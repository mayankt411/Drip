<!-- Generated into paper/paper_confirmatory.md by src/report/make_confirmatory_report.py. Edit this template, not the output. -->

# Empirical Limits of Free 10-Meter Sentinel-2 Imagery for Floating-Roof Oil Storage Monitoring: A Pre-Registered Confirmatory Study at Cushing, Oklahoma

[Author names and affiliations to be added]

## Abstract

Free 10 m Sentinel-2 imagery would make crude storage monitoring widely accessible if the shadow that a floating-roof tank's shell casts on its roof could be measured reliably. We tested this in a pre-registered confirmatory study (Protocol 2.0.0, locked 2026-11-03) at Cushing, Oklahoma, using an untouched 2024-01-01 to 2024-06-30 window, {{n_tanks}} eligible tanks, and blinded human readings as the reference (mean inter-rater difference {{irr_mad}} m). Three frozen methods were compared: single-band thresholding (M1), a multi-band spectral index (M2), and a sub-pixel radial gradient (M3). Question 1 required at least {{need_pct}}% of tanks within ±{{tol}} m and a median absolute residual of at most {{med_max}} m. No method came close: pass rates were {{m1_rate}}%, {{m2_rate}}% and {{m3_rate}}% for M1, M2 and M3, and median absolute residuals ranged from {{median_min}} to {{median_max}} m. Question 2 offers an explanation. The mean contrast-to-noise ratio of the shadow crescent was {{cnr_mean}} (range {{cnr_min_obs}} to {{cnr_max_obs}}; threshold {{cnr_min}}), so the signal sat below sensor noise at all {{cnr_below}} tanks. Question 3, agreement with weekly stock changes from the U.S. Energy Information Administration (EIA), was conditional on Question 1 and was not tested. All {{n_tanks}} tanks were evaluated on one acquisition ({{scene_date}}), and {{cloud_target_excluded_pct}}% of products from the two target tiles were excluded for cloud cover. The result is a negative one for these three methods at 10 m. It does not test finer optical or radar sensors, which the literature identifies as candidates.

*Keywords:* Sentinel-2, floating-roof tanks, crude oil storage, pre-registration, negative result, Cushing

## Introduction

Crude oil held in storage is a closely watched quantity, and the EIA publishes weekly stock figures for Cushing, Oklahoma. A free, global, satellite-based estimate could complement them if it were accurate enough. Sentinel-2 is the obvious candidate: its multispectral instrument delivers 10 m pixels in the blue, green, red and near-infrared bands and 20 m pixels in the shortwave infrared band used here (Drusch et al., 2012; European Space Agency, n.d.), and the data are free.

The measurement idea is geometric. An external floating-roof tank has a roof that rides on the liquid, so the roof sinks as the tank empties. The fixed shell above the roof then casts a shadow across the roof surface, and on flat ground its length along the solar azimuth is L = d / tan(α), where d is the drop of the roof below the rim and α is the solar elevation. Shadow length therefore tracks fill level, and published methods use it to infer reserve status, height or volume (Wang et al., 2016; Wang et al., 2019).

Whether that works depends on resolution. Wang et al. (2019) estimated tank height from shadows in Gaofen-2 imagery with 0.81 m panchromatic and 3.2 m multispectral bands and reported a mean absolute height error of 0.238 m on a 21.8 m tank. Spaceborne radar offers a different route through double-bounce geometry: Villamil Lopez and Stilla (2021) estimated fill for floating-roof tanks from TerraSAR-X data over Rotterdam, and Tsai et al. (2024) reported tracking floating-roof height changes with TerraSAR-X spotlight data. Comparisons of satellite-derived Cushing stocks with EIA data also exist, but the two we located are trade and vendor reports that describe agreement qualitatively or as survey totals (Kayrros, 2021; "DigitalGlobe Satellite Validates U.S. Oil Inventory," 2011). In the literature we reviewed, we found no peer-reviewed, pre-registered assessment of free 10 m imagery for this task.

At 10 m, the geometry is unfavorable. The tanks in this study are {{diam_px_min}} to {{diam_px_max}} pixels across, and the blinded reference crescent lengths ({{ref_min}} to {{ref_max}} m) span only {{ref_px_min}} to {{ref_px_max}} pixels. We ask three questions, registered before the 2024 data were opened. Q1: does any frozen method reproduce human-verified shadow lengths well enough to count as a valid measurement? Q2: is the shadow contrast larger than sensor noise at this resolution? Q3: if Q1 passes, do the resulting series carry information about EIA stock changes?

## Method

### Pre-Registration and Data

The protocol was frozen as Pre-Registration v2 (Protocol 2.0.0; `docs/prereg_v2.md`, `configs/prereg_v2.yaml`) and locked in commit `ede4a3f` on 2026-11-03, following the logic of separating confirmatory from exploratory work (Nosek et al., 2018). The confirmatory test window is 2024-01-01 to 2024-06-30. The 2024 data files first appear in the repository in commit `8087717`, after the lock; the manifest does not record retrieval times for them, so that ordering rests on the commit history. Deviations and reporting notes identified while writing up are listed in `docs/deviations.md`.

Imagery is Sentinel-2 Level-2A from the Copernicus Data Space Ecosystem, tiles T14SQE (primary) and T14SPE. The 2024 catalogue holds {{cloud_stac_items}} products over {{cloud_stac_dates}} acquisition dates across four tiles. Rasters for the evaluated scene comprise B02, B03, B04, B08, B11 (native 20 m) and the true-color image. The tank set is the pre-declared registry of {{n_tanks}} external floating-roof crude tanks (radius {{radius_min}} to {{radius_max}} m, shell height {{height_min}} to {{height_max}} m), with no additions or substitutions.

### Human Reference

Two trained inspectors measured the crescent independently on true-color and B04 rasters at 1:1 native resolution under a 2% linear stretch, along the solar azimuth from the southern shell rim to the inner shadow-illuminated floor boundary. They were required to be blind to algorithm output and to EIA figures. When the two readings differed by at most 1.5 m the reference was their mean; otherwise a joint adjudication would be logged. All {{irr_agreed}} tanks were resolved by the mean (largest difference {{irr_max_diff}} m). Mean absolute difference was {{irr_mad}} m and Pearson *r* = {{irr_r}}. All readings come from {{product}} ({{scene_date}}; solar elevation {{sun_elev}}°, azimuth {{sun_az}}°).

### Candidate Methods

All methods were frozen before data ingestion, as described in the protocol. M1 applies Otsu thresholding to the B04 band inside the tank's bounding circle and measures the contiguous dark run along the solar azimuth. M2 classifies shadow pixels with a spectral shadow index, SI = (1 − NIR)(1 − Red) / (1 + SWIR1), against a fixed threshold of 0.45, using B02, B03, B04, B08 and B11. M3 interpolates B04 along the azimuth ray with a cubic spline at 1 m steps and places the edge at the maximum positive gradient inside the tank radius. The configuration file lists a different band set and index name for M2 (Note 006 in `docs/deviations.md`); the description above follows the protocol document.

### Question Definitions

For Q1 a tank passes when its absolute residual against the reference is at most {{tol}} m. A method passes when at least {{need_pct}}% of tanks pass and its median absolute residual is at most {{med_max}} m; if no method meets both criteria, Q1 fails. The protocol specifies Holm–Bonferroni correction across the three methods (Holm, 1979) without naming a test statistic. We therefore report a one-sided exact binomial test of the null that a method's pass probability is at most 0.80, Holm-adjusted across the three methods, as a post hoc operationalization (Deviation 003). The verdicts depend only on the registered thresholds.

For Q2, the contrast-to-noise ratio is CNR = |μ_crescent − μ_roof| / σ_noise, where σ_noise is estimated from static paved surfaces beside the tank farms. The registered detectability threshold is CNR ≥ {{cnr_min}}, evaluated for every eligible tank regardless of the Q1 outcome. Q3 is tested if and only if at least one method passes Q1. A physical plausibility check requires 0 ≤ L ≤ (H − 1.5 m) / tan(α), where H is the shell height, and treats an extraction with more than 20% anomalous tanks as invalid.

## Results

### Question 1: Measurement Validity

Q1 fails. No method reached the pass-rate criterion or the median criterion (Table 1). M1 placed {{m1_pass}} of {{n_tanks}} tanks within tolerance, M2 placed {{m2_pass}} and M3 placed {{m3_pass}}. Median absolute residuals were {{m1_median}}, {{m2_median}} and {{m3_median}} m against a requirement of {{med_max}} m. Holm-adjusted *p* values were {{m1_p_holm}} for all three methods, which gives no evidence that any method reaches the gate.

{{table1}}

The errors differ in character. M2 overestimated the shadow on all {{m2_over}} tanks (mean signed residual {{m2_signed}} m), while M1 (mean {{m1_signed}} m; {{m1_over}} overestimates) and M3 (mean {{m3_signed}} m; {{m3_over}} overestimates) erred in both directions. Selecting the best method separately for each tank would not have rescued the result: only {{tanks_any_pass}} of {{n_tanks}} tanks ({{oracle_rate}}%) had at least one method within tolerance, and {{tanks_none_pass}} tanks had none. Figure 1 shows the estimates against the reference in units of the pixel width.

**Figure 1**

*Reference Crescent Length and Automated Estimates in Units of the 10 m Pixel*

![Figure 1. Reference crescent length and automated estimates for the ten tanks, with a 3 m tolerance band, the geometric ceiling for each tank, and shading that alternates every 10 m.](figures/figure1.svg)

*Note.* Markers show M1 (circle), M2 (square) and M3 (triangle). The black tick is the blinded human reference, the gray band is the ±{{tol}} m tolerance, and the dashed line is each tank's geometric ceiling. This figure is built from the per-tank result file; a true radial-profile figure needs the 10 m rasters, which are not distributed with the repository.

### Question 2: Contrast-to-Noise Diagnostic

Q2 fails: the crescent is noise-dominated at 10 m (Table 2). The mean CNR was {{cnr_mean}} (range {{cnr_min_obs}} to {{cnr_max_obs}}) against a threshold of {{cnr_min}}, and all {{cnr_below}} tanks fell below it; all {{cnr_below_1}} were also below 1.0. Noise estimates ranged from {{sigma_min}} to {{sigma_max}} DN and exceeded the contrast between the crescent and roof windows. This gives a mechanistic explanation for the Q1 outcome that does not depend on the details of any one method.

{{table2}}

The signed contrast in Table 2 adds a caution. In {{contrast_reversed}} of {{n_tanks}} tanks the mean DN in the crescent window was higher than in the roof window, the opposite of what a shadow produces. The registered CNR uses an absolute difference, so these tanks still receive a CNR value, but it is not evidence of a shadow signal.

### Physical Plausibility Check

The physical plausibility check did not invalidate any extraction (Table 3): no estimate lay outside the geometric bounds. Even so, {{m2_at_ceiling}} M2 estimates and {{m3_at_ceiling}} M3 estimate sat within 0.1 m of the ceiling, which may indicate that the segmentation extended to the limit of its search range.

{{table3}}

### Question 3: Not Tested

Q3 is not tested. It was registered as conditional on Q1, every method failed Q1, and running it would have compared an invalid measurement series with macro-level benchmark data. No Q3 result is reported.

## Discussion

### Interpretation

Under a protocol fixed in advance, none of the three frozen methods turned a 10 m Sentinel-2 scene into usable shadow lengths for these tanks, and the diagnostic indicates why. A reference crescent of {{ref_px_min}} to {{ref_px_max}} pixels is blended with its surroundings by the sensor's point spread function and by pixel sampling, so the boundary between shadow and lit roof is smeared across the same one or two pixels the method must resolve. The Q2 result quantifies the consequence: the intensity step is smaller than the estimated noise. These explanations are consistent with the data but were not isolated experimentally; the committed files do not contain radial profiles or point-spread measurements.

Mixed-sign errors from M1 and M3 are consistent with edge placement driven by noise. The one-sided bias of M2 suggests its index threshold segmented more than the crescent, though we cannot confirm this without the run's code (Note 007).

For scale, the {{tol}} m tolerance corresponds, at the solar elevation of this scene, to a roof-height change of about {{tol_roof_m}} m. With {{kbbl_per_m_min}} to {{kbbl_per_m_max}} thousand barrels per metre of roof height at the registry radii, that is roughly {{tol_kbbl_min}} to {{tol_kbbl_max}} thousand barrels per tank. This is illustrative arithmetic for cylindrical tanks, not a registered criterion.

### What the Reference Can and Cannot Show

Agreement between inspectors was high ({{irr_mad}} m mean absolute difference), and the inspectors could place a crescent on every tank, which suggests that a person can see the shadow when using the tank outline as context. The reference measures what blinded people read from the same 10 m raster; it is not an in-situ roof-height measurement. It therefore tests whether algorithms reproduce human reading, not physical accuracy. The reference lengths also span a narrow range ({{ref_min}} to {{ref_max}} m), which limits how much variation in fill level the ten tanks represent on this date.

### Limitations

All {{n_tanks}} tanks come from a single acquisition, so tank-to-tank variation and temporal variation are confounded and the effective sample is one scene and one sun geometry. Shadows are longer at lower solar elevation, so a winter scene is plausibly among the more favorable cases for detection; summer geometry would likely be harder, though we did not test it. Ten tanks is a small sample, although the failure is not marginal: even a per-tank best-of-three choice reached {{oracle_rate}}%.

Cloud screening used scene-level cloud cover from the catalogue rather than the tank-footprint Scene Classification Layer rule in the protocol (Note 004). On that basis {{cloud_target_excluded}} of {{cloud_target_items}} products from the two target tiles ({{cloud_target_excluded_pct}}%) exceeded the {{cloud_max}}% threshold, and only {{cloud_primary_clear_dates}} of {{cloud_stac_dates}} acquisition dates were at or below it on the primary tile. Even a method that worked would yield a sparse series.

The M1–M3 and CNR code behind the result files is not in the repository, the rasters are not distributed with it, and the two registered descriptions of M2 differ. These are recorded as Notes 006 and 007, and the single-scene design as Note 005. The scope of the claim is correspondingly narrow: three specific methods, one scene, one site.

### Exploratory History and Voided Analyses

Two earlier events shaped this study and are disclosed in `docs/deviations.md`. In Incident 001, exploratory runs on 2021–2023 data were voided because the extraction code cropped windows from downsampled preview thumbnails of about 290 m per pixel rather than native 10 m rasters; the metrics and the hypothesis claims derived from them were retracted. In Incident 002, a stop gate on ten native 10 m December 2023 verification scenes failed: radial thresholding passed 0 of 10 tanks and sub-pixel gradient detection passed 1 of 10. The 2021–2023 period was therefore closed to confirmatory claims, and the confirmatory study was registered on the unopened 2024 window.

### Implications

The results indicate that the tested 10 m approaches do not give usable shadow lengths at Cushing, and the contrast diagnostic suggests that improvement would have to come from higher resolution or different physics rather than from tuning thresholds on these data. The literature points to candidates: shadow-based estimation with sub-metre to 3 m optical imagery (Wang et al., 2019) and radar methods based on double-bounce geometry (Villamil Lopez & Stilla, 2021; Tsai et al., 2024). We did not test them, and our data cannot say what resolution suffices. Evaluating such sensors under the same pre-registered gate and CNR diagnostic is the natural next step.

## Reproducibility and Code Availability

The repository is at https://github.com/mayankt411/Drip. The protocol lock is commit `ede4a3f`; the result files were committed in `8087717`. Data provenance and SHA-256 checksums are in `data/manifest.csv`, and `src/acquire/verify_manifest.py` checks them against a local checkout (two of the 2024 JSON checksums were computed on CRLF copies; see Note 008). The tables, Figure 1 and every number in this paper are generated from the committed result files by `src/report/make_confirmatory_report.py`, which also checks that its recomputed pass counts, medians and CNR values agree with the committed summary files. The Sentinel-2 rasters are excluded from version control because of their size and must be downloaded from the Copernicus Data Space Ecosystem. The code that produced the three result CSVs from the rasters is not yet committed (Note 007), so the results are archived but not yet regenerable from this repository alone.

## References

DigitalGlobe satellite validates U.S. oil inventory. (2011, August 1). *EI Journal*. https://eijournal.com/?p=4661

Drusch, M., Del Bello, U., Carlier, S., Colin, O., Fernandez, V., Gascon, F., Hoersch, B., Isola, C., Laberinti, P., Martimort, P., Meygret, A., Spoto, F., Sy, O., Marchese, F., & Bargellini, P. (2012). Sentinel-2: ESA's optical high-resolution mission for GMES operational services. *Remote Sensing of Environment, 120*, 25–36. https://doi.org/10.1016/j.rse.2011.11.026

European Space Agency. (n.d.). *MultiSpectral Instrument (MSI) overview*. Sentinel-2 MSI Technical Guide, Copernicus Sentinel Online. Retrieved November 4, 2026, from https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/msi-instrument

Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics, 6*(2), 65–70.

Kayrros. (2021, August 18). *Drone flights over Cushing: Bringing transparency on crude inventories to 100%*. https://kayrros.com/drone-flights-over-cushing-bringing-transparency-on-crude-inventories-to-100/

Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The preregistration revolution. *Proceedings of the National Academy of Sciences, 115*(11), 2600–2606. https://doi.org/10.1073/pnas.1708274114

Tsai, Y.-L. S., Huang, C.-J., Chen, C.-L., & Han, J.-Y. (2024). Automatic monitoring of oil tank 3D geometry and storage changes with interferometric coherence and SAR intensity information. *IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing, 17*, 1584–1595. https://doi.org/10.1109/JSTARS.2023.3337126

Villamil Lopez, C., & Stilla, U. (2021). Monitoring of oil tank filling with spaceborne SAR using coherent scatterers. *IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing, 14*, 5638–5655. https://doi.org/10.1109/JSTARS.2021.3082181

Wang, Q., Zhang, J., & Hu, X. (2016). Automatic oil reserve analysis through the shadows of exterior floating crest oil tanks in highlight optical satellite images. In G. Bebis et al. (Eds.), *Advances in visual computing: ISVC 2016* (Lecture Notes in Computer Science, Vol. 10073, pp. 23–32). Springer. https://doi.org/10.1007/978-3-319-50832-0_3

Wang, T., Li, Y., Yu, S., & Liu, Y. (2019). Estimating the volume of oil tanks based on high-resolution remote sensing images. *Remote Sensing, 11*(7), Article 793. https://doi.org/10.3390/rs11070793
