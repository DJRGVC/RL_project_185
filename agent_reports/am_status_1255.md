# Status Update — 2026-05-12 12:55 PDT

## (a) Modal App — Phase 2 Attempt 5

**App:** `ap-NWsFCh9kA9P0syU9JhIBAR` — status: **ephemeral (detached)**, Tasks: **10** (at Modal's 10-GPU concurrency cap).
**Queued:** 8 verified_cf runs still behind the cap, waiting for slots.

All 10 running runs confirmed live in W&B since ~18:25–18:28Z. Only 1 verified_cf (vcf_pp_s42) made it through; the other 9 running are vlm_cf. All runs are early-stage — this is a W&B sync lag effect: W&B summaries show 1.4k–3.2k steps but the local log evidence and heartbeat times confirm all are progressing at ~1300–1800 steps/min (est from timestamps).

### Per-run table (attempt 5, 10 running)

| Run | Step (W&B) | vlm_calls | cf_relabeled | cf_returned_none | none/calls | sr |
|-----|-----------|-----------|-------------|-----------------|------------|-----|
| vlm_cf_push_s42 | 3198 | 90 | 319 | 30 | **33%** | 0.05 |
| vlm_cf_push_s123 | 3128 | 90 | 346 | 29 | **32%** | 0.00 |
| vlm_cf_push_s999 | 2616 | 75 | 275 | 21 | **28%** | 0.20 |
| vlm_cf_sld_s42 | 2956 | 89 | 418 | 9 | **10%** | 0.00 |
| vlm_cf_sld_s123 | 2970 | 90 | 419 | 9 | **10%** | 0.00 |
| vlm_cf_sld_s999 | 2874 | 87 | 379 | 11 | **13%** | 0.05 |
| vlm_cf_pp_s42 | 1531 | 45 | 192 | 10 | **22%** | 0.00 |
| vlm_cf_pp_s123 | 1619 | 47 | 203 | 10 | **21%** | 0.00 |
| vlm_cf_pp_s999 | 1480 | 43 | 157 | 13 | **30%** | 0.10 |
| vlm_vcf_pp_s42 | 1383 | 40 | 0 | 40 | **100%** | 0.00 |

**None/calls rates:** Push=28–33%, Slide=10–13%, PnP(vlm_cf)=21–30% — all WELL BELOW the 73% failure threshold from attempts 3/4. The split-provider routing is working.

**CRITICAL EXCEPTION — vlm_vcf_pp_s42:** 100% none-rate (40/40 calls returned none, 0 relabeled). `cf_verifications_rejected_no_success: 24` — the verified_cf pipeline is rejecting all VLM outputs at the verification stage. This is distinct from rate-limit none-rate; it's a semantic rejection (VLM proposes a CF but the simulated rollout doesn't achieve the goal). Not yet a crisis at step 1383, but flags that the vcf verification gate may be too strict on PnP at current early-training success rates.

**0/10 runs >= 30k steps.** Avg step: ~2,376. These runs are ~1.5–2 hours old at this check — expected pace is ~500k steps in ~5.2h, so by step count these are running **slower than projected** (~750 steps/min vs 1600 projected at T+2min). Possible cause: Modal cold-start overhead, or the GPU concurrency cap forcing some sharing.

**ETA revision:** At ~750–1000 steps/min, 500k steps = 8–11h wall-clock. Revised completion: **~20:00–22:00 PDT** (not 17:00–18:00 as originally projected).

## (b) Oracle-CF 1M PnP — Progress

Both local seeds (PIDs 199586, 199587) healthy. **W&B step counts (~24k) are stale due to W&B sync lag.** Local logs are authoritative:

| Run | PID | Local log step | Progress | Last eval success | Status |
|-----|-----|---------------|----------|-------------------|--------|
| pnp_1m_s42 | 199586 | **~591,000** | **59.1%** | 0.35 (at 590k) | Normal — new best 0.35 saved |
| pnp_1m_s123 | 199587 | **~593,000** | **59.3%** | 0.45 (at 590k) | Normal |

Rate: ~1000 steps every 11–12s (≈5,000 steps/min per seed). No signs of convergence stall — loss is still declining. Success rates fluctuating 0.20–0.45 which is typical mid-training variance for PnP HER.

**ETA to 1M:** ~(1M-592k) / 5000 steps/min ≈ 82 min → finish ~**14:15 PDT**.

## (c) Oracle-CF FetchSlide — Bonus Local Runs

3 new local Slide runs (PIDs 213984, 214016, 214017) started at ~18:36Z. These are a THIRD set — the second set (finished, W&B shows 10264 steps, success 0.1–0.2) appear to have hit an issue. These new ones are at ~104k/250k (41.6%).

| Run | PID | Local log step | Progress | Last eval success |
|-----|-----|---------------|----------|-------------------|
| sld_s42 | 213984 | **~104,000** | **41.6%** | 0.000 (at 100k) |
| sld_s123 | 214016 | **~104,000** | **41.6%** | 0.000 |
| sld_s999 | 214017 | **~104,000** | **41.6%** | 0.050 |

FetchSlide success = 0 at 100k steps is expected — this task is notoriously hard and typically needs >150k to see any movement.

**ETA:** ~(250k–104k) / 1000 steps/min per log ≈ ~25 min → finish ~**13:20 PDT**.

Note: There were also previous finished Slide runs (step=10264, success up to 0.20) from ~17:46Z — unclear why these ran only 10264 steps instead of 250k. Possible early-stop bug or manual kill.

## (d) Anomalies / Red Flags

1. **vlm_vcf_pp_s42: 100% verification failure** — `cf_verifications_rejected_no_success: 24/24`. All proposed CFs verified as non-achieving. At step 1383 it's too early to panic, but if this persists to 10k steps the vcf variant will have no CF data at all for PnP. Watch for this in the next status check.

2. **W&B sync lag on Oracle-CF PnP** — W&B shows only 24k steps while local logs show 590k. The runs are logging locally and syncing only intermittently. Not a training issue, but W&B dashboards will be misleading until sync catches up.

3. **Phase 2 throughput lower than projected** — ~750 steps/min vs 1600 step/min estimated at T+2min. Could be due to Modal GPU concurrency cap (10 runs × ≥70 VLM calls each already visible, so VLM latency may be the bottleneck rather than training compute). No alert threshold crossed, but completion pushed to evening.

4. **8 queued runs still waiting** — Modal hard cap at 10 concurrent. The queued 8 will not start until current runs complete. Given revised 8–11h runtime, queued runs won't start until ~20:00–21:00 PDT and won't finish until **~04:00–08:00 PDT tomorrow**.

## (e) ETA Summary

| Milestone | ETA |
|-----------|-----|
| Oracle-CF Slide 3× seeds done | ~13:20 PDT |
| Oracle-CF PnP 1M seeds done | ~14:15 PDT |
| Phase 2 attempt 5 first 10 runs done | ~20:00–22:00 PDT |
| Phase 2 queued 8 runs start | ~20:00–22:00 PDT |
| Phase 2 queued 8 runs done | ~04:00–08:00 PDT tomorrow |

---
*Generated by status agent at 12:55 PDT. READ-ONLY — no modifications made.*
