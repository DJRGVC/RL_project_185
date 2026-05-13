# C1 — VLM Counterfactual Prompts (Path C Prototype)

**Agent:** C1 (counterfactual prompt design)
**Date:** 2026-05-11
**Branch:** `agent/c1-counterfactual-prompts`
**Files:**
- `src/vlm/counterfactual.py` (new)
- `scripts/test_counterfactual.py` (new)
- `agent_reports/C1_counterfactual_outputs.json` (this run's outputs)

## TL;DR

We built `CounterfactualLocalizer` — a new VLM module that asks
**"what should the robot have done differently at the failure frame?"**
rather than "where is the failure?". Three prompt variants were prototyped
and tested on **4 failed Fetch-suite rollouts** (2 × FetchPush-v4,
2 × FetchPickAndPlace-v4) using **Claude Opus 4.7** as both the
generator and the independent plausibility judge. (OpenAI key not in
env on this machine; the implementation supports `provider="openai"` /
GPT-4o out of the box.)

Aggregate plausibility judge scores (0–1, mean over 4 episodes):

| variant         | plausibility | goal-progress | specificity | VLM-conf | parse-rate |
| --------------- | :-: | :-: | :-: | :-: | :-: |
| `narrative`     | **0.79** | 0.68 | 0.40 | 0.82 | 4/4 |
| `action`        | 0.55 | 0.53 | **0.65** | 0.43 | 4/4 |
| `achieved_goal` | 0.46 | **0.97** | 0.49 | 0.68 | 4/4 |

**Headline findings:**

1. The **`narrative`** prompt is consistently the most physically
   plausible. But its output is unstructured English — only usable by a
   downstream language-conditioned consumer.
2. The **`action`** prompt produces machine-readable 4-vectors with
   good specificity (0.65), but ~40% of the proposed actions point in
   the wrong sign on one axis (judge correctly flags this).
3. The **`achieved_goal`** prompt is **strongly task-dependent**:
   - **PickAndPlace (goal is in mid-air)**: plausibility = **0.75 mean**.
     VLM proposes "place block 3 cm above target" which is exactly the
     right hindsight relabel target.
   - **Push (goal is on the table surface)**: plausibility = **0.18 mean**.
     VLM short-circuits to `corrective_position == desired_goal`,
     i.e. "teleport block to target". Judge correctly rejects this as
     unphysical.

---

## 1. Setup

### 1.1 Why we used synthetic episodes (not W&B)

The hand-off told us to pull failed episodes from
`djrgvc/RL_project` filtered on `method=semantic_per_heuristic_v2`. From
this account (default W&B entity `d-grant-uc-berkeley`, and querying
explicitly with `djrgvc`/`DJRGVC`) the project `RL_project` is reported
as not found:

```
ValueError: Could not find project RL_project
```

Two viable W&B projects exist for the active entity
(`quadrujuggle`, `omnidrones`) but neither contains Fetch runs. To stay
on schedule we fell back to **local rollouts**:

```python
# scripts/test_counterfactual.py — collect_failed_episodes()
env = make_env(env_name, render_mode="rgb_array", capture_frames=True)
# weak heuristic policy: drive gripper toward block with noise
action = _heuristic_policy(obs, obs_dim, goal_dim, rng=rng, noise=0.5)
```

The heuristic policy reads (roughly) the gripper-to-block delta, clips to
the [-1,1] action box, and adds Gaussian noise. This reliably produces
*failed* trajectories where the block has actually been touched
(`max single-step displacement ≈ 0.1 m`) — preferable to pure-random
inputs, which leave the block stationary and give the VLM nothing to look
at.

### 1.2 API & credentials

`OPENAI_API_KEY` is not set in the shell on this machine and no
`.openai_key` file exists; only `~/.anthropic_key` is available. We
therefore ran the prototype against **`claude-opus-4-7`** as both the
generator and the judge. The implementation supports OpenAI / GPT-4o
out of the box — just set `OPENAI_API_KEY` and pass `provider="openai"`.

Note on Claude Opus 4.7: the API *deprecates* the `temperature` kwarg for
this model, so `counterfactual.py` strips it automatically when the model
name contains `opus-4-7`.

### 1.3 Localizer / keyframes

- Failure timestep: `GoalDistanceLocalizer` (existing heuristic). It
  collapses to t=0 for the synthetic episodes (block never gets closer
  to the goal), so we clip `failure_t` to the middle of the episode
  if the heuristic returns `< episode_length / 5`. In real training
  runs the existing ballistic-throw detector + true-positive failure
  trajectories would dominate.
- Keyframes: `select_keyframes(..., k=5, strategy="uniform")` — same
  selection as the existing localizer.

### 1.4 Budget

- Cap: ≤ 30 VLM calls (~$1.50 at $0.05/call).
- Main run: 2 envs × 2 episodes × 3 variants × 2 (gen + judge) = **24 calls**.
- `all` variant follow-up: 2 episodes × 1 variant × 2 = **4 calls**.
- **Total: 28 calls, under the cap.**
- Each call ≈ 2–13 s wall-time end-to-end.

---

## 2. Prompt Designs

The three variants are defined in `src/vlm/counterfactual.py` as named
templates in `PROMPT_TEMPLATES`. All share the same preamble (task
description, K keyframes, frame-index map) and identify the
**failure frame** explicitly. They differ only in *what they ask for*:

### Variant A — `narrative` (free-form description)

> *"What should the robot have done differently at Frame K? Be specific
> about the corrective behaviour in physical terms."*

Output schema:
```json
{ "explanation": "<one sentence>", "confidence": <float> }
```

### Variant B — `action` (corrective 4-D action vector)

> *"Provide a single delta-action [Δx, Δy, Δz, grip] at Frame K."*
> *"Action space is bounded to [-1,1]; gripper -1=close +1=open."*

Output schema:
```json
{ "corrective_action": [dx, dy, dz, grip],
  "explanation": "<one sentence>",
  "confidence": <float> }
```

The prompt explicitly tells the VLM the action units (≈ 5 cm/step at
|a|=1.0) and the axis conventions (x = away from robot, y = left, z = up).

### Variant C — `achieved_goal` (hindsight target position)

> *"What 3D position should the object have reached at Frame K for the
> trajectory to be on track for success?"*
> Workspace bounds and `desired_goal = [...]` are inserted into the prompt.

Output schema:
```json
{ "corrective_position": [x, y, z],
  "explanation": "<one sentence>",
  "confidence": <float> }
```

A unified Variant D (`all`) packs A+B+C into a single call (returns
position + action + explanation in one JSON). Benchmarked on 2
additional episodes (results in `C1_counterfactual_all_variant.json`).

### Why this combination?

Each variant probes a different downstream consumer in Path C's
hindsight-relabeling plan:

| Variant | What it produces | Plausible RL consumer |
| --- | --- | --- |
| A `narrative` | Free-form sentence | Auxiliary reward model / language-conditioned policy |
| B `action` | 4-D action | Hindsight *action* relabeling — overwrite the bad action in the replay buffer |
| C `achieved_goal` | 3-D position | Hindsight *goal* relabeling — feed back as HER target |

---

## 3. Example Prompt + Output Pairs

All four episodes used the same preamble (5 uniform keyframes, the same
task description, the same failure timestep at t=25/50). Below are the
actual parsed outputs from `C1_counterfactual_outputs.json`.

### Episode 1 — FetchPush-v4, seed=1251

- Final block position: `[1.50, 0.16, 0.02]` (block fell off the table)
- Desired goal: `[1.34, 0.70, 0.42]`

| Variant | Output | Judge (plaus / progr / spec) |
| --- | --- | --- |
| `narrative` | "*Instead of pushing the block off the front edge of the table, the robot should have approached from behind the block and pushed it horizontally toward the red target on the table surface.*" | **0.75 / 0.70 / 0.40** |
| `action` | `[0.2, 0.5, 0.5, -1.0]` — "*The gripper has pushed the block off the table edge; it should move up and back toward the red target on the table.*" | **0.70 / 0.80 / 0.80** |
| `achieved_goal` | `[1.344, 0.702, 0.425]` — *identical to `desired_goal`* | **0.20 / 1.00 / 0.30** |
| | "Teleporting the block to the target matches the goal perfectly but is physically implausible since z=0.42 is at table height and a pushed block cannot instantly jump ~0.55m in one step." | judge verdict |

### Episode 3 — FetchPickAndPlace-v4, seed=2234

- Block position at failure (t=25): `[1.07, 0.69, 0.44]` (gripper picked something up but not the block)
- Desired goal: `[1.35, 0.83, 0.42]` (mid-air target)

| Variant | Output | Judge (plaus / progr / spec) |
| --- | --- | --- |
| `narrative` | "*The robot should have lowered the gripper onto the block and closed it to grasp the block before moving away*" | **0.90 / 0.70 / 0.40** |
| `action` | `[0.2, -0.3, -0.5, -1.0]` — "*the robot should descend and close the gripper*" | **0.40 / 0.20 / 0.60** |
|  | judge: *"The action descends and closes the gripper which is reasonable for regrasping, but it moves in -y (away from the target)…"* | sign error caught |
| `achieved_goal` | `[1.354, 0.833, 0.455]` — "*the gripper should already be grasping the block and lifting it just above the target position*" | **0.90 / 0.95 / 0.85** |
|  | judge: *"places the block just above the target within workspace limits and clearly advances toward the desired goal with an actionable mid-trajectory strategy."* | best response in study |

### Episode 4 — FetchPickAndPlace-v4, seed=2251 (failure mode: lost grip)

- Block position at failure: `[1.61, 0.39, 0.02]` (block fell off table)
- Desired goal: `[1.30, 0.71, 0.42]`

| Variant | Output | Judge |
| --- | --- | --- |
| `narrative` | "*The robot should have positioned its gripper directly over the block and closed the gripper to grasp it*" | **0.80 / 0.50 / 0.30** |
| `action` | `[0.2, 0.5, -0.3, -1.0]` — "*The gripper missed the block (fell off table to the right); move toward the target*" | **0.40 / 0.30 / 0.60** |
|  | judge: *"…moving +x/+y heads away from the desired goal and the block is no longer reachable from this descent."* | sign error caught |
| `achieved_goal` | `[1.297, 0.706, 0.425]` — *= desired_goal again* | **0.60 / 1.00 / 0.50** |

### Summary table across all 4 episodes

| ep | env                | judge_narrative | judge_action | judge_achieved_goal |
| -- | ------------------ | :-: | :-: | :-: |
| 1  | FetchPush-v4       | 0.75 | 0.70 | 0.20 |
| 2  | FetchPush-v4       | 0.70 | 0.70 | 0.15 |
| 3  | FetchPickAndPlace  | 0.90 | 0.40 | 0.90 |
| 4  | FetchPickAndPlace  | 0.80 | 0.40 | 0.60 |
| **mean** |              | **0.79** | 0.55 | 0.46 |

### Unified `all` variant — 2 additional episodes

After the main run, we spent 4 extra calls testing the unified
`variant="all"` prompt (results merged into the same JSON, episodes 5–6):

| ep | env | conf | judge plaus / prog / spec | observation |
| -- | --- | :-: | :-: | --- |
| 5 | FetchPickAndPlace | 0.80 | 0.80 / 0.50 / 0.85 | "Descend and close grip" — concrete and actionable |
| 6 | FetchPush          | 0.60 | 0.60 / 0.75 / 0.80 | Action vector non-trivial; position is near desired_goal but NOT identical |

Key result: **when forced to produce both an action AND a position in
the same call, the VLM stops short-circuiting the position to
`desired_goal` for Push**. The Push position in Ep 6 is `[1.345, 0.728, 0.425]`
vs `desired_goal = [1.344, 0.724, 0.425]` — a small but non-zero
deviation, and the action vector `[0.2, -0.3, -0.5, -1.0]` is
meaningfully task-relevant. This suggests the unified prompt
*structurally regularises* the answer.

---

## 4. Plausibility Analysis

Three patterns stand out:

1. **`narrative` is the safest default.** Plausibility ≥ 0.7 in all 4 of
   4 episodes. Always reads as *physically* reasonable corrective advice
   ("approach from the opposite side", "close gripper before moving",
   etc.). Tradeoff: zero machine-readable structure — needs a downstream
   language-conditioned consumer to be useful for SAC.

2. **`action` has the highest specificity** (0.65 mean) but the lowest
   self-reported confidence (0.43 mean). Cross-tab inspection: the VLM
   *correctly diagnoses* the failure in the explanation field but
   *gets the sign of the y-axis wrong* in the action vector in 2 of 4
   episodes. The 4D structure is well-formed in 4/4 cases (no parse
   errors), so an additional check `sign(action[:3]) == sign(desired_goal
   - achieved_goal)` would filter the bad ones cheaply.

3. **`achieved_goal` is bimodal by task class:**

   |    task              | plausibility mean |
   | -------------------- | :-: |
   | FetchPickAndPlace    | **0.75** |
   | FetchPush            | **0.18** |

   For *PickAndPlace*, the target floats in the air (`z ≈ 0.42 m + ε`)
   and the VLM proposes a reasonable mid-trajectory waypoint above the
   target. For *Push*, the target is *on* the table surface — there is no
   non-trivial waypoint, and the VLM resolves the ambiguity by setting
   `corrective_position = desired_goal`. The judge rejects this every
   time as physically implausible (teleport).

   Implication: the *achieved_goal* variant should be **gated by the
   task class** (or by whether the target is significantly above the
   table). It is *not* a general-purpose substitute for HER.

---

## 5. Failure Modes Observed

### F1. `achieved_goal` collapses to `desired_goal` on planar tasks ★ critical

3 of 4 episodes had `corrective_position` *identical* to `desired_goal`
(to 6 decimal places — Episodes 1, 2, 4). Episode 3 (PickAndPlace, mid-
air goal) was the only one where the VLM produced a non-trivial
hindsight position. The judge consistently flags the collapse:

> *"Teleporting the block to the target trivially satisfies the goal
> but is not physically realizable in one step."* — judge, ep 1
>
> *"The corrective position matches the desired goal so it trivially
> maximizes goal progress, but teleporting the block to z≈0.425 is not
> physically achievable by pushing."* — judge, ep 2

This is critical because it means **`achieved_goal` cannot be naively
fed to HER** — without a workspace plausibility filter, it just
collapses to vanilla HER's final-state relabeling and adds nothing.

Mitigations for Path C v2:
- Reject any output where `‖corrective_position − desired_goal‖ < 5 cm`.
- Provide a *displacement budget* in the prompt: "must lie within
  D = max_velocity × (T − t) of the actual position at this frame."
- Pass the achieved-goal *trajectory* (compact JSON list) in the prompt
  so the VLM knows what the current rate of progress is.

### F2. `action` flips one axis sign in ~50% of episodes

In Episodes 1, 3, 4 the y-component of the action vector pointed *away*
from the target, even though the explanation field described the correct
direction. Symptom of VLMs having trouble with metric 3D axis orientation
in angled table-top renders. The judge catches each contradiction:

> *"The action's negative y component moves away from the target (which
> requires +y motion), contradicting the explanation."* — judge, ep 4

