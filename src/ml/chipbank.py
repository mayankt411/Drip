"""Cut a 16x16x6 chip around every registry tank on every downloaded date."""
import numpy as np
import pandas as pd

from .common import ROOT, cfg
from .cube import make_grid

CUBES = ROOT / "data" / "processed" / "cubes"
BANK = ROOT / "data" / "processed" / "chipbank.npz"
REGISTRY = ROOT / "data" / "tanks" / "cushing_full_registry.csv"


def disc_mask(radius_px, size):
    yy, xx = np.mgrid[:size, :size]
    cc = (size - 1) / 2
    return (xx - cc) ** 2 + (yy - cc) ** 2 <= max(radius_px, 1.5) ** 2


def tank_chip(refl, scl, row, col, size, cloud_classes):
    """Chip and QC for a tank whose centre sits at (row, col) in grid pixels."""
    r0, c0 = int(round(row - size / 2)), int(round(col - size / 2))
    h, w = refl.shape[1:]
    if r0 < 0 or c0 < 0 or r0 + size > h or c0 + size > w:
        return None
    return refl[:, r0:r0 + size, c0:c0 + size], scl[r0:r0 + size, c0:c0 + size]


def build_bank(registry, cube_paths, c, grid=None):
    grid = grid or make_grid(c)
    size = c["cnn"]["chip_px"]
    cols = (registry.x_utm.to_numpy() - grid["x0"]) / grid["res"]
    rows = (grid["y1"] - registry.y_utm.to_numpy()) / grid["res"]
    rad = registry.diameter_m.to_numpy() / 2 / grid["res"]
    n, d = len(registry), len(cube_paths)
    chips = np.zeros((d, n, 6, size, size), np.uint16)
    cloud = np.ones((d, n), np.float32)
    nodata = np.ones((d, n), np.float32)
    disc_mean = np.zeros((d, n, 6), np.float32)
    dates, sun = [], np.zeros((d, 2), np.float32)
    for k, path in enumerate(cube_paths):
        z = np.load(path)
        refl, scl = z["refl"], z["scl"]
        dates.append(path.stem)
        sun[k] = [float(z["sun_elev"]), float(z["sun_az"])]
        for i in range(n):
            got = tank_chip(refl, scl, rows[i], cols[i], size, c["cloud_scl_classes"])
            if got is None:
                continue
            chip, sc = got
            m = disc_mask(rad[i], size)
            chips[k, i] = chip
            cloud[k, i] = np.isin(sc[m], c["cloud_scl_classes"]).mean()
            nodata[k, i] = (chip[2][m] == 0).mean()
            ok = m & (chip[2] > 0)
            if ok.any():
                disc_mean[k, i] = chip[:, ok].mean(axis=1) / 10000.0
    return {"chips": chips, "cloud": cloud, "nodata": nodata, "disc_mean": disc_mean,
            "dates": np.array(dates), "sun": sun}


def main():
    c = cfg()
    reg = pd.read_csv(REGISTRY)
    paths = sorted(CUBES.glob("*.npz"))
    bank = build_bank(reg, paths, c)
    bank["tank_ids"] = reg.tank_id.to_numpy()
    BANK.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(BANK, **bank)
    print("bank:", bank["chips"].shape)


if __name__ == "__main__":
    main()
