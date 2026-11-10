# Pre-registration v4.3: per-tank weights and exact-date EIA matching

Written and committed before any v4.3 run. Nothing below changes after a result is seen. A bug fix is allowed only if it is disclosed next to the result.

## Why this exists

These tests are **post hoc**. v4.1 (walk-forward radar H3) came out PARTIAL: the level is tracked, but the weekly-change rule fails at lag 1 on the primary set (2020-2022). v4.2 (floating-roof-only hub) came out PARTIAL as well, with almost no change, so fixed-roof noise is not the cause. v4.3 tries two other causes. The v4 verdict stays FAIL, v4.1 stays PARTIAL and v4.2 stays PARTIAL. v4.3 does not replace them.

## Cleanup first (registered deviation, Note 011)

Registry rows 136, 142 and 219 are bare ground, not tanks. They are flagged `bare_ground = 1` (not deleted). v4.3 gives them zero weight in both models. v4, v4.1 and v4.2 results are frozen and were not recomputed. The YOLO model for H1 was not retrained.

## Change 1: per-tank learned weights

**Idea.** The hub model averages tanks by area, so every tank counts the same way. Tanks differ: some respond strongly to their fill level, some barely, some in the opposite direction.

**Method.** For each fold, take every kept tank's four deviation features (disc mean VV, disc max VV, disc mean VH, disc-minus-rim VV, relative to the tank's own training baseline for the same orbit), averaged by EIA week. Fit one ridge regression of EIA stocks on all tanks' features together (about 1,600 columns), on the training weeks only. Missing cells are set to zero after standardising; z-scores are clipped to plus or minus 5. The penalty comes from {1, 10, 100, 1,000, 10,000} by 5-fold contiguous blocked CV on the training weeks. Folds, minimum training weeks (40), valid-fraction rule (0.5 of area weight seen on a pass) and test windows are exactly those of v4.1. No new radar features are extracted.

**Comparison model.** The v4.1 hub model, run on the same cleaned tank set in the same run. All numbers for both models are reported.

## Change 2: exact-date EIA matching (rule C)

**Idea.** Rules A and B interpolate EIA between Fridays to the pass date. That smooths weekly changes and may weaken the difference test.

**Method.** Keep only passes within one day of an EIA reporting Friday and use that Friday's reading with no interpolation. Differences are taken between consecutive kept passes 5 to 14 days apart (lag 0: same interval; lag 1: next interval), as in rule B. This is run for both models.

**Power warning.** Only a fraction of passes fall near a Friday, so the sample is smaller. A wide interval is a power problem, not evidence against radar.

## Pass rules and status

- **Status** (decided on the per-tank model with rules A and B, exactly as v4.1): five rules on the primary set (2020-2022): level r >= 0.65, p < .001 and CI > 0; both gap-difference CIs > 0; R-squared above both baselines; placebo; r positive. PASS if the primary set passes all five; PARTIAL if only the pooled 2020-2026 set does; otherwise FAIL.
- **Exact-date check** (reported, not part of the status): both rule-C difference CIs > 0, for each scope and each model.
- **Improved over v4.1** means: the per-tank status ranks higher than the hub model's status in this same run (FAIL < PARTIAL < PASS). Nothing else counts as an improvement.

## Allowed claims

- If the per-tank status is PASS: radar tracks Cushing stocks, level and weekly changes, in these folds. The prospective window still decides.
- If the status is not higher than the hub's: per-tank weights add nothing here. Say that.
- If rule C passes and rules A and B do not: weekly changes are visible when EIA is matched on the exact day, with the smaller sample stated.
- **Not allowed:** claims about barrels per tank; picking the better of the two models after the fact; tuning alphas, clipping or the one-day window after seeing results.

## Prospective window

2026-11-01 to 2027-04-30, per-tank model only, scored once, no earlier than 2027-05-01 (locked in code). Registered now: if v4.3 is not improved over the hub model, the prospective test uses the hub model of v4.1 instead and the per-tank model is dropped.

## Outputs

`results/h3_radar_v43_pertank_*` and `results/h3_radar_v43_hub_*` (metrics, weekly, passes, verdict).

## Run order

1. Commit this file and the code.
2. `.\.venv\Scripts\python.exe -m pytest tests/ml -q`
3. `.\.venv\Scripts\python.exe -m src.ml.walkforward_v43`
4. Commit the results.
