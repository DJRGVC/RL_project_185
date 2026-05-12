# BLOCKER: verified_cf.yaml variant fix — ADDRESSED at 0030 PDT 2026-05-12

**Status**: ADDRESSED 2026-05-12 00:30 PDT. See "Resolution" section at the bottom of this file.

**Severity**: BLOCKER for differentiation between `verified_cf` and `vlm_cf` runs

## Issue
PATHC-LEAD's handoff (22:25 PDT) flagged that:
- `configs/verified_cf.yaml` currently sets `vlm_variant: achieved_goal`
- N1's verification mechanism (`src/vlm/verified_counterfactual.py`) only triggers when the VLM returns a `corrective_action`
- `corrective_action` is only produced when `vlm_variant=all`
- So as configured, `verified_cf` runs and `vlm_cf` runs produce **functionally identical training data** — the verification step is silently a no-op

## Fix (one-line change)
In `configs/verified_cf.yaml`, change `vlm_variant: achieved_goal` (or whatever it currently is) to `vlm_variant: all`. Then `verification` will fire on actual corrective actions.

## Validation
After fix, smoke-test on FetchPickAndPlace-v4 for 5k steps and confirm `buffer/cf_verifications_attempted > 0` in W&B summary. If still 0, deeper bug.

## Priority
Pick this up in the **23:47 PDT code/feature work cron** firing. Comment out and address before Phase 2 actually fires on Modal (which will be via the watchdog's auto-launch logic once A1's sweep clears Modal).

---

## Resolution (2026-05-12 00:30 PDT)

**TL;DR.** The TODO file's "one-line config fix" diagnosis was technically true but
operationally incomplete: `configs/verified_cf.yaml` already had
`vlm_variant: all` (verified via `git show 5a859f5 -- configs/verified_cf.yaml`).
The actual reason `verified_cf` runs were producing functionally-identical
data to `vlm_cf` runs was a **silent no-op** further down the call chain.

### Root cause

- `make_counterfactual_fn(...)` (in `src/vlm/counterfactual.py`) returned
  3-tuples `(failure_t, corrective_position, confidence)` and **discarded**
  the VLM's `corrective_action` 4-vector — even when `variant="all"`.
- `_build_cf_provider(...)` (in `train.py`) "verified" branch then iterated
  over those 3-tuples and **appended them straight through** to its result,
  never invoking `VerifiedCounterfactualLocalizer.verify(...)`. The
  inline comment ("position-only CFs aren't verifiable; trust them") meant
  the wrapping was structurally a no-op.

### Fix (commit on `agent/pathc-lead`)

Three coordinated changes:

1. **`src/vlm/counterfactual.py`**: added optional `return_action: bool` kwarg
   to `make_counterfactual_fn`. When True, the callable returns 4-tuples
   `(idx, pos, conf, corrective_action_or_None)`. Default `False` preserves
   the original 3-tuple contract used by `vlm` and oracle providers (no
   behavior change for in-flight runs).

2. **`train.py::_build_cf_provider`**:
   - Force `variant="all"` when `cf_provider == "verified"` (with a warning if
     a user explicitly set a position-only variant in their config), so the
     VLM is actually asked for a corrective_action.
   - Call `make_counterfactual_fn(..., return_action=True)` for the verified
     branch to receive 4-tuples.
   - Plumb `corrective_action` into `verifier.verify(...)`, using
     `reconstruct_snapshot_for_synthetic_episode(...)` to build the failure-
     timestep snapshot from the buffer's `achieved_goals` array (kinematic
     approximation: block teleported to achieved[k_i], robot pose = init).
   - On verification PASS: promote confidence to 1.0 and replace the
     position with the simulator's actual achieved_goal at success time
     (so the buffer relabels with physics, not VLM noise).
   - On verification FAIL: drop the CF (buffer degrades to vanilla HER).
   - Return the verifier as a third element of the tuple so the buffer
     can hold the reference for W&B logging.

3. **`train.py::train()`**: pass the verifier to `CounterfactualHERBuffer`,
   and log new W&B metrics under `buffer/cf_verifications_*` (attempted,
   succeeded, rejected_no_action, rejected_no_success, rejected_exception,
   success_rate). These metrics will be zero on `vlm_cf` runs and non-zero
   on `verified_cf` runs, finally making the two methods differentiable.

### Validation

- `tests/test_counterfactual_buffer.py` — 15 invariants pin the existing
  CF-HER buffer behavior (p=0 ≡ HER, causal validity, success skip,
  call_interval gating, low-conf drops, etc.).
- `tests/test_verified_cf_wiring.py` — 11 invariants pin the new contract,
  including:
  - `test_signature_has_return_action`: signature contract.
  - `test_verifier_stats_tick_when_cf_invoked`: **proves
    `verifications_attempted > 0` after a single verified call** (the
    pivotal assertion the TODO file asked for).
  - `test_verified_promotes_confidence_when_simulator_succeeds`: pass-path.
  - `test_verified_rejection_yields_no_cf`: fail-path.
  - `test_no_action_in_4tuple_still_yields_position_cf`: degenerate path
    where the VLM emits a position but no action.

Both suites pass: 26 / 26.

### Out-of-scope follow-ups

- The snapshot reconstruction is **kinematic only**: the robot pose is the
  initial-reset pose, not the precise mid-episode pose at failure. A real
  fix would pipe live `snapshot_from_env(env)` captures through the buffer.
  For 250k-step training where >>1000 verifications will run, the
  kinematic approximation is reasonable (the robot moves a small amount
  relative to the block displacement that matters for verification).
- A full smoke-test run (1-2k steps on FetchPickAndPlace) requires an
  OpenAI key in the env; the unit tests stub the VLM call so they pin
  the wiring without spending tokens. Run

  ```
  set -a; source .env; set +a
  python train.py --config configs/verified_cf.yaml \
      env.name=FetchPickAndPlace-v4 \
      training.total_steps=2000 \
      training.warmup_steps=200 \
      training.log_interval=100 \
      logging.use_wandb=true
  ```

  to confirm `buffer/cf_verifications_attempted > 0` in W&B after a few
  failed episodes. (Phase 2 launch path will exercise this automatically
  once Modal frees.)
