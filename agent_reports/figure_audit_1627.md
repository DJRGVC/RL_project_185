# Figure audit — 16:27 — `fig_learning_curves`

## What I created
- `agent_reports/figs/fig_learning_curves.pdf` (vector)
- `agent_reports/figs/fig_learning_curves.png` (300 DPI raster)
- `agent_reports/figs/_fig_learning_curves_caption.txt` (3-line caption draft for next paper-iter to paste into main.tex)
- `agent_reports/make_fig_learning_curves.py` (re-runnable script; pulls live from W&B)

## Purpose
First proper NeurIPS-style learning-curve figure for the paper draft. Most NeurIPS RL papers carry one — we previously only had end-of-training bars. This shows `eval/success_rate` vs `global_step` for our three key conditions, faceted by Fetch env (Push, PnP, Slide).

## Data sources (W&B project `d-grant-uc-berkeley/RL_project`)
- **HER baseline** — 9 runs, tag `path_c_overnight_2026-05-11`, name prefix `path_c_kill_her_`, 3 envs × 3 seeds, 250k steps.
- **vlm_cf attempt 5** — 9 runs, name prefix `path_c_vlm_cf_`, `created_at > 2026-05-12T18:20:00Z`, 3 envs × 3 seeds, 500k steps.
- **Oracle-CF 1M PnP** — 3 runs, tag `oracle_cf_1m_pnp`, PnP only, 1M steps.

All 21 expected runs were retrieved (asserted). For each seed, history was pulled via `run.scan_history(keys=['global_step', 'eval/success_rate'])`. The `eval/success_rate` key has data for all 21 runs (no need to fall back to `charts/eval/success_rate`).

## Aggregation
Per (env, method) I interpolate each seed onto a common 300-point step grid (linear in step), then compute mean and SE = std(ddof=1)/sqrt(n_seeds) across seeds. Shaded bands are ±1 SE (matches §5 statistical methodology in the paper). For visual honesty, each seed's actual final-step value is overlaid as a small open dot.

## Style (NeurIPS, per ~/feedback_neurips_figures.md)
- 6.75 in wide × 2.4 in tall (two-column NeurIPS), 3-panel grid
- DejaVu Sans 9pt axis labels, 8pt ticks, 7.5pt legend
- Tableau Color Blind 10 palette: HER = gray (`#ABABAB`), vlm_cf = blue (`#006BA4`), Oracle-CF = Okabe-Ito green (`#009E73`)
- No chart titles. Env name appears as a small bold subtitle inside each axes' upper-left.
- Light horizontal grid only, top/right spines removed.
- Single legend in the PnP (middle) facet's lower-right corner — not duplicated.
- Saved vector PDF + 300 DPI PNG with `bbox_inches='tight'`.

## x-axis choice
Linear, not log. Linear is clearer for showing Oracle-CF's mid-training climb on PnP (the key story) and HER's flat plateau. Log would compress the 500k–1M region where Oracle-CF actually pulls away.

## Visual verification (post-render check)
Rendered the PDF to PNG at 120 DPI and inspected:
- Y range [0, 1] — yes
- All three facets visible with env subtitles — yes
- Shaded ±SE bands visible for all curves — yes
- HER (gray) truncates at 250k in every facet — yes (caption notes this)
- Oracle-CF (green) appears only in PnP, runs to 1M — yes
- vlm_cf (blue) covers all three envs to 500k — yes
- Per-seed final dots visible as open circles at each curve's right edge — yes
- Legend in one place only (PnP lower-right), readable — yes
- No chart title — confirmed

## Story the figure tells
- **FetchPush**: vlm_cf climbs sharply between 100k and 400k to ~0.95. HER starts climbing late at 200k and is truncated. vlm_cf clearly outperforms within its budget.
- **FetchPickAndPlace**: vlm_cf and HER both plateau low around ~0.2 within their budgets. Oracle-CF (green) is the standout — it climbs steadily through the second half of training to ~0.6 mean at 1M, with one seed reaching 0.9. This is the climb the caption highlights.
- **FetchSlide**: vlm_cf shows noisy mid-training climb to ~0.5 with one outlying low seed (0.2) at the end. HER plateaus near zero.

## Constraints honored
- Did not touch main.tex (next paper-iter cron will insert the figure).
- Did not touch any in-flight training.
- W&B auth via ~/.netrc.
- Used `.venv` (`source .venv/bin/activate`).
- Caption is in a sidecar `.txt` not on the figure itself.

## Re-run
```bash
source .venv/bin/activate
python agent_reports/make_fig_learning_curves.py
```
The script re-pulls from W&B each run (no caching), so it will pick up new HER/oracle/vlm_cf data automatically. The 21-run discovery is asserted; the script will fail loudly if any expected runs are missing.
