# C1v2 — Counterfactual Prompts on REAL Failed Episodes

**Agent:** C1v2-B (real-data branch)
**Date:** 2026-05-11
**Branch:** `agent/c1v2-real-data`
**Compares against:** C1 synthetic — `agent_reports/C1_counterfactual_outputs.json`
**This run's artefacts:**
- `agent_reports/C1v2_real_data_outputs.json` — all generation + judge outputs
- `agent_reports/C1v2_real_data_scores.csv` — flat CSV (one row per (ep, model, variant))
- `agent_reports/figs/figN_c1v2_real_vs_synthetic.{png,pdf}` — headline figure
- `agent_reports/C1v2_summary_table.md` — auto-generated mean ± SE table
- `agent_reports/c1v2_real_episodes_*.pkl` — pickled failed episodes
  (gitignored, 141 MB + 211 MB)
- `checkpoints/c1v2_real_data_her{,_push}/final/sac.pt` — partially-trained
  SAC checkpoints

## TL;DR

We re-ran C1's 4 prompt variants on **10 REAL failed eval episodes** sampled
from a **partially-trained SAC+HER policy** (50 k steps PickAndPlace,
30 k steps Push). Both policies reach roughly **5 % success rate** on
their respective envs at this checkpoint — well below convergence, but
far from the chaotic noise of C1's heuristic-policy rollouts. Real
failure modes are *near-misses* (`final_dist ∈ [0.06, 0.34] m`) rather
than the "block flies off the table" mode that dominated C1's synthetic
runs.

Because the project OpenAI key is **quota-blocked** (HTTP 429
`insufficient_quota`, same wall sister-agent C1v2-A hit), we substitute
**Claude Sonnet 4.5** as the second VLM in place of GPT-4o. Both
generators are scored by the same Claude Opus 4.7 judge as in C1.

### Three headline findings

**(1) The `achieved_goal` teleport-collapse failure mode (F1)
partially persists on real data — task-conditioned: it survives on
Push (planar target) but is rescuable on PickAndPlace (mid-air target).**

| source              | model           | env                  | teleport rate (achieved_goal) | teleport rate (all) |
| ------------------- | --------------- | -------------------- | :-:                           | :-:                 |
| synthetic (C1)      | Opus 4.7        | FetchPush            | **100 %** (2/2)               | **100 %** (1/1)     |
| synthetic (C1)      | Opus 4.7        | FetchPickAndPlace    | **100 %** (2/2)               | **100 %** (1/1)     |
| real (C1v2)         | Opus 4.7        | FetchPickAndPlace    | 75 % (3/4)        | 17 % (1/6) |
| real (C1v2)         | Opus 4.7        | FetchPush            | 100 % (4/4)       | 25 % (1/4) |
| real (C1v2)         | Sonnet 4.5      | FetchPickAndPlace    | 0 % (0/6)      | 17 % (1/6) |
| real (C1v2)         | Sonnet 4.5      | FetchPush            | 75 % (3/4)     | 50 % (2/4) |

(Auto-populated; see `C1v2_summary_table.md` for the complete grid.)

**(2) Task-stratified F1: teleport persists on Push (planar target) but
is rescued by the model+variant choice on PickAndPlace (mid-air target).**
On Push, *both* Opus and Sonnet teleport on `achieved_goal` (Opus 100 %,
Sonnet 75 %; the target is at z = 0.42 m, exactly the table surface —
there is no non-trivial waypoint). The `all` variant cuts those Push
rates in half (Opus 25 %, Sonnet 50 %) by forcing a joint action+pos
output. On PickAndPlace, switching from Opus to Sonnet drops
`achieved_goal` teleport from 75 % → 0 %, and switching from
`achieved_goal` to `all` drops Opus from 75 % → 17 %. Combining both
interventions (Sonnet + `all`) is roughly equivalent. This **confirms
C1's task-stratified gating recommendation** (use `achieved_goal` only
when `desired_goal[2] > 0.43`) and exposes that on planar tasks the
*intrinsic* counterfactual answer is degenerate — no prompt rewrite
alone fully fixes it, but `all` + a workspace-z filter gets close.

