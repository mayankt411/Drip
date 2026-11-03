# Pre-Registration Protocol & Study Classification Notice

## Study Classification: EXPLORATORY (Post-Hoc Disclosed)
> **CRITICAL SCIENTIFIC INTEGRITY DISCLOSURE:**
> Although the chronological 60/40 split, hypothesis statements, and evaluation criteria were formulated prior to final manuscript drafting, formal cryptographic pre-registration on an immutable ledger (e.g. OSF / AsPredicted) was **NOT** executed prior to inspecting the 2021–2023 Sentinel-2 catalogue. Furthermore, an earlier evaluation run was conducted on flawed thumbnail rasters and formally voided (see [deviations.md](file:///C:/Users/Mayan/.gemini/antigravity/scratch/oil-tank-inventory/docs/deviations.md), Incident 001).
> 
> Therefore, in accordance with open-science standards and peer-review integrity guidelines:
> - **All hypotheses (H1, H2, H3) are classified and reported as EXPLORATORY, not confirmatory.**
> - P-values and confidence intervals are descriptive diagnostics.
> - The held-out split remains strictly chronological (development: 2021-01-01 to 2022-10-14; validation: 2022-10-19 to 2023-12-31).

---

## Registered Protocol & Methodological Quality Controls

### 1. Physical Quality Control (QC) Boundary
Any extracted shadow length $L$ must strictly satisfy the physical geometric bound:
$$0 \le L \le \frac{H_{\text{shell}} - 1.5}{\tan(\alpha)}$$
where $H_{\text{shell}}$ is the tank shell height (18.0 m) and $\alpha$ is the solar elevation angle at overpass.
- Any candidate measurement outside this range is rejected as physically anomalous (e.g. cloud shadow, terrain artifact, or sub-pixel noise).
- Values are **never clipped** into the interval; rejections are logged transparently with exact counts and reasons.

### 2. Differencing & Missing Observation Rule
Week-to-week changes $\Delta S_t = S_t - S_{t-1}$ are defined **only** when both week $t$ and week $t-1$ contain a valid, cloud-free, QC-passing satellite observation.
- If week $t-1$ was occluded by clouds ($>40\%$ cloud cover) or failed QC, $\Delta S_t$ is recorded as missing (`NaN`). Multi-week bridging differences are strictly barred from the single-week difference analysis.
- Valid sample size $N_{\text{diff}}$ must be reported for every lag.

### 3. Autocorrelation & Block-Bootstrap Procedure
To account for temporal serial dependence in weekly inventory changes:
- Block bootstrap with block length $B = 4$ weeks is the primary resampling method (1,000 resamples).
- Sensitivity checks across alternative block sizes $B \in \{2, 4, 8\}$ weeks must be reported in full.

### 4. Calibration Protocol (Zero Leakage)
- Scaling/calibration parameters ($k_{\text{scale}}, b_0$) may only be estimated on the development partition (2021-01-01 to 2022-10-14).
- Level correlations ($r$) must be reported on **uncalibrated raw volumes** first, followed by calibrated figures.
- Primary information-content tests evaluate first-differences ($\Delta S_t, \Delta E_t$), which are invariant to scale and shift.

---

## Registered Hypotheses (Exploratory Benchmark Targets)

### Hypothesis 1 (H1: Inventory Level Tracking)
- **Statement:** Aggregated weekly satellite estimates across the tank registry correlate positively with official EIA weekly Cushing crude stocks in the held-out validation period.
- **Metric:** Pearson correlation coefficient $r$, Spearman rank correlation $\rho$, and $R^2$.
- **Pre-registered Success Threshold:** $r > 0.40$ with two-tailed $p < 0.05$.
- **Status:** PENDING (Awaiting 10m native band extraction).

### Hypothesis 2 (H2: Cloud Degradation)
- **Statement:** The Mean Absolute Percentage Error (MAPE) of the satellite volume estimate is higher in cloudy weeks (cloud cover above development-period median) than in clear weeks (cloud cover below median).
- **Metric:** $\Delta \text{MAPE} = \text{MAPE}_{\text{cloudy}} - \text{MAPE}_{\text{clear}}$.
- **Pre-registered Success Threshold:** $\Delta \text{MAPE} > 0$ with one-tailed permutation test $p < 0.05$.
- **Status:** PENDING (Awaiting 10m native band extraction).

### Hypothesis 3 (H3: First-Difference Information Content)
- **Statement:** Week-to-week changes in satellite-estimated volume ($\Delta S_t = S_t - S_{t-1}$) are correlated with week-to-week changes in official EIA stocks ($\Delta E_{t+k}$) at lags $k \in \{0, 1, 2\}$.
- **Metric:** Lagged Pearson correlation $r_k$ with block-bootstrap 95% confidence intervals.
- **Pre-registered Success Threshold:** $r_0 > 0.20$ or $r_1 > 0.20$ with bootstrap CI excluding 0 (with multiple-comparison disclosure).
- **Status:** PENDING (Awaiting 10m native band extraction).
