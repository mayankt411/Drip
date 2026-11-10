"""Tables, figure and paper for framework v3. Every number comes from results/ files."""
import json
import re
from collections import defaultdict

import numpy as np
import pandas as pd

from .common import ROOT, cfg
from .framework import fw

RES, PAPER = ROOT / "results", ROOT / "paper"
BLUE, ORANGE, GREY = "#0072B2", "#D55E00", "#555555"


def f(x, d=2):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}".replace("-", "−")


def pv(p):
    return "n/a" if p is None or np.isnan(p) else ("< .001" if p < 0.001 else f"{p:.3f}".lstrip("0"))


def read(name):
    p = RES / name
    return pd.read_csv(p) if p.exists() else None


def h1(fwc):
    m = read("ml_yolo_metrics.csv")
    if m is None:
        return None, None
    r, t = m.iloc[0], fwc["hypotheses"]["h1_detection"]
    out = pd.DataFrame([{"map50": r.map50, "precision": r.precision, "recall": r.recall, "map50_95": r.map50_95,
                         "target_map50": t["target_map50"], "target_precision": t["target_precision"],
                         "n_images": r.n_images, "n_labels": r.n_labels}])
    out.to_csv(RES / "h1_yolo_metrics.csv", index=False)
    ok = r.map50 >= t["target_map50"] and r.precision >= t["target_precision"]
    return out, {"status": "PASS" if ok else "FAIL", "map50": float(r.map50), "precision": float(r.precision)}


def tables(fwc):
    t = {}
    o, v = h1(fwc)
    if o is not None:
        r = o.iloc[0]
        t["table_h1"] = "\n".join(["**Table 1**", "", "*Tank Detection on Held-Out Terminals*", "", "| Metric | Value | Target |", "|:--|--:|--:|",
                                   f"| mAP@50 | {f(r.map50, 3)} | ≥ {f(r.target_map50)} |", f"| Precision | {f(r.precision, 3)} | ≥ {f(r.target_precision)} |",
                                   f"| Recall | {f(r.recall, 3)} | n/a |", f"| Test images / labelled tanks | {int(r.n_images)} / {int(r.n_labels)} | n/a |"])
    h2 = read("h2_classification_metrics.csv")
    if h2 is not None:
        rows = ["**Table 2**", "", "*Structural and Operational Classification*", "",
                "| Task | Model | Status | *n* | Accuracy | Macro F1 |", "|:--|:--|:--|--:|--:|--:|"]
        for _, r in h2.iterrows():
            rows.append(f"| {r.task.replace('_', ' ')} | {r.model} | {str(r.status).replace('_', ' ').lower()} | "
                        f"{int(r.n_test) if 'n_test' in r and not pd.isna(r.n_test) else 'n/a'} | "
                        f"{f(r.get('accuracy', np.nan))} | {f(r.get('macro_f1', np.nan))} |")
        t["table_h2"] = "\n".join(rows)
    h3 = read("h3_macro_metrics.csv")
    if h3 is not None:
        rows = ["**Table 3**", "", "*Hub Activity Index Against EIA Cushing Stocks, Test Weeks 2023–2024*", "",
                "| Comparison | *n* | *r* | *p* | 95% CI | ρ |", "|:--|--:|--:|--:|:--|--:|"]
        for _, r in h3.iterrows():
            rows.append(f"| {r.comparison.replace('_', ' ')} | {int(r.n_pairs)} | {f(r.pearson_r)} | {pv(r.pearson_p)} | "
                        f"[{f(r.ci_lo)}, {f(r.ci_hi)}] | {f(r.spearman_rho)} |")
        rows += ["", "*Note.* *p* is the naive Pearson test; smoothing the EIA series adds autocorrelation, so it is optimistic. Intervals are stationary block bootstrap."]
        t["table_h3"] = "\n".join(rows)
    return t, v


def figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    g = read("h3_macro_weekly.csv")
    if g is None:
        return
    g["week_end"] = pd.to_datetime(g.week_end)
    z = lambda a: (a - np.nanmean(a)) / np.nanstd(a)
    plt.rcParams.update({"svg.fonttype": "none", "font.size": 9})
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(g.week_end, z(g.eia_smooth.to_numpy(float)), color=GREY, lw=1.6, label="EIA, 4-week mean (z-score)")
    ok = g["index"].notna()
    ax.scatter(g.week_end[ok], z(g["index"].to_numpy(float))[ok], s=16, color=ORANGE, label="Activity index (z-score)")
    ax.set_ylabel("z-score")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    (PAPER / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(PAPER / "figures" / "macro_utilization.svg")


def main():
    fwc = fw()
    t, v1 = tables(fwc)
    h3v = json.loads((RES / "h3_verdict.json").read_text(encoding="utf-8")) if (RES / "h3_verdict.json").exists() else None
    h2 = read("h2_classification_metrics.csv")
    fill = defaultdict(lambda: "[not yet run]")
    fill.update(t)
    if v1:
        fill["h1_sentence"] = (f"The detector {'met' if v1['status'] == 'PASS' else 'did not meet'} the targets: mAP@50 {v1['map50']:.3f}, "
                               f"precision {v1['precision']:.3f}.")
    if h2 is not None:
        s = h2[(h2.task == "structural_floating_vs_fixed") & (h2.model == "cnn")]
        if len(s):
            r, maj = s.iloc[0], h2[h2.model == "majority"].iloc[0]
            tgt = fwc["hypotheses"]["h2_classification"]["target_accuracy"]
            fill["h2_sentence"] = (f"Floating-roof versus fixed-dome accuracy on held-out terminals was {r.accuracy:.2f} (macro F1 {r.macro_f1:.2f}) "
                                   f"against a majority-class accuracy of {maj.accuracy:.2f}; the {tgt:.2f} target was "
                                   f"{'met' if r.accuracy >= tgt and r.accuracy > maj.accuracy else 'not met'}.")
        else:
            fill["h2_sentence"] = "Structural classification could not be tested: " + str(h2.iloc[-1].get("reason", "too few labels")) + "."
        fill["h2_op_sentence"] = "Operational (active versus idle) classification was not tested because no independent activity labels exist."
    if h3v:
        fill["h3_sentence"] = (f"The smoothed activity index had r = {f(h3v['pearson_r'])} with EIA stocks over {h3v['n_pairs']} test weeks "
                               f"(raw EIA: r = {f(h3v['raw_r'])}; season-only control: r = {f(h3v['season_r'])}); the criteria were "
                               f"{'met' if h3v['status'] == 'PASS' else 'not all met'}.")
    tpl = (PAPER / "paper_v3_template.md").read_text(encoding="utf-8")
    text = re.sub(r"\{\{(\w+)\}\}", lambda m: fill[m.group(1)], tpl)
    if not (RES / "h3_verdict.json").exists():
        head, sep, body = text.partition("\n---\n")
        text = head + sep + "> **DRAFT SHELL: results are filled in when the pipeline is run.**\n\n" + body
    (PAPER / "paper_v3.md").write_text(text, encoding="utf-8")
    for n, s in t.items():
        (PAPER / "tables").mkdir(exist_ok=True)
        (PAPER / "tables" / f"v3_{n}.md").write_text(s + "\n", encoding="utf-8")
    figure()
    print("paper/paper_v3.md written")


if __name__ == "__main__":
    main()
