# PATHC-LEAD handoff (overnight 2026-05-11 → 2026-05-12)

Agent: PATHC-LEAD. Branch: `agent/pathc-lead` (in worktree). Time: 22:18 PDT.

## What got built

1. **C1's `counterfactual.py`** is now on `agent/pathc-lead`:
   `src/vlm/counterfactual.py`. Exposes `CounterfactualLocalizer`,
   `CounterfactualResult`, `make_counterfactual_fn`, `judge_counterfactual`.
   Loaded into `src/vlm/__init__.py`.

2. **`src/buffers/counterfactual_buffer.py` extended** beyond C2's stub:
   - Added `cf_input_kind: 'vlm'|'state'` so the buffer can be driven by
     hand-coded oracles (state input) in addition to the VLM CF interface.
   - Added `cf_window` and confidence-weighted "nearest upcoming CF" draw.
   - Pre-decrement `episodes_failed` counter so `cf_call_interval=1` fires
     on the first failed episode (was off-by-one).
   - Added `verifications_attempted`, `verifications_passed`,
     `low_conf_dropped` to the stats dict.

3. **`src/vlm/oracle_cf.py`** — hand-coded per-task CFs:
   - `oracle_cf_push`: midpoint of (ee, desired_goal) at max-ee-block-distance
     frame. Confidence 1.0.
   - `oracle_cf_pick_and_place`: mid-air waypoint at
     (desired_x, desired_y, desired_z + 0.08) at first-drop frame. The
     Sonnet-4.5 / C1v2-B insight, made deterministic.
   - `oracle_cf_slide`: ballistic-trajectory terminus at peak-velocity frame.
     Uses simple friction model (mu=0.1, g=9.81) to predict where the puck
     will stop.
   - `oracle_cf_reach`: trivial Reach oracle (smoke-only).
   - All output `(frame_index, xyz, confidence=1.0)` tuples and clip to the
     Fetch workspace bounds.
   - `make_oracle_cf_fn(env_name)` returns a state-CF callback.

4. **Configs**:
   - `configs/oracle_cf.yaml` — `replay.type=cf_her`, `cf_provider=oracle`,
     `cf_input_kind=state`, `p_counterfactual=0.25`, `her_k=4`.
   - `configs/vlm_cf.yaml` — same buffer with `cf_provider=vlm`,
     `vlm_model=gpt-4o-mini` (cost control), `vlm_variant=achieved_goal`
     (C1v2-A bake-off winner), `cf_call_interval=8`.
   - `configs/verified_cf.yaml` — `cf_provider=verified` with the N1
     simulator-gating verifier (currently passes position-only CFs
     through without verification rollout, since N1's rollout works for
     action-based CFs only; positional CFs are trusted directly).

5. **train.py wiring**: `replay.type == 'cf_her'` is now a first-class
   path. `_build_cf_provider()` builds the callable (oracle/vlm/verified),
   `train()` wraps the underlying buffer with `CounterfactualHERBuffer`,
   handles capture-frames for the VLM path, and pushes CF buffer stats
   (`buffer/cf_relabel_count`, `buffer/cf_vlm_calls`, etc.) to W&B every
   episode.

6. **Bug fix**: `src/vlm/localizer.py` prompt template's JSON example had
   unescaped `{...}` which raised `KeyError("\"failure_frame_index\"")` on
   `.format()`. Now escaped as `{{...}}`. This was blocking VLM-CF runs
   from working.

7. **Modal**: added `spawn()` and `run_path_c_phase2()` entrypoints to
   `modal_app.py` so Phase 2 jobs can be fire-and-forget without blocking
   the orchestrator.

8. **W&B tags**: `src/utils/logger.py` now honors `WANDB_TAGS` env var
   (CSV); orchestrator sets it per-run so every Path C run carries
   `path_c_overnight_2026-05-11` plus method/env tags.

## What's running RIGHT NOW

Orchestrator process `path_c_orchestrator.py` (PID via
`pgrep -f path_c_orchestrator`) launched the **Phase 1 kill experiment**
on the local RTX 5070 Ti at 22:16:30 PDT. State:

- 18 Phase 1 runs (HER + Oracle-CF × 3 envs × 3 seeds × 250k steps).
- 3 concurrent at a time; first batch (HER + PnP × {42, 123, 999}) is
  training (verified W&B-live as of 22:18 PDT).
- Expected wallclock per run: ~14 min. Total Phase 1: ~85 min.
  Expected Phase 1 completion: ~23:45 PDT.

Phase 2 (VLM-CF + Verified-CF on Modal) is **NOT** running. Modal is full
of A1's HER sweep. The orchestrator was launched with `--skip-phase2` so
it won't try to claim Modal. To start Phase 2 once Modal frees:

