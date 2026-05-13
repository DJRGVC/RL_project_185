# A1 HER Baselines Report

Branch: `agent/a1-her-baselines` (worktree at `/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/.claude/worktrees/agent-ab64adbfe10d16d22`). Commit: `4d6bbf9`.

## Modal App ID
`ap-RlxdhxgDoMSFobTyggIZG8` (detached) — Modal dashboard: https://modal.com/apps/agile-quadrupeds/main/ap-RlxdhxgDoMSFobTyggIZG8

27 jobs spawned (3 methods x 3 envs x 3 seeds). Modal is rolling them out as GPUs free up; ~10 running concurrently at launch.

## W&B Filter URL
Project: https://wandb.ai/d-grant-uc-berkeley/RL_project
Filter by tag: https://wandb.ai/d-grant-uc-berkeley/RL_project?tag=her_baselines

All HER baseline runs have tags `her_baselines`, `<method>`, `<env_slug>`, and a method-prefix tag (e.g. `her_baselines_her`) for grouping. As of writing: 10/27 already syncing live, finished local smoke `her_baselines_smoke_local_seed42` also synced as proof of credential path.

Run names follow the requested prefix: `her_baselines_<method>_<env>_seed<N>`. Examples confirmed live in W&B:
- `her_baselines_her_fetch_pickandplace_seed42`
- `her_baselines_her_per_fetch_pickandplace_seed999`
- `her_baselines_her_semantic_per_fetch_pickandplace_seed123`
- `her_baselines_her_fetch_push_seed42`

## Changes Made

### 1. `modal_app.py` (run_ablation rewrite)
- `METHODS` now contains all three HER variants:
  - `("configs/her.yaml", "her", [])`
  - `("configs/her_per.yaml", "her_per", [])`
  - `("configs/her_semantic_per.yaml", "her_semantic_per", ["replay.vlm_provider=heuristic"])`
- `ENVS = ["FetchPickAndPlace-v4", "FetchPush-v4", "FetchSlide-v4"]` and `SEEDS = [42, 123, 999]` preserved.
- Run name prefix: `her_baselines_<method>_<env_slug>_seed<N>`.
- `train_remote` now accepts a `wandb_tags` arg that is exported as `WANDB_TAGS` inside the container; the launcher passes `"her_baselines,<method>,<env_slug>"` per job.
- `train_remote` overrides `WANDB_PROJECT=RL_project` and `WANDB_ENTITY=d-grant-uc-berkeley`. **The Modal secret had `WANDB_ENTITY=djrgvc`, but the secret's `WANDB_API_KEY` belongs to the `d-grant` user who does not own `djrgvc/RL_project` — every prior W&B init was failing silently with "permission denied".** Overriding to the team entity (`d-grant-uc-berkeley`) where the user owns `RL_project` makes the runs actually log.

### 2. `src/utils/logger.py`
- Reads `WANDB_TAGS` (comma-separated) from env and adds them to `wandb.init`. Method-prefix is appended as an extra tag for grouping.
- Added a try/retry: if `wandb.init` fails with the configured `wandb_entity`, retry with `entity=None` (default user entity). Belt-and-suspenders for credential mismatches.

