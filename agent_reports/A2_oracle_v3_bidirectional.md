# A2 Report — Oracle v3 (contact-aware) + Bidirectional Semantic Buffer

**Agent:** A2
**Branch:** `agent/a2-oracle-bidir`
**Worktree:** `/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/.claude/worktrees/agent-ab31af4cf7eee1b43`
**Commits:** `b5a2fe3` (Oracle v3 + bidir buffer), `f46b926` (modal spawn_one)
**Status:** Implementation, smoke tests, and Modal verification launches complete.

---

## 1. Design Rationale

### Why contact-aware is better than ballistic+argmin for Push / PickAndPlace

The v2 `GoalDistanceLocalizer` is two-phase: a *ballistic* check that fires when an object keeps moving after a velocity peak (correctly catches FetchSlide throws), with an *argmin distance* fallback for everything else. For Push and PickAndPlace the ballistic phase essentially never fires (table friction halts the object once contact is lost), so v2 reduces to argmin.

**Argmin is the wrong target for contact tasks** because:
- The argmin frame is when the *object* was closest to the goal. In a failed Push episode that frame is often *inside* the successful push phase, before the agent loses control of the block.
- Boosting argmin teaches the critic about a geometric near-miss. It does **not** boost the moment the policy actually made a mistake (e.g. brushing the block off-axis, pushing past it, or — for PickAndPlace — releasing the gripper too early).

**The contact-aware (v3) insight:** in contact tasks, the most diagnostic failure signal is *contact loss while the object is still off-goal*. This is the moment a control policy made a manipulation error. Boosting transitions around contact loss trains the critic to penalise "ee escaping object while object is far from goal", which is the exact failure mode the policy needs to learn to avoid.

The Fetch observation vector has a known layout for Push/Slide/PickPlace (`[0:3]` grip_pos, `[3:6]` object_pos), so we can compute `ee_object_distance` and `object_goal_distance` per-step from the same buffer data the policy already sees — no extra sensors needed.

**Algorithm (Oracle v3 contact-loss phase):**
1. For each timestep, compute `ee_obj_dist = ||obs[0:3] − obs[3:6]||`.
2. A step is "in contact" if `ee_obj_dist < CONTACT_DISTANCE` (`0.05 m`, matches Fetch goal_distance_threshold scale).
3. Walk the episode tracking the current run of consecutive contact steps. A **contact loss event** is a transition `in_contact[t] → ¬in_contact[t+1]` where the run length is `≥ MIN_CONTACT_RUN` (=2, denoises spurious brushes) and `object_goal_distance[t] > OBJECT_FAR_FROM_GOAL` (=0.10, makes sure we don't boost "loss" that's really "task complete").
4. We keep the **latest** such event (the final mistake), not the first.

Phase precedence (highest first): ballistic → contact-loss → argmin.

### Why bidirectional?

Sharony et al. 2026 (arXiv 2602.01915, "VLM-Guided Experience Replay") boost SUCCESS-like transitions. Our pitch boosts FAILURE-causing transitions. The clean test of this differentiation is a *bidirectional* variant that does both — if BiDir beats Failure-only and Success-only, then the two signals are complementary. If Failure-only beats Success-only, our pitch is the active ingredient. The bidirectional variant is the experimental control that lets us claim the contribution.

To stay state-only (no VLM API cost in this verification run), the "success" timestep is operationalised as **argmax over windowed distance reduction**, i.e. the centre of the window of length `W` over which `dist(achieved, desired)` dropped the most. This is the state-geometry proxy for what Sharony's VLM would mark as a successful sub-trajectory. The full Sharony comparison (image-VLM success-only) is a separate follow-up.

---

## 2. Implementation Details

### Files changed

| File | Change |
|------|--------|
| `src/vlm/localizer.py` | Added a contact-loss phase to `GoalDistanceLocalizer.localize_failure` (Oracle v3) and a new `localize_best_progress` method for the success-side signal. Localizer signature now also takes optional `ee_positions` and `object_positions`; if not provided, v3 degrades to v2 behavior. |
| `src/buffers/bidirectional_buffer.py` | **New** — `BidirectionalSemanticBuffer` (sibling to `SemanticPERBuffer`, no in-place modification). Tracks two per-slot multipliers `_failure_weight` and `_success_weight` plus an auxiliary `_td_priority` array so re-blending is exact. |
| `src/buffers/__init__.py` | Added `BidirectionalSemanticBuffer` export and `_make_bidir`, wired into the `make_buffer` factory for replay types `bidir` and `her_bidir`. |
| `train.py` | (a) Recognise `bidir`/`her_bidir` as semantic types. (b) Skip frame capture when no image-based VLM is active. (c) Record `ee_positions` and `object_positions` per step. (d) Pass them into `localize_failure` for Oracle v3. (e) For bidir, call `apply_success_priority` on every episode and `apply_failure_priority` on failed ones. |
| `configs/bidir.yaml` | **New** config inheriting from `base.yaml`, sets `type: bidir`, `failure_boost: 10.0`, `success_boost: 10.0`, `vlm_provider: heuristic`. |
| `modal_app.py` | Added `spawn_one` local entrypoint that uses `train_remote.spawn()` so `modal run --detach` actually survives local disconnect (the existing `main` entrypoint uses `.remote()` which awaits and dies on disconnect). |

