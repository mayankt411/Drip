"""Plumbing tests for the radar study on synthetic arrays; no result comes from here."""
import json

import numpy as np
import pandas as pd
import pytest
from affine import Affine
from pyproj import Transformer

from src.ml import evaluate_radar, radar, report_v4
from src.ml.common import cfg


def test_tank_features_see_a_bright_disc_and_skip_edges():
    tr = Transformer.from_crs("EPSG:4326", "EPSG:32614", always_xy=True)
    x, y = tr.transform(-96.77, 35.98)
    tf = Affine(10, 0, x - 500, 0, -10, y + 500)
    vv = np.full((100, 100), 0.05, np.float32)
    vh = np.full((100, 100), 0.01, np.float32)
    vv[48:53, 48:53] = 0.5
    tanks = pd.DataFrame({"longitude": [-96.77, -96.77], "latitude": [35.98, 35.98 + 0.0044], "diameter_m": [60.0, 60.0]})
    out = radar.tank_features(vv, vh, tf, "EPSG:32614", 10, tanks, radar.rc())
    assert out[0, 0] > out[0, 2] and out[0, 3] > 5  # disc well above rim in dB
    assert np.isnan(out[1]).all()  # second tank sits outside the window


def test_effective_start_needs_every_full_year():
    c = {"min_passes_per_year": 30}
    counts = pd.Series({"2018": 10, "2019": 50, "2020": 60, "2021": 70, "2022": 70, "2023": 70, "2024": 10})
    assert radar.effective_start(counts, c) == 2019
    assert radar.effective_start(pd.Series({"2022": 5, "2023": 70}), c) == 2023


def make_world(tmp_path, monkeypatch, signal, last="2024-06-28"):
    rng = np.random.default_rng(3)
    weeks = pd.date_range("2018-01-05", last, freq="7D")
    t = 2 * np.pi * weeks.dayofyear / 365.25
    eia = 40000 + 6000 * np.sin(t) + np.cumsum(rng.normal(0, 900, len(weeks)))
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    data = [{"period": w.strftime("%Y-%m-%d"), "series": cfg()["eia"]["series"], "value": float(v)} for w, v in zip(weeks, eia)]
    (raw / "eia_cushing_weekly_test.json").write_text(json.dumps({"response": {"data": data}}))
    n = 30
    tanks = pd.DataFrame({"tank_id": range(n), "diameter_m": rng.uniform(30, 80, n)})
    tanks["area_weight_m2"] = np.pi * (tanks.diameter_m / 2) ** 2
    (tmp_path / "tanks.csv").write_text(tanks.to_csv(index=False))
    feat = tmp_path / "radar" / "feat"
    feat.mkdir(parents=True)
    k = 0
    for d in pd.date_range("2018-01-02", last, freq="6D"):
        j = int(np.argmin(abs(weeks - d)))
        base = (eia[j] - 40000) / 6000 if signal else rng.normal()
        f = rng.normal(0, 0.3, (n, 4)) + base * np.array([1.0, 0.6, 0.8, 0.5])
        np.savez(feat / f"p{k}.npz", feats=f.astype(np.float32), date=d.strftime("%Y-%m-%d"),
                 orbit="ascending" if k % 2 == 0 else "descending", rel_orbit=14 if k % 2 == 0 else 63)
        k += 1
    c = cfg()
    c["stats"]["n_boot"] = 60
    monkeypatch.setattr(evaluate_radar, "ROOT", tmp_path)
    monkeypatch.setattr(evaluate_radar, "OUT", tmp_path / "radar")
    monkeypatch.setattr(evaluate_radar, "REGISTRY", tmp_path / "tanks.csv")
    monkeypatch.setattr(evaluate_radar, "RES", tmp_path / "results")
    monkeypatch.setattr(evaluate_radar, "cfg", lambda *a: c)


def test_strong_signal_passes_and_noise_does_not(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=True)
    evaluate_radar.main()
    v = json.loads((tmp_path / "results" / "h3_radar_verdict.json").read_text())
    assert v["pearson_r"] > 0.65 and v["r_ok"] and v["n_test_weeks"] > 40
    sub = tmp_path / "null"
    sub.mkdir()
    make_world(sub, monkeypatch, signal=False)
    evaluate_radar.main()
    v = json.loads((sub / "results" / "h3_radar_verdict.json").read_text())
    assert v["status"] == "FAIL"


def test_report_writes_paper(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=True)
    evaluate_radar.main()
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper" / "paper_v4_template.md").write_text(open("paper/paper_v4_template.md", encoding="utf-8").read(), encoding="utf-8")
    (tmp_path / "data" / "tanks").mkdir(parents=True)
    pd.read_csv(tmp_path / "tanks.csv").to_csv(tmp_path / "data" / "tanks" / "cushing_full_registry.csv", index=False)
    monkeypatch.setattr(report_v4, "ROOT", tmp_path)
    monkeypatch.setattr(report_v4, "RES", tmp_path / "results")
    monkeypatch.setattr(report_v4, "PAPER", tmp_path / "paper")
    report_v4.main()
    text = (tmp_path / "paper" / "paper_v4.md").read_text(encoding="utf-8")
    assert "{{" not in text and "Table 4" in text


def test_confirm_window_scores_later_weeks_with_same_model(tmp_path, monkeypatch):
    make_world(tmp_path, monkeypatch, signal=True, last="2026-06-26")
    evaluate_radar.main("test")
    evaluate_radar.main("confirm")
    a = json.loads((tmp_path / "results" / "h3_radar_verdict.json").read_text())
    b = json.loads((tmp_path / "results" / "h3_radar_confirm_verdict.json").read_text())
    assert a["n_test_weeks"] > 40 and b["n_test_weeks"] > 40 and b["r_ok"]
    w = pd.read_csv(tmp_path / "results" / "h3_radar_confirm_weekly.csv", parse_dates=["week_end"])
    assert w.week_end.min() >= pd.Timestamp("2024-07-01")
