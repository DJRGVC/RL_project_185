# Path C overnight run status

_Updated 2026-05-12 22:25:00  • orchestrator started 2026-05-12T05:16:30.667169Z_


## Phase 1 (KILL: HER vs HER+Oracle-CF on 5070Ti)

- pending  : 0
- running  : 3
- done     : 15
- failed   : 0

| run_id | status | started | duration | exit_code |
|---|---|---|---|---|
| her_pp_s42 | done | 2026-05-12T05:16:30.667415Z | 1815s | 0 |
| her_pp_s123 | done | 2026-05-12T05:16:30.667742Z | 1815s | 0 |
| her_pp_s999 | done | 2026-05-12T05:16:30.667986Z | 1815s | 0 |
| her_push_s42 | done | 2026-05-12T05:46:45.801838Z | 1815s | 0 |
| her_push_s123 | done | 2026-05-12T05:46:45.802257Z | 1815s | 0 |
| her_push_s999 | done | 2026-05-12T05:46:45.802540Z | 1800s | 0 |
| her_sld_s42 | done | 2026-05-12T06:16:45.878831Z | 1800s | 0 |
| her_sld_s123 | done | 2026-05-12T06:17:00.885636Z | 1800s | 0 |
| her_sld_s999 | done | 2026-05-12T06:17:00.886087Z | 1800s | 0 |
| ocf_pp_s42 | done | 2026-05-12T06:46:45.955738Z | 1800s | 0 |
| ocf_pp_s123 | done | 2026-05-12T06:47:00.989990Z | 1800s | 0 |
| ocf_pp_s999 | done | 2026-05-12T06:47:00.990354Z | 1800s | 0 |
| ocf_push_s42 | done | 2026-05-12T07:16:46.026205Z | 1800s | 0 |
| ocf_push_s123 | done | 2026-05-12T07:17:01.033119Z | 1815s | 0 |
| ocf_push_s999 | done | 2026-05-12T07:17:01.033503Z | 1815s | 0 |
| ocf_sld_s42 | running | 2026-05-13T04:23:30.549854Z | - | - |
| ocf_sld_s123 | running | 2026-05-13T04:23:30.550344Z | - | - |
| ocf_sld_s999 | running | 2026-05-13T04:23:30.553239Z | - | - |

## Phase 2 (VLM-CF + Verified-CF on Modal A10G)

- pending  : 0
- running  : 18
- done     : 0
- failed   : 0

| run_id | status | started |
|---|---|---|
| vcf_pp_s42 | running | 2026-05-12T17:33:16.530449Z |
| vcf_pp_s123 | running | 2026-05-12T17:33:36.611078Z |
| vcf_pp_s999 | running | 2026-05-12T17:33:56.743272Z |
| vcf_push_s42 | running | 2026-05-12T17:34:16.673845Z |
| vcf_push_s123 | running | 2026-05-12T17:34:36.404417Z |
| vcf_push_s999 | running | 2026-05-12T17:34:56.185586Z |
| vcf_sld_s42 | running | 2026-05-12T17:36:07.866282Z |
| vcf_sld_s123 | running | 2026-05-12T17:36:27.599414Z |
| vcf_sld_s999 | running | 2026-05-12T17:36:49.633809Z |
| vrcf_pp_s42 | running | 2026-05-12T17:37:09.315008Z |
| vrcf_pp_s123 | running | 2026-05-12T17:37:29.746202Z |
| vrcf_pp_s999 | running | 2026-05-12T17:37:49.476095Z |
| vrcf_push_s42 | running | 2026-05-12T17:39:01.156984Z |
| vrcf_push_s123 | running | 2026-05-12T17:39:21.138457Z |
| vrcf_push_s999 | running | 2026-05-12T17:39:40.819786Z |
| vrcf_sld_s42 | running | 2026-05-12T17:40:00.600964Z |
| vrcf_sld_s123 | running | 2026-05-12T17:40:20.532021Z |
| vrcf_sld_s999 | running | 2026-05-12T17:40:40.162880Z |

## Logs

- Orchestrator events: /home/daniel-grant/.local/state/path_c_orchestrator.log
- Per-run train.log : /home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/logs/<run_name>/train.log
- W&B: https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_overnight_2026-05-11
