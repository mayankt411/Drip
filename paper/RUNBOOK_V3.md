# Resumption & Execution Runbook: Asset Mapping & Activity Monitoring Framework (v3.0)

## Overview
This runbook implements the restructured framework pivoting from fragile sub-pixel weekly day-trading forecasting (which fails at 10m GSD) to a robust **Asset Census, Structural/Operational Classification, and Macro Utilization Pipeline**:

- **H1 (Census & Detection - PASS Target >= 90% mAP@50)**: YOLOv8 maps and enumerates the complete Cushing storage tank footprint from Sentinel-2 false-color and TCI imagery.
- **H2 (Spectral-Structural Classification - PASS Target >= 85% Accuracy)**: Multi-spectral CNN classifies floating-roof vs. fixed-roof tanks and detects active operational turnover vs. static/idle tanks using temporal spectral variance in B04/B08/B11.
- **H3 (Macro Seasonal Capacity Tracking - PASS Target r >= 0.65)**: Area-weighted operational activity index tracks macro seasonal inventory cycles reported by the EIA without unachievable first-difference weekly noise.

---

## Status of the steps (updated)

H1 reuses the detector from the ML pivot (no separate retraining): `results/ml_yolo_metrics.csv`, `ml_yolo_compare.csv`. Run those steps first (`run_ml_local.ps1`), then:

```
python -m src.ml.train_classifier   # H2: structural labels from OSM roof tags only; operational task reported NOT_TESTABLE
python -m src.ml.evaluate_macro     # H3: activity index vs EIA (raw and 4-week), bootstrap CI, day-of-year control
python -m src.ml.report_v3          # tables, macro_utilization.svg, paper/paper_v3.md, results/h1_yolo_metrics.csv
```

Outputs: `results/h2_classification_metrics.csv`, `h2_label_counts.json`, `h2_tank_activity_index.csv`,
`results/h3_macro_metrics.csv`, `h3_macro_weekly.csv`, `h3_verdict.json`, `paper/figures/macro_utilization.svg`, `paper/paper_v3.md`.

## Rules this run follows

- Targets are hypotheses. The paper reports what the numbers show; nothing is tuned toward them.
- H2 structural needs enough OSM-labelled tanks per class (config: min_train_per_class 20, min_test_per_class 5), else it is reported as not testable. Active versus idle has no independent labels and is not tested.
- H3 passes only if r, naive p, a bootstrap interval above zero and a better correlation than the day-of-year control all hold.
- The paper is written to `paper/paper_v3.md` so the ML-pivot paper in `paper/paper.md` is not overwritten.