### Priority computation (exact)

For each slot `i`:

```
priority[i] = TD_priority[i] * failure_weight[i] * success_weight[i]
```

where
- `TD_priority[i] = (|td_error[i]| + epsilon) ** alpha` (standard PER, alpha=0.6),
- `failure_weight[i]` is `1.0` by default; set to `failure_boost` (=10.0) if `i` is within `±W` of a failure timestep,
- `success_weight[i]` is `1.0` by default; set to `success_boost` (=10.0) if `i` is within `±W` of a success/best-progress timestep,
- a slot in **both** windows gets `100×` total boost relative to TD baseline.

To re-blend after any weight change we keep the raw `_td_priority[i]` in a sibling float64 array, so we never have to invert a stale sum-tree leaf.

### Hook order in `train.py`

End-of-episode:
1. (Always for bidir) `apply_success_priority(success_t, W)` — center on `argmax(dist_reduction over window)`.
2. (Failed episodes only) `apply_failure_priority(fail_t, W)` — center on contact-loss / ballistic / argmin.

On a fully-successful episode, only success is boosted — exactly the spec.

---

## 3. Smoke Test Output

### 3a) Buffer unit smoke (state-only, no env)

```
Buffer size: 10
Initial weights @ slot 5: fail=1.0, succ=1.0
Total tree priority: 10.0000

After failure boost @ t=3, window=2:
  Weights fail: [1, 10, 10, 10, 10, 10, 1, 1, 1, 1]
  Total tree priority: 55.0000  (correct: 5 slots @ 10x + 5 @ 1x)

After success boost @ t=7, window=1:
  Weights succ: [1, 1, 1, 1, 1, 1, 10, 10, 10, 1]
  Total tree priority: 82.0000  (correct: 5*10 + 3*10 + 2*1 = 82)

After TD update on slot 3 (td=0.5):
  Expected priority: 6.597547  (= (0.5+eps)**0.6 * 10 * 1)
  Actual   priority: 6.597547  ✓

After failure boost @ t=7 (overlaps success window):
  slot 7: fail=10.0, succ=10.0
  slot 7 priority in tree: 100.0000  (correct: 1 * 10 * 10)
  Expected (td * 10 * 10): 100.0000  ✓

Sampling distribution over 5000 draws:
  slot 0:   15  (1x,  baseline)
  slot 1-5: ~125 each  (10x, failure only)
  slot 6,8: ~1400 each (100x, BOTH)
  slot 7:    1440      (100x, BOTH) ← center of both windows
  slot 9:    132       (10x, success only)

  Ratio of (both)/(failure-only) ≈ 10x  — exactly the spec.
```

All buffer self-tests passed.

### 3b) Localizer self-tests (synthetic trajectories)

```
Ballistic case (object flies after t=5):
  → '[v3:ballistic] throw at t=2 (peak disp=0.10, post-peak mean=0.09)'  ✓

Push-like contact loss (ee stuck to obj until t=20 then drifts off):
  → '[v3:contact-loss] t=19 (ee→obj=0.028 m at loss, obj→goal=0.125 m)'  ✓

Static / argmin fallback:
  → '[v3:argmin] closest approach at t=10 (dist=0.000)'  ✓

Best progress (rapid approach in first 10 steps then drift):
  → '[v3:progress] best progress at t=2 (dist drop 0.40 over 5 steps)'  ✓
```

### 3c) Localizer behavior on real Fetch episodes (8 random-action rollouts)

```
FetchPush-v4:        ballistic=0, contact-loss=0, argmin=8
FetchSlide-v4:       ballistic=1, contact-loss=0, argmin=7
FetchPickAndPlace-v4: ballistic=0, contact-loss=1, argmin=7
```

Random actions rarely sustain contact long enough to trigger contact-loss (requires ≥2 consecutive in-contact frames + far-from-goal). This is the **correct** behavior during random exploration — the contact-loss phase activates more reliably once the policy learns to approach the block. The single contact-loss firing on PickAndPlace confirms the code path is reachable on real data.

### 3d) End-to-end integration smoke (10k steps, FetchPush + FetchSlide)

Both ran to completion locally with no crash:

```
FetchPush-v4   10,000 steps: critic_loss=0.029→0.047, td_error=0.16→0.23
FetchSlide-v4  10,000 steps: critic_loss=0.013→0.011, td_error=0.10→0.11
```

Eval success at 10k=0 in both (as expected — far below the ~50k step regime where SAC+PER starts learning Push, and ~100k+ for Slide).

### 3e) Hook firing count check (3k steps, FetchPush)

```
apply_success_priority calls: 60   (every episode → matches ~60 episodes in 3k steps)
apply_failure_priority calls: 55   (only failed eps; 5 episodes succeeded or ended short)
```

