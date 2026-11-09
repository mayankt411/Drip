"""Correlation statistics with a stationary block bootstrap over a weekly grid."""
import numpy as np
from scipy import stats


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    if ok.sum() < 4 or np.std(x[ok]) == 0 or np.std(y[ok]) == 0:
        return np.nan, ok.sum()
    return float(np.corrcoef(x[ok], y[ok])[0, 1]), int(ok.sum())


def stationary_indices(n, mean_block, rng):
    """One stationary-bootstrap index draw of length n (Politis and Romano)."""
    new = rng.random(n) < 1.0 / mean_block
    new[0] = True
    pos = np.flatnonzero(new)
    block = np.cumsum(new) - 1
    starts = rng.integers(n, size=len(pos))
    return (starts[block] + (np.arange(n) - pos[block])) % n


def boot_corr(x, y, mean_block, n_boot, ci=0.95, seed=0):
    """Bootstrap CI for Pearson r. Indices are drawn on the full grid, so gaps stay gaps."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    rng = np.random.default_rng(seed)
    n = len(x)
    rs = []
    for _ in range(n_boot):
        i = stationary_indices(n, mean_block, rng)
        r, k = pearson(x[i], y[i])
        if not np.isnan(r):
            rs.append(r)
    rs = np.array(rs)
    a = (1 - ci) / 2
    return float(np.quantile(rs, a)), float(np.quantile(rs, 1 - a)), len(rs)


def level_metrics(pred, truth):
    pred, truth = np.asarray(pred, float), np.asarray(truth, float)
    ok = ~(np.isnan(pred) | np.isnan(truth))
    p, t = pred[ok], truth[ok]
    r, pr = stats.pearsonr(p, t)
    rho, prho = stats.spearmanr(p, t)
    ss = ((t - p) ** 2).sum()
    r2 = 1 - ss / ((t - t.mean()) ** 2).sum()
    return {"n": int(ok.sum()), "pearson_r": float(r), "pearson_p": float(pr),
            "spearman_rho": float(rho), "spearman_p": float(prho), "r2": float(r2),
            "rmse": float(np.sqrt(ss / ok.sum()))}


def first_diff_pairs(sat, eia, lag):
    """Delta S_t vs Delta E_{t+lag} on a weekly grid; sat has NaN for missing weeks.
    A difference exists only when both neighbouring weeks are observed."""
    sat, eia = np.asarray(sat, float), np.asarray(eia, float)
    ds = np.full(len(sat), np.nan)
    ds[1:] = sat[1:] - sat[:-1]
    de = np.full(len(eia), np.nan)
    de[1:] = eia[1:] - eia[:-1]
    if lag:
        ds, de = ds[:-lag], de[lag:]
    return ds, de
