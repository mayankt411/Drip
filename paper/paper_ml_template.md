---
title: "Hub-Level Deep Learning on Free 10-Meter Sentinel-2 Imagery for Cushing Crude Storage: An Exploratory Follow-Up to a Negative Pre-Registered Result"
---

# Abstract

A pre-registered study found that geometric shadow methods on free 10 m Sentinel-2 imagery could not recover floating-roof heights at Cushing, Oklahoma (mean crescent-to-roof contrast-to-noise ratio {{prior_cnr_mean}} against a threshold of 2.0). This follow-up asks a different question: can a convolutional network, trained on {{train_window}} and tested on {{test_window}}, track weekly EIA Cushing stocks from tank-level image chips? Tank locations come from OpenStreetMap, a YOLO detector is evaluated on held-out terminals, and a chip-level network is supervised only by hub-level EIA totals. The analysis is exploratory because the test period had already been inspected in the earlier study. {{h1_sentence}} {{h3_sentence}} {{baseline_sentence}} Per-tank fill accuracy could not be tested because no per-tank labels exist.

# 1. Introduction

The earlier pre-registered study (Protocol 2.0.0) tested three shadow-geometry methods on {{prior_n_tanks}} tanks in one scene. The methods met the accuracy criterion on {{prior_m1_pass}}, {{prior_m2_pass}} and {{prior_m3_pass}} tanks respectively, and the roof-contrast check failed. That result says shadow geometry is too weak at 10 m. It does not say the imagery carries no inventory signal. A learned model can use reflectance and context that a geometric method ignores, so the question is worth one more test, with baselines for season and sun angle and an honest label of its status.

This paper reports that test. It is **not** confirmatory. The 2023 and 2024 windows were opened during the earlier study, and the design here was chosen after seeing that result.

# 2. Data

**Imagery.** Sentinel-2 L2A scenes for tiles T14SQE and T14SPE, cloud cover at most 20% at product level, mosaicked onto a common 10 m grid. Bands B02, B03, B04 and B08 are native 10 m; B11 and B12 are resampled from 20 m. Reflectance is DN scaled by the per-product offset and gain.

**Tank registry.** Storage tanks were taken from OpenStreetMap (man_made=storage_tank) around Cushing. Diameter comes from the footprint polygon where available. OSM carries no capacity, so each tank is weighted by its footprint area. This is a proxy, not capacity.

**Labels.** There are no per-tank fill labels. The only supervision is the EIA weekly Cushing stock series, which covers the whole hub and includes tanks outside the registry.

**Splits.** Training uses {{train_window}}. Testing uses {{test_window}}. For detection, whole terminals (clusters of tanks within 1.5 km) are held out, so test tanks are spatially separate from training tanks.

# 3. Methods

**Detection (Stage 1).** A YOLOv8-nano detector was trained on 4x upscaled false-colour windows (B04, B03, B02) with labels drawn automatically from OSM footprints. It is scored on held-out terminals on test-period dates. Three detector sizes (the YOLOv8-nano baseline, YOLOv8-small and YOLO11-small) were trained on the same data and compared on validation images from the training terminals; the one with the highest validation mAP@50 was kept. Hypothesis H1: mAP@50 at least {{h1_map50_min}} and precision at least {{h1_precision_min}}.

**Fill regression (Stage 2).** A small convolutional network takes a 16 x 16 x 6 chip per tank plus sun-geometry inputs and outputs a fill fraction. The hub estimate is the area-weighted mean fill over valid tanks, mapped to barrels by a positive affine transform fitted against EIA on training weeks. Five seeds are averaged. Early stopping uses a chronological inner validation split inside the training years.

**Baselines.** To control for season and sun angle, the CNN is compared with (a) the training mean, (b) ridge regression on area-weighted disc reflectance (B04, B08, B11) plus sun elevation, (c) ridge on the same four sun-geometry terms the CNN receives, and (d) ridge on day-of-year harmonics.

**Statistics (Stage 3).** Pearson r, Spearman rho and R-squared on weekly pairs; first-difference correlation at lag 0 and 1 using strictly consecutive weeks. Confidence intervals use a stationary block bootstrap (mean block {{block}} weeks, {{n_boot}} draws). Hypothesis H3 requires, on the test weeks, (i) r of at least {{level_r_min}} with a naive p below .001 and a bootstrap interval above zero, because the naive test ignores autocorrelation; (ii) bootstrap intervals above zero for the first-difference correlation at **both** lag 0 and lag 1; and (iii) a higher R-squared than every baseline. H2 (per-tank MAE below 15% of capacity) is not tested.

# 4. Results

{{table_yolo}}

{{h1_sentence}}

{{table_yolo_compare}}

{{compare_sentence}}

{{table_cnn}}

{{table_eia}}

{{h3_sentence}} {{baseline_sentence}}

![Detection on held-out terminals](figures/yolo_detection.svg)

![CNN hub estimate against EIA](figures/eia_vs_satellite_ml.svg)

# 5. Discussion

{{discussion}}

# 6. Limitations

1. The analysis is post hoc and the test windows were inspected earlier, so results are exploratory.
2. The detector was chosen after a first configuration narrowly missed H1, so the final H1 result carries a small selection effect; the selection used validation data only and all configurations are reported.
3. The registry comes from OSM and has no capacity. Area weights are a proxy.
4. Supervision is hub-level and weak; the network is not shown to read individual tank fill, and H2 is untested.
5. Auto-labelled detection ground truth is noisy: tanks absent from OSM count as false positives.
6. The number of weekly pairs is small, so intervals are wide and the naive p-value is optimistic.
7. EIA Cushing stocks include fixed-roof tanks and pipeline fill, which satellites cannot see in the same way.
8. Seasonal and sun-angle effects confound any single-hub series, even with baselines.

# 7. Conclusion

{{h3_sentence}} The earlier negative result on shadow geometry stands unchanged. Any positive finding here needs confirmation on a window not previously opened.

# Data and Code Availability

Code, configuration and the checksum manifest are in the project repository. Raw imagery and EIA data are public. All numbers in this paper are generated from files in `results/` by `src/ml/report.py`.
