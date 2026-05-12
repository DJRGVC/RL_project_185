# `achieved_goal_blind` prompt variant + CF deviation logging

**Branch**: `agent/pathc-lead`
**Date**: 2026-05-12 (Opus 4.7, code-only, no training launched)
**Status**: code shipped, 32/32 unit tests pass, 200-step CPU smoke OK
(4 real Anthropic API calls fired in the smoke run, no crashes).

## Motivation

`ACHIEVED_GOAL_PROMPT` (the variant `vlm_cf.yaml` was running in production)
literally writes `desired_goal = [x, y, z]` into the prompt body. Across the
C1v2 bake-off and the Phase 2 attempts we kept seeing the same failure
signature: the VLM regurgitates the goal coords as `corrective_position`,
the 5 cm teleport gate (`reject_teleport_radius_m=0.05`) drops the CF, and
the buffer falls back to vanilla HER for that episode — so the VLM call is
wasted budget. The structural cause is the prompt: if you hand the answer
to the model, the model gives it back.

The **`achieved_goal_blind`** variant removes the `desired_goal = ...` line
from the prompt entirely. The VLM still gets:

- the qualitative task description ("push a block to the target"),
- the workspace bound box (so it knows the legal x/y/z ranges),
- the 5 keyframes with frame-to-timestep mapping,
- the `failure_frame_index` identifier,

and is asked: *"based on the trajectory in the keyframes, what 3D position
should the object have reached at this frame to make progress toward the
(unspecified) goal?"* The proposal must therefore be inferred from
visual evidence alone, which kills the lazy-regurgitation failure mode
at the source rather than gating it after the fact.

## What changed

| File                                                 | Change                                                                                                   |
|------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| `src/vlm/counterfactual.py`                          | Added `ACHIEVED_GOAL_BLIND_PROMPT`; registered as `"achieved_goal_blind"` in `PROMPT_TEMPLATES`; updated `_parse` warning set so the new variant is recognised. |
| `configs/vlm_cf_blind.yaml` (new)                    | Copy of `vlm_cf.yaml` with `vlm_variant: achieved_goal_blind`; everything else (provider, model, p, window, interval, gate) identical so the ablation is clean. |
| `src/buffers/counterfactual_buffer.py`               | Added running-mean accumulators (`_cf_dev_sum_to_desired`, `_cf_dev_sum_to_achieved`), counters (`cf_accepted_count`, `cf_in_workspace_count`), Fetch workspace bounds, an `_update_cf_deviation_stats` helper, a `reset_cf_deviation_stats` method, and a `get_cf_deviation_stats` accessor. Hooked into `finish_episode` after the low-confidence filter so only accepted CFs are counted. |
| `train.py`                                           | After the existing CF-stats / verifier-stats / PER-stats blocks, surface `replay.get_cf_deviation_stats()` keys directly into `cf_metrics` (already namespaced under `buffer/`). |
| `tests/test_counterfactual_buffer.py`                | Added `TestCFDeviationLogging` (6 new tests): empty when no CFs, correct distances for a known CF, in-workspace flag for in/out CFs, running mean over multiple episodes, reset clears the dict, low-confidence CFs are not counted. |

## New W&B keys

(emitted only when at least one CF has been accepted — short-circuits cleanly
otherwise so dashboards don't get NaNs early)

- `buffer/cf_corrective_pos_to_desired_dist` — running mean of
  `||corrective_position - desired_goal||_2`. Small ⇒ teleport collapse.
- `buffer/cf_corrective_pos_to_achieved_dist` — running mean of
  `||corrective_position - achieved_goal_at_failure_frame||_2`. Small ⇒
  the VLM is just suggesting "keep doing what you did" (useless).
- `buffer/cf_corrective_pos_in_workspace` — running mean of the in-Fetch-bounds
  indicator (x∈[1.05,1.55], y∈[0.4,1.1], z∈[0.4,0.85]). Should be ≈1.
- `buffer/cf_accepted_count` — denominator (number of CFs accepted into the
  buffer since training start, or since the last
  `reset_cf_deviation_stats()`).

The productive regime sits in the middle: a CF that is far from
desired_goal (not a teleport) but also far from achieved_at_failure (not a
"stay the course"), and still inside the workspace.

## Verification

```
$ python tests/test_counterfactual_buffer.py
  passed: 32   failed: 0
```

```
$ CUDA_VISIBLE_DEVICES="" python train.py \
    --config configs/vlm_cf_blind.yaml \
    training.total_steps=200 training.warmup_steps=100 \
    training.eval_interval=1000000 training.save_interval=1000000 \
    replay.cf_call_interval=1 logging.use_wandb=false logging.use_tensorboard=false
```

200 steps on FetchPickAndPlace-v4, 4 episodes, 4 Anthropic API calls fired,
training completed cleanly (`Training complete. Best success rate: 0.000`,
which is expected — 200 steps is far below convergence; we only need the
plumbing to be alive).

## Planned use

Tomorrow's ablation slot (after the p-sweep completes): launch
`vlm_cf_blind.yaml` against `vlm_cf.yaml` on `FetchPickAndPlace-v4` and
`FetchSlide-v4`, seeds {0, 1, 2}, same compute budget. The key diagnostic
is the new `buffer/cf_corrective_pos_to_desired_dist` curve: under the
blind prompt we expect a much wider distribution (rather than the
spike-near-zero we see today under `achieved_goal`), which should translate
to a higher rate of CFs surviving the teleport gate and a non-trivial
fraction of CF relabels per episode (whereas `vlm_cf` is currently
degrading to ~vanilla HER on most episodes).

## Out of scope (deliberately)

- `verified_cf` flow: the blind variant emits only `corrective_position`,
  so it can't feed the simulator-verifier (which needs a 4-D action). If
  we want a blind+verified combo we'd add a sibling `ALL_BLIND_PROMPT` and
  route it through the same machinery — leave for after the ablation
  signal lands.
- Bidir / Sharony stacks: untouched; this is a pure `cf_provider: vlm`
  swap.
- `vlm_cf.yaml` itself is left unmodified (in-flight Modal Phase 2
  attempt 5 + local Oracle-CF runs).
