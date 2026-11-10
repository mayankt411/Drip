"""H3: hub activity index against EIA Cushing stocks, raw and 4-week smoothed, on 2023-2024.
The index is how far tanks sit from their own development-year reflectance; it is not a stock level,
so only correlations are reported. No sign flipping, and a day-of-year control is always shown."""
import json

import numpy as np
import pandas as pd

from .common import ROOT, cfg
from .eia import load_eia
from .framework import activity_matrix, fw, load_inputs, tank_baseline
from .stats import boot_corr, first_diff_pairs, level_metrics, pearson

RES = ROOT / "results"


def weekly(dt, ok, act, reg):
    w = reg.area_weight_m2.to_numpy()
    m = ~np.isnan(act)
    idx = np.where(m.sum(1) > 0, (np.nan_to_num(act) * w * m).sum(1) / np.maximum((w * m).sum(1), 1e-9), np.nan)
    df = dt.assign(index=idx)
    df = df[df.usable & df["index"].notna()]
    return df.groupby(["split", "week_end"]).agg(index=("index", "mean"), n_dates=("index", "size")).reset_index()


def season_fit(eia, c):
    s = c["splits"]
    tr = eia[(eia.week_end >= s["train_start"]) & (eia.week_end <= s["train_end"])]
    t = 2 * np.pi * tr.week_end.dt.dayofyear.to_numpy() / 365.25
    X = np.c_[np.ones(len(t)), np.sin(t), np.cos(t)]
    beta = np.linalg.lstsq(X, tr.eia_mbbl.to_numpy(), rcond=None)[0]
    return lambda wk: np.c_[np.ones(len(wk)), np.sin(2 * np.pi * wk.dt.dayofyear.to_numpy() / 365.25),
                            np.cos(2 * np.pi * wk.dt.dayofyear.to_numpy() / 365.25)] @ beta


def metric_row(name, x, y, st, c, seed):
    r, n = pearson(x, y)
    row = {"comparison": name, "n_pairs": n, "pearson_r": r}
    if n >= 8 and not np.isnan(r):
        row.update({k: v for k, v in level_metrics(x, y).items() if k in ("pearson_p", "spearman_rho", "spearman_p")})
        row["ci_lo"], row["ci_hi"], _ = boot_corr(x, y, st["block_lengths"][0], st["n_boot"], st["ci"], seed=seed)
    return row


def main():
    c, f = cfg(), fw()
    h3, st = f["hypotheses"]["h3_macro_utilization"], c["stats"]
    bank, reg, ok, dt = load_inputs(c)
    mu, _, _ = tank_baseline(bank, ok, dt)
    wk = weekly(dt, ok, activity_matrix(bank, ok, mu), reg)
    eia = load_eia(c)
    win = h3["smoothing_window_weeks"]
    eia["eia_smooth"] = eia.eia_mbbl.rolling(win, min_periods=win).mean()
    s = c["splits"]
    test = wk[wk.split == "test"].merge(eia, on="week_end", how="left")
    grid = eia[(eia.week_end >= s["test_start"]) & (eia.week_end <= s["test_end"])].reset_index(drop=True)
    grid["index"] = grid.week_end.map(test.set_index("week_end")["index"])
    season = season_fit(eia, c)
    grid["season_pred"] = np.where(grid["index"].notna(), season(grid.week_end), np.nan)  # same weeks as the index
    rows = [metric_row("index_vs_eia_raw", grid["index"].to_numpy(), grid.eia_mbbl.to_numpy(), st, c, c["seed"]),
            metric_row(f"index_vs_eia_{win}wk_smoothed", grid["index"].to_numpy(), grid.eia_smooth.to_numpy(), st, c, c["seed"]),
            metric_row("season_only_vs_eia_raw", grid.season_pred.to_numpy(), grid.eia_mbbl.to_numpy(), st, c, c["seed"]),
            metric_row(f"season_only_vs_eia_{win}wk_smoothed", grid.season_pred.to_numpy(), grid.eia_smooth.to_numpy(), st, c, c["seed"])]
    ds, de = first_diff_pairs(grid["index"].to_numpy(), grid.eia_mbbl.to_numpy(), 0)
    rows.append(metric_row("index_vs_eia_first_difference_lag0", ds, de, st, c, c["seed"]))
    m = pd.DataFrame(rows)
    for col in ("pearson_p", "spearman_rho", "spearman_p", "ci_lo", "ci_hi"):
        if col not in m:
            m[col] = np.nan
    RES.mkdir(exist_ok=True)
    m.to_csv(RES / "h3_macro_metrics.csv", index=False)
    grid.to_csv(RES / "h3_macro_weekly.csv", index=False)
    sm = m[m.comparison == f"index_vs_eia_{win}wk_smoothed"].iloc[0]
    sea = m[m.comparison == f"season_only_vs_eia_{win}wk_smoothed"].iloc[0]
    crit = {"r_ok": bool(sm.pearson_r >= h3["target_pearson_r"]), "p_ok": bool(sm.pearson_p < h3["target_p_value"]),
            "ci_ok": bool(sm.ci_lo > 0), "beats_season": bool(sm.pearson_r > sea.pearson_r)}
    v = {"status": "PASS" if all(crit.values()) else "FAIL", **crit, "pearson_r": float(sm.pearson_r),
         "pearson_p": float(sm.pearson_p), "n_pairs": int(sm.n_pairs), "season_r": float(sea.pearson_r),
         "raw_r": float(m.iloc[0].pearson_r),
         "note": "naive p ignores autocorrelation, which smoothing makes worse; the bootstrap interval is also required"}
    (RES / "h3_verdict.json").write_text(json.dumps(v, indent=2), encoding="utf-8")
    print(json.dumps(v, indent=2))


if __name__ == "__main__":
    main()
