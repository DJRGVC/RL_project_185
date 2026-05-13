# AM Status — 2026-05-12 10:54 PDT

**Agent:** status-check (Sonnet 4.6), 5-min budget  
**Checked at:** 2026-05-12T17:54Z

---

## Summary

Phase 2 attempt 4 (Modal entrypoint `ap-V7VfJd1LnaXq4tyPbX9jgX`, launched 10:34 PDT) is healthy: 10 of 18 runs are `running` in W&B, all confirmed `anthropic / claude-sonnet-4-5`, with `cf_relabel_count` actively growing (range 10–53 at steps 9950–12650) — no runs stuck at 0. The none-rate is ~40–50% (`cf_vlm_returned_none` ≈ 20–21 vs relabel counts 10–53), which is above the target < 30% threshold flagged in `_PHASE2_HEALTH_CHECK.md` — worth monitoring but not yet an abort condition. The 8 `verified_cf` runs remain queued inside Modal's container-start phase (sibling apps `ap-LG5OAh5hmn9fCvHbARf8ui` etc. show 0 tasks active), consistent with the Modal A10G concurrency cap. Attempt 3 (`ap-bLMnC0sqx6kVCe7oAERWUQ`) is confirmed `stopped`. Oracle-CF 1M PnP seeds 42 and 123 are both `running` locally at step ~273–275k (PIDs 199586/199587 alive), progressing at ~11 steps/sec wall-clock; seed 42 has `eval/success_rate=0.0` and seed 123 has `0.1` — both within expected slow-start range for FetchPickAndPlace at 27% completion of 1M steps. Three additional FetchSlide-v4 oracle_cf runs (seeds 42/123/999, PIDs 204393/204425/204426) are also running locally — these appear to be a follow-on experiment not mentioned in the handoff but are not interfering. Phase 1 (`path_c_overnight_2026-05-11`) is stable at 22 finished / 3 running, no regressions detected.

**ETAs:**
- Phase 2 all 18 runs done: ~12:30 PDT (10:34 + ~2hr first wave; queued 8 start as slots free)
- Oracle-CF 1M seeds 42/123 done: ~12:25 PDT (~1.75 hr remaining at ~10.9 min/10k steps each)
- Seed 999 (sequential): ~14:25 PDT

**Anomalies:**
- `cf_vlm_returned_none` ratio ~40–50% on sampled runs (target <30%); not yet abort-level but warrants a check at step 20k per health-check protocol.
- 3 unexpected FetchSlide oracle_cf processes running locally (PIDs 204393/204425/204426) — likely a prior agent's experiment; not touching them.
- 5 sibling Modal apps show 0 active tasks (verified_cf queue waiting for A10G slots) — this is expected behavior under the concurrency cap, not an error.
