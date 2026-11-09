"""Unit tests on small synthetic arrays. They check code paths only; no result comes from here."""
import numpy as np
import pandas as pd
import pytest
import torch

from src.ml import cube, eia, registry, stats
from src.ml.chipbank import disc_mask, tank_chip
from src.ml.model import HubModel, geom_vec


def test_stationary_indices_range_and_length():
    rng = np.random.default_rng(1)
    i = stats.stationary_indices(50, 4, rng)
    assert len(i) == 50 and i.min() >= 0 and i.max() < 50


def test_boot_ci_brackets_strong_correlation():
    rng = np.random.default_rng(0)
    x = np.cumsum(rng.normal(size=60))
    y = x + rng.normal(scale=0.3, size=60)
    lo, hi, n = stats.boot_corr(x, y, 4, 300, seed=1)
    assert lo > 0.8 and hi <= 1.0 and n > 250


def test_first_diff_skips_gaps():
    sat = np.array([1.0, 2.0, np.nan, 4.0, 7.0])
    ds, de = stats.first_diff_pairs(sat, np.arange(5, dtype=float), 0)
    assert np.isnan(ds[2]) and np.isnan(ds[3]) and ds[1] == 1.0 and ds[4] == 3.0


def test_first_diff_lag_shifts_eia():
    sat = np.arange(6, dtype=float)
    eia_ = np.array([0, 1, 3, 6, 10, 15], float)
    ds, de = stats.first_diff_pairs(sat, eia_, 1)
    assert len(ds) == len(de) == 5 and de[1] == 2.0


def test_level_metrics_perfect():
    m = stats.level_metrics([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    assert m["r2"] == pytest.approx(1.0) and m["rmse"] == pytest.approx(0)


def test_week_assignment_window():
    e = pd.DataFrame({"week_end": pd.to_datetime(["2023-01-06", "2023-01-13"])})
    w = eia.assign_weeks(["2023-01-05", "2023-01-09"], e)
    assert w[0] == pd.Timestamp("2023-01-06")
    assert w[1] == pd.Timestamp("2023-01-06")  # 3 days away, still inside the window
    far = eia.assign_weeks(["2023-01-10"], e)
    assert far[0] == pd.Timestamp("2023-01-13")


def test_parse_diameter():
    assert registry.parse_diameter("45") == 45.0
    assert registry.parse_diameter("45,5 m") == 45.5
    assert registry.parse_diameter("big") is None and registry.parse_diameter(None) is None


def test_clusters_and_split_keep_terminals_whole():
    xy = np.array([[0, 0], [100, 0], [5000, 0], [5100, 0], [0, 5000], [100, 5000]], float)
    cl = registry.assign_clusters(xy, 1500)
    assert len(set(cl)) == 3
    df = pd.DataFrame({"tank_id": range(6), "x_utm": xy[:, 0], "y_utm": xy[:, 1], "cluster": cl})
    df["split"] = registry.split_clusters(df, 0.3)
    for _, g in df.groupby("cluster"):
        assert g.split.nunique() == 1
    assert (df.split == "heldout").any() and (df.split == "train").any()


def test_reflectance_scaling_and_nodata():
    dn = np.array([0, 1000, 5000, 20000], np.uint16)
    out = cube.to_reflectance_u16(dn, 0.0001, -0.1)
    assert out[0] == 0 and out[1] == 0 and out[2] == 4000 and out[3] == 10000


def test_mosaic_fills_gaps_only():
    a = (np.zeros((6, 2, 2), np.uint16), np.zeros((2, 2), np.uint8))
    b = (np.full((6, 2, 2), 7, np.uint16), np.full((2, 2), 4, np.uint8))
    a[0][2, 0, 0] = 5
    r, s = cube.mosaic([a, b])
    assert r[2, 0, 0] == 5 and r[2, 1, 1] == 7 and s[1, 1] == 4 and s[0, 0] == 0


def test_chip_bounds_and_disc():
    refl = np.random.default_rng(0).integers(0, 3000, (6, 40, 40)).astype(np.uint16)
    scl = np.zeros((40, 40), np.uint8)
    assert tank_chip(refl, scl, 20, 20, 16, [3])[0].shape == (6, 16, 16)
    assert tank_chip(refl, scl, 3, 3, 16, [3]) is None
    m = disc_mask(4, 16)
    assert m.sum() > 10 and not m[0, 0]


def test_hub_model_shapes_and_weights():
    torch.manual_seed(0)
    h = HubModel()
    chips = torch.rand(5, 6, 16, 16)
    w = torch.tensor([1.0, 2, 3, 4, 5])
    out, m = h(chips, geom_vec(33.7, 158.8), w)
    assert out.ndim == 0 and 0 < float(m.detach()) < 1
    out.backward()
    assert h.a_raw.grad is not None


def test_no_credentials_in_source():
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parents[2]
    pat = re.compile(r"(CDSE_PASSWORD|EIA_API_KEY)\s*[=:]\s*['\"][A-Za-z0-9!@#$%^&*._-]{12,}['\"]")
    for f in list((root / "src").rglob("*.py")) + list((root / "configs").rglob("*.yaml")):
        assert not pat.search(f.read_text()), f
