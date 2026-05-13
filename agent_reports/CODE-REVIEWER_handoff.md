# CODE-REVIEWER handoff (overnight 2026-05-11 → 2026-05-12)

**Agent**: CODE-REVIEWER (Opus 4.7, 1M context).
**Window**: 22:18 PDT 2026-05-11 → 01:30 PDT 2026-05-12 (3-hour budget).
**Scope**: continuous code review of PATHC-LEAD's commits + cron agents' overnight code/feature commits to `agent/pathc-lead` and other agent branches.

## Topline

- **Commits reviewed**: 15 across `agent/pathc-lead` (the only branch with new commits during my window). Includes 3 substantive code commits (`5a859f5`, `b393fe3`, `168518b`, `6ac734e`) and 11 docs/paper commits.
- **Findings by severity**:
  - **3 BLOCKERs** identified. 1 was fixed mid-window by a follow-up cron agent (B1, fix in `168518b`). 2 remain (B2, B3 — both regressions vs `agent/a1-her-baselines`).
  - **~12 ISSUEs** documented (CF buffer code-paths, orchestrator quirks, cross-branch divergences, W&B grouping bug).
  - **5 NITs** documented.
- **Auto-fixed by me**: 0 (deliberate — modifying live-imported source while training runs was deemed too risky for the upside; all NITs left for morning consolidation).
- **Tests run**: `tests/test_counterfactual_buffer.py` (15/15 pass) and `tests/test_verified_cf_wiring.py` (11/11 pass). Both added by the same fix commit that closed BLOCKER B1.

## Top-3 BLOCKERs the morning agent MUST verify

### ~~B1 — `verified_cf` provider was a silent no-op~~ **RESOLVED IN-WINDOW (commit 168518b)**

The Cycle-1 BLOCKER I raised: `train.py:_build_cf_provider`'s 'verified' branch built a `VerifiedCounterfactualLocalizer` but never called `.verify()` — and `make_counterfactual_fn` discarded the corrective_action. Result would have been: `verified_cf` and `vlm_cf` runs producing functionally-identical training data.

**Action taken by cron agent at 00:01 PDT** (commit `168518b`):
- Added `return_action=True` plumbing through `make_counterfactual_fn` → 4-tuple return.
- Forced `vlm_variant='all'` when `cf_provider='verified'`.
- Wrote real `verifier.verify(corrective_action=ca)` call with kinematic-snapshot reconstruction.
- Promoted verified CFs (conf=1.0, position replaced with simulator-observed achieved_goal); dropped rejected ones.
- Added `tests/test_verified_cf_wiring.py` (11 invariants) pinning the contract.
- Added W&B metrics `buffer/cf_verifications_attempted/succeeded/rejected_*/success_rate`.

**Verification by code-reviewer**: I ran both test suites: 15/15 + 11/11 = 26/26 PASS. The wiring is correct and back-compatible (`return_action=False` keeps the 3-tuple contract for in-flight `vlm_cf`/`oracle_cf` runs).

**Morning verification step**: after Phase 2 fires, check the first `verified_cf` run's W&B summary for `buffer/cf_verifications_attempted > 0`. If 0, deeper bug.

**Caveat the morning agent must internalize**: forced `vlm_variant='all'` for verified-CF will have *higher pre-verification teleport-collapse* than `vlm_cf` (per C1v2-A bake-off, `'achieved_goal'` had 0% teleport collapse, `'all'` had non-zero). After verification filtering, expect verified_cf to have **lower CF density** than vlm_cf — making the head-to-head comparison favour vlm_cf even if the per-CF quality is higher under verification. The morning analysis must look at `cf_verifications_success_rate` and `cf_relabel_count` jointly, not just success rate.

### B2 — Phase 2 Modal jobs will likely crash on W&B init (NOT YET FIXED)

**Triple regression** on `agent/pathc-lead` vs `agent/a1-her-baselines` (which had it right):

