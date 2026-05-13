# Status Update 13:57 PDT — 2026-05-12

## Oracle-CF 1M PnP (PRIORITY)

**NOT YET COMPLETE — still running, ~95 min of wallclock elapsed past ETA**

| Run | State | Step | SR |
|-----|-------|------|----|
| path_c_kill_ocf_pnp_1m_s42_seed42 | running | 904,000 | 0.35 |
| path_c_kill_ocf_pnp_1m_s123_seed123 | running | 905,800 | 1.00 |

- Both procs confirmed alive (PIDs 199586, 199587).
- ~95k steps remain on each (~50 min at current throughput if ~2k steps/min).
- s123 hit SR=1.00 — full solve. s42 at 0.35, trending up from 0.30.
- Latest checkpoints (since 12:55): s42 up to step_900k, s123 up to step_900k.
- No step_950k or step_1000k dirs yet — confirms not finished.
- Seed 999 has NOT started for Oracle-CF 1M (no matching run in W&B).

## Phase 2 Attempt 5

**Modal app ap-NWsFCh9kA9P0syU9JhIBAR: ephemeral (detached), 10 tasks running.**

Running cf (VLM, non-verified) runs — healthy progress:

| Run | Step | SR |
|-----|------|----|
| vlm_cf_push_s42 | 238,600 | 0.50 |
| vlm_cf_push_s999 | 215,150 | 0.45 |
| vlm_cf_push_s123 | 235,800 | 0.10 |
| vlm_cf_sld_s42 | 222,650 | 0.10 |
| vlm_cf_sld_s123 | 223,550 | 0.10 |
| vlm_cf_sld_s999 | 217,550 | 0.00 |
| vlm_cf_pp_s42 | 104,750 | 0.00 |
| vlm_cf_pp_s123 | 118,150 | 0.00 |
| vlm_cf_pp_s999 | 108,550 | 0.10 |
| vlm_vcf_pp_s42 | 102,600 | 0.00 |

All 10 active runs alive. vcf_pp_s42 (verified) still at SR=0, step 102k — consistent with the 100% verifier-rejection concern from last update.

## Blockers / Concerns

1. **Oracle-CF 1M ETA slip**: Was ~13:08, now estimated ~14:50 PDT. Both procs still alive — no crash, just slower than predicted.
2. **vcf_pp_s42 verified run**: Still SR=0 at 102k steps. 100% verifier-rejection pattern not resolved.
3. **Seed 999 for Oracle-CF 1M**: Not started. Waiting on s42/s123 completion to assess whether a third seed is needed.
