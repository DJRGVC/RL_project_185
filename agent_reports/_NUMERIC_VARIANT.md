# Numeric-Context Prompt Variants for VLM-CF

**Date:** 2026-05-12
**Branch:** `agent/pathc-lead`
**Agent:** code-agent (Opus 4.7)
**Status:** Implemented + smoke-tested. **Not yet trained.**

## Motivation

The existing `achieved_goal` and `achieved_goal_blind` prompt templates feed the
VLM 5 image keyframes plus a frame-to-timestep map and (for the knows-goal
variant) the desired_goal coordinates. Empirically, VLMs reason far better
about geometric tasks when given *numerical state* alongside images: image
tokens give them coarse spatial context, but the numerical table lets them
quantify where the block actually went versus where it should have gone.

The current `achieved_goal` arm has shown the well-documented "teleport
collapse" failure mode (CF predictions clustered around `desired_goal`), and
the `achieved_goal_blind` arm corrects this at the prompt level but throws
away geometric grounding entirely. **Numerical trajectory context is the
natural third axis:** does adding mm-precise block xyz + gripper ee_xyz help
the VLM produce more useful counterfactual goals?

## What was added

Two new prompt variants in `src/vlm/counterfactual.py`:

| Variant | Knows desired_goal? | Numerical table? |
|---|---|---|
| `achieved_goal` (existing) | yes | no |
| `achieved_goal_blind` (existing) | no | no |
| **`achieved_goal_numeric`** (new) | yes | **yes** |
| **`achieved_goal_blind_numeric`** (new) | no | **yes** |

Both new templates render a markdown table:

```
| Frame | Step | Block xyz (achieved_goal) | Gripper ee_xyz       |
|-------|------|---------------------------|----------------------|
| 0     | 0    | [1.460, 0.833, 0.425]     | [1.342, 0.749, 0.535]|
| 1     | 12   | [1.460, 0.833, 0.425]     | [1.385, 0.703, 0.632]|
| 2     | 24   | [1.460, 0.833, 0.425]     | [1.325, 0.765, 0.712]|
| 3     | 37   | [1.460, 0.833, 0.425]     | [1.273, 0.846, 0.704]|
| 4     | 49   | [1.460, 0.833, 0.425]     | [1.348, 0.858, 0.581]|
```

This sample (from the FetchPickAndPlace smoke run) shows exactly the kind of
signal the VLM otherwise has to infer from pixels alone: the block xyz never
moves (the robot never made contact), while the gripper drifts around in 3D.
A purely visual prompt could miss this; a numerical prompt makes it unmissable.

The 2x2 ablation matrix the four variants give us is the headline
contribution of this change. It separately tests:

- **Axis 1 (image-only vs image+numeric).** Does feeding mm-precise positions
  improve CF quality?
- **Axis 2 (knows-goal vs blind).** Does withholding desired_goal still
  eliminate teleport collapse when the VLM has numerical context to work
  with, or does the numeric table re-introduce a different failure mode?

## Files changed

1. `src/vlm/counterfactual.py`
   - Added `ACHIEVED_GOAL_NUMERIC_PROMPT` and `ACHIEVED_GOAL_BLIND_NUMERIC_PROMPT`.
   - Registered both in `PROMPT_TEMPLATES`.
   - Added `NUMERIC_VARIANTS` and `BLIND_VARIANTS` frozensets so the buffer
     and the localizer stay in sync.
   - Added `_build_traj_table(timestep_indices, achieved_goals_at_keyframes,
     ee_positions_at_keyframes)` helper.
   - Extended `CounterfactualLocalizer.query()` with two new optional kwargs:
     `achieved_goals_at_keyframes`, `ee_positions_at_keyframes`. Only
     consumed when `variant in NUMERIC_VARIANTS`.
   - Extended the closure returned by `make_counterfactual_fn` with an
     `ee_positions: Optional[np.ndarray]` kwarg and `**_unused_kwargs`. It
     slices per-step achieved_goals / ee_positions at the keyframe indices
     before calling `query()`. Backwards-compatible: old callers passing only
     `(achieved_goals, desired_goal, keyframes)` still work — the table just
     gets `[n/a, n/a, n/a]` rows for missing data (and old variants don't
     consume the table at all).

2. `src/buffers/counterfactual_buffer.py`
   - `_query_vlm` now extracts `ee_positions = obs[:, 0:3]` (Fetch convention,
     verified by reading `src/envs/wrappers.py`) and forwards it to the VLM
     callback for the `vlm` input kind.

