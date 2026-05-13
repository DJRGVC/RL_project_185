# Figure Audit 03:05 — figN2_cross_task_transfer

**Figure improved:** `agent_reports/figs/figN2_cross_task_transfer.{png,pdf}`
**Script edited:** `agent_reports/make_figN2.py`

**Problem identified:** The cross-task transfer bar chart (n=4 episodes per env) was missing per-episode jitter dots that every other bar chart in the paper now carries (fig1, fig4, figN_c1v2_model_comparison were all fixed in prior audits). With only 4 binary observations per cell (0 or 1 per episode), a bar + error-bar alone is highly misleading — two 0/1 patterns can yield identical means but completely different distributions. Additionally, the rcParams default `axes.grid: True` was leaking vertical gridlines through the bars, violating the memory guideline "Light horizontal gridlines only on bar charts; avoid heavy or vertical grid."

**Changes made:**
1. Collected per-episode boolean values for all three metrics (parse, judge, tolerant kf agreement) as `parse_dots`, `judge_dots`, `agree_dots` lists.
2. Added `ax.scatter(...)` overlays on each bar center with small uniform jitter (±0.06 width), white-filled circles with dark outlines (matching fig1/fig4 style), `zorder=5`, `clip_on=False`.
3. Replaced `ax.grid(axis="y")` with an explicit `ax.grid(False)` + `ax.yaxis.grid(True, ...)` pattern that suppresses any vertical grid bleed from rcParams.
4. Increased `ylim` top from 1.07 to 1.12 to give dots at y=1.0 clearance above bar tops.
5. PNG and PDF both regenerated via the venv.

**Result:** Dots at y=1 cluster visibly above bar tops; the two failing agreement episodes in FetchPush (y=0) are now visible as open circles at the baseline, making the variance structure immediately readable to a reviewer without inspecting the caption.
