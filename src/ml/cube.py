"""Crop the AOI out of Sentinel-2 band files onto one 10 m UTM grid and stack the bands."""
import math

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

from .common import aoi, cfg

BAND_ORDER = ["B02", "B03", "B04", "B08", "B11", "B12"]


def make_grid(c=None):
    c = c or cfg()
    b = aoi(c)
    t = Transformer.from_crs("EPSG:4326", c["utm_crs"], always_xy=True)
    x0, y0 = t.transform(b["west"], b["south"])
    x1, y1 = t.transform(b["east"], b["north"])
    x0, y0 = math.floor(x0 / 10) * 10, math.floor(y0 / 10) * 10
    x1, y1 = math.ceil(x1 / 10) * 10, math.ceil(y1 / 10) * 10
    return {"x0": x0, "y1": y1, "w": int((x1 - x0) / 10), "h": int((y1 - y0) / 10), "res": 10}


def read_on_grid(path, grid, resampling):
    """Read one band file onto the grid. Pixels outside the file come back as 0."""
    left, top = grid["x0"], grid["y1"]
    right, bottom = left + grid["w"] * grid["res"], top - grid["h"] * grid["res"]
    with rasterio.open(path) as src:
        win = from_bounds(left, bottom, right, top, transform=src.transform)
        return src.read(1, window=win, out_shape=(grid["h"], grid["w"]), boundless=True,
                        fill_value=0, resampling=resampling)


def to_reflectance_u16(dn, scale, offset):
    """DN to reflectance x 10000 as uint16. DN 0 is nodata and stays 0."""
    refl = np.clip(dn.astype(np.float64) * scale + offset, 0, 1.0)
    out = np.round(refl * 10000).astype(np.uint16)
    out[dn == 0] = 0
    return out


def crop_product(files, scale, offset, grid):
    """files: band name -> local path (B02..B12 and 'SCL'). Returns (6,H,W) uint16 and SCL."""
    layers = []
    for b in BAND_ORDER:
        rs = Resampling.nearest if b in ("B02", "B03", "B04", "B08") else Resampling.bilinear
        dn = read_on_grid(files[b], grid, rs)
        layers.append(to_reflectance_u16(dn, scale, offset))
    scl = read_on_grid(files["SCL"], grid, Resampling.nearest).astype(np.uint8)
    return np.stack(layers), scl


def mosaic(parts):
    """Fill pixels from later tiles wherever the earlier ones have no data (B04 == 0)."""
    refl, scl = parts[0]
    refl, scl = refl.copy(), scl.copy()
    for r2, s2 in parts[1:]:
        gap = refl[2] == 0
        refl[:, gap] = r2[:, gap]
        scl[gap] = s2[gap]
    return refl, scl
