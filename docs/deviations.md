# Methodological Deviations & Invalidation Log

## Incident 001: Invalidation of Phases 4 through 7 (Date: 2026-11-03)

### 1. Root Cause Analysis
- **Image Resolution Mismatch**: Extraction code (`src/preprocess/extract_real_tanks.py`) mistakenly cropped sub-windows from downsampled Sentinel-2 preview thumbnails ($343 \times 343$ pixels covering a $100\text{ km} \times 100\text{ km}$ tile, resulting in $\approx 290\text{ m/pixel}$) rather than reading the native 10-meter Level-2A surface reflectance rasters (`B02`, `B03`, `B04`, `B08`, `SCL`).
- **Physical Impossibility**: At $\approx 290\text{ m/pixel}$, an $80\text{ m}$ diameter tank spans only $\approx 0.27$ pixels. Applying a $10\text{ m}$ multiplier to radial steps across background terrain produced mathematically impossible shadow lengths ($44\text{ m}$ to $80\text{ m}$) on tanks with only $18\text{ m}$ shell height, and impossible crescent areas ($59,200\text{ m}^2$ on a tank whose total surface area is only $5,026\text{ m}^2$).
- **Weekly Estimate Discrepancy**: `weekly_estimates.csv` reported a mean shadow length of $68.2\text{ m}$ for `2021-W01` because it ingested the corrupted output from `extract_real_tanks.py`, directly contradicting the analytical physical limit ($L_{\text{max}} = 29.99\text{ m}$ at $\alpha = 28.82^\circ$).

### 2. Corrective Actions Taken
1. **Phases 4 through 7 Formally Declared VOID**:
   - All output CSVs (`results/metrics.csv`, `results/weekly_estimates.csv`, `results/stratified_metrics.csv`, `results/lagged_correlation.csv`) have been deleted.
   - Claims of `H1 PASS` and `H3 PASS` are retracted and classified as null and void.
2. **Locked Test Period Status**:
   - Because the 2022-10-19 to 2023-12-31 test period was unblinded and evaluated during the flawed runs, it is permanently contaminated.
   - Any re-evaluation on the 2021–2023 dataset must be classified as **POST-HOC EXPLORATORY**.
   - Any future confirmatory test requires an unopened temporal window (e.g., 2024).

---

## Incident 002: Stop-Gate Residual Failure on 2023 Verification Scenes (Date: 2026-11-03)

### 1. Event Description
Following the recovery of native 10-meter Level-2A bands (`B04`, `B08`), an automated Stop Gate was executed on the 10 reference inspection scenes from December 2023 (`data/manual_checks.csv`).
- **Pre-registered Gate Threshold:** Every tank residual must satisfy $|\hat{L}_i - L_{\text{ref}, i}| \le 3.0\text{ m}$.
- **Result:**
  - Automated radial thresholding collapsed to the analytical upper boundary ($L_{\text{max}} \approx 28\text{ m}$) across all 10 tanks (Mean Absolute Residual: $13.49\text{ m}$, 0/10 passing).
  - Sub-pixel radial gradient edge detection yielded residuals ranging from $-11.11\text{ m}$ to $+16.06\text{ m}$ (Mean Absolute Residual: $8.69\text{ m}$, only 1/10 passing).
- **Decision:** **STOP GATE FAILED.** Pipeline execution on the 2023 period was halted immediately to preserve protocol integrity.

### 2. Corrective Protocol Transition
In accordance with open-science rules:
1. The 2021–2023 dataset is permanently closed to confirmatory claims.
2. A new, strictly confirmatory study protocol is pre-registered in `docs/prereg_v2.md` on an untouched post-2023 temporal window (2024-01-01 to 2024-06-30).
3. Candidate methods (M1, M2, M3) and the Q2 Contrast-to-Noise Ratio (CNR) diagnostic are locked before any 2024 data is downloaded or inspected.
