# Push OCF Corrected Rerun — LAUNCHED

**Timestamp:** 2026-05-12T09:30:10Z  
**Launcher PID (nohup shell):** 131586  
**First training PID (seed 42):** 131590  
**Expected completion:** ~2026-05-12T11:00Z (~90 min wallclock, sequential 3 seeds × ~30 min each)

## Pre-launch checks (all PASSED)

| Check | Result |
|---|---|
| GPU memory used | 577 MiB (threshold: <2000 MiB) |
| Competing train.py processes | None |
| Script path | `scripts/run_corrected_push_ocf.sh` (exists, executable) |
| oracle_cf.py git commit | `ccb63d4` (most recent on file) |
| Bug fix line (`obj[k]`) | Present at line 107: `cf_xyz = 0.5 * (obj[k] + g)` |
| ANTHROPIC_KEY | ~/.anthropic_key readable |
| OPENAI_KEY | ~/.openai_key readable |
| .venv/bin/activate | Present |

## Launch command

```
source .venv/bin/activate
nohup bash scripts/run_corrected_push_ocf.sh > ~/.local/state/path_c_push_rerun.log 2>&1 &
```

Log file: `~/.local/state/path_c_push_rerun.log`

## W&B confirmation (60s after launch)

- Run `path_c_kill_ocf_push_fix_s42_seed42` **state: running**
- Tags: `oracle_cf_pushfix`, `path_c_kill_2026-05-11`, `path_c_kill_ocf_push_fix_s42`
- Entity/project: `d-grant-uc-berkeley/RL_project`
- Created: 2026-05-12T09:29:53Z

## Expected W&B runs

| Run name | Seed | Status |
|---|---|---|
| path_c_kill_ocf_push_fix_s42 | 42 | RUNNING |
| path_c_kill_ocf_push_fix_s123 | 123 | QUEUED (sequential) |
| path_c_kill_ocf_push_fix_s999 | 999 | QUEUED (sequential) |

## Fix summary

The corrected script uses `midpoint(block_pos[k], goal)` instead of `midpoint(ee[k], goal)` for the Push counterfactual, anchoring CFs to a physically meaningful workspace position. This addresses the root cause of OCF underperforming HER (0.283 vs 0.617 success) in the 2026-05-11 Path C KILL run.

## Morning agent action

Filter W&B: `tags=path_c_kill_2026-05-11 AND tags=oracle_cf_pushfix` to compare corrected OCF-Push numbers against HER baseline (0.617). The KILL verdict should be re-evaluated with these corrected results.
