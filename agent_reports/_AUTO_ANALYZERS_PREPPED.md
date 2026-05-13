# Auto-analyzers prepped — morning workflow is 1 command away

Generated: 2026-05-13 ~06:55Z (overnight, Daniel asleep).
Branch: `agent/pathc-lead` (also pushed to `main`).

## TL;DR

Two zero-touch scripts have been added under `agent_reports/`.  Both are
**idempotent** and **graceful**: re-running is safe and they exit 0 when
the expected W&B runs aren't done yet.

| Script                                | Purpose                                  | When to run            |
|---------------------------------------|------------------------------------------|------------------------|
| `make_psweep_analysis.py`             | Aggregate p_counterfactual sweep + emit table + figure + paper paragraph | After p-sweep finishes (~06:00 PDT). Safe to run earlier. |
| `refresh_fig_headline_v6.py`          | Regenerate headline bar chart with HER@1M Push+Slide once all 9 runs finished | After HER@1M Push+Slide finishes (~04:30 PDT). |

## Morning workflow

```bash
cd ~/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185
source .venv/bin/activate
python agent_reports/make_psweep_analysis.py
python agent_reports/refresh_fig_headline_v6.py
```

If `refresh_fig_headline_v6.py` prints "NOT READY", just wait and re-run.

## Artifact map

### `make_psweep_analysis.py` outputs
- `agent_reports/_psweep_results.md` — table of p / mean SR / SE / per-seed
- `agent_reports/figs/fig_psweep.pdf` and `.png` — NeurIPS-style bar chart (single panel, 4.0 x 2.8 in, viridis CB-safe palette, seed dots overlaid)
- `agent_reports/_psweep_paragraph.tex` — paste-ready LaTeX prose

### `refresh_fig_headline_v6.py` outputs
- `agent_reports/figs/fig_headline_v6.pdf` and `.png` — drop-in replacement for v5 (only emitted once 9/9 HER@1M runs are finished)
- `agent_reports/_her_1m_seed_table.md` — provenance: per-env, per-seed final SR + W&B run names
- `agent_reports/_fig_headline_v6_state.json` — hash of HER values to support idempotent re-runs

The paper LaTeX is NOT touched.  Updating `\includegraphics{fig_headline_v5}`
to `fig_headline_v6` in `papers/*.tex` is the paper agent's call (or one
`sed`).

## Current state at hand-off (2026-05-13 06:55Z)

- **p-sweep**: 12/18 finished, 9 running.  Partial table already generated
  (`agent_reports/_psweep_results.md`).  Fully-complete cells: p=0.00 and
  p=0.25.  Best-so-far is essentially a three-way tie between p=0.00 /
  0.10 / 0.25 at ~0.33; p=0.50/0.75/1.00 are still in flight but the
  early reads suggest p=1.00 is the weakest cell (means 0.04–0.08 at
  whatever step they've reached).  This will firm up when all 18 finish.
- **HER@1M**: 3/9 finished (PnP done from earlier; Push and Slide still
  running).  Script correctly detects this and exits 0.
- **Wave B / matched-500k**: not touched here — these run separately, no
  morning-blocking analyzer needed yet (paper has placeholders for these
  results already).

## Style notes

Both figures follow `feedback_neurips_figures.md`: no chart titles, DejaVu
Sans 8–10pt, CB-safe palettes (viridis for the p-sweep gradient, Okabe-Ito
/ Tableau CB10 for the multi-method headline), error bars are mean ± SE
with caps, vector PDF + 300 dpi PNG, `bbox_inches="tight"`.

## Safety properties

1. **Idempotent**: rerunning produces identical bytes (up to W&B response
   timing); `refresh_fig_headline_v6.py` short-circuits via JSON state
   hash to avoid regenerating identical figures.
2. **Graceful**: every W&B call is wrapped in try/except and returns 0 on
   failure with a clear message.  Missing/partial cells render as
   placeholder bars or "n/3" annotations, never crash.
3. **Read-only on the paper**: neither script writes anywhere outside
   `agent_reports/`.
4. **No training launched**: scripts only query W&B.

## Files added in this session

```
agent_reports/make_psweep_analysis.py
agent_reports/refresh_fig_headline_v6.py
agent_reports/_psweep_results.md             # first dry-state output
agent_reports/_psweep_paragraph.tex          # first dry-state output
agent_reports/figs/fig_psweep.png            # first dry-state output
agent_reports/figs/fig_psweep.pdf            # first dry-state output
agent_reports/_AUTO_ANALYZERS_PREPPED.md     # this file
```

Note: the `_psweep_*` and `fig_psweep.*` outputs are checked in at the
12-runs-finished partial-data state — they'll be overwritten by the
morning re-run with full 18/18 data.