### 3. `src/envs/wrappers.py` + `train.py`
- `make_env` only requests `render_mode` when `capture_frames=True`. Without OSMesa/EGL installed (e.g. Daniel's local Linux box) MuJoCo's offscreen context cannot initialize even when frames are not used; the previous code unconditionally requested rgb_array and crashed `env.reset()`.
- `train.py` now sets `needs_frames = is_semantic and vlm_provider != "heuristic"`, so HER+SemanticPER (heuristic) no longer needs MuJoCo rendering. This matters for both local smoke tests AND Modal (the heuristic localizer is purely numeric).

## Files Modified
| File | Purpose |
|------|---------|
| `modal_app.py` | New HER baselines sweep; W&B entity override; tag passthrough |
| `src/envs/wrappers.py` (lines 104-115) | Only set render_mode when frames are needed |
| `train.py` (lines 136-142) | Disable frame capture for heuristic localizer |
| `src/utils/logger.py` (lines 38-86) | W&B tags from env + entity-fallback |

## Smoke Test Results

All run locally with `FetchReach-v4` (faster than the Fetch envs we are sweeping), 2k steps, warmup 500, eval 2 episodes, `WANDB_MODE=disabled`. After fix to `make_env`, all three configs train end-to-end:

| Config | Steps | Final critic loss | Final actor loss | Notes |
|--------|-------|-------------------|------------------|-------|
| `configs/her.yaml` | 2000 | 0.3764 | 1.67 | UniformReplayBuffer + HER wrap |
| `configs/her_per.yaml` | 2000 | 0.2461 | 1.43 | PERBuffer + HER wrap |
| `configs/her_semantic_per.yaml` (heuristic) | 2000 | 0.2162 | 1.55 | SemanticPERBuffer + HER + GoalDistanceLocalizer |

Additionally smoked `her.yaml` on the real env (`FetchPickAndPlace-v4`, 10k steps) and `her_semantic_per.yaml` (heuristic) on `FetchPickAndPlace-v4` (5k steps) — both completed without errors and produced sensible loss curves.

Unit test of the HER buffer (`src/buffers/her_buffer.py`) wrapping all three underlying buffers passed: `push`, `finish_episode`, `sample`, `update_priorities`, `apply_semantic_priority`, and `get_episode_start` all behave correctly. Synthetic transitions are added (5 real + ~14 synthetic with k=4 future strategy on a 5-step episode).

## Known Issues

1. **GPU concurrency limit**: 10 of 27 jobs running at launch. Modal queues the rest; they will start as GPUs free. Total wall-time at 1M steps each is the binding constraint (each run is ~3-5h on A10G per existing semantic_per_heuristic_v2 cadence).
2. **HER + SemanticPER ep_start_idx**: `train.py` captures `ep_start_idx = replay._ptr` BEFORE pushes, so `apply_semantic_priority` boosts the real transitions only — the k=4 synthetic HER transitions inserted after `finish_episode` are not boosted. This is intentional (semantic boost is grounded in the actual trajectory) but worth noting in the paper.
3. **Modal secret hygiene**: WANDB_ENTITY=djrgvc in the secret is misleading. After the sweep wraps up the secret should be corrected to `WANDB_ENTITY=d-grant-uc-berkeley` so the override in `train_remote` is no longer needed. I did not touch the secret — only the runtime code.
4. **Stopped apps**: I created several Modal apps while debugging (`ap-AIFy8pRcAIpmnc7uackUD1`, `ap-xNG178sG6fpj1Qmtg32gKn`, `ap-TR49OVsYIs250MRkKOtqKj`, `ap-bQzpTDIXxryhRcCqxuk7Kh`, `ap-GuK6wF28mYLESaW0SvENVa`, `ap-R8N6J7J9zayehUFIQNuqCZ`, `ap-RE1EMvXvhFhuqO3GV1ODKr`, `ap-b4jSy4TkrCALFZTaCMEHrx`, `ap-vhKtSciZVwmfWU93oEAkqi`, `ap-ZF3dXQUcZEgXWiPiQknbj5` debug). All have been stopped — only `ap-RlxdhxgDoMSFobTyggIZG8` is live.
5. **One left-over W&B smoke run**: `her_baselines_smoke_local_seed42` (state: finished) sits in the W&B project. Harmless but can be deleted from the dashboard.

## Next Steps

- Monitor W&B (https://wandb.ai/d-grant-uc-berkeley/RL_project?tag=her_baselines) for the 27 runs. Expected completion in a single overnight window once Modal cycles all the GPUs through.
- After completion, generate per-env success-rate vs. step plots grouped by method tag (`her`, `her_per`, `her_semantic_per`) and compare to the existing `semantic_per_heuristic_v2` baselines.
- If HER+Semantic PER beats HER+PER and HER alone, the paper can claim Semantic PER stacks on the standard HER stack — that is the headline experiment.
- Fix Modal secret WANDB_ENTITY to d-grant-uc-berkeley so the runtime override in `modal_app.py:train_remote` can be removed.
- Decide whether to also re-launch the non-HER baselines (uniform, per, semantic_per_heuristic) under the same tag scheme so the entire ablation lives under one filter. Existing semantic_per_heuristic_v2 runs are in a separate project; rerunning them is cheap (heuristic localizer) and gives clean comparison.
