# Matched-horizon HER@500k + PER@500k baseline launcher — PREPPED

**Date:** 2026-05-12 (PDT, evening)
**Branch:** `agent/pathc-lead`
**Status:** Auto-launcher armed. Will fire when local GPU frees.

## Why this exists

The headline table currently compares `vlm_cf @ 500k steps` against
`HER @ 250k steps` — half the training budget. A skeptical reader will
(rightly) flag this as an unfair horizon mismatch. These runs supply the
**canonical matched-horizon comparators**: HER@500k and PER@500k on the
same three Fetch envs and same three seeds we use for vlm_cf / verified_cf.

When complete, the paper can claim, e.g.:

> Matched-horizon comparison at 500k env-steps:
>   FetchPush  — vlm_cf 0.95 vs HER 0.X vs PER 0.X
>   FetchPnP   — vlm_cf 0.YY vs HER 0.X vs PER 0.X
>   FetchSlide — vlm_cf 0.ZZ vs HER 0.X vs PER 0.X

## Run inventory — 18 total

| Method | Config             | Envs (3)                                            | Seeds (3)     | Steps  | W&B tag             |
|--------|--------------------|-----------------------------------------------------|---------------|--------|---------------------|
| HER    | `configs/her.yaml` | FetchPush-v4, FetchPickAndPlace-v4, FetchSlide-v4   | 42, 123, 999  | 500_000 | `path_c_her_500k`   |
| PER    | `configs/per.yaml` | FetchPush-v4, FetchPickAndPlace-v4, FetchSlide-v4   | 42, 123, 999  | 500_000 | `path_c_per_500k`   |

Per-run name format: `path_c_<method>_500k_<env_slug>_s<SEED>_seed<SEED>`
(e.g. `path_c_her_500k_push_s42_seed42`).

All runs also tagged `path_c_matched_horizon_500k` for one-shot W&B filtering.

`configs/per.yaml` was verified to exist with `replay.type: per` and standard
PER hyperparameters (`per_alpha=0.6, per_beta_start=0.4 → 1.0` over 500k
anneal steps, `per_epsilon=1e-6`) and parses cleanly under PyYAML.

## Scheduling — wave-by-wave, 9 in parallel

* **Wave 1 — HER@500k** (9 runs in parallel): ~3 h wall.
* **Wave 2 — PER@500k** (9 runs in parallel, after Wave 1 drains): ~3 h wall.

Total wall ≈ **6 hours** end-to-end once the current HER@1M wave frees the GPU.

## VRAM budget

* GPU: NVIDIA RTX 5070 Ti, 16303 MiB total.
* Current footprint (HER@1M × 7 + oracle_cf@250k × 3 + display): ~3.7 GB used,
  ~12.1 GB free.
* Per-run footprint (matches in-flight HER@1M procs): ~310 MiB.
* Worst case (9 parallel) ≈ 2.8 GB — fits with massive headroom on the *next*
  wave, since the HER@1M wave will have fully drained before we launch.

## Cost

* GPU compute: **$0** (all local RTX 5070 Ti).
* API calls: **$0** (no VLM, no Modal).

## Auto-launch wiring

Two scripts, both in `scripts/`:

* **`scripts/run_matched_horizon_500k.sh`** — fires the two waves
  sequentially (HER, then PER). Per-run logs at
  `~/.local/state/matched_500k_<env>_<method>_s<seed>.log`. Touches
  `agent_reports/_MATCHED_500K_DONE.flag` on completion.

* **`scripts/wait_for_her1m_finish_then_launch_500k.sh`** — polls every
  5 minutes for `pgrep -f 'python.*train.*total_steps=1000000'` returning
  empty. On drain, with a 30 s grace re-check to suppress flapping:
  - touches `agent_reports/_HER1M_DONE.flag`,
  - `nohup` launches `run_matched_horizon_500k.sh`
    (log: `~/.local/state/matched_500k_run.log`),
  - touches `agent_reports/_MATCHED_500K_LAUNCHED.flag`,
  - writes the run-script PID to
    `agent_reports/_MATCHED_500K_LAUNCHED.pid`.

  Idempotent — refuses to fire twice if the `LAUNCHED.flag` exists.

### Currently running watcher

| PID    | Started (PDT)            | Script                                                     |
|--------|--------------------------|------------------------------------------------------------|
| 312176 | 2026-05-12 22:24:19      | `bash scripts/wait_for_her1m_finish_then_launch_500k.sh`   |

* Launcher log:  `~/.local/state/matched_500k_launcher.log`
* Launcher PID:  `~/.local/state/matched_500k_launcher.pid` → 312176
* Run log:       `~/.local/state/matched_500k_run.log` (created when wave fires)

## Conflict check with Wave B watcher

* **Wave B watcher** (PID 258223, `scripts/launch_waveB_when_psweep_done.sh`)
  fires HER/PER/Sharony/2x2 **on Modal** after the p-sweep drains.
* **This watcher** (PID 312176, `scripts/wait_for_her1m_finish_then_launch_500k.sh`)
  fires HER@500k/PER@500k **on the local GPU** after the HER@1M wave drains.
* Different infrastructure, different drain triggers, different lock files
  and flags. **No conflict.**

## Operator one-liners

```bash
# Watcher health
ps -p $(cat ~/.local/state/matched_500k_launcher.pid) -o pid,etime,cmd

# Watcher log (live)
tail -f ~/.local/state/matched_500k_launcher.log

# After HER@1M drains and run wave fires
ls -la agent_reports/_HER1M_DONE.flag agent_reports/_MATCHED_500K_LAUNCHED.flag
tail -f ~/.local/state/matched_500k_run.log
ls ~/.local/state/matched_500k_*_s*.log

# Pre-fire cancel (if needed)
kill $(cat ~/.local/state/matched_500k_launcher.pid)
```

## Status flags (created automatically)

* `agent_reports/_HER1M_DONE.flag`              — HER@1M drain detected.
* `agent_reports/_MATCHED_500K_LAUNCHED.flag`   — run wave fired.
* `agent_reports/_MATCHED_500K_LAUNCHED.pid`    — run-script PID.
* `agent_reports/_MATCHED_500K_DONE.flag`       — all 18 runs complete.
