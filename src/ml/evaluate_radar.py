"""H3 with Sentinel-1: weekly radar features against EIA Cushing stocks.
Everything is fitted on the training years only; the test years are scored once. The radar features are
each tank's departure from its own training mean for the same orbit. No sign flipping, no smoothing."""
import json
import warnings

import numpy as np
import pandas as pd

from .common import ROOT, cfg
from .eia import assign_weeks
from .radar import FEATS, OUT, REGISTRY, rc
from .stats import boot_corr, first_diff_pairs, level_metrics

RES = ROOT / "results"


def load_eia_all(c):
    rows = []
    for p in sorted((ROOT / "data" / "raw").glob("eia_cushing_weekly_*.json")):
        for r in json.load(open(p, encoding="utf-8"))["response"]["data"]:
            if r["series"] == c["eia"]["series"]:
                rows.append((r["period"], float(r["value"])))
    df = pd.DataFrame(rows, columns=["week_end", "eia_mbbl"]).drop_duplicates("week_end")
    df["week_end"] = pd.to_datetime(df["week_end"])
    return df.sort_values("week_end").reset_index(drop=True)


def load_passes():
    groups = {}
    for f in sorted((OUT / "feat").glob("*.npz")):
        try:
            z = np.load(f)
            groups.setdefault((str(z["date"]), f"{z['orbit']}{int(z['rel_orbit'])}"), []).append(z["feats"])
        except Exception:  # a file cut off by an interrupted run; skip it
            print("skipping unreadable", f.name)
    keys = sorted(groups)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        F = np.stack([np.nanmean(np.stack(groups[k]), 0) for k in keys])
    meta = pd.DataFrame(keys, columns=["date", "key"])
    meta["date"] = pd.to_datetime(meta["date"])
    return meta, F


