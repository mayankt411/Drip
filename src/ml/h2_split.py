"""H2 re-split into spatial blocks. The original terminal-cluster split holds 63 of the 64 fixed-roof tanks in the held-out
cluster, so H2 cannot be trained. Rule fixed in docs/h2_resplit.md before the classifier was run: 1 km blocks, seeded order,
fixed-roof tanks balanced first, then total tanks. One seed, no retries. Only the split_h2 column is written; split is untouched."""
import numpy as np
import pandas as pd

from .common import ROOT, cfg

REG = ROOT / "data" / "tanks" / "cushing_full_registry.csv"
LABELS = ROOT / "data" / "roofs" / "labels.csv"
CELL_M = 1000


def assign(reg, fixed, seed, cell=CELL_M):
    """Whole blocks go to one side. fixed is a boolean array, True for labelled fixed-roof tanks."""
    key = (reg.x_utm // cell).astype(int).astype(str) + "_" + (reg.y_utm // cell).astype(int).astype(str)
    cells = pd.DataFrame({"key": key, "fixed": fixed}).groupby("key").agg(n=("fixed", "size"), fx=("fixed", "sum"))
    cells = cells.sample(frac=1, random_state=seed)  # seeded shuffle
    tot, fx, side = {"train": 0, "heldout": 0}, {"train": 0, "heldout": 0}, {}
    for k, c in cells.iterrows():
        if c.fx:
            s = "train" if fx["train"] <= fx["heldout"] else "heldout"
        else:
            s = "train" if tot["train"] <= tot["heldout"] else "heldout"
        side[k] = s
        tot[s] += c.n
        fx[s] += c.fx
    return key.map(side)


def main():
    reg = pd.read_csv(REG)
    lab = pd.read_csv(LABELS).set_index("idx").label
    fixed = np.asarray((reg.index + 1).map(lab) == "fixed")
    reg["split_h2"] = assign(reg, fixed, cfg()["seed"])
    reg.to_csv(REG, index=False)
    reg[["tank_id", "split_h2"]].to_csv(ROOT / "data" / "roofs" / "split_h2.csv", index=False)
    reg["label"] = (reg.index + 1).map(lab)
    print(reg.groupby(["split_h2", "label"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
