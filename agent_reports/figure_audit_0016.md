# Figure audit — 2026-05-12 00:16

**Figure improved:** `agent_reports/figs/figN_c1v2_model_comparison.{png,pdf}`

**Script written:** `agent_reports/make_figN_c1v2_comparison_v2.py`

## What was wrong (prior version)

The original figure (`build_c1v2_comparison.py` in `.claude/worktrees/agent-a5a0e661e4795fd08/scripts/`) had three NeurIPS-style violations: (1) `ax.set_xlabel()` was used to name the panel ("Plausibility" / "Specificity") — a semantic anti-pattern because `xlabel` should label the axis scale, not the panel, and it caused confusion when reading the figure independently of a caption; (2) x-tick labels ("narrative", "action", "achieved_goal", "all") had `rotation=15, ha='right'`, producing an untidy 15-degree slant — "achieved_goal" in particular ran into the bar grouping; (3) there were no per-episode data points, masking the very high within-variant variance (e.g. Opus 4.7 "achieved_goal" plausibility spread from ~0.15 to ~0.9 across 6 episodes), which is directly relevant to R1's concern about small-n claims.

## Improvements made

- Panel labels moved to `ax.set_title()` (bold, 9pt) and `ax.set_xlabel()` removed entirely.
- x-tick labels replaced with short abbreviations (`narr.`, `action`, `ag`, `all`) at `rotation=0` — no clipping, no slant.
- Per-episode score dots (n=6) overlaid on each bar with a small random jitter (seed=42) and white outlines for legibility; this makes the within-condition variance visible without adding any new data.
- Y-axis label updated to `"Judge score (mean ± SE, n=6 ep)"` so the sample size is self-documenting.
- NeurIPS two-column width (6.75 in) preserved; height bumped from 2.7 to 3.0 in to give the title row clearance.
- Horizontal gridlines only (explicit `grid(axis="x", visible=False)`).
