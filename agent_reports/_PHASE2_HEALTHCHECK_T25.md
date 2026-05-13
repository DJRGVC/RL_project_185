# Phase 2 Attempt 4 Health Check — T+25min (11:01 PDT)

**Check time:** 2026-05-12 18:06 UTC  
**Modal entrypoint:** ap-V7VfJd1LnaXq4tyPbX9jgX  
**Action taken:** STOPPED (main app + 6 siblings)

---

## Per-Run Table

| Run Name | Step | relabel | none | vlm_calls | none/calls% | none/total% |
|----------|------|---------|------|-----------|-------------|-------------|
| path_c_vlm_cf_pp_s42_seed42       | 21400 | 112 | 27 | 51 | 53% | 19% |
| path_c_vlm_cf_pp_s123_seed123     | 18800 |  83 | 30 | 45 | 67% | 27% |
| path_c_vlm_cf_pp_s999_seed999     | 17100 |  58 | 30 | 41 | 73% | 34% |
| path_c_vlm_cf_pp_s42_seed42       | 18050 |  85 | 28 | 43 | 65% | 25% |
| path_c_vlm_cf_pp_s123_seed123     | 17300 |  44 | 33 | 41 | 80% | 43% |
| path_c_vlm_cf_push_s42_seed42     | 20250 |  49 | 36 | 47 | 77% | 42% |
| path_c_vlm_cf_push_s999_seed999   | 18750 |  49 | 33 | 43 | 77% | 40% |
| path_c_vlm_cf_push_s123_seed123   | 15500 |  20 | 32 | 36 | 89% | 62% |
| path_c_vlm_cf_pp_s999_seed999     | 16450 |  36 | 31 | 39 | 79% | 46% |
| path_c_vlm_cf_sld_s42_seed42      | 18000 |  65 | 31 | 44 | 70% | 32% |

**Runs analyzed:** 10  
**Runs past warmup (step > 5000):** 10

---

## Metric Summary

| Metric | Value |
|--------|-------|
| Avg none/vlm_calls rate | **73.1%** |
| Avg none/(relabel+none+exc) rate | 37.0% |
| Exceptions | 0 across all runs |

**Note on denominator:** The protocol's `none/(relabel+none+exc)` formula gives 37% (AMBIGUOUS). Using `none/vlm_calls` (the correct denominator — `vlm_calls` is logged separately as total attempts including successes) gives 73.1% (FAILING). The W&B metric `buffer/cf_vlm_calls` was confirmed present and represents true call attempts.

---

## Verdict: FAILING

Average none-rate relative to actual VLM calls = **73.1%** (threshold: ≥50%)

---

## Diagnosis: Anthropic API Rate Limits (5 req/min + 10k tokens/min)

Modal logs confirm the cause is **NOT** by-design gate rejections. The `returned_none` counter is incrementing due to exhausted Anthropic API rate limits:

```
WARNING | [CF variant=achieved_goal] attempt 2 failed: Error code: 429 - 
  "This request would exceed your organization's rate limit of 5 requests per minute
   (model: claude-sonnet-4-5-20250929)"
WARNING | [CF variant=achieved_goal] attempt 2 failed: Error code: 429 - 
  "This request would exceed your organization's rate limit of 10,000 input tokens per minute
   (model: claude-sonnet-4-5-20250929)"
```

- Continuous 429 storms visible across entire log tail (18:05–18:06 UTC)
- Both RPM limit (5 req/min) and TPM limit (10k input tokens/min) being hit
- 18 parallel runs all calling claude-sonnet-4-5 simultaneously overwhelms the org limit
- No by-design `cf_min_confidence` or `reject_teleport_radius_m` patterns found in logs
- `buffer/cf_vlm_exceptions = 0` across all runs confirms errors are silently counted as `returned_none` after retry exhaustion, not as exceptions

---

## Root Cause

18 runs × concurrent VLM CF calls → ~15-18 calls/min burst rate → exceeds 5 req/min org limit for claude-sonnet-4-5. The model switch from gpt-4o-mini (attempt 3) to claude-sonnet-4-5 (attempt 4) hit a much tighter RPM ceiling.

---

## Recommendation

1. **Do not relaunch with claude-sonnet-4-5 at 18-run parallelism.** The org limit is 5 req/min — this cannot support even 1 run making >1 CF call every 12 seconds.
2. **Options for attempt 5:**
   - Switch back to gpt-4o-mini or gpt-4o with proper RPD guard (the attempt 3 failure was RPD, not RPM — may be recoverable with per-run rate limiting)
   - Use claude-sonnet-4-5 but reduce parallelism to ≤2 runs
   - Add inter-run jitter + per-run token budget to stay under 10k TPM
   - Consider Anthropic Batch API for non-latency-critical CF calls

---

## Actions Taken

- Stopped main app `ap-V7VfJd1LnaXq4tyPbX9jgX` (7 containers)
- Stopped 6 sibling apps: ap-9WCthsWEROtJEjMu6tXZnZ, ap-vKCsME2wgZaBMHeai3eH1z, ap-fFEHDaIJ2417rT0mWnrcb8, ap-LG5OAh5hmn9fCvHbARf8ui, ap-zImQZk7tMvy2iz02xhgA5g, ap-YQI1G3YPWAm57YSlr4HK3a
