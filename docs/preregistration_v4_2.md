# Pre-registration v4.2: three follow-up tests

Written and committed before any v4.2 run. Nothing below is changed after a result is seen. A bug fix is allowed only if it is disclosed next to the result.

## Why this exists, and what it is not

These tests are **post hoc**. They were chosen after two earlier results:

- v4.1 (walk-forward radar H3) came out PARTIAL. The level is tracked in the pooled 2020-2026 set but not in the primary set (2020-2022), where the weekly-change rule fails at lag 1.
- The first H2 run on spatial blocks passed its pre-set rule, but a diameter-only rule scored as well or better. Fixed-roof tanks here are small (median 35 m) and floating-roof tanks large (median 61 m), so size alone separates them.

The v4 verdict stays FAIL and the v4.1 verdict stays PARTIAL. v4.2 does not replace them. All three results below are reported, whatever they show. Three tests means three chances of a lucky pass; a single PASS counts as supporting evidence, not proof.

## Shared rules

- Labels: `roof_shape` in the registry, from `data/roofs/labels.csv`. One reader (Claude), no blind audit yet. "Fixed" includes tanks with an internal floating roof, which look closed from above. Tanks marked unsure are left out of every test.
- Split: `split_h2`, 1 km blocks, seeded, same as the first H2 run.
- No change to features, thresholds, windows, folds or alphas after seeing a result.
- One run each. The commands are in the last section.

## 1. Floating-roof-only radar H3 (walk-forward)

**Idea.** Only open floating roofs move up and down with the oil, so radar from fixed roofs adds noise.

**Method.** Exactly the v4.1 walk-forward (`src/ml/walkforward_radar.py`), but the hub value uses only tanks labelled `floating_roof`. Fixed and unsure tanks get zero weight. Nothing else changes: same features, folds (test years 2020-2026, at least 40 training weeks), rules A and B, placebo shifts and thresholds.

**Pass rules.** The same five as v4.1, on the primary set (2020-2022): level r >= 0.65 with p < .001 and CI > 0; both gap-difference CIs > 0; R-squared above both baselines; placebo; r positive.

**Status.** PASS if the primary set passes all five. PARTIAL if only the pooled 2020-2026 set does. Otherwise FAIL.

**Outputs.** `results/h3_radar_wf_float_*`. The prospective window (2026-11-01 to 2027-04-30) uses `prospective_float`, scored once, no earlier than 2027-05-01.

**Allowed claim if PASS or PARTIAL.** Radar from floating-roof tanks tracks EIA stocks at the level reported, in these folds. **Not allowed:** saying it beats the all-tanks version unless both numbers are shown side by side, or any claim about barrels per tank.

## 2. Size-controlled H2 (optical CNN, tanks up to 40 m)

**Idea.** Remove the size shortcut by testing only where sizes overlap.

**Method.** `src/ml/train_classifier.py 40`: the same CNN, ridge on band means, majority and diameter-rule baselines as the first H2 run, trained and tested only on tanks with diameter <= 40 m.

**Gate.** At least 20 tanks per class in train and 5 per class in held-out. If the gate fails, the result is NOT_TESTABLE and is reported as such.

**Pass rules.** Accuracy >= 0.85, macro F1 >= 0.80, macro F1 above the majority baseline, and macro F1 above the diameter rule.

**Outputs.** `results/h2_classification_metrics_band40.csv`, `h2_verdict_band40.json`, `h2_label_counts_band40.json`.

**Allowed claim if PASS.** The CNN separates open floating from fixed roofs among similar-sized tanks, on one reader's labels. **If FAIL or NOT_TESTABLE:** H2 is reported as "separable by size in this site; not shown beyond size".

## 3. Radar H2 (Sentinel-1 roof type)

**Idea.** An open floating roof changes radar return as the roof rises and falls; a fixed roof barely does.

**Method.** `src/ml/h2_radar.py`. Per tank, the mean and standard deviation over time of the four radar features (disc mean VV, disc max VV, disc mean VH, disc-minus-rim VV), per orbit then averaged by pass count. Tanks need at least 30 passes. Ridge on a plus/minus one target, alpha from {0.1, 1, 10, 100} by stratified 5-fold CV on training tanks only. Baselines: majority and diameter rule.

**Primary test:** tanks up to 40 m. **Secondary:** all tanks (reported, with the size confound stated beside it).

**Gate.** Same as section 2.

**Pass rules.** Same as section 2.

**Outputs.** `results/h2_radar_metrics.csv`, `h2_radar_verdict.json`.

**Allowed claim if PASS.** Radar level and variability carry roof-type information beyond size. **Not allowed:** a combined radar-plus-optical claim; that test is not registered.

## What counts as a failure of the plan

- A test that cannot run (gate fails, files missing) is reported as not testable, never silently dropped.
- If a result looks wrong and a bug is found, the fix and the before/after numbers are both reported.

## Run order

1. Commit this file and the code.
2. `.\.venv\Scripts\python.exe -m pytest tests -q`
3. `.\.venv\Scripts\python.exe -m src.ml.walkforward_radar run_float`
4. `.\.venv\Scripts\python.exe -m src.ml.train_classifier 40`
5. `.\.venv\Scripts\python.exe -m src.ml.h2_radar`
6. Commit the results.
