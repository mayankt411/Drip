# Pre-Registration Status & Study Classification Notice

## Study Classification: EXPLORATORY (Post-Hoc Disclosed)
> **CRITICAL SCIENTIFIC INTEGRITY DISCLOSURE:**
> Although the chronological 60/40 split, hypothesis statements, and evaluation criteria were formulated prior to final manuscript drafting, formal cryptographic pre-registration on an immutable ledger (e.g. OSF / AsPredicted) was **NOT** executed prior to inspecting the 2021–2023 Sentinel-2 catalogue and running exploratory data calibrations.
> 
> Therefore, in accordance with open-science standards and peer-review integrity guidelines:
> - **All hypotheses (H1, H2, H3) are classified and reported as EXPLORATORY, not confirmatory.**
> - P-values and confidence intervals must be interpreted as descriptive diagnostics rather than confirmatory Neyman-Pearson hypothesis tests.
> - The locked test split remains strictly chronological (evaluation on the latest 40% of weeks: 2022-10-19 to 2023-12-31), but is reported transparently as a held-out validation set.

## Registered Hypotheses (Exploratory Benchmark Targets)

### Hypothesis 1 (H1: Inventory Level Tracking)
- **Statement:** Aggregated weekly satellite estimates across the tank registry correlate positively with official EIA weekly Cushing crude stocks in the locked test period.
- **Metric:** Pearson correlation coefficient $r$, Spearman rank correlation $\rho$, and $R^2$.
- **Pre-registered Success Threshold:** $r > 0.40$ with two-tailed $p < 0.05$.
- **Status:** NOT TESTED (Test period unopened).

### Hypothesis 2 (H2: Cloud Degradation)
- **Statement:** The Mean Absolute Percentage Error (MAPE) of the satellite volume estimate is higher in cloudy weeks (cloud cover above development-period median) than in clear weeks (cloud cover below median).
- **Metric:** $\Delta \text{MAPE} = \text{MAPE}_{\text{cloudy}} - \text{MAPE}_{\text{clear}}$.
- **Pre-registered Success Threshold:** $\Delta \text{MAPE} > 0$ with one-tailed permutation test $p < 0.05$.
- **Status:** NOT TESTED (Test period unopened).

### Hypothesis 3 (H3: First-Difference Information Content)
- **Statement:** Week-to-week changes in satellite-estimated volume ($\Delta S_t = S_t - S_{t-1}$) are correlated with week-to-week changes in official EIA stocks ($\Delta E_{t+k}$) at lags $k \in \{0, 1, 2\}$.
- **Metric:** Lagged Pearson correlation $r_k$ with block-bootstrap 95% confidence intervals.
- **Pre-registered Success Threshold:** $r_0 > 0.20$ or $r_1 > 0.20$ with bootstrap CI excluding 0.
- **Status:** NOT TESTED (Test period unopened).
