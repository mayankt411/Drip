# Pre-Registration Document v2.0 (CONFIRMATORY PROTOCOL)
**Title:** Confirmatory Evaluation of Free 10 m Sentinel-2 Imagery for Floating-Roof Oil Storage Shadow Extraction at Cushing, Oklahoma  
**Protocol Version:** 2.0.0  
**Registration Date:** 2026-11-03  
**Status:** FROZEN PRIOR TO OPENING TEST WINDOW  

---

## 1. Study Area and AOI Definition
- **Geographic Area:** Cushing Commercial Crude Oil Hub, Payne County, Oklahoma, USA.
- **Center Coordinates:** Latitude $35.9800^\circ\text{N}$, Longitude $-96.7700^\circ\text{W}$ (EPSG:4326).
- **Bounding Box (`configs/aoi.yaml`):**
  - West: $-96.8500^\circ$, East: $-96.6900^\circ$
  - South: $35.9100^\circ$, North: $36.0500^\circ$
- **Target MGRS Tiles:** `T14SQE` (primary), `T14SPE` (secondary western overlap), projected to UTM Zone 14N (EPSG:32614).

---

## 2. Tank Eligibility and Registry
- **Eligibility Criteria:**
  1. Verified external floating-roof crude storage tank located within the Cushing terminal footprint.
  2. Ground-truth shell height ($H \ge 15.0\text{ m}$) and diameter ($D \ge 60.0\text{ m}$) established and verified.
  3. Clear spatial separation from neighboring structures to prevent inter-tank shadow occlusion.
- **Pre-Declared Eligible Tank Count:** $N = 10$ tanks, recorded in `data/tanks/tank_registry.csv`. No tanks will be added, removed, or substituted post-hoc.

---

## 3. Human Reference Measurement Protocol
- **Blinded Independent Inspection:** Manual readings conducted independently by two trained remote sensing inspectors.
- **Protocol:**
  - True color (`TCI_10m`) and Red band (`B04_10m`) rasters displayed under linear 2% percentile stretch at $1:1$ native pixel resolution.
  - Shadow crescent length ($L_{\text{ref}}$) measured along the solar azimuth line from the southern tank shell rim to the inner shadow-illuminated floor boundary.
  - Inspectors are strictly blind to automated algorithm outputs and official EIA weekly inventory figures.
- **Disagreement Resolution:** If $|L_1 - L_2| \le 1.5\text{ m}$, the reference value is the arithmetic mean $(L_1 + L_2)/2$. If $|L_1 - L_2| > 1.5\text{ m}$, a joint adjudication is performed and logged in `data/manual_readings_v2.csv`.
- **Inter-Rater Reliability:** Reported via Pearson $r$ and Mean Absolute Difference (MAD).

---

## 4. Candidate Measurement Methods (M1, M2, M3)
All candidate methods are strictly frozen prior to data ingestion:

### Method 1 (M1: Single-Band Threshold Crescent Extraction)
- **Spectral Band:** Native Level-2A Red Band (`B04`, $10\text{ m}$ GSD).
- **Search Vector:** Radial transect oriented along the exact solar azimuth $\theta_{\text{sun}}$.
- **Segmentation:** Otsu bimodal thresholding within the circumscribed tank bounding circle. Shadow length is computed as the radial chord of contiguous sub-threshold pixels along the illumination axis.

### Method 2 (M2: Multi-Band Spectral Index Classifier)
- **Spectral Bands:** `B02` (Blue), `B03` (Green), `B04` (Red), `B08` (NIR), `B11` (SWIR1).
- **Index Formulation:** Spectral Shadow Index $\text{SI} = \frac{(1 - \text{NIR}) \times (1 - \text{Red})}{1 + \text{SWIR1}}$.
- **Classification:** Pixels exceeding the empirical shadow index threshold $\tau_{\text{SI}} = 0.45$ within the tank perimeter are classified as interior shadow. Shadow length $L_{\text{M2}}$ is derived from the segmented crescent width along $\theta_{\text{sun}}$.