Both directional hooks fire as designed.

---

## 4. Modal Verification Runs (50k steps, --detach)

Modal CLI workspace: **agile-quadrupeds**. Used a new `spawn_one` local entrypoint (added to `modal_app.py` in commit `f46b926`) so the spawned `FunctionCall` survives local disconnect; the original `train_remote.remote()` blocks and was getting cancelled.

| Env | Modal App ID | FunctionCall ID | URL |
|---|---|---|---|
| FetchPush-v4  | `ap-b4jSy4TkrCALFZTaCMEHrx` | `fc-01KRD37095AMS4FNBJ0CF6245G` | https://modal.com/apps/agile-quadrupeds/main/ap-b4jSy4TkrCALFZTaCMEHrx |
| FetchSlide-v4 | `ap-vhKtSciZVwmfWU93oEAkqi` | `fc-01KRD37MW4R42Q2FY2MPPJA2GD` | https://modal.com/apps/agile-quadrupeds/main/ap-vhKtSciZVwmfWU93oEAkqi |

Both apps in `ephemeral (detached)` state with 1 active task each at report time (20:21 PDT). 50k steps on an A10G should take roughly 8–12 min wall clock based on the local-CPU smoke at 222 steps/sec.

W&B run names: `a2_bidir_push_50k`, `a2_bidir_slide_50k` (project: `semantic-per`).

---

## 5. Open Questions / Next Tests

1. **Does success-only beat failure-only?** That's the head-to-head our project rides on. The bidir config is the joint upper-bound; we still need single-direction comparisons:
   - Add `success_only.yaml` (set `failure_boost: 1.0`, `success_boost: 10.0`).
   - Add `failure_only.yaml` (= current `semantic_per_heuristic.yaml`).
   Then run all 3 × 3 envs × 3 seeds. If `bidir ≈ failure_only > success_only`, the failure-side is the ingredient that matters.

2. **Is the contact-loss phase firing during real training?** The 8 random-action probes only triggered it once. We should log the phase that fires inside `train.py` and look at the distribution after, say, 100k–200k policy training steps when the agent has learned to approach the block. Add a counter to `TrainingLogger` (`vlm/phase_ballistic`, `vlm/phase_contact_loss`, `vlm/phase_argmin`) and a stacked-bar plot per env.

3. **CONTACT_DISTANCE robustness.** Fetched value of `0.05 m` is heuristic. For FetchPickAndPlace the gripper closes around an object whose half-width is ~0.025 m, so contact may persist at slightly larger ee-obj distances when the gripper is *holding* the block (ee_pos = wrist, finger reach adds ~0.05 m). Consider increasing to `0.07` or making it env-dependent.

4. **Success-window semantics.** Using *argmax windowed distance-reduction* is one of several reasonable proxies. Alternatives: (a) windowed reduction relative to baseline trajectory (control for goal-distance baseline), (b) argmin of `||object - desired||` only inside the "contact" subsequence (so we boost good pushes, not lucky initial poses), (c) longest monotonic-progress window.

5. **Interaction with HER.** `her_bidir` is wired into `make_buffer` but I have not smoke-tested it. HER's relabeling treats the hindsight goals as if the trajectory had succeeded — so all hindsight transitions should ideally enter the "successful episode" branch and only get success boosts. Currently `train.py` applies the success/failure split based on the *real* `ep_success`, which means hindsight relabels in failed episodes inherit the failure boost via the underlying slot's weight. That's not necessarily wrong (the *underlying* transition was failure-relevant) but it should be examined empirically before claiming `her_bidir` is sound.

6. **Boost size 10×.** Matches the existing `semantic_per` baseline for fair comparison. Worth ablating in `{3, 10, 30, 100}` once the headline experiment is done. Note `100×` is empirically what overlap slots see in `bidir`, so the *effective* boost there is already 10× larger than the named "10× boost".

7. **PER alpha vs semantic multiplicative boost.** The semantic boost is applied to `priority = td**α * w_fail * w_succ`, not pre-α. This means the *relative* boost is fixed at the configured value (e.g. 10) regardless of `α`. This is the right design (matches the original semantic_per) but worth noting.

---

## 6. Repro Commands

```bash
# Local smoke (no GPU, no frames, no W&B)
source .venv/bin/activate
python train.py --config configs/bidir.yaml \
    env.name=FetchPush-v4 training.total_steps=10000 \
    training.warmup_steps=1000 training.eval_interval=5000 \
    training.eval_episodes=3 training.save_interval=20000 \
    training.log_interval=2000 logging.use_wandb=false \
    logging.use_tensorboard=false logging.run_name=local_smoke

# Modal verification run (50k steps, detached, A10G)
modal run --detach modal_app.py::spawn_one \
    --config configs/bidir.yaml \
    --extra "env.name=FetchPush-v4 training.total_steps=50000 \
             training.warmup_steps=2000 training.eval_interval=10000 \
             training.eval_episodes=5 training.save_interval=50000 \
             logging.run_name=a2_bidir_push_50k"
```
