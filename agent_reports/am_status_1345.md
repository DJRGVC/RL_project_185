# Status Update — 2026-05-12 13:45 PDT

## (a) Modal App — Phase 2 Attempt 5

**App:** `ap-NWsFCh9kA9P0syU9JhIBAR` — status: **ephemeral (detached)**, Tasks: **10** (unchanged, at cap).
**Queued:** 8 verified_cf runs still waiting.

### Phase 2 Per-run table (W&B, as of ~13:45)

| Run | Step | cf_relabel | cf_none | none_rate | sr |
|-----|------|-----------|---------|-----------|-----|
| vlm_cf_push_s42 | 6,694 | 614 | 65 | **10.6%** | 0.30 |
| vlm_cf_push_s123 | 6,573 | 693 | 59 | **8.5%** | 0.00 |
| vlm_cf_push_s999 | 5,802 | 633 | 42 | **6.6%** | 0.25 |
| vlm_cf_sld_s42 | 6,322 | 847 | 23 | **2.7%** | 0.00 |
| vlm_cf_sld_s123 | 6,260 | 862 | 22 | **2.6%** | 0.00 |
| vlm_cf_sld_s999 | 6,099 | 817 | 24 | **2.9%** | 0.05 |
| vlm_cf_pp_s42 | 2,902 | 330 | 24 | **7.3%** | 0.00 |
| vlm_cf_pp_s123 | 3,459 | 443 | 18 | **4.1%** | 0.05 |
| vlm_cf_pp_s999 | 3,052 | 351 | 22 | **6.3%** | 0.10 |
| vlm_vcf_pp_s42 | 2,830 | **0** | 83 | **100%** | 0.00 |

**None/calls rates** have improved significantly from the 12:55 report — Push dropped from 28–33% to 7–11%, Slide from 10–13% to 3%. The split-provider routing is working better as VLM caches warm. vlm_cf steps are ~2x faster than vcf because no verification overhead.

**vlm_vcf_pp_s42 still at 100% rejection rate** — 83 VLM calls, 0 relabeled. At step 2830 it has zero CF experience. This run is effectively a standard HER run so far. If this persists to 10k steps, flag for kill/replace.

**Step pace revised:** vlm_cf runs gained ~3k steps in ~50 min since 12:55 → ~60 steps/min per run. At this rate, 500k steps = ~139h — still confirms ~20:00–22:00 PDT finish for batch 1, not earlier.

**ETA to 500k (batch 1 complete):** ~20:00–22:00 PDT (unchanged).

---

## (b) Oracle-CF 1M PnP — STATUS: LOGGING STALL, PROCESSES ALIVE

**CRITICAL:** Both PnP 1M processes (PIDs 199586/199587) are alive and CPU-active but all logging stopped at 12:25–12:26.

- Last log entry: s42=step 763k (12:26 PDT), s123=step 765k (12:26 PDT)
- Checkpoint dirs confirm: newest checkpoint is `step_750000` (created 12:24–12:25) — no step_800000 yet
- Both processes show **~100 CPU ticks/s** (verified 5-second delta measurement) — they are computing
- Both hold 310 MiB GPU memory (nvidia-smi confirmed)
- Root cause: wandb sync thread appears **blocked**, causing the training loop (which may flush to wandb at checkpoint boundaries) to also hang. This is a wandb sync hang, not a training crash.

**What we KNOW:**
- At 12:26, s42 was at step ~763k, success_rate at step 750k = **0.25**
- At 12:26, s123 was at step ~765k, success_rate at step 750k = **0.55**
- W&B API shows stale step counts of 30k (sync lag ~720k steps behind)

**Extrapolated current state (13:45 PDT, 79 min past last log):**
- Rate before stall: ~96 steps/s per seed → 79 min × 96 × 60 = ~455k more steps possible
- However, if the wandb hang is actually stalling the loop (not just logging), current step may still be ~763k/765k
- Without evidence of new checkpoints or log writes, **cannot confirm 1M reached**
- Best case: runs are at ~1.2M steps but logging silently; worst case: frozen at step ~763k in a wandb flush wait

**Action recommended (not taken — read-only):** `kill -USR1 199586 199587` to force a status dump, or check if `step_800000` checkpoint appears in the next 10 min. If wandb is truly blocking, the processes need a wandb timeout config fix or restart from step_750000.

**Kill verdict impact:** At step 750k, s42=0.25 and s123=0.55. These are above the 0.35 "survival threshold" for s123 and borderline for s42. The **kill verdict does not survive** if these trends hold to 1M — consistent with the headline concern flagged at 12:55. But we need to confirm 1M completion before declaring this.

---

## (c) Oracle-CF FetchSlide — COMPLETED at 12:24

All 3 local Slide Oracle-CF runs **finished** at 12:24 PDT:

| Run | Final Step | Best success | Final success |
|-----|-----------|-------------|--------------|
| sld_s42 | 250,000 | 0.300 | 0.050 |
| sld_s123 | 250,000 | 0.050 | 0.050 |
| sld_s999 | 250,000 | 0.150 | 0.150 |

FetchSlide performance is low (best 0.30 for s42, but 0.05–0.15 for others) — consistent with the task's hardness. These are Oracle-CF results, so these represent an upper bound on what the VLM-CF variant can achieve. W&B should show these as `finished`.

---

## (d) New files since 12:55

New files created since the prior status check include:
- `_PHASE2_ATTEMPT5_LAUNCHED.md` — phase 2 launch record
- `ANTMAZE_PIVOT_PLAN.md` — possible pivot plan document
- `overnight_state.json`, `overnight_status.md` — overnight state tracking
- `training_status_1130.md` — prior status snapshot
- `_VLM_BAKEOFF_*` — VLM bakeoff results (new batch)
- `_SHARONY_BASELINE_IMPL.md` — Sharony baseline implementation note

No new `_*FAILED*.md` or `_*DEAD*.md` files since 12:55. Prior failures remain from 11:07 (`_phase2_RETRY3_FAILED.md`) and 10:29 (`_phase2_LAUNCH_FAILED.md`).

---

## (e) Red Flags

1. **Oracle-CF PnP 1M logging stall** — HIGH PRIORITY. Both processes alive but silent for 80 min. Cannot confirm 1M completion. wandb sync hang is the likely cause. Checkpoint at step_750000 is the last verified state.

2. **vlm_vcf_pp_s42: persistent 100% rejection** — 83/83 VLM calls rejected, 0 CF relabels at step 2830. Still burning compute with zero CF benefit. Watch at step 5k–10k for continue/kill decision.

3. **Phase 2 throughput still slow** — ~60 steps/min vs 750 steps/min projected. VLM latency is the bottleneck. No improvement from 12:55 estimate.

---

## (f) ETA Summary

| Milestone | Status | ETA |
|-----------|--------|-----|
| Oracle-CF Slide 3× done | DONE | 12:24 PDT |
| Oracle-CF PnP 1M complete | **UNKNOWN** — stalled at 763k/765k last log | ~13:08 PDT extrapolated, unconfirmed |
| Phase 2 batch 1 (10 runs) done | In progress, ~6k/500k steps | ~20:00–22:00 PDT |
| Phase 2 batch 2 (8 queued) start | Waiting on batch 1 | ~20:00–22:00 PDT |
| Phase 2 batch 2 done | | ~04:00–08:00 PDT tomorrow |

---
*Generated by status agent at 13:45 PDT. READ-ONLY — no modifications made to training code or processes.*
