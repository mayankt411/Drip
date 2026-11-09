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

---

## Reporting Notes Recorded at Write-Up (Date: 2026-11-04)

These were found while preparing `paper/paper.md` and do not change any registered verdict.

### Deviation 003: Holm-Bonferroni operationalization
`docs/prereg_v2.md` Section 5 requires Holm-Bonferroni correction across the three methods but does not name a test statistic. For the write-up, a one-sided exact binomial test of H0: pass probability <= 0.80 was used per method, then Holm-adjusted (`src/report/make_confirmatory_report.py`). This choice was made after results were known. All three adjusted p values are > .999. Verdicts rest on the registered pass-rate and median-residual thresholds only.

### Note 004: Cloud screening basis
The 2024 exclusion log records scene-level `eo:cloud_cover` from the STAC catalogue (threshold 20%), not the tank-footprint Scene Classification Layer rule in `docs/prereg_v2.md` Section 6. Logged exclusions: 44 of 72 T14SQE and T14SPE products (61.1%). Across all four tiles in the catalogue the figure is 87 of 144 (60.4%). No footprint-level SCL screening record is in the repository.

### Note 005: Single acquisition date
All 10 tanks in `data/manual_readings_v2.csv` come from one acquisition (S2B_MSIL2A_20240129T171549, 2024-01-29). 14 dates in the window had T14SQE scene cloud cover at or below 20%, but only one was evaluated.

### Note 006: Method 2 definition differs between registered files
`docs/prereg_v2.md` defines M2 with bands B02, B03, B04, B08 and B11 and an explicit index formula. `configs/prereg_v2.yaml` lists B02, B03, B04, B08, B8A, B11 and B12 and names the index `shadow_index_s2`. Only B02, B03, B04, B08, B11 and TCI were downloaded for 2024-01-29. The paper describes M2 as in `docs/prereg_v2.md`; which definition the run used cannot be confirmed from this repository (see Note 007).

### Note 007: Evaluation code and rasters are not in the repository
No script in the repository at commit `8087717` writes the three 2024 result CSVs, and the rasters are gitignored. The results are committed but cannot be regenerated from this checkout. The M1-M3 and CNR code used for the run should be committed before the paper claims computational reproducibility.

### Note 008: Line endings in manifest checksums
The manifest checksums for `data/raw/eia_cushing_weekly_2024.json` and `data/raw/s2_cushing_stac_2024.json` were computed on CRLF copies. The committed files use LF, so those two checksums only match after CRLF conversion. LF checksums were appended as separate rows; `src/acquire/verify_manifest.py` accepts either.

### Note 009: No retrieval timestamps for 2024 files
The 2024 manifest rows (STAC catalogue, EIA series, rasters) do not record retrieval times. That they were obtained after the protocol lock (`ede4a3f`, 2026-11-03) rests on the commit history: they first appear in `8087717` (2026-11-04).

## Note 010: Exploratory ML follow-up (branch ml-pivot)
After the pre-registered study returned a negative result, a separate ML analysis was added (src/ml, paper/paper.md). It is post hoc: the 2023-2024 windows had been inspected earlier, so all verdicts are exploratory. Supervision is hub-level EIA stocks only; per-tank accuracy (H2) is not testable. The tank registry comes from OpenStreetMap with a footprint-area proxy for capacity. The confirmatory paper is preserved as paper/paper_confirmatory.md. No ML results existed at the time of this note: the code was unit-tested on synthetic arrays only.
