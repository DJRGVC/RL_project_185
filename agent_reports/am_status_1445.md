# Status Update — 14:45 PDT, 2026-05-12

## Oracle-CF 1M PnP — COMPLETE (seeds 42 & 123)

| Seed | Final Step | Final SR | State    |
|------|-----------|----------|----------|
| s42  | 1,000,000 | **0.30** | finished |
| s123 | 1,000,000 | **0.90** | finished |
| **Mean (s42+s123)** | — | **0.60** | — |

- Both 1M checkpoints confirmed on disk:
  - `checkpoints/path_c_kill_ocf_pnp_1m_s42_seed42/step_1000000`
  - `checkpoints/path_c_kill_ocf_pnp_1m_s123_seed123/step_1000000`
- s42 underperformed last-check projection (was SR=0.35 @ 904k; landed at 0.30 final — slight drop at end).
- s123 held strong (was SR=1.00 @ 905k; landed at 0.90 final — minor regression from top).

**Seed 999 — YES, started.** Running at step=107,550, SR=0.10 (very early, ~10.8% through). ETA to 1M: roughly 14–15 hrs at current pace.

---

## Phase 2 Attempt 5 — VLM VCF Runs

Top runs by env (prefix `path_c_vlm_vcf_`), all state=finished except vcf_pp_s42 (running):

| Run                          | Step    | SR   | Notes                   |
|------------------------------|---------|------|-------------------------|
| vcf_pp_s999                  | 13,500  | 0.10 | finished (too early?)   |
| vcf_push_s42                 | 17,350  | 0.05 | finished                |
| vcf_pp_s42 (running)         | 143,100 | 0.00 | active, 0% SR so far    |
| vcf_pp_s123                  | 14,000  | 0.00 | finished                |
| vcf_push_s123/s999/sld_s42   | ~350    | n/a  | crashed early (step~350)|

PnP none-rate: not logging `eval/none_rate` field in W&B summary — field absent across all vcf runs.

---

## vcf_pp_s42 Verifier-Rejection Analysis

At step=143,550 (running):
- `buffer/cf_verifications_attempted`: 101
- `buffer/cf_verifications_rejected_no_success`: **101 (100%)**
- `buffer/cf_verifications_succeeded`: 0
- `buffer/cf_verifications_success_rate`: **0.0**
- `buffer/cf_vlm_returned_none`: 173
- `eval/success_rate`: 0.0

**YES — still 100% rejection rate.** Every single CF attempt rejected for `no_success`. VLM is generating CFs but none pass the success verifier. This has not improved despite >140k steps.

---

## Modal

One app running (ephemeral/detached, created 11:25 PDT): `ap-NWsFCh9kA9P0syU9JhIBAR` (semantic-p…, 10 tasks). Two stopped apps from earlier today.

---

## Key Actions Needed

1. **Oracle-CF 1M mean = 0.60** — solid result. Lock in for paper §4 table once s999 finishes (or use 2-seed mean now as preliminary).
2. **vcf_pp_s42 100% rejection** — this is a systematic failure. CF generation produces non-successful states; verifier blocks all of them. Consider relaxing success threshold or checking CF generation logic.
3. **Phase 2 Att5 Push/Slide** — most runs died at step ~350 (crash). Need diagnosis before next relaunch.
