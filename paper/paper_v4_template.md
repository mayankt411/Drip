---
title: "Can Free Sentinel-1 Radar Track Crude Oil Storage at Cushing, Oklahoma? A Pre-Specified Test"
---

# Abstract

{{abstract}}

# Method

Backscatter (VV and VH, radiometrically terrain-corrected) was read for each of the {{n_tanks}} mapped tanks on every Sentinel-1 pass from {{train_start}} to June 2024 ({{n_passes}} pass-orbit combinations). For each tank and orbit, the training-period mean was subtracted, so the features measure how far a tank sits from its own usual return: disc mean VV, disc maximum VV, disc mean VH, and disc minus rim VV. Features were averaged over tanks (weighted by footprint area), then over each EIA week. A ridge regression with time-blocked cross-validation was fitted on weeks up to 2022 and scored once on 2023 to June 2024. The seasonal baseline uses day-of-year harmonics fitted on the same training weeks.

The criteria were fixed in advance: *r* ≥ 0.65, *p* < .001, a bootstrap interval above zero, first-difference intervals above zero at lags 0 and 1, and an *R*² above both baselines.

# Results

{{table}}

{{sentence}}

![Radar prediction against EIA stocks, test weeks]({{figure}})

# Limitations

Free 10 m imagery gives 4 to 30 pixels per tank. Tank roof type is unlabelled in OpenStreetMap, so floating-roof tanks could not be isolated. EIA reports the whole Cushing hub, while the registry covers mapped tanks only. Weeks without a pass are left blank rather than filled.
