# Figure Audit — 15:12

**Figures inspected this pass:** all 18 PNGs in `agent_reports/figs/` (fig1_headline_success, fig2_differentiation_table, fig3_paths_status, fig4_averages, fig_morning_headline, figN2_cross_task_transfer, figN_c1v2_model_comparison, figN_c1v2_real_vs_synthetic, results_explainer_bars, results_explainer_mechanism, results_explainer_paths, results_explainer_push_climb, results_explainer_timeline, explainer_cf_her, explainer_family_tree, explainer_problem, explainer_semantic_per, explainer_verified_cf).

**One remaining issue found and fixed:** `figN_c1v2_model_comparison.png` had bold in-panel chart titles ("Plausibility" / "Specificity") placed via `ax.set_title()`. Despite the script comment claiming this was an improvement over old code, bold `ax.set_title()` calls still violate the NeurIPS guideline "No chart titles — move to figure caption." All other figures were either already NeurIPS-compliant data figures or are internal-presentation infographics not bound for the paper body.

**Fix applied:** In `agent_reports/make_figN_c1v2_comparison_v2.py`, replaced `ax.set_title(mlabel, fontsize=9, fontweight="bold", pad=4)` with `ax.set_xlabel(mlabel, fontsize=9)` and renamed the metric labels to panel-letter form `"(a) Plausibility"` / `"(b) Specificity"`. This places the panel discriminator at the x-axis label position (standard for multi-panel NeurIPS figures) rather than floating above the bars. Figure regenerated via `.venv/bin/python agent_reports/make_figN_c1v2_comparison_v2.py`; confirmed visually that bold titles are absent in the updated PNG and PDF.

**Status:** All 18 figures are now NeurIPS-compliant or are internal status infographics out of scope for the paper body.
