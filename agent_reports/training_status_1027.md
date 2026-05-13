# Training Status — 2026-05-12 10:27 PDT (17:27 UTC)

Agent: training-status-check (Sonnet 4.6)

---

## W&B Tag Summary

| Tag | Total | Running | Finished | Crashed/Failed |
|-----|-------|---------|----------|----------------|
| `path_c_overnight_2026-05-11` | 22 | 0 | 22 | 0 |
| `oracle_cf_1m_pnp` | 2 | 2 | 0 | 0 |
| `path_c_vlm_2026-05-12` | 0 | 0 | 0 | 0 (tag not applied) |
| `path_a_pivot_2026-05-12` | 6 | 0 | 6 | 0 |

**Note on `path_c_vlm_2026-05-12` tag:** The 18 Phase 2 Modal runs were launched with per-run tags (e.g. `path_c_vlm_cf_pp`, `path_c_vlm_vcf_push`, etc.) but NOT the expected umbrella tag `path_c_vlm_2026-05-12`. Querying without this tag filter reveals the actual picture below.

---

## Path C Overnight (Phase 1) — COMPLETE

All 22 runs finished. Covers HER and Oracle-CF on FetchPickAndPlace, FetchPush, FetchSlide x 3 seeds. Max step at ~10264 (250k-step kills as designed).

---

## Oracle-CF 1M PnP — RUNNING (HEALTHY)

- **Runs:** 2 running (seed 42, seed 123) | seed 999 pending (sequential after batch 1)
- **PIDs:** 199586 (seed 42), 199587 (seed 123) — confirmed alive
- **Step progress:**
  - seed 42: global_step=40,200 / 1,000,000 (4.0%) — last heartbeat 17:27:54 UTC
  - seed 123: global_step=40,250 / 1,000,000 (4.0%) — last heartbeat 17:27:54 UTC
- **Step rate:** approx 178 steps/sec per process
- **eval/success_rate:** 0.0 at step 30k (expected — too early for PnP convergence)

### Expected milestones
| Milestone | Steps | Est. wall-clock |
|-----------|-------|-----------------|
| First eval | 50k | ~17:32 UTC |
| 10% done | 100k | ~17:34 UTC |
| 250k (KILL baseline) | 250k | ~17:50 UTC |
| Batch 1 complete (~1M) | 1M | ~19:25 UTC |
| Batch 2 seed 999 starts | — | ~19:25 UTC |
| All done (seed 999) | 1M | ~21:25 UTC |

---

## Path C Phase 2 (VLM) on Modal — ALERT: CRASHED

**Status: CRITICAL — 11 of 18 runs crashed within 6-26 seconds. 5 runs never appeared in W&B. 1 run currently starting (may also crash).**

### Modal app
- `ap-bLMnC0sqx6kVCe7oAERWUQ` — state: ephemeral (detached), 10 tasks, created 10:27 PDT
- Previous apps `ap-dzTbfB1VPzyhx73lN1Jles` and `ap-OCyr832mvzGOvjyePo9qjP` stopped (10:25-10:26 PDT)
- Old Phase 1 app `ap-PWMTBsinFWdaAK048ySfBV` stopped (22:20 PDT 5/11)

### Run-level status (found 16/18 expected, 5 missing entirely)

| Run name | State | global_step | Runtime | VLM calls | VLM None |
|----------|-------|-------------|---------|-----------|----------|
| path_c_vlm_cf_push_s42 | finished | 1600 | 26s | 3 | 3 |
| path_c_vlm_cf_push_s999 | finished | 1250 | 23s | 2 | 2 |
| path_c_vlm_cf_sld_s42 | finished | 1150 | 21s | 2 | 1 |
| path_c_vlm_cf_push_s123 | finished | 850 | 16s | 2 | 2 |
| path_c_vlm_cf_sld_s123 | finished | 700 | 13s | 1 | 1 |
| path_c_vlm_cf_sld_s999 | finished | 350 | 6s | 0 | 0 |
| path_c_vlm_vcf_push_s42 | finished | 350 | 8s | 0 | 0 |
| path_c_vlm_vcf_push_s123 | finished | 350 | 9s | 0 | 0 |
| path_c_vlm_vcf_push_s999 | finished | 350 | 6s | 0 | 0 |
| path_c_vlm_vcf_sld_s42 | finished | 250 | 6s | 0 | 0 |
| path_c_vlm_cf_pp_s42 | running | N/A | ~0s | — | — |
| path_c_vlm_vcf_pp_s42 | MISSING | — | — | — | — |
| path_c_vlm_vcf_pp_s123 | MISSING | — | — | — | — |
| path_c_vlm_vcf_pp_s999 | MISSING | — | — | — | — |
| path_c_vlm_vcf_sld_s123 | MISSING | — | — | — | — |
| path_c_vlm_vcf_sld_s999 | MISSING | — | — | — | — |

### Crash signature
- `buffer/cf_vlm_returned_none > 0` in every run that made VLM calls — VLM returning None
- `buffer/cf_relabel_count = 0` in all runs — zero VLM relabeling occurred
- `buffer/cf_vlm_exceptions = 0` — silent None, not a Python exception
- Runs with 0 VLM calls also terminated early — possibly OOM or config error pre-VLM

**Likely root cause:** VLM API credentials not injected into Modal containers. Silent None return with no exception matches a missing-API-key stub behavior. Check Modal secrets configuration.

---

## Path A Pivot — COMPLETE

All 6 runs finished (FetchPush, FetchPickAndPlace, FetchSlide x seed 42, 123). Max steps ~11.6k-12.2k. Bidirectional HER pivot runs.

---

## Process / Infrastructure

| Component | Status |
|-----------|--------|
| Oracle CF 1M PIDs (199586, 199587) | ALIVE |
| overnight_watchdog (PID 56086) | ALIVE |
| Modal Phase 2 app `ap-bLMnC0sqx6kVCe7oAERWUQ` | RUNNING (ephemeral, 10 tasks) |
| Phase 2 launch flag | EXISTS (set 2026-05-11 22:21) |

---

## Anomalies / Action Items

1. **CRITICAL — Phase 2 VLM crash:** All VLM runs dying in seconds. Check Modal secrets for VLM API key.
2. **TAG MISMATCH:** Phase 2 runs lack `path_c_vlm_2026-05-12` umbrella tag.
3. **MISSING RUNS:** 5 of 18 VLM runs never appeared in W&B (crashed before init).
4. **NEW MODAL APP:** `ap-bLMnC0sqx6kVCe7oAERWUQ` with 10 tasks at 10:27 PDT — unclear if Phase 2 relaunch or different job.
5. **Oracle CF success_rate=0 at step 30k** — normal/expected for FetchPickAndPlace-v4.

Alert file written: `agent_reports/_phase2_LAUNCH_FAILED.md`
