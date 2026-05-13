# Oracle-CF 1M PnP Launch Report

**Launch timestamp:** 2026-05-12T17:24:54Z  
**Launched by:** LAUNCHER agent (Sonnet 4.6)  
**Script:** `scripts/run_oracle_cf_1m_pnp.sh`

---

## Process IDs

| Role | PID | Seed | W&B Run ID | W&B Run Name |
|------|-----|------|------------|--------------|
| Launcher (nohup shell) | 199579 | — | — | — |
| Batch 1: seed 42 | 199586 | 42 | `844hn0lf` | `path_c_kill_ocf_pnp_1m_s42_seed42` |
| Batch 1: seed 123 | 199587 | 123 | `v1dc09bz` | `path_c_kill_ocf_pnp_1m_s123_seed123` |
| Batch 2: seed 999 | sequential after batch 1 | 999 | TBD | `path_c_kill_ocf_pnp_1m_s999_seed999` |

---

## Preconditions verified

- **GPU free:** 624 MiB used / ~15.2 GB free at launch time (PASS)
- **Bug fix at HEAD:** `ccb63d4` — "Path C: fix oracle_cf_push midpoint bug + Modal WANDB_ENTITY override" (PASS)
- **Config:** `configs/oracle_cf.yaml` — no in-flight conflicts, used as-is
- **Step override:** `training.total_steps=1000000` passed via hydra CLI (not written to config)

---

## Expected completion

| Batch | Seeds | Wall-clock | Est. finish |
|-------|-------|------------|-------------|
| Batch 1 (parallel) | 42, 123 | ~2 hr | 2026-05-12 ~19:25 UTC |
| Batch 2 (sequential) | 999 | ~2 hr | 2026-05-12 ~21:25 UTC |

Total: ~4 hr from launch (~21:25 UTC / 14:25 PDT).

---

## W&B filter URL

```
https://wandb.ai/d-grant-uc-berkeley/RL_project/runs?filters={"tags":{"$in":["oracle_cf_1m_pnp"]}}
```

Direct run links:
- Seed 42:  https://wandb.ai/d-grant-uc-berkeley/RL_project/runs/844hn0lf
- Seed 123: https://wandb.ai/d-grant-uc-berkeley/RL_project/runs/v1dc09bz

W&B tags on all runs:
- `path_c_kill_2026-05-11`
- `oracle_cf_1m_pnp`
- `oracle_cf_pushfix_followup`
- `path_c_kill_ocf_pnp_1m` (wandb auto-expanded from comma-separated env)

---

## Per-seed logs

| Seed | Log path |
|------|----------|
| 42   | `~/.local/state/oracle_cf_1m_pnp_s42.log` |
| 123  | `~/.local/state/oracle_cf_1m_pnp_s123.log` |
| 999  | `~/.local/state/oracle_cf_1m_pnp_s999.log` |

Launcher log: `~/.local/state/oracle_cf_1m_pnp.log`

---

## Rationale

The 250k-step KILL verdict may be premature. HER on FetchPickAndPlace-v4 typically
requires 500k–1M steps to converge. This re-run provides an honest verdict at the
published convergence horizon (1M steps), matching the methodology in the paper.
