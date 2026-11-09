"""Tables, figures and paper numbers for the ML study. Everything is read from results/."""
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from .common import ROOT, cfg

RES = ROOT / "results"
PAPER = ROOT / "paper"
BLUE, ORANGE, GREEN, GREY = "#0072B2", "#D55E00", "#009E73", "#555555"
LABEL = {"cnn": "CNN", "ridge": "Ridge (B04, B08, B11, sun)", "sun_only": "Ridge (sun elevation only)",
         "train_mean": "Training mean"}


def fmt(x, d=2):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}".replace("-", "−")


def fmt_p(p):
    return "n/a" if p is None or np.isnan(p) else ("< .001" if p < 0.001 else f"{p:.3f}".lstrip("0"))


def load():
    d = {}
    for name in ("ml_yolo_metrics", "ml_eia_metrics", "ml_weekly_inventory", "ml_cnn_training_log"):
        f = RES / f"{name}.csv"
        d[name] = pd.read_csv(f) if f.exists() else None
    for name in ("ml_verdicts", "ml_cnn_training_summary"):
        f = RES / f"{name}.json"
        d[name] = json.loads(f.read_text()) if f.exists() else None
    return d


def table_yolo(d, c):
    m = d["ml_yolo_metrics"]
    if m is None:
        return None
    r = m.iloc[0]
    return "\n".join([
        "**Table 1**", "", "*Tank Detection on Held-Out Terminals (Test Dates 2023–2024)*", "",
        "| Metric | Value | Pre-specified threshold |", "|:--|--:|--:|",
        f"| Precision | {fmt(r.precision)} | ≥ {fmt(c['h1']['precision_min'])} |",
        f"| Recall | {fmt(r.recall)} | n/a |",
        f"| mAP@50 | {fmt(r.map50)} | ≥ {fmt(c['h1']['map50_min'])} |",
        f"| mAP@50–95 | {fmt(r.map50_95)} | n/a |",
        f"| Test images / labelled tanks | {int(r.n_images)} / {int(r.n_labels)} | n/a |", "",
        "*Note.* Labels come from OpenStreetMap footprints, so they are noisy; detections of tanks missing from OSM count as false positives."])


def table_cnn(d, c):
    s, w = d["ml_cnn_training_summary"], d["ml_weekly_inventory"]
    if s is None or w is None:
        return None
    seeds = [v for k, v in s.items() if k.endswith("best_val_mse_z")]
    return "\n".join([
        "**Table 2**", "", "*Hub-Level CNN Training and Per-Tank Validation Status*", "",
        "| Item | Value |", "|:--|--:|",
        f"| Training dates (fit / inner validation) | {s['n_fit_dates']} / {s['n_val_dates']} |",
        f"| Ensemble seeds | {len(seeds)} |",
        f"| Best inner-validation MSE, standardized (mean over seeds) | {fmt(float(np.mean(seeds)), 3)} |",
        f"| Per-tank fill MAE, RMSE, R² (H2) | not testable |", "",
        "*Note.* No per-tank fill-level labels exist, so the network is trained against hub-level EIA stocks only and H2 is not tested. "
        "MSE is on z-scored EIA stocks."])


def table_eia(d, c):
    m = d["ml_eia_metrics"]
    if m is None:
        return None
    rows = ["**Table 3**", "", "*Agreement With EIA Weekly Cushing Stocks on the Held-Out Test Period*", "",
            "| Method | Tank source | *n* | *r* | *p* | 95% CI | ρ | *R*² | Δ lag 0 *r* [CI] | Δ lag 1 *r* [CI] |",
            "|:--|:--|--:|--:|--:|:--|--:|--:|:--|:--|"]
    t = m[m.split == "test"]
    for (method, src), g in t.groupby(["method", "tank_source"]):
        lv = g[g.metric == "level"].iloc[0]

        def ci(row):
            return f"{fmt(row.pearson_r)} [{fmt(row.ci_lo)}, {fmt(row.ci_hi)}]" if "ci_lo" in row and not np.isnan(row.get("ci_lo", np.nan)) else fmt(row.pearson_r)
        dl = {k: g[g.metric == f"diff_lag{k}"].iloc[0] for k in (0, 1)}
        rows.append(f"| {LABEL[method]} | {src} | {int(lv.n_pairs)} | {fmt(lv.pearson_r)} | {fmt_p(lv.get('pearson_p', np.nan))} | "
                    f"[{fmt(lv.get('ci_lo', np.nan))}, {fmt(lv.get('ci_hi', np.nan))}] | {fmt(lv.get('spearman_rho', np.nan))} | "
                    f"{fmt(lv.get('r2', np.nan))} | {ci(dl[0])} | {ci(dl[1])} |")
    rows += ["", f"*Note.* Level statistics use weeks with a valid satellite pass. *p* is the naive Pearson test and ignores autocorrelation; "
             f"intervals are stationary block bootstrap (mean block {c['stats']['block_lengths'][0]} weeks, {c['stats']['n_boot']} draws). "
             "Δ columns use consecutive weeks only. Models were fit on 2021–2022 only."]
    return "\n".join(rows)


