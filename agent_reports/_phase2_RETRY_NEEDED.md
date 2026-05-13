# Phase 2 Attempt 3 — STOPPED. Retry Required.
**Stopped:** 2026-05-12 ~17:36 UTC  
**Reason:** OpenAI gpt-4o-mini RPD quota exhausted (10k/day free tier fully consumed)

---

## Fix Required Before Attempt 4

### Option A (Recommended): Switch all tasks to Anthropic
Edit `configs/vlm_cf.yaml` and `configs/verified_cf.yaml`:
```yaml
vlm_model: claude-sonnet-4-5   # was: gpt-4o-mini
```
`cf_pp` runs proved Anthropic works at 18-run parallelism. Apply globally.

### Option B: Upgrade OpenAI to Tier 1 paid
- Add $5+ credit at platform.openai.com → RPD limit lifts
- Free-tier RPD=10,000 is exhausted in ~3 hrs with 18 concurrent runs

### Option C: Stagger launches
- Launch 6 runs at a time with 2-hour gaps
- Keeps within the 10k RPD limit per batch

---

## Do NOT relaunch until:
- [ ] OpenAI quota resets (midnight UTC) OR paid tier added, OR
- [ ] VLM model switched to Anthropic across all task configs

---

## What was lost
- 3 `cf_pp` runs were at step ~2400-4100 (< 1% of 500k) — negligible
- 6 `cf_push`/`cf_sld` runs were fully degraded (vanilla HER), no valid VLM data
- No usable Phase 2 checkpoints from this attempt
