# Push Rerun PID 131590 — DEAD (COMPLETED SUCCESSFULLY)

**Detected:** 2026-05-12 10:27 UTC by training-status-check agent

**Status: NOT a crash — job finished normally.**

PID 131590 (first seed train.py for `run_corrected_push_ocf.sh`) is no longer running. The nohup shell (PID 131586) is also gone.

All 3 seeds completed and are registered in W&B under tag `oracle_cf_pushfix`:

| Seed | W&B Run | Final Success Rate | Finished |
|------|---------|--------------------|----------|
| 42   | path_c_kill_ocf_push_fix_s42_seed42   | 0.300 | 09:44z |
| 123  | path_c_kill_ocf_push_fix_s123_seed123 | 0.250 | 09:59z |
| 999  | path_c_kill_ocf_push_fix_s999_seed999 | 0.600 | 10:14z |

**Mean corrected OCF-Push success: 0.383** (HER baseline: 0.617, delta = -0.234)

## Verdict

The bug fix improved OCF-Push from 0.000 to 0.383, but it still does not beat HER (0.617). **KILL verdict for Oracle-CF on FetchPush is confirmed.** No action required for relaunch — this is informational only.
