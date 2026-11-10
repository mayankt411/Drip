"""Table, figure and paper for the radar study. Every number comes from results/ files."""
import json
import re

import numpy as np
import pandas as pd

from .common import ROOT
from .report_v3 import f, pv

RES, PAPER = ROOT / "results", ROOT / "paper"


def table(m):
    names = {"radar_all": "Radar, all tanks", "radar_large_tanks": "Radar, large tanks", "radar_plus_season": "Radar + season",
             "season_only": "Season only", "train_mean": "Training mean"}
    rows = ["**Table 4**", "", "*Radar Predictions Against EIA Cushing Stocks, Test Weeks 2023–2024*", "",
            "| Model | Comparison | *n* | *r* | *p* | 95% CI | *R*² |", "|:--|:--|--:|--:|--:|:--|--:|"]
    for _, r in m.iterrows():
        rows.append(f"| {names.get(r.variant, r.variant)} | {r.comparison.replace('_', ' ')} | {int(r.n)} | {f(r.get('pearson_r', np.nan))} | "
                    f"{pv(r.get('pearson_p', np.nan))} | [{f(r.get('ci_lo', np.nan))}, {f(r.get('ci_hi', np.nan))}] | {f(r.get('r2', np.nan))} |")
    rows += ["", "*Note.* Season-only and training-mean rows are scored on the same weeks as the radar model. Large-tank and season variants are reported, not used for the verdict."]
    return "\n".join(rows)


def figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    g = pd.read_csv(RES / "h3_radar_weekly.csv", parse_dates=["week_end"])
    plt.rcParams.update({"svg.fonttype": "none", "font.size": 9})
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(g.week_end, g.eia_mbbl / 1000, color="#555555", lw=1.6, label="EIA stocks")
    ax.plot(g.week_end, g.season_only / 1000, color="#999999", lw=1, ls="--", label="Season only")
    ok = g.radar_all.notna()
    ax.scatter(g.week_end[ok], g.radar_all[ok] / 1000, s=16, color="#D55E00", label="Radar model")
    ax.set_ylabel("Million barrels")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    (PAPER / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(PAPER / "figures" / "radar_vs_eia.svg")


def main():
    m = pd.read_csv(RES / "h3_radar_metrics.csv")
    v = json.loads((RES / "h3_radar_verdict.json").read_text(encoding="utf-8"))
    tanks = pd.read_csv(ROOT / "data" / "tanks" / "cushing_full_registry.csv")
    if v["status"] == "NOT_TESTABLE":
        sentence = "The radar model could not be scored: " + v["reason"] + "."
    else:
        fails = [k for k in ("r_ok", "p_ok", "ci_ok", "diff_ok", "beats_baselines") if not v[k]]
        sentence = (f"On {v['n_test_weeks']} test weeks the radar model had *r* = {f(v['pearson_r'])}, *p* {pv(v['pearson_p'])}, "
                    f"*R*² = {f(v['r2'])}; the best baseline *R*² was {f(v['best_baseline_r2'])}. "
                    + ("All criteria were met." if v["status"] == "PASS" else "Criteria not met: " + ", ".join(fails).replace("_ok", "").replace("_", " ") + "."))
    abstract = (f"Hypothesis 3 was re-tested with Sentinel-1 radar. Verdict: {v['status'].replace('_', ' ').lower()}. " + sentence)
    figure()
    tpl = (PAPER / "paper_v4_template.md").read_text(encoding="utf-8")
    fill = {"abstract": abstract, "table": table(m), "sentence": sentence, "figure": "figures/radar_vs_eia.svg",
            "n_tanks": str(len(tanks)), "train_start": v.get("train_start", "")[:4], "n_passes": str(v.get("n_passes", ""))}
    (PAPER / "paper_v4.md").write_text(re.sub(r"\{\{(\w+)\}\}", lambda x: fill[x.group(1)], tpl), encoding="utf-8")
    (PAPER / "tables").mkdir(exist_ok=True)
    (PAPER / "tables" / "v4_table_h3_radar.md").write_text(table(m) + "\n", encoding="utf-8")
    print("paper/paper_v4.md written")


if __name__ == "__main__":
    main()