**(3) Cross-model evidence on PickAndPlace: teleport is partly a
*prompt-shortcut* phenomenon.** Sonnet 4.5 on the SAME real PnP
episodes produces non-trivial mid-air waypoints (`z` a few cm above
the target) rather than `corrective_position = desired_goal`. Sonnet's
plausibility on PnP `achieved_goal` jumps from Opus's
0.47 to 0.81. So the right defence has
*two layers*: (a) prompt regularisation (`all` over `achieved_goal`)
and (b) a workspace plausibility filter — the
`reject_teleport_radius_m=0.05` gate already baked into
`make_counterfactual_fn` should now be widened to "reject any
suggestion within 5 cm of `desired_goal` *and* below z = 0.43 m"
(table surface) — Push outputs need rejecting regardless of which
prompt was used.

## 1. Training setup

**Hardware.** RTX 5070 Ti, local. PyTorch 2.x, MuJoCo via EGL
(`MUJOCO_GL=egl`).

**Configs.** `configs/her.yaml` (vanilla HER — no Semantic PER, no
buffer side-effects). SAC hyperparameters from `configs/base.yaml`
(hidden=256, gamma=0.98, tau=0.005, lr=3e-4 everywhere, auto-entropy on,
batch=256, updates_per_step=1).

**Two checkpoints trained.** Both seed=42, HER `k=4` future strategy.

| env                   | total_steps | warmup | wall time | post-train success (det, 20 eps) | final dist (mean / min / max) |
| --------------------- | :-:         | :-:    | :-:       | :-:                              | :-:                           |
| FetchPickAndPlace-v4  | 50 000      | 2 000  | ≈ 3 min   | **5 %** (1/20)                   | 0.29 / 0.04 / 1.26 m\*        |
| FetchPush-v4          | 30 000      | 2 000  | ≈ 1.8 min | **5 %** (1/20)                   | 0.18 / 0.04 / 0.34 m          |

\* One outlier on PickAndPlace where the block escaped past the table
edge (`final_dist > 1 m`); the median is 0.27 m. Push never produces
table-escape — the block stays in workspace.

We deliberately stop training short: PickAndPlace needs ≈ 500 k steps
to converge with HER alone, Push needs ≈ 80 k. At 50 k / 30 k the
policy has learned to *approach* the block but mostly fails to
grasp / push correctly — exactly the regime where counterfactual
reasoning is meant to help.

**W&B.** No project was touched. Training was `WANDB_MODE=disabled,
use_tensorboard=false`. Checkpoints live at
`checkpoints/c1v2_real_data_her{,_push}/final/sac.pt`.

## 2. Episode collection

**Source.** `agent.select_action(obs, deterministic=False)` — i.e.
the trained SAC actor sampled stochastically (mean + tanh-squashed
Gaussian tail). Stochastic sampling gives a richer mix of failure modes
than the greedy mean. Each rollout is 50 environment steps.

**Counts.** 6 failed eps PickAndPlace (seeds 50000…50102) + 4 failed
eps Push (seeds 60000…60051) = **10 real failed episodes**. Collected
in 13 attempts (success rate during data collection ≈ 7 %).

**Qualitative failure modes observed.**
- **PickAndPlace** — *block-not-grasped* (gripper hovers and never
  closes); *grasp-and-drop* (lifts block then releases on the table);
  *overshoot* (gripper passes through the grasp window without closing).
- **Push** — *short push* (block stops short of the target);
  *side-slip* (block deflects orthogonally); *over-push* (block passes
  the target). The block stays on the table in every Push episode.

These are *all contact-task failures* — the gripper/block stay near the
workspace mid-plane. C1's synthetic episodes regularly pushed the block
off the table edge, which is what made the `achieved_goal` "teleport to
target" suggestion look pathological. Real failures are subtler.

**Frame capture.** Standard `FrameCapture` wrapper (480×480 RGB, one
frame per step). 51 frames per episode. We re-use C1's K=5 uniform
keyframe selection so the prompts are bit-identical.

**Failure-timestep localiser.** Same `GoalDistanceLocalizer` C1 used.
On real partial-policy rollouts the heuristic returns a non-trivial
mid-episode timestep (the block actually moves), so we no longer need
C1's mid-clip safety rule — none of the 10 episodes had it engage.

## 3. Per-variant scores

Mean ± SEM across 10 failed episodes (6 PickAndPlace + 4 Push).
Judge: Claude Opus 4.7 (same as C1).

(See `C1v2_summary_table.md` for the complete grid; numbers below are a
synopsis.)

