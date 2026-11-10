"""v4.3: per-tank learned weights and exact-date EIA matching on the v4.1 walk-forward.
Plan and rules: docs/preregistration_v4_3.md. Two models run side by side on the same folds:
pertank (ridge over every tank's features, the new model) and hub (the v4.1 model, for comparison)."""
import warnings
from datetime import date

import numpy as np
import pandas as pd

from . import evaluate_radar as ev
from . import walkforward_radar as wf
from .eia import assign_weeks
from .stats import first_diff_pairs

ALPHAS = [1.0, 10.0, 100.0, 1000.0, 10000.0]
CLIP, EXACT_DAYS = 5.0, 1
RANK = {"NOT_TESTABLE": -1, "FAIL": 0, "PARTIAL": 1, "PASS": 2}


def ridge_wide(Z, y, a):
    """Ridge when there are more columns than weeks: solve in the weeks-by-weeks space."""
    ym = y.mean()
    u = np.linalg.solve(Z @ Z.T + a * np.eye(len(Z)), y - ym)
    b = Z.T @ u
    return lambda Zn: ym + Zn @ b


def fit_predict(Xtr, ytr, Xte, k=5):
    mu, sd = np.nanmean(Xtr, 0), np.nanstd(Xtr, 0)
    use = np.isfinite(mu) & (sd > 1e-9)
    z = lambda X: np.where(use, np.clip(np.nan_to_num((X - np.where(use, mu, 0)) / np.where(use, sd, 1), nan=0.0), -CLIP, CLIP), 0.0)
    Ztr, Zte = z(Xtr), z(Xte)
    folds = np.array_split(np.arange(len(ytr)), k)  # contiguous blocks, as in v4
    best, alpha = np.inf, ALPHAS[0]
    for a in ALPHAS:
        err = 0.0
        for f in folds:
            tr = np.setdiff1d(np.arange(len(ytr)), f)
            err += ((ridge_wide(Ztr[tr], ytr[tr], a)(Ztr[f]) - ytr[f]) ** 2).sum()
        if err < best:
            best, alpha = err, a
    return ridge_wide(Ztr, ytr, alpha)(Zte), alpha


def exact_eia(dates, eia, days=EXACT_DAYS):
    """EIA Friday value for passes within a day of a reporting Friday; NaN otherwise. No interpolation."""
    t = eia.week_end.map(pd.Timestamp.toordinal).to_numpy(float)
    d = pd.DatetimeIndex(dates).map(pd.Timestamp.toordinal).to_numpy(float)
    i = np.abs(d[:, None] - t[None, :]).argmin(1)
    return np.where(np.abs(d - t[i]) <= days, eia.eia_mbbl.to_numpy()[i], np.nan)


def pairs_for(out, pas, eia, lo, hi):
    grid = eia[(eia.week_end >= lo) & (eia.week_end <= hi)]
    sat = grid.week_end.map(out.set_index("week_end").radar_all).to_numpy(float)
    wk0, wk1 = (first_diff_pairs(sat, grid.eia_mbbl.to_numpy(), k) for k in (0, 1))
    g0, g1 = wf.gap_pairs(pas)
    e0, e1 = wf.gap_pairs(pas.assign(eia_interp=exact_eia(pas.date, eia)))
    return {"diff_lag0_week": wk0, "diff_lag1_week": wk1, "diff_lag0_gap": g0, "diff_lag1_gap": g1,
            "diff_lag0_exact": e0, "diff_lag1_exact": e1}


def pertank(base, ctx, train_end, lo, hi):
    """Swap the hub prediction for a ridge over all kept tanks' deviation features."""
    meta, F, w, eia, r, start = (ctx[k] for k in ["meta", "F", "w", "eia", "r", "start"])
    train = ((meta.date >= start) & (meta.date <= train_end)).to_numpy()
    keep = w > 0
    D = ev.deviations(meta, F, train, r["min_baseline_passes"])[:, keep, :]
    P, N, K = D.shape
    X = D.reshape(P, N * K)
    seen = (~np.isnan(D)).any(2)
    ok = ((seen * w[keep]).sum(1) / w[keep].sum()) >= r["min_valid_fraction"]
    weeks = assign_weeks(meta.date, eia).to_numpy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        W = pd.DataFrame(X[ok]).groupby(weeks[ok]).mean()
        Pd = pd.DataFrame(X[ok]).groupby(meta.date.to_numpy()[ok]).mean()
    W.index = pd.DatetimeIndex(W.index)
    W = W.join(eia.set_index("week_end").eia_mbbl, how="inner")
    tr = W[(W.index >= start) & (W.index <= train_end)]
    cols = list(range(N * K))
    out, pas = base["weekly"].copy(), base["passes"].copy()
    out["radar_hub"], pas["radar_hub"] = out.radar_all, pas.radar_all
    if len(tr) < wf.MIN_TRAIN:
        out["radar_all"], pas["radar_all"] = np.nan, np.nan
        return {**base, "weekly": out, "passes": pas, "alpha": np.nan}
    te_w = out.week_end[out.week_end.isin(W.index)]
    pd_in = Pd[(Pd.index >= lo) & (Pd.index <= hi)] if len(Pd) else Pd
    Xte = np.vstack([W.loc[te_w, cols].to_numpy(), pd_in[cols].to_numpy()]) if len(pd_in) else W.loc[te_w, cols].to_numpy()
    pred, alpha = fit_predict(tr[cols].to_numpy(), tr.eia_mbbl.to_numpy(), Xte)
    out["radar_all"] = out.week_end.map(pd.Series(pred[:len(te_w)], index=te_w.to_numpy()))
    pas["radar_all"] = pas.date.map(pd.Series(pred[len(te_w):], index=pd_in.index.to_numpy()))
    return {**base, "weekly": out, "passes": pas, "alpha": alpha}


