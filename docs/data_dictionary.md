# Data Dictionary

## 1. Tank Registry (`data/tanks/tank_registry.csv`)
- `tank_id`: Unique identifier (e.g., TANK_001).
- `latitude`, `longitude`: WGS84 decimal degrees of tank center.
- `radius_meters`: Measured inner wall radius in meters.
- `height_meters`: Measured or documented tank wall height in meters.
- `tank_type`: Type of roof structure (`FLOATING_ROOF` or `FIXED_ROOF`). Only floating roof tanks are included in primary shadow inventory volume.
- `method_note`: Method used for identification/measurement.
- `confidence_grade`: `HIGH` or `MEDIUM`.
- `operator`: Known operating terminal midstream company.

## 2. Manifest (`data/manifest.csv`)
- `source_url_or_endpoint`: Source URL or API endpoint.
- `retrieval_time_utc`: ISO 8601 UTC timestamp of retrieval.
- `query_params`: Exact query parameters used.
- `product_id_or_series`: Sentinel-2 product name or EIA series ID.
- `cloud_cover`: Percent scene cloud cover.
- `sha256_checksum`: SHA-256 hash of the downloaded raw file.
- `status`: Acquisition status (`SUCCESS`, `FAILED`).

## 4. Real Satellite Pixel Measurements (`data/processed/real_satellite_pixel_measurements.csv`)
- `date`: YYYY-MM-DD of satellite overpass.
- `image_file`: Filename of the real downloaded Sentinel-2 acquisition in `data/raw/imagery/`.
- `sun_elevation_deg`: Solar elevation angle above the horizon at acquisition time (degrees).
- `sun_azimuth_deg`: Solar azimuth angle clockwise from North (degrees).
- `cloud_cover_pct`: Scene cloud cover percentage from STAC metadata.
- `avg_shadow_length_m`: Mean linear shadow length measured along the ephemeris solar ray (meters).
- `avg_shadow_crescent_area_px`: Total 2D count of pixels classified as shadow across the circular tank footprint (pixel area, where 1 pixel = 100 m² at 10m GSD).
- `hub_sample_volume_mbbl`: Aggregate volume across the 10 surveyed registry tanks (thousand barrels).

## 5. Weekly Estimates Provenance Ledger (`results/weekly_estimates.csv`)
- `iso_week`: Calendar week (YYYY-Www).
- `period`: EIA weekly reporting period end date (Friday).
- `split_group`: `DEVELOPMENT` (earliest 60%) or `TEST` (latest 40%).
- `granule_id`: Specific Sentinel-2 L2A product identifier used for measurement.
- `granule_sha256`: Cryptographic SHA-256 hash tracing back to `data/manifest.csv`.
- `eia_stocks_mbbl`: Official EIA ending stocks excluding SPR for Cushing (thousand barrels).
- `raw_sample_stocks_mbbl`: Uncalibrated raw satellite physical volume summed over the 10 registry tanks (thousand barrels).
- `calibrated_stocks_mbbl`: Raw sample volume scaled by the development-period calibration factor $K_{\text{dev}}$ to match nominal hub working capacity.
- `mean_cloud_cover`: Percent cloud cover of the selected weekly granule.
- `mean_sun_elevation`: Solar elevation angle at sensing time.
- `status`: `VALID_OBSERVATION` or `CLOUD_BLOCKED_OR_NO_PASS`.
