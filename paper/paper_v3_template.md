---
title: "Automated Asset Census, Structural Classification and Macro Activity Tracking of Crude Oil Storage at Cushing, Oklahoma, Using Sentinel-2 and Deep Learning"
---

# Abstract

This exploratory study asks three questions about free 10 m Sentinel-2 imagery of the Cushing storage hub: can a detector find the tanks, can a network tell floating-roof from fixed-dome tanks, and does a hub-level spectral activity index follow EIA stocks? {{h1_sentence}} {{h2_sentence}} {{h3_sentence}} The analysis is post hoc: the 2023 and 2024 windows were inspected in an earlier pre-registered study and in a first ML analysis, and targets were set after those results.

# 1. Background

An earlier pre-registered study found that shadow geometry could not recover floating-roof height at 10 m. A first ML analysis then showed that a CNN supervised by hub-level EIA stocks did not track them. This framework asks narrower questions that 10 m imagery might support.

# 2. Data

Sentinel-2 L2A tiles T14SQE and T14SPE, bands B02, B03, B04, B08, B11 and B12 on a common 10 m grid. Tanks come from OpenStreetMap. Development years are 2021–2022 and evaluation years 2023–2024. Test tanks come from held-out terminal clusters. EIA stocks are series W_EPC0_SAX_YCUOK_MBBL.

# 3. Methods

**H1.** A YOLO detector is trained on training terminals and scored on held-out terminals. Detector sizes were compared on validation images only.

**H2.** Structural labels come only from OSM roof tags. A small CNN on temporal-mean multi-spectral chips is compared with a ridge classifier and with the majority class. Operational labels (active versus idle) have no independent source, so that task is not tested. Per-tank spectral variance is saved as a descriptive index only.

**H3.** The activity index is each tank's relative departure from its own development-year reflectance in B04, B08 and B11, area-weighted across valid tanks and averaged by week. It is not a stock level. It is correlated with EIA stocks, raw and as a 4-week mean, with a stationary block bootstrap and a day-of-year control fitted on development years. H3 passes only if r, the naive p, a bootstrap interval above zero and the control comparison all pass.

# 4. Results

{{table_h1}}

{{h1_sentence}}

{{table_h2}}

{{h2_sentence}} {{h2_op_sentence}}

{{table_h3}}

![Activity index and EIA stocks](figures/macro_utilization.svg)

{{h3_sentence}}

# 5. Limitations

1. The analysis is post hoc and targets followed earlier results.
2. OSM roof tags may be sparse, which limits H2.
3. Activity cannot be validated without independent operational labels.
4. Smoothing EIA stocks makes weekly points dependent, so naive p-values are optimistic.
5. The activity index is confounded with season and vegetation, which the day-of-year control only partly addresses.
6. The registry has few terminal clusters, so the spatial split is coarse.

# 6. Conclusion

{{h3_sentence}} Any positive result needs confirmation on a window not previously opened.