```bash
cd ~/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185
source .venv/bin/activate
set -a; source .env; set +a
nohup python scripts/path_c_orchestrator.py --phase2-only \
    > /tmp/orch_phase2.log 2>&1 &
```

…or one-shot via Modal:

```bash
modal run --detach modal_app.py::run_path_c_phase2
```

## How to read the morning results

**Single-pane W&B view**:
<https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_overnight_2026-05-11>

Group by method (W&B does this automatically — group is the
`path_c_kill_her` / `path_c_kill_ocf` prefix). The success-rate panel
should show:

- 3 HER seeds plotted as one line/band per env.
- 3 Oracle-CF seeds plotted as a second line/band per env.

**Decision rule for the KILL test**:

| Outcome on `FetchPickAndPlace-v4` eval/success_rate | Verdict |
|---|---|
| Oracle-CF − HER ≥ +0.10  | **Path C is alive.** Continue with VLM-CF (Phase 2). |
| Oracle-CF − HER in (0, +0.10) | Weak signal. Treat as ablation, not headline. |
| Oracle-CF − HER ≤ 0 | **Path C is dead.** Pivot the paper to Path A (Sharony differentiation). |

Why PnP is the deciding env: it has the largest goal-space and the most
nontrivial intermediate-waypoint structure (mid-air pickup), so it's the
task where CF should provide the largest signal. Push is easy (HER already
solves it). Slide depends on action precision more than goal proposals.

**Buffer health metrics** to glance at in W&B (proves CF actually
fired):
- `buffer/cf_relabel_count` — should be growing throughout training.
- `buffer/cf_vlm_calls` — for vlm_cf runs, should grow ~ (episodes / 8).
- `buffer/cf_vlm_returned_none` — should stay much smaller than `cf_vlm_calls`.

## Known risks / things to check first thing

1. **GPU contention.** 3 concurrent jobs running. If any DIES (OOM,
   driver hiccup), the orchestrator marks it `failed`; restarting the
   orchestrator resumes it (idempotency keyed on `run_id`).
2. **W&B 503s.** Saw one transient 503 at startup; wandb auto-retried.
   Runs continue offline if W&B is dead and re-sync when it recovers.
3. **Oracle-CF "teleports to goal".** The PnP oracle outputs
   `(g_x, g_y, g_z + 0.08)` — that's 8 cm above the goal. It's NOT a
   teleport-to-goal collapse (the 8 cm offset keeps the CF physically
   meaningful), but it's worth checking the CF buffer's
   `buffer/cf_relabel_count` ratio: if Oracle-CF *only* works because
   it's planting the goal directly into the replay, the comparison
   against HER+VLM-CF is interesting (oracle is the ceiling).
4. **Phase 2 didn't actually launch.** If 07:00 arrives and Modal was
   still busy with A1's sweep, no VLM-CF runs will exist. That's OK —
   the kill experiment alone is the headline. Launch Phase 2 manually
   first thing in the morning.

## Files modified / created

- New:
  - `src/vlm/counterfactual.py` (from C1's worktree)
  - `src/vlm/oracle_cf.py`
  - `configs/oracle_cf.yaml`, `configs/vlm_cf.yaml`, `configs/verified_cf.yaml`
  - `scripts/path_c_orchestrator.py`
  - `agent_reports/overnight_path_c_plan.json`
  - `agent_reports/overnight_path_c_README.md`
  - `agent_reports/PATHC-LEAD_handoff.md` (this file)
- Modified:
  - `src/buffers/counterfactual_buffer.py` (cf_input_kind, oracle path, stats)
  - `src/buffers/__init__.py` (`cf_her` → UniformReplayBuffer)
  - `src/vlm/__init__.py` (export new types)
  - `src/vlm/localizer.py` (escape `{...}` in JSON prompt)
  - `src/utils/logger.py` (WANDB_TAGS env var)
  - `train.py` (cf_her wiring, CF stats logging)
  - `modal_app.py` (spawn + run_path_c_phase2 entrypoints)

Two commits on `agent/pathc-lead`:

- `5a859f5`: Path C: counterfactual HER (oracle/VLM/verified) integration.
- `b393fe3`: Path C orchestrator + plan + Modal Phase 2 spawn.

## If everything is on fire in the morning

```bash
# Kill the orchestrator, leave running children alone.
pkill -TERM -f path_c_orchestrator

# Or kill EVERYTHING.
pkill -TERM -f "python train.py --config configs/her.yaml"
pkill -TERM -f "python train.py --config configs/oracle_cf.yaml"
```

The state file persists, so `python scripts/path_c_orchestrator.py`
will resume — completed runs are skipped, failed runs retry once.
