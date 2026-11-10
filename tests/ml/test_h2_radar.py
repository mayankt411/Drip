"""Plumbing tests for the radar roof-type test on synthetic arrays; no result comes from here."""
import json

import numpy as np
import pandas as pd

from src.ml import h2_radar as h


def world(n=120, seed=0, signal=True):
    rng = np.random.default_rng(seed)
    y = np.tile([0, 1], n // 2)  # 1 floating, 0 fixed
    P = 80
    base = rng.normal(0, 1, (P, 1, 1)) * (1 + (y == 1) * 1.5 * signal)[None, :, None]  # floating roofs move with the level
    F = base + rng.normal(0, 0.2, (P, n, 4)) + (y == 1)[None, :, None] * 0.5 * signal
    meta = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=P, freq="6D").strftime("%Y-%m-%d"), "key": ["a"] * P})
    reg = pd.DataFrame({"diameter_m": rng.uniform(20, 40, n), "roof_shape": np.where(y == 1, "floating_roof", "dome"),
                        "split_h2": np.where(np.arange(n) % 3 == 0, "heldout", "train")})
    return reg, meta, F, y


def test_features_are_mean_and_std_and_gate_on_pass_count():
    reg, meta, F, y = world()
    F[:, 0, :] = np.nan
    X, valid = h.tank_features(meta, F)
    assert X.shape == (len(reg), 8) and not valid[0] and valid[1:].all()
    assert np.allclose(X[1, :4], np.nanmean(F[:, 1], 0))


def test_signal_is_found_and_noise_is_not():
    reg, meta, F, y = world(signal=True)
    X, valid = h.tank_features(meta, F)
    rows, n = h.run_band(reg, X, valid, y, 40.0, 1)
    assert h.verdict(rows)["accuracy_ok"]
    reg, meta, F, y = world(signal=False, seed=2)
    X, valid = h.tank_features(meta, F)
    rows, _ = h.run_band(reg, X, valid, y, 40.0, 1)
    assert h.verdict(rows)["status"] != "PASS"


def test_too_few_tanks_is_not_testable():
    reg, meta, F, y = world(n=30)
    X, valid = h.tank_features(meta, F)
    rows, _ = h.run_band(reg, X, valid, y, 40.0, 1)
    assert rows[0]["status"] == "NOT_TESTABLE" and h.verdict(rows)["status"] == "NOT_TESTABLE"


def test_main_writes_files(tmp_path, monkeypatch):
    reg, meta, F, y = world()
    reg.to_csv(tmp_path / "reg.csv", index=False)
    monkeypatch.setattr(h, "REG", tmp_path / "reg.csv")
    monkeypatch.setattr(h, "RES", tmp_path / "results")
    monkeypatch.setattr(h.ev, "load_passes", lambda: (meta, F))
    h.main()
    v = json.loads((tmp_path / "results" / "h2_radar_verdict.json").read_text())
    assert v["primary"] == "size_controlled" and "all_tanks" in v["verdict"]
    assert (tmp_path / "results" / "h2_radar_metrics.csv").exists()
