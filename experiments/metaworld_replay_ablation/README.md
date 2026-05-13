# Auxiliary study — replay-mechanism ablation on MetaWorld

This subdirectory holds the code, configs, and results for an auxiliary
study referenced from the main paper's appendix
(see `agent_reports/paper/appendix.tex`, section
`Auxiliary Study: Replay-Mechanism Ablation on MetaWorld`, label
`app:metaworld`). It is intentionally separated from the rest of the
repository because it runs vanilla SAC on a different benchmark family
(MetaWorld v3) than the main paper's Fetch experiments and shares no
code with `../../src/`.

## What's here

- `proposal.md` — the original pre-registered proposal
  (hypotheses H1/H2/H3, experimental plan, contingencies).
- `results/README.md` — the post-hoc writeup with hypothesis outcomes,
  the PER-helps surprise, and the demo-replay/demo-priority
  implementation collapse.
- `results/efficiency.json` — per-task / per-variant statistics with
  bootstrap 95% CIs (final success, steps-to-{0.25,0.5,0.8}).
- `results/per_run.csv` — one row per run (60 rows).
- `results/manifest.json` — captured runtime metadata
  (environment snapshots, costs, missing runs).
- `results/figures/` — the three figures rendered by `analyze.py`
  (also copied into `agent_reports/paper/` as `fig_mw_*.png`).
- `src/` — SAC, replay buffer, demo loader, trainer, analysis.
- `train.py`, `analyze.py`, `modal_app.py`, `config.yaml`, `Makefile`,
  `pyproject.toml`, `uv.lock` — entry points and dependency lock.

## Reproducing

The sweep is `3 tasks × 4 variants × 5 seeds = 60` SAC runs at
500k env steps each (≈130.5 L4-GPU-hours on Modal, ≈\$104 at list
rate). See `proposal.md` §"Experimental plan" for the full setup and
`results/README.md` §7 "Compute and reproducibility" for the actual
run metadata.

```bash
# from this directory
uv sync                                # install deps from uv.lock

# Smoke (single seed, single task, single variant)
uv run python train.py --task drawer-open-v3 --variant uniform \
    --seed 0 --total_steps 20000

# Full sweep on Modal
uv run modal run --detach modal_app.py::sweep

# Aggregate and produce figures + tables
uv run python analyze.py --run_root output/
```

## Where this appears in the paper

- **Related Work** (`main.tex`, `\paragraph{Demonstration-augmented replay.}`)
  — motivates demo-augmented RL as the content-side counterpart to PER
  and surfaces the Schaul-max-priority equivalence observed here.
- **Discussion** (`main.tex`,
  `\paragraph{Cross-benchmark corroboration on MetaWorld.}`,
  label `sec:disc:metaworld`)
  — reports the headline cross-benchmark finding (PER >> uniform in
  sparse-reward SAC) and the demo-saturation boundary
  (easy tasks solved; `sweep-into-v3` not).
- **Appendix** (`appendix.tex`, label `app:metaworld`)
  — full setup, results table with bootstrap CIs, all three figures,
  the implementation-collapse code trace, and pre-registered follow-ons.
