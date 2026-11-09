"""Stage 3: hub series, baselines, EIA metrics and the hypothesis verdicts."""
import json

import numpy as np
import pandas as pd
import torch

from .common import ROOT, cfg
from .eia import load_eia
from .hub import (BANK, REGISTRY, cnn_predict, date_table, fit_ridge, load_models,
                  ridge_features, valid_mask)
from .stats import boot_corr, first_diff_pairs, level_metrics, pearson
from .train_cnn import split_fit_val
from .yolo import match_detections

RES = ROOT / "results"


def detected_mask(bank, reg, c):
    det_dir = ROOT / "data" / "ml" / "detections"
    out = np.zeros(bank["chips"].shape[:2], bool)
    for k, d in enumerate(bank["dates"]):
        f = det_dir / f"{d}.csv"
        if not f.exists():
            print(f"warning: no detections for {d}; the YOLO tank source is skipped")
            return None
        det = pd.read_csv(f)
        out[k] = match_detections(reg, det, c["yolo"]["iou_match_m"])
    return out


def sun_features(bank, k):
    """Same four sun-geometry terms the CNN sees."""
    e, a = np.radians(bank["sun"][k])
    return np.array([np.sin(a), np.cos(a), np.sin(e), np.cos(e)])


def season_features(dt, k):
    """Day-of-year harmonics: the plain seasonal control."""
    t = 2 * np.pi * dt.date[k].dayofyear / 365.25
    return np.array([np.sin(t), np.cos(t)])


def weekly_rows(c):
    bank = dict(np.load(BANK, allow_pickle=True))
    reg = pd.read_csv(REGISTRY)
    ok = valid_mask(bank, c)
    det = detected_mask(bank, reg, c)
    n = c["cnn"]
    base = date_table(bank, reg, c, ok, n["min_valid_fraction"])
    fit, val = split_fit_val(base, c["splits"]["val_share_weeks"])
    models = load_models(c, "cuda" if torch.cuda.is_available() else "cpu")
    sources = {"registry": (ok, n["min_valid_fraction"])}
    if det is not None:
        sources["yolo"] = (ok & det, n["min_valid_fraction_yolo"])
    frames = []
    for src, (mask, frac) in sources.items():
        dt = date_table(bank, reg, c, mask, frac)
        cnn = cnn_predict(models, bank, reg, mask, dt)
        X = {k: ridge_features(bank, mask, reg, k) for k in dt.index[dt.usable]}
        fit_k, val_k = [k for k in fit if k in X], [k for k in val if k in X]
        rid, _ = fit_ridge(np.array([X[k] for k in fit_k]), dt.loc[fit_k, "eia_mbbl"].to_numpy(),
                           n["ridge_alphas"], np.array([X[k] for k in val_k]), dt.loc[val_k, "eia_mbbl"].to_numpy())
        mean_const = dt.loc[fit_k, "eia_mbbl"].mean()
        preds = {"cnn": cnn[:, 0], "ridge": np.array([rid(X[k][None])[0] if k in X else np.nan for k in dt.index]),
                 "train_mean": np.where(dt.usable, mean_const, np.nan)}
        for name, feat in (("sun_only", lambda k: sun_features(bank, k)), ("seasonal", lambda k: season_features(dt, k))):
            F = {k: feat(k) for k in X}
            fn, _ = fit_ridge(np.array([F[k] for k in fit_k]), dt.loc[fit_k, "eia_mbbl"].to_numpy(),
                              n["ridge_alphas"], np.array([F[k] for k in val_k]), dt.loc[val_k, "eia_mbbl"].to_numpy())
            preds[name] = np.array([fn(F[k][None])[0] if k in F else np.nan for k in dt.index])
        for method, p in preds.items():
            f = dt.copy()
            f["method"], f["tank_source"], f["pred_mbbl"] = method, src, p
            f["mean_fill"] = cnn[:, 1] if method == "cnn" else np.nan
            f["n_valid_tanks"] = mask.sum(1)
            frames.append(f)
    df = pd.concat(frames, ignore_index=True)
    role = {base.date[k]: "fit" for k in fit} | {base.date[k]: "val" for k in val}
    df["fit_role"] = df["date"].map(role).fillna("")
    return df, {"n_registry_tanks": len(reg), "n_dates": len(base), "n_fit_dates": len(fit), "n_val_dates": len(val),
                "n_usable_registry": int(base.usable.sum()),
                "n_usable_yolo": int(df[(df.tank_source == "yolo") & (df.method == "cnn")].usable.sum()) if det is not None else 0}