3. `train.py`
   - The `cf_fn_verified` wrapper now accepts and forwards `ee_positions`
     so the verified-CF stack remains compatible with the numeric variants
     (currently only used by `vlm_cf_*` configs; verified-CF uses variant
     `all` which ignores numeric data).

4. `configs/vlm_cf_numeric.yaml` (new) — knows-goal + numeric.
5. `configs/vlm_cf_blind_numeric.yaml` (new) — blind + numeric.
6. `tests/test_counterfactual_prompts.py` (new, 10 tests).
7. `agent_reports/_numeric_smoke.py` (this smoke harness).

## Smoke test results

`configs/vlm_cf_numeric.yaml`, 200 steps, FetchPickAndPlace-v4, Anthropic
client monkey-patched to return a canned non-teleport CF
(`[1.25, 0.78, 0.48]`, conf 0.9):

- 4 failed episodes -> 4 VLM calls (cf_call_interval=1 to exercise the path).
- The first rendered prompt (truncated):
  - Contains the markdown table header `| Frame | Step | Block xyz ...`.
  - Block xyz column populated from `achieved_goals[ts_indices[i]]`.
  - Gripper ee_xyz column populated from `obs[ts_indices[i], 0:3]`.
  - `desired_goal = [...]` line present (knows-goal variant).
  - Failure frame index injected correctly (~51% -> Frame 2 of 5).
- CFs accepted into the buffer (passed teleport gate at 5cm).
- `buffer/cf_*` metrics logged normally (no regressions).

`configs/vlm_cf_blind_numeric.yaml`, same setup:

- 4 VLM calls.
- Table present, `desired_goal =` line absent, "withheld" caveat present.

## Test results

All 10 new prompt tests pass. All 32 existing CF buffer tests still pass.
All 11 verified-CF wiring tests still pass.

```
$ python tests/test_counterfactual_prompts.py
... 10 passed, 0 failed
$ python tests/test_counterfactual_buffer.py
... 32 passed, 0 failed
$ python tests/test_verified_cf_wiring.py
... 11 passed, 0 failed
```

## What is NOT in this change

- **No training run was launched.** Existing in-flight runs (Modal Phase 2 +
  local Oracle-CF Slide) are untouched.
- **Existing `achieved_goal` / `achieved_goal_blind` prompts are unchanged.**
  This is deliberate: keep them frozen for clean ablation against the
  p-sweep auto-launcher results.
- **`configs/vlm_cf.yaml` and `vlm_cf_blind.yaml` are unchanged.** The
  numeric variants live in their own configs.

## Recommended next wave (post-p-sweep)

Run 3 seeds per cell of the 2x2 matrix on FetchPickAndPlace and FetchPush:

| | knows desired_goal | blind |
|---|---|---|
| visual only | `vlm_cf.yaml` (already running) | `vlm_cf_blind.yaml` (already running) |
| visual + numeric | `vlm_cf_numeric.yaml` (NEW) | `vlm_cf_blind_numeric.yaml` (NEW) |

Headline metrics to compare:

1. `buffer/cf_corrective_pos_to_desired_dist` (teleport-collapse signal —
   should rise for numeric variants if the numerical table grounds the VLM
   in trajectory geometry instead of the goal coords).
2. `buffer/cf_corrective_pos_to_achieved_dist` (stay-the-course signal —
   should stay > 5cm to indicate the VLM is proposing something different
   from what already happened).
3. `eval/success_rate` learning curves (the headline number).
4. C1v2-style offline judge: re-score the rendered prompts with a Sonnet 4.5
   judge under matched seeds, plot plausibility / goal_progress / specificity.

If `achieved_goal_numeric` beats `achieved_goal` on (3) and reduces (1), the
paper has a clean "numerical context matters" finding that is independent of
the existing blind-vs-non-blind result. If `achieved_goal_blind_numeric`
matches or beats `achieved_goal_blind` on (3) without re-introducing teleport
collapse, that gives us a second independent win: "you can be blind to the
goal and still produce useful CFs, provided you have numerical context."

## Risks / caveats

- The table consumes ~150-200 extra tokens per VLM call; at
  `cf_call_interval=16` this is a few dollars per training run, not a budget
  concern.
- The VLM may over-anchor on the numerical values and ignore the images.
  Mitigation: the prompt explicitly instructs "Use BOTH the images and the
  numerical table above"; if we see degraded image use, swap the order
  (images first then table) or remove the gripper column.
- The ee_pos slice (`obs[:, 0:3]`) is the Fetch convention. For FetchReach,
  `achieved_goal == gripper_pos`, so the block and gripper columns will be
  identical; this is correct and the VLM will see it.
