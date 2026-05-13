# Status Update — 15:45 PDT, 2026-05-12

## Modal App

`ap-NWsFCh9kA9P0syU9JhIBAR` — ephemeral/detached, 10 tasks, still alive (created 11:25 PDT).

---

## Phase 2 Attempt 5 — VLM CF / VCF Runs (delta from 15:15)

All 10 runs still `running`.

| Run                              | global_step | SR    | Delta from 15:15         |
|----------------------------------|-------------|-------|--------------------------|
| cf_push_s42_seed42               | 494,150     | 0.95  | +66k steps; SR held 1.00→0.95 |
| cf_push_s123_seed123             | 494,400     | 0.95  | +75k steps; SR held 0.80→0.95 |
| cf_push_s999_seed999             | 469,300     | 0.80  | +67k steps; SR held 0.95→0.80 |
| cf_sld_s42_seed42                | 450,000     | 0.50  | +59k steps; SR 0.35→0.50 ↑ |
| cf_sld_s123_seed123              | 462,250     | 0.60  | +68k steps; SR 0.20→0.60 ↑ big jump |
| cf_sld_s999_seed999              | 455,000     | 0.55  | +67k steps; SR 0.35→0.55 ↑ |
| cf_pp_s42_seed42                 | 224,300     | 0.00  | +39k steps; still stuck  |
| cf_pp_s123_seed123               | 238,950     | 0.05  | +34k steps; barely moving |
| cf_pp_s999_seed999               | 222,400     | 0.25  | +37k steps; SR 0.15→0.25 ↑ |
| vcf_pp_s42_seed42                | 227,700     | 0.00  | +37k steps; still 0.00   |

### Push (cf_ prefix):
- s42: **0.95**, s123: **0.95**, s999: **0.80** — all near 500k budget, very strong
- Push runs are at ~94-99% of 500k budget. Finishing imminently.

### Slide (cf_ prefix):
- s42: **0.50**, s123: **0.60**, s999: **0.55** — significant improvement since 15:15
- All three improved by 0.15–0.40 SR. Slide is converging well.

### PnP cf_ runs (~222-239k steps):
- s42: **0.00**, s123: **0.05**, s999: **0.25** — s999 making progress, others stuck
- PnP is badly lagging Push/Slide; 100-250k steps behind at same wall time.

---

## vcf_pp_s42 Verifier-Rejection (step=227,700)

- `buffer/cf_verifications_attempted`: **156** (was 134 at 15:15; +22 attempts)
- `buffer/cf_verifications_rejected_no_success`: **156 (100%)** — still 100% rejection
- `buffer/cf_verifications_succeeded`: 0
- `buffer/cf_vlm_calls`: **270** (was 227 at 15:15)
- `buffer/cf_vlm_returned_none`: **270** — all VLM calls returning None (VLM not generating valid proposals)
- `buffer/cf_relabel_count`: 0 — zero counterfactuals ever applied to buffer
- `eval/success_rate`: **0.00** (was 0.10 at 15:15 — ticked back to 0)

Situation unchanged: all 270 VLM calls return None, all 156 verification attempts rejected. The VLM is failing to produce any CF proposals for PnP. SR is 0.

---

## Oracle-CF 1M PnP (delta from 15:15)

| Run                                    | global_step | SR   | State    |
|----------------------------------------|-------------|------|----------|
| path_c_kill_ocf_pnp_1m_s42_seed42      | 1,000,000   | 0.30 | finished |
| path_c_kill_ocf_pnp_1m_s123_seed123    | 1,000,000   | 0.90 | finished |
| **path_c_kill_ocf_pnp_1m_s999_seed999**| **500,700** | **0.50** | **running** |

Delta s999: 349k → 500.7k (+151k steps, ~30 min wall time). SR improved 0.40 → 0.50.
Progress: 50.1% of 1M. At current pace (~302k/hr), ETA to completion: ~3.3 hrs (~19:00 PDT, earlier than previous 21:00 estimate).

---

## Local Processes (confirmed running)

```
226889  python train.py oracle_cf.yaml  FetchPickAndPlace-v4  seed=999  (s999 1M run, 1M budget)
232552  python train.py oracle_cf.yaml  FetchSlide-v4  seed=42   (250k budget)
232584  python train.py oracle_cf.yaml  FetchSlide-v4  seed=123  (250k budget)
232585  python train.py oracle_cf.yaml  FetchSlide-v4  seed=999  (250k budget)
```

Local Slide Oracle-CF runs (232552/84/85) not yet visible in W&B query — may be logging under different run names or not yet reached first eval interval.

---

## Key Developments Since 15:15

1. **Push nearing completion**: All 3 seeds at ~94-99% of 500k budget with SR 0.80-0.95. Will finish in the next ~30 min.
2. **Slide SR surge**: cf_sld_s123 jumped 0.20→0.60 (+40pp). All Slide seeds now 0.50-0.60.
3. **Oracle s999 accelerating**: Step pace increased to ~302k/hr (was ~242k/30min earlier). New ETA ~19:00 PDT. SR=0.50 at 500k steps.
4. **vcf_pp_s42 fully broken**: All 270 VLM calls returning None. Zero usable CFs. Needs VLM pipeline fix.
5. **PnP cf_ runs**: s999 showing signs of life (0.25 SR), but s42/s123 near-zero.
