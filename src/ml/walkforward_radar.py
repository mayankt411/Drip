"""v4.1: walk-forward test of the Sentinel-1 radar model, exactly as fixed in docs/preregistration_v4_1.md.
Each fold trains on past years only and scores the next year once. Features, alpha grid, thresholds, folds
and windows are frozen; do not edit them after the pre-registration commit."""
import json
import warnings
from datetime import date

import numpy as np
import pandas as pd

from . import evaluate_radar as ev
from .radar import FEATS
from .stats import boot_corr, first_diff_pairs, level_metrics, pearson

MIN_TRAIN = 40
GAP = (5, 14)
SHIFTS = [k for k in range(-52, 53) if abs(k) >= 13]
PROSPECTIVE = ("2026-11-01", "2027-04-30", date(2027, 5, 1))
PRIMARY = ["2020", "2021", "2022"]
VARIANT = {False: "all_tanks", True: "floating_roof_tanks_only"}
VARIANTS = ["radar_large_tanks", "radar_plus_season"]  # reported, never used for the verdict


def setup(c, r, only_floating=False, drop_bare=False):
    tanks = pd.read_csv(ev.REGISTRY)
    eia = ev.load_eia_all(c)
    meta, F = ev.load_passes()
    start = r["train_start"]
    cov = ev.OUT / "coverage.json"
    if cov.exists():
        start = max(start, json.loads(cov.read_text(encoding="utf-8"))["effective_start"])
    w = tanks.area_weight_m2.to_numpy()
    if only_floating:  # v4.2: keep only tanks read as open floating roofs; fixed roofs and unsure tanks get zero weight
        w = np.where((tanks.roof_shape == "floating_roof").to_numpy(), w, 0.0)
    if drop_bare and "bare_ground" in tanks:  # v4.3: three registry entries that are bare ground, not tanks
        w = np.where(tanks.bare_ground.to_numpy() == 1, 0.0, w)
    big = np.where(tanks.diameter_m.to_numpy() >= r["large_tank_min_m"], w, 0.0)
    return dict(meta=meta, F=F, w=w, big=big, eia=eia, r=r, start=start)


def interp_eia(dates, eia):
    """EIA linearly interpolated to each date from the two Fridays around it (rule A)."""
    t = eia.week_end.map(pd.Timestamp.toordinal).to_numpy(float)
    d = pd.DatetimeIndex(dates).map(pd.Timestamp.toordinal).to_numpy(float)
    left = np.searchsorted(t, d, side="right") - 1
    right = np.searchsorted(t, d, side="left")
    ok = (left >= 0) & (right < len(t))
    ok[ok] = (t[right[ok]] - t[left[ok]]) <= 7
    return np.where(ok, np.interp(d, t, eia.eia_mbbl.to_numpy()), np.nan)


def gap_pairs(p):
    """Rule B: changes between consecutive observed pass-days 5 to 14 days apart.
    Lag 0 pairs the radar change with the EIA change over the same interval, lag 1 with the next interval's."""
    p = p.dropna(subset=["radar_all", "eia_interp"]).sort_values("date")
    d = p.date.map(pd.Timestamp.toordinal).to_numpy()
    dx, dy = np.diff(p.radar_all.to_numpy()), np.diff(p.eia_interp.to_numpy())
    ok = (np.diff(d) >= GAP[0]) & (np.diff(d) <= GAP[1])
    both = ok[:-1] & ok[1:]
    return (dx[ok], dy[ok]), (dx[:-1][both], dy[1:][both])


