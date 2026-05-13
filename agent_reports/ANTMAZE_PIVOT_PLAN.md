# ANTMAZE_PIVOT_PLAN — porting SAC + HER + CF-HER + Verified-CF to AntMaze

**Author:** ANTMAZE-INFRA-SCOUT (Opus 4.7) — read-only investigation
**Date:** 2026-05-12
**Status:** Design doc. No code changes, no training, no Modal launches were performed.

---

## 1. Why AntMaze (and why now)

Our headline negative on Fetch is now well-supported: even a **privileged Oracle-CF** with perfect failure-frame knowledge fails to clear vanilla HER by the kill threshold (Δ ≥ +0.10) on FetchPickAndPlace / FetchPush / FetchSlide. The most natural reading is that on Fetch the *bottleneck is not credit assignment* — HER's "future" strategy already covers the goal manifold densely because Fetch goal spaces are small (a 50 × 70 × 40 cm box), episodes are short (50 steps), and dynamics are smooth. There is no headroom for a smarter relabeler.

**AntMaze flips every one of those properties:**

| property | Fetch | AntMaze (U / Medium / Large) |
|---|---|---|
| goal space | 50 × 70 × 40 cm | 12 × 12 m (U) → 36 × 24 m (Large) |
| episode horizon | 50 | 700 (U) / 1000 (M, L) |
| action dim | 4 (ee deltas) | 8 (joint torques) |
| reward polarity | **−1 / 0** (sparse) | **0 / +1** (sparse), d ≤ 0.45 m |
| `achieved_goal` | 3-D ee or object pos | 2-D Ant CoM (x, y) |
| obstacles | none | walls — "pretend you meant where you ended up" is **wrong** for HER when you ended up on the wrong side of a wall |

In AntMaze, HER is a known failure case in the literature (Andrychowicz 2017 § 7, Plappert 2018, Trott 2019, Yang 2021): success rates collapse from ≈ 0.85 on UMaze to ≈ 0.1 on Large with standard HER+DDPG, and credit assignment — "which junction did the ant turn left when it should have turned right?" — is the canonical hard sub-problem. This is *exactly* the regime where (a) a VLM-localised corrective goal should provide signal HER cannot, and (b) a sim-verifier can cheaply confirm the suggestion (the maze layout is known and step cost is < 1 ms).

Reference for the "HER struggles on AntMaze" claim already in our bibliography (`L2_bibliography.md`): Pignatelli 2023 (credit-assignment survey, arXiv 2312.01072) and Mesnard 2021 (counterfactual credit assignment, ICML). Concrete AntMaze numbers come from D4RL (Fu 2020, arXiv 2004.07219) and HIRO / RIS variants — to be added to the bibliography under thread 2.

---

## 2. Code audit — what assumes Fetch

Files inspected (all under `/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/`):

- `src/envs/wrappers.py` — env factory + `FlattenGoalObs` + `FrameCapture`.
- `train.py` — main loop + `_build_cf_provider`.
- `configs/base.yaml` — top-level config.
- `src/buffers/her_buffer.py` — vanilla HER relabeler.
- `src/buffers/counterfactual_buffer.py` — CF-HER (`_build_trajectory_dict` is Fetch-pinned).
- `src/vlm/oracle_cf.py` — `oracle_cf_push`, `oracle_cf_pick_and_place`, `oracle_cf_slide`, `oracle_cf_reach`.
- `src/vlm/counterfactual.py` — VLM prompts (`ACHIEVED_GOAL_PROMPT`, `ALL_PROMPT`, `ACTION_PROMPT`, `JUDGE_PROMPT`).
- `src/vlm/verified_counterfactual.py` — sim verifier + `reconstruct_snapshot_for_synthetic_episode`.
- `modal_app.py` — Modal image spec.

The wrappers themselves are **largely env-agnostic**: `FlattenGoalObs` reads dims from `env.observation_space["achieved_goal"].shape[0]` and `observation_space["observation"].shape[0]`, so the obs layout transition (Fetch 25+3+3=31-D → AntMaze 27+2+2=31-D — coincidentally identical) needs zero wrapper changes. The places where Fetch is hard-coded:

