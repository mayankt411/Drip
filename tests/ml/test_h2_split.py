"""Plumbing tests for the H2 re-split on synthetic tanks."""
import numpy as np
import pandas as pd

from src.ml import h2_split


def tanks(n=300, seed=1):
    r = np.random.default_rng(seed)
    return pd.DataFrame({"x_utm": r.uniform(0, 6000, n), "y_utm": r.uniform(0, 6000, n)}), r.random(n) < 0.15


def test_blocks_stay_whole_and_fixed_roofs_are_shared():
    reg, fixed = tanks()
    s = h2_split.assign(reg, fixed, seed=7)
    key = (reg.x_utm // 1000).astype(int).astype(str) + "_" + (reg.y_utm // 1000).astype(int).astype(str)
    assert (pd.DataFrame({"k": key, "s": s}).groupby("k").s.nunique() == 1).all()
    n = pd.crosstab(s, fixed)
    assert n.loc["train", True] >= 0.3 * fixed.sum() and n.loc["heldout", True] >= 0.3 * fixed.sum()


def test_same_seed_gives_same_split_and_other_seed_differs():
    reg, fixed = tanks()
    a, b, c = (h2_split.assign(reg, fixed, seed=k) for k in (7, 7, 8))
    assert (a == b).all() and not (a == c).all()
