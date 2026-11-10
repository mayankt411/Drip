"""H2: floating-roof vs fixed-dome classification from multi-spectral chips.
Labels come only from OSM roof tags. The operational (active vs idle) split has no independent labels
and is reported as not testable; per-tank variance is saved as a descriptive index only."""
import json

import numpy as np
import pandas as pd
import torch
from torch import nn

from .common import ROOT, cfg, seed_all
from .framework import fw, load_inputs, tank_baseline
from .hub import fit_ridge

RES = ROOT / "results"
FLOAT = {"floating", "floating_roof", "external_floating", "internal_floating"}
FIXED = {"dome", "domed", "cone", "conical", "fixed", "fixed_roof"}  # 'flat' is ambiguous and left out


def structural_labels(reg, h2):
    fl = set(h2.get("float_tags", FLOAT))
    fx = set(h2.get("fixed_tags", FIXED))
    tag = reg.roof_shape.astype("string").str.lower().str.strip()
    y = np.full(len(reg), -1)
    y[tag.isin(fx).to_numpy()] = 0
    y[tag.isin(fl).to_numpy()] = 1
    return y


def mean_chips(bank, ok, dt, split):
    idx = dt.index[(dt.split == split) & dt.usable].to_numpy()
    ch = bank["chips"][idx].astype(np.float32) / 10000.0
    w = ok[idx][:, :, None, None, None]
    return (ch * w).sum(0) / np.maximum(w.sum(0), 1)


class Tiny(nn.Module):
    def __init__(self):
        super().__init__()
        self.f = nn.Sequential(nn.Conv2d(6, 16, 3, padding=1), nn.ReLU(), nn.Conv2d(16, 32, 3, padding=1), nn.ReLU())
        self.h = nn.Sequential(nn.Dropout(0.3), nn.Linear(64, 2))

    def forward(self, x):
        f = self.f(x)
        return self.h(torch.cat([f.mean((2, 3)), f.amax((2, 3))], 1))


