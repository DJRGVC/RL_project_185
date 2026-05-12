# EMERGENCY-FIX-AGENT handoff (2026-05-12)

**Agent**: EMERGENCY-FIX (Opus 4.7, 1M context). Budget: 45 minutes. Branch: `agent/pathc-lead`.

## TL;DR

Two CODE-REVIEWER-flagged BLOCKERs are fixed in one commit (`ccb63d4`):

1. **B-PUSH design bug** in `src/vlm/oracle_cf.py::oracle_cf_push` — CF midpoint switched from `(ee[k] + goal) / 2` to `(block_pos[k] + goal) / 2`. The original placed CFs in arbitrary workspace regions whenever the agent had lost the block.
2. **B2 Modal WANDB_ENTITY regression** in `modal_app.py::train_remote` — re-added the `os.environ["WANDB_ENTITY"]="d-grant-uc-berkeley"` (and `WANDB_PROJECT`) override before any wandb import. Mirrors the a1-her-baselines fix pattern. Phase 2 jobs will no longer silently fail at `wandb.init`.

A corrected-Push rerun is queued (not launched) via `scripts/run_corrected_push_ocf.sh` and a `phase1_rerun_push` block appended to `agent_reports/overnight_path_c_plan.json`.

## What was fixed and committed

### Commit `ccb63d4` (HEAD on `agent/pathc-lead`)

> "Path C: fix oracle_cf_push midpoint bug + Modal WANDB_ENTITY override"

- `src/vlm/oracle_cf.py`: oracle_cf_push uses `obj[k]` (block_pos) instead of `ee[k]` as the midpoint anchor. Updated docstring to explain the design rationale and reference the failed 2026-05-11 KILL data.
- `modal_app.py`: train_remote sets `WANDB_PROJECT=RL_project` and `WANDB_ENTITY=d-grant-uc-berkeley` at the top of the function (before `from train import ...` triggers logger.py / wandb).

### Verification

- 26/26 existing CF tests pass: `tests/test_counterfactual_buffer.py` (15/15) + `tests/test_verified_cf_wiring.py` (11/11).
- Unit-level smoke test of `oracle_cf_push` via `make_oracle_cf_fn('FetchPush-v4')`: confirms the CF position is exactly `0.5 * (block_pos[k] + goal)` and ~21 cm away from the previous buggy `0.5 * (ee[k] + goal)` value on a synthetic adversarial trajectory.
- Modal app syntax check + ordering verified: `WANDB_ENTITY` override appears before `from train import ...` so logger.py reads the corrected entity.

## What was queued but NOT launched

- `scripts/run_corrected_push_ocf.sh` — runs 3 seeds (42/123/999) of `configs/oracle_cf.yaml` on `FetchPush-v4` at 250k steps sequentially. W&B tags: `path_c_kill_2026-05-11,oracle_cf_pushfix`. Run names: `path_c_kill_ocf_push_fix_s{42,123,999}`. DRY_RUN verified.
- `agent_reports/overnight_path_c_plan.json::phase1_rerun_push` — JSON entry mirroring the runs above for plan completeness. NOTE: `scripts/path_c_orchestrator.py` currently only iterates `phase1_kill` and `phase2_vlm` — the orchestrator will NOT auto-pick this. Morning agent must invoke the shell script directly OR teach the orchestrator about the new phase.
- DO NOT launch until the in-flight Phase 1 ocf_sld batch (PIDs 117601/117602/117603 as of 01:21 PDT) completes. Each in-flight run is ~30 min @ 250k steps.

## Expected verdict change

Original Phase 1 KILL final numbers (per CODE-REVIEWER handoff):

| env | HER mean | OCF mean | Δ (OCF − HER) |
|---|---|---|---|
| PickAndPlace | 0.183 | 0.133 | −0.05 |
| Push | 0.617 | 0.283 | **−0.33** |
| Slide | 0.183 | 0.183 |  0.00 |

Once `oracle_cf_push_fix` lands, the **Push Δ should jump significantly** — possibly to a tie or modestly positive — because the CF is no longer a workspace-random goal. Predicted post-fix range (informed guess, not measured):
- If the corrected CF behaves like a "block-future" goal with momentum, expect Push OCF in the **0.50 - 0.65** range, i.e. Δ ≈ −0.10 to +0.05.
- A clean +0.10 beat is unlikely from this fix alone because (a) the CF density is unchanged (still p_counterfactual=0.25), (b) 250k steps is short, and (c) the corrective signal is now correct-but-not-strong.

