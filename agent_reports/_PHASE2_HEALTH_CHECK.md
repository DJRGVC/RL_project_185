# Phase 2 Retry (Attempt 4) — VLM Health Check
**Launched:** 2026-05-12 17:34 UTC (10:34 PDT)
**Modal entrypoint app:** `ap-V7VfJd1LnaXq4tyPbX9jgX` (7 worker tasks)
**Plus spawned siblings (one app per `train_remote.spawn`):**
`ap-9WCthsWEROtJEjMu6tXZnZ`, `ap-vKCsME2wgZaBMHeai3eH1z`, `ap-fFEHDaIJ2417rT0mWnrcb8`,
`ap-LG5OAh5hmn9fCvHbARf8ui`, `ap-zImQZk7tMvy2iz02xhgA5g`, `ap-YQI1G3YPWAm57YSlr4HK3a`
**Status: LAUNCHED (initial)**

---

## Verdict (2 sentences)

All 18 Phase-2 jobs were re-spawned with `vlm_provider=anthropic, vlm_model=claude-sonnet-4-5` after attempt 3 collapsed under the OpenAI free-tier `gpt-4o-mini` RPD cap. As of the first health check (~T+2 min), 10 vlm_cf runs are visible in W&B as `running` with the new Sonnet configuration; the 8 verified_cf runs are still queueing inside Modal's container-start phase.

---

## Configuration changes (committed in 94fd13f on `agent/pathc-lead`)

- `configs/vlm_cf.yaml`: `vlm_provider: openai -> anthropic`, `vlm_model: gpt-4o-mini -> claude-sonnet-4-5`
- `configs/verified_cf.yaml`: same switch
- `agent_reports/overnight_path_c_plan.json::phase2_vlm._per_task_vlm_models`: normalised FetchPush-v4 and FetchSlide-v4 to `anthropic / claude-sonnet-4-5` (previously openai/gpt-4o-mini). Added `_per_task_vlm_models_note` recording the rationale.

Smoke test: `make_counterfactual_fn(provider='anthropic', variant='all', model='claude-sonnet-4-5')` constructs cleanly inside the local venv.

---

## Per-run state at T+2 min (sampled 17:36Z)

10 W&B runs visible with `provider=anthropic, model=claude-sonnet-4-5` confirmed via run.config:

| Run | State | provider | model |
|-----|-------|----------|-------|
| path_c_vlm_cf_pp_s42_seed42 (x2) | running | anthropic | claude-sonnet-4-5 |
| path_c_vlm_cf_pp_s123_seed123 (x2) | running | anthropic | claude-sonnet-4-5 |
| path_c_vlm_cf_pp_s999_seed999 (x2) | running | anthropic | claude-sonnet-4-5 |
| path_c_vlm_cf_push_s42_seed42 | running | anthropic | claude-sonnet-4-5 |
| path_c_vlm_cf_push_s123_seed123 | running | anthropic | claude-sonnet-4-5 |
| path_c_vlm_cf_push_s999_seed999 | running | anthropic | claude-sonnet-4-5 |
| path_c_vlm_cf_sld_s42_seed42 | running | anthropic | claude-sonnet-4-5 |

Note: the duplicate `cf_pp_*` entries (one set at 17:33Z, another at 17:34Z) are the
Modal `train_remote.spawn` lag — the second batch will get auto-killed by W&B as the older
session takes ownership; not a quota or wiring issue.

Step counts and `cf_relabel_count` / `cf_vlm_returned_none` are not yet populated because
`training.log_interval=1000` and the new SAC processes are still inside the replay-buffer
warmup (no rows committed at sample time).

---

## Cost projection (informational)

Sonnet 4.5, 18 runs x 500k steps x CF every ~50 steps ≈ 180k CF calls.
At ~$0.003 input + ~$0.015 output per call ≈ **~$160 total spend** for Phase 2.
User authorised "no cap" for this retry. If budget pressure arrives, raise
`replay.cf_call_interval=8 -> 32` via launch override to quarter the bill.

---

## Next health check should verify

1. All 18 runs eventually appear in W&B (8 verified_cf still queued at T+2 min).
2. `cf_relabel_count` > 0 by step ~5k on at least 3 of 6 cf_pp runs (matches the prior
   Sonnet 4.5 baseline of 19-45 relabels at 2400-4100 steps).
3. `cf_vlm_returned_none / (cf_vlm_returned_none + cf_relabel_count) < 0.3` on PnP runs.
4. No more `OpenAI RPD` 429 errors in Modal logs (only Anthropic should be called now).
5. Anthropic token-rate 429s, if any, should be retried internally by the SDK and not
   collapse runs into vanilla HER.

If any of (2)-(5) fails by step 20k, write `_phase2_RETRY2_FAILED.md` and stop.

---

## Files touched
- `configs/vlm_cf.yaml`
- `configs/verified_cf.yaml`
- `agent_reports/overnight_path_c_plan.json`
- `agent_reports/_PHASE2_HEALTH_CHECK.md` (this file)
