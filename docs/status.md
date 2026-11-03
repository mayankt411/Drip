# Status Log & Pre-Registration Audit (Protocol v2.0)

## 1. Protocol Registration & Commit Lock
- **Pre-Registration v2 Document:** `docs/prereg_v2.md`
- **Configuration Spec:** `configs/prereg_v2.yaml`
- **Git Commit Hash (LOCKED):** `ede4a3fd56960d1538d5b01aec2241ecc5261510`
- **Lock Timestamp:** 2026-11-03T19:40:00+04:00
- **Study Status:** STRICTLY CONFIRMATORY on pristine, unopened 2024 window (`2024-01-01` to `2024-06-30`).

---

## 2. Research Questions Status

| Question | Description | Gate / Threshold | Status | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **Q1 (Measurement Validity)** | Do automated methods (M1, M2, M3) reproduce human reference shadow within $\pm 3.0\text{ m}$? | $\ge 80\%$ pass rate & Median Abs Residual $\le 2.0\text{ m}$ | IN PROGRESS | PENDING |
| **Q2 (Contrast Diagnostic)** | Is there measurable shadow contrast ($10\text{ m}$ GSD) relative to sensor noise? | Contrast-to-Noise Ratio $\text{CNR} \ge 2.0$ | IN PROGRESS | PENDING |
| **Q3 (EIA Forecasting)** | Do satellite volume changes predict EIA Cushing stock changes at lag 0 and 1? | Block-bootstrap CI excluding 0 | CONDITIONAL | LOCKED (Evaluated ONLY if Q1 PASS) |

---

## 3. Historical Invalidation Log Summary
- **Incident 001:** Thumbnail downsampling error in original exploratory runs (2021–2023) voided. All earlier metrics permanently retracted.
- **Incident 002:** Stop Gate residual verification on native 10m December 2023 rasters failed (10% pass rate). 2021–2023 temporal window permanently designated as historical exploratory context. Confirmatory study established on untouched 2024 data.
