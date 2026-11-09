"""Download Sentinel-2 L2A bands from CDSE, crop to the AOI, keep only the compact cube.

Credentials come from CDSE_USERNAME / CDSE_PASSWORD in the environment or a local .env.
Every raw band file is hashed into data/manifest.csv before it is deleted.
"""
import argparse
import time

import numpy as np
import pandas as pd
import requests

from .common import ROOT, cfg, env_credential, log_manifest, sha256
from .cube import BAND_ORDER, crop_product, make_grid, mosaic

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CUBES = ROOT / "data" / "processed" / "cubes"
RAWDIR = ROOT / "data" / "raw" / "rasters_ml"


class Auth:
    def __init__(self):
        self.token, self.t0 = None, 0.0

    def header(self):
        if self.token is None or time.time() - self.t0 > 420:
            r = requests.post(TOKEN_URL, timeout=60, data={
                "client_id": "cdse-public", "grant_type": "password",
                "username": env_credential("CDSE_USERNAME"), "password": env_credential("CDSE_PASSWORD")})
            r.raise_for_status()
            self.token, self.t0 = r.json()["access_token"], time.time()
        return {"Authorization": f"Bearer {self.token}"}


def fetch(url, dest, auth, tries=4):
    dest.parent.mkdir(parents=True, exist_ok=True)
    for k in range(tries):
        try:
            with requests.get(url, headers=auth.header(), stream=True, timeout=120) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            tmp.replace(dest)
            return
        except requests.RequestException:
            if k == tries - 1:
                raise
            time.sleep(5 * (k + 1))


def process_date(date, rows, grid, auth, keep_raw):
    out = CUBES / f"{date.replace('-', '')}.npz"
    if out.exists():
        return "skip"
    parts, used = [], []
    for _, p in rows.iterrows():
        files = {}
        for b in BAND_ORDER + ["SCL"]:
            key = f"{b}_10m" if b in ("B02", "B03", "B04", "B08") else f"{b}_20m"
            url = p[key]
            dest = RAWDIR / p.product_id / url.split("Nodes(")[-1].split(")")[0]
            fetch(url, dest, auth)
            log_manifest(url.split("/$value")[0][:200], f"tile={p.tile};band={b}", p.product_id,
                         p.cloud, sha256(dest), "SUCCESS")
            files[b] = dest
        parts.append(crop_product(files, p.scale, p.offset, grid))
        used.append(p.product_id)
        if not keep_raw:
            for f in files.values():
                f.unlink(missing_ok=True)
    refl, scl = mosaic(parts)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, refl=refl, scl=scl, sun_elev=float(rows.sun_elev.mean()),
                        sun_az=float(rows.sun_az.mean()), products=np.array(used))
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)
    ap.add_argument("--keep-raw", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="only the first N dates")
    a = ap.parse_args()
    c = cfg()
    df = pd.read_csv(ROOT / "data" / "ml" / "scenes.csv", dtype={"date": str})
    if a.start:
        df = df[df.date >= a.start]
    if a.end:
        df = df[df.date <= a.end]
    dates = sorted(df.date.unique())[: a.limit]
    grid, auth = make_grid(c), Auth()
    for i, d in enumerate(dates, 1):
        print(f"[{i}/{len(dates)}] {d}", process_date(d, df[df.date == d], grid, auth, a.keep_raw), flush=True)


if __name__ == "__main__":
    main()
