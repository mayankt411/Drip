# Pre-registration v4.1: Walk-Forward Test of the Sentinel-1 Radar Model

Written 2026-11-10, before any v4.1 number exists. Commit this file first; the git commit is the timestamp.
Plan only: no code is run until this file is committed and the code matches it.

## 1. Why this test exists

The v4 radar study (frozen model, trained 2018–2022) gave, against EIA Cushing stocks:

| Window | Weeks | r (level) | R² | First-difference r (lag 0 / 1) | Verdict |
|---|--:|--:|--:|--|--|
| 2023-01 to 2024-06 | 42 | 0.944 | 0.795 | 0.70 / 0.72 (10 pairs, CI includes 0) | Fail |
| 2024-07 to 2026-10 | 68 | 0.680 | 0.185 | 0.20 / 0.06 (21 pairs, CI includes 0) | Fail |

Level tracking held on a fresh window; weekly changes were not shown. No untouched window is left, so v4.1 uses
(a) years the radar model was fitted on but never scored (2020–2022) and (b) a prospective window that does not exist yet.
v4.1 does **not** replace the v4 verdict. v4 stays "Fail" in every report.

## 2. Honest disclosure of what was already seen

- The model class, the four features and the pass rule were fixed before the 2023–2026 results and are unchanged here.
- The changes in Section 4 (A, B) were chosen after seeing that the v4 first-difference test had too few pairs.
- 2023–2026 results are already known, so they count only as secondary evidence.
- 2020–2022 weeks were used for fitting but never scored. They are the primary test.

## 3. Design (frozen)

**Model.** Same as v4: for each tank and orbit, subtract that tank's mean over the fold's training passes; area-weighted
hub average of four features (disc mean VV, disc max VV, disc mean VH, disc-minus-rim VV, all in dB); weekly average;
ridge regression with alpha from {0.01, 0.1, 1, 10, 100} chosen by 5-fold blocked cross-validation inside the training weeks.
No feature, alpha grid or window change after this file is committed.

**Folds (expanding window, past only).** Test years 2020, 2021, 2022, 2023, 2024, 2025, 2026 (to the last EIA week available).
Each fold trains on all weeks before its test year. A fold with fewer than 40 training weeks is reported as not scored.
Tank baselines are recomputed from each fold's training passes only.

**Baselines (per fold, same weeks):** training mean; day-of-year harmonics fitted on the fold's training EIA weeks.

## 4. Evaluation rules

**Unchanged from v4 (reported for every fold and pooled):** weekly units, EIA matched to the nearest Friday (at most 3 days), strict
consecutive-week differences.

**A. Date-matched target (new).** For pass-level scoring, EIA is interpolated linearly between the two Fridays around each pass date.

**B. Gap-tolerant differences (new).** Differences are taken between consecutive observed pass-days that are 5 to 14 days apart,
and the EIA change is taken over the same interval. Lag 1 compares the radar change with the next interval's EIA change.

**Primary test set:** pooled out-of-sample predictions for the 2020, 2021 and 2022 folds.
**Secondary:** pooled 2020–2026; each fold alone; the v4 windows.

**Pass rule (all must hold on the primary set):**
1. Level Pearson r ≥ 0.65, naive p < .001, and a stationary-block-bootstrap 95% interval (mean block 4, 10,000 draws) above zero.
2. Gap-tolerant first-difference correlation at lag 0 and lag 1: bootstrap interval above zero for both.
3. Pooled R² above the pooled R² of both baselines.
4. Placebo: r at true alignment must exceed the 95th percentile of |r| when EIA is shifted by every whole number of weeks from ±13 to ±52.
5. r must be positive. No sign flipping.

**Claiming a pass:** all five on the primary set. A pass on the secondary set only is reported as "partial".

## 5. What is not allowed after this commit

Changing features, alpha grid, thresholds, windows or fold definitions; dropping tanks, passes or weeks after seeing where the model misses;
smoothing either series; choosing among model variants on test weeks. A code bug fix is allowed only if disclosed with the before-and-after numbers.
Variants (large tanks only, radar plus season) are reported but never used for the verdict.

## 6. Prospective window

Frozen v4 model (trained 2018–2022). Weeks from 2026-11-01 to 2027-04-30, scored once, no earlier than 2027-05-01, with the same pass rule
(A and B included). Reported whatever it shows.

## 7. How results will be described

| Outcome | Claim allowed |
|---|---|
| All five rules pass on 2020–2022 | "Radar tracks Cushing stocks level and changes on previously unscored years" (and then the prospective window decides) |
| Level and baselines pass; differences fail | "Radar tracks the level, not weekly changes" |
| Level fails | "The 2023–2026 result did not generalise to 2020–2022" |
| Placebo fails | "The alignment is not distinguishable from chance" |

## 8. Known limits

Training for the 2020 fold is only 2018–2019. The 2021 drawdown to 26 million barrels from 59 may fall outside the 2018–2019 range.
Sentinel-1B stopped in December 2021, so pass density changes across folds. EIA covers the whole hub; the registry covers mapped tanks only.
Roof types are unlabelled.