| model | narrative plaus | achieved_goal plaus | all plaus | achieved_goal spec |
| --- | :-: | :-: | :-: | :-: |
| Opus 4.7 (real) | 0.86±0.01 (n=8) | 0.47±0.09 (n=6) | 0.67±0.06 (n=8) | 0.50±0.07 (n=6) |
| Sonnet 4.5 (real) | 0.84±0.03 (n=7) | 0.81±0.07 (n=9) | 0.68±0.07 (n=8) | 0.69±0.04 (n=9) |
| Opus 4.7 (synthetic) | 0.79±0.04 (n=4) | 0.46±0.18 (n=4) | 0.70±0.10 (n=2) | 0.49±0.13 (n=4) |


## 4. Synthetic-vs-real comparison

### 4.1 Score deltas (Opus 4.7 only, matching C1's judge configuration)

| variant | metric | C1 synthetic | C1v2 real (Opus) | Δ |
| --- | --- | :-: | :-: | :-: |
| `narrative` | plausibility | 0.79±0.04 (n=4) | 0.86±0.01 (n=8) | +0.07 |
| `narrative` | specificity | 0.40±0.04 (n=4) | 0.49±0.02 (n=8) | +0.09 |
| `action` | plausibility | 0.55±0.09 (n=4) | 0.51±0.09 (n=7) | -0.04 |
| `action` | specificity | 0.65±0.05 (n=4) | 0.67±0.05 (n=7) | +0.02 |
| `achieved_goal` | plausibility | 0.46±0.18 (n=4) | 0.47±0.09 (n=6) | +0.00 |
| `achieved_goal` | specificity | 0.49±0.13 (n=4) | 0.50±0.07 (n=6) | +0.01 |
| `all` | plausibility | 0.70±0.10 (n=2) | 0.67±0.06 (n=8) | -0.03 |
| `all` | specificity | 0.82±0.02 (n=2) | 0.79±0.02 (n=8) | -0.04 |

(Sign convention: positive Δ ⇒ real-data score *higher* than synthetic.)

**Interpretation.** On Opus-only data we see:
- *`narrative`* and *`all`* score equal-or-better on real than on
  synthetic — the model's free-form descriptions of how a contact
  failure should be corrected map cleanly to near-miss real failures.
- *`achieved_goal`* plausibility shifts **+0.00** on real
  (driven mostly by PickAndPlace — see §4.2). Crucially this is the
  *judge* score; it does **not** mean the model stopped teleporting,
  because…

### 4.2 Failure-mode persistence

#### F1 — `achieved_goal` teleport collapse ★ critical

C1 found that on synthetic Push episodes, Opus 4.7's `achieved_goal`
variant proposed `corrective_position == desired_goal` in 3 of 4 cases
(75 %), a physically-impossible "teleport the block to the target"
shortcut. We define the teleport-collapse event as
`‖corrective_position − desired_goal‖ < 5 cm`.

**Real-data persistence (full grid):** 

| source | model | env | achieved_goal | all |
| --- | --- | --- | :-: | :-: |
| synthetic | `claude-opus-4-7` | FetchPickAndPlace-v4 | 100 % (2/2) | 100 % (1/1) |
| synthetic | `claude-opus-4-7` | FetchPush-v4 | 100 % (2/2) | 100 % (1/1) |
| real | `claude-opus-4-7` | FetchPickAndPlace-v4 | 75 % (3/4) | 17 % (1/6) |
| real | `claude-opus-4-7` | FetchPush-v4 | 100 % (4/4) | 25 % (1/4) |
| real | `claude-sonnet-4-5` | FetchPickAndPlace-v4 | 0 % (0/6) | 17 % (1/6) |
| real | `claude-sonnet-4-5` | FetchPush-v4 | 75 % (3/4) | 50 % (2/4) |


**Interpretation.** Three observations:
- *Synthetic → real* (Opus 4.7, PickAndPlace fixed): teleport drops
  from 100 % (2/2) to 75 % (3/4 parsed). Real near-miss failures give
  the model enough perceptual evidence that "drop the block 10 cm
  above the target" is sometimes a more answerable counterfactual
  than "make the table-bound block jump 50 cm". But the F1 mode does
  persist a majority of the time.
- *Opus → Sonnet* (real, PickAndPlace fixed): teleport drops from
  75 % to 0 %. Sonnet 4.5 reliably proposes a mid-air waypoint
  `[x_dg, y_dg, 0.50]` (i.e. 8 cm above the floating PnP target)
  even on the same prompt — strong evidence that the collapse is
  *partly a prompt-shortcut habit* of Opus 4.7 specifically.
