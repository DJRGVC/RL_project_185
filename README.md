# Semantic Failure Localization for Prioritized Experience Replay

**CS 285: Deep Reinforcement Learning, UC Berkeley, Spring 2026**  
**Team: Parshawn Gerafian, Matei Gardea, Daniel Grant**

---

## Table of Contents

1. [Overview](#overview)
2. [Motivation](#motivation)
3. [Research Hypothesis](#research-hypothesis)
4. [The Algorithm: SAC](#the-algorithm-sac)
5. [Replay Buffer Strategies](#replay-buffer-strategies)
6. [Failure Localization Methods](#failure-localization-methods)
7. [Environments](#environments)
8. [Implementation Details](#implementation-details)
9. [Design Decisions and Iterations](#design-decisions-and-iterations)
10. [Results](#results)
11. [Failure Timestep Analysis](#failure-timestep-analysis)
12. [Why FetchSlide Reversed](#why-fetchslide-reversed)
13. [Key Findings](#key-findings)
14. [Project Structure](#project-structure)
15. [Setup](#setup)
16. [Running Experiments](#running-experiments)
17. [Config Reference](#config-reference)
18. [References](#references)

---

## Overview

This project investigates whether a **Vision-Language Model (VLM)** — specifically GPT-4o — can improve reinforcement learning sample efficiency by identifying the causal failure moment in failed robotic manipulation episodes and boosting the replay priority of those transitions.

We implement and compare four replay buffer strategies on top of **Soft Actor-Critic (SAC)** across three **Gymnasium-Robotics Fetch** environments, running 3 seeds × 4 methods × 3 environments = **36 full training runs** (1M steps each) on Modal A10G GPUs.

| Method | Localizer | Description |
|---|---|---|
| **Uniform** | — | All transitions sampled with equal probability |
| **PER** | — | Transitions weighted by TD-error (Schaul et al. 2015) |
| **Semantic PER (GPT-4o)** | GPT-4o vision | PER + VLM-identified failure boosting |
| **Semantic PER (Oracle)** | Ground-truth geometry | PER + heuristic failure boosting using simulator state |

---

## Motivation

Off-policy RL algorithms like SAC learn from a replay buffer — a pool of past (state, action, reward, next_state) tuples. The simplest strategy is uniform sampling: every transition is equally likely to be replayed. **Prioritized Experience Replay (PER)** improves on this by sampling transitions proportional to their TD-error — the agent revisits experiences it currently finds surprising.

But TD-error is a *local* signal. A transition at timestep 12 that caused the failure at timestep 47 will have a low TD-error at t=12 (the consequence hasn't been observed yet) and a high TD-error at t=47 (where nothing useful can be learned). PER tends to focus on the *consequences* of failures rather than the *causes*.

**Our insight:** A VLM can look at the entire episode as a sequence of keyframes and pinpoint the causal failure moment — the timestep where the robot made the critical mistake. Boosting replay priority around that moment shifts training toward the decisions that actually matter.

This approach is inspired by how humans review failures: we watch the tape, identify the decisive moment, and practice that specific scenario rather than replaying the whole episode uniformly.

---

## Research Hypothesis

> After each failed episode, a VLM can identify the critical causal failure timestep from sampled keyframes. Boosting replay priority multiplicatively around that timestep — while preserving PER's TD-error signal — should improve sample efficiency over TD-error prioritization alone, especially on tasks where sparse rewards make TD-error uninformative.

**Revised hypothesis (after iteration):**
> Semantic PER underperforms PER on FetchPush because GPT-4o cannot reliably localize failures in abstract MuJoCo renders, and the original additive blending formula suppresses PER's signal when the VLM is wrong. With multiplicative blending and ground-truth failure localization (oracle), Semantic PER can exceed PER on average across all environments.

---

## The Algorithm: SAC

We use **Soft Actor-Critic** — an off-policy, maximum entropy deep RL algorithm designed for continuous action spaces.

### Why SAC?

- **Off-policy**: Learns from stored past experience (the replay buffer), making it compatible with PER and Semantic PER. On-policy algorithms like PPO or GRPO discard past experience and cannot use replay buffers.
- **Maximum entropy**: Maximizes reward *plus* policy entropy, encouraging natural exploration without ε-greedy or manual exploration schedules.
- **Sample efficient**: Reuses experience via the replay buffer, critical for robot manipulation tasks where environment steps are expensive.

### The Objective

Standard RL maximizes cumulative reward. SAC maximizes:

```
J(π) = Σ E[ r(s_t, a_t) + α × H(π(·|s_t)) ]
```

where `H` is the entropy of the policy and `α` is a learned temperature parameter. Higher `α` → more exploration. `α` is automatically tuned to hit a target entropy of `-action_dim`.

### Network Architecture

| Network | Input | Output | Architecture |
|---|---|---|---|
| Actor | observation (31d) | mean + log_std of Gaussian (8d each) | 2-layer MLP, ReLU, hidden=256 |
| Critic 1 | observation + action (39d) | Q-value (scalar) | 2-layer MLP, ReLU, hidden=256 |
| Critic 2 | observation + action (39d) | Q-value (scalar) | 2-layer MLP, ReLU, hidden=256 |

We use **twin critics** (two independent Q-networks) and take `min(Q1, Q2)` as the target to prevent overestimation bias (clipped double Q-learning).

### Update Loop

Every environment step after warmup (10k steps):

```
1. Sample batch of 256 transitions from replay buffer (weighted by priority)

2. Critic update:
   a. Compute target: y = r + γ × (min(Q1', Q2')(s', ã') - α × log π(ã'|s'))
      where ã' ~ π(·|s') (reparameterization trick)
   b. Minimize: L_critic = MSE(Q1(s,a), y) + MSE(Q2(s,a), y)
   c. Clip gradients: max_norm=1.0

3. Actor update:
   a. Maximize: E[min(Q1,Q2)(s, ã) - α × log π(ã|s)]
   b. Clip gradients: max_norm=1.0

4. Alpha update:
   a. Minimize: E[-α × (log π(a|s) + target_entropy)]
   b. target_entropy = -action_dim

5. Soft update target critics:
   θ' ← τ × θ + (1 - τ) × θ'    (τ = 0.005)

6. Update replay priorities with new TD-errors
```

**Gradient clipping** (`max_norm=1.0`) was added after observing critic loss explosions (critic_loss > 1000) early in training. This stabilizes learning under high importance-sampling weights from PER.

### Hyperparameters

| Parameter | Value |
|---|---|
| Hidden dim | 256 |
| Learning rates (actor, critic, alpha) | 3e-4 |
| Gamma (discount) | 0.98 |
| Tau (polyak) | 0.005 |
| Batch size | 256 |
| Updates per step | 1 |
| Warmup steps | 10,000 |
| Buffer capacity | 1,000,000 |
| Total steps | 1,000,000 |
| Eval interval | 5,000 steps |
| Eval episodes | 20 |

---

## Replay Buffer Strategies

### 1. Uniform Replay

A ring buffer of capacity 1M. Transitions are pushed in FIFO order and sampled with equal probability (`np.random.randint`). All importance-sampling weights are 1.0. This is the baseline — no prioritization.

### 2. Prioritized Experience Replay (PER)

Implements Schaul et al. (2015) with a **SumTree** data structure:

- **SumTree**: Binary tree where leaves store transition priorities and internal nodes store sums. Enables O(log N) priority updates and O(log N) stratified sampling.
- **Priority**: `p_i = (|δ_i| + ε)^α` where `δ_i` is the TD-error, `ε=1e-6` prevents zero priority, `α=0.6` controls prioritization strength.
- **Stratified sampling**: Splits total priority into `batch_size` equal segments, samples one transition per segment — ensures full coverage of the priority distribution.
- **Importance sampling**: Corrects sampling bias via `w_i = (N × p_i / Σp)^(-β)`, with `β` annealing from 0.4 → 1.0 over 500k steps.

After each SAC gradient step, priorities are updated with the new TD-errors.

### 3. Semantic PER

Extends PER with a `_semantic_weight` array (one float per buffer slot, initialized to 1.0). After the VLM or oracle identifies `failure_t` for a failed episode:

```python
# Apply semantic boost to window around failure
for t in [failure_t - 5 ... failure_t + 5]:
    _semantic_weight[t] = semantic_boost  # 10.0
```

**Priority blending (multiplicative):**

```python
final_priority[t] = TD_priority[t] × _semantic_weight[t]
```

The multiplicative formula is critical. When the VLM is wrong, `_semantic_weight` stays at 1.0 for those transitions (no boost applied) and TD-priority is unchanged. This degrades gracefully to standard PER when the semantic signal is absent or wrong.

**The original additive formula (what we used initially and why we changed it):**

```python
# WRONG — used initially, caused Semantic PER < PER
final = 0.7 × semantic_priority + 0.3 × TD_priority
```

This meant 70% of the signal was the VLM's guess even when the VLM was unreliable. It actively suppressed PER's signal. The multiplicative formula eliminates this problem: a semantic weight of 1.0 (no boost) leaves TD-priority completely intact.

---

## Failure Localization Methods

Both methods produce one number — `failure_t` — which is passed to `apply_semantic_priority`. Everything downstream is identical.

### Method 1: GPT-4o VLM Localizer

**Invoked every 10th failed episode** (`vlm_call_interval=10`) to avoid API rate limits across 9 parallel runs.

**Step-by-step:**

1. **Capture frames**: `FrameCapture` wrapper calls `env.render()` after each step, accumulating RGB frames throughout the episode.

2. **Sample keyframes**: Select K=5 frames at uniform intervals:
   ```
   50-step episode → keyframes at steps [5, 15, 25, 35, 45]
   ```

3. **Encode**: Each frame (numpy uint8 array) → JPEG → base64 string.

4. **Build prompt**:
   ```
   "You are analyzing a robotic manipulation trajectory.
   Task: {task_description}
   
   You are shown 5 keyframes from an episode that FAILED.
   Frames are in chronological order. Frame 0 ≈ 10% through episode, etc.
   
   Identify which keyframe shows the critical failure moment.
   If the failure is ambiguous, set failure_frame_index to null.
   
   Respond ONLY with JSON:
   {"failure_frame_index": <int or null>, "reasoning": "<one sentence>"}"
   ```

5. **Query GPT-4o**: Send prompt + images. Add random jitter `sleep(uniform(0.5, 3.0))` before the call to stagger parallel API requests.

6. **Escape hatch**: If GPT-4o returns `null`, no semantic boost is applied — the episode is processed as standard PER. This prevents noisy boosts when the VLM is uncertain.

7. **Map to timestep**: `failure_frame_index = 2` → keyframe at step 25 → `failure_t = 25`.

8. **Fallback on error**: If the API call fails entirely, defaults to `failure_t = 0.67 × episode_length` (last third).

**Limitation**: GPT-4o was trained on natural images. MuJoCo renders — grey robot arm, flat table, small colored block on a uniform background — are visually far from its training distribution. Adjacent keyframes look nearly identical. The VLM often guesses.

### Method 2: Heuristic Oracle Localizer

**Invoked every failed episode** (no API cost). Uses ground-truth object positions from the simulator.

During the episode, `train.py` records `ep_obs[-goal_dim*2:-goal_dim]` (the `achieved_goal` slice of the flattened observation — the object's 3D position) at every timestep. This gives a trajectory of positions `[p_0, p_1, ..., p_T]`.

**Two-phase logic:**

**Phase 1 — Ballistic detection** (for FetchSlide):

Compute per-step object displacement (proxy for velocity):
```python
displacement[t] = ||positions[t+1] - positions[t]||
peak_t   = argmax(displacement)
peak_vel = displacement[peak_t]
```

Check if the episode has a throw-and-release structure:
```python
post_mean = mean(displacement[peak_t+1 : peak_t+7])

if peak_vel > 0.008 and post_mean > 0.35 × peak_vel:
    # Object kept moving after the peak → robot released it → ballistic episode
    failure_t = peak_t  # the throw moment
```

This detects FetchSlide episodes where the robot throws the puck and then loses contact. After release, the puck slides freely (constant velocity), so `post_mean ≈ peak_vel`. The throw moment is when the agent made its last causal decision.

**Phase 2 — Closest approach** (for FetchPush, FetchPickAndPlace):

If the ballistic condition is not met (robot maintains contact throughout):
```python
distances = [||positions[t] - desired_goal|| for t in 0..T]
failure_t = argmin(distances)
```

The moment the object was geometrically closest to the target — when the policy was "almost there" before diverging.

**Why this is "oracle"**: A real robot deployment doesn't expose `achieved_goal` as a structured vector. This approach requires direct access to the simulator's internal state and would not work on physical hardware or raw video observations. It is an upper bound on what Semantic PER could achieve with perfect localization.

---

## Environments

All three environments are from `gymnasium-robotics`, using a 7-DOF Fetch robotic arm. Observations are dicts with `{observation, achieved_goal, desired_goal}` flattened to a 31-dimensional vector. All use **sparse binary rewards**: 0 for success, -1 for failure. Episodes are 50 steps.

### FetchPickAndPlace-v4
**Task**: Pick up a block from the table and place it at a floating 3D target position.  
**Why it's hard**: Requires two contact events in sequence — grasp the block, then precisely release at the goal. The block must be lifted off the table (contact + closed gripper), transported (continuous control), and released at the correct position. Failures include grasping at the wrong angle, dropping the block in transit, or imprecise placement.

### FetchPush-v4
**Task**: Push a block across a table to a 2D goal position.  
**Why PER solves it**: The robot must make and maintain contact with the block while sliding it to the goal. Contact events produce large TD-error spikes, giving PER clear signal to prioritize. The task is geometrically simple — the robot can push in a straight line. All methods learn by 1M steps, but PER learns dramatically faster.

### FetchSlide-v4
**Task**: Hit a puck on a frictionless table so it slides to a distant target.  
**Why it's hard**: The agent must impart the correct velocity direction and magnitude in a brief contact window. After release, the puck slides freely — the agent has no further control. Failures that look geometrically different (puck slides to wrong side, right direction but wrong speed) may look identical in TD-error space. PER has almost no signal because the reward is equally -1 whether the puck missed by 1cm or 1m.

---

## Implementation Details

### Observation Extraction

The Gymnasium-Robotics Fetch environments return goal-conditioned dict observations. We use a `FlattenGoalObs` wrapper:

```python
obs = np.concatenate([obs["observation"],    # 25d robot proprioception
                       obs["achieved_goal"],  # 3d object position
                       obs["desired_goal"]])  # 3d target position
# Total: 31d
```

Extracting `achieved_goal` and `desired_goal` from this vector is robust to wrapper chain attribute delegation issues:
```python
achieved_goal = ep_obs[-goal_dim*2:-goal_dim]  # slicing, not getattr
desired_goal  = ep_obs[-goal_dim:]
```

### Frame Capture

For GPT-4o experiments, a `FrameCapture` wrapper calls `env.render()` after every step and stores frames in `env.episode_frames`. At episode end, 5 keyframes are selected and sent to the VLM. This adds ~15% overhead to episode time.

### Cloud Training (Modal)

All 36 full runs execute on Modal A10G GPUs (16GB VRAM). Key configuration:
- `MUJOCO_GL=osmesa` — headless software rendering (no display in cloud containers)
- Persistent volume at `/results` — checkpoints and logs survive container restarts
- `--detach` flag required for multi-job ablations so jobs survive CLI exit
- 9 jobs spawn in parallel; Modal queues the rest as GPUs free up

### Logging

Every run logs to both TensorBoard (local) and Weights & Biases (cloud):

| Metric | Logged every |
|---|---|
| `eval/success_rate` | 5,000 steps |
| `eval/mean_return` | 5,000 steps |
| `loss/critic`, `loss/actor`, `loss/alpha` | 1,000 steps |
| `train/alpha`, `train/td_error` | 1,000 steps |
| `train/episode_return`, `train/success` | episode end |
| `vlm/failure_timestep`, `vlm/failure_pct` | each VLM call |
| `vlm/failure_keyframe` | each VLM call (image) |
| `vlm/confidence` | each VLM call |

---

## Design Decisions and Iterations

### Iteration 1: Additive blending → Multiplicative blending

**Problem**: Initial Semantic PER used additive blending:
```python
final = 0.7 × semantic_priority + 0.3 × TD_priority
```
When the VLM was unreliable, this meant 70% of the priority signal was noise. Semantic PER performed worse than PER everywhere.

**Fix**: Multiplicative blending:
```python
final = TD_priority × semantic_weight
```
`semantic_weight` is 1.0 by default (neutral — identical to PER) and only boosted to 10.0 in the identified failure window. When the VLM is wrong, the boost is absent and performance degrades to PER, not below it.

### Iteration 2: VLM rate limiting → vlm_call_interval=10

**Problem**: 9 parallel runs each calling GPT-4o after every failed episode saturated the API. HTTP 429 rate limit errors caused every VLM call to fall back to the default heuristic.

**Fix**: `vlm_call_interval=10` — each run only queries the VLM on 1 in 10 failed episodes. This reduces API calls by 10x while still providing semantic signal across many episodes of training.

### Iteration 3: Wrapper attribute delegation → Direct observation slicing

**Problem**: `getattr(env, "last_achieved_goal", None)` returned `None` through the gymnasium wrapper chain in the Modal container, causing `ep_achieved_goals` to always be empty and the heuristic localizer to crash on every episode.

**Fix**: Extract `achieved_goal` directly from the flattened observation vector:
```python
prev_achieved = ep_obs[-goal_dim*2:-goal_dim].copy()
```
This is guaranteed to work regardless of wrapper structure.

### Iteration 4: argmin distance → Ballistic detection for FetchSlide

**Problem**: The oracle localizer used `argmin(||achieved - desired||)` for all tasks. On FetchSlide, the puck's closest geometric approach to the target often occurs post-throw as the puck slides across the table — the oracle identified `failure_t` at episode fraction 0.98 on average. The robot has zero control during this phase; those transitions teach the critic nothing.

**Evidence from W&B** (failure timestep fraction distribution, FetchSlide):
- Oracle v1: Mean=0.713, **Median=0.980** (69.3% of calls in last third of episode)
- GPT-4o: Mean=0.474, Median=0.500 (roughly uniform across episode)

This explained why Oracle v1 (0.167) massively underperformed GPT-4o (0.550) on FetchSlide despite having access to ground-truth state.

**Fix**: Two-phase localizer — detect ballistic episodes via velocity profile, use the throw moment as `failure_t`. This shifts oracle FetchSlide localizations to episode fraction ~0.2–0.3 (the actual throw window).

### Iteration 5: VLM escape hatch

Added `"failure_frame_index": null` as a valid GPT-4o response. When GPT-4o is uncertain, it returns null and no semantic boost is applied. This prevents noise injection on episodes where the VLM has low confidence rather than forcing a guess.

---

## Results

Full ablation: 36 runs (3 envs × 4 methods × 3 seeds), 1M steps each.

### Final Success Rate (mean ± std over 3 seeds)

| Method | FetchPickAndPlace | FetchPush | FetchSlide | Average |
|---|---|---|---|---|
| Uniform | 0.067 ± 0.094 | 0.083 ± 0.085 | 0.083 ± 0.118 | 0.078 |
| PER | 0.100 ± 0.071 | **0.950 ± 0.041** | 0.100 ± 0.108 | 0.383 |
| Semantic PER (GPT-4o) | 0.200 ± 0.187 | 0.167 ± 0.170 | **0.550 ± 0.402** | 0.306 |
| Semantic PER (Oracle v1) | **0.383 ± 0.306** | 0.700 ± 0.356 | 0.167 ± 0.118 | 0.417 |

### Plot Descriptions

**fig1_curves.png** — Learning curves per environment. X-axis: training steps (0–1M). Y-axis: eval success rate (20-episode average). Shaded bands = ±1 std across 3 seeds. Shows when each method starts learning and how quickly it plateaus.

**fig2_bars.png** — Final success rate bar chart per environment. Error bars = ±1 std across 3 seeds. Best for direct method comparison at 1M steps.

**fig3_avg.png** — Average success rate across all three environments combined. Single curve per method, showing overall sample efficiency.

**fig4_individual_seeds.png** — 3×4 grid showing each individual seed run. Reveals inter-seed variance and whether averages are representative.

**fig5_failure_timestep_dist.png** — Histogram of `failure_t / episode_length` for FetchSlide runs. Oracle v1 peaks at 0.98; GPT-4o is roughly uniform. This is the diagnostic that motivated the ballistic fix.

**fig6_failure_bias_over_time.png** — Scatter + rolling mean of failure fraction over training steps. Shows whether either localizer's bias shifts as the policy improves.

---

## Failure Timestep Analysis

### What we measured

`vlm/failure_pct = failure_t / episode_steps` is logged to W&B at every VLM call. This tells us *where in the episode* each method identifies the failure point.

### FetchSlide: The critical diagnostic

```
GPT-4o (n=4534 calls across 3 seeds):
  Early (<0.33): 29.5%
  Mid (0.33–0.66): 51.1%
  Late (>0.66): 19.5%
  Mean=0.474, Median=0.500

Oracle v1 (n=6000 calls):
  Early (<0.33): 25.3%
  Mid (0.33–0.66): 5.4%
  Late (>0.66): 69.3%
  Mean=0.713, Median=0.980
```

Oracle v1 placed 69.3% of its localizations in the final third of the episode — long after the robot had released the puck. GPT-4o's uniform spread accidentally covered the early throw window more often, which explains why GPT-4o (0.550) massively outperformed Oracle v1 (0.167) on FetchSlide despite having no access to ground truth.

### Implications

The failure timestep distribution is a leading indicator of localization quality. A good localizer for contact tasks should cluster localizations **early to mid episode** (where the agent's actions are causal). Late-episode localizations on throw-and-release tasks indicate the localizer is tracking geometric consequences rather than causal decisions.

---

## Why FetchSlide Reversed

This is the most counter-intuitive finding: GPT-4o (0.550) beat the ground-truth Oracle (0.167) on FetchSlide.

**The explanation:**

In FetchSlide, the task structure is:
```
Steps 1–15:  Robot moves toward puck (puck stationary)
Steps 12–18: Robot makes contact, throws puck (puck velocity peaks)
Steps 18–50: Puck slides freely — robot has zero control
```

The `argmin(distance)` oracle finds when the puck was *geometrically closest* to the target. For FetchSlide, this often happens during the free-sliding phase (steps 20–50) when the puck passes near the target before overshooting. At that point the robot cannot do anything — it already released the puck 30 steps ago.

GPT-4o, despite being unreliable at interpreting MuJoCo renders, tends to pick *visually distinct* frames. Since the early frames (robot approaching puck) look different from mid-episode frames (puck in motion), GPT-4o sometimes identifies the throw frame — which is causally correct.

**The key lesson:** Failure localization must be causally grounded, not just geometrically accurate. Proximity to goal is not equivalent to causal influence. For throw-and-release tasks, the causal failure point is determined by the physics of object release, not the puck's trajectory afterward.

The Oracle v2 (currently running) fixes this with ballistic detection.

---

## Key Findings

**1. Multiplicative blending is necessary for graceful degradation.**
Additive blending (`0.7 × semantic + 0.3 × TD`) is catastrophic when the VLM is wrong — it actively suppresses PER's signal. Multiplicative blending (`TD × semantic_weight`) degrades to standard PER when semantic weight is 1.0, making Semantic PER a strict superset of PER in the best case.

**2. Semantic PER helps most when PER's TD-error signal is weak.**
On FetchSlide, PER achieves only 10% success — the puck barely moves in early failed episodes, so all TD-errors are uniformly small and PER has nothing to exploit. Any causal failure signal (even noisy VLM) outperforms pure TD prioritization. On FetchPush, PER reaches 95% — TD-error already finds the right transitions, and the VLM signal adds noise.

**3. VLM localization quality is the main bottleneck.**
Oracle v1 (0.417 avg) outperforms GPT-4o (0.306 avg), confirming that *better localization → better Semantic PER performance*. The gap between oracle and VLM represents the headroom that better visual models (video-language models, domain-finetuned VLMs, or learned failure detectors) could close.

**4. Failure localization assumptions must match task physics.**
`argmin(distance)` is the wrong metric for throw-and-release tasks. The oracle must reason about when the agent had causal control, not just when geometric proximity to the goal was highest. Task-specific localization logic (ballistic detection, contact detection, gripper state) significantly impacts whether the semantic signal is useful.

**5. High variance is the regime we're operating in.**
Standard deviations of 0.1–0.4 on success rate (3 seeds) show that all methods are at the boundary of what 1M steps can solve. Longer runs or more seeds would be needed to draw statistically robust conclusions. FetchPickAndPlace and FetchSlide likely need 2–5M steps for reliable learning.

**6. The semi-Markovian keyframe problem.**
GPT-4o receives discrete keyframes, but failures often result from sequences of sub-optimal actions occurring *between* keyframes rather than visible state at a single frame. A video-language model (processing temporal sequences rather than isolated frames) would be more appropriate for identifying failure *patterns* rather than failure *moments*.

---

## Project Structure

```
RL_project_185/
│
├── train.py                         # Main training loop (1M steps)
├── evaluate.py                      # Standalone evaluation script
├── modal_app.py                     # Modal cloud deployment
│
├── configs/
│   ├── base.yaml                    # Shared hyperparameters
│   ├── uniform.yaml                 # Uniform replay
│   ├── per.yaml                     # Standard PER
│   ├── semantic_per.yaml            # Semantic PER with GPT-4o
│   ├── semantic_per_heuristic.yaml  # Semantic PER with oracle localizer
│   ├── her.yaml                     # Hindsight Experience Replay (experimental)
│   ├── her_per.yaml                 # HER + PER (experimental)
│   └── her_semantic_per.yaml        # HER + Semantic PER (experimental)
│
├── src/
│   ├── agents/
│   │   └── sac.py                   # SAC: twin Q-networks, auto entropy, grad clip
│   │
│   ├── buffers/
│   │   ├── __init__.py              # make_buffer factory
│   │   ├── replay_buffer.py         # Uniform ring buffer O(1)
│   │   ├── per_buffer.py            # PER with SumTree O(log N)
│   │   ├── semantic_buffer.py       # Semantic PER: multiplicative blending
│   │   └── her_buffer.py            # HER wrapper (k=4, future strategy)
│   │
│   ├── envs/
│   │   └── wrappers.py              # FlattenGoalObs + FrameCapture wrappers
│   │
│   ├── vlm/
│   │   ├── __init__.py
│   │   └── localizer.py             # GPT-4o + GoalDistanceLocalizer (oracle)
│   │
│   └── utils/
│       ├── keyframes.py             # Keyframe selection and frame index mapping
│       └── logger.py                # TensorBoard + W&B logger
│
├── scripts/
│   ├── plot_results.py              # Multi-run W&B comparison plots
│   └── plot_training.py             # Single-run live dashboard
│
├── plots/
│   ├── fig1_curves.png              # Learning curves per env (mean ± std)
│   ├── fig2_bars.png                # Final success rate bar chart
│   ├── fig3_avg.png                 # Average across all environments
│   ├── fig4_individual_seeds.png    # Individual seed breakdown
│   ├── fig5_failure_timestep_dist.png  # Where each localizer identifies failures
│   └── fig6_failure_bias_over_time.png # Localization bias shift over training
│
├── requirements.txt
├── .env.example                     # Template — copy to .env and fill in keys
├── .gitignore
└── README.md
```

---

## Setup

### Local (code editing, plotting)

```bash
# Clone
git clone https://github.com/parshawn/RL_project_185.git
cd RL_project_185

# Create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env — add OPENAI_API_KEY and WANDB_API_KEY
```

> **Note:** MuJoCo training requires Linux x86_64 with a GPU. Use Modal for actual training runs.

### Modal (GPU training)

**Step 1 — Install and authenticate:**
```bash
pip install modal
modal token new    # opens browser for auth
```

**Step 2 — Create Modal Secret** at [modal.com](https://modal.com) → Secrets → Create:

Name: `semantic-per-secrets`

| Key | Value |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI key |
| `WANDB_API_KEY` | Your W&B key |
| `WANDB_ENTITY` | Your W&B username/team |
| `WANDB_PROJECT` | `RL_project` |

**Step 3 — Verify:**
```bash
modal run modal_app.py --config configs/uniform.yaml --extra "training.total_steps=1000"
```

---

## Running Experiments

### Single run on Modal:
```bash
modal run modal_app.py --config configs/semantic_per.yaml
modal run modal_app.py --config configs/per.yaml --extra "env.name=FetchPush-v4"
```

### Full ablation (all methods, all envs, all seeds) — detach required:
```bash
# Edit modal_app.py → METHODS list to select which configs to run
modal run --detach modal_app.py::run_ablation
```

### Monitor runs:
```bash
modal app list
modal app logs <app-id>    # stream live logs
```

### Local training (Linux + GPU only):
```bash
python train.py --config configs/per.yaml
python train.py --config configs/semantic_per.yaml env.name=FetchSlide-v4 training.seed=42
```

### Plot results from W&B:
```bash
# Generates all figures in plots/
python scripts/plot_results.py \
    --wandb_project RL_project \
    --wandb_entity <your-entity> \
    --out_dir plots/
```

---

## Config Reference

All configs inherit from `configs/base.yaml`.

| Parameter | Default | Description |
|---|---|---|
| `env.name` | `FetchPickAndPlace-v4` | Gymnasium environment ID |
| `env.max_episode_steps` | `50` | Steps per episode |
| `sac.hidden_dim` | `256` | MLP hidden layer size |
| `sac.lr_actor` | `3e-4` | Actor learning rate |
| `sac.lr_critic` | `3e-4` | Critic learning rate |
| `sac.gamma` | `0.98` | Discount factor |
| `sac.tau` | `0.005` | Polyak averaging coefficient |
| `sac.batch_size` | `256` | Replay batch size |
| `sac.updates_per_step` | `1` | Gradient updates per env step |
| `training.total_steps` | `1_000_000` | Total environment steps |
| `training.warmup_steps` | `10_000` | Steps of random exploration |
| `training.eval_interval` | `5_000` | Steps between evaluations |
| `training.eval_episodes` | `20` | Episodes per evaluation |
| `training.seed` | `42` | Random seed |
| `replay.type` | — | `uniform`, `per`, `semantic_per` |
| `replay.capacity` | `1_000_000` | Buffer size |
| `replay.per_alpha` | `0.6` | Priority exponent |
| `replay.per_beta_start` | `0.4` | IS weight annealing start |
| `replay.per_beta_end` | `1.0` | IS weight annealing end |
| `replay.per_beta_anneal_steps` | `500_000` | Steps to anneal beta |
| `replay.vlm_keyframes` | `5` | Keyframes sent to VLM |
| `replay.vlm_failure_window` | `5` | Priority boost half-width (steps) |
| `replay.semantic_boost` | `10.0` | Multiplicative priority boost |
| `replay.vlm_call_interval` | `10` | VLM called every N failed episodes |
| `replay.vlm_provider` | `openai` | `openai`, `anthropic`, or `heuristic` |
| `replay.vlm_model` | `gpt-4o` | Model ID |
| `logging.use_wandb` | `true` | Enable W&B logging |
| `logging.use_tensorboard` | `true` | Enable TensorBoard logging |
| `logging.log_dir` | `logs/` | Local log directory |
| `logging.checkpoint_dir` | `checkpoints/` | Checkpoint directory |

---

## References

- Schaul, T., Quan, J., Antonoglou, I., & Silver, D. (2015). *Prioritized Experience Replay*. ICLR 2016.
- Haarnoja, T., Zhou, A., Abbeel, P., & Levine, S. (2018). *Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor*. ICML 2018.
- Haarnoja, T., et al. (2019). *Soft Actor-Critic Algorithms and Applications*. arXiv:1812.05905.
- Andrychowicz, M., et al. (2017). *Hindsight Experience Replay*. NeurIPS 2017.
- Plappert, M., et al. (2018). *Multi-Goal Reinforcement Learning: Challenging Robotics Environments and Request for Research*. arXiv:1802.09464.
- Achiam, J., et al. (2023). *GPT-4 Technical Report*. arXiv:2303.08774.

---

*CS 285 — Deep Reinforcement Learning, UC Berkeley, Spring 2026.*