def weekly_grid(df, method, source, split, c):
    s = c["splits"]
    lo, hi = (s["train_start"], s["train_end"]) if split == "train" else (s["test_start"], s["test_end"])
    eia = load_eia(c)
    eia = eia[(eia.week_end >= lo) & (eia.week_end <= hi)].reset_index(drop=True)
    sub = df[(df.method == method) & (df.tank_source == source) & (df.split == split) & df.usable]
    pred = sub.groupby("week_end").pred_mbbl.mean()
    return eia.week_end, eia.eia_mbbl.to_numpy(), eia.week_end.map(pred).to_numpy(dtype=float)


def metrics_rows(df, c):
    st = c["stats"]
    rows = []
    for (method, source), _ in df.groupby(["method", "tank_source"]):
        for split in ("train", "test"):
            wk, eia, pred = weekly_grid(df, method, source, split, c)
            kinds = [("level", pred, eia)] + [(f"diff_lag{k}", *first_diff_pairs(pred, eia, k)) for k in st["diff_lags"]]
            for kind, x, y in kinds:
                r, n = pearson(x, y)
                row = {"method": method, "tank_source": source, "split": split, "metric": kind, "n_pairs": n, "pearson_r": r}
                if kind == "level" and n >= 4 and np.nanstd(x) > 0:
                    row.update({k: v for k, v in level_metrics(x, y).items() if k not in ("n", "pearson_r")})
                if n >= 8 and not np.isnan(r):
                    for b in st["block_lengths"]:
                        lo, hi, _ = boot_corr(x, y, b, st["n_boot"], st["ci"], seed=c["seed"])
                        tag = "" if b == st["block_lengths"][0] else f"_b{b}"
                        row[f"ci_lo{tag}"], row[f"ci_hi{tag}"] = lo, hi
                rows.append(row)
    cols = ["method", "tank_source", "split", "metric", "n_pairs", "pearson_r", "pearson_p", "spearman_rho",
            "spearman_p", "r2", "rmse", "ci_lo", "ci_hi"]
    out = pd.DataFrame(rows)
    for col in cols + [f"ci_{e}_b{b}" for b in st["block_lengths"][1:] for e in ("lo", "hi")]:
        if col not in out:
            out[col] = np.nan
    return out


def verdicts(metrics, c):
    st, v = c["stats"], {}
    y = ROOT / "results" / "ml_yolo_metrics.csv"
    if y.exists():
        m = pd.read_csv(y).iloc[0]
        v["H1"] = {"status": "PASS" if (m.map50 >= c["h1"]["map50_min"] and m.precision >= c["h1"]["precision_min"]) else "FAIL",
                   "map50": float(m.map50), "precision": float(m.precision), "recall": float(m.recall)}
    else:
        v["H1"] = {"status": "NOT RUN"}
    v["H2"] = {"status": "NOT TESTABLE", "reason": "no per-tank fill labels; supervision is hub-level EIA only"}
    for source in ("yolo", "registry"):
        sub = metrics[(metrics.method == "cnn") & (metrics.tank_source == source) & (metrics.split == "test")]
        if sub.empty:
            v[f"H3_{source}"] = {"status": "NOT RUN"}
            continue
        lvl = sub[sub.metric == "level"].iloc[0]
        d = sub[sub.metric.str.startswith("diff")]
        level_ok = bool(lvl.pearson_r >= st["level_r_min"] and lvl.pearson_p < st["level_p_max"] and lvl.ci_lo > 0)
        diff_ok = bool(len(d) == len(st["diff_lags"]) and (d.ci_lo > 0).all())
        base = metrics[(metrics.tank_source == source) & (metrics.split == "test") & (metrics.metric == "level") & (metrics.method != "cnn")]
        best_base = float(base.r2.max()) if len(base) and base.r2.notna().any() else None
        beats = bool(best_base is None or (lvl.r2 > best_base))
        v[f"H3_{source}"] = {"status": "PASS" if (level_ok and diff_ok and beats) else "FAIL", "level_pass": level_ok,
                             "diff_pass": diff_ok, "beats_baselines": beats, "pearson_r": float(lvl.pearson_r),
                             "pearson_p": float(lvl.pearson_p), "r2": float(lvl.r2), "best_baseline_r2": best_base}
    return v


def main():
    c = cfg()
    RES.mkdir(exist_ok=True)
    df, counts = weekly_rows(c)
    df.to_csv(RES / "ml_weekly_inventory.csv", index=False)
    metrics = metrics_rows(df, c)
    metrics.to_csv(RES / "ml_eia_metrics.csv", index=False)
    pd.DataFrame([{"hypothesis": "H2", "status": "NOT_TESTABLE", "n_tank_labels": 0,
                   "reason": "no per-tank fill-level ground truth; the CNN is trained on hub-level EIA stocks only"}]
                 ).to_csv(RES / "ml_tank_metrics.csv", index=False)
    out = {"counts": counts, "verdicts": verdicts(metrics, c)}
    (RES / "ml_verdicts.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps(out, indent=2, default=float))


if __name__ == "__main__":
    main()
