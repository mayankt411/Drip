"""Plumbing tests for framework v3 on synthetic arrays; no result comes from here."""
import json

import numpy as np
import pandas as pd
import pytest

from src.ml import evaluate_macro, framework, report_v3, train_classifier
from src.ml.common import cfg
from src.ml.hub import date_table, valid_mask


def synth(n=60, seed=0):
    rng = np.random.default_rng(seed)
    c = cfg()
    days = pd.date_range("2021-01-08", "2024-06-28", freq="7D")
    d = len(days)
    chips = rng.integers(500, 3000, (d, n, 6, 16, 16)).astype(np.uint16)
    bank = {"chips": chips, "cloud": np.zeros((d, n), np.float32), "nodata": np.zeros((d, n), np.float32),
            "disc_mean": rng.uniform(0.05, 0.3, (d, n, 6)).astype(np.float32),
            "dates": np.array([x.strftime("%Y%m%d") for x in days]), "sun": np.c_[np.full(d, 40.0), np.full(d, 150.0)].astype(np.float32)}
    tag = np.array(["dome"] * 25 + ["floating"] * 25 + [None] * (n - 50), dtype=object)
    reg = pd.DataFrame({"tank_id": range(n), "area_weight_m2": rng.uniform(1000, 9000, n), "roof_shape": tag,
                        "split": ["train"] * 40 + ["heldout"] * (n - 40)})
    ok = valid_mask(bank, c)
    dt = date_table(bank, reg, c, ok, 0.5)
    return c, bank, reg, ok, dt


def test_structural_labels_leave_ambiguous_out():
    reg = pd.DataFrame({"roof_shape": ["dome", "floating", "flat", None, "Cone"]})
    assert list(train_classifier.structural_labels(reg, {})) == [0, 1, -1, -1, 0]


def test_scores_perfect_and_confusion():
    s = train_classifier.scores(np.array([0, 0, 1, 1]), np.array([0, 0, 1, 1]))
    assert s["accuracy"] == 1 and s["macro_f1"] == 1 and s["cm_float_float"] == 2


def test_macro_and_report_run_end_to_end(tmp_path, monkeypatch):
    c, bank, reg, ok, dt = synth()
    c["stats"]["n_boot"] = 40
    inputs = lambda c_=None: (bank, reg, ok, dt)
    for mod in (evaluate_macro, train_classifier, framework):
        monkeypatch.setattr(mod, "load_inputs", inputs, raising=False)
    monkeypatch.setattr(evaluate_macro, "cfg", lambda *a: c)
    monkeypatch.setattr(train_classifier, "cfg", lambda *a: c)
    res = tmp_path / "results"
    paper = tmp_path / "paper"
    (paper / "figures").mkdir(parents=True)
    (paper / "tables").mkdir()
    for mod in (evaluate_macro, train_classifier, report_v3):
        monkeypatch.setattr(mod, "RES", res)
    monkeypatch.setattr(report_v3, "PAPER", paper)
    res.mkdir()
    (paper / "paper_v3_template.md").write_text(open("paper/paper_v3_template.md", encoding="utf-8").read(), encoding="utf-8")
    evaluate_macro.main()
    v = json.loads((res / "h3_verdict.json").read_text())
    assert v["status"] in ("PASS", "FAIL") and "season_r" in v
    train_classifier.main()
    h2 = pd.read_csv(res / "h2_classification_metrics.csv")
    assert (h2.task == "operational_active_vs_idle").any() and (h2.status == "NOT_TESTABLE").any()
    pd.DataFrame([{"split": "t", "precision": .9, "recall": .9, "precision_maxf1": .9, "recall_maxf1": .9, "map50": .91,
                   "map50_95": .5, "n_images": 10, "n_labels": 100}]).to_csv(res / "ml_yolo_metrics.csv", index=False)
    report_v3.main()
    text = (paper / "paper_v3.md").read_text(encoding="utf-8")
    assert "{{" not in text and "not yet run" not in text and (paper / "figures" / "macro_utilization.svg").exists()


def test_too_few_labels_is_reported_not_forced(tmp_path, monkeypatch):
    c, bank, reg, ok, dt = synth()
    reg["roof_shape"] = None
    monkeypatch.setattr(train_classifier, "load_inputs", lambda c_=None: (bank, reg, ok, dt))
    monkeypatch.setattr(train_classifier, "RES", tmp_path)
    monkeypatch.setattr(train_classifier, "cfg", lambda *a: c)
    train_classifier.main()
    h2 = pd.read_csv(tmp_path / "h2_classification_metrics.csv")
    assert (h2.status == "NOT_TESTABLE").all()
