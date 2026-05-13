# VLM-CF p_counterfactual sweep — final success rates

Tag: `path_c_vlm_cf_psweep_2026-05-12`
Generated: 2026-05-13T06:54:24Z
Env: FetchPickAndPlace-v4   Horizon: 500k   Seeds: [42, 123, 999]

Final success rate = mean of last 5 eval points; SE computed across n_finished seeds (ddof=1).

| p     | n_finished/3 | mean SR | SE     | s42      | s123     | s999     |
|-------|--------------|---------|--------|----------|----------|----------|
| 0.00 | 3/3          |   0.330 |  0.045 | 0.240    | 0.370    | 0.380    |
| 0.10 | 2/3          |   0.320 |  0.110 | 0.210    | 0.140(running) | 0.430    |
| 0.25 | 3/3          |   0.327 |  0.107 | 0.200    | 0.240    | 0.540    |
| 0.50 | 1/3          |   0.250 |  0.000 | 0.250    | 0.170(running) | 0.090(running) |
| 0.75 | 0/3          |       — |      — | 0.040(running) | 0.060(running) | 0.110(running) |
| 1.00 | 0/3          |       — |      — | 0.070(running) | 0.020(running) | 0.080(running) |

**Best p (fully complete only):** p=0.00 with mean SR = 0.330 ± 0.045