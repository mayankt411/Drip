"""Train the hub-level CNN on 2021-2022 weeks only. EIA is the only target; no tank labels exist."""
import json

import numpy as np
import torch

from .common import ROOT, cfg, log_manifest, seed_all, sha256
from .hub import BANK, CKPT_DIR, REGISTRY, chips_for, date_table, valid_mask
from .model import HubModel
import pandas as pd


def split_fit_val(dates_df, share):
    """Chronological split of the usable training dates into fit and inner-validation."""
    idx = dates_df.index[(dates_df.split == "train") & dates_df.usable].tolist()
    cut = int(round(len(idx) * (1 - share)))
    wk = dates_df.week_end
    while 0 < cut < len(idx) and wk[idx[cut]] == wk[idx[cut - 1]]:
        cut += 1  # keep one EIA week on a single side of the cut
    return idx[:cut], idx[cut:]


def band_stats(bank, tank_ok, idx):
    px = np.concatenate([bank["chips"][k][tank_ok[k]].transpose(1, 0, 2, 3).reshape(6, -1) for k in idx], axis=1)
    px = px.astype(np.float64) / 10000.0
    return px.mean(1), px.std(1)


def train_seed(seed, bank, reg, tank_ok, dates_df, fit, val, c, device):
    n = c["cnn"]
    if len(val) < 5 or len(fit) < 10:
        raise SystemExit(f"too few usable training dates (fit {len(fit)}, val {len(val)}); check the cubes and cloud filters")
    seed_all(seed)
    ymu, ysd = dates_df.loc[fit, "eia_mbbl"].mean(), dates_df.loc[fit, "eia_mbbl"].std()
    z = ((dates_df.eia_mbbl - ymu) / ysd).to_numpy()
    model = HubModel(arch=n["arch"], dropout=n["dropout"]).to(device)
    model.net.set_norm(*band_stats(bank, tank_ok, fit))
    opt = torch.optim.AdamW(model.parameters(), lr=n["lr"], weight_decay=n["weight_decay"])
    w_all = torch.tensor(reg.area_weight_m2.to_numpy(), dtype=torch.float32, device=device)

    def loss_on(ks, train):
        model.train(train)
        tot = 0.0
        for k in ks:
            m = torch.tensor(tank_ok[k], device=device)
            x, g = chips_for(bank, k, tank_ok[k], device)
            y, _ = model(x, g, w_all[m])
            loss = (y - float(z[k])) ** 2
            if train:
                (loss / len(ks)).backward()
            tot += loss.item()
        return tot / len(ks)

    best, bad, state = np.inf, 0, None
    log = []
    for epoch in range(n["epochs"]):
        order = list(np.random.permutation(fit))
        for i in range(0, len(order), 8):
            opt.zero_grad()
            loss_on(order[i:i + 8], True)
            opt.step()
        with torch.no_grad():
            tr, va = loss_on(fit, False), loss_on(val, False)
        log.append({"seed": seed, "epoch": epoch, "train_mse_z": tr, "val_mse_z": va})
        if va < best - 1e-6:
            best, bad, state = va, 0, {k: v.clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= n["patience"]:
                break
    if state is None:
        state = {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(state)
    return model, ymu, ysd, log, best


def main():
    c = cfg()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    bank = dict(np.load(BANK, allow_pickle=True))
    reg = pd.read_csv(REGISTRY)
    tank_ok = valid_mask(bank, c)
    dates_df = date_table(bank, reg, c, tank_ok, c["cnn"]["min_valid_fraction"])
    fit, val = split_fit_val(dates_df, c["splits"]["val_share_weeks"])
    assert dates_df.loc[fit + val, "split"].eq("train").all(), "test dates leaked into training"
    CKPT_DIR.mkdir(parents=True, exist_ok=True)
    logs, summary = [], {"n_fit_dates": len(fit), "n_val_dates": len(val), "device": device}
    for seed in c["cnn"]["seeds"]:
        model, ymu, ysd, log, best = train_seed(seed, bank, reg, tank_ok, dates_df, fit, val, c, device)
        path = CKPT_DIR / f"seed_{seed}.pt"
        torch.save({"state": model.state_dict(), "arch": c["cnn"]["arch"], "y_mean": float(ymu),
                    "y_std": float(ysd), "seed": seed, "best_val_mse_z": float(best)}, path)
        log_manifest("local:train_cnn", f"seed={seed};arch={c['cnn']['arch']}", path.name, "NA", sha256(path), "SUCCESS")
        logs += log
        summary[f"seed_{seed}_best_val_mse_z"] = float(best)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    pd.DataFrame(logs).to_csv(out / "ml_cnn_training_log.csv", index=False)
    (out / "ml_cnn_training_summary.json").write_text(json.dumps(summary, indent=2))
    print(summary)


if __name__ == "__main__":
    main()