def fold(name, ctx, train_end, lo, hi):
    meta, F, w, eia, r, start = (ctx[k] for k in ["meta", "F", "w", "eia", "r", "start"])
    r2 = {**r, "train_end": train_end}
    wk = ev.weekly_features(meta, F, w, eia, r2, start)
    tr = wk[(wk.week_end >= start) & (wk.week_end <= train_end)]
    te = wk[(wk.week_end >= lo) & (wk.week_end <= hi)]
    if len(tr) < MIN_TRAIN or len(te) == 0:
        return {"name": name, "scored": False, "n_train": len(tr), "n_test": len(te)}
    # pass-level features with this fold's tank baselines
    train = ((meta.date >= start) & (meta.date <= train_end)).to_numpy()
    H = ev.hub(ev.deviations(meta, F, train, r["min_baseline_passes"]), w, r["min_valid_fraction"])
    ps = pd.DataFrame(H, columns=FEATS)
    ps["date"] = meta.date.to_numpy()
    ps = ps.dropna().groupby("date")[FEATS].mean().reset_index()
    ps = ps[(ps.date >= lo) & (ps.date <= hi)]
    pred, alpha = ev.fit_predict(tr[FEATS].to_numpy(), tr.eia_mbbl.to_numpy(),
                                 np.vstack([te[FEATS].to_numpy(), ps[FEATS].to_numpy()]), r)
    out = te[["week_end", "eia_mbbl"]].copy()
    out["radar_all"] = pred[:len(te)]
    for v, wt, season in [("radar_large_tanks", ctx["big"], False), ("radar_plus_season", w, True)]:
        p, _ = ev.run_variant(v, wt, meta, F, eia, r2, start, season, lo, hi)
        out[v] = out.week_end.map(p) if p is not None else np.nan
    tre = eia[(eia.week_end >= start) & (eia.week_end <= train_end)]
    sx = ev.harmonics(tre.week_end)
    mu, sd = sx.mean(0), sx.std(0) + 1e-9
    sea = ev.ridge((sx - mu) / sd, tre.eia_mbbl.to_numpy(), 1e-6)
    out["season_only"] = sea((ev.harmonics(out.week_end) - mu) / sd)
    out["train_mean"] = tre.eia_mbbl.mean()
    out["fold"] = name
    pas = pd.DataFrame({"date": ps.date.to_numpy(), "radar_all": pred[len(te):], "fold": name})
    pas["eia_interp"] = interp_eia(pas.date, eia)
    # v4 rule kept for comparison: strictly consecutive weeks on the full weekly grid
    grid = eia[(eia.week_end >= lo) & (eia.week_end <= hi)]
    sat = grid.week_end.map(out.set_index("week_end").radar_all).to_numpy(float)
    wk0, wk1 = (first_diff_pairs(sat, grid.eia_mbbl.to_numpy(), k) for k in (0, 1))
    g0, g1 = gap_pairs(pas)
    return {"name": name, "scored": True, "alpha": alpha, "n_train": len(tr), "n_test": len(te),
            "weekly": out, "passes": pas, "pairs": {"diff_lag0_week": wk0, "diff_lag1_week": wk1, "diff_lag0_gap": g0, "diff_lag1_gap": g1}}


def r2_of(x, y):
    ok = ~(np.isnan(x) | np.isnan(y))
    return float(1 - ((y[ok] - x[ok]) ** 2).sum() / ((y[ok] - y[ok].mean()) ** 2).sum()) if ok.sum() >= 2 else np.nan


def placebo(W, eia):
    """95th percentile of |r| when EIA is shifted by whole weeks, 13 to 52 either way."""
    s = eia.set_index("week_end").eia_mbbl
    rs = []
    for k in SHIFTS:
        r, n = pearson(W.radar_all.to_numpy(float), (W.week_end + pd.Timedelta(days=7 * k)).map(s).to_numpy(float))
        if n >= 8 and not np.isnan(r):
            rs.append(abs(r))
    return (float(np.quantile(rs, 0.95)) if rs else np.nan), len(rs)


def scope_rows(scope, parts, eia, st, seed, with_placebo):
    parts = [p for p in parts if p["scored"]]
    if not parts:
        return []
    W = pd.concat([p["weekly"] for p in parts], ignore_index=True)
    P = pd.concat([p["passes"] for p in parts], ignore_index=True)
    boot = lambda x, y: boot_corr(x, y, st["block_lengths"][0], st["n_boot"], st["ci"], seed=seed)

    def row(kind, x, y, ci=True, **kw):
        x, y = np.asarray(x, float), np.asarray(y, float)
        ok = ~(np.isnan(x) | np.isnan(y))
        x, y = x[ok], y[ok]
        out = {"scope": scope, "comparison": kind, "n": int(ok.sum()), **kw}
        if len(x) >= 8 and np.ptp(x) > 1e-9 and np.ptp(y) > 1e-9:
            m = level_metrics(x, y)
            out.update(pearson_r=m["pearson_r"], pearson_p=m["pearson_p"])
            if ci:
                out["ci_lo"], out["ci_hi"], _ = boot(x, y)
        return out

    y = W.eia_mbbl.to_numpy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rows = [row("level", W.radar_all, y, r2=r2_of(W.radar_all.to_numpy(), y))]
        rows += [row(f"level_{v}", W[v], y, r2=r2_of(W[v].to_numpy(), y)) for v in VARIANTS]
        rows += [row(f"level_{b}", W[b], y, ci=False, r2=r2_of(W[b].to_numpy(), y)) for b in ["season_only", "train_mean"]]
        rows.append(row("level_pass", P.radar_all, P.eia_interp, r2=r2_of(P.radar_all.to_numpy(float), P.eia_interp.to_numpy(float))))
        for k in ["diff_lag0_week", "diff_lag1_week", "diff_lag0_gap", "diff_lag1_gap"] + [k for k in parts[0]["pairs"] if k.endswith("_exact")]:
            rows.append(row(k, np.concatenate([p["pairs"][k][0] for p in parts]), np.concatenate([p["pairs"][k][1] for p in parts])))
        if with_placebo:
            p95, n = placebo(W, eia)
            rows.append({"scope": scope, "comparison": "placebo", "n": n, "p95_abs_r": p95})
    return rows


