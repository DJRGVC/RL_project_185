# SHARONY_ENVS_SCOUT — porting our pipeline to Sharony et al.'s benchmark envs

**Author:** SHARONY-ENVS-SCOUT (Opus 4.7, 1M-ctx) — read-only investigation
**Date:** 2026-05-12
**Status:** Design doc only. No code changes, no installs, no Modal launches were performed.
**Reads:** `src/envs/wrappers.py`, `src/buffers/her_buffer.py`, `src/buffers/counterfactual_buffer.py`, `src/vlm/oracle_cf.py`, `src/vlm/counterfactual.py`, `src/vlm/verified_counterfactual.py`, `train.py`, `configs/base.yaml`, `agent_reports/L1_sharony_differentiation.md`, `agent_reports/ANTMAZE_PIVOT_PLAN.md`. WebFetch on PyPI (`minigrid`, `ogbench`), GitHub source for OGBench `manipspace`/Scene and MiniGrid DoorKey, and the HTML build of arXiv 2602.01915.

---

## 0. TL;DR

| Question | Answer |
|---|---|
| Can we run our exact pipeline on Sharony's envs as-is? | **No.** Three blocking mismatches per env. |
| Cheapest single-env port? | **OGBench Scene 3** (continuous SAC works) — ~5 days, ~80 GPU-h, ~$40 VLM. |
| Hardest port? | **MiniGrid DoorKey** — requires a new RL algorithm (DQN/IQN) since SAC is continuous-only; our HER buffer + CF buffer + Verified-CF all assume continuous goal-conditioned MDPs. ~10–14 days. |
| Compared to AntMaze pivot? | **AntMaze is materially cheaper** (1.5–2 days infra, ~50 GPU-h) because gymnasium-robotics + Dict obs is already what our HER buffer expects. OGBench's Scene tasks have **no Dict obs and no native `achieved_goal/desired_goal`** — we have to synthesize them. AntMaze ports our pipeline almost verbatim; OGBench requires re-wiring the goal interface. |
| Recommendation | **Path-A (recommended): AntMaze pivot first** (already planned, ~2 days). **Path-B (optional defensive add-on): OGBench Scene 3 only**, scoped to "1 env, 3 seeds, headline plot only", as a Sharony-overlap concession. **Skip MiniGrid for v1.** Fall-back framing if neither lands: position §2 as "we evaluate on the standard sparse-reward goal-conditioned manipulation benchmark; Sharony's envs are non-goal-conditioned and not directly comparable without a goal-interface adapter". |

---

## 1. Package availability (read-only check)

```text
$ pip show minigrid          → WARNING: Package(s) not found: minigrid
$ pip show gym-minigrid      → WARNING: Package(s) not found: gym-minigrid
$ pip show ogbench           → WARNING: Package(s) not found: ogbench
$ pip show gymnasium         → Version: 1.2.1   (note: ours is 1.4.2 in repo venv)
$ pip show mujoco            → Version: 3.8.0
```

**Neither package is installed.** Both are on PyPI and pip-installable:

- `minigrid` (Farama, Python ≥ 3.10) — `pip install minigrid`. Pure-Python, no system deps. **Trivial** to install.
- `ogbench` (Park et al., Python ≥ 3.8) — `pip install ogbench`. Bundles `dm_control`/MuJoCo XML for the manipspace + locomaze + powderworld envs. Same MuJoCo backend we already use for Fetch. **Trivial** to install.

Neither install would break our existing env (Fetch is also MuJoCo via `gymnasium_robotics`). No system-level new deps are required.

**Blockers: none at the install level.** All blockers are at the API/code-port level (§§ 3–4).

---

## 2. API + obs/action space mapping

### 2a. Our Fetch baseline (reference)

| Field | Value |
|---|---|
| Observation space | `Dict{observation: Box(25,), achieved_goal: Box(3,), desired_goal: Box(3,)}` |
| Action space | `Box([-1,1], (4,))` (Δx, Δy, Δz, gripper) |
| Horizon | 50 steps |
| Reward | sparse, `{0 if dist<0.05 else -1}` |
| Frame | `render_mode='rgb_array'` → ~`(480, 480, 3)` RGB via MuJoCo offscreen |
| Goal interface | native — `env.unwrapped.compute_reward(ag, dg, info)` is the source of truth |
| RL algo | SAC (continuous) |
| HER | strategy='future', k=4 |

