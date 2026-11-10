"""Sentinel-1 backscatter per tank from Planetary Computer (anonymous). One AOI window per pass, cached."""
import argparse
import json
import sys
import threading
import time

import numpy as np
import pandas as pd
from pyproj import Transformer

from .common import ROOT, aoi, cfg, log_manifest, sha256

REGISTRY = ROOT / "data" / "tanks" / "cushing_full_registry.csv"
OUT = ROOT / "data" / "radar"
FEATS = ["vv_db", "vv_max_db", "vh_db", "contrast_db"]
LOCK = threading.Lock()


def rc():
    return cfg("configs/v4_radar.yaml")


def db(x):
    return 10 * np.log10(np.maximum(x, 1e-6))


def search(c):
    import planetary_computer as pc
    from pystac_client import Client
    b = aoi()
    cat = Client.open(c["stac"], modifier=pc.sign_inplace)
    q = cat.search(collections=[c["collection"]], bbox=[b["west"], b["south"], b["east"], b["north"]],
                   datetime=f"{c['start']}/{c['end']}", max_items=10000)
    rows = []
    for it in q.items():
        p = it.properties
        rows.append({"id": it.id, "date": it.datetime.strftime("%Y-%m-%d"), "orbit": p.get("sat:orbit_state", "na"),
                     "rel_orbit": int(p.get("sat:relative_orbit", -1)), "item": it})
    return rows


def read_window(item):
    """VV and VH linear power over the AOI, with the window transform and CRS."""
    import planetary_computer as pc
    import rasterio
    from rasterio.windows import from_bounds
    b = aoi()
    item = pc.sign(item)
    arrs, tf, crs, res = {}, None, None, None
    for pol in ("vv", "vh"):
        with rasterio.open(item.assets[pol].href) as ds:
            t = Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)
            xs, ys = t.transform([b["west"], b["east"]], [b["south"], b["north"]])
            win = from_bounds(min(xs), min(ys), max(xs), max(ys), ds.transform).round_offsets().round_lengths()
            a = ds.read(1, window=win, boundless=True, fill_value=np.nan).astype("float32")
            a[a <= 0] = np.nan
            arrs[pol] = a
            tf, crs, res = ds.window_transform(win), ds.crs, abs(ds.res[0])
    return arrs["vv"], arrs["vh"], tf, crs, res


def tank_features(vv, vh, tf, crs, res, tanks, c):
    """Per tank: disc mean VV, disc max VV, disc mean VH (dB) and disc minus rim VV (dB)."""
    tr = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    x, y = tr.transform(tanks.longitude.to_numpy(), tanks.latitude.to_numpy())
    cols, rows = (~tf) @ (np.asarray(x), np.asarray(y))
    rad = np.maximum(tanks.diameter_m.to_numpy() / 2 / res, 1.5)
    h, w = vv.shape
    out = np.full((len(tanks), len(FEATS)), np.nan, np.float32)
    for i, (cx, cy, r) in enumerate(zip(cols, rows, rad)):
        m = int(np.ceil(r * c["rim_outer"])) + 1
        x0, x1, y0, y1 = int(cx) - m, int(cx) + m + 1, int(cy) - m, int(cy) + m + 1
        if x0 < 0 or y0 < 0 or x1 > w or y1 > h:
            continue
        a, b = vv[y0:y1, x0:x1], vh[y0:y1, x0:x1]
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
        disc = (d <= r * c["disc_shrink"]) & ~np.isnan(a) & ~np.isnan(b)
        rim = (d >= r * c["rim_inner"]) & (d <= r * c["rim_outer"]) & ~np.isnan(a)
        if disc.sum() < 3 or rim.sum() < 3:
            continue
        v = db(a[disc].mean())
        out[i] = [v, db(a[disc].max()), db(b[disc].mean()), v - db(a[rim].mean())]
    return out


def process(row, tanks, c):
    f = OUT / "feat" / f"{row['id']}.npz"
    if f.exists():
        return "cached"
    vv, vh, tf, crs, res = read_window(row["item"])
    feats = tank_features(vv, vh, tf, crs, res, tanks, c)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.stem + ".tmp.npz")
    np.savez_compressed(tmp, feats=feats, date=row["date"], orbit=row["orbit"], rel_orbit=row["rel_orbit"])
    tmp.replace(f)
    with LOCK:
        log_manifest(c["stac"], f"collection={c['collection']};aoi", row["id"], "NA", sha256(f), "SUCCESS")
    return "ok"


def attempt(row, tanks, c):
    for k in range(1, c["retries"] + 1):
        try:
            return process(row, tanks, c)
        except Exception as e:  # network blips are common; the item is retried on the next run if all fail
            err = type(e).__name__
            time.sleep(5 * k)
    return f"failed:{err}"


def yearly(rows):
    return pd.Series([r["date"][:4] for r in rows]).value_counts().sort_index()


def effective_start(counts, c):
    """Earliest year from which every full year has enough passes (2024 is partial)."""
    ok = {int(y): n >= c["min_passes_per_year"] for y, n in counts.items() if int(y) < 2024}
    start = None
    for y in sorted(ok, reverse=True):
        if not ok[y]:
            break
        start = y
    return start


def check():
    c = rc()
    rows = search(c)
    if not rows:
        print("no Sentinel-1 items found; stopping")
        return 1
    counts = yearly(rows)
    print("passes per year:\n", counts.to_string())
    print("orbits:", pd.Series([f"{r['orbit']}{r['rel_orbit']}" for r in rows]).value_counts().to_dict())
    start = effective_start(counts, c)
    if start is None:
        print("no run of years with enough passes; stopping")
        return 1
    tanks = pd.read_csv(REGISTRY)
    t0 = time.time()
    vv, vh, tf, crs, res = read_window(rows[len(rows) // 2]["item"])
    feats = tank_features(vv, vh, tf, crs, res, tanks, c)
    cov = float(np.mean(~np.isnan(feats[:, 0])))
    print(f"test read {time.time() - t0:.1f}s, pixel {res:.0f} m, tanks covered {cov:.0%}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "coverage.json").write_text(json.dumps({"effective_start": f"{start}-01-01", "passes": counts.to_dict(),
                                                    "test_read_coverage": cov}, indent=2), encoding="utf-8")
    return 0 if cov > 0.3 else 1


def run(workers):
    from concurrent.futures import ThreadPoolExecutor
    c = rc()
    cov = OUT / "coverage.json"
    if cov.exists():
        c["start"] = max(c["start"], json.loads(cov.read_text(encoding="utf-8"))["effective_start"])
    rows = search(c)
    tanks = pd.read_csv(REGISTRY)
    print(len(rows), "passes from", c["start"])
    bad = 0
    with ThreadPoolExecutor(workers) as ex:
        for k, (r, s) in enumerate(zip(rows, ex.map(lambda r: attempt(r, tanks, c), rows)), 1):
            if s.startswith("failed"):
                bad += 1
                print(r["id"], s)
            if k % 25 == 0:
                print(f"{k}/{len(rows)} done, {bad} failed", flush=True)
    print(f"finished, {bad} failed")
    return 1 if bad > max(5, 0.05 * len(rows)) else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["check", "run"])
    ap.add_argument("--workers", type=int, default=rc()["workers"])
    a = ap.parse_args()
    sys.exit(check() if a.mode == "check" else run(a.workers))
