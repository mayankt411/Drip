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
   - Any future confirmatory test requires an unopened temporal window (e.g., 2024–2026).
3. **Mandatory Protocol for Pipeline Rebuilding**:
   - Native 10m Ground Sample Distance rasters (`.jp2` or Cloud-Optimized GeoTIFFs for bands B02, B03, B04, B08) must be downloaded and cropped using exact UTM Zone 14N geo-coordinates.
   - Extraction must be run and verified on the 10 manual-check reference scenes first. If computer vision residuals against human inspection fail, execution must halt immediately.