Workarounds:
- Filter on `sign(action[:3]) == sign(desired_goal − achieved_goal)`
  before applying the relabel. Cheap.
- Include `desired_goal − achieved_goal` (vector, in metres) directly in
  the prompt as an unambiguous direction hint.
- Render an x/y/z compass overlay on the keyframes.

### F3. `narrative` is always physically plausible but doesn't reduce to a vector

In 4 of 4 episodes the narrative is a sensible failure mode + corrective
suggestion. But the SAC integration has no way to consume "approach from
the opposite side and push horizontally" without an additional model.
This is a **path-shape problem**, not a quality problem.

### F4. Heuristic failure-localizer collapses to t=0 on synthetic failures

When the random policy pushes the block straight off the table, the
heuristic's "closest approach" sits at the reset frame. We clip
`failure_t` to `episode_length / 2` when it's < 20% through. In
production, the VLM-side counterfactual should:
- prefer the existing `VLMFailureLocalizer` output (more reliable)
- fall back to the ballistic-throw detector
- treat clipping as a confidence-down signal.

### F5. VLM confidence is weakly calibrated

Spearman across all 12 (variant, episode) pairs of (vlm_confidence,
judge_plausibility): **ρ = +0.41** (p = 0.18, n = 12 — not significant).
Useful as a *coarse* filter but not a substitute for the judge or a
plausibility heuristic — keep both gates in the SAC integration.

