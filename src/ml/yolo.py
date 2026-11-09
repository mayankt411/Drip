"""Stage 1: YOLO tank detector on Sentinel-2 chips, labelled from the OSM registry."""
import argparse
import shutil

import numpy as np
import pandas as pd
from PIL import Image

from .common import ROOT, cfg, in_range, log_manifest, seed_all, sha256
from .cube import make_grid

CUBES = ROOT / "data" / "processed" / "cubes"
DS = ROOT / "data" / "ml" / "yolo"
REGISTRY = ROOT / "data" / "tanks" / "cushing_full_registry.csv"


def rgb_u8(refl):
    """B04/B03/B02 as 8-bit with a fixed 0..0.3 reflectance stretch (same for every date)."""
    img = refl[[2, 1, 0]].astype(np.float32) / 10000.0
    return (np.clip(img / 0.3, 0, 1) * 255).astype(np.uint8).transpose(1, 2, 0)


def cluster_windows(rows, cols, rad, c):
    """Windows over one cluster's extent (plus margin), cut into <=tile_px pieces.
    Windows never grow past the cluster extent, so other terminals stay out of them."""
    y = c["yolo"]
    m = y["window_margin_px"]
    r0, r1 = int(rows.min() - rad.max()) - m, int(rows.max() + rad.max()) + m
    c0, c1 = int(cols.min() - rad.max()) - m, int(cols.max() + rad.max()) + m
    step = y["tile_px"] - y["tile_overlap_px"]
    out = []
    for r in range(r0, max(r1 - y["tile_overlap_px"], r0 + 1), step):
        for k in range(c0, max(c1 - y["tile_overlap_px"], c0 + 1), step):
            out.append((r, k, min(r + y["tile_px"], r1), min(k + y["tile_px"], c1)))
    return [w for w in out if w[2] - w[0] >= 24 and w[3] - w[1] >= 24]


def labels_for(win, rows, cols, rad, up):
    r0, c0, r1, c1 = win
    lines = []
    for r, k, a in zip(rows, cols, rad):
        if not (r0 <= r < r1 and c0 <= k < c1):
            continue
        x0, x1 = max(k - a, c0), min(k + a, c1)
        y0, y1 = max(r - a, r0), min(r + a, r1)
        w, h = (c1 - c0), (r1 - r0)
        lines.append(f"0 {((x0 + x1) / 2 - c0) / w:.6f} {((y0 + y1) / 2 - r0) / h:.6f} {(x1 - x0) / w:.6f} {(y1 - y0) / h:.6f}")
    return lines


def window_cloud(scl, win, classes):
    r0, c0, r1, c1 = win
    sub = scl[max(r0, 0):r1, max(c0, 0):c1]
    return float(np.isin(sub, classes).mean()) if sub.size else 1.0


def build_dataset(c):
    seed_all(c["seed"])
    grid = make_grid(c)
    reg = pd.read_csv(REGISTRY)
    s, up = c["splits"], c["yolo"]["upscale"]
    rows_all = (grid["y1"] - reg.y_utm.to_numpy()) / grid["res"]
    cols_all = (reg.x_utm.to_numpy() - grid["x0"]) / grid["res"]
    rad_all = reg.diameter_m.to_numpy() / 2 / grid["res"]
    plan = {"train": ("train", s["train_start"], s["yolo_val_start"]),
            "val": ("train", s["yolo_val_start"], s["train_end"]),
            "test": ("heldout", s["test_start"], s["test_end"])}
    rng = np.random.default_rng(c["seed"])
    counts = {}
    for part, (which, d0, d1) in plan.items():
        for sub in ("images", "labels"):
            shutil.rmtree(DS / part / sub, ignore_errors=True)
            (DS / part / sub).mkdir(parents=True)
        sel = reg[reg.split == which]
        wins = []
        for cid in sel.cluster.unique():
            idx = np.where(reg.cluster == cid)[0]
            wins += cluster_windows(rows_all[idx], cols_all[idx], rad_all[idx], c)
        n_img = 0
        for path in sorted(CUBES.glob("*.npz")):
            day = f"{path.stem[:4]}-{path.stem[4:6]}-{path.stem[6:]}"
            if not in_range(day, d0, d1) or (part == "train" and day >= d1):
                continue
            z = np.load(path)
            img = rgb_u8(z["refl"])
            rng = np.random.default_rng(c["seed"] + int(path.stem))
            for wi, win in enumerate(wins):
                if window_cloud(z["scl"], win, c["cloud_scl_classes"]) > 0.20:
                    continue
                lab = labels_for(win, rows_all, cols_all, rad_all, up)
                if not lab and rng.random() > c["yolo"]["background_tile_share"]:
                    continue
                crop = Image.fromarray(img[win[0]:win[2], win[1]:win[3]])
                crop = crop.resize((crop.width * up, crop.height * up), Image.BICUBIC)
                name = f"{path.stem}_{part}_{wi:03d}"
                crop.save(DS / part / "images" / f"{name}.png")
                (DS / part / "labels" / f"{name}.txt").write_text("\n".join(lab) + "\n")
                n_img += 1
        counts[part] = n_img
    (DS / "data.yaml").write_text(
        f"path: {DS}\ntrain: train/images\nval: val/images\ntest: test/images\nnames:\n  0: tank\n")
    return counts


