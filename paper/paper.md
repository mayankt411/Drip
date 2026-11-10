---
title: "Hub-Level Deep Learning on Free 10-Meter Sentinel-2 Imagery for Cushing Crude Storage: An Exploratory Follow-Up to a Negative Pre-Registered Result"
---

# Abstract

A pre-registered study found that geometric shadow methods on free 10 m Sentinel-2 imagery could not recover floating-roof heights at Cushing, Oklahoma (mean crescent-to-roof contrast-to-noise ratio 0.34 against a threshold of 2.0). This follow-up asks a different question: can a convolutional network, trained on 2021-01-01 to 2022-12-31 and tested on 2023-01-01 to 2024-06-30, track weekly EIA Cushing stocks from tank-level image chips? Tank locations come from OpenStreetMap, a YOLO detector is evaluated on held-out terminals, and a chip-level network is supervised only by hub-level EIA totals. The analysis is exploratory because the test period had already been inspected in the earlier study. The detector met the thresholds on the held-out terminals: mAP@50 was 0.876 and precision 0.900. The CNN hub series did not meet all of the level, first-difference and baseline criteria. On test weeks the CNN did not have a higher R² than every baseline (best baseline: Training mean, R² = −0.02; CNN R² = −0.51). Per-tank fill accuracy could not be tested because no per-tank labels exist.

# 1. Introduction

The earlier pre-registered study (Protocol 2.0.0) tested three shadow-geometry methods on 10 tanks in one scene. The methods met the accuracy criterion on 3, 1 and 2 tanks respectively, and the roof-contrast check failed. That result says shadow geometry is too weak at 10 m. It does not say the imagery carries no inventory signal. A learned model can use reflectance and context that a geometric method ignores, so the question is worth one more test, with baselines for season and sun angle and an honest label of its status.

This paper reports that test. It is **not** confirmatory. The 2023 and 2024 windows were opened during the earlier study, and the design here was chosen after seeing that result.

# 2. Data

**Imagery.** Sentinel-2 L2A scenes for tiles T14SQE and T14SPE, cloud cover at most 20% at product level, mosaicked onto a common 10 m grid. Bands B02, B03, B04 and B08 are native 10 m; B11 and B12 are resampled from 20 m. Reflectance is DN scaled by the per-product offset and gain.

**Tank registry.** Storage tanks were taken from OpenStreetMap (man_made=storage_tank) around Cushing. Diameter comes from the footprint polygon where available. OSM carries no capacity, so each tank is weighted by its footprint area. This is a proxy, not capacity.

**Labels.** There are no per-tank fill labels. The only supervision is the EIA weekly Cushing stock series, which covers the whole hub and includes tanks outside the registry.

**Splits.** Training uses 2021-01-01 to 2022-12-31. Testing uses 2023-01-01 to 2024-06-30. For detection, whole terminals (clusters of tanks within 1.5 km) are held out, so test tanks are spatially separate from training tanks.

# 3. Methods

**Detection (Stage 1).** A YOLOv8-nano detector was trained on 4x upscaled false-colour windows (B04, B03, B02) with labels drawn automatically from OSM footprints. It is scored on held-out terminals on test-period dates. Three detector sizes (the YOLOv8-nano baseline, YOLOv8-small and YOLO11-small) were trained on the same data and compared on validation images from the training terminals; the one with the highest validation mAP@50 was kept. Hypothesis H1: mAP@50 at least 0.85 and precision at least 0.80.

**Fill regression (Stage 2).** A small convolutional network takes a 16 x 16 x 6 chip per tank plus sun-geometry inputs and outputs a fill fraction. The hub estimate is the area-weighted mean fill over valid tanks, mapped to barrels by a positive affine transform fitted against EIA on training weeks. Five seeds are averaged. Early stopping uses a chronological inner validation split inside the training years.

**Baselines.** To control for season and sun angle, the CNN is compared with (a) the training mean, (b) ridge regression on area-weighted disc reflectance (B04, B08, B11) plus sun elevation, (c) ridge on the same four sun-geometry terms the CNN receives, and (d) ridge on day-of-year harmonics.

**Statistics (Stage 3).** Pearson r, Spearman rho and R-squared on weekly pairs; first-difference correlation at lag 0 and 1 using strictly consecutive weeks. Confidence intervals use a stationary block bootstrap (mean block 4 weeks, 10000 draws). Hypothesis H3 requires, on the test weeks, (i) r of at least 0.70 with a naive p below .001 and a bootstrap interval above zero, because the naive test ignores autocorrelation; (ii) bootstrap intervals above zero for the first-difference correlation at **both** lag 0 and lag 1; and (iii) a higher R-squared than every baseline. H2 (per-tank MAE below 15% of capacity) is not tested.

# 4. Results

**Table 1**

*Tank Detection on Held-Out Terminals (Test Dates 2023–2024)*

| Metric | Value | Pre-specified threshold |
|:--|--:|--:|
| Precision | 0.900 | ≥ 0.80 |
| Recall | 0.903 | n/a |
| mAP@50 | 0.876 | ≥ 0.85 |
| mAP@50–95 | 0.453 | n/a |
| Test images / labelled tanks | 620 / 18047 | n/a |

*Note.* Precision and recall are at the deployment confidence threshold; mAP uses all thresholds. Labels come from OpenStreetMap footprints, so they are noisy; detections of tanks missing from OSM count as false positives.

The detector met the thresholds on the held-out terminals: mAP@50 was 0.876 and precision 0.900.

**Table 1b**

*Detector Sizes Compared; Selection by Validation mAP@50*