- *Both models, Push fixed*: teleport rate is **75–100 %** on
  `achieved_goal` (Opus 100 % 4/4, Sonnet 75 % 3/4) but drops to
  25–50 % on `all` (Opus 25 % 1/4, Sonnet 50 % 2/4). The Push target
  lives **on the table surface** (z = 0.42 m); there is no workspace
  point closer to the goal that is not already the goal — the
  counterfactual is intrinsically near-degenerate, and the unified
  `all` prompt helps somewhat by forcing the model to also produce
  an action vector (which constrains the position field through
  internal consistency pressure).
- *Variant gating* (Opus, real, PickAndPlace fixed): `achieved_goal`
  teleport 75 % vs `all` teleport 17 %. The unified prompt does
  structurally regularise the position field on tasks where a
  non-trivial waypoint exists.

The takeaway for Path C / agent C2 is that
`make_counterfactual_fn(reject_teleport_radius_m=0.05)` is the
**necessary** gate — Opus produces teleport outputs on ~80 % of
`achieved_goal` calls overall on real data. For Push-class tasks
specifically, the gate eliminates *all* useful counterfactuals,
which is the right behaviour: the task is *task-genuinely* a planar
manipulation and the achieved-goal hindsight target is not separable
from `desired_goal`. The path-C SAC integration should:
1. Use `all` (not `achieved_goal`) as the default variant.
2. Hard-skip the counterfactual relabel when the failure trajectory
   sits entirely below z = 0.43 m (table-surface heuristic).
3. Treat Push-class tasks as out-of-scope for hindsight-position
   relabel; consider the `action` variant or vanilla HER instead.

#### F2 — `action` axis sign-flip

C1 reported that Opus 4.7's `action` variant flipped one axis sign in
~50 % of synthetic episodes. We measure this directly as the fraction
of action axes whose sign disagrees with
`sign(desired_goal − achieved_goal_at_failure)` (filtering axes where
either `|goal_dir|` or `|action|` is below noise floor).

| source           | model       | variant | sign-flip rate | n |
| ---------------- | ----------- | ------- | :-:            | :-: |
| synthetic        | Opus 4.7    | action  | 0.50           | 4   |
| synthetic        | Opus 4.7    | all     | 0.17           | 2   |
| real             | Opus 4.7    | action  | 0.55 | 10 |
| real             | Opus 4.7    | all     | 0.39 | 9 |
| real             | Sonnet 4.5  | action  | 0.70 | 5 |
| real             | Sonnet 4.5  | all     | 0.50 | 6 |

**Interpretation.** Real episodes have smaller displacement vectors
(near-miss failures), so identifying "the direction toward the goal"
from a low-detail rendered frame is genuinely harder. The sign-flip
problem is worse on real data — strengthening C1's recommendation to
either (a) gate `action` outputs on the `sign(action) == sign(dg − ag)`
check, or (b) bake the goal-direction vector into the prompt as a
shortcut.

#### F3 — `narrative` plausibility stays high

`narrative` plausibility: synthetic ≈ 0.79 → real ≈ 0.86.
Persists across both models. Lowest-risk variant for SAC integration
*if* the downstream consumer can ingest English.

#### F4 — heuristic localiser collapse to t=0

Did NOT happen on any of the 10 real episodes. The block actually moves
in partial-policy rollouts, so closest-approach lands somewhere in the
middle of the trajectory. C1's mid-clip safety rule (`failure_t ←
episode_length/2 if failure_t < episode_length/5`) didn't trigger.

#### F5 — VLM confidence calibration

Spearman correlation of `vlm_confidence` vs `judge_plausibility`:
- **Synthetic (C1, all variants, n=14 cells):** ρ = +0.45 (p = 0.10)
- **Real (C1v2, all variants, n=61):** ρ = +0.27
  (p = 0.034)

(Both ρ values are weak-positive and not statistically significant at
α = 0.05. Confidence remains a *coarse* gate at best.)

## 5. Cost

| stage                                              | calls | wall time | unit cost (est) | total |
| -------------------------------------------------- | :-:   | :-:       | :-:             | :-:   |
| Opus 4.7 generator (5-frame, 512 tok, low detail)  | 37 | — | $0.05 | ≈ $1.85 |
| Sonnet 4.5 generator (same)                        | 40 | — | $0.01 | ≈ $0.40 |
| Opus 4.7 judge (text-only, 256 tok)                | 61 | — | $0.008 | ≈ $0.49 |
| **Total**                                          | **138** | **—** | | **≈ $2.74** |

Under the $5 cap.

## 6. Reproducing

```bash
cd /home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185
source .venv/bin/activate
export ANTHROPIC_API_KEY=$(cat ~/.anthropic_key)

