# Background and Literature Review: Satellite-Based Oil Storage Estimation

## 1. Verified Citations and References

- **Wang, T., Li, Y., Yu, S.-T., & Liu, Y. (2019).** *Estimating the Volume of Oil Tanks Based on High-Resolution Remote Sensing Images.* Remote Sensing, 11(7), 793. DOI: [10.3390/rs11070793](https://doi.org/10.3390/rs11070793).
  - *Method:* Gaofen-2 (sub-meter optical) imagery; circular Hough transform for tank radius; Otsu thresholding + morphology for exterior/interior shadow; sub-pixel median filtering.
  - *Status:* Verified on MDPI. Validated on isolated individual tanks without hub-level or official inventory benchmark.
- **Mukherjee, A., Panayotov, G., & Shon, J. (2021).** *Eye in the sky: Private satellites and government macro data.* Journal of Financial Economics, 141(1), 234-254. DOI: [10.1016/j.jfineco.2021.04.013](https://doi.org/10.1016/j.jfineco.2021.04.013).
  - *Method:* Exploits local cloud cover shocks over critical hubs (including Cushing) as an exogenous instrument for satellite coverage quality.
  - *Status:* Verified in JFE. Demonstrates that alternative satellite data reduces announcement surprises when skies are clear.
- **Arnese (2022).** *Super-resolution for storage tank monitoring.* MSc thesis, Politecnico di Milano, handle [10589/197079](https://hdl.handle.net/10589/197079).
  - *Finding:* Sentinel-2 (10 m native resolution) yields shadows spanning only 1–4 pixels across for typical commercial tanks, requiring caution or super-resolution.
  - *Status:* Verified thesis repository record.
- **IEEE JSTARS (2024).** *Automatic Monitoring of Oil Tank 3D Geometry and Storage Changes With Interferometric Coherence and SAR Intensity Information.* IEEE JSTARS, DOI: [10.1109/JSTARS.2023.3337126](https://doi.org/10.1109/JSTARS.2023.3337126).
  - *Status:* Verified spotlight SAR study using high-resolution non-free radar.

## 2. Literature Search Log & Gap Status

### A. Preliminary Search Scope
Initial scoping was conducted via web search engines, Google Scholar, and publisher repositories (MDPI, Elsevier ScienceDirect, IEEE Xplore index pages).
- **Search Strings Used:**
  1. `"oil tank" AND "floating roof" AND "Sentinel-2" AND "inventory"`
  2. `"Cushing" AND "satellite" AND "EIA" AND "crude stocks"`
  3. `"storage volume" AND ("Sentinel-1" OR "Sentinel-2") AND "validation"`

### B. Scientific Status of Gaps G1–G3: PLAUSIBLE BUT UNCONFIRMED
> **IMPORTANT INTEGRITY DISCLOSURE:**
> Gaps G1, G2, and G3 are **hypothesized and plausible based on preliminary indexing**, but **HAVE NOT BEEN SYSTEMATICALLY CONFIRMED** across formal Scopus, IEEE Xplore, and CNKI full-text databases.
> - **G1 (Tracking official weekly inventory with free Sentinel-2/1):** Plausible.
> - **G2 (Open, reproducible inventory-validated pipeline):** Plausible.
> - **G3 (Error breakdown by cloud cover and sun elevation against macro inventory):** Plausible.
> 
> The paper must transparently disclose that a systematic multi-database bibliometric query remains pending, and must not claim absolute novelty beyond the surveyed sources.

## 3. Scope and Limitations
This study enforces strict adherence to free public data (Sentinel-2 L2A via CDSE) and direct physical shadow geometry, tested and reported with full provenance.