def figure_eia(d, c):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    w = d["ml_weekly_inventory"]
    if w is None:
        return False
    src = "yolo" if ((w.tank_source == "yolo") & (w.method == "cnn") & w.usable).any() else "registry"
    g = w[(w.method == "cnn") & (w.tank_source == src) & w.usable].copy()
    g["week_end"] = pd.to_datetime(g.week_end)
    wk = g.groupby("week_end").agg(pred=("pred_mbbl", "mean"), eia=("eia_mbbl", "first"), split=("split", "first")).reset_index()
    plt.rcParams.update({"svg.fonttype": "none", "font.size": 9})
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4), gridspec_kw={"width_ratios": [2.2, 1]})
    ax[0].plot(wk.week_end, wk.eia / 1000, color=GREY, lw=1.4, label="EIA (weeks with a pass)")
    for sp, col, lab in (("train", BLUE, "CNN, training weeks"), ("test", ORANGE, "CNN, test weeks")):
        s = wk[wk.split == sp]
        ax[0].scatter(s.week_end, s.pred / 1000, s=14, color=col, label=lab, zorder=3)
    ax[0].axvline(pd.Timestamp(c["splits"]["test_start"]), color=GREY, ls=":", lw=1)
    ax[0].set_ylabel("Cushing stocks (million bbl)")
    ax[0].legend(frameon=False, fontsize=8)
    t = wk[wk.split == "test"]
    ax[1].scatter(t.eia / 1000, t.pred / 1000, s=16, color=ORANGE)
    lim = [min(t.eia.min(), t.pred.min()) / 1000 - 1, max(t.eia.max(), t.pred.max()) / 1000 + 1]
    ax[1].plot(lim, lim, color=GREY, lw=1, ls="--")
    ax[1].set_xlabel("EIA (million bbl)")
    ax[1].set_ylabel("CNN hub estimate (million bbl)")
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    (PAPER / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(PAPER / "figures" / "eia_vs_satellite_ml.svg")
    return src


def figure_yolo(d, c):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pr = RES / "ml_yolo_pr_curve.csv"
    if not pr.exists():
        return False
    p = pd.read_csv(pr)
    plt.rcParams.update({"svg.fonttype": "none", "font.size": 9})
    imgs = sorted((ROOT / "data" / "ml" / "yolo" / "test" / "images").glob("*.png"))[:2]
    fig, ax = plt.subplots(1, 1 + len(imgs), figsize=(9, 3.2))
    ax[0].plot(p.recall, p.precision, color=BLUE, lw=1.6)
    ax[0].set(xlabel="Recall", ylabel="Precision", xlim=(0, 1), ylim=(0, 1.02))
    ax[0].spines[["top", "right"]].set_visible(False)
    try:
        from PIL import Image
        from ultralytics import YOLO
        model = YOLO(str(ROOT / c["yolo"]["checkpoint"]))
        for a, f in zip(ax[1:], imgs):
            im = Image.open(f)
            a.imshow(im)
            a.axis("off")
            lab = f.parent.parent / "labels" / (f.stem + ".txt")
            for line in lab.read_text().split("\n"):
                if line:
                    _, cx, cy, bw, bh = map(float, line.split())
                    a.add_patch(plt.Rectangle(((cx - bw / 2) * im.width, (cy - bh / 2) * im.height), bw * im.width, bh * im.height,
                                              fill=False, ec=GREEN, lw=1.2))
            for b in model.predict(str(f), imgsz=c["yolo"]["imgsz"], conf=c["yolo"]["conf"], verbose=False)[0].boxes.xyxy.cpu().numpy():
                a.add_patch(plt.Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec=ORANGE, lw=1.2, ls="--"))
            a.set_title("green: OSM label, orange: detection", fontsize=8)
    except Exception as e:
        ax[1].text(0.5, 0.5, f"overlay unavailable:\n{type(e).__name__}", ha="center")
    fig.tight_layout()
    fig.savefig(PAPER / "figures" / "yolo_detection.svg")
    return True


