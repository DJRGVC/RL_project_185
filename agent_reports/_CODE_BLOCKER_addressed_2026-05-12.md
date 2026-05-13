# CODE-REVIEWER BLOCKERS

> Auto-overwritten each cycle. Reflects the most critical issues found.

## RESOLVED in commit 168518b (00:01 PDT 2026-05-12)

### ~~B1 — `verified_cf` provider is a no-op~~ ✅ FIXED

`commit 168518b "Path C: fix verified_cf no-op, add p_counterfactual sweep configs, add CF-HER tests"` — closes the no-op:
- `make_counterfactual_fn` gained `return_action: bool` kwarg → 4-tuples carry corrective_action.
- `_build_cf_provider` in train.py now actually calls `verifier.verify(...)`, forces `vlm_variant='all'` when verified is selected, reconstructs MuJoCo snapshots via `reconstruct_snapshot_for_synthetic_episode`, and either promotes verified CFs to confidence=1.0 or drops them.
- `cf_verifications_*` W&B metrics surface attempted/succeeded/rejected counters.
- Added `tests/test_verified_cf_wiring.py` (11 invariants) and `tests/test_counterfactual_buffer.py` (15 invariants). Both suites self-report 26/26 passing.

**Verified by code-reviewer**: the wiring is correct; the fix is back-compatible (`return_action=False` keeps the old 3-tuple contract for vanilla `vlm_cf` and `oracle_cf` runs already in flight).

**Minor caveat for the morning consolidator**:
- Forced `vlm_variant='all'` means verified_cf CFs may have higher teleport-collapse rate (per C1v2-A) before verification filters them. So verified_cf could end up with LOWER CF density than vlm_cf-with-`achieved_goal`. The `cf_verifications_success_rate` metric will reveal this.
- `reconstruct_snapshot_for_synthetic_episode` creates a fresh `gym.make(env_name)` PER verify call. At ~625 calls per 250k-step run, that's ~5-10 min wallclock overhead. Acceptable, but bears monitoring.

---

## Active blockers (must be addressed before morning consolidation)

### B2 — Phase 2 Modal jobs may crash on W&B init (multi-file regression)

**Triple regression** on `agent/pathc-lead` vs `agent/a1-her-baselines`:

1. **`modal_app.py:train_remote`** (commit 5a859f5 / b393fe3) removed the `WANDB_PROJECT` and `WANDB_ENTITY=d-grant-uc-berkeley` os.environ overrides that a1 explicitly added because the Modal secret bakes in `WANDB_ENTITY=djrgvc`.
2. **`modal_app.py:train_remote`** also removed the `wandb_tags` parameter (replaced by env var read in logger.py — but Modal secrets fix WANDB_ENTITY before that env var is read by the container).
3. **`src/utils/logger.py`** removed the try/except fallback to default entity (the a1 version: on perm-denied, retry with entity=None).

**Combined impact**: Every Phase 2 Modal training job is likely to crash at `wandb.init` with permission denied to `djrgvc/RL_project`. The orchestrator marks the run failed but no actual training happens. **This would silently kill all of Phase 2.**

**Workarounds for tonight** (in order of safety):
- (Safest) Verify the Modal secret was already updated to set `WANDB_ENTITY=d-grant-uc-berkeley`. If yes, this is moot.
- (Moderate) Have a human apply the a1-her-baselines `os.environ["WANDB_ENTITY"]="d-grant-uc-berkeley"` override at the top of `train_remote` in `modal_app.py`, commit, and require Modal to rebuild the image. (Image rebuild takes ~10 min on the next launch.)
- (Risky) Restore the try/except fallback in `src/utils/logger.py` so failed entity falls back to default. (Still rebuilds image.)

**Morning merge action**: re-introduce the `WANDB_ENTITY` override in `modal_app.py::train_remote` AND restore the try/except fallback in `src/utils/logger.py`.

### B3 — `src/envs/wrappers.py` regression to unconditional `render_mode`

The `agent/a1-her-baselines` branch had a guard: `kwargs["render_mode"]` was set only when `capture_frames=True`. The `agent/pathc-lead` branch (b393fe3) regressed to **always** set `render_mode`.

**Impact**: any environment created without an offscreen GL context (e.g., a Modal worker that didn't get OSMesa installed correctly) will crash at `gym.make(...)`. With `MUJOCO_GL=osmesa` in the Modal image and `MUJOCO_GL=egl` set by the local orchestrator, in practice this is harmless. But it's a regression that loses defensiveness.

**Morning merge action**: take the a1-her-baselines version of `src/envs/wrappers.py:make_env`.

---

_Last update: 2026-05-12 00:10 PDT_
