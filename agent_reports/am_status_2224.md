# Status Delta — 2026-05-12 22:24 PDT

**Modal:** 1 app active (`ap-NRYpqbAgLKspwPdJRjZ1xx`, description "semantic-p…"), state ephemeral/detached, 10 tasks. Note: the Phase 2 Modal app (`ap-V7VfJd1LnaXq4tyPbX9jgX`) was stopped at 18:07 UTC after Attempt 4 failure.

**Local procs:** 11 python-train processes total; 8 with `total_steps=1000000`. Exceeds expected 7 — likely includes residual psweep runs. GPU at 88% util, 3735/16303 MiB VRAM.

**Watchdogs:** 2 alive — `overnight_watchdog.sh` (PID 56086) and `launch_waveB_when_psweep_done.sh` (PID 258223). Missing: `wait_for_her1m` and `wait_for_outline` (expected 3-4 total, only 2 found).

**W&B:** 1 NEW run in last 45min (`path_c_vlm_cf_psweep_p50_pp_s123_seed123`, running). TOTAL RUNNING: 20, all `path_c_vlm_cf_psweep_*` variants, steps ranging 6k–20k. HER 1M run (`path_c_her_1m_pp_s999`) at step 18562.

**Recent commits (top 3):**
- `e38403d` Paper iter §5.4: bridge cross-task pilot to Phase 2 convergent evidence
- `5ce97fb` Paper iter §1 bullets (1)(2): name IS-pairing requirement, soften uniqueness claim
- `1ecd34c` Section dive 2135: §5.5 real-data — policy-precision bridge to verified-CF

---

## !! BRIGHT FLAG — THREE ACTIVE FAILURE ALERTS !!

1. **`_phase2_RETRY3_FAILED.md` (11:07 PDT today)** — Phase 2 Attempt 4 STOPPED. Root cause: Anthropic API rate limits (5 RPM, 10k TPM) for claude-sonnet-4-5. With 18 parallel runs making concurrent VLM CF calls, 73.1% of VLM calls returned None (threshold: ≥50% = FAILING). All 7 containers + 6 sibling Modal apps stopped. Attempt 5 requires model switch back to gpt-4o-mini or reducing parallelism to ≤2 runs.

2. **`_wandb_STALLED.md` (10:46 PDT today)** — W&B stalled for 478 minutes as of that time. However, W&B API is responding now (20 running runs visible), so this may be stale or referring to a specific run's log stream.

3. **`_phase2_LAUNCH_FAILED.md` (10:29 PDT today)** — Earlier Phase 2 launch failure (pre-dates the Attempt 4 health check).

**Older (pre-today) alerts:** `_push_rerun_DEAD.md` (03:29 PDT), `_CODE_BLOCKER.md` (00:08 PDT).

---

**Action needed on wake:** Phase 2 VLM-CF is blocked. Attempt 5 options per health check: (a) revert to gpt-4o-mini with per-run rate limiting, (b) cap parallelism ≤2 for claude-sonnet-4-5, (c) use Anthropic Batch API.
