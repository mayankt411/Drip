"""Plumbing tests for v4.3 on synthetic arrays; no result comes from here."""
import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from src.ml import evaluate_radar as ev
from src.ml import walkforward_radar as wf
from src.ml import walkforward_v43 as v43

from .test_radar import make_world


def test_exact_match_keeps_only_passes_within_a_day_of_a_friday():
    eia = pd.DataFrame({"week_end": pd.to_datetime(["2024-01-05", "2024-01-12"]), "eia_mbbl": [10.0, 20.0]})
    v = v43.exact_eia(pd.to_datetime(["2024-01-04", "2024-01-05", "2024-01-06", "2024-01-08", "2024-01-13"]), eia)
    assert list(v[:3]) == [10.0, 10.0, 10.0] and np.isnan(v[3]) and v[4] == 20.0


def test_wide_ridge_matches_the_normal_equation():
    rng = np.random.default_rng(0)
    Z, y = rng.normal(size=(30, 12)), rng.normal(size=30)
    a = 3.0
    direct = ev.ridge(Z, y, a)(Z[:5])
    assert np.allclose(v43.ridge_wide(Z, y, a)(Z[:5]), direct)


def test_fit_predict_finds_a_signal_and_ignores_missing_cells():
    rng = np.random.default_rng(1)
    y = rng.normal(size=120)
    X = rng.normal(size=(120, 40))
    X[:, 3] += 2 * y
    X[rng.random(X.shape) < 0.2] = np.nan
    p, alpha = v43.fit_predict(X[:90], y[:90], X[90:])
    assert np.corrcoef(p, y[90:])[0, 1] > 0.6 and alpha in v43.ALPHAS


def test_flagged_tanks_get_no_weight(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=True, last="2026-06-26")
    t = pd.read_csv(tmp_path / "tanks.csv")
    t["bare_ground"] = [1, 1, 1] + [0] * (len(t) - 3)
    t.to_csv(tmp_path / "tanks.csv", index=False)
    assert (wf.setup(ev.cfg(), ev.rc(), drop_bare=True)["w"][:3] == 0).all()
    assert (wf.setup(ev.cfg(), ev.rc())["w"][:3] > 0).all()


def test_run_writes_both_models_and_keeps_old_verdicts(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=True, last="2026-06-26")
    v43.main("run")
    for m in ("hub", "pertank"):
        v = json.loads((tmp_path / "results" / f"h3_radar_v43_{m}_verdict.json").read_text())
        assert v["v4_verdict_unchanged"] == "FAIL" and v["v4_1_verdict_unchanged"] == "PARTIAL" and v["model"] == m
        assert v["primary"]["r_ok"] and set(v["exact_date_ok"]) <= {"primary_2020_2022", "pooled_2020_2026"}
        M = pd.read_csv(tmp_path / "results" / f"h3_radar_v43_{m}_metrics.csv")
        assert {"diff_lag0_exact", "diff_lag1_exact", "diff_lag0_gap"} <= set(M.comparison)
    pt = json.loads((tmp_path / "results" / "h3_radar_v43_pertank_verdict.json").read_text())
    assert set(pt["vs_hub"]) == {"hub_status", "improved"}
    assert not (tmp_path / "results" / "h3_radar_wf_verdict.json").exists()


def test_noise_does_not_pass(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=False, last="2026-06-26")
    v43.main("run")
    assert json.loads((tmp_path / "results" / "h3_radar_v43_pertank_verdict.json").read_text())["status"] != "PASS"


def test_prospective_window_is_locked_until_may_2027(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=True)
    with pytest.raises(SystemExit):
        v43.main("prospective", today=date(2027, 4, 30))