### Method 3 (M3: Sub-Pixel Gradient Radial Profile)
- **Spectral Band:** Native `B04` ($10\text{ m}$ GSD).
- **Sub-Pixel Profile:** Continuous 1D cubic spline interpolation of digital numbers along the solar azimuth ray at $0.1\text{ pixel}$ ($1.0\text{ m}$) steps.
- **Edge Localization:** Numerical differentiation of the profile; the shadow-to-roof transition boundary is localized at the maximum positive gradient $\max(d\text{DN}/dr)$ bounded within the physical tank radius.

---

## 5. Pre-Registered Hypotheses & Decision Rules

### Question 1 (Q1: Measurement Validity & Gate)
- **Hypothesis:** At least one automated method (M1, M2, or M3) accurately reproduces human-verified shadow lengths on the locked test tanks.
- **Individual Tank Tolerance:** Absolute residual $|\hat{L}_i - L_{\text{ref}, i}| \le 3.0\text{ m}$.
- **Method Pass Criteria:**
  1. Pass Rate $\ge 80\%$ (at least 8 out of 10 eligible tanks within $\pm 3.0\text{ m}$).
  2. Median Absolute Residual $\le 2.0\text{ m}$.
- **Multiple Comparisons:** Holm-Bonferroni correction applied across the three methods.
- **Decision Outcome:** If no method meets both criteria, **Q1 FAILS**.

### Question 2 (Q2: Measurement Contrast-to-Noise Diagnostic)
- **Hypothesis:** The physical contrast between the shadow crescent and surrounding surfaces exceeds sensor noise at $10\text{ m}$ resolution.
- **Metric:** Contrast-to-Noise Ratio (CNR):
  $$\text{CNR} = \frac{|\mu_{\text{crescent}} - \mu_{\text{roof}}|}{\sigma_{\text{noise}}}$$
  where $\sigma_{\text{noise}}$ is estimated from invariant static paved surfaces adjacent to the tank farms.
- **Threshold for Detectable Signal:** $\text{CNR} \ge 2.0$.
- **Reporting:** Evaluated and reported unconditionally across all eligible tanks, serving as the diagnostic explanation if Q1 fails.

### Question 3 (Q3: Information Content & Forecasting - Strictly Conditional)
- **Condition:** **Tested IF AND ONLY IF at least one method passes Q1.** If all methods fail Q1, Q3 is **NOT TESTED** and reported as non-applicable.
- **Procedure:** Week-to-week changes $\Delta S_t = S_t - S_{t-1}$ evaluated against EIA weekly stock changes $\Delta E_{t+k}$ at lags $k \in \{0, 1\}$.
- **Missing Data Rule:** $\Delta S_t$ is computed **only** for strictly consecutive cloud-free weeks ($t$ and $t-1$ both valid). Multi-week bridging is barred.
- **Autocorrelation Correction:** Stationary block bootstrap with block length $B = 4$ weeks (1,000 iterations), with sensitivity reported at $B \in \{2, 8\}$.

---

## 6. Physical Quality Controls and Cloud Rules
1. **Physical Elevation Bounds:** For every observation, the shadow length must satisfy:
   $$0 \le L \le \frac{H - 1.5}{\tan(\alpha)}$$
   Any measurement violating this condition is flagged as physically anomalous. An extraction with $>20\%$ anomalous tanks is invalid.
2. **Cloud Threshold:** Scenes are screened using the Level-2A Scene Classification Layer (`SCL`). A tank observation is rejected if cloud/cirrus cover over the tank footprint exceeds $20\%$.

---

## 7. Reporting Commitments
- **Full Transparency:** Results for all three methods (M1, M2, M3) will be published in the final tables. No method will be omitted.
- **Explicit Verdicts:** Outcomes will be stated as **PASS**, **FAIL**, **NOT SUPPORTED**, or **INCONCLUSIVE** based strictly on the registered criteria.