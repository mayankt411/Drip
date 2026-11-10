"""Framework v3 settings and the shared per-tank activity table."""
import numpy as np
import pandas as pd

from .common import cfg
from .hub import BANK, REGISTRY, date_table, valid_mask

BANDS = [2, 3, 4]  # B04, B08, B11 in the chip bank order


def fw():
    return cfg("configs/framework_v3.yaml")


def load_inputs(c=None):
    c = c or cfg()
    bank = dict(np.load(BANK, allow_pickle=True))
    reg = pd.read_csv(REGISTRY)
    ok = valid_mask(bank, c)
    dt = date_table(bank, reg, c, ok, c["cnn"]["min_valid_fraction"])
    return bank, reg, ok, dt


def tank_baseline(bank, ok, dt):
    """Per-tank mean reflectance over the development-year dates only."""
    idx = dt.index[(dt.split == "train") & dt.usable].to_numpy()
    x = bank["disc_mean"][idx][:, :, BANDS]
    m = ok[idx][:, :, None]
    cnt = m.sum(0)
    mu = np.where(cnt > 0, (x * m).sum(0) / np.maximum(cnt, 1), np.nan)
    sd = np.sqrt(np.where(cnt > 1, (((x - mu) ** 2) * m).sum(0) / np.maximum(cnt - 1, 1), np.nan))
    return mu, sd, cnt[:, 0]


def activity_matrix(bank, ok, mu):
    """Relative departure of each tank from its own development-year mean, per date."""
    x = bank["disc_mean"][:, :, BANDS]
    dev = np.abs(x - mu[None]) / np.maximum(mu[None], 1e-3)
    out = dev.mean(2)
    out[~ok] = np.nan
    return out
