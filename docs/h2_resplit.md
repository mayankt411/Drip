# H2 re-split and test plan

Written 2026-11-10, before the H2 classifier was run on the new split. Commit this file first; the commit is the timestamp.

## Why

H2 asks whether Sentinel-2 chips separate floating-roof from fixed-roof tanks. OpenStreetMap has no roof tags, so labels were read
from aerial imagery (Esri World Imagery crops), 413 tanks: 338 floating, 64 fixed, 11 unsure (unsure tanks are excluded).
The original split is by terminal cluster. It puts 1 fixed-roof tank in training and 63 in the held-out cluster, so the classifier
cannot be trained (gate: 20 per class in training, 5 per class held out). The original split stays as it is for H1 and H3.

## Disclosures

- The split rule below is chosen after the label counts were known, so H2 is a post hoc test. It is reported as such.
- The labels come from one reader (an AI model) looking at contact sheets, not from OpenStreetMap. Agreement with a blind human
  sample (30 tanks, `src.ml.roofs check`) is reported next to the result.
- "Fixed" means a closed roof seen from above. An internal floating roof sits under a fixed roof and reads as fixed.
- Three registry entries (136, 142, 219) show bare ground and are labelled unsure.
- Spatial blocks are 1 km wide, so neighbouring blocks on different sides can share terrain and sun conditions. This is weaker
  than the original terminal split.

## Split rule (frozen)

1. Blocks are 1 km grid cells on UTM coordinates (`x_utm`, `y_utm`). A block goes whole to one side.
2. Blocks are shuffled with the project seed (7). In that order, a block with fixed-roof tanks goes to the side that holds fewer
   fixed-roof tanks so far; any other block goes to the side that holds fewer tanks.
3. The result is stored in a new `split_h2` column. `split` is not changed. One seed, no retries.

## Test (unchanged from the existing H2 code)

- Train on `split_h2 == train`, test on `split_h2 == heldout`, same chips and dates as before (train dates 2021 to 2022, test dates 2023
  to June 2024), 5 seeds, class-weighted loss, validation drawn from training tanks.
- Baselines: majority class, ridge on band means.
- Pass: accuracy at least 0.85 and macro F1 at least 0.80 (framework targets), and macro F1 above the majority guess.
  Floating roofs are about 80% of tanks, so accuracy alone is not enough.
- Reported either way: counts per class and split, confusion matrix, the ridge comparison, and the label agreement figure.

## Not allowed after this commit

Changing the block size, seed, assignment order, chips, model, thresholds or label file after seeing the result.
Re-labelling tanks because the model misses them. A code bug fix is allowed only if disclosed with before-and-after numbers.

## What each outcome allows us to say

| Outcome | Claim |
|---|---|
| Pass | "Sentinel-2 chips separate open floating from fixed roofs on held-out spatial blocks (post hoc split)" |
| Fails, ridge about equal | "No evidence the roof type is readable at 10 m beyond band means" |
| Fails, CNN at majority level | "Roof type is not readable at 10 m with this model" |