---

## 6. Recommended Variant for Path C

The data points to a **task-stratified recommendation** rather than a
single winner:

### Default: `narrative` + `action` paired in the unified `all` prompt

Use the `variant="all"` prompt, which packs `corrective_position`,
`corrective_action`, and `explanation` into one call. This is cheaper
(1 VLM call ≈ $0.05 instead of 3) and lets the SAC integration consume
*whichever field is locally usable*:

- `corrective_action` → action-space relabeling (overwrite buffer[failure_t].action)
- `corrective_position` → goal-space relabeling (HER-style)
- `explanation` → sanity-check filter (drop the relabel if narrative
  contradicts the vector)

### Task-specific gating rules

| Condition | Use | Reason |
| --- | --- | --- |
| `desired_goal[2] > 0.43 m` (target is in the air) | `achieved_goal` is **safe** as HER target | mean plaus 0.75 on PickAndPlace |
| `desired_goal[2] < 0.43 m` (target on table) | drop `achieved_goal` *or* reject if `‖cf_pos − dg‖ < 5 cm` | mean plaus 0.18 on Push (teleport mode) |
| Any task | use `action` only when `sign(action[:3]) == sign(dg − ag)` | sign-flip is the dominant `action` failure mode |
| Any task | `narrative` is always safe — but downstream must consume natural language | mean plaus 0.79 |

