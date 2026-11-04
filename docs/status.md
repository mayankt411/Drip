# Status Log & Pre-Registration Audit (Protocol v2.0)

## 1. Protocol Registration & Commit Lock
- **Pre-Registration v2 Document:** `docs/prereg_v2.md`
- **Configuration Spec:** `configs/prereg_v2.yaml`
- **Git Commit Hash (LOCKED):** `ede4a3fd56960d1538d5b01aec2241ecc5261510`
- **Lock Timestamp:** 2026-11-03T19:40:00+04:00
- **Study Status:** STRICTLY CONFIRMATORY on pristine, unopened 2024 window (`2024-01-01` to `2024-06-30`).

---

## 2. Research Questions Status (locked 2024 window, recorded 2026-11-04)

| Question | Description | Gate / Threshold | Status | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **Q1 (Measurement Validity)** | Do automated methods (M1, M2, M3) reproduce human reference shadow within $\pm 3.0\text{ m}$? | $\ge 80\%$ pass rate & Median Abs Residual $\le 2.0\text{ m}$ | COMPLETE | **FAIL.** M1 3/10 (30.0%, median 6.71 m); M2 1/10 (10.0%, median 8.09 m); M3 2/10 (20.0%, median 6.91 m). No method met either criterion. |
| **Q2 (Contrast Diagnostic)** | Is there measurable shadow contrast ($10\text{ m}$ GSD) relative to sensor noise? | Contrast-to-Noise Ratio $\text{CNR} \ge 2.0$ | COMPLETE | **FAIL (noise-dominated).** Mean CNR 0.34 (range 0.07 to 0.93); 10/10 tanks below threshold. |
| **Q3 (EIA Forecasting)** | Do satellite volume changes predict EIA Cushing stock changes at lag 0 and 1? | Block-bootstrap CI excluding 0 | CONDITIONAL | **NOT TESTED.** Gate respected: all methods failed Q1, so Q3 is non-applicable under `docs/prereg_v2.md` Section 5. |

Results files: `results/q1_summary.csv`, `results/q1_residuals_all_methods.csv`, `results/q2_contrast_diagnostics.csv` (commit `8087717`).
Write-up: `paper/paper.md`, built by `src/report/make_confirmatory_report.py` from those files. Tables are in `paper/tables/`, Figure 1 is `paper/figures/figure1.svg`.
Provenance: `data/manifest.csv` holds SHA-256 checksums for the 2024 STAC catalogue, EIA series, the twelve 2024-01-29 rasters, the human readings and the three result files. Check with `python src/acquire/verify_manifest.py`. See `docs/deviations.md` (reporting notes) for known gaps.

---

## 3. Historical Invalidation Log Summary
- **Incident 001:** Thumbnail downsampling error in original exploratory runs (2021–2023) voided. All earlier metrics permanently retracted.
- **Incident 002:** Stop Gate residual verification on native 10m December 2023 rasters failed (10% pass rate). 2021–2023 temporal window permanently designated as historical exploratory context. Confirmatory study established on untouched 2024 data.