def train(c):
    from ultralytics import YOLO
    y = c["yolo"]
    seed_all(c["seed"])
    model = YOLO(y["weights"])
    model.train(data=str(DS / "data.yaml"), epochs=y["epochs"], imgsz=y["imgsz"], batch=y["batch"],
                seed=c["seed"], project=str(ROOT / "models" / "yolo_runs"), name="tank", exist_ok=True,
                pretrained=y["weights"].endswith(".pt"))
    best = ROOT / "models" / "yolo_runs" / "tank" / "weights" / "best.pt"
    dest = ROOT / y["checkpoint"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(best, dest)
    log_manifest("local:ultralytics_train", f"weights={y['weights']};epochs={y['epochs']};seed={c['seed']}",
                 dest.name, "NA", sha256(dest), "SUCCESS")


def evaluate(c):
    """Precision, recall, mAP@50 and the PR curve on the held-out terminals (test split)."""
    from ultralytics import YOLO
    model = YOLO(str(ROOT / c["yolo"]["checkpoint"]))
    m = model.val(data=str(DS / "data.yaml"), split="test", imgsz=c["yolo"]["imgsz"],
                  conf=0.001, iou=0.6, plots=False, verbose=False)
    b = m.box
    at = model.val(data=str(DS / "data.yaml"), split="test", imgsz=c["yolo"]["imgsz"],
                   conf=c["yolo"]["conf"], iou=0.6, plots=False, verbose=False).box
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    n_img = len(list((DS / "test" / "images").glob("*.png")))
    n_lab = sum(len(p.read_text().split("\n")) - 1 for p in (DS / "test" / "labels").glob("*.txt"))
    pd.DataFrame([{"split": "test_heldout_terminals", "precision": float(at.mp), "recall": float(at.mr), "precision_maxf1": float(b.mp), "recall_maxf1": float(b.mr),
                   "map50": float(b.map50), "map50_95": float(b.map), "n_images": n_img,
                   "n_labels": n_lab}]).to_csv(out / "ml_yolo_metrics.csv", index=False)
    rec, prec = np.asarray(b.px), np.asarray(b.prec_values)[0]
    pd.DataFrame({"recall": rec, "precision": prec}).to_csv(out / "ml_yolo_pr_curve.csv", index=False)
    pd.DataFrame(m.confusion_matrix.matrix).to_csv(out / "ml_yolo_confusion.csv", index=False)
    return b


def detect_dates(c, tile_px=160, overlap=16):
    """Run the detector over the full AOI for every cube and store detections (grid pixels)."""
    from torchvision.ops import nms
    import torch
    from ultralytics import YOLO
    model = YOLO(str(ROOT / c["yolo"]["checkpoint"]))
    grid, up = make_grid(c), c["yolo"]["upscale"]
    out = ROOT / "data" / "ml" / "detections"
    out.mkdir(parents=True, exist_ok=True)
    step = tile_px - overlap
    for path in sorted(CUBES.glob("*.npz")):
        img = rgb_u8(np.load(path)["refl"])
        h, w = img.shape[:2]
        boxes, scores = [], []
        for r in range(0, h, step):
            for k in range(0, w, step):
                crop = Image.fromarray(img[r:r + tile_px, k:k + tile_px])
                crop = crop.resize((crop.width * up, crop.height * up), Image.BICUBIC)
                res = model.predict(np.array(crop), imgsz=c["yolo"]["imgsz"], conf=c["yolo"]["conf"], verbose=False)[0]
                for (x0, y0, x1, y1), s in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.conf.cpu().numpy()):
                    boxes.append([k + x0 / up, r + y0 / up, k + x1 / up, r + y1 / up])
                    scores.append(float(s))
        keep = nms(torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4),
                   torch.tensor(scores, dtype=torch.float32), 0.5).numpy() if boxes else []
        det = pd.DataFrame([{"col": (boxes[i][0] + boxes[i][2]) / 2, "row": (boxes[i][1] + boxes[i][3]) / 2,
                             "w_px": boxes[i][2] - boxes[i][0], "conf": scores[i]} for i in keep])
        det["x_utm"] = grid["x0"] + det.col * grid["res"] if len(det) else []
        det["y_utm"] = grid["y1"] - det.row * grid["res"] if len(det) else []
        det.to_csv(out / f"{path.stem}.csv", index=False)


def match_detections(registry, det, radius_m):
    """For each registry tank: was a detection centre within radius_m?"""
    if len(det) == 0:
        return np.zeros(len(registry), bool)
    dx = registry.x_utm.to_numpy()[:, None] - det.x_utm.to_numpy()[None, :]
    dy = registry.y_utm.to_numpy()[:, None] - det.y_utm.to_numpy()[None, :]
    return (np.hypot(dx, dy) <= radius_m).any(axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["dataset", "train", "eval", "detect"])
    a = ap.parse_args()
    c = cfg()
    if a.step == "dataset":
        print(build_dataset(c))
    elif a.step == "train":
        train(c)
    elif a.step == "eval":
        evaluate(c)
    else:
        detect_dates(c)


if __name__ == "__main__":
    main()
