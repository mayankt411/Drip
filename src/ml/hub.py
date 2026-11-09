"""Weekly hub series: valid-tank masks, CNN and baseline predictions for every date."""
import numpy as np
import pandas as pd
import torch

from .common import ROOT, cfg
from .eia import assign_weeks, load_eia
from .model import HubModel, geom_vec

BANK = ROOT / "data" / "processed" / "chipbank.npz"
REGISTRY = ROOT / "data" / "tanks" / "cushing_full_registry.csv"
CKPT_DIR = ROOT / "models" / "cnn"


def valid_mask(bank, c):
    n = c["cnn"]
    return (bank["cloud"] <= n["max_tank_cloud_fraction"]) & (bank["nodata"] == 0)


def date_table(bank, reg, c, tank_ok, min_fraction):
    """One row per date: coverage, EIA week, split and whether the date is usable."""
    w = reg.area_weight_m2.to_numpy()
    frac = (tank_ok * w).sum(1) / w.sum()
    dates = pd.to_datetime(bank["dates"], format="%Y%m%d")
    eia = load_eia(c)
    weeks = assign_weeks(dates, eia).to_numpy()
    s = c["splits"]
    split = np.where((dates >= s["train_start"]) & (dates <= s["train_end"]), "train",
                     np.where((dates >= s["test_start"]) & (dates <= s["test_end"]), "test", "outside"))
    df = pd.DataFrame({"date": dates, "week_end": weeks, "split": split, "valid_fraction": frac})
    df = df.merge(eia, on="week_end", how="left")
    df["usable"] = (df.valid_fraction >= min_fraction) & df.week_end.notna() & (df.split != "outside")
    df["usable"] &= df.eia_mbbl.notna()
    return df


def chips_for(bank, k, mask, device="cpu"):
    x = torch.tensor(bank["chips"][k][mask].astype(np.float32) / 10000.0, device=device)
    return x, geom_vec(*bank["sun"][k]).to(device)


def load_models(c, device="cpu"):
    models = []
    for p in sorted(CKPT_DIR.glob("seed_*.pt")):
        ck = torch.load(p, map_location=device, weights_only=False)
        m = HubModel(arch=ck["arch"], dropout=0.0).to(device)
        m.load_state_dict(ck["state"])
        m.eval()
        models.append((m, ck["y_mean"], ck["y_std"]))
    return models


@torch.no_grad()
def cnn_predict(models, bank, reg, tank_ok, dates_df, device="cpu"):
    w = torch.tensor(reg.area_weight_m2.to_numpy(), dtype=torch.float32, device=device)
    out = []
    for k, row in dates_df.iterrows():
        mask = tank_ok[k]
        if not row.usable or mask.sum() == 0:
            out.append((np.nan, np.nan))
            continue
        x, g = chips_for(bank, k, mask, device)
        ys, ms = [], []
        for m, ym, ys_ in models:
            y, fill = m(x, g, w[torch.tensor(mask, device=device)])
            ys.append(y.item() * ys_ + ym)
            ms.append(fill.item())
        out.append((float(np.mean(ys)), float(np.mean(ms))))
    return np.array(out)


def ridge_features(bank, tank_ok, reg, k):
    mask = tank_ok[k]
    w = reg.area_weight_m2.to_numpy()[mask]
    band = bank["disc_mean"][k][mask][:, [2, 3, 4]]
    return np.concatenate([(band * w[:, None]).sum(0) / w.sum(), [bank["sun"][k][0]]])


def fit_ridge(X, y, alphas, Xv, yv):
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z, Zv = (X - mu) / sd, (Xv - mu) / sd
    best = None
    for a in alphas:
        coef = np.linalg.solve(Z.T @ Z + a * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
        err = np.mean((Zv @ coef + y.mean() - yv) ** 2) if len(yv) else 0.0
        if best is None or err < best[0]:
            best = (err, a, coef)
    return lambda Xn: ((Xn - mu) / sd) @ best[2] + y.mean(), best[1]
