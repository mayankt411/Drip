"""Tables, Figure 1 and paper numbers for the locked 2024 confirmatory run.

Reads only committed result files. Every number in paper/paper.md comes
from here; the paper itself is filled in from paper/paper_template.md.
"""
import csv
import json
import math
import re
import statistics as st
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper"
METHODS = {
    "M1": "Single-band threshold (B04)",
    "M2": "Multi-band spectral index",
    "M3": "Sub-pixel radial gradient (B04)",
}
COLORS = {"M1": "#0072B2", "M2": "#D55E00", "M3": "#009E73"}


def rows(rel):
    with open(ROOT / rel, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cfg(key):
    text = (ROOT / "configs/prereg_v2.yaml").read_text(encoding="utf-8")
    return float(re.search(rf"{key}:\s*([0-9.]+)", text).group(1))


def r(x, d=2):
    s = str(Decimal(str(x)).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))
    return s.replace("-", "\u2212")


def apa_p(p):
    if p > 0.999:
        return "> .999"
    if p < 0.001:
        return "< .001"
    return r(p, 3).lstrip("0")


def upper_tail(k, n, p0):
    return sum(math.comb(n, i) * p0**i * (1 - p0) ** (n - i) for i in range(k, n + 1))


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, top = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        top = max(top, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = top
    return adj


def cloud_numbers(cloud_max):
    stac = json.load(open(ROOT / "data/raw/s2_cushing_stac_2024.json", encoding="utf-8"))
    items = stac if isinstance(stac, list) else stac["features"]
    seen = [
        (i["id"].split("_")[5], i["properties"]["datetime"][:10], i["properties"]["eo:cloud_cover"])
        for i in items
    ]
    target = [s for s in seen if s[0] in ("T14SQE", "T14SPE")]
    flagged = [s for s in target if s[2] > cloud_max]
    with open(ROOT / "data/exclusions.csv", newline="", encoding="utf-8") as f:
        logged = [x for x in csv.reader(f) if len(x) > 1 and x[1].startswith("2024-")]
    assert len(logged) == len(flagged), "exclusion log and STAC cloud cover disagree"
    clear_dates = {s[1] for s in seen if s[0] == "T14SQE" and s[2] <= cloud_max}
    return {
        "stac_items": len(seen),
        "stac_dates": len({s[1] for s in seen}),
        "target_items": len(target),
        "target_excluded": len(flagged),
        "target_excluded_pct": r(100 * len(flagged) / len(target), 1),
        "all_tiles_excluded": sum(s[2] > cloud_max for s in seen),
        "all_tiles_excluded_pct": r(100 * sum(s[2] > cloud_max for s in seen) / len(seen), 1),
        "primary_clear_dates": len(clear_dates),
    }


def table1(q1, summ, tol, need, med_max, ps, adj):
    out = [
        "**Table 1**",
        "",
        "*Question 1: Agreement Between Automated Shadow Lengths and the Blinded Human Reference (N = 10 Tanks)*",
        "",
        "| Method | Passes | Pass rate (%) | *Mdn* abs. residual (m) | *M* abs. residual (m) | *M* signed residual (m) | *p* | Holm-adjusted *p* | Criteria met | Verdict |",
        "|:--|--:|--:|--:|--:|--:|--:|--:|:--|:--|",
    ]
    for i, m in enumerate(METHODS):
        s = summ[m]
        signed = st.mean(float(t[f"{m.lower()}_residual_m"]) for t in q1)
        rate_ok = float(s["pass_rate_pct"]) >= need
        med_ok = float(s["median_abs_residual_m"]) <= med_max
        out.append(
            f"| {m}: {METHODS[m]} | {s['pass_count']}/{s['eligible_tanks']} | {s['pass_rate_pct']} | "
            f"{s['median_abs_residual_m']} | {s['mean_abs_residual_m']} | {r(signed)} | "
            f"{apa_p(ps[i])} | {apa_p(adj[i])} | {'Yes' if rate_ok else 'No'} / {'Yes' if med_ok else 'No'} | {s['verdict']} |"
        )
    out += [
        "",
        f"*Note.* A tank passes when its absolute residual is at most {r(tol, 1)} m. Registered criteria: pass rate "
        f"≥ {r(need, 0)}% and median absolute residual ≤ {r(med_max, 1)} m (\"Criteria met\" lists rate / median). "
        "Signed residual is automated minus reference, so positive values are overestimates. *p* is a one-sided exact "
        f"binomial test of H~0~: pass probability ≤ {r(need / 100)}, Holm–Bonferroni adjusted across the three methods. "
        "The protocol names the correction but not the test statistic, so this test is a post hoc operationalization "
        "(Deviation 003 in `docs/deviations.md`); verdicts rest on the registered thresholds, not on *p*.",
    ]
    return "\n".join(out)


def table2(q2, cnr_min):
    out = [
        "**Table 2**",
        "",
        "*Question 2: Contrast-to-Noise Diagnostic for the Shadow Crescent at 10 m Resolution*",
        "",
        "| Tank | μ~crescent~ (DN) | μ~roof~ (DN) | Signed contrast (DN) | σ~noise~ (DN) | CNR | Status |",
        "|:--|--:|--:|--:|--:|--:|:--|",
    ]
    for t in q2:
        d = float(t["mu_crescent"]) - float(t["mu_roof"])
        out.append(
            f"| {t['tank_id']} | {t['mu_crescent']} | {t['mu_roof']} | {r(d, 1)} | {t['sigma_noise']} | "
            f"{t['contrast_to_noise_ratio']} | {t['diagnostic_status'].replace('FAIL_', 'Fail: ').replace('_', ' ').capitalize()} |"
        )
    out += [
        "",
        f"*Note.* CNR = |μ~crescent~ − μ~roof~| / σ~noise~, with σ~noise~ estimated from static paved surfaces beside the "
        f"tank farms. The registered detectability threshold is CNR ≥ {r(cnr_min, 1)}. Signed contrast is crescent minus "
        "roof; a shadow would be expected to make it negative. DN = digital number.",
    ]
    return "\n".join(out)


def table3(bounds, clear):
    out = [
        "**Table 3**",
        "",
        "*Physical Plausibility of Automated Estimates Against the Geometric Ceiling*",
        "",
        "| Method | Above ceiling | Within 0.1 m of ceiling | Anomalous fraction (%) |",
        "|:--|--:|--:|--:|",
    ]
    for m in METHODS:
        b = bounds[m]
        out.append(f"| {m}: {METHODS[m]} | {b['above']} | {b['at']} | {r(100 * b['above'] / b['n'], 1)} |")
    out += [
        "",
        f"*Note.* The ceiling for each tank is (*H* − {r(clear, 1)} m) / tan(α), with *H* the registry shell height and α "
        "the solar elevation of the acquisition. The protocol treats an extraction with more than 20% anomalous tanks as invalid.",
    ]
    return "\n".join(out)


def figure1(q1, lmax):
    n = len(q1)
    row, x0, x1, top = 36, 110, 750, 78
    height = top + row * n + 62
    sx = lambda m: x0 + (x1 - x0) * m / 30
    ink, muted = "#222222", "#555555"
    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 780 {height}" width="780" height="{height}" '
        'font-family="Arial, Helvetica, sans-serif" font-size="12" role="img">',
        "<title>Reference and automated shadow lengths in units of the 10 m pixel</title>",
        "<desc>For each of ten tanks, the blinded reference crescent length with a 3 m tolerance band, "
        "the three automated estimates, and the geometric ceiling.</desc>",
        f'<rect width="780" height="{height}" fill="#ffffff"/>',
    ]
    for b in range(3):
        fill = "#f0f0ec" if b % 2 else "#ffffff"
        s.append(f'<rect x="{sx(10 * b):.1f}" y="{top}" width="{sx(10) - sx(0):.1f}" height="{row * n}" fill="{fill}"/>')
    for i, t in enumerate(q1):
        yc = top + row * i + row / 2
        ref = float(t["reference_shadow_m"])
        if i:
            s.append(f'<line x1="{x0}" x2="{x1}" y1="{top + row * i}" y2="{top + row * i}" stroke="#e4e4e0"/>')
        s.append(f'<text x="{x0 - 10}" y="{yc + 4:.1f}" text-anchor="end" fill="{ink}">{t["tank_id"]}</text>')
        s.append(
            f'<rect x="{sx(ref - 3):.1f}" y="{yc - 15:.1f}" width="{sx(6) - sx(0):.1f}" height="30" fill="#c4cad0" opacity="0.6"/>'
        )
        c = sx(lmax[t["tank_id"]])
        s.append(f'<line x1="{c:.1f}" x2="{c:.1f}" y1="{yc - 15:.1f}" y2="{yc + 15:.1f}" stroke="#777" stroke-width="1.5" stroke-dasharray="3 2"/>')
        s.append(f'<line x1="{sx(ref):.1f}" x2="{sx(ref):.1f}" y1="{yc - 16:.1f}" y2="{yc + 16:.1f}" stroke="#111" stroke-width="2.5"/>')
        for m, dy in (("M1", -9), ("M2", 0), ("M3", 9)):
            cx, cy, col = sx(float(t[f"{m.lower()}_shadow_m"])), yc + dy, COLORS[m]
            s.append(marker(m, cx, cy, col))
    ybase = top + row * n
    s.append(f'<line x1="{x0}" x2="{x1}" y1="{ybase}" y2="{ybase}" stroke="{muted}"/>')
    for m in range(0, 31, 5):
        s.append(f'<line x1="{sx(m):.1f}" x2="{sx(m):.1f}" y1="{ybase}" y2="{ybase + 5}" stroke="{muted}"/>')
        s.append(f'<text x="{sx(m):.1f}" y="{ybase + 19}" text-anchor="middle" fill="{ink}">{m}</text>')
    s.append(
        f'<text x="{(x0 + x1) / 2:.0f}" y="{ybase + 42}" text-anchor="middle" fill="{ink}">'
        "Shadow crescent length along the solar azimuth (m); shading alternates every 10 m, the pixel width</text>"
    )
    lx = 20
    s.append(f'<line x1="{lx}" x2="{lx}" y1="22" y2="40" stroke="#111" stroke-width="2.5"/>')
    s.append(f'<text x="{lx + 8}" y="35" fill="{ink}">Reference</text>')
    s.append(f'<rect x="{lx + 88}" y="23" width="26" height="16" fill="#c4cad0" opacity="0.6"/>')
    s.append(f'<text x="{lx + 120}" y="35" fill="{ink}">±3 m tolerance</text>')
    for k, m in enumerate(METHODS):
        cx = lx + 250 + 70 * k
        s.append(marker(m, cx, 31, COLORS[m]))
        s.append(f'<text x="{cx + 10}" y="35" fill="{ink}">{m}</text>')
    s.append(f'<line x1="{lx + 480}" x2="{lx + 480}" y1="22" y2="40" stroke="#777" stroke-width="1.5" stroke-dasharray="3 2"/>')
    s.append(f'<text x="{lx + 488}" y="35" fill="{ink}">Geometric ceiling</text>')
    s.append("</svg>")
    return "\n".join(s)


