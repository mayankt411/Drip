# Sentinel-2 Cushing Crude Oil Storage Estimation Pipeline

A reproducible research pipeline and academic evidence base estimating crude oil storage at Cushing, Oklahoma from free Sentinel-2 optical imagery, validated against official U.S. EIA weekly ending stocks.

## Repository Layout
```
oil-tank-inventory/
  configs/         # AOI coordinates, temporal splits, and locked thresholds
  data/
    raw/           # Read-only raw imagery and EIA JSON responses
    processed/     # Masked and resampled products
    tanks/         # Real tank registry with coordinates and geometry
    manifest.csv   # Provenance ledger with URLs, queries, and SHA-256 hashes
    exclusions.csv # Explicit failure and exclusion logs
  src/
    acquire/       # CDSE and EIA v2 download scripts
    measure/       # Classical shadow geometry and volume calculations
    evaluate/      # Hypothesis testing and stratified evaluation
  docs/            # Scientific documentation and pre-registration
  tests/           # Formula and integration unit tests
```

## Quick Start
1. Configure credentials:
   ```bash
   cp .env.example .env
   # Add CDSE_USERNAME, CDSE_PASSWORD, and EIA_API_KEY
   ```
2. Install pinned dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run unit tests:
   ```bash
   pytest tests/
   ```
