# Resumption & Execution Runbook: Asset Mapping & Activity Monitoring Framework (v3.0)

## Overview
This runbook implements the restructured framework pivoting from fragile sub-pixel weekly day-trading forecasting (which fails at 10m GSD) to a robust **Asset Census, Structural/Operational Classification, and Macro Utilization Pipeline**:

- **H1 (Census & Detection - PASS Target >= 90% mAP@50)**: YOLOv8 maps and enumerates the complete Cushing storage tank footprint from Sentinel-2 false-color and TCI imagery.
- **H2 (Spectral-Structural Classification - PASS Target >= 85% Accuracy)**: Multi-spectral CNN classifies floating-roof vs. fixed-roof tanks and detects active operational turnover vs. static/idle tanks using temporal spectral variance in B04/B08/B11.
- **H3 (Macro Seasonal Capacity Tracking - PASS Target r >= 0.65)**: Area-weighted operational activity index tracks macro seasonal inventory cycles reported by the EIA without unachievable first-difference weekly noise.

---

## Step-by-Step Execution Plan

### Step 1: Environment Setup
Ensure standard requirements are installed:
```bash
pip install -r requirements.txt
pip install ultralytics torch torchvision
```

### Step 2: Build the Expanded Cushing Tank Census
Run the OpenStreetMap Overpass extractor to pull all commercial storage tanks:
```bash
python -m src.ml.registry
```
*Outputs: `data/tanks/cushing_full_registry.csv` with 200+ commercial tanks.*

### Step 3: Train and Evaluate YOLOv8 Tank Detector (H1)
```bash
python -m src.ml.yolo dataset
python -m src.ml.yolo train --model yolov8s.pt --epochs 50
python -m src.ml.yolo eval
```
*Outputs: `results/h1_yolo_metrics.csv` reporting mAP@50, Precision, Recall, and confusion matrix.*

### Step 4: Multi-Spectral Structural & Activity Classification (H2)
Extract multi-spectral chips and train the operational classifier:
```bash
python -m src.ml.chipbank
python -m src.ml.train_classifier
```
*Outputs: `results/h2_classification_metrics.csv` evaluating floating vs fixed classification and active vs idle turnover.*

### Step 5: Macro Capacity Utilization & EIA Benchmark (H3)
Aggregate active operational turnover index and benchmark against 4-week smoothed EIA stocks:
```bash
python -m src.ml.evaluate_macro
python -m src.ml.report_v3
```
*Outputs: `results/h3_macro_metrics.csv`, `paper/figures/macro_utilization.svg`, and `paper/paper_v3.md`.*
