# Figure Audit — 2334

**Figure improved:** `agent_reports/figs/figN_c1v2_real_vs_synthetic.png` (+ PDF)

**Source script created:** `agent_reports/make_figN_c1v2_improved.py`

**What was changed and why:**

`figN_c1v2_real_vs_synthetic` was the weakest figure in the set: it had value annotations on every single bar (33 floating text labels in total), which directly violates the NeurIPS memory guideline "No value labels on bars unless they convey something axes can't show." With a y-axis already showing 0–1.0 in steps of 0.2, those labels conveyed nothing the axis did not already show and added significant visual noise. The figure was also 8.6 inches wide (non-standard), where the NeurIPS two-column width is 6.75 inches. All bar value labels were removed, the figure width was corrected to 6.75 in (height adjusted to 3.1 in to compensate and keep bar proportions reasonable), and the x-axis tick labels were shortened to "narr. / action / ag / all" to prevent crowding in the narrower panels. The improvement is a noticeably cleaner, more readable figure that matches the style of the other NeurIPS-compliant figures in the set (fig1, fig4, figN2).