1. **`src/vlm/oracle_cf.py`** — `_X_LO`, `_Y_LO`, `_Z_LO` workspace clip (Fetch table), `oracle_cf_push/pnp/slide/reach` are all task-specific.
2. **`src/buffers/counterfactual_buffer.py:_build_trajectory_dict`** — comment "Fetch: obs[0:3]=ee_pos, achieved_goal=object_pos". For AntMaze: obs[0:2]=Ant CoM xy = `achieved_goal`; obs[2:15] = ant joint angles; obs[15:27] = joint velocities. No ee/object distinction. The trajectory-dict schema should grow an `agent_pos` field and drop the `ee_pos/object_pos` distinction for maze envs.
3. **`src/vlm/counterfactual.py` prompts** — `ACHIEVED_GOAL_PROMPT` explicitly says "Fetch workspace x ∈ [1.05, 1.55] m ...". `ACTION_PROMPT` describes a 4-D ee-delta+gripper. `JUDGE_PROMPT` similarly bakes Fetch geometry.
4. **`src/vlm/verified_counterfactual.py`** — three places matter:
   - `success_threshold=0.05` default (AntMaze uses **0.45 m**).
   - The success check: `if rew >= -1e-6: verified = True`. On Fetch (rewards ∈ {−1, 0}), `rew >= -1e-6` correctly fires only on success. **On AntMaze (rewards ∈ {0, 1}), this same check fires every step** — both 0 and 1 are ≥ −1e-6. The verifier would mark every counterfactual as "verified" within step 0. This is the single most dangerous porting bug.
   - `reconstruct_snapshot_for_synthetic_episode` is hard-coded to `"object0:joint"`, a Fetch-specific freejoint name. AntMaze has no such joint; the Ant has the freejoint `"root"` and 8 hinges. For AntMaze the "kinematic reconstruction" approach should be replaced (or just dropped) in favour of always using `snapshot_from_env(training_env)` at the failure step, since the Ant's pose dynamics matter for joint-torque rollout (unlike Fetch where the gripper-mocap dominates).
5. **`train.py:_build_cf_provider`** — `if is_verified and variant not in ("all","action"): variant = "all"`. For AntMaze the 8-D joint-torque corrective action is **not VLM-friendly**. Verified-CF on AntMaze should ship `corrective_position` (xy) and use a **short hand-coded controller** (e.g. PD toward the corrective xy) for the verification rollout, not a VLM-proposed 8-vector. This is the second non-trivial design change.
6. **`configs/base.yaml`** — `env.name`, `env.max_episode_steps=50`, `env.goal_distance_threshold=0.05`, `sac.gamma=0.98`, and `training.total_steps=1_000_000` all encode Fetch assumptions. AntMaze needs `max_episode_steps ∈ {700, 1000}`, `goal_distance_threshold=0.45`, `gamma ≈ 0.99` (longer horizon), and 2–5 M steps depending on size.

Wrapper / agent code (`src/agents/SAC`, `src/buffers/*` other than CF) appears env-agnostic — they read shapes from the env. No SAC changes anticipated.

---

## 3. Dependencies — already there (lucky)

```text
gymnasium_robotics: 1.4.2     # confirmed
gymnasium:          1.3.0
mujoco:             3.8.1
```

The setup-time warning about pinning to `gymnasium-robotics==1.2.0` for "v1 reproducibility" applies only to **Adroit** (relocate / hammer / door) dense-reward changes — not Fetch v4 and not AntMaze. I verified that `gym.make("FetchPickAndPlace-v4")` still resolves to the same observation layout (25 + 3 + 3) and returns `compute_reward = -1.0` for non-success, i.e. **Fetch reproducibility is preserved** at gymnasium-robotics 1.4.2. AntMaze envs register cleanly: `AntMaze_UMaze-v4`, `AntMaze_Medium-v4`, `AntMaze_Large-v4` all work (v5 is also available; v4 is the documented stable goal-conditioned variant). **No dependency upgrade is needed.**

A v4 deprecation warning is emitted; we should pin to v4 in configs and ignore the warning for reproducibility with published numbers.

---

## 4. Oracle-CF design for AntMaze (the "perfect" ceiling)

