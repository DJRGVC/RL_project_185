# Expert-Demonstration Replay Priority for Sparse-Reward SAC

## Abstract

Off-policy deep RL with sparse rewards is bottlenecked by replay sampling: the buffer is dominated by zero-reward transitions, and Prioritized Experience Replay (PER) provides little signal early in training when TD errors are uninformative. A separate line of work — demonstration-augmented RL — seeds the replay buffer with expert trajectories and shows improved sample efficiency, but typically conflates two mechanisms: *what* is in the buffer (the demonstrations themselves) and *how often* it is sampled (priority). We disentangle these on three sparse-reward MetaWorld manipulation tasks by comparing four variants of SAC that differ only in the replay-buffer policy: uniform, TD-error PER, demo-preloaded with uniform sampling, and demo-preloaded with the demonstrations pinned at fixed maximum priority. The first three are baselines drawn from the literature; the fourth isolates the priority mechanism. We report sample efficiency, asymptotic performance, and learning-stability metrics with bootstrap confidence intervals.

## Background

Soft Actor-Critic (Haarnoja et al., 2018) is the standard off-policy continuous-control algorithm, but its replay buffer treats every transition identically. Prioritized Experience Replay (Schaul et al., 2016) oversamples transitions by absolute TD error, with importance-sampling correction and annealed bias. In sparse-reward continuous control, however, the critic is randomly initialized and almost every transition has zero reward, so TD errors are near-uniform for tens of thousands of environment steps and PER's signal is weak in the regime that matters most.

Demonstration-augmented RL (DDPGfD, Vecerik et al., 2017; SACfD; DAPG, Rajeswaran et al., 2017) pre-loads expert transitions into the buffer. The literature attributes gains to two mechanisms simultaneously: the agent sees successful trajectories at all, and the agent sees them more often than random transitions. Most published implementations also assign elevated priorities to demonstration transitions, but rarely report the no-priority ablation, leaving the relative contribution of the two mechanisms unclear in the sparse-reward setting.

## Method

The base agent is SAC with twin critics, automatic temperature tuning, two-layer 256-unit MLPs, and a 1M-transition replay buffer. The reward is sparse — replaced by `float(success)` from the MetaWorld success indicator — so all variants face the same hard exploration problem. Variants differ only in the buffer:

- **uniform** — standard replay; every transition has equal sample probability.
- **per** — PER with α=0.6, β annealed 0.4→1.0 over training, priorities updated by `|TD error|` after each gradient step.
- **demo-replay** — buffer pre-loaded with K=10 expert episodes per task collected from MetaWorld's scripted policies, sampling uniform thereafter.
- **demo-priority** — same pre-load, but every demonstration transition is held at a fixed priority of 10× the default for the entire run; `update_priorities` skips demo indices, so the priority floor never decays.

Comparing **demo-replay** against **uniform** isolates the contribution of demonstration content; comparing **demo-priority** against **demo-replay** isolates the contribution of priority pinning at matched demonstration content. Comparing **per** against **uniform** quantifies the value of TD-error prioritization in the sparse-reward regime under our exact configuration.

## Hypotheses

**H1.** Demonstration content alone (demo-replay) improves sample efficiency over uniform replay in sparse-reward SAC on MetaWorld.

**H2.** Pinning demonstration priority (demo-priority) further improves sample efficiency over demo-replay at matched demonstration content, especially early in training.

**H3.** TD-error PER provides no meaningful benefit over uniform replay in this sparse-reward regime, because TD errors are uninformative before the agent finds reward.

## Experimental plan

**Sweep.** Three sparse-reward MetaWorld v3 manipulation tasks — `drawer-open-v3`, `sweep-into-v3`, `button-press-v3` — × four variants × five seeds = 60 SAC runs, each 500k environment steps, on Modal L4 GPUs. Total compute roughly 50 GPU-hours, ~$30. Evaluation every 10k steps over 10 episodes with greedy actions.

**Metrics.** Primary: environment steps to first crossing of three success thresholds (0.25, 0.5, 0.8), aggregated across seeds with bootstrap 95% confidence intervals. Secondary: final success rate at 500k steps; area under the success-rate curve; mean episode length on success. Tertiary (diagnostic): replay-buffer demo-sampling fraction, actor entropy, alpha, Q estimates, and gradient norms.

**Reproducibility.** Frozen dataclass config, fixed seed list, environment snapshot (Python/PyTorch/MuJoCo/MetaWorld versions, git SHA) recorded per run, summary JSON written atomically. Sweep dispatch and analysis pipeline are committed scripts (`modal_app.py::sweep`, `analyze.py`).

## Contingencies and contribution

If H1 holds and H2 holds, the contribution is a clean decomposition of the two demo-RL mechanisms with bootstrap confidence intervals on three matched tasks — disentangling content from priority. If H1 holds but H2 fails, the contribution is evidence that priority pinning offers nothing beyond seeding the buffer with successful trajectories, which would simplify how the demo-RL literature presents the method. If H1 fails on these tasks, the contribution is a documented negative result that constrains when demonstration-augmented RL helps. H3 is a side check that frames PER's expected ceiling in this regime; either outcome is informative.

## Relevance to deep RL

The proposal targets the replay-sampling decision that every off-policy deep RL implementation makes implicitly. It separates two mechanisms (what is in the buffer vs. how often it is sampled) that the demonstration-augmented RL literature has historically conflated, on a continuous-control benchmark where the sparse-reward exploration problem makes the choice load-bearing. The experimental protocol is fully self-contained: tiny MLPs, scripted-policy demos, no learned reward model, no foundation-model dependency.
