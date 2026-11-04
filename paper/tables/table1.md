**Table 1**

*Question 1: Agreement Between Automated Shadow Lengths and the Blinded Human Reference (N = 10 Tanks)*

| Method | Passes | Pass rate (%) | *Mdn* abs. residual (m) | *M* abs. residual (m) | *M* signed residual (m) | *p* | Holm-adjusted *p* | Criteria met | Verdict |
|:--|--:|--:|--:|--:|--:|--:|--:|:--|:--|
| M1: Single-band threshold (B04) | 3/10 | 30.0 | 6.71 | 6.12 | −3.81 | > .999 | > .999 | No / No | FAIL |
| M2: Multi-band spectral index | 1/10 | 10.0 | 8.09 | 7.38 | 7.38 | > .999 | > .999 | No / No | FAIL |
| M3: Sub-pixel radial gradient (B04) | 2/10 | 20.0 | 6.91 | 6.36 | −0.83 | > .999 | > .999 | No / No | FAIL |

*Note.* A tank passes when its absolute residual is at most 3.0 m. Registered criteria: pass rate ≥ 80% and median absolute residual ≤ 2.0 m ("Criteria met" lists rate / median). Signed residual is automated minus reference, so positive values are overestimates. *p* is a one-sided exact binomial test of H~0~: pass probability ≤ 0.80, Holm–Bonferroni adjusted across the three methods. The protocol names the correction but not the test statistic, so this test is a post hoc operationalization (Deviation 003 in `docs/deviations.md`); verdicts rest on the registered thresholds, not on *p*.
