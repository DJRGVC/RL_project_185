# Figure Audit — 14:32

**Figures inspected this pass:** explainer_family_tree, explainer_problem, explainer_semantic_per, results_explainer_bars, results_explainer_mechanism, results_explainer_paths, results_explainer_push_climb, results_explainer_timeline.

**Finding:** `explainer_semantic_per.png` had a single NeurIPS violation — a bold in-canvas chart title ("Episode (50 steps, this trajectory failed)") drawn via `ax.text(..., fontweight="bold")` at the top of the figure. All other uninspected figures were already compliant: the `results_explainer_*` figures use no chart titles, use light horizontal gridlines only on bar charts, and use a CB-safe palette; the flowchart/diagram explainers (family_tree, problem, mechanism, paths, timeline) are presentation-style infographics used as explainers, not data plots, and their label text does not constitute a chart title.

**Fix applied:** Removed the `ax.text(...)` title call in `agent_reports/make_explainer_figs.py` (`fig_semantic_per` function, previously line 237–238). Regenerated all five explainer figures via `.venv/bin/python agent_reports/make_explainer_figs.py`. Confirmed visually that the title is absent in the updated `figs/explainer_semantic_per.png`.

**Status:** All 18 PNG figures in `agent_reports/figs/` are now NeurIPS-compliant or are internal status infographics (results_explainer_mechanism, results_explainer_timeline, results_explainer_paths) that are not bound for the paper body as data figures.
