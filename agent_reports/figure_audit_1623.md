# Figure audit 16:23 PDT — fig_headline_v2

**Author:** FIGURE AGENT (Opus 4.7), 25-min budget run.

**Artifact:** `agent_reports/figs/fig_headline_v2.{png,pdf}` (NEW; existing
`fig1_headline_success.{png,pdf}` left untouched per brief).

**Script:** `agent_reports/make_fig_headline_v2.py` (re-runnable from project
root with `.venv/bin/python`).

**Caption draft:** `agent_reports/_fig_headline_v2_caption.txt`.

## What changed vs. fig1_headline_success

| Aspect | fig1 (existing) | fig_headline_v2 (new) |
|---|---|---|
| Methods | Uniform, PER, Semantic PER GPT-4o, Semantic PER Oracle | Uniform, PER, HER, Oracle-CF, **vlm_cf (ours)** |
| Source | 36-run README aggregate | Multi-source: 36-run + Phase-1 overnight + Oracle 1M + vlm_cf attempt-5 |
| Headline method | none specifically | vlm_cf in bright green (#2CA02C) — visually dominant |
| HER ref line | absent | per-env horizontal dashed at HER mean |
| Horizon annotation | absent | per-method horizon under x-axis (italic, small) |
| Seed dots | absent in fig1 | white-fill / dark-outline overlay on methods with per-seed data |

## Data provenance

- Uniform/PER per-env mean+SE: `make_plots_neurips.py` (unchanged 36-run aggregate, 3M steps).
- HER per-seed: `CODE-REVIEWER_handoff.md` line 71-74 table
  ([0.700, 0.450, 0.700] Push / [0.100, 0.050, 0.400] PnP /
  [0.200, 0.100, 0.250] Slide; Phase 1 overnight, 250k steps).
- Oracle-CF Push post-fix per-seed: `MORNING_REPORT_2026-05-12.md` line 125
  ([0.300, 0.250, 0.600], commit ccb63d4 rerun, 250k steps).
- Oracle-CF PnP 1M per-seed: brief, mean 0.583 from [0.30, 0.90, 0.55].
- Oracle-CF Slide per-seed: same Phase-1 overnight CODE-REVIEWER table
  ([0.200, 0.200, 0.150]).
- vlm_cf attempt-5 per-seed: `paper/main.tex` §5.6(C) lines 1535/1539
  ([1.00, 0.95, 0.90] Push / [0.35, 0.35, 0.50] PnP-in-flight /
  [0.25, 0.70, 0.70] Slide; 500k steps).

## SE computation

For methods with seed lists, SE = std(ddof=1) / sqrt(3). For Uniform/PER, SE is
preserved from the README 36-run aggregate (not recomputed).

## Visual verification

PDF rendered at 140 DPI via `pdftoppm`, inspected. Confirmed:
- No chart title (NeurIPS convention from memory file).
- 5 method colors with vlm_cf bright green standing out as headline.
- Error bars + seed dots visible, dots are white-fill with thin dark outline.
- HER reference dashed line drawn as a per-env segment, in legend.
- Legend below axes, ncols=4 — does not crowd bars.
- y-axis ticks every 0.2, range [0, 1.08].
- Horizon annotation appears as one compact italic gray line under x labels.
- Font: DejaVu Sans throughout.

## Known caveats / honest notes

1. **vlm_cf PnP is in-flight** (paper says ~60% of 500k budget, partial mean
   ~0.23 still rising). The brief instructed me to use the 0.35/0.35/0.50
   estimate (~0.40 mean) as the working number; this is flagged in the
   horizon string and should be re-rendered once the run completes. If
   the final number differs, edit `SEEDS[("vlm_cf (ours)", "FetchPickAndPlace")]`
   in `make_fig_headline_v2.py` and rerun.
2. **HER Push number reconciliation.** The CODE-REVIEWER table reports HER
   Push mean = 0.617 (mean of [0.700, 0.450, 0.700]); the MORNING_REPORT
   reports 0.550. The brief specified 0.617 as ground truth, so the
   CODE-REVIEWER seed values are used. Both numbers refer to the same Phase
   1 overnight runs; the discrepancy may be eval-criterion vs.
   best-checkpoint aggregation. Worth confirming with PATHC-LEAD before
   freezing the camera-ready figure.
3. **Oracle-CF row is "best available per env"** rather than a single
   coherent run-set. The horizon string "250k–1M" advertises this.
   Alternative: drop Oracle-CF entirely or split into Oracle-CF@250k and
   Oracle-CF@1M rows. Current single-row mixing is consistent with the
   brief instruction "combining best-available".
4. **Did not pull from W&B.** Brief authorized hardcoded values as fallback.
   All numbers are sourced from committed-to-disk markdown reports and the
   working tex file; no live W&B query was made. Re-pulling from W&B
   would primarily affect seed-level precision, not the qualitative ranking.
5. **Did not touch main.tex** (per brief; insertion is a separate agent's job)
   and **did not overwrite** `fig1_headline_success.{png,pdf}`.

## Suggested follow-ups

- Once vlm_cf PnP completes 500k, rerun the script (one-line dict edit).
- If PATHC-LEAD confirms HER Push = 0.550 is preferred, swap the seed list
  to the MORNING_REPORT triplet.
- Consider adding a small "in-flight" hatching style to vlm_cf PnP bar to
  visually distinguish completed-vs-in-progress estimates — currently no
  such cue is present.
