"""Index the Sentinel-2 products in the STAC dumps and pick the dates worth downloading."""
import json

import pandas as pd

from .common import ROOT, cfg, in_range

STAC_FILES = ["data/raw/s2_cushing_stac_2021_2023.json", "data/raw/s2_cushing_stac_2024.json"]
OUT = ROOT / "data" / "ml" / "scenes.csv"


def band_keys(c):
    return [f"{b}_10m" for b in c["bands"]["ten_m"]] + [f"{b}_20m" for b in c["bands"]["twenty_m"]] + [c["bands"]["scl"]]


def index_products(c):
    keys = band_keys(c)
    rows, seen = [], set()
    for rel in STAC_FILES:
        for f in json.load(open(ROOT / rel, encoding="utf-8"))["features"]:
            tile = f["id"].split("_")[5]
            if f["id"] in seen or tile not in c["tiles"]:
                continue
            seen.add(f["id"])
            p, a = f["properties"], f["assets"]
            row = {"product_id": f["id"], "date": p["datetime"][:10], "tile": tile,
                   "cloud": p["eo:cloud_cover"], "sun_elev": p["view:sun_elevation"],
                   "sun_az": p["view:sun_azimuth"], "baseline": p.get("processing:version"),
                   "scale": a["B04_10m"].get("raster:scale", 0.0001),
                   "offset": a["B04_10m"].get("raster:offset", 0.0)}
            for k in keys:
                row[k] = a[k]["alternate"]["https"]["href"]
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["date", "tile"]).reset_index(drop=True)


def select(df, c):
    s = c["scenes"]
    ok = df.cloud <= s["max_scene_cloud_percent"]
    ok &= df.date.map(lambda d: in_range(d, s["window_start"], s["window_end"]))
    return df[ok].reset_index(drop=True)


def main():
    c = cfg()
    df = index_products(c)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sel = select(df, c)
    sel.to_csv(OUT, index=False)
    print(len(df), "products indexed;", len(sel), "pass the cloud filter on", sel.date.nunique(), "dates")


if __name__ == "__main__":
    main()