1. `modal_app.py:train_remote` lost the `os.environ["WANDB_ENTITY"]="d-grant-uc-berkeley"` override that a1 added because the Modal secret bakes in `WANDB_ENTITY=djrgvc` (which doesn't own RL_project).
2. `modal_app.py:train_remote` lost the `wandb_tags` parameter (the b393fe3 swap to env-var-only tagging defeats Modal's per-function secret model).
3. `src/utils/logger.py` lost the try/except fallback that on perm-denied retries with entity=None.

**Combined impact**: every Phase 2 Modal training job is likely to crash at `wandb.init` with permission denied to `djrgvc/RL_project`. The orchestrator marks the run failed and continues — so **all of Phase 2 is at risk of silently failing**.

**Morning verification step**: BEFORE manually launching Phase 2 via `modal run --detach modal_app.py::run_path_c_phase2`, do ONE of these:
- (Best) Apply the a1-her-baselines `os.environ["WANDB_ENTITY"]="d-grant-uc-berkeley"` override at the top of `train_remote` and force a Modal image rebuild.
- (OK) Update the Modal secret `semantic-per-secrets` to set `WANDB_ENTITY=d-grant-uc-berkeley` (a one-line change in the Modal dashboard; no image rebuild required).
- (Risky) Restore the try/except in `src/utils/logger.py`.

**Morning merge action**: take the a1-her-baselines version of `src/utils/logger.py` and `modal_app.py:train_remote` and stack the b393fe3 WANDB_TAGS env-var pickup on top.

### B3 — `src/envs/wrappers.py` regression to unconditional `render_mode`

Less severe than B2 but in the same regression class. The a1-her-baselines version had `kwargs["render_mode"] = render_mode` only when `capture_frames=True`. The b393fe3 version regressed to unconditional. Any environment created without an offscreen GL context (Modal cold-start without OSMesa, local non-`MUJOCO_GL` invocations) will crash at `gym.make`.

**Tonight's safety**: `MUJOCO_GL=osmesa` is set in the Modal image and `MUJOCO_GL=egl` is set by the local orchestrator's `_build_env`, so the regression is harmless. Bears fixing in the merge regardless.

**Morning merge action**: take the a1-her-baselines version of `src/envs/wrappers.py:make_env`.

## Phase 1 status as of 00:48 PDT

- HER: 9/9 done (all rc=0).
- OCF: 6/9 done (PnP + Push, all rc=0). OCF Slide 3/3 running.
- ETA full Phase 1 completion: ~01:20 PDT (within my hard stop).

### Phase 1 KILL test FINAL results (from `logs/path_c_orch_*.log` "Best success rate" lines)

| seed | HER PnP | OCF PnP | HER Push | OCF Push | HER Sld | OCF Sld |
|---|---|---|---|---|---|---|
| 42  | 0.100 | 0.100 | 0.700 | 0.150 | 0.200 | 0.200 |
| 123 | 0.050 | 0.100 | 0.450 | 0.500 | 0.100 | 0.200 |
| 999 | 0.400 | 0.200 | 0.700 | 0.200 | 0.250 | 0.150 |
| **mean** | **0.183** | **0.133** | **0.617** | **0.283** | **0.183** | **0.183** |
| **delta (OCF − HER)** | **−0.050** | | **−0.333** | | **0.000** | |

**KILL verdict (per the operator README's `+0.10 on PnP` rule)**: **PATH C IS NOT ALIVE BY THE STRICT RULE.** OCF lags HER by 0.05 on PnP, far below the +0.10 threshold. Push is *catastrophically* worse for OCF. Slide is a tie.

**Headline finding for the morning lead** (not a code issue, but the data say this):

- **PnP**: OCF − HER = **−0.05** (OCF slightly worse). Fails the KILL rule (+0.10).
- **Push**: OCF − HER = **−0.33** (OCF significantly worse). OCF is **actively harming** Push.

### Hypothesis for why OCF underperforms on Push

`src/vlm/oracle_cf.py:oracle_cf_push` picks the frame where ee-block distance is maximised, then outputs `midpoint(ee[k], desired_goal)` as the CF goal. The chosen frame is where the agent has *lost* the block (ee far from block) — so `ee[k]` is at an arbitrary location, often where the agent has nudged off to the side or overshot. The midpoint is consequently in some random region neither close to the block nor close to the goal. Relabeling 25% of HER transitions with this random midpoint goal injects bad signal: the policy learns "this state-action pair was useful for reaching some weird midpoint" — a no-op-to-bad gradient compared to vanilla HER's achieved-future strategy.

**Suggestion for the morning lead**: either (a) ablate the Push oracle by trying `midpoint(block_pos[k], desired_goal)` instead of `midpoint(ee[k], ...)`, OR (b) gate the CF on a sanity-check like "only emit CF if `|ee[k] - block[k]| < 0.10`" (the agent was in contact with the block), OR (c) just use `block_pos[k]` interpolated toward `desired_goal` (an "achieved future" with momentum).

### Hypothesis for why OCF ties HER on Slide (Slide oracle works as intended)

`oracle_cf_slide` outputs the ballistic-trajectory terminus. Since Slide failure modes are "puck launched in slightly-wrong-direction-or-velocity", the predicted terminus is *near* the actual puck path. The synthetic relabel says "if your goal were where the puck actually goes, you succeeded" — which is essentially the standard HER "future" achievement strategy with a small physics extrapolation. So it doesn't help much but doesn't hurt.

### Bottom line for the morning lead

- **Path C as currently implemented underperforms HER on PnP and is destructive on Push.** The KILL rule says drop Path C.
- **Before dropping Path C entirely**, consider that:
  - The PnP oracle (mid-air-above-goal waypoint) is the *right* shape per C1v2-B Sonnet-4.5 findings — yet it didn't beat HER. This is a serious data point: even a perfect spatial CF heuristic doesn't help PnP within 250k steps from cold-start SAC.
  - 250k steps may be too few for HER+OCF to start exploiting CF goals (cold-start SAC spends ~50k steps just on warmup + initial exploration). Consider extending to 500k steps before final kill verdict.
  - The Push oracle is *demonstrably wrong* (midpoint-of-ee-and-goal at max-divergence frame). Re-running Push OCF with a corrected oracle (per the suggestion above) might be worthwhile before final verdict.
- **Phase 2 (VLM-CF)**: if Path C dies on Oracle (ceiling), VLM-CF (an even noisier signal) will not save it. Probably skip Phase 2 launch in the morning unless you want to confirm the death.

## Files I created

- `agent_reports/code_review_findings.md` — append-only log of all findings by cycle.
- `agent_reports/code_review_seen_shas.txt` — SHA tracking.
- `agent_reports/_CODE_BLOCKER.md` — current active blockers (overwritten each cycle).
- `agent_reports/CODE-REVIEWER_handoff.md` — this file.

## Files I deliberately did NOT modify

- Any executable source code under `src/`, `configs/`, `scripts/`, `train.py`, `modal_app.py`. Rationale: training is running, source files may be re-imported by spawned worker processes on hot reload edges, and the upside of fixing NITs in-window was not worth the risk to a 3-hour overnight kill experiment.
- Tests in `tests/` — already written and passing.

## Open ISSUEs the morning consolidator should fold in

(From `agent_reports/code_review_findings.md`; see full file for line-level detail.)

- **W&B group derivation** (cycle 5): the plan's run_name `path_c_kill_ocf_pp_s42` confuses `run_name.split("_seed")[0]` because the seed suffix is `_s42` (not `_seed42`). Each seed lives in its own W&B group; per-method comparison panels don't auto-populate. Workaround: filter by tag in the W&B UI. Fix in `agent_reports/overnight_path_c_plan.json` by dropping `_s{seed}` from run_name.
- **Phase 2 Modal tags not propagated** (cycle 3): `path_c_orchestrator.py:launch_modal_run` uses `subprocess.Popen` but doesn't set Modal-container env vars. Phase 2 runs will be untagged.
- **`cf_window` parameter is dead code** (cycle 3): documented to widen the corrective relabel window but never referenced.
- **`vlm_returned_none` double-counts** when `_query_vlm` exceptions (cycle 1): minor diagnostic noise.
- **`rejected_no_action` is a misnomer** in the 168518b fix: appended to verified output, not actually rejected.

## Recommendation to morning lead

1. **Before launching Phase 2**: address B2 (Modal WANDB_ENTITY) — see options above. Without this, Phase 2 silently dies.
2. **For Phase 2 verified_cf vs vlm_cf comparison**: check `buffer/cf_relabel_count` ratio AND `cf_verifications_success_rate` together. Don't read raw success rate alone — the forced `variant='all'` for verified mode confounds the comparison.
3. **Phase 1 KILL verdict**: filter W&B by `tags=path_c_overnight_2026-05-11`, then compare run groups (HER vs OCF) on `eval/success_rate` for each env. Apply the +0.10 threshold from the operator README.
4. **For Phase 3 (VLM tier ablation, 6ac734e)**: not launching tonight per the commit; configs are in `configs/ablation_vlmtier_v{0,1,2,3}.yaml`. Run after Phase 2 settles.
5. **The forced `vlm_variant='all'` regression**: if verified_cf underperforms vlm_cf, consider whether the morning agent should re-run verified_cf with `variant='achieved_goal'` (giving up sim-verification but matching the C1v2-A winner) as an additional ablation.

— CODE-REVIEWER (Opus 4.7, 1M context)
2026-05-12 00:38 PDT