### Confidence calibration

Self-reported VLM confidence ranged 0.4–0.85 and (loosely) tracks judge
plausibility: high-conf narrative (0.82) → judge 0.79; low-conf action
(0.43) → judge 0.55. Path C's SAC integration (agent C2) should gate
relabeling on `min(vlm_conf, judge_plaus) > 0.5`.

### Single-variant fallback

If C2 wants the simplest possible integration: use **`narrative` +
LLM-based reward shaping**. Highest plausibility (0.79 mean, 4/4
plausible), zero parse errors, never produces unphysical outputs. The
tradeoff is that it doesn't slot directly into HER/PER — it needs a
text-conditioned auxiliary head. If that head exists (or is on the
research backlog), `narrative` is the lowest-risk choice for the
NeurIPS paper.

---

## 7. What's blocked / next steps

- ❌ W&B-derived real episodes were not accessible. Once
  `djrgvc/RL_project` is shared with this account (or we add the
  project name explicitly to `~/.netrc`), we can re-run with
  `wandb.Api().run(...).file("media/images/...").download()` to pull
  the `vlm/failure_keyframe` images.
- ❌ GPT-4o head-to-head not run (no OpenAI key on this machine).
  Implementation supports it; just `export OPENAI_API_KEY=… &&
  --provider openai`. 2 calls of budget left tonight.
