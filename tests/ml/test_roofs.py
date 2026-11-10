"""Plumbing tests for the roof labelling helper, on synthetic crops."""
import numpy as np
import pandas as pd
from PIL import Image

from src.ml import roofs


def world(tmp_path, monkeypatch, n=40):
    reg = pd.DataFrame({"tank_id": [f"T{i}" for i in range(n)], "latitude": 35.95, "longitude": -96.75, "diameter_m": 50.0,
                        "roof_shape": np.nan, "split": ["train"] * (n // 2) + ["heldout"] * (n - n // 2)})
    (tmp_path / "reg.csv").write_text(reg.to_csv(index=False))
    monkeypatch.setattr(roofs, "REG", tmp_path / "reg.csv")
    monkeypatch.setattr(roofs, "OUT", tmp_path / "roofs")
    (tmp_path / "roofs" / "crops").mkdir(parents=True)
    for t in reg.tank_id[:-3]:  # last three crops missing on purpose
        Image.new("RGB", (256, 256), (120, 130, 110)).save(tmp_path / "roofs" / "crops" / f"{t}.jpg")
    return reg


def test_sheets_cover_every_tank_even_with_missing_crops(tmp_path, monkeypatch):
    world(tmp_path, monkeypatch)
    roofs.sheets()
    assert len(list((tmp_path / "roofs" / "sheets").glob("*.png"))) == 2
    assert Image.open(tmp_path / "roofs" / "sheets" / "sheet_01.png").size == (6 * 256, 5 * 256)


def test_apply_writes_known_tags_and_keeps_a_backup(tmp_path, monkeypatch, capsys):
    world(tmp_path, monkeypatch)
    lab = ["floating"] * 20 + ["fixed"] * 15 + ["unsure"] * 5
    pd.DataFrame({"idx": range(1, 41), "tank_id": [f"T{i}" for i in range(40)], "label": lab}).to_csv(tmp_path / "roofs" / "labels.csv", index=False)
    roofs.apply()
    r = pd.read_csv(tmp_path / "reg.csv")
    assert set(r.roof_shape.dropna()) == {"floating_roof", "dome"} and r.roof_shape.isna().sum() == 5
    assert (tmp_path / "reg.before_roofs.csv").exists()
    assert "H2 gate" in capsys.readouterr().out


def test_check_reports_agreement(tmp_path, monkeypatch, capsys):
    world(tmp_path, monkeypatch)
    lab = ["floating", "fixed"] * 20
    pd.DataFrame({"idx": range(1, 41), "tank_id": "x", "label": lab}).to_csv(tmp_path / "roofs" / "labels.csv", index=False)
    roofs.audit(n=10)
    key = pd.read_csv(tmp_path / "roofs" / "audit_key.csv")
    truth = "".join("f" if lab[i - 1] == "floating" else "x" for i in key.idx)
    roofs.check(truth)
    assert "agreement 100%" in capsys.readouterr().out
    roofs.check(("x" if truth[0] == "f" else "f") + truth[1:])
    assert "agreement 90%" in capsys.readouterr().out
