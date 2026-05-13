# Phase 2 Attempt 4 — FAILED

**Time:** 2026-05-12 18:07 UTC  
**Modal app:** ap-V7VfJd1LnaXq4tyPbX9jgX (STOPPED)  
**Failure mode:** Anthropic API rate limit (5 req/min + 10k TPM) for claude-sonnet-4-5  

VLM-CF mechanism silently degraded: 73% of VLM calls returned None due to 429 rate limit exhaustion after retries. Runs were training but CF relabeling was ~75% ineffective. All 7 containers + 6 sibling apps stopped at T+90min.

See `_PHASE2_HEALTHCHECK_T25.md` for full diagnosis and attempt 5 recommendations.
