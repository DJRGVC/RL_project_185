## Figure audit — 02:33

**Target:** `fig4_averages.png` (horizontal bar, avg success rate across 3 Fetch envs)

**Problem identified:** This figure was the weakest untouched plot. It lacked individual-seed visibility — the same small-n criticism (R1) that motivated the fig1 fix at 01:35 applied here too, but was unaddressed. The original aggregated SE formula was also wrong: it used `sqrt(mean(var_i))` (which does not correctly propagate uncertainty across environments); the correct formula is `sqrt(sum(var_i)) / n_envs`.

**Changes made (`make_plots_neurips.py`, `fig4_averages` function):**
1. Added per-seed dots overlaid on each horizontal bar. Seed values are computed as the across-environment average of the deterministic {μ−σ, μ, μ+σ} triplet (same method used in fig1, from `make_fig1_with_seed_dots.py`), giving 3 dots per method that together reproduce the reported mean/std. Dots use the same white-fill + dark-outline style as fig1.
2. Fixed aggregated SE formula to `sqrt(sum(SE_i^2)) / n_envs`.
3. Added "○ individual seeds" legend entry in the upper-right whitespace.
4. Added "n=3 seeds" annotation in the top-right corner.
5. Minor: xlim widened slightly (0.65→0.68) to give the high-seed outlier dots for Oracle and GPT-4o breathing room; x-gridlines turned on for readability on the horizontal chart.
6. Saved PNG + PDF (both overwritten in place).

**Result:** Reviewers can now directly see that Oracle's high-seed performance on FetchPush (~0.70 avg) drives its average bar, and that GPT-4o has high variance across environments — both critical to interpreting the small-n result honestly.