### 2b. MiniGrid DoorKey (8x8, 12x12, 16x16)

Source: `https://github.com/Farama-Foundation/Minigrid/blob/master/minigrid/envs/doorkey.py` (read via WebFetch).

| Field | Value |
|---|---|
| Observation space | **Dict** `{'image': Box(uint8, (7,7,3)), 'direction': Discrete(4), 'mission': str}` — *partial observation*, no `achieved_goal`/`desired_goal` |
| Action space | **Discrete(7)** — {left, right, forward, pickup, drop, toggle, done} |
| Horizon | `max_steps = 10 * size² ⇒ 640 / 1440 / 2560` for 8/12/16 |
| Reward | `1 − 0.9·step_count/max_steps` on success, else `0` — **time-discounted, NOT sparse {0,−1}** |
| Frame (full grid) | rgb via `env.render(mode='rgb_array')` — `(size*tile, size*tile, 3)` (default tile=32 → 256/384/512 px square) |
| Goal interface | **none native** — success = "agent reaches green goal square after opening the locked door with the key" |
| RL algo (theirs) | DQN, IQN |
| Sharony's HER analog | n/a — DoorKey is non-goal-conditioned; they don't run HER, they prioritize replay |

**Blockers for our pipeline:**

1. **Discrete actions** — our SAC implementation in `src/agents/sac.py` is continuous-only. Either we add a DQN/IQN path (large) or we cast DoorKey into continuous via Gumbel-softmax / continuous relaxation (ugly, no precedent in Sharony).
2. **No native goal interface** — HER fundamentally requires an `achieved_goal/desired_goal` decomposition. To run HER on DoorKey we'd have to synthesize one (e.g. `achieved_goal = (agent_xy, has_key, door_open)`, `desired_goal = (goal_xy, False, True)`) — a non-trivial design decision and not how the env is usually evaluated.
3. **Reward is non-sparse {0, 0.1..1}** — our `compute_reward_fn` plumbing assumes {0, −1} or {0, +1} polarities. Time-discounted positive reward changes the verifier's success check (currently `rew >= -1e-6` — see § 6 of `ANTMAZE_PIVOT_PLAN.md` for the same bug under AntMaze's {0,+1} polarity).
4. **VLM rendering** — top-down grid is fine for VLM consumption (Sharony's "Modified Game" ablation confirms VLMs see DoorKey clearly). Not a blocker.

### 2c. OGBench Scene 3 / 4 / 5

Source: `https://github.com/seohongpark/ogbench` master branch — `ogbench/manipspace/envs/scene_env.py` and `manipspace_env.py` (WebFetch).

| Field | Value |
|---|---|
| Observation space | **flat `Box`** — concatenated joint positions + velocities + end-effector pose + gripper opening + per-object states (cube positions, button states one-hot, drawer position, window position). **NOT a Dict**, **no native `achieved_goal`/`desired_goal`**. |
| Action space | `Box([-1,1], (5,))` — 3-D ee Δposition + 1-D ee Δyaw + 1-D gripper |
| Horizon | not defined in the env class; set externally (Sharony's paper does not state, but standard OGBench is 750–1000 steps for "play" mode) |
| Reward | **multi-task sparse**: `reward = Σ successes − N_subtasks` ∈ {−N, …, 0}. For Scene there are typically 3–4 sub-conditions (button, drawer, cube pose, window). Success = all sub-conditions met. |
| Frame | `64 × 64 × 3` RGB (per OGBench project page) — note: this is much smaller than Fetch's ~480×480; VLM keyframes will be **noticeably lower resolution** |
| Goal interface | **none native** — multi-task success conditions are the "goal"; there is no scalar `desired_goal` vector |
| Robot | UR5e + Robotiq 2F-85 gripper |
| RL algo (theirs) | SAC, TD3 |
| Sub-tasks | Sharony's Scene-3 = "rearrange-medium", Scene-4 = "put-in-drawer", Scene-5 = "rearrange-hard" |

**Blockers for our pipeline:**

1. **No native `achieved_goal`/`desired_goal`.** This is the biggest issue. Our HER buffer (`src/buffers/her_buffer.py`) and `FlattenGoalObs` wrapper (`src/envs/wrappers.py`) both expect a Dict-obs env that exposes these. For Scene we must:
   - Pick an `achieved_goal` projection (e.g. cube positions + drawer open-frac + button states + window angle, dim ≈ 8–12 depending on the sub-task).
   - Define a synthetic `desired_goal` (read the sub-task spec from the env's reward function — feasible but ~30 LOC per Scene task).
   - Write a `compute_reward(ag, dg, info)` that mirrors the env's success conditions. This is the load-bearing surgery: HER fundamentally needs `compute_reward` to be computable for *arbitrary* `(ag, dg)` pairs, not just the live one. For multi-condition tasks this means we ship our own `compute_reward` that lifts the env's success check into a pure function.
2. **5-D action (not 4-D Fetch).** Minor — SAC reads `env.action_space.shape[0]` already (`train.py:337`). The Fetch oracles and prompts that hard-code 4-D (`ACTION_PROMPT` in `counterfactual.py`) need a Scene branch. **Manageable.**
3. **64×64 keyframes** — lower than what GPT-4o is calibrated for. Our existing prompts assume the VLM can resolve a ~5 cm block in a ~480px frame. Will the VLM see a Scene cube at 64×64? Probably yes but it's an open empirical question. Risk: VLM-CF accuracy collapses on small frames. Mitigation: ask the env to render at 256×256 (OGBench supports custom render shape) for VLM input only, while the policy stays state-based.
4. **Multi-condition reward** — `reward = sum(successes) - n_subtasks` ∈ {−3, ..., 0} or {−4, ..., 0}. Our `compute_reward_fn` plumbing handles single-condition sparse {0,−1}. For HER + our oracle, the cleanest path is to **project to the *primary* sub-condition for headline runs** (e.g. for Scene-4 "put-in-drawer", `achieved_goal = cube_in_drawer_indicator + cube_xyz`, `desired_goal = (1, cube_target_xyz)`) and pull the multi-condition story into an appendix.
5. **OGBench is not built on gymnasium-robotics.** It uses `dm_control` patterns wrapped to look gym-like. Our `import gymnasium_robotics` line in `verified_counterfactual.py:_ensure_env` (line 186) is Fetch-specific. We'd need a Scene branch in `_ensure_env` that does `import ogbench` instead and constructs `gym.make("scene-play-singletask-task3-v0", ...)` (or whatever the exact ID is — confirm post-install). **~20 LOC fix, low risk.**
6. **Snapshotting.** Scene uses `dm_control` MuJoCo physics under the hood. Our `MujocoSnapshot(qpos, qvel, time, mocap_pos, mocap_quat, goal)` schema in `verified_counterfactual.py:84-94` is Fetch-specific (mocap-driven ee). Scene uses **direct torque/IK control on UR5e joints**, not a mocap-target. So `mocap_pos` / `mocap_quat` are likely absent. The snapshot schema must become env-conditional: Fetch keeps mocap; Scene snapshot is `(qpos, qvel, time, sub_task_state, goal_spec)`. **~80 LOC fix.**

---

## 3. Codebase porting cost — per-file diff matrix

Files involved (line counts: `wrappers.py:125`, `her_buffer.py:113`, `counterfactual_buffer.py:610`, `oracle_cf.py:256`, `counterfactual.py:931`, `verified_counterfactual.py:475`, `train.py:801`, `configs/base.yaml`).

| File | MiniGrid DoorKey | OGBench Scene 3 | OGBench Scene 4/5 (incr. on Scene 3) |
|---|---|---|---|
| `src/envs/wrappers.py` | new `MiniGridGoalAdapter` wrapper (synthesize `(agent_xy, has_key, door_open)` as `achieved_goal`); `FlattenGoalObs` rewrite to handle Discrete image obs (~+80 LOC) | new `OGBenchSceneGoalAdapter` (extract cube/button/drawer/window state into `achieved_goal`); add `make_env` branch for `scene-*-v0` (~+60 LOC) | +10 LOC per task (different `achieved_goal` projection) |
| `src/buffers/her_buffer.py` | **structural rewrite** — `desired_goal` is mixed-type (xy + booleans). Sparse-reward recomputation needs Discrete-action branch (~+50 LOC) | Recompute against multi-condition reward; works with float/bool projection (~+25 LOC) | +0 (uniform interface) |
| `src/buffers/counterfactual_buffer.py` | `_build_trajectory_dict` rewrite — no `ee_pos`/`object_pos`. Use `agent_pos` and grid-cell coords (~+40 LOC) | `_build_trajectory_dict` rewrite — `ee_pos` + per-object positions; drop `object_pos` singular (~+40 LOC) | +5 LOC per task |
| `src/vlm/oracle_cf.py` | new `oracle_cf_doorkey` — A* on the grid from agent_pos to (key, then door, then goal); 3-stage waypointing (~+150 LOC) | new `oracle_cf_scene3` — "put cube on target" heuristic = midpoint(cube_pos, target_pos) at frame of max ee-cube distance, similar to Push (~+80 LOC) | +60 LOC per task (Scene-4: heuristic for drawer-open + cube-into-drawer; Scene-5: harder, multi-cube rearrange) |
| `src/vlm/counterfactual.py` | new `_PROMPT_TEMPLATES_DOORKEY` dict — discrete-action prompts (return action index ∈ {0..6}), grid-coord corrective_position (~+200 LOC across narrative/action/achieved-goal/judge variants) | new `_PROMPT_TEMPLATES_SCENE` — 5-D action prompts, sub-task-aware corrective targets (~+150 LOC) | +80 LOC per task |
| `src/vlm/verified_counterfactual.py` | **fundamental rewrite** — snapshot is grid state (agent_pos, has_key, door_open), not MuJoCo qpos. Verify by stepping the discrete env with VLM action sequence. Success check `rew > 0` (NOT `rew >= -1e-6` — same polarity bug as AntMaze). (~+200 LOC; ~80 LOC refactor for env-conditional snapshot) | snapshot schema becomes env-conditional (no mocap for Scene). Success check `rew >= -1e-6` only correct if we re-project to single-condition reward; otherwise `rew == 0` is the success threshold. (~+100 LOC) | +30 LOC per task |
| `train.py` | branch `_build_cf_provider` and main loop on `discrete_action` (no SAC, dispatch to DQN/IQN). **Requires a new agent.** (~+80 LOC for dispatch; **plus** a new DQN/IQN agent file ~+400 LOC, or import from CleanRL/SB3) | small branches — env-conditional `compute_reward_fn`, env-conditional `success_threshold` (~+30 LOC) | +5 LOC per task |
| `src/agents/` | **new file** `dqn.py` or `iqn.py` (~+400 LOC) or import `stable_baselines3.DQN` | none (SAC works) | none |
| `configs/` | 3 new configs (`oracle_cf_doorkey_8x8.yaml`, `_12x12.yaml`, `_16x16.yaml`) — different `total_steps`, `gamma`, `algo: dqn` (~+30 LOC each) | 1 new config (`oracle_cf_scene3.yaml`) (~+30 LOC) | +30 LOC per task |
| **Total new+modified LOC** | **≈ 1,100–1,500 LOC** | **≈ 500–650 LOC** | **+250 LOC per additional Scene task** |
| **Days of focused implementation** | **8–14 days** (DQN port dominates) | **3–5 days** | +1.5 days per additional Scene task |

### 3b. Honest port-difficulty rating

| Component | MiniGrid | Scene 3 | Comment |
|---|---|---|---|
| Env wrapper | **Hard port** | **Medium port** | Both need a synthesized goal interface; MiniGrid is harder because obs is partial-grid+direction, not state. |
| HER buffer | **Hard port** | **Medium port** | Mixed-type goals (MiniGrid) are nastier than multi-condition float goals (Scene). |
| Oracle CF | **Medium port** (A* is well-defined) | **Medium port** (heuristic per sub-task) | Both have a clean ground-truth path; Scene's is just less canonical. |
| VLM prompt | **Medium port** | **Medium port** | Both need new templates; both are within precedent. |
| Verified CF | **Hard port** (snapshot rewrite + discrete-action rollout + reward polarity) | **Medium port** (snapshot rewrite + reward polarity) | The polarity bug from `ANTMAZE_PIVOT_PLAN.md` § 6 / § 10 applies to both. |
| RL algorithm | **Hard port (new agent)** | **Easy** (SAC unchanged) | This single bullet is what makes MiniGrid 2–3× the cost of Scene 3. |

---

## 4. Compute + training cost

Sharony's paper used a mix of A100 / A40 / A4000 GPUs (paper § "Computational Resources"); they do not publish per-run wall-clock. Our Modal A10G runs Fetch SAC at ~1.5–2 h / 1 M steps. Estimates below use the heuristic "wall-clock per step scales with action-dim × MuJoCo contacts; algorithm-update cost scales with batch × hidden-dim", which gives the per-env multipliers in column 3.

| Env | Steps to convergence (literature / Sharony) | Wall-clock per seed (A10G) | GPU-h per 3-seed × 5-method ablation | API $ for VLM-CF (1 seed) | API $ for full ablation |
|---|---|---|---|---|---|
| MiniGrid DoorKey-8x8 | 0.5 M (Sharony shows VLM-RB peaks here) | 1 h (Discrete + small NN, fast) | 15 h × {HER, CF-HER, VLM-CF, Verified-CF, Sharony-RB} × 3 seeds = ~45 h | ~$8 (smaller failure rate, ~600 failed episodes/seed) | ~$120 across 3 grid sizes × 5 methods |
| MiniGrid DoorKey-12x12 | 1 M | 2 h | 30 h | ~$15 | (rolled into ↑) |
| MiniGrid DoorKey-16x16 | 2 M | 4 h | 60 h | ~$25 | (rolled into ↑) |
| OGBench Scene 3 | 1 M | ~2.5 h (5-D action, larger state, similar update cost) | 37 h | ~$20 | ~$100 across 3 tasks × 5 methods |
| OGBench Scene 4 | 1 M | ~2.5 h | 37 h | ~$20 | (rolled into ↑) |
| OGBench Scene 5 | 2 M | ~5 h | 75 h | ~$40 | (rolled into ↑) |

**Aggregate compute if we did everything (MiniGrid + OGBench, 3 seeds × 5 methods):**

- ~285 GPU-hours on A10G (~$140 at $0.50/h on Modal).
- ~$220 in OpenAI API calls (GPT-4o) for VLM-CF runs.

**Compute if we did OGBench Scene 3 only (1 env, 3 seeds, 5 methods):**

- ~37 GPU-h, ~$20 API. **Fits comfortably in a week of evening runs.**

---

## 5. Comparison table — port cost vs paper impact

| Env | Algo change? | New oracle? | New VLM prompt? | Verified-CF feasible? | Total LOC | Days impl | GPU-h | $ | Risk |
|---|---|---|---|---|---|---|---|---|---|
| **MiniGrid DoorKey 8x8** | **Yes** — DQN/IQN required | Yes — A* on grid | Yes — discrete-action template | Yes (grid snapshot is trivial; discrete-action rollout) | ~1,100 | 8–10 | 45 | $10 | **High** — DQN port has highest failure mode; discrete-CF is unprecedented for our framework |
| **MiniGrid DoorKey 16x16** | (rolls into ↑) | (same A*) | (same template) | (same) | +60 | +1 | 60 | $25 | High |
| **OGBench Scene 3** | **No** — SAC works | Yes — Push-style midpoint heuristic | Yes — 5-D action + sub-task aware | Yes (UR5e snapshot, no mocap) | ~500 | 3–5 | 37 | $20 | **Medium** — goal-interface synthesis is the load-bearing step |
| **OGBench Scene 4** | No | Yes — drawer-aware | Yes — drawer template | Yes (same) | +250 | +1.5 | 37 | $20 | Medium |
| **OGBench Scene 5** | No | Yes — multi-cube | Yes — multi-cube template | Yes (same) | +250 | +1.5 | 75 | $40 | Medium-high (multi-cube success is the hardest pure-manipulation task in Sharony's table) |

---

## 6. Compare to the AntMaze pivot (already planned)

Per `agent_reports/ANTMAZE_PIVOT_PLAN.md`:

| Dimension | AntMaze (UMaze + Medium + Large, 3 mazes × 4 methods × 3 seeds = 36 runs) | OGBench Scene 3 only (5 methods × 3 seeds = 15 runs) |
|---|---|---|
| Engineering LOC | ~425 | ~500 |
| Days of infra | 1.5–2 (already estimated for the 3-maze grid) | 3–5 (single env) |
| GPU-h | ~50 (across 3 mazes) | ~37 (single env) |
| API $ | ~$25 | ~$20 |
| Algo change | **None** — SAC unchanged | None — SAC unchanged |
| HER goal interface | **Native** — gymnasium_robotics gives `{observation, achieved_goal, desired_goal}` out of the box | **Synthesize** — we have to define and ship a `compute_reward(ag, dg, info)` that mirrors Scene's multi-condition success |
| Oracle CF | Clean — BFS on maze layout, *literally optimal* | Heuristic — midpoint-style; not provably optimal |
| Verified CF | Clean (after reward-polarity fix) — same MuJoCo backend, same snapshot mechanics | Snapshot schema rewrite (no mocap, sub-task state) — ~80 LOC |
| Sim backend | `gymnasium_robotics` + MuJoCo — **already in our deps** | `ogbench` + `dm_control` — new pip install |
| Paper narrative | "Same method scales from FetchPush to AntMaze-Large; oracle gives a clean upper bound; method works in long-horizon credit-assignment regime where HER is known to struggle" | "Same method works on Sharony's exact benchmark — direct head-to-head" |
| Reviewer-defense value | **Strong but indirect** — shows we go beyond Fetch but doesn't address "you didn't run on their envs" head-on | **Strong and direct** — silences the specific "you didn't run on Sharony's envs" critique |
| Risk that we don't reach a result by deadline | **Low** (1.5–2 day infra, well-scoped) | **Medium** (3–5 day infra; goal-interface synthesis can stretch) |

**Verdict:** AntMaze is materially cheaper and lower-risk per unit of methodological reach, *but* OGBench Scene 3 specifically buys us the head-to-head with Sharony that AntMaze does not. The two are **complementary, not substitutes**.

---

## 7. Sharony's reported numbers — VLM-RB vs baselines

From the HTML build of arXiv 2602.01915v1 (Table 1, paraphrased):

| Algo family | Task | VLM-RB success-rate gain vs UER / PER | Sample-efficiency gain |
|---|---|---|---|
| DQN/IQN | DoorKey-8x8 | +0.0% / +0.0% (UER already saturates) | +19–23% |
| DQN/IQN | DoorKey-12x12 | **+61.3% / +22.0%** | +32–53% |
| DQN/IQN | DoorKey-16x16 | **+241.7% / +70.8%** | +24–38% |
| SAC/TD3 | Scene-3 | +0.0% / +0.0% (already saturates) | +21–41% |
| SAC/TD3 | Scene-4 | **+22.0% / +2.0%** | +20–45% |
| SAC/TD3 | Scene-5 | **+119.4% / +49.1%** | +18–46% |

Reproduction targets if we run on these envs:

- **Scene-3:** UER already saturates → headroom is **sample efficiency only**, no headline success-rate gap to close. Risky as a single env to bet on for "we beat Sharony" — but **honest as a sanity check**: our method should match their numbers and show similar sample-eff gain.
- **Scene-4:** modest +22% headline gain over UER → some headroom; we can hope to match or improve.
- **Scene-5:** **biggest headline gain (+119% vs UER)** — this is the env most likely to differentiate our failure-direction signal from their success-direction signal. *But* it's also the hardest port (multi-cube rearrange) and the longest training (~5 h × 3 seeds × 5 methods = 75 GPU-h).
- **DoorKey-16x16:** the most dramatic headline (+241% vs UER) — but requires a DQN port we don't have.

**Strategic note:** Sharony chose Scene-3 / 4 / 5 to span "easy → medium → hard"; we should mirror that. If we only do **one** Scene task, Scene-4 ("put-in-drawer") is the sweet spot: medium difficulty, modest gain headroom, single-sub-task structure that maps cleanly onto a synthesized `achieved_goal`/`desired_goal` pair (`cube_xy_in_drawer_frame`). Scene-3 is a sanity-check no-op; Scene-5 is a money-no-object stretch.

---

## 8. Phased recommendation

### Phase A — week 1 (recommended, already planned): AntMaze pivot

This is `ANTMAZE_PIVOT_PLAN.md`. ~1.5–2 days infra + 2–3 days wall-clock to a 3-maze × 4-method × 3-seed grid. **Ship this regardless of OGBench decisions.** Buys us long-horizon credit assignment without touching the RL algorithm.

### Phase B — week 2 (defensive add-on, recommended): OGBench Scene 3 + Scene 4

Two tasks, 5 methods (HER baseline, CF-HER, VLM-CF, Verified-CF, Sharony-VLM-RB reimplementation), 3 seeds = 30 runs. ~75 GPU-h, ~$40 API. **Ports our method onto Sharony's exact benchmark for direct head-to-head.** Skips Scene-5 (75 GPU-h alone) and skips MiniGrid (DQN port).

- Day 1 (~6 h coding): `OGBenchSceneGoalAdapter` in `src/envs/wrappers.py`; project Scene-3 sub-task state into `(achieved_goal, desired_goal)`; write `compute_reward_scene3(ag, dg, info)` as a pure function.
- Day 2 (~6 h coding): `oracle_cf_scene3` (Push-style midpoint heuristic on the primary cube); Scene-specific VLM prompts; `_PROMPT_TEMPLATES_SCENE` block in `counterfactual.py`.
- Day 3 (~6 h coding): env-conditional snapshot schema in `verified_counterfactual.py` (drop mocap requirement); fix reward-polarity check (`rew >= -1e-6` → `rew >= 0` since Scene reward ∈ {−N..0}). Run 3 seeds × HER baseline as the sanity check.
- Day 4: launch full 5-method × 3-seed grid for Scene-3.
- Day 5: add Scene-4 (~+250 LOC, mostly oracle/prompt deltas) and repeat.

### Phase C — week 3 (optional stretch): OGBench Scene 5

If Scene-3/4 land cleanly *and* show our failure-direction CF differentiates from Sharony's success-direction. Otherwise skip — Scene-5 is +1.5 days infra + 75 GPU-h for one extra data point.

### Phase D — DEFER (do not pursue for v1): MiniGrid DoorKey

Requires a DQN/IQN port (~+400 LOC for a new agent) and a fundamental rewrite of HER + Verified-CF for discrete actions. **8–10 days of focused infra for a single env family.** Not worth it for a reviewer-defense response unless we have 3 weeks of clear runway. **Falsifier:** if MiniGrid becomes essential (e.g. a reviewer specifically demands "show DQN+CF-HER works"), the cleanest path is to import `stable_baselines3.DQN` rather than writing one, which collapses to ~+150 LOC of glue.

### Phase E (fallback) — defensive Fetch-only framing in §2

If none of Phases A–C land before the deadline, the §2 framing becomes:

> "We evaluate on Gymnasium-Robotics Fetch, the standard sparse-reward continuous-action goal-conditioned manipulation benchmark. Sharony et al. (2026) evaluate on MiniGrid DoorKey (discrete-action gridworld with DQN/IQN) and OGBench Scene (multi-task manipulation with no native goal-conditioned interface). The two environment suites have **disjoint structural assumptions** — HER and our counterfactual-HER mechanism require a native `(observation, achieved_goal, desired_goal)` decomposition and a sparse `compute_reward(ag, dg, info)` that Fetch provides natively and Sharony's envs do not. Our contribution is therefore best read as **complementary** to VLM-RB, addressing the goal-conditioned manipulation regime they did not cover, rather than a direct head-to-head replacement."

This is **defensible but weak** — reviewers will read it as "they didn't do the work". Use only if Phase A *and* Phase B both fail.

---

## 9. Three falsifiers per env (what would tell us this is the wrong testbed)

### MiniGrid DoorKey

1. **DQN baseline saturates 8x8 within our compute budget** — then 8x8 is sanity-check only, story rides on 12x12/16x16. (Sharony already shows this; UER hits ceiling on 8x8.)
2. **Synthesized goal-interface is ambiguous** — if `achieved_goal = (agent_xy, has_key, door_open)` doesn't recover the env's success criterion under `compute_reward(ag, dg, info)` (e.g. spatial reachability matters), our HER signal is corrupt and the whole framework is moot. **Mitigation: unit test `compute_reward` against `env.unwrapped` rewards on 100 random trajectories before any training.**
3. **VLM cannot resolve a 32×32 corner-tile in the rendered grid** — keyframes at default tile_size=32 give a 256–512px square; the key/door symbols are 32×32 sprites. Within GPT-4o's resolution band but borderline. **Falsifier: VLM localization accuracy < 50% on a 10-episode hand-labelled set before we trust CF-HER outputs.**

### OGBench Scene 3 / 4 / 5

1. **Synthesized `compute_reward(ag, dg, info)` doesn't match the env's success check on hindsight goals.** This is the same risk as MiniGrid: if our `achieved_goal/desired_goal` projection loses information that the env uses to declare success, HER relabels are bogus. **Mitigation: 100-trajectory consistency test before training.**
2. **64×64 default render is too low-resolution for the VLM to detect a 2 cm cube on the table.** OGBench supports higher-res rendering, but the *trained* policy receives 64×64 (or state-only). If we ship a higher-res render *only for VLM input*, that's a free fix; if not, the VLM-CF path collapses. **Falsifier: VLM correctly localizes "which cube is the agent holding" on < 70% of failed episodes in a 30-episode hand-labelled set.**
3. **Sharony's UER already saturates Scene-3 within their training budget** (per Table 1: +0.0% gain). If we use Scene-3 alone, *no method* can show a headline success-rate gap; we'd have to rely on sample-efficiency curves. **Mitigation: pair Scene-3 with Scene-4 in any results table to ensure at least one task has measurable headroom.**

---

## 10. Closing recommendation (1 paragraph)

**Pursue Phase A (AntMaze pivot) immediately and unconditionally** — it's already planned, cheapest at ~1.5–2 days infra and ~50 GPU-h, ports our pipeline almost verbatim (Dict obs + sparse reward + MuJoCo backend are all native to gymnasium-robotics, no new deps), and gives us the long-horizon credit-assignment regime the §2 narrative needs. **Pursue Phase B (OGBench Scene 3 + Scene 4) in week 2** as the direct head-to-head with Sharony — it adds ~5 days of infra and ~75 GPU-h, the chief risk is goal-interface synthesis (Scene tasks don't expose `achieved_goal`/`desired_goal` natively), and the chief reward is silencing the "you didn't run on their envs" reviewer critique with our own numbers on two of the three Scene tasks Sharony evaluated. **Skip Phase D (MiniGrid)** for v1 — the DQN port is 8–10 days and a discrete-action CF-HER is unprecedented for our framework; the marginal paper value does not justify the marginal cost in a NeurIPS-deadline regime. If Phase B slips past day 5, **fall back to the defensive framing in Phase E**: argue Sharony's envs and ours have disjoint structural assumptions (goal-conditioned vs not, sparse-binary-reward vs multi-condition-shaped, continuous-Fetch vs discrete-MiniGrid + multi-task-Scene), and that the two contributions are complementary rather than competing. Order of operations across the next two weeks: AntMaze (Phase A) → OGBench Scene 3 (Phase B Day 1–4) → OGBench Scene 4 (Phase B Day 5) → write the comparison table, ship.
