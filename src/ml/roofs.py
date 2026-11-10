"""Roof-type labelling helper for H2.
Pulls one small aerial crop per tank, builds numbered contact sheets to read, and writes the labels into the
registry's roof_shape column. Crops are for labelling only: do not commit or redistribute them.
Imagery: Esri World Imagery (Esri, Maxar, Earthstar Geographics); keep that credit in anything that shows it.
Classes: 'floating' = open floating roof seen from above; 'fixed' = closed roof (dome or cone).
An internal floating roof sits under a fixed roof, so it will read as 'fixed'. Say so in the paper."""
import sys
import time

import numpy as np
import pandas as pd
import requests
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer

from .common import ROOT

REG = ROOT / "data" / "tanks" / "cushing_full_registry.csv"
OUT = ROOT / "data" / "roofs"
URL = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
TILE, COLS, ROWS = 256, 6, 5
TAG = {"floating": "floating_roof", "fixed": "dome"}  # values train_classifier.py already recognises
TO = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


def side_m(diam):
    return max(1.8 * diam, 70.0)


def fetch():
    reg = pd.read_csv(REG)
    (OUT / "crops").mkdir(parents=True, exist_ok=True)
    for _, t in reg.iterrows():
        f = OUT / "crops" / f"{t.tank_id}.jpg"
        if f.exists():
            continue
        x, y = TO.transform(t.longitude, t.latitude)
        h = side_m(t.diameter_m) / np.cos(np.radians(t.latitude)) / 2  # web mercator stretches ground distance
        p = {"bbox": f"{x - h},{y - h},{x + h},{y + h}", "bboxSR": 3857, "imageSR": 3857, "size": f"{TILE},{TILE}", "format": "jpg", "f": "image"}
        for _ in range(3):
            try:
                r = requests.get(URL, params=p, timeout=30)
                if r.ok and r.headers.get("content-type", "").startswith("image"):
                    f.write_bytes(r.content)
                    break
            except requests.RequestException:
                pass
            time.sleep(2)
        else:
            print("failed", t.tank_id)
        time.sleep(0.15)
    print(len(list((OUT / "crops").glob("*.jpg"))), "of", len(reg), "crops on disk")


def tile(t, num, font):
    f = OUT / "crops" / f"{t.tank_id}.jpg"
    im = Image.open(f).convert("RGB").resize((TILE, TILE)) if f.exists() else Image.new("RGB", (TILE, TILE), (70, 70, 70))
    d = ImageDraw.Draw(im)
    r = t.diameter_m / side_m(t.diameter_m) * TILE / 2  # ticks just outside the tank so the roof stays clear
    c = TILE / 2
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        d.line([c + dx * (r + 3), c + dy * (r + 3), c + dx * (r + 12), c + dy * (r + 12)], fill=(255, 255, 0), width=2)
    d.rectangle([0, 0, 44, 24], fill=(0, 0, 0))
    d.text((4, 2), str(num), fill=(255, 255, 255), font=font)
    return im


def font():
    try:
        return ImageFont.truetype("arial.ttf", 18)
    except OSError:
        return ImageFont.load_default()


def sheet(rows, path, numbers):
    fn = font()
    im = Image.new("RGB", (COLS * TILE, ROWS * TILE), (0, 0, 0))
    for k, ((_, t), n) in enumerate(zip(rows.iterrows(), numbers)):
        im.paste(tile(t, n, fn), ((k % COLS) * TILE, (k // COLS) * TILE))
    im.save(path)


def sheets():
    reg = pd.read_csv(REG)
    (OUT / "sheets").mkdir(parents=True, exist_ok=True)
    per = COLS * ROWS
    for s in range(0, len(reg), per):
        sheet(reg.iloc[s:s + per], OUT / "sheets" / f"sheet_{s // per + 1:02d}.png", range(s + 1, min(s + per, len(reg)) + 1))
    print("sheets in", OUT / "sheets", "- tile numbers are registry rows, 1-based")


def audit(n=30, seed=7):
    """A random sample for you to label blind, to measure agreement with the labels file."""
    reg = pd.read_csv(REG)
    pick = np.sort(np.random.default_rng(seed).choice(len(reg), n, replace=False))
    sheet(reg.iloc[pick], OUT / "audit.png", range(1, n + 1))
    pd.DataFrame({"pos": range(1, n + 1), "idx": pick + 1}).to_csv(OUT / "audit_key.csv", index=False)
    print("label tiles 1 to", n, "in", OUT / "audit.png", "as a string of f (floating), x (fixed), u (unsure)")


def check(mine):
    key = pd.read_csv(OUT / "audit_key.csv")
    lab = pd.read_csv(OUT / "labels.csv").set_index("idx").label
    mine = pd.Series(list(mine.lower()), index=key.pos)
    assert len(mine) == len(key), f"expected {len(key)} letters"
    ref = key.set_index("pos").idx.map(lab).map({"floating": "f", "fixed": "x"})
    ok = ref.notna() & mine.isin(["f", "x"])
    a, b = ref[ok], mine[ok]
    agree = (a == b).mean()
    pe = sum(((a == k).mean() * (b == k).mean()) for k in "fx")
    print(f"compared {int(ok.sum())} tiles: agreement {agree:.0%}, kappa {(agree - pe) / (1 - pe):.2f}")
    print("disagreements at idx:", list(key.set_index("pos").idx[ok & (ref != mine)]))


def apply():
    reg = pd.read_csv(REG)
    lab = pd.read_csv(OUT / "labels.csv").set_index("idx").label
    bak = REG.with_name(REG.stem + ".before_roofs.csv")
    if not bak.exists():
        reg.to_csv(bak, index=False)
    reg["roof_shape"] = (reg.index + 1).map(lab).map(TAG)
    reg.to_csv(REG, index=False)
    for s in ["train", "heldout"]:
        print(s, reg[reg.split == s].roof_shape.value_counts(dropna=False).to_dict())
    n = reg.groupby("split").roof_shape.value_counts().unstack(fill_value=0)
    print("H2 gate (20 train, 5 held-out per class):", bool((n.loc["train"] >= 20).all() and (n.loc["heldout"] >= 5).all()))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"fetch": fetch, "sheets": sheets, "audit": audit, "apply": apply}.get(cmd, lambda: check(sys.argv[2]) if cmd == "check" else print(__doc__))()
