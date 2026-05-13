# Status Update — 15:15 PDT, 2026-05-12

## Oracle-CF 1M PnP

| Run                                   | global_step | SR   | State   |
|---------------------------------------|-------------|------|---------|
| path_c_kill_ocf_pnp_1m_s42_seed42     | 1,000,000   | 0.30 | finished |
| path_c_kill_ocf_pnp_1m_s123_seed123   | 1,000,000   | 0.90 | finished |
| **path_c_kill_ocf_pnp_1m_s999_seed999** | **349,500** | **0.40** | **running** |

Delta from 14:45: s999 advanced from ~107k → 349.5k (+242k steps, ~30min of wall time).
Progress: 34.95% of 1M. At current pace (~242k/30min), ETA to completion: ~5.6 hrs (roughly 21:00 PDT).
SR at 349k = 0.40 — ahead of s42 at same point (s42 was ~0.10 early), positive signal.

Checkpoint on disk: latest confirmed = step_300000 (step_350000 not yet written at query time).

---

## Phase 2 Attempt 5 — VLM CF / VCF Runs

**Modal**: 1 app alive (`ap-NWsFCh9kA9P0syU9JhIBAR`, ephemeral/detached, created 11:25 PDT, 10 tasks).

### Currently Running (10 runs)

All 10 runs show state=running. Real step counts from W&B summary `global_step`:

| Run                          | global_step | SR   | Notes                    |
|------------------------------|-------------|------|--------------------------|
| cf_push_s42_seed42           | 428,000     | 1.00 | Push: strong convergence |
| cf_push_s123_seed123         | 419,000     | 0.80 | Push: good               |
| cf_push_s999_seed999         | 401,900     | 0.95 | Push: strong             |
| cf_sld_s42_seed42            | 391,300     | 0.35 | Slide: moderate          |
| cf_sld_s123_seed123          | 393,950     | 0.20 | Slide: low               |
| cf_sld_s999_seed999          | 387,600     | 0.35 | Slide: moderate          |
| vcf_pp_s42_seed42 (vcf!)     | 190,350     | 0.10 | VCF PnP — see below      |
| cf_pp_s42_seed42             | 185,500     | 0.00 | CF PnP: stuck            |
| cf_pp_s999_seed999           | 185,400     | 0.15 | CF PnP: low              |
| cf_pp_s123_seed123           | 204,850     | 0.05 | CF PnP: very low         |

**Runs >= 200k steps**: 7 of 10 (all Push/Slide runs, plus vcf_pp_s42).
**Runs >= 50% of budget** (assuming 500k total): Push runs are at ~80–86%, Slide runs ~78%.

### Push SR by seed (cf_ prefix):
- s42: **1.00**, s123: **0.80**, s999: **0.95** — all strong

### Slide SR by seed (cf_ prefix):
- s42: **0.35**, s123: **0.20**, s999: **0.35** — moderate, improving

### PnP SR (cf_ prefix, ~185-205k steps):
- s42: **0.00**, s123: **0.05**, s999: **0.15** — very low, all lagging Push/Slide

---

## vcf_pp_s42 Verifier-Rejection Count

At global_step=190,350 (up from 143,100 at 14:45):
- `buffer/cf_verifications_attempted`: **134** (was 101 at 14:45 — added 33 attempts)
- `buffer/cf_verifications_rejected_no_success`: **134 (100%)**
- `buffer/cf_verifications_succeeded`: 0
- `buffer/cf_vlm_returned_none`: **227** (was 173 — VLM still returning None frequently)
- `eval/success_rate`: **0.10** (was 0.00 — slight improvement)

**Rejection trend: still 100% rejection rate.** +33 attempts since 14:45, all rejected. SR ticked up to 0.10 but no CF verifications have ever passed. The VLM-proposed CFs pass the generation step but none satisfy the success verifier.

---

## Finished (Crashed) Runs — Attempt 5 Older Batch

18 finished runs, all with global_step in range 512–890 (crashed very early):
- vcf_* runs died at ~500-900 steps
- cf_sld_* earlier instances died at ~800 steps
Consistent early-crash pattern from prior launch — all superseded by currently-running instances.

---

## Local Processes

```
226889  python train.py  oracle_cf.yaml  FetchPickAndPlace-v4  seed=999  (s999 1M run)
227277  python train.py  oracle_cf.yaml  FetchSlide-v4  seed=42   (Slide s42)
227278  python train.py  oracle_cf.yaml  FetchSlide-v4  seed=123  (Slide s123)
227279  python train.py  oracle_cf.yaml  FetchSlide-v4  seed=999  (Slide s999)
```

3 additional local FetchSlide Oracle-CF runs (250k budget) — not previously in status report. All running.

---

## Anomalies

1. FetchSlide Oracle-CF local processes (227277-279) were not in previous status update — new or previously not noticed.
2. cf_pp_* runs (PnP, non-vcf) at 185-205k steps with 0-5% SR — may not converge without VCF assist.
3. vcf_pp_s42 SR moved 0.00 → 0.10 despite 100% CF rejection — base policy learning is happening, CFs not contributing.

---

## Key Actions Needed

1. **Oracle s999**: On track. ~349k/1M (35%), SR=0.40. ETA ~21:00 PDT. No intervention needed.
2. **Push runs**: All 3 seeds strong (0.80-1.00 SR at ~410-428k steps). Likely to converge well before 500k if that is the budget.
3. **Slide runs**: Moderate (0.20-0.35 SR at ~388-394k steps). May need more steps or seed averaging.
4. **PnP cf_ runs**: Poor (0.00-0.15 SR at ~185-205k steps). Consider whether these need more time or a different approach.
5. **vcf_pp_s42 rejection**: Persistent 100% rejection — CF generation pipeline producing unverifiable counterfactuals for PnP. Needs code-level fix before another vcf PnP run.
6. **FetchSlide local runs**: Confirm these are intentional (250k budget each).