def deviations(meta, F, train, nmin):
    """Each tank's feature minus its own training mean for the same orbit."""
    D = np.full_like(F, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _, idx in meta.groupby("key").indices.items():
            tr = idx[train[idx]]
            if len(tr) < nmin:
                continue
            mu = np.nanmean(F[tr], 0)
            mu[(~np.isnan(F[tr])).sum(0) < nmin] = np.nan
            D[idx] = F[idx] - mu
    return D


def hub(D, w, minfrac):
    """Area-weighted mean over tanks seen on that pass; NaN if too little of the hub was seen."""
    out = np.full((len(D), D.shape[2]), np.nan)
    for j in range(D.shape[2]):
        m = ~np.isnan(D[:, :, j])
        den = (w * m).sum(1)
        out[:, j] = np.where(den >= minfrac * w.sum(), (np.nan_to_num(D[:, :, j]) * w * m).sum(1) / np.maximum(den, 1e-9), np.nan)
    return out


def harmonics(dates):
    t = 2 * np.pi * pd.DatetimeIndex(dates).dayofyear.to_numpy() / 365.25
    return np.c_[np.sin(t), np.cos(t)]


def ridge(Z, y, a):
    ym = y.mean()
    b = np.linalg.solve(Z.T @ Z + a * np.eye(Z.shape[1]), Z.T @ (y - ym))
    return lambda Zn: ym + Zn @ b


def fit_predict(Xtr, ytr, Xte, rcfg):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    Ztr, Zte = (Xtr - mu) / sd, (Xte - mu) / sd
    folds = np.array_split(np.arange(len(ytr)), rcfg["cv_folds"])  # contiguous blocks, no shuffling
    best, alpha = np.inf, None
    for a in rcfg["ridge_alphas"]:
        err = 0.0
        for f in folds:
            tr = np.setdiff1d(np.arange(len(ytr)), f)
            err += ((ridge(Ztr[tr], ytr[tr], a)(Ztr[f]) - ytr[f]) ** 2).sum()
        if err < best:
            best, alpha = err, a
    return ridge(Ztr, ytr, alpha)(Zte), alpha


def weekly_features(meta, F, w, eia, rcfg, train_start):
    d = meta.date
    train = ((d >= train_start) & (d <= rcfg["train_end"])).to_numpy()
    D = deviations(meta, F, train, rcfg["min_baseline_passes"])
    H = hub(D, w, rcfg["min_valid_fraction"])
    wk = pd.DataFrame(H, columns=FEATS)
    wk["week_end"] = assign_weeks(meta.date, eia).to_numpy()
    wk = wk.dropna()
    return wk.groupby("week_end")[FEATS].mean().reset_index().merge(eia, on="week_end", how="inner")


def run_variant(name, w, meta, F, eia, rcfg, train_start, with_season=False, lo=None, hi=None):
    wk = weekly_features(meta, F, w, eia, rcfg, train_start)
    tr = wk[(wk.week_end >= train_start) & (wk.week_end <= rcfg["train_end"])]
    te = wk[(wk.week_end >= (lo or rcfg["test_start"])) & (wk.week_end <= (hi or rcfg["test_end"]))]
    X = lambda df: np.c_[df[FEATS].to_numpy(), harmonics(df.week_end)] if with_season else df[FEATS].to_numpy()
    if len(tr) < 30 or len(te) < 8:
        return None, {"n_train": len(tr), "n_test": len(te)}
    pred, alpha = fit_predict(X(tr), tr.eia_mbbl.to_numpy(), X(te), rcfg)
    return pd.Series(pred, index=te.week_end), {"alpha": alpha, "n_train": len(tr), "n_test": len(te)}


def score(name, pred, truth, st, seed, lags):
    rows = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        kinds = [("level", pred, truth)] + [(f"diff_lag{k}", *first_diff_pairs(pred, truth, k)) for k in lags]
        for kind, x, y in kinds:
            ok = ~(np.isnan(x) | np.isnan(y))
            row = {"variant": name, "comparison": kind, "n": int(ok.sum())}
            if kind == "level" and ok.sum() >= 8:
                ss = ((y[ok] - x[ok]) ** 2).sum()
                row.update(r2=1 - ss / ((y[ok] - y[ok].mean()) ** 2).sum(), rmse=float(np.sqrt(ss / ok.sum())))
            if ok.sum() >= 8 and np.ptp(x[ok]) > 1e-9 and np.ptp(y[ok]) > 1e-9:
                m = level_metrics(x, y)
                row.update(pearson_r=m["pearson_r"], pearson_p=m["pearson_p"])
                row["ci_lo"], row["ci_hi"], _ = boot_corr(x, y, st["block_lengths"][0], st["n_boot"], st["ci"], seed=seed)
            rows.append(row)
    return rows


def verdict(m, r3):
    p = m[m.variant == "radar_all"].set_index("comparison")
    if "level" not in p.index or pd.isna(p.loc["level"].get("pearson_r", np.nan)):
        return {"status": "NOT_TESTABLE", "reason": "too few overlapping test weeks"}
    lv = p.loc["level"]
    base = m[(m.comparison == "level") & m.variant.isin(["season_only", "train_mean"])].r2.max()
    diffs = [p.loc[f"diff_lag{k}"] for k in r3["diff_lags"]]
    crit = {"r_ok": bool(lv.pearson_r >= r3["r_min"]), "p_ok": bool(lv.pearson_p < r3["p_max"]), "ci_ok": bool(lv.ci_lo > 0),
            "diff_ok": bool(all(d.get("ci_lo", np.nan) > 0 for d in diffs)), "beats_baselines": bool(lv.r2 > base)}
    return {"status": "PASS" if all(crit.values()) else "FAIL", **crit, "pearson_r": float(lv.pearson_r),
            "pearson_p": float(lv.pearson_p), "r2": float(lv.r2), "best_baseline_r2": float(base), "n_test_weeks": int(lv.n)}


def main(window="test"):
    """window 'confirm' scores the same model on the later, never-inspected weeks."""
    c, r = cfg(), rc()
    lo, hi, tag = (r["test_start"], r["test_end"], "h3_radar") if window == "test" else (r["confirm_start"], r["confirm_end"], "h3_radar_confirm")
    st = c["stats"]
    tanks = pd.read_csv(REGISTRY)
    eia = load_eia_all(c)
    meta, F = load_passes()
    start = r["train_start"]
    cov = OUT / "coverage.json"
    if cov.exists():
        start = max(start, json.loads(cov.read_text(encoding="utf-8"))["effective_start"])
    w = tanks.area_weight_m2.to_numpy()
    big = np.where(tanks.diameter_m.to_numpy() >= r["large_tank_min_m"], w, 0.0)
    grid = eia[(eia.week_end >= lo) & (eia.week_end <= hi)].reset_index(drop=True)
    tr_eia = eia[(eia.week_end >= start) & (eia.week_end <= r["train_end"])]
    sx = harmonics(tr_eia.week_end)
    sea = ridge((sx - sx.mean(0)) / (sx.std(0) + 1e-9), tr_eia.eia_mbbl.to_numpy(), 1e-6)
    z = harmonics(grid.week_end)
    preds, info = {}, {}
    for name, wt, ws in [("radar_all", w, False), ("radar_large_tanks", big, False), ("radar_plus_season", w, True)]:
        p, info[name] = run_variant(name, wt, meta, F, eia, r, start, ws, lo, hi)
        grid[name] = grid.week_end.map(p) if p is not None else np.nan
    grid["season_only"] = sea((z - sx.mean(0)) / (sx.std(0) + 1e-9))
    grid["train_mean"] = tr_eia.eia_mbbl.mean()
    seen = grid.radar_all.notna()  # baselines are scored on the same weeks as the radar model
    truth = grid.eia_mbbl.to_numpy()
    rows = []
    for name in ["radar_all", "radar_large_tanks", "radar_plus_season"]:
        rows += score(name, grid[name].to_numpy(), truth, st, c["seed"], r["h3"]["diff_lags"])
    for name in ["season_only", "train_mean"]:
        rows += score(name, np.where(seen, grid[name], np.nan), truth, st, c["seed"], r["h3"]["diff_lags"])
    m = pd.DataFrame(rows)
    v = verdict(m, r["h3"])
    v.update({"train_start": start, "n_passes": int(len(meta)), "info": info,
              "note": "radar_large_tanks and radar_plus_season are reported, not used for the verdict"})
    RES.mkdir(exist_ok=True)
    m.to_csv(RES / f"{tag}_metrics.csv", index=False)
    grid.to_csv(RES / f"{tag}_weekly.csv", index=False)
    (RES / f"{tag}_verdict.json").write_text(json.dumps(v, indent=2, default=float), encoding="utf-8")
    print(json.dumps(v, indent=2, default=float))
    print(m[m.comparison == "level"].to_string(index=False))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "test")
