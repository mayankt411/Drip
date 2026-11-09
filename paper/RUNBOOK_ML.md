# Runbook: ML study (run on a machine with internet and a GPU)

Credentials: put `CDSE_USERNAME`, `CDSE_PASSWORD`, `EIA_API_KEY` in a local `.env` (gitignored) or export them. Nothing in the repo stores them.

```
pip install -r requirements.txt
python -m pytest tests/ml -q                 # must pass first

python -m src.ml.registry                    # OSM tanks -> data/tanks/cushing_full_registry.csv
python -m src.ml.scenes                      # STAC index -> data/ml/scenes.csv
python -m src.ml.download                    # downloads, hashes into data/manifest.csv, builds cubes (hours; resumable)

python -m src.ml.yolo dataset                # auto-labelled windows from OSM
python -m src.ml.yolo train                  # GPU
python -m src.ml.yolo eval                   # H1 metrics on held-out terminals
python -m src.ml.yolo detect                 # detections per date for the YOLO tank source

python -m src.ml.chipbank                    # chips for every tank and date
python -m src.ml.train_cnn                   # 5 seeds, trains on 2021-2022 only
python -m src.ml.evaluate                    # weekly inventory, EIA metrics, verdicts
python -m src.ml.report                      # tables, SVG figures, paper/paper.md
python -m src.ml.provenance                  # SHA-256 of models and results into the manifest
```

Send back `results/ml_*.csv`, `results/ml_*.json`, `models/yolo_tank_best.pt` and `data/manifest.csv`. Do not edit numbers by hand: `paper/paper.md` is regenerated from `results/`.

Notes
- H2 (per-tank MAE) is reported as NOT_TESTABLE: there are no per-tank labels.
- The test period 2023-2024 was inspected in the earlier study, so every verdict is exploratory.
- If `download` stalls, rerun it; finished dates are skipped.
