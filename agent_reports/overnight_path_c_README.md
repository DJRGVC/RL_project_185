# Path C overnight operator guide

**Generated:** 2026-05-11 22:16 PDT by `PATHC-LEAD`.
**Morning deadline:** 07:00 PDT 2026-05-12.

## TL;DR

- Orchestrator running on this PC.  PID: `pgrep -f path_c_orchestrator`.
- Live status: `agent_reports/overnight_status.md` (refreshed every poll).
- Event log: `~/.local/state/path_c_orchestrator.log` (JSON lines).
- Per-run train logs: `logs/path_c_orch_<run_id>.log`.
- W&B dashboard: <https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_overnight_2026-05-11>

## What's running

**Phase 1** (KILL experiment) on local RTX 5070 Ti, concurrency = 3:

- 9 HER baseline runs: 3 envs × 3 seeds × 250k steps.
- 9 HER+Oracle-CF runs: same matrix.
- Each run ≈ 9 min; total Phase 1 ≈ 55 min.
- Tagged `path_c_kill_*`. Method group prefix = `path_c_kill_her` or `path_c_kill_ocf`.

**Phase 2** (VLM-CF runs) is currently **paused** waiting for Modal capacity
(A1's HER sweep is using all 10 GPUs). The orchestrator can launch Phase 2
once `modal app list` shows free GPUs. Currently launched with
`--skip-phase2`; to launch Phase 2 after Modal frees up, run:

```bash
cd ~/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185
source .venv/bin/activate
nohup python scripts/path_c_orchestrator.py --phase2-only \
    > /tmp/orch_phase2.log 2>&1 &
```

Or one-shot from inside Modal:

```bash
modal run --detach modal_app.py::run_path_c_phase2
```

## Where the data lives

- **W&B runs**: `d-grant-uc-berkeley/RL_project`, tagged
  `path_c_overnight_2026-05-11`. Filter further with `path_c_kill` or
  `path_c_vlm`.
- **Local TensorBoard**: `logs/<run_name>/` — viewable with
  `tensorboard --logdir logs/`.
- **Checkpoints**: `checkpoints/<run_name>/best/` and `final/`.
- **Orchestrator state**: `agent_reports/overnight_state.json` (resumes
  on restart — skips already-done runs).

## Kill switches

- **Stop the orchestrator** (does not kill running children):
  ```bash
  pkill -TERM -f path_c_orchestrator
  ```
- **Kill all Phase 1 children**:
  ```bash
  pkill -TERM -f "python train.py --config configs/her.yaml"
  pkill -TERM -f "python train.py --config configs/oracle_cf.yaml"
  ```
- **Stop a Modal app**:
  ```bash
  modal app list
  modal app stop ap-<id>
  ```

## How to interpret morning results

1. Open the W&B dashboard, filter tag `path_c_overnight_2026-05-11`.
2. Group by `method` (panel preset already exists) — compare
   `path_c_kill_her` vs `path_c_kill_ocf` on `eval/success_rate`.
3. **Decision rule (KILL)**: if `HER+Oracle-CF` does *not* beat `HER` by
   at least **+0.10 success rate** on `FetchPickAndPlace-v4` (across 3 seeds),
   Path C is dead and the paper should focus on Path A.
4. **Verdict (COMMIT)**: if Oracle-CF wins by ≥ 0.10 on PnP and shows any
   gain on Push/Slide, the path is real and the VLM-CF runs (Phase 2)
   should be the headline experiment.

## Restart from cold

If the PC reboots overnight or the orchestrator dies:

```bash
cd ~/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185
source .venv/bin/activate
set -a; source .env; set +a
# Resume Phase 1 (orchestrator skips runs marked 'done' in state).
nohup python scripts/path_c_orchestrator.py > /tmp/orch.log 2>&1 &
```

## Sanity checks (run these to verify health)

```bash
# Orchestrator is alive
pgrep -f path_c_orchestrator >/dev/null && echo OK || echo DEAD

# GPU is busy
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv

# Most-recent train.log progress
tail -5 logs/path_c_orch_$(ls -t logs/ | head -1)
```

## Known risks

- **W&B 503**: transient, retries inside `wandb.init`. If a run loses
  network, it will keep training and reconnect when network recovers.
- **OOM (rare)**: 3 concurrent SAC trainers used ~1.6 GB VRAM in smoke;
  16 GB headroom. If you see OOMs, drop concurrency to 2 in the plan
  (`_concurrency_local` in `overnight_path_c_plan.json`) and restart.
- **OpenAI 429**: only affects Phase 2 (VLM CF). Orchestrator catches
  exceptions in train.py's CF callback — the run falls back to vanilla
  HER for that episode and continues.
- **Modal full**: the Phase 2 launcher waits for ≤ 4 active workspace
  containers. If A1's sweep is still saturating Modal at morning, kick
  off `modal run --detach modal_app.py::run_path_c_phase2` manually.
