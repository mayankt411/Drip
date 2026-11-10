"""Plumbing tests for the v4.1 walk-forward test on synthetic arrays; no result comes from here."""
import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from src.ml import evaluate_radar as ev
from src.ml import walkforward_radar as wf

from .test_radar import make_world


def ctx_for(tmp_path, monkeypatch, signal=True, last="2026-06-26"):
    make_world(tmp_path, monkeypatch, signal=signal, last=last)
    return wf.setup(ev.cfg(), ev.rc())


def test_interpolation_and_gap_rule():
    eia = pd.DataFrame({"week_end": pd.to_datetime(["2024-01-05", "2024-01-12", "2024-01-26"]), "eia_mbbl": [10.0, 20.0, 40.0]})
    v = wf.interp_eia(pd.to_datetime(["2024-01-05", "2024-01-08", "2024-01-19", "2023-12-31", "2024-01-27"]), eia)
    assert v[0] == 10 and v[1] == pytest.approx(10 + 10 * 3 / 7) and np.isnan(v[2]) and np.isnan(v[3]) and np.isnan(v[4])
    days = pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15", "2024-02-10", "2024-02-17"])
    p = pd.DataFrame({"date": days, "radar_all": [0.0, 1.0, 3.0, 10.0, 12.0], "eia_interp": [0.0, 2.0, 6.0, 20.0, 24.0]})
    (x0, y0), (x1, y1) = wf.gap_pairs(p)
    assert list(x0) == [1.0, 2.0, 2.0] and list(y0) == [2.0, 4.0, 4.0]  # the 26-day jump is skipped
    assert list(x1) == [1.0] and list(y1) == [4.0]  # radar change 0-7 vs EIA change 7-14


def test_fold_needs_forty_training_weeks(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path, monkeypatch)
    assert wf.fold("2018", ctx, "2017-12-31", "2018-01-01", "2018-12-31")["scored"] is False
    assert wf.fold("2020", ctx, "2019-12-31", "2020-01-01", "2020-12-31")["scored"] is True


def test_frozen_fold_matches_v4_weekly_predictions(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path, monkeypatch)
    ev.main("test")
    v4 = pd.read_csv(tmp_path / "results" / "h3_radar_weekly.csv", parse_dates=["week_end"]).dropna(subset=["radar_all"])
    r = ctx["r"]
    f = wf.fold("v4_window1", ctx, r["train_end"], r["test_start"], r["test_end"])["weekly"]
    m = v4.merge(f, on="week_end", suffixes=("_v4", "_wf"))
    assert len(m) == len(v4) == len(f)
    for col in ["radar_all", "radar_large_tanks", "radar_plus_season", "season_only", "train_mean"]:
        assert np.allclose(m[f"{col}_v4"], m[f"{col}_wf"])


def test_fold_never_sees_its_own_or_later_eia(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path, monkeypatch)
    a = wf.fold("2022", ctx, "2021-12-31", "2022-01-01", "2022-12-31")
    moved = dict(ctx, eia=ctx["eia"].assign(eia_mbbl=np.where(ctx["eia"].week_end >= "2022-01-01", ctx["eia"].eia_mbbl + 1e5, ctx["eia"].eia_mbbl)))
    b = wf.fold("2022", moved, "2021-12-31", "2022-01-01", "2022-12-31")
    for col in ["radar_all", "season_only", "train_mean"]:
        assert np.allclose(a["weekly"][col], b["weekly"][col])
    assert np.allclose(a["passes"].radar_all, b["passes"].radar_all)


def test_run_writes_files_and_keeps_v4_fail(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=True, last="2026-06-26")
    wf.main("run")
    v = json.loads((tmp_path / "results" / "h3_radar_wf_verdict.json").read_text())
    assert v["v4_verdict_unchanged"] == "FAIL" and v["status"] in {"PASS", "PARTIAL", "FAIL"}
    assert v["primary"]["r_ok"] and v["primary"]["positive"]
    m = pd.read_csv(tmp_path / "results" / "h3_radar_wf_metrics.csv")
    assert {"primary_2020_2022", "pooled_2020_2026", "v4_window1", "v4_window2", "2024"} <= set(m.scope)
    assert (m[m.scope == "primary_2020_2022"].comparison == "placebo").any()


def test_noise_does_not_pass(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=False, last="2026-06-26")
    wf.main("run")
    v = json.loads((tmp_path / "results" / "h3_radar_wf_verdict.json").read_text())
    assert v["status"] != "PASS"


def test_prospective_window_is_locked_until_may_2027(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=True)
    with pytest.raises(SystemExit):
        wf.main("prospective", today=date(2027, 4, 30))


def test_float_mode_drops_fixed_and_unsure_tanks(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=True, last="2026-06-26")
    t = pd.read_csv(tmp_path / "tanks.csv")
    t["roof_shape"] = ["floating_roof"] * 12 + ["dome"] * 12 + [np.nan] * 6
    t.to_csv(tmp_path / "tanks.csv", index=False)
    allw = wf.setup(ev.cfg(), ev.rc())["w"]
    fw = wf.setup(ev.cfg(), ev.rc(), only_floating=True)["w"]
    assert (fw[:12] == allw[:12]).all() and (fw[12:] == 0).all()
    wf.main("run_float")
    v = json.loads((tmp_path / "results" / "h3_radar_wf_float_verdict.json").read_text())
    assert v["variant"] == "floating_roof_tanks_only" and v["v4_verdict_unchanged"] == "FAIL"
    assert not (tmp_path / "results" / "h3_radar_wf_verdict.json").exists()


def test_float_prospective_is_still_locked(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=True)
    with pytest.raises(SystemExit):
        wf.main("prospective_float", today=date(2027, 4, 30))