def with_pairs(p, eia, lo, hi):
    if not p["scored"]:
        return p
    return {**p, "pairs": pairs_for(p["weekly"], p["passes"], eia, lo, hi)}


def exact_ok(M):
    g = M.set_index("comparison")
    return bool(all(k in g.index and g.loc[k, "ci_lo"] > 0 for k in ["diff_lag0_exact", "diff_lag1_exact"]))


def run_model(model, bases, spans, ctx, eia, st, seed, r):
    folds = []
    for b, (tr_end, lo, hi) in zip(bases, spans):
        if b["scored"] and model == "pertank":
            b = pertank(b, ctx, tr_end, lo, hi)
        folds.append(with_pairs(b, eia, lo, hi))
    return folds


def judge(folds, wins, eia, st, seed, r, model):
    by = {p["name"]: p for p in folds}
    scopes = [("primary_2020_2022", [by[k] for k in wf.PRIMARY if k in by], True), ("pooled_2020_2026", folds, True)]
    scopes += [(p["name"], [p], False) for p in folds + wins]
    M = pd.DataFrame([x for s, ps, pl in scopes for x in wf.scope_rows(s, ps, eia, st, seed, pl)])
    crit = {s: wf.criteria(M[M.scope == s], r["h3"]) for s in ["primary_2020_2022", "pooled_2020_2026"] if (M.scope == s).any()}
    prim, pool = crit.get("primary_2020_2022"), crit.get("pooled_2020_2026")
    status = "NOT_TESTABLE" if prim is None else "PASS" if all(prim.values()) else "PARTIAL" if pool and all(pool.values()) else "FAIL"
    v = {"status": status, "model": model, "primary": prim, "pooled_2020_2026": pool, "claim": wf.claim(prim) if prim else None,
         "exact_date_ok": {s: exact_ok(M[M.scope == s]) for s in crit},
         "folds": {p["name"]: {k: p[k] for k in ["scored", "n_train", "n_test", "alpha"] if k in p} for p in folds + wins},
         "v4_verdict_unchanged": "FAIL", "v4_1_verdict_unchanged": "PARTIAL"}
    return M, v


def main(mode="run", today=None):
    c, r = ev.cfg(), ev.rc()
    st, seed = c["stats"], c["seed"]
    if mode == "prospective" and (today or date.today()) < wf.PROSPECTIVE[2]:
        raise SystemExit(f"The prospective window is scored once, no earlier than {wf.PROSPECTIVE[2]}.")
    ctx = wf.setup(c, r, drop_bare=True)
    eia, last = ctx["eia"], ctx["eia"].week_end.max()
    if mode == "prospective":
        span = (r["train_end"], wf.PROSPECTIVE[0], wf.PROSPECTIVE[1])
        base = wf.fold("prospective", ctx, *span)
        parts = run_model("pertank", [base], [span], ctx, eia, st, seed, r)
        M = pd.DataFrame(wf.scope_rows("prospective", parts, eia, st, seed, True))
        c1 = wf.criteria(M, r["h3"])
        wf.save("h3_radar_v43_prospective", M, parts, {"status": "PASS" if all(c1.values()) else "FAIL", **c1, "claim": wf.claim(c1), "exact_date_ok": exact_ok(M)})
        return
    spans = [(f"{y - 1}-12-31", f"{y}-01-01", min(pd.Timestamp(f"{y}-12-31"), last)) for y in range(2020, 2027) if pd.Timestamp(f"{y}-01-01") <= last]
    names = [str(y) for y in range(2020, 2027) if pd.Timestamp(f"{y}-01-01") <= last]
    spans += [(r["train_end"], r["test_start"], r["test_end"]), (r["train_end"], r["confirm_start"], r["confirm_end"])]
    names += ["v4_window1", "v4_window2"]
    bases = [wf.fold(n, ctx, *s) for n, s in zip(names, spans)]
    res, verdicts = {}, {}
    for model in ("hub", "pertank"):
        allf = run_model(model, bases, spans, ctx, eia, st, seed, r)
        M, verdicts[model] = judge(allf[:len(names) - 2], allf[len(names) - 2:], eia, st, seed, r, model)
        res[model] = (M, allf)
    pt = verdicts["pertank"]
    pt["vs_hub"] = {"hub_status": verdicts["hub"]["status"], "improved": bool(RANK[pt["status"]] > RANK[verdicts["hub"]["status"]])}
    for model in ("hub", "pertank"):
        wf.save(f"h3_radar_v43_{model}", res[model][0], res[model][1], verdicts[model])


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "run")