| Model | Params (M) | Val mAP@50 | Test mAP@50 | Test precision | Test recall | Selected |
|:--|--:|--:|--:|--:|--:|:--|
| baseline_yolov8n | 3.1 | 0.993 | 0.849 | 0.880 | 0.883 |  |
| yolo11s | 9.4 | 0.993 | 0.882 | 0.892 | 0.917 |  |
| yolov8s | 11.1 | 0.994 | 0.876 | 0.900 | 0.903 | yes |

*Note.* The model was chosen on validation images (2022 dates, training terminals) only. Test columns are reported for every model for transparency and did not influence the choice.

3 detector configurations were compared on validation mAP@50 and yolov8s was selected (validation 0.9937); on the held-out terminals it reached mAP@50 0.876. Validation mAP@50 was saturated (all models within 0.0005), so it could not separate them; the choice is therefore close to arbitrary. On the held-out terminals every larger model scored higher than the baseline (baseline 0.849).

**Table 2**

*Hub-Level CNN Training and Per-Tank Validation Status*

| Item | Value |
|:--|--:|
| Training dates (fit / inner validation) | 47 / 12 |
| Ensemble seeds | 5 |
| Best inner-validation MSE, standardized (mean over seeds) | 0.049 |
| Per-tank fill MAE, RMSE, R² (H2) | not testable |

*Note.* No per-tank fill-level labels exist, so the network is trained against hub-level EIA stocks only and H2 is not tested. MSE is on z-scored EIA stocks.

**Table 3**

*Agreement With EIA Weekly Cushing Stocks on the Held-Out Test Period*

| Method | Tank source | *n* | *r* | *p* | 95% CI | ρ | *R*² | Δ lag 0 *r* [CI] | Δ lag 1 *r* [CI] |
|:--|:--|--:|--:|--:|:--|--:|--:|:--|:--|
| CNN | registry | 37 | 0.30 | .067 | [−0.08, 0.59] | 0.21 | −0.51 | −0.16 [−0.74, 0.26] | 0.05 [−0.54, 0.73] |
| CNN | yolo | 37 | 0.32 | .052 | [−0.05, 0.60] | 0.22 | −0.51 | −0.15 [−0.75, 0.31] | 0.06 [−0.55, 0.73] |
| Ridge (B04, B08, B11, sun) | registry | 37 | −0.33 | .050 | [−0.60, 0.04] | −0.27 | −0.24 | −0.31 [−0.70, 0.44] | −0.31 [−0.61, 0.64] |
| Ridge (B04, B08, B11, sun) | yolo | 37 | −0.33 | .045 | [−0.61, 0.04] | −0.29 | −0.24 | −0.33 [−0.71, 0.44] | −0.33 [−0.62, 0.65] |
| Ridge (day of year) | registry | 37 | 0.08 | .639 | [−0.39, 0.49] | 0.03 | −0.03 | 0.21 [−0.73, 0.91] | 0.20 [−0.84, 0.87] |
| Ridge (day of year) | yolo | 37 | 0.08 | .642 | [−0.39, 0.49] | 0.03 | −0.03 | 0.21 [−0.73, 0.91] | 0.20 [−0.84, 0.87] |
| Ridge (sun geometry only) | registry | 37 | −0.44 | .007 | [−0.73, −0.06] | −0.44 | −0.19 | −0.29 [−0.85, 0.68] | −0.25 [−0.87, 0.72] |
| Ridge (sun geometry only) | yolo | 37 | −0.44 | .007 | [−0.73, −0.06] | −0.44 | −0.19 | −0.29 [−0.85, 0.68] | −0.25 [−0.87, 0.72] |
| Training mean | registry | 37 | n/a | n/a | [n/a, n/a] | n/a | −0.02 | n/a | n/a |
| Training mean | yolo | 37 | n/a | n/a | [n/a, n/a] | n/a | −0.02 | n/a | n/a |

*Note.* Level statistics use weeks with a valid satellite pass. *p* is the naive Pearson test and ignores autocorrelation; intervals are stationary block bootstrap (mean block 4 weeks, 10000 draws). Δ columns use consecutive weeks only. Models were fit on 2021–2022 only.

The CNN hub series did not meet all of the level, first-difference and baseline criteria. On test weeks the CNN did not have a higher R² than every baseline (best baseline: Training mean, R² = −0.02; CNN R² = −0.51).

![Detection on held-out terminals](figures/yolo_detection.svg)

![CNN hub estimate against EIA](figures/eia_vs_satellite_ml.svg)

# 5. Discussion

On the test weeks the CNN hub series had r = 0.32 (95% bootstrap CI [−0.05, 0.60]) and R² = −0.51 against EIA stocks. The estimates spanned only 27–30 million bbl on test weeks while EIA spanned 21–43; on training weeks the estimates spanned 27–32 against 21–59. The network therefore did not reproduce the stock variation even in the years it was fitted on, which points to a weak signal at this resolution and label quality rather than to overfitting. A model that sees only sun geometry reached r = −0.44 on the same weeks, so correlations of either sign of this size can arise from season and sun angle alone. The first-difference correlations, which remove shared slow trends, were small and their intervals include zero.

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

The CNN hub series did not meet all of the level, first-difference and baseline criteria. The earlier negative result on shadow geometry stands unchanged. Any positive finding here needs confirmation on a window not previously opened.

# Data and Code Availability

Code, configuration and the checksum manifest are in the project repository. Raw imagery and EIA data are public. All numbers in this paper are generated from files in `results/` by `src/ml/report.py`.
