**Table 3**

*Agreement With EIA Weekly Cushing Stocks on the Held-Out Test Period*

| Method | Tank source | *n* | *r* | *p* | 95% CI | ρ | *R*² | Δ lag 0 *r* [CI] | Δ lag 1 *r* [CI] |
|:--|:--|--:|--:|--:|:--|--:|--:|:--|:--|
| CNN | registry | 37 | 0.30 | .067 | [−0.08, 0.59] | 0.21 | −0.51 | −0.16 [−0.74, 0.26] | 0.05 [−0.54, 0.73] |
| CNN | yolo | 37 | 0.32 | .052 | [−0.05, 0.60] | 0.22 | −0.51 | −0.15 [−0.75, 0.31] | 0.06 [−0.55, 0.73] |
| Ridge (B04, B08, B11, sun) | registry | 37 | −0.33 | .050 | [−0.60, 0.04] | −0.27 | −0.24 | −0.31 [−0.70, 0.44] | −0.31 [−0.61, 0.64] |
| Ridge (B04, B08, B11, sun) | yolo | 37 | −0.33 | .045 | [−0.61, 0.04] | −0.29 | −0.24 | −0.33 [−0.71, 0.44] | −0.33 [−0.62, 0.65] |
| Ridge (day of year) | registry | 37 | 0.08 | .639 | [−0.39, 0.49] | 0.03 | −0.03 | 0.21 [−0.73, 0.91] | 0.20 [−0.84, 0.87] |
| Ridge (day of year) | yolo | 37 | 0.08 | .642 | [−0.39, 0.49] | 0.03 | −0.03 | 0.21 [−0.73, 0.91] | 0.20 [−0.84, 0.87] |
| Ridge (sun geometry only) | registry | 37 | −0.44 | .007 | [−0.73, −0.06] | −0.44 | −0.19 | −0.29 [−0.85, 0.68] | −0.25 [−0.87, 0.72] |
| Ridge (sun geometry only) | yolo | 37 | −0.44 | .007 | [−0.73, −0.06] | −0.44 | −0.19 | −0.29 [−0.85, 0.68] | −0.25 [−0.87, 0.72] |
| Training mean | registry | 37 | n/a | n/a | [n/a, n/a] | n/a | −0.02 | n/a | n/a |
| Training mean | yolo | 37 | n/a | n/a | [n/a, n/a] | n/a | −0.02 | n/a | n/a |

*Note.* Level statistics use weeks with a valid satellite pass. *p* is the naive Pearson test and ignores autocorrelation; intervals are stationary block bootstrap (mean block 4 weeks, 10000 draws). Δ columns use consecutive weeks only. Models were fit on 2021–2022 only.