The maze layout is **completely accessible at runtime**:

```python
m = env.unwrapped.maze
m.maze_map            # nested list of ints: 0=floor, 1=wall, r=reset, g=goal
m.maze_size_scaling   # cell size in metres (e.g. 4.0 for UMaze)
m.x_map_center, m.y_map_center  # world-frame offset
m.unique_goal_locations         # list of np.array([x, y]) — feasible goals
```

That means we can compute an **exact geodesic distance map** from every reachable cell to the goal (BFS on the wall-graph), and at any failure timestep return the **next cell on the optimal path from the ant's current cell**. This is strictly stronger than Fetch's oracle-CF: there it's a hand-derived heuristic (midpoint, mid-air pocket), here it's *literally optimal* for the navigation sub-problem.

```python
def oracle_cf_antmaze(trajectory):
    """Perfect-information oracle for AntMaze."""
    maze       = trajectory["maze_map"]          # 2D int array
    cell_size  = trajectory["maze_size_scaling"]
    origin_xy  = trajectory["maze_origin_xy"]    # (-x_map_center, -y_map_center)
    pos_xy     = trajectory["achieved_goals"]    # (T, 2)
    goal_xy    = trajectory["desired_goal"]      # (2,)
    T          = trajectory["T"]

    # 1) Convert continuous (x, y) into integer (row, col) cells.
    def world_to_cell(xy):
        c = int((xy[0] - origin_xy[0]) / cell_size)
        r = int((xy[1] - origin_xy[1]) / cell_size)
        return (r, c)

    # 2) BFS from goal cell — geodesic distance over wall-free cells.
    dist, parent = bfs_geodesic(maze, world_to_cell(goal_xy))

    # 3) Find the failure frame: the timestep where geodesic distance
    #    to goal *stops decreasing* (the ant got stuck / turned wrong).
    geo = np.array([dist.get(world_to_cell(p), np.inf) for p in pos_xy])
    if not np.any(np.isfinite(geo)):
        return None
    # Failure = first frame where the geodesic distance stagnates / increases
    # for >= W steps after a previous improvement.
    k = detect_geo_stagnation(geo, window=20)

    # 4) Corrective goal = world-frame centre of the *next* cell on the
    #    optimal path from cell(pos[k]) toward the goal.
    cell_k    = world_to_cell(pos_xy[k])
    next_cell = parent.get(cell_k)  # one step closer to goal
    if next_cell is None:
        return None
    cf_xy = cell_to_world(next_cell, cell_size, origin_xy)
    return [(int(k), cf_xy.astype(np.float32), 1.0)]
```

Two implementation notes:
- The `_build_trajectory_dict` schema needs `maze_map`, `maze_size_scaling`, `maze_origin_xy` plumbed through. Source: `env.unwrapped.maze.maze_map`, etc. Cheap to add — under 20 LOC in `counterfactual_buffer.py`.
- The failure-frame detector should be **geodesic-stagnation**, not Euclidean closest-approach. Euclidean is misleading in mazes (you can be 1 m from the goal but 10 m geodesic-distance away through a wall).

This oracle is the *clean ceiling*: it captures everything the maze structure tells us. If CF-HER + this oracle can't beat HER by ≥ 0.10 on AntMaze-Medium, the credit-assignment hypothesis is falsified for this benchmark too — and the project has its honest negative.

---

## 5. VLM-CF prompt design for AntMaze

Top-down rendered frames (mode `rgb_array`, default AntMaze cam) make the maze layout visually obvious: walls are grey blocks, the Ant is the dark blob, the goal is a red sphere. The VLM should answer in **world-frame (x, y)**, not pixel coords, so we tell it the world bounds.