def marker(m, cx, cy, col):
    if m == "M1":
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.5" fill="{col}" stroke="#fff" stroke-width="1.5"/>'
    if m == "M2":
        return f'<rect x="{cx - 4:.1f}" y="{cy - 4:.1f}" width="8" height="8" fill="{col}" stroke="#fff" stroke-width="1.5"/>'
    pts = f"{cx:.1f},{cy - 5:.1f} {cx - 5:.1f},{cy + 4:.1f} {cx + 5:.1f},{cy + 4:.1f}"
    return f'<polygon points="{pts}" fill="{col}" stroke="#fff" stroke-width="1.5"/>'


def main():
    tol, need = cfg("q1_tolerance_meters"), cfg("q1_min_pass_rate") * 100
    med_max, cnr_min = cfg("q1_max_median_absolute_residual"), cfg("q2_cnr_threshold")
    clear, cloud_max = cfg("physical_height_clearance_meters"), cfg("cloud_footprint_threshold_percent")

    q1, q2 = rows("results/q1_residuals_all_methods.csv"), rows("results/q2_contrast_diagnostics.csv")
    summ = {s["method_id"]: s for s in rows("results/q1_summary.csv")}
    man = rows("data/manual_readings_v2.csv")
    reg = {t["tank_id"]: t for t in rows("data/tanks/tank_registry.csv")}
    n = len(q1)

    # recompute from per-tank rows and make sure the summary file agrees
    for m in METHODS:
        k = m.lower()
        ab = [abs(float(t[f"{k}_residual_m"])) for t in q1]
        for t in q1:
            diff = float(t[f"{k}_shadow_m"]) - float(t["reference_shadow_m"]) - float(t[f"{k}_residual_m"])
            assert abs(diff) < 0.011, (m, t["tank_id"])
        assert sum(a <= tol for a in ab) == int(summ[m]["pass_count"]), m
        assert abs(st.median(ab) - float(summ[m]["median_abs_residual_m"])) < 0.006, m
        assert abs(st.mean(ab) - float(summ[m]["mean_abs_residual_m"])) < 0.006, m
    for t in q2:
        calc = abs(float(t["mu_crescent"]) - float(t["mu_roof"])) / float(t["sigma_noise"])
        assert abs(calc - float(t["contrast_to_noise_ratio"])) < 0.011, t["tank_id"]

    ks = [int(summ[m]["pass_count"]) for m in METHODS]
    ps = [upper_tail(k, n, need / 100) for k in ks]
    adj = holm(ps)

    elev = {float(x["sun_elevation_deg"]) for x in man}
    az = {float(x["sun_azimuth_deg"]) for x in man}
    assert len(elev) == 1 and len(az) == 1
    elev, az = elev.pop(), az.pop()
    lmax = {tid: (float(reg[tid]["height_meters"]) - clear) / math.tan(math.radians(elev)) for tid in reg}
    bounds = {}
    for m in METHODS:
        est = [(t["tank_id"], float(t[f"{m.lower()}_shadow_m"])) for t in q1]
        bounds[m] = {
            "n": n,
            "above": sum(v > lmax[i] + 0.005 or v < 0 for i, v in est),
            "at": sum(0 <= lmax[i] - v <= 0.1 for i, v in est),
        }

    a = [float(x["inspector_a_m"]) for x in man]
    b = [float(x["inspector_b_m"]) for x in man]
    ref = [float(t["reference_shadow_m"]) for t in q1]
    cnr = [float(t["contrast_to_noise_ratio"]) for t in q2]
    sig = [float(t["sigma_noise"]) for t in q2]
    radius = [float(t["radius_meters"]) for t in reg.values()]
    height = [float(t["height_meters"]) for t in reg.values()]

    nums = {
        "n_tanks": n,
        "tol": r(tol, 1), "need_pct": r(need, 0), "med_max": r(med_max, 1), "cnr_min": r(cnr_min, 1),
        "cloud_max": r(cloud_max, 0),
        "scene_date": man[0]["scene_date"], "product": man[0]["product_id"],
        "sun_elev": r(elev, 1), "sun_az": r(az, 1),
        "ref_min": r(min(ref), 1), "ref_max": r(max(ref), 1),
        "ref_px_min": r(min(ref) / 10, 1), "ref_px_max": r(max(ref) / 10, 1),
        "radius_min": r(min(radius), 0), "radius_max": r(max(radius), 0),
        "height_min": r(min(height), 1), "height_max": r(max(height), 1),
        "diam_px_min": r(2 * min(radius) / 10, 0), "diam_px_max": r(2 * max(radius) / 10, 0),
        "irr_mad": r(st.mean(abs(x - y) for x, y in zip(a, b))),
        "irr_r": r(st.correlation(a, b)).lstrip("0"),
        "irr_max_diff": r(max(abs(x - y) for x, y in zip(a, b))),
        "irr_agreed": sum(x["adjudication_status"] == "AGREED_MEAN" for x in man),
        "cnr_mean": r(st.mean(cnr)), "cnr_min_obs": r(min(cnr)), "cnr_max_obs": r(max(cnr)),
        "cnr_below": sum(c < cnr_min for c in cnr),
        "cnr_below_1": sum(c < 1.0 for c in cnr),
        "sigma_min": r(min(sig), 0), "sigma_max": r(max(sig), 0),
        "contrast_reversed": sum(float(t["mu_crescent"]) > float(t["mu_roof"]) for t in q2),
        "q1_methods_failed": sum(summ[m]["verdict"] == "FAIL" for m in METHODS),
    }
    for i, m in enumerate(METHODS):
        s, k = summ[m], m.lower()
        nums[f"{k}_pass"] = s["pass_count"]
        nums[f"{k}_rate"] = s["pass_rate_pct"]
        nums[f"{k}_median"] = s["median_abs_residual_m"]
        nums[f"{k}_mean"] = s["mean_abs_residual_m"]
        nums[f"{k}_p"] = apa_p(ps[i])
        nums[f"{k}_p_holm"] = apa_p(adj[i])
        nums[f"{k}_at_ceiling"] = bounds[m]["at"]
        nums[f"{k}_above_ceiling"] = bounds[m]["above"]
        res = [float(t[f"{k}_residual_m"]) for t in q1]
        nums[f"{k}_signed"] = r(st.mean(res))
        nums[f"{k}_over"] = sum(x > 0 for x in res)
    nums["median_min"] = min(summ[m]["median_abs_residual_m"] for m in METHODS)
    nums["median_max"] = max(summ[m]["median_abs_residual_m"] for m in METHODS)
    nums.update({f"cloud_{k}": v for k, v in cloud_numbers(cloud_max).items()})
    any_pass = sum(any(abs(float(t[f"{m.lower()}_residual_m"])) <= tol for m in METHODS) for t in q1)
    nums["tanks_any_pass"] = any_pass
    nums["tanks_none_pass"] = n - any_pass
    nums["oracle_rate"] = r(100 * any_pass / n, 1)
    drop = tol * math.tan(math.radians(elev))
    bbl = lambda rad: math.pi * rad**2 * 6.28981 / 1000
    nums["tol_roof_m"] = r(drop, 1)
    nums["kbbl_per_m_min"], nums["kbbl_per_m_max"] = r(bbl(min(radius)), 0), r(bbl(max(radius)), 0)
    nums["tol_kbbl_min"], nums["tol_kbbl_max"] = r(drop * bbl(min(radius)), 0), r(drop * bbl(max(radius)), 0)

    tables = {"table1": table1(q1, summ, tol, need, med_max, ps, adj), "table2": table2(q2, cnr_min), "table3": table3(bounds, clear)}
    for name, text in tables.items():
        (OUT / "tables" / f"{name}.md").write_text(text + "\n", encoding="utf-8")
    (OUT / "figures" / "figure1.svg").write_text(figure1(q1, lmax), encoding="utf-8")
    (ROOT / "results" / "paper_numbers.json").write_text(json.dumps(nums, indent=2) + "\n", encoding="utf-8")

    template = OUT / "paper_template.md"
    if template.exists():
        fill = {**{k: str(v) for k, v in nums.items()}, **tables}
        text = re.sub(r"\{\{(\w+)\}\}", lambda g: fill[g.group(1)], template.read_text(encoding="utf-8"))
        (OUT / "paper.md").write_text(text, encoding="utf-8")
    print("ok:", len(nums), "numbers,", len(tables), "tables, figure written")


if __name__ == "__main__":
    main()