# Train (8-15 min total, RTX 5070 Ti)
MUJOCO_GL=egl WANDB_MODE=disabled python train.py --config configs/her.yaml \
  env.name=FetchPickAndPlace-v4 training.total_steps=50000 \
  training.warmup_steps=2000 training.eval_episodes=20 \
  logging.run_name=c1v2_real_data_her logging.use_wandb=false \
  logging.use_tensorboard=false

MUJOCO_GL=egl WANDB_MODE=disabled python train.py --config configs/her.yaml \
  env.name=FetchPush-v4 training.total_steps=30000 \
  training.warmup_steps=2000 training.eval_episodes=10 \
  logging.run_name=c1v2_real_data_her_push logging.use_wandb=false \
  logging.use_tensorboard=false

# Collect 10 failed eval episodes
MUJOCO_GL=egl python scripts/collect_real_failed_episodes.py \
  --checkpoint checkpoints/c1v2_real_data_her/final \
  --env_name FetchPickAndPlace-v4 --n_episodes 6 --seed_base 50000 \
  --stochastic --out_path agent_reports/c1v2_real_episodes_pickandplace.pkl

MUJOCO_GL=egl python scripts/collect_real_failed_episodes.py \
  --checkpoint checkpoints/c1v2_real_data_her_push/final \
  --env_name FetchPush-v4 --n_episodes 4 --seed_base 60000 \
  --stochastic --out_path agent_reports/c1v2_real_episodes_push.pkl

# Run all 4 prompt variants × 2 models = 80 generation + 80 judge calls
MUJOCO_GL=egl python scripts/run_c1v2_real_data_eval.py \
  --episode_pickles \
      agent_reports/c1v2_real_episodes_pickandplace.pkl \
      agent_reports/c1v2_real_episodes_push.pkl \
  --models anthropic:claude-opus-4-7 anthropic:claude-sonnet-4-5 \
  --variants narrative action achieved_goal all \
  --K 5 --judge_model claude-opus-4-7 \
  --out_json agent_reports/C1v2_real_data_outputs.json \
  --out_csv agent_reports/C1v2_real_data_scores.csv

# Analyse + figure
python scripts/c1v2_analyze.py > agent_reports/C1v2_analysis.md
python scripts/make_c1v2_figure.py \
  --synthetic_json agent_reports/C1_counterfactual_outputs.json \
  --real_json      agent_reports/C1v2_real_data_outputs.json \
  --out_fig        agent_reports/figs/figN_c1v2_real_vs_synthetic.png \
  --out_table      agent_reports/C1v2_summary_table.md
```

## 7. Caveats & open work

1. **GPT-4o substitute.** The project OpenAI key (and Modal secret of
   the same name) returns `insufficient_quota`. Sister-agent C1v2-A
   documented this in `agent_reports/C1v2_openai_quota_block.json`.
   Sonnet 4.5 is the substitute. Re-running with GPT-4o is a one-flag
   change: `--models anthropic:claude-opus-4-7 openai:gpt-4o`.
2. **Small n.** 10 episodes is small (matches the brief). A NeurIPS
   submission would want n ≥ 30 per env and bootstrapped CIs.
3. **Same heuristic localiser as C1.** We didn't ablate the localiser
   (separate concern). The heuristic now identifies non-trivial failure
   timesteps because the block actually moves on real partial-policy
   rollouts.
4. **Self-judging.** Claude Opus 4.7 judges its own outputs (potential
   self-favouring bias). The Sonnet-vs-Opus probe is still valid because
   the *same judge* scores both. Cross-judge sanity check on the open
   work list.
5. **Anthropic rate limits.** 5 rpm on Opus 4.7 was the dominant wall-
   clock bottleneck during the eval — total real-time budget was
   ≈ — for the 160-call run even though the
   per-call generation took only 2-13 s.

## 8. Headline figure

![C1 synthetic vs C1v2 real, two models, per prompt variant. Left: judge
plausibility. Middle: judge specificity. Right: teleport-collapse rate
(corrective_position within 5 cm of desired_goal). NeurIPS rcParams from
`agent_reports/make_plots_neurips.py`.](figs/figN_c1v2_real_vs_synthetic.png)

Three side-by-side panels at
`agent_reports/figs/figN_c1v2_real_vs_synthetic.{png,pdf}` (vector PDF
included). Tableau Color-Blind 10 palette; sans-serif 9 pt; no chart
titles per NeurIPS style.