```
Task: A four-legged ant must navigate a 2-D maze to a red goal sphere. The
maze is shown top-down. Walls are grey blocks; the ant is the dark blob.
The episode succeeds when the ant's centre of mass is within {0.45} m of
the goal.

Maze world-frame bounds: x ∈ [{x_lo}, {x_hi}] m, y ∈ [{y_lo}, {y_hi}] m.
The maze is composed of {N} × {M} cells of size {cell_size} m. ASCII layout
(W = wall, . = floor, S = ant start, G = goal):
{ascii_maze}

{K} keyframes from a FAILED episode are shown in chronological order.
desired_goal = {[gx, gy]}
A failure-detection module identified Frame {failure_frame_index}
(~{failure_frame_pct:.0f}% through the episode) as the critical decision point.

QUESTION: At Frame {failure_frame_index}, what 2-D (x, y) target position
SHOULD the ant have been heading toward — the next waypoint on a viable
path from its current cell to the goal? Return one corridor-centre point
in an *adjacent* free cell, not the goal itself.

Respond with ONLY a JSON object:
{
  "corrective_position": [x, y],
  "explanation": "<one concise sentence naming the junction and direction>",
  "confidence": <float 0–1>
}
```

Key differences from the Fetch prompts:

- `corrective_position` is **2-D**, not 3-D.
- We embed the **ASCII maze layout** in the prompt — gives the VLM the geometry without forcing it to infer walls from pixels alone (we observed in C1v2 that pixel-only spatial reasoning is unreliable).
- We **drop** the `corrective_action` variant for AntMaze. An 8-D joint-torque vector is not VLM-friendly and is empirically wrong-shaped (no VLM will reliably produce stable torques). Verified-CF will instead use a **PD controller toward `corrective_position`** for its rollout (see § 6).
- The "reject teleport" gate (`reject_teleport_radius_m`) becomes "reject if `corrective_position` is within 1 cell of `desired_goal`": the VLM-equivalent of teleport on Fetch is "the next waypoint is the goal itself", which trivialises the CF.

The judge prompt also needs a maze layout block but is otherwise structurally identical.

---

## 6. Verified-CF for AntMaze — replace VLM-action with PD-to-waypoint

The original verified-CF stores a VLM-proposed 4-D Fetch action and replays it. On AntMaze the proposed `corrective_position` (xy waypoint) is the natural unit of CF, but the verifier still needs a *joint-torque action sequence* to roll out. The cheapest, most-honest answer is a **two-component PD controller** in `verified_counterfactual.py`:

1. **Heading PD:** turn the ant body to face `corrective_position`. ≈ 2 of the 8 actuators dominate (the hip rotations).
2. **Forward PD:** alternating leg-swing pattern at a fixed cadence (open-loop ant gait, the standard "walk forward at heading θ" controller from D4RL eval).

This is < 60 LOC. It is *not* a learned policy — it's a hand-tuned controller whose only job is to drive the ant toward the waypoint for N_verify_steps (≈ 100, an order of magnitude longer than Fetch's 50 because AntMaze dynamics are slower). If the sim reports `compute_reward == 1.0` within those steps, the CF is verified.

**The fragile success-check bug must be fixed before anything else.** Current code:

```python
if rew >= -1e-6:                                    # WRONG for AntMaze
    result.verified = True
```

This needs to switch on `env_name` (or be parameterised by `success_reward_value`):

```python
# Fetch: rew == 0 on success, -1 on fail.
# AntMaze: rew == 1.0 on success, 0.0 on fail.
if rew >= self.success_reward_threshold - 1e-6:
    result.verified = True
```

with `success_reward_threshold = 0.0` for Fetch, `1.0` for AntMaze. The `success_threshold` (distance, currently 0.05) similarly becomes 0.45 m for AntMaze.

Snapshotting: AntMaze doesn't have a single freejoint named `object0:joint`. For training we should pipe **live snapshots** from the training env at the failure step (`VerifiedCounterfactualLocalizer.snapshot_from_env`) rather than reconstructing kinematically. This is already supported by the API — `reconstruct_snapshot_for_synthetic_episode` is only used as a smoke-test fallback and can be deprecated for AntMaze.

---

## 7. Modal compatibility

`modal_app.py` installs `libosmesa6-dev`, sets `MUJOCO_GL=osmesa`, `PYOPENGL_PLATFORM=osmesa`. AntMaze uses MuJoCo (the same engine + offscreen renderer Fetch uses) so the existing image works. Memory-side I confirmed AntMaze envs construct + step cleanly on the local box once MUJOCO_GL is unset (local has GLFW). On Modal (no display, osmesa) it should mirror Fetch behaviour exactly. **No image changes anticipated.**