def fit_cnn(xtr, ytr, xva, yva, seed, epochs=300, patience=40):
    seed_all(seed)
    m = Tiny()
    mu, sd = xtr.mean((0, 2, 3), keepdims=True), xtr.std((0, 2, 3), keepdims=True) + 1e-4
    nz = lambda a: torch.tensor((a - mu) / sd)
    xt, xv = nz(xtr), nz(xva)
    wts = torch.tensor(len(ytr) / (2 * np.maximum(np.bincount(ytr, minlength=2), 1)), dtype=torch.float32)
    lossf = nn.CrossEntropyLoss(weight=wts)
    opt = torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=5e-4)
    best, bad, state = 1e9, 0, None
    yt, yv = torch.tensor(ytr), torch.tensor(yva)
    for _ in range(epochs):
        m.train()
        opt.zero_grad()
        lossf(m(xt), yt).backward()
        opt.step()
        m.eval()
        with torch.no_grad():
            v = lossf(m(xv), yv).item()
        if v < best - 1e-5:
            best, bad, state = v, 0, {k: t.clone() for k, t in m.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    m.load_state_dict(state or m.state_dict())
    m.eval()
    return m, (mu, sd)


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


def main():
    c, f = cfg(), fw()
    h2 = f["hypotheses"]["h2_classification"]
    bank, reg, ok, dt = load_inputs(c)
    y = structural_labels(reg, h2)
    col = "split_h2" if "split_h2" in reg.columns else "split"  # spatial-block split when docs/h2_resplit.md was applied
    tr, te = (y >= 0) & (reg[col] == "train").to_numpy(), (y >= 0) & (reg[col] == "heldout").to_numpy()
    n = {"labelled": int((y >= 0).sum()), "train": [int((y[tr] == k).sum()) for k in (0, 1)],
         "heldout": [int((y[te] == k).sum()) for k in (0, 1)], "roof_tag_counts": reg.roof_shape.value_counts(dropna=False).to_dict()}
    RES.mkdir(exist_ok=True)
    mu, sd, cnt = tank_baseline(bank, ok, dt)
    pd.DataFrame({"tank_id": reg.tank_id, "mean_B04": mu[:, 0], "mean_B08": mu[:, 1], "mean_B11": mu[:, 2],
                  "std_B04": sd[:, 0], "std_B08": sd[:, 1], "std_B11": sd[:, 2], "n_dates": cnt}
                 ).to_csv(RES / "h2_tank_activity_index.csv", index=False)
    need_tr, need_te = h2.get("min_train_per_class", 20), h2.get("min_test_per_class", 5)
    rows = [{"task": "operational_active_vs_idle", "model": "none", "split": "none", "status": "NOT_TESTABLE",
             "reason": "no independent activity labels; a variance-defined label would be circular"}]
    if min(n["train"]) < need_tr or min(n["heldout"]) < need_te:
        rows.append({"task": "structural_floating_vs_fixed", "model": "none", "split": "none", "status": "NOT_TESTABLE",
                     "reason": f"too few OSM-labelled tanks per class (train {n['train']}, held-out {n['heldout']})"})
    else:
        xtr_all, xte = mean_chips(bank, ok, dt, "train"), mean_chips(bank, ok, dt, "test")
        rng = np.random.default_rng(c["seed"])
        idx = np.flatnonzero(tr)
        va = np.zeros(len(idx), bool)
        for k in (0, 1):
            sel = np.flatnonzero(y[idx] == k)
            va[rng.choice(sel, max(1, len(sel) // 5), replace=False)] = True
        fit_i, val_i = idx[~va], idx[va]
        te_i = np.flatnonzero(te)
        prob = np.zeros((len(te_i), 2))
        for seed in c["cnn"]["seeds"]:
            m, (mu_c, sd_c) = fit_cnn(xtr_all[fit_i], y[fit_i], xtr_all[val_i], y[val_i], seed)
            with torch.no_grad():
                prob += torch.softmax(m(torch.tensor((xte[te_i] - mu_c) / sd_c)), 1).numpy()
        pc = prob.argmax(1)
        feat = lambda ch: ch.mean((2, 3))
        a = feat(xtr_all)
        rg, _ = fit_ridge(a[fit_i], 2.0 * y[fit_i] - 1, [0.1, 1.0, 10.0], a[val_i], 2.0 * y[val_i] - 1)
        pr = (rg(feat(xte)[te_i]) > 0).astype(int)
        maj = np.full(len(te_i), np.bincount(y[fit_i]).argmax())
        for name, p in (("cnn", pc), ("ridge_band_means", pr), ("majority", maj)):
            rows.append({"task": "structural_floating_vs_fixed", "model": name, "split": "heldout_spatial_blocks_2023_2024" if col == "split_h2" else "heldout_terminals_2023_2024",
                         "status": "SCORED", "n_test": len(te_i), **scores(y[te_i], p)})
    pd.DataFrame(rows).to_csv(RES / "h2_classification_metrics.csv", index=False)
    sc = {r["model"]: r for r in rows if r.get("status") == "SCORED"}
    if "cnn" in sc:  # targets from the framework; the CNN must also beat the majority guess on macro F1
        t = h2.get("target_accuracy", 0.85), h2.get("target_f1", 0.80)
        v = {"split": col, "accuracy_ok": bool(sc["cnn"]["accuracy"] >= t[0]), "f1_ok": bool(sc["cnn"]["macro_f1"] >= t[1]),
             "beats_majority": bool(sc["cnn"]["macro_f1"] > sc["majority"]["macro_f1"]),
             "beats_ridge": bool(sc["cnn"]["macro_f1"] > sc["ridge_band_means"]["macro_f1"])}
        v["status"] = "PASS" if v["accuracy_ok"] and v["f1_ok"] and v["beats_majority"] else "FAIL"
        (RES / "h2_verdict.json").write_text(json.dumps(v, indent=2), encoding="utf-8")
    (RES / "h2_label_counts.json").write_text(json.dumps(n, indent=2, default=str), encoding="utf-8")
    print(json.dumps(n, indent=2, default=str))
    print(pd.DataFrame(rows)[["task", "model", "status"]].to_string(index=False))


if __name__ == "__main__":
    main()
