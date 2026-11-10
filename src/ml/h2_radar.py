"""H2 from Sentinel-1: separate floating from fixed roofs using each tank's radar level and how much it moves over time.
Plan and rules: docs/preregistration_v4_2.md, section 3. Labels come from data/roofs/labels.csv (applied to the registry),
the split is split_h2. The size-controlled test (tanks up to 40 m) is the primary one; the all-tanks test is secondary."""
import json
import warnings

import numpy as np
import pandas as pd

from . import evaluate_radar as ev
from .common import ROOT, cfg
from .h2_common import labels, scores, size_rule
from .radar import FEATS

REG = ROOT / "data" / "tanks" / "cushing_full_registry.csv"
RES = ROOT / "results"
BAND_M, MIN_PASSES, ALPHAS = 40.0, 30, [0.1, 1.0, 10.0, 100.0]
TARGET_ACC, TARGET_F1 = 0.85, 0.80


def tank_features(meta, F, min_passes=MIN_PASSES):
    """Per tank: mean and spread (std) of each radar feature over time, taken per orbit and averaged by pass count."""
    T, K = F.shape[1], F.shape[2]
    num, den = np.zeros((T, 2 * K)), np.zeros((T, 2 * K))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _, idx in meta.groupby("key").indices.items():
            sub = F[idx]
            cnt = (~np.isnan(sub)).sum(0)
            w = np.where(cnt >= 10, cnt, 0).astype(float)
            for part, v in enumerate((np.nanmean(sub, 0), np.nanstd(sub, 0))):
                num[:, part * K:(part + 1) * K] += np.nan_to_num(v) * w
                den[:, part * K:(part + 1) * K] += w
    X = np.where(den > 0, num / np.maximum(den, 1e-9), np.nan)
    seen = (~np.isnan(F)).any(2).sum(0)
    return X, (seen >= min_passes) & ~np.isnan(X).any(1)


def fit_predict(Xtr, ytr, Xte, seed):
    """Ridge on a plus/minus one target; the penalty comes from 5-fold CV on the training tanks only."""
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    Ztr, Zte, t = (Xtr - mu) / sd, (Xte - mu) / sd, 2.0 * ytr - 1
    rng = np.random.default_rng(seed)
    fold = np.zeros(len(ytr), int)
    for k in (0, 1):
        i = np.flatnonzero(ytr == k)
        fold[rng.permutation(i)] = np.arange(len(i)) % 5
    err = []
    for a in ALPHAS:
        wrong = 0
        for f in range(5):
            tr = fold != f
            wrong += ((ev.ridge(Ztr[tr], t[tr], a)(Ztr[~tr]) > 0).astype(int) != ytr[~tr]).sum()
        err.append(wrong)
    a = ALPHAS[int(np.argmin(err))]
    return (ev.ridge(Ztr, t, a)(Zte) > 0).astype(int), a


def run_band(reg, X, valid, y, band, seed):
    ok = valid & (y >= 0)
    if band:
        ok &= (reg.diameter_m <= band).to_numpy()
    tr, te = ok & (reg.split_h2 == "train").to_numpy(), ok & (reg.split_h2 == "heldout").to_numpy()
    n = {"band_max_m": band, "train": [int((y[tr] == k).sum()) for k in (0, 1)], "heldout": [int((y[te] == k).sum()) for k in (0, 1)]}
    if min(n["train"]) < 20 or min(n["heldout"]) < 5:
        return [{"band_max_m": band, "model": "none", "status": "NOT_TESTABLE", "reason": f"too few tanks per class {n}"}], n
    d = reg.diameter_m.to_numpy()
    p, alpha = fit_predict(X[tr], y[tr], X[te], seed)
    preds = {"radar_ridge": p, "diameter_rule": size_rule(d[tr], y[tr], d[te]),
             "majority": np.full(te.sum(), np.bincount(y[tr]).argmax())}
    return [{"band_max_m": band, "model": m, "status": "SCORED", "n_test": int(te.sum()), "alpha": alpha if m == "radar_ridge" else np.nan,
             **scores(y[te], q)} for m, q in preds.items()], n


def verdict(rows):
    s = {r["model"]: r for r in rows if r["status"] == "SCORED"}
    if "radar_ridge" not in s:
        return {"status": "NOT_TESTABLE"}
    r = s["radar_ridge"]
    v = {"accuracy_ok": bool(r["accuracy"] >= TARGET_ACC), "f1_ok": bool(r["macro_f1"] >= TARGET_F1),
         "beats_majority": bool(r["macro_f1"] > s["majority"]["macro_f1"]), "beats_size_rule": bool(r["macro_f1"] > s["diameter_rule"]["macro_f1"])}
    return {"status": "PASS" if all(v.values()) else "FAIL", **v}


def main():
    c = cfg()
    reg = pd.read_csv(REG)
    meta, F = ev.load_passes()
    X, valid = tank_features(meta, F)
    y = labels(reg)
    rows, counts, verd = [], {}, {}
    for name, band in (("size_controlled", BAND_M), ("all_tanks", None)):
        r, counts[name] = run_band(reg, X, valid, y, band, c["seed"])
        rows += r
        verd[name] = verdict(r)
    RES.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(RES / "h2_radar_metrics.csv", index=False)
    out = {"primary": "size_controlled", "verdict": verd, "counts": counts, "valid_tanks": int(valid.sum()), "features": ["mean_" + f for f in FEATS] + ["std_" + f for f in FEATS]}
    (RES / "h2_radar_verdict.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(json.dumps(out, indent=2, default=float))
    print(pd.DataFrame(rows)[["band_max_m", "model", "status", "accuracy", "macro_f1"]].to_string(index=False))


if __name__ == "__main__":
    main()