Run cost on Modal A10G: AntMaze episodes are 14–20× longer than Fetch (700–1000 steps vs 50), so for the same `total_steps` budget the wall-clock is dominated not by step count but by SAC update cost (unchanged) — expect **roughly 1.5–2× the per-step time** of Fetch because of larger MuJoCo state (8 DOF instead of 7, more contacts), but the same 1 M agent-step run completes in ~3–4 h on an A10G (vs Fetch's 1.5–2 h). At 2–3 M steps for Medium/Large the wall-clock per seed is 6–12 h. Budget 50 GPU-hours for a 3-seed, 3-method, 3-maze grid.

---

## 8. Phased launch plan

**Day 1 — infra + Oracle-CF baseline.** ~6 hours of coding.
- New file `src/envs/antmaze_wrappers.py` (or extend `wrappers.py` with an env-router). Exposes `make_env('AntMaze_UMaze-v4', …)` returning a `FlattenGoalObs`-wrapped env with `goal_dim=2`.
- New file `src/vlm/oracle_cf_antmaze.py` with BFS-geodesic oracle (§ 4). Register under `_ORACLE_REGISTRY` in `oracle_cf.py`.
- Extend `_build_trajectory_dict` to include `maze_map`, `maze_size_scaling`, `maze_origin_xy`, `agent_pos` for maze envs.
- New config `configs/oracle_cf_antmaze_umaze.yaml` (env.name, max_episode_steps=700, goal_distance_threshold=0.45, sac.gamma=0.99, replay.cf_provider=oracle).
- Launch 3 seeds × {HER baseline, Oracle-CF} on AntMaze-UMaze on Modal. **First read-out at 1.5 h** (UMaze is small).

**Day 2 — VLM-CF + Verified-CF.** ~6 hours.
- Add AntMaze branch in `counterfactual.py` prompts (new `_PROMPT_TEMPLATES_ANTMAZE` dict; gate selection on `env_name.startswith("AntMaze")`).
- Fix the `rew >= -1e-6` bug in `verified_counterfactual.py` (§ 6) + the success-distance threshold parameter.
- Add `VerifiedCounterfactualLocalizer._pd_to_waypoint_action_sequence(snap, waypoint, N)` for the AntMaze controller (open-loop ant gait + heading PD; can lift the controller from `gymnasium_robotics/envs/maze/ant_maze_v4.py:WaypointController` directly — they ship one).
- Launch 3 seeds × {VLM-CF, Verified-CF} on AntMaze-UMaze + AntMaze-Medium.

**Day 3 — scale-up + cross-task transferability (N2-style).** ~3 hours of orchestration.
- Run the full grid: {HER, Oracle-CF, VLM-CF, Verified-CF} × {UMaze, Medium, Large} × {3 seeds} = 36 runs. The N2 narrative writes itself: *same VLM prompt*, *three different maze sizes*, measure success-rate scaling.
- Falsifiers / risks below.

**Total engineering LOC estimate:** ≈ 350 LOC new + ≈ 60 LOC modified across 6 files. **1.5–2 days of focused implementation** before the first AntMaze training launch. **2–3 day wall-clock** to reach a full 3-maze × 4-method × 3-seed paper-grade table.

**API cost estimate:** VLM-CF on AntMaze is *cheaper* than on Fetch per episode (fewer keyframes needed — the maze geometry is in the prompt; we can use K=3 instead of K=5) but episodes are longer, so failed episodes per seed are fewer (≈ 1500 over 1 M steps vs 4000 on Fetch). At cf_call_interval=10 with gpt-4o ≈ \$0.005 / call → \$0.75 per 1 M-step seed → ~\$25 across the whole 3-maze grid. **Verified-CF is roughly the same**, the simulator-verifier is free.

---

## 9. Falsifiers — what would tell us AntMaze isn't the right testbed

1. **HER already saturates on UMaze.** If our HER baseline hits ≥ 0.85 on UMaze within 1 M steps (matching the literature), UMaze is too easy and we should drop it from the headline table — but it stays as a *plumbing sanity check*. Cutoff: HER ≥ 0.80 on UMaze ⇒ medium/large is the comparison ground.
2. **Oracle-CF underperforms HER on AntMaze-Medium.** This would mean *even with perfect geodesic guidance* the SAC value function can't propagate the signal over 1000-step horizons. That's a different bottleneck (function approximation / exploration noise), and AntMaze becomes a story about RL fundamentals rather than CF-HER vs HER. Cutoff: Oracle-CF − HER ≤ +0.05 on Medium ⇒ pivot Day-3 to a different narrative.
3. **VLM-CF cannot beat HER even when Oracle-CF can.** Would mean the VLM's spatial reasoning is the bottleneck, not the mechanism. Salvageable as a "VLM-as-policy" negative — but only if the gap is clean (Oracle − VLM ≥ +0.15).

---

## 10. Risks

- **Pose snapshotting is more invasive than on Fetch.** Live snapshots from the training env at failure time require either a callback exposing the env, or storing per-step `qpos/qvel` in the buffer. The latter is cheap on Fetch but doubles the buffer footprint on AntMaze (27-D state, 8-D action vs 25/4). Plan: store snapshots only at K-th-step granularity (every 50 steps) and reconstruct the failure-step snapshot by stepping forward from the nearest checkpoint. ~50 LOC.
- **Reward-polarity / threshold bug is silent.** The `rew >= -1e-6` mismatch (§ 6) would *not* crash training — it would *silently* mark every verification as a pass, making Verified-CF look identical to VLM-CF in W&B logs. Mitigation: add an explicit `assert sim_success_reward in (0.0, 1.0)` smoke test in `verified_counterfactual.py` *before* the Day-2 launch.
- **AntMaze v4 deprecation.** Gymnasium-Robotics 1.4.2 warns AntMaze_*-v4 is "out of date" and suggests v5. v5 changed Ant observation layout slightly (added contact forces). If we pin to v4 we get the canonical D4RL numbers; if we accidentally pick up v5 our HER baseline won't be comparable to literature. Mitigation: explicit `env_name = "AntMaze_UMaze-v4"` strings in configs and a startup assertion `assert "v4" in env_name`.

---

## Appendix A — exact code locations to touch

| change | file | LOC est |
|---|---|---|
| env router + AntMaze wrapper | `src/envs/wrappers.py` | +40 |
| BFS-geodesic oracle | `src/vlm/oracle_cf.py` (or new file) | +120 |
| `_build_trajectory_dict` maze fields | `src/buffers/counterfactual_buffer.py` | +20 |
| AntMaze VLM prompts | `src/vlm/counterfactual.py` | +80 |
| reward-polarity + dist-threshold + PD controller | `src/vlm/verified_counterfactual.py` | +90 |
| `_build_cf_provider` env-conditional defaults | `train.py` | +15 |
| 3 new configs (`oracle_cf_antmaze_*.yaml`) | `configs/` | +60 |
| Total | | ≈ 425 |

## Appendix B — verified runtime facts (probed in this investigation)

- `gymnasium_robotics.__version__ == "1.4.2"` (already installed; no upgrade required).
- `gym.make("AntMaze_UMaze-v4")` succeeds with obs `Dict{observation:(27,), achieved_goal:(2,), desired_goal:(2,)}`, action `Box(-1, 1, (8,))`, `spec.max_episode_steps == 700`.
- `env.unwrapped.compute_reward(np.zeros(2), np.zeros(2), {})` returns **1.0** for AntMaze; `FetchPickAndPlace-v4` returns **−1.0** when the goal isn't yet reached. Opposite polarities — see § 6.
- `env.unwrapped.maze` exposes `maze_map`, `maze_size_scaling=4.0`, `x_map_center=10.0`, `y_map_center=10.0`, `unique_goal_locations` (7 candidate goals for UMaze), and `compute_reward` source `(distance <= 0.45)`.
- `env.unwrapped.ant_env` is the underlying AntEnv (gymnasium MuJoCo Ant), giving direct access to qpos/qvel for snapshot machinery.
- Fetch v4 reproducibility is preserved at gymnasium-robotics 1.4.2 (same obs shape, same reward source).