**Headline implication for the morning agent**: even after the Push fix, the +0.10 KILL rule will likely fail on **all three envs**. The fix changes Push from "actively harmful" to "neutral", which is informative but not lifesaving for Path C.

## Should the morning agent re-evaluate KILL on PnP + Slide only?

**Yes — that is the cleanest read of the pre-fix data:**

- The PnP and Slide oracles were correct as written; their numbers are valid.
- PnP Δ = −0.05 (not bad signal — just below threshold), Slide Δ = 0.00 (tie).
- The Push Δ = −0.33 came from a **demonstrably wrong oracle**, so it's not a valid datum for the KILL rule. Including it in the average drags the verdict toward "Path C is actively destructive" when the truth is "Path C is null".

**Recommendation**: report the KILL verdict TWO ways in the morning writeup:
1. **Strict (pre-fix data, all three envs)**: Path C dies. Δ averaged across envs ≈ −0.13. Plot Push as buggy.
2. **Corrected (PnP + Slide only, OR pre-fix PnP/Slide + post-fix Push)**: Path C is null but not destructive. Mean Δ ≈ −0.025. Push fix run is the load-bearing decision input.

If the corrected Push run lands at Δ ≈ 0.00 (tie), the strongest claim the paper can make is "Oracle-CF gives **no net improvement** over vanilla HER at 250k steps from cold-start SAC, even when the oracle is correctly designed". That's still a publishable negative result; combined with the C1v2-B Sonnet 4.5 "right-shape" finding, it's a tight loop closure.

If the corrected Push run lands at Δ ≥ +0.05 (modest beat), the +0.10 strict rule is failed but the **direction is right**. Consider extending to 500k steps before the final kill verdict, per CODE-REVIEWER's earlier suggestion.

## Files modified (this session)

- `src/vlm/oracle_cf.py` — fixed `oracle_cf_push` midpoint.
- `modal_app.py` — fixed B2 WANDB_ENTITY override.
- `scripts/run_corrected_push_ocf.sh` — NEW, manual rerun script.
- `agent_reports/overnight_path_c_plan.json` — appended `phase1_rerun_push` block.
- `agent_reports/_EMERGENCY_FIX_HANDOFF.md` — this file.

## Files deliberately NOT touched

- `src/utils/logger.py` — B2 mitigated by the os.environ override at the top of `train_remote`; restoring the a1 try/except fallback is recommended but not urgent and would require an image rebuild anyway. CODE-REVIEWER flagged this for the morning merge.
- `src/envs/wrappers.py` (B3 unconditional `render_mode`) — harmless under current Modal/local GL setup per CODE-REVIEWER's analysis. Morning merge can take the a1 version.
- In-flight Phase 1 ocf_sld processes (PIDs 117601/117602/117603) — DID NOT TOUCH. The `oracle_cf.py` edit is safe because (a) those processes already imported the function object at process start, and (b) they only call `oracle_cf_slide`, not `oracle_cf_push`.
- Existing `path_c_orchestrator.py` — the new `phase1_rerun_push` is a JSON addition only; the orchestrator code is untouched, so the in-flight orchestrator (PID 117592) cannot be confused by it.

## What the morning agent should do first

1. Confirm Phase 1 ocf_sld completed cleanly (`ls logs/path_c_kill_ocf_sld_s*/train.log` has rc=0 markers).
2. Pull `agent/pathc-lead`, verify HEAD is `ccb63d4`.
3. Decide whether to launch the Push rerun manually (`bash scripts/run_corrected_push_ocf.sh`) — 90 min wallclock if GPU is free.
4. If Phase 2 has already fired via the 03:00 watchdog: check W&B for the first `path_c_vlm_*` run's `wandb.init` line. If `entity=d-grant-uc-berkeley` and the run exists in the UI: B2 fix worked. If not: image-rebuild may have lagged the launch — restart the affected Modal jobs.
5. Re-evaluate the KILL verdict per the "two-way report" recommendation above.

— EMERGENCY-FIX-AGENT (Opus 4.7, 1M context)
2026-05-12 PDT
