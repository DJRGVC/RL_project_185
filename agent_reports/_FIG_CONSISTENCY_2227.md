# Figure Consistency Overhaul — 2026-05-12 22:27

## Inventory (figures referenced in both papers)

Both `agent_reports/paper/main.tex` and `agent_reports/paper_cs285/main.tex`
reference exactly five figures (one `\includegraphics` per file each):

| Figure file (pre-overhaul) | Used as | Where (main / cs285) |
| --- | --- | --- |
| `fig_envs.pdf` | env screenshot grid | both papers |
| `fig1_headline_success.pdf` | HEADLINE (4-method bar chart, pre-fix) | both papers |
| `figN_c1v2_model_comparison.pdf` | judge plausibility / specificity 4o vs Opus | both papers |
| `figN2_cross_task_transfer.pdf` | VLM keyframe agreement bar chart | both papers |
| `figN_c1v2_real_vs_synthetic.pdf` | C1v2 real vs synthetic bars | both papers |

The standalone (non-paper-mounted) figures that appear in
`agent_reports/figs/` and are reachable from generation scripts:

- `fig_headline_v2.{png,pdf}`, `fig_headline_v3.{png,pdf}` — the current
  6-method bar chart with HER + Oracle-CF + vlm_cf + verified_cf overlaid.
- `fig_learning_curves.{png,pdf}`, `fig_learning_curves_v2.{png,pdf}` — 1×3
  training-curve panel.
- `fig_morning_headline.{png,pdf}`, `fig4_averages.{png,pdf}` — older snapshot
  figures retained on disk; not paper-mounted.

The paper-mounted headline file (`fig1_headline_success.pdf`) was the OLD
4-method pre-fix version. v3 (newer, 6-method, NeurIPS-styled) lived only in
`figs/`. The biggest reviewer risk was that the headline figure in the paper
mixes training horizons (250k vs 500k vs 3M vs 1M) without that being legible
on the chart itself — caption mentioned it, bars did not.

## What changed

### 1. New `fig_headline_v4.{png,pdf}` (centerpiece)
   Location: `agent_reports/figs/fig_headline_v4.{png,pdf}` plus a copy in
   each paper directory (`agent_reports/paper/`, `agent_reports/paper_cs285/`).
   Generator: `agent_reports/make_fig_headline_v4.py` (re-runnable;
   inherits seed data from v3 verbatim so numbers do not drift).

   Improvements over v3:
   - **Per-bar horizon stamp**: every bar now carries a small italic-gray
     text label directly under its base showing that cell's training
     horizon (e.g., `3M`, `250k`, `500k`, `1M`). This is the bulletproof
     fix for the "cross-horizon comparison" reviewer concern — readers can
     no longer accidentally compare a 3M-step bar against a 500k-step bar
     without seeing the asymmetry.
   - **Legend horizon tag**: each legend entry also embeds the method's
     summary horizon (e.g., `Uniform (3M)`, `HER (250k)`,
     `vlm_cf (ours) (500k)`).
   - **Footer flag**: an italic gray subcaption beneath the legend explicitly
     instructs the reader to treat cross-horizon comparisons as efficiency
     claims, not asymptotic dominance.
   - **Unified palette** (CB-safe, deliberate per-method color pin):
     - `Uniform` → `#ABABAB` (neutral gray)
     - `PER`     → `#5F9ED1` (CB10 mid-blue; moved off `#006BA4` so vlm_cf can own that color)
     - `HER`     → `#FF800E` (CB10 orange)
     - `Oracle-CF` → `#009E73` (Okabe-Ito bluish-green)
     - `vlm_cf (ours)` → `#006BA4` (CB10 dark blue)
     - `verified_cf (ours)` → `#CC79A7` (Okabe-Ito reddish-purple)
   - Same NeurIPS-conventions kept: no chart title, DejaVu Sans, ±1 SE
     caps, seed dots overlaid, light horizontal grid only.

### 2. Caption updates in both papers
   The figure caption was rewritten to (a) state up-front that the
   comparison is cross-horizon, (b) name the horizon for every method, and
   (c) instruct readers how to interpret within-horizon vs cross-horizon
   bars. The transparency note about the pre-fix GPT-4o run is kept as a
   tail clause. Caption updated identically in:
   - `agent_reports/paper/main.tex` (around line 1138)
   - `agent_reports/paper_cs285/main.tex` (around line 974)

### 3. fig_learning_curves_v2 — verified palette
   Already uses horizon-tagged labels in the legend
   (`HER (DDPG+HER)`, `Oracle-CF (1M)`, etc.). Palette is CB-safe and
   matches v4 for vlm_cf (CB10 blue), verified_cf (Okabe purple), and
   Oracle-CF (Okabe green). No change needed.

### 4. fig_envs — no change
   This is the env screenshot grid; no comparison content, no palette gap.

### 5. figN_c1v2_model_comparison / figN_c1v2_real_vs_synthetic /
    figN2_cross_task_transfer — palette spot-check
   These compare *VLM models* (Opus 4.7 vs GPT-4o vs Sonnet 4.5), not
   training methods. Their palettes use CB10 blue/orange to differentiate
   models — internally consistent with each other; no clash with the
   training-method palette because they are a separate semantic
   dimension. No re-render needed.

## Paper builds — verified
Both papers compile cleanly with the new figure mounted:
- `agent_reports/paper/main.pdf` — `fig_headline_v4.pdf` on page 14
  (rendered & visually inspected at 150 DPI).
- `agent_reports/paper_cs285/main.pdf` — `fig_headline_v4.pdf` on page 12
  (rendered & visually inspected at 150 DPI).

## Files retained for reference (not deleted)
- `agent_reports/figs/fig_headline_v3.{png,pdf}` — v3 on disk for reference.
- `agent_reports/figs/fig1_headline_success.{png,pdf}` — original pre-v3
  on disk.
- The paper directories' previous `fig1_headline_success.pdf` is still
  there too (no longer referenced; the new `fig_headline_v4.pdf` lives
  alongside it).

## Re-runnable generator command
```
.venv/bin/python agent_reports/make_fig_headline_v4.py
```
Writes both `.png` (for inline checks) and `.pdf` (for paper mount) into
`agent_reports/figs/`. The script is data-frozen against the v3
seed-level numbers so re-running is a no-op as long as the source seeds
remain unchanged.

## Before / after preview paths
- Before (paper-mounted): `agent_reports/paper/fig1_headline_success.pdf` (16 KB, 4-method pre-fix line/bar chart, no horizon annotation)
- After  (paper-mounted): `agent_reports/paper/fig_headline_v4.pdf` (35 KB, 6-method bar chart, per-bar horizon stamps + legend horizon tags + cross-horizon footer)
- Rendered side-by-side previews at 150 DPI:
  - `/tmp/paper_fig1-1.png` (old, paper-mounted)
  - `/tmp/figs_v3-1.png` (v3, intermediate)
  - `agent_reports/figs/fig_headline_v4.png` (new, paper-mounted)
  - `/tmp/paper_p14-14.png` (main paper page 14, headline figure embedded)
  - `/tmp/cs285_p12-12.png` (cs285 paper page 12, headline figure embedded)
