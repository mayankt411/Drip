# Current Project Status & Phase Gate Log

## 1. Provenance and Integrity Audit (NO MOCK DATA)
- **Official EIA Stocks**: 157 weekly records retrieved directly from EIA API v2 (`W_EPC0_SAX_YCUOK_MBBL`). Authenticated and verified.
- **Sentinel-2 Catalog**: 877 Level-2A products cataloged directly from Copernicus Data Space Ecosystem (CDSE) STAC API over the Cushing AOI.
- **Exclusions**: 407 cloudy products (>40% cloud cover) logged in `data/exclusions.csv`.
- **Integrity Compliance**:
  - Any shortcut scripts containing synthetic noise or pseudo-measurements (`process_pipeline.py`) have been **purged**.
  - All synthetic machine learning scripts (`yololite_tank_detector_demo.m`) have been **purged**.
  - No synthetic data is permitted to feed any result or metric.

## 2. Research Phase Gate Status
- **Phase 0 (Literature & Environment)**: COMPLETED.
- **Phase 1 (Acquisition)**:
  - EIA weekly series fully downloaded (`data/raw/eia_cushing_weekly_2021_2023.json`).
  - S2 L2A STAC catalog fully downloaded (`data/raw/s2_cushing_stac_2021_2023.json`).
  - Full-band multispectral rasters (`.jp2` B02, B03, B04, B08, SCL) download pipeline established in `src/acquire/download_bands.py`.
- **Phase 2 (Cloud & Quality Masking)**: COMPLETED (47 weeks blocked by clouds, 110 weeks available).
- **Phase 3 (Tank Registry Validation)**: Ground truth registry established with 10 Cushing commercial tanks (`data/tanks/tank_registry.csv`).
- **Phase 4 (Shadow Measurement & Resolution Check)**:
  - Resolution check conducted at 10m Sentinel-2 GSD (`src/measure/run_phase4_resolution_check.py`).
  - Physical shadow lengths $< 5\text{ m}$ (summer midday $> 55^\circ$ elevation) span $< 0.5$ pixels, creating severe discretization limits. Winter/autumn ($< 45^\circ$) yields $> 0.9$ to $1.6$ pixels.
- **Phase 5 (Geometry & Manual Verification)**:
  - 10 real manual geometry checks logged in `data/manual_checks.csv` across real Sentinel-2 acquisitions.
- **Phase 6–7 (Locked Evaluation)**:
  - PENDING download of all target multispectral band rasters. Results directory purged until pixel-level raster extraction on full bands is complete.
