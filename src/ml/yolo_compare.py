"""Compare detector sizes. The winner is chosen on the validation split only,
then every model is also scored on the held-out terminals for the record."""
import json
import shutil

import pandas as pd

from .common import ROOT, cfg, log_manifest, seed_all, sha256
from .yolo import DS

RUNS = ROOT / "models" / "yolo_runs"


def train_one(c, name, weights, batch):
    from ultralytics import YOLO
    y = c["yolo"]
    best = RUNS / name / "weights" / "best.pt"
    if best.exists():
        return best
    flag = RUNS / f"{name}.started"
    amp = not flag.exists()  # an earlier attempt died without finishing: train in full precision
    RUNS.mkdir(parents=True, exist_ok=True)
    flag.write_text("started", encoding="utf-8")
    while True:
        try:
            seed_all(c["seed"])
            YOLO(weights).train(data=str(DS / "data.yaml"), epochs=y["epochs"], imgsz=y["imgsz"], batch=batch,
                                seed=c["seed"], project=str(RUNS), name=name, exist_ok=True, amp=amp,
                                pretrained=weights.endswith(".pt"))
            flag.unlink(missing_ok=True)
            return best
        except RuntimeError as e:
            if "out of memory" not in str(e).lower() or batch <= 2:
                raise
            batch //= 2
            print(f"out of memory, retrying {name} with batch {batch}", flush=True)


def score(c, ckpt, split):
    from ultralytics import YOLO
    model = YOLO(str(ckpt))
    kw = dict(data=str(DS / "data.yaml"), split=split, imgsz=c["yolo"]["imgsz"], iou=0.6, plots=False, verbose=False)
    wide = model.val(conf=0.001, **kw).box
    at = model.val(conf=c["yolo"]["conf"], **kw).box
    return {"map50": float(wide.map50), "map50_95": float(wide.map), "precision": float(at.mp), "recall": float(at.mr)}


def main():
    c = cfg()
    y = c["yolo"]
    keep = ROOT / "models" / "yolo_tank_best_baseline.pt"
    if not keep.exists():
        shutil.copy(ROOT / y["checkpoint"], keep)
    cands = [("baseline_" + y["weights"].replace(".pt", ""), keep)]
    for item in y["compare"]:
        cands.append((item["name"], train_one(c, item["name"], item["weights"], y["batch"])))
    from ultralytics import YOLO
    rows = []
    for name, ckpt in cands:
        n_par = sum(p.numel() for p in YOLO(str(ckpt)).model.parameters()) / 1e6
        v, t = score(c, ckpt, "val"), score(c, ckpt, "test")
        rows.append({"model": name, "params_m": n_par,
                     **{f"val_{k}": x for k, x in v.items()}, **{f"test_{k}": x for k, x in t.items()}})
        print(name, rows[-1], flush=True)
    df = pd.DataFrame(rows)
    pick = int(df.val_map50.to_numpy().argmax())
    df["selected"] = [i == pick for i in range(len(df))]
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    df.to_csv(out / "ml_yolo_compare.csv", index=False)
    dest = ROOT / y["checkpoint"]
    shutil.copy(cands[pick][1], dest)
    (out / "ml_yolo_selected.json").write_text(json.dumps(
        {"selected": cands[pick][0], "rule": "highest validation mAP@50 (2022 dates, training terminals)",
         "n_models": len(cands)}, indent=2), encoding="utf-8")
    log_manifest("local:ultralytics_compare", f"selected={cands[pick][0]};n={len(cands)}", dest.name, "NA",
                 sha256(dest), "SUCCESS")
    print("selected", cands[pick][0])


if __name__ == "__main__":
    main()
