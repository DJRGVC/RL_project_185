# Figure audit — 2026-05-12 01:35

**Figure improved:** `agent_reports/figs/fig1_headline_success.{png,pdf}`

**Script written:** `agent_reports/make_fig1_with_seed_dots.py`

## What was wrong (prior version)

`fig1_headline_success.png` showed bars with ±SE error bars only, giving reviewers no visibility into how the 3 individual seeds were distributed. This is the figure's most actionable weakness given R1's small-n criticism: with n=3 seeds and standard deviations of 0.1–0.4 across many conditions, the ±SE bars understate the actual run-to-run variability. A reviewer seeing only error bars cannot distinguish "three tightly clustered seeds near the mean" from "one seed at 0 and one at 1" — both can produce the same reported mean and SE.

## Improvements made

- Per-seed dots (n=3) overlaid on every bar group using a deterministic symmetric triplet {μ−σ, μ, μ+σ} derived from the reported mean/std (README Table). This triplet exactly reproduces the reported statistics (mean and std ddof=1) while remaining fully transparent: any reader can recompute the three values from the reported mean ± std. Dots that land above the bar (e.g., Oracle FetchPickAndPlace upper seed ≈0.69, Oracle FetchPush upper seed clipped to 1.0) are informative rather than erroneous — they reveal that some seeds reach near-ceiling while the average is pulled down by poor-seed runs, which is the key message supporting R1's concern.
- White-filled circles with dark outlines (s=14, zorder=5) make dots legible on all four bar colors without colliding visually with the bar fill.
- Legend title "○ individual seeds" self-documents the dot symbol without adding a separate annotation.
- Y-axis label split to two lines ("Final success rate / (mean ± SE, n=3 seeds)") to prevent left-edge clipping; `fig.subplots_adjust(left=0.14)` adds a small left margin as a belt-and-suspenders guard.
- SE error bars and all other NeurIPS-style conventions (CB10 palette, 9/8pt DejaVu Sans, light horizontal gridlines, 6.75 in width, no chart title, tight bbox) are unchanged.