def numbers(d, c):
    n = {}
    prior = json.loads((RES / "paper_numbers.json").read_text())
    for k in ("m1_pass", "m2_pass", "m3_pass", "cnr_mean", "n_tanks", "median_min", "median_max"):
        n[f"prior_{k}"] = prior[k]
    v = d["ml_verdicts"]
    if v:
        n.update({f"count_{k}": val for k, val in v["counts"].items()})
        for k, h in v["verdicts"].items():
            n[f"{k.lower()}_status"] = h["status"]
            for kk, vv in h.items():
                if isinstance(vv, float):
                    n[f"{k.lower()}_{kk}"] = fmt(vv, 3)
    n["train_window"] = f"{c['splits']['train_start']} to {c['splits']['train_end']}"
    n["test_window"] = f"{c['splits']['test_start']} to {c['splits']['test_end']}"
    n["h1_map50_min"], n["h1_precision_min"] = fmt(c["h1"]["map50_min"]), fmt(c["h1"]["precision_min"])
    n["level_r_min"] = fmt(c["stats"]["level_r_min"])
    n["n_boot"], n["block"] = c["stats"]["n_boot"], c["stats"]["block_lengths"][0]
    return n


def sentences(d):
    """Result sentences chosen by the verdicts, so the text never outruns the numbers."""
    v = d["ml_verdicts"]["verdicts"] if d["ml_verdicts"] else {}
    s = {}
    h1 = v.get("H1", {}).get("status")
    s["h1_sentence"] = {"PASS": "The detector met both pre-specified thresholds on the held-out terminals.",
                        "FAIL": "The detector did not meet the pre-specified thresholds on the held-out terminals."}.get(h1, "[not yet run]")
    h3 = v.get("H3_yolo", v.get("H3_registry", {})).get("status")
    s["h3_sentence"] = {"PASS": "The CNN hub series met the pre-specified level and first-difference criteria in this exploratory test.",
                        "FAIL": "The CNN hub series did not meet the pre-specified level and first-difference criteria."}.get(h3, "[not yet run]")
    base = d["ml_eia_metrics"]
    s["baseline_sentence"] = "[not yet run]"
    if base is not None and h3:
        t = base[(base.split == "test") & (base.metric == "level")]
        src = "yolo" if (t.tank_source == "yolo").any() else "registry"
        t = t[t.tank_source == src].set_index("method")
        if "cnn" in t.index:
            others = t.drop("cnn")
            best = others.r2.idxmax()
            beats = t.loc["cnn", "r2"] > others.r2.max()
            s["baseline_sentence"] = (f"On test weeks the CNN {'had a higher' if beats else 'did not have a higher'} R² than every baseline "
                                      f"(best baseline: {LABEL[best]}, R² = {fmt(others.r2.max())}; CNN R² = {fmt(t.loc['cnn','r2'])}).")
    return s


def compile_paper(d, c):
    tpl = (PAPER / "paper_ml_template.md").read_text(encoding="utf-8")
    fill = defaultdict(lambda: "[not yet run]")
    fill.update({k: str(x) for k, x in numbers(d, c).items()})
    fill.update(sentences(d))
    for name, fn in (("table_yolo", table_yolo), ("table_cnn", table_cnn), ("table_eia", table_eia)):
        fill[name] = fn(d, c) or "*Not yet generated: run the pipeline (see paper/RUNBOOK_ML.md).*"
    banner = ""
    if d["ml_verdicts"] is None:
        banner = "> **DRAFT SHELL: no model has been trained yet. Every bracketed value is filled from results files when the pipeline is run.**\n\n"
    text = re.sub(r"\{\{(\w+)\}\}", lambda m: fill[m.group(1)], tpl)
    head, sep, body = text.partition("\n---\n")
    text = head + sep + banner + body if sep else banner + text
    (PAPER / "paper.md").write_text(text, encoding="utf-8")
    return text


def main():
    c, d = cfg(), load()
    (PAPER / "tables").mkdir(parents=True, exist_ok=True)
    for name, fn in (("ml_table1_yolo", table_yolo), ("ml_table2_cnn", table_cnn), ("ml_table3_eia", table_eia)):
        t = fn(d, c)
        if t:
            (PAPER / "tables" / f"{name}.md").write_text(t + "\n", encoding="utf-8")
    figure_eia(d, c)
    figure_yolo(d, c)
    compile_paper(d, c)
    print("paper/paper.md written")


if __name__ == "__main__":
    main()
