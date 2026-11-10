"""Small pieces shared by the two H2 runs (Sentinel-2 chips and Sentinel-1 radar)."""
import numpy as np

FLOAT, FIXED = "floating_roof", "dome"  # the tags src.ml.roofs writes into the registry


def labels(reg):
    """1 floating, 0 fixed, -1 unlabelled."""
    y = np.full(len(reg), -1, dtype=np.int64)
    y[(reg.roof_shape == FIXED).to_numpy()] = 0
    y[(reg.roof_shape == FLOAT).to_numpy()] = 1
    return y


def size_rule(d_tr, y_tr, d_te):
    """The diameter-only baseline: the best single cut-off on training tanks, either direction."""
    best = (-1.0, 0.0, 1)
    for t in np.unique(d_tr):
        for s in (1, -1):
            a = (((d_tr * s) > (t * s)).astype(int) == y_tr).mean()  # bigger means floating when s is 1
            if a > best[0]:
                best = (a, t, s)
    return (((d_te * best[2]) > (best[1] * best[2])).astype(int))


def scores(y, p):
    acc = float((y == p).mean())
    f1s, rec = [], []
    for k in (0, 1):
        tp = ((p == k) & (y == k)).sum()
        pr = tp / max((p == k).sum(), 1)
        rc = tp / max((y == k).sum(), 1)
        f1s.append(0.0 if pr + rc == 0 else 2 * pr * rc / (pr + rc))
        rec.append(rc)
    cm = np.array([[((y == a) & (p == b)).sum() for b in (0, 1)] for a in (0, 1)])
    return {"accuracy": acc, "balanced_accuracy": float(np.mean(rec)), "macro_f1": float(np.mean(f1s)),
            "cm_fixed_fixed": int(cm[0, 0]), "cm_fixed_float": int(cm[0, 1]),
            "cm_float_fixed": int(cm[1, 0]), "cm_float_float": int(cm[1, 1])}