def criteria(M, r3):
    g = M.set_index("comparison")
    get = lambda k, col: g.loc[k, col] if k in g.index and col in g.columns else np.nan
    r_true = get("level", "pearson_r")
    base = np.nanmax([get("level_season_only", "r2"), get("level_train_mean", "r2")])
    c = {"r_ok": r_true >= r3["r_min"], "p_ok": get("level", "pearson_p") < r3["p_max"], "ci_ok": get("level", "ci_lo") > 0,
         "diff_ok": bool(get("diff_lag0_gap", "ci_lo") > 0 and get("diff_lag1_gap", "ci_lo") > 0),
         "beats_baselines": get("level", "r2") > base, "placebo_ok": r_true > get("placebo", "p95_abs_r"), "positive": r_true > 0}
    return {k: bool(v) for k, v in c.items()}


def claim(c):
    if all(c.values()):
        return "Radar tracks Cushing stocks, level and changes, on previously unscored years; the prospective window decides."
    if not (c["r_ok"] and c["p_ok"] and c["ci_ok"] and c["positive"]):
        return "The 2023-2026 level result did not generalise to 2020-2022."
    if not c["placebo_ok"]:
        return "The alignment is not distinguishable from chance."
    if not c["beats_baselines"]:
        return "Radar tracks the level but does not beat the baselines."
    return "Radar tracks the level, not weekly changes."


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    return o


def save(tag, M, parts, verdict):
    ev.RES.mkdir(exist_ok=True)
    M.to_csv(ev.RES / f"{tag}_metrics.csv", index=False)
    ok = [p for p in parts if p["scored"]]
    if ok:
        pd.concat([p["weekly"] for p in ok]).to_csv(ev.RES / f"{tag}_weekly.csv", index=False)
        pd.concat([p["passes"] for p in ok]).to_csv(ev.RES / f"{tag}_passes.csv", index=False)
    (ev.RES / f"{tag}_verdict.json").write_text(json.dumps(clean(verdict), indent=2), encoding="utf-8")
    print(json.dumps(clean(verdict), indent=2))
    print(M[M.comparison.isin(["level", "level_pass", "diff_lag0_gap", "diff_lag1_gap", "placebo"])].to_string(index=False))


def main(mode="run", today=None):
    """mode: run, prospective, or either with _float for the floating-roof-only variant (docs/preregistration_v4_2.md)."""
    c, r = ev.cfg(), ev.rc()
    st, seed = c["stats"], c["seed"]
    float_only, mode = mode.endswith("_float"), mode.removesuffix("_float")
    sfx = "_float" if float_only else ""
    if mode == "prospective" and (today or date.today()) < PROSPECTIVE[2]:
        raise SystemExit(f"The prospective window is scored once, no earlier than {PROSPECTIVE[2]}.")
    ctx = setup(c, r, float_only)
    eia, last = ctx["eia"], ctx["eia"].week_end.max()
    if mode == "prospective":
        parts = [fold("prospective", ctx, r["train_end"], PROSPECTIVE[0], PROSPECTIVE[1])]
        M = pd.DataFrame(scope_rows("prospective", parts, eia, st, seed, True))
        c1 = criteria(M, r["h3"])
        save("h3_radar_wf_prospective" + sfx, M, parts, {"status": "PASS" if all(c1.values()) else "FAIL", **c1, "claim": claim(c1), "variant": VARIANT[float_only]})
        return
    folds = [fold(str(y), ctx, f"{y - 1}-12-31", f"{y}-01-01", min(pd.Timestamp(f"{y}-12-31"), last))
             for y in range(2020, 2027) if pd.Timestamp(f"{y}-01-01") <= last]
    wins = [fold("v4_window1", ctx, r["train_end"], r["test_start"], r["test_end"]),
            fold("v4_window2", ctx, r["train_end"], r["confirm_start"], r["confirm_end"])]
    by = {p["name"]: p for p in folds}
    scopes = [("primary_2020_2022", [by[k] for k in PRIMARY if k in by], True), ("pooled_2020_2026", folds, True)]
    scopes += [(p["name"], [p], False) for p in folds + wins]
    M = pd.DataFrame([x for s, ps, pl in scopes for x in scope_rows(s, ps, eia, st, seed, pl)])
    crit = {s: criteria(M[M.scope == s], r["h3"]) for s in ["primary_2020_2022", "pooled_2020_2026"] if (M.scope == s).any()}
    prim, pool = crit.get("primary_2020_2022"), crit.get("pooled_2020_2026")
    status = "NOT_TESTABLE" if prim is None else "PASS" if all(prim.values()) else "PARTIAL" if pool and all(pool.values()) else "FAIL"
    verdict = {"status": status, "primary": prim, "pooled_2020_2026": pool, "claim": claim(prim) if prim else None,
               "folds": {p["name"]: {k: p[k] for k in ["scored", "n_train", "n_test", "alpha"] if k in p} for p in folds + wins},
               "v4_verdict_unchanged": "FAIL", "variant": VARIANT[float_only],
               "note": "level and baseline rules use weekly units as in v4; difference rules use gap-tolerant pairs (rule B); variants are not used for the verdict"}
    save("h3_radar_wf" + sfx, M, folds + wins, verdict)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "run")