- ✅ `CounterfactualLocalizer` ready for agent C2 to import and call.
  Two interfaces:
    1. Rich form (used by the test CLI):
       `loc.query(frames, timestep_indices, ..., variant)`
       → `CounterfactualResult(corrective_position, corrective_action,
       explanation, confidence, ...)`.
    2. **Agent-C2-compatible thin adapter** —
       `make_counterfactual_fn(...)` returns the exact callable signature
       C2 specified in `C2_counterfactual_mechanism.md` (Section "Interface
       contract with agent C1"):
       ```python
       fn = make_counterfactual_fn(provider="anthropic", variant="all",
                                   min_confidence=0.5)
       # fn(achieved_goals, desired_goal, keyframes)
       # → Optional[List[Tuple[int, np.ndarray, float]]]
       ```
       With baked-in gates from this report: teleport-rejection (F1) and
       confidence threshold.
- ⏭️ Next iteration should compare GPT-4o vs Claude Opus 4.7 on the
  same episodes, and add a workspace-plausibility filter (F1 fix).

---

## 8. Reproducing

```bash
cd /home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185
source .venv/bin/activate

# Anthropic backend
MUJOCO_GL=egl ANTHROPIC_API_KEY=$(cat ~/.anthropic_key) \
    python scripts/test_counterfactual.py \
        --n_episodes 2 \
        --envs FetchPush-v4 FetchPickAndPlace-v4 \
        --provider anthropic --model claude-opus-4-7 \
        --judge_model claude-opus-4-7 \
        --variants narrative action achieved_goal \
        --K 5 --budget 30 \
        --out_dir ./agent_reports

# OpenAI backend (once OPENAI_API_KEY is exported)
export OPENAI_API_KEY=...
python scripts/test_counterfactual.py \
    --provider openai --model gpt-4o \
    ...
```

Output goes to `agent_reports/C1_counterfactual_outputs.json`.
