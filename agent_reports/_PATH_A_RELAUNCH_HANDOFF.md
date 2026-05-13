# Path A Relaunch Handoff — 2026-05-12 03:35 PDT

Author: emergency agent (Opus 4.7). Branch: `agent/pathc-lead`. Commit: `eb899be`.

## Issue 1 — Path A bidirectional relaunch: LIVE

### Root cause confirmed
All 6 watchdog spawns died immediately. From `~/.local/state/path_a_pivot_*.log`:

```
FileNotFoundError: [Errno 2] No such file or directory: 'configs/bidir.yaml'
```

Two compounding problems in `scripts/overnight_watchdog.sh::launch_path_a_pivot`:

1. **Missing config.** `configs/bidir.yaml` only lived on `agent/a2-oracle-bidir`,
   not on `agent/pathc-lead` (the orchestrator's branch). When the watchdog ran
   it had no such file in cwd.
2. **Wrong CLI form.** `train.py` accepts only `--config <path>` plus hydra-style
   `key.subkey=value` overrides (`argparse.parse_known_args()` slurps the rest
   into the overrides list). The watchdog used `--env`/`--seed`/`--total_steps`/
   `--run_name` which would have been silently parsed as override "keys" — and
   even if config had existed, train.py would have crashed on `key_path.split(".")`
   producing single-element keys that can't traverse the cfg dict. So even past
   the FileNotFound, every spawn would have died.

### Fix
- Cherry-picked A2's commit `b5a2fe3` (Oracle v3 + BidirectionalSemanticBuffer)
  onto `agent/pathc-lead`. One conflict in `train.py` resolved to keep both
  pathc-lead's CF-HER frame-capture logic and A2's bidir frame-capture
  short-circuit. Smoke-tested 2k steps on FetchPush — clean.
- New `scripts/relaunch_path_a_pivot.sh` uses correct hydra-style overrides:
  ```
  python train.py --config configs/bidir.yaml \
      env.name=FetchPush-v4 training.seed=42 training.total_steps=300000 \
      training.eval_interval=10000 ... logging.run_name=...
  ```
  Runs sequentially (single GPU). Tagged `path_a_pivot_2026-05-12,bidir_relaunch`
  via `WANDB_TAGS` env var.

### Launch status: LIVE
- Spawned 03:33 PDT as pid 144540 (`nohup ./scripts/relaunch_path_a_pivot.sh`).
- Run 1/6 in flight: `path_a_pivot_bidir_FetchPush-v4_seed42`, W&B id `8qxhqlye`,
  at step=10000 / 300000 by 03:34. Sustained ~250 steps/s.
- Projected wall time: ~20 min/run × 6 = **~2 hours total**. All 6 runs finish
  by ~05:35 PDT. Plenty of data by morning.

Sequence (Push first, fastest):
  FetchPush-v4 s42 → FetchPush-v4 s123 → FetchPickAndPlace-v4 s42 →
  FetchPickAndPlace-v4 s123 → FetchSlide-v4 s42 → FetchSlide-v4 s123

Per-run logs at `~/.local/state/path_a_relaunch_<env>_seed<seed>.log`.
Driver log at `~/.local/state/path_a_relaunch.log`.

W&B filter for morning review:
  https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=bidir_relaunch

## Issue 2 — Modal busy_count=11: NOT zombies. DID NOT STOP.

`modal app list`:

| App ID | Tasks | Created | Notes |
|---|---|---|---|
| `ap-RlxdhxgDoMSFobTyggIZG8` | 8 (was 9) | 2026-05-11 20:23 PDT | A1's HER sweep. Active training, recent step lines (985k/740k/505k/etc.) — NOT zombies. Tasks completing one by one (9 → 8 during this investigation). |
| `ap-PWMTBsinFWdaAK048ySfBV` | 1 | 2026-05-11 22:20 PDT | A2's bidir Modal verification (`a2_bidir_push_50k` / `a2_bidir_slide_50k`), step=26000+ with live OpenAI calls. Active. |

Both apps showing recent activity within the last minute. **No zombies; no action
taken.** The orchestrator's busy_count=11 was therefore legitimate, and Phase 2
remains correctly gated by the watchdog's `check_modal_free()` until A1's sweep
finishes. ETA for A1 freeing Modal: hard to predict — top step was 987k at
03:31, runs are aimed at 1M-step ceiling, so the last container should finish
within ~30 minutes if nothing's pinned. The watchdog polls every 5 min and
will auto-launch Phase 2 when it sees a1_running==0.

## Issue 3 — Watchdog Oracle-CF delta calc: BUG (W&B name filter mismatch). Documented, not patched.

Hypothesis: the pivot script's run-name filter is wrong.

Watchdog code (`scripts/overnight_watchdog.sh` lines 78-79):
```python
her_runs = [r for r in runs if 'path_c_kill_her_' in (r.name or '') and 'oracle' not in (r.name or '')]
oracle_runs = [r for r in runs if 'path_c_kill_her_oracle' in (r.name or '') or 'oracle_cf' in (r.name or '')]
```

Actual run names on W&B (from API spot-check with `path_c_overnight_2026-05-11`):
- HER runs are named `path_c_kill_her_<env>_s<seed>_seed<seed>`
  (e.g. `path_c_kill_her_pp_s42_seed42`)
- Oracle-CF runs are named `path_c_kill_ocf_<env>_s<seed>_seed<seed>`
  (e.g. `path_c_kill_ocf_pp_s42_seed42`)

Neither `'path_c_kill_her_oracle'` nor `'oracle_cf'` (as a substring) appears in
any run name. So `oracle_runs == []`, `oracle_mean = 0 / max(0,1) = 0.000`,
`delta = 0 - her_mean ≈ -0.275`, which is < 0.10 → pivot triggered.

In reality the OCF data is non-zero. From the 9 `path_c_kill_ocf_*` runs:
- PnP: 0.100 / 0.050 / 0.200 → mean 0.117
- Push: 0.100 / 0.350 / 0.200 → mean 0.217
- Slide: 0.200 / 0.200 / 0.150 / (+ duplicate set 0.150, 0.050, 0.050) → ~0.133

Across all 9 unique OCF runs the mean is ~0.156. HER mean was ~0.275 (`path_c_kill_her_*`:
PnP 0.400/0.050/0.050; Push 0.450/0.600/0.600; Slide 0.200/0.050/0.050 = mean ~0.272).
Real delta: OCF − HER ≈ **−0.116**, still below the +0.10 kill criterion → **the
pivot decision was correct anyway**, just for the wrong stated reason.

Fix (not applied, low priority per directive): change the OCF filter to
`'path_c_kill_ocf' in (r.name or '')`. Optionally also widen HER to use a
shared tag-based partition rather than name-substring.

## Files touched

- `configs/bidir.yaml` *(new, from cherry-pick)*
- `src/buffers/__init__.py` *(bidir factory wiring, from cherry-pick)*
- `src/buffers/bidirectional_buffer.py` *(new, from cherry-pick)*
- `src/vlm/localizer.py` *(Oracle v3 + `localize_best_progress`, from cherry-pick)*
- `train.py` *(merged: pathc-lead CF-HER capture-frames + A2 bidir capture-frames)*
- `scripts/relaunch_path_a_pivot.sh` *(new)*

Committed as `eb899be` on `agent/pathc-lead`. Not pushed.

## What to check in the morning

1. `tail -f ~/.local/state/path_a_relaunch.log` — driver log; should show 6 ✓ lines.
2. W&B `bidir_relaunch` tag for eval/success curves at 300k.
3. `modal app list` — Phase 2 should auto-launch once A1's sweep finishes.
