# PER + CF-HER pre-staged — ready to fire after Phase 2 attempt 4

**Branch**: `agent/pathc-lead`
**Status**: code + tests + configs committed; NOT launched.
**Author**: PRE-STAGE AGENT (Opus 4.7), 2026-05-12.

---

## What this is

PER (Prioritized Experience Replay; Schaul et al. 2015) stacked **on top of**
CF-HER (Verified-CF, VLM-CF, or Oracle-CF). The two mechanisms are orthogonal:

- **CF-HER**: chooses *which transitions to INSERT* (synthetic, VLM-proposed-
  and-verified relabeled successes).
- **PER**: chooses *which transitions to SAMPLE* (proportional `|TD|^α` with
  annealed IS-correction weights `(1/N · p_i)^(-β_t)`).

When a Verified-CF synthetic transition is inserted, it lands at the buffer's
current **max-priority** (standard PER initialisation for novel transitions).
This means PER over-samples those synthetic terminal-success-like transitions
while their TD error is still high → they propagate Q-value information
faster than they would under uniform sampling. As their TD error decays they
fall to background priority and PER stops over-sampling them. Clean, automatic.

This also aligns the empirical method with §3's IS-posterior framing, which
is derived under PER's priority distribution.

---

## How it was implemented (Option B — composition)

**Cleanest design given the existing inheritance:**

- `HERBuffer.sample` / `.update_priorities` already **delegate** to the
  underlying buffer (see `src/buffers/her_buffer.py:92-96`).
- `CounterfactualHERBuffer` inherits this delegation.
- All it took to enable PER under CF-HER was wiring `make_buffer` to return
  a `PERBuffer` instead of a `UniformReplayBuffer` when `replay.type ==
  "cf_her_per"`.
- Synthetic transitions inserted via `_push_relabeled` → `self.buffer.push(...)`
  → `PERBuffer.push` → automatically set to max-priority. **No special-cased
  code** needed for "give Verified-CF transitions max priority" — that's
  just standard PER.

### Files changed

| File | Change |
|---|---|
| `src/buffers/__init__.py` | New `cf_her_per` branch → routes to `_make_per(cfg)` (mirrors existing `her_per` pattern). |
| `src/buffers/counterfactual_buffer.py` | New `priority_mode: 'uniform'|'prioritized'` ctor arg (informational + validation). New `get_per_stats()` method exposing β, max-priority, sum-tree mass, buffer size. |
| `train.py` | `use_cf_her` now matches both `cf_her` and `cf_her_per`. New local `cf_priority_mode` derived from replay type, passed into `CounterfactualHERBuffer(...)`. PER stats merged into the existing `buffer/cf_*` W&B logging block (`buffer/per_beta`, `buffer/per_max_priority`, `buffer/per_sum_tree_total`, …). |
| `tests/test_counterfactual_buffer.py` | +8 new tests across 5 new classes. Old test classes unchanged. |
| `configs/verified_cf_per.yaml` | NEW — Verified-CF + PER. |
| `configs/vlm_cf_per.yaml` | NEW — VLM-CF + PER. |
| `configs/oracle_cf_per.yaml` | NEW — Oracle-CF + PER (sanity ablation). |

### Existing configs untouched

- `configs/oracle_cf.yaml`, `configs/verified_cf.yaml`, `configs/vlm_cf.yaml` — **unchanged**, still produce `UniformReplayBuffer` underlying. In-flight runs are safe.

---

## Tests

```bash
source .venv/bin/activate
python tests/test_counterfactual_buffer.py        # 26 PASS / 0 FAIL
python tests/test_verified_cf_wiring.py           # 11 PASS / 0 FAIL
```

**New tests**:

1. `TestPERModeSamplesWithPriority::test_per_mode_high_td_dominates_sampling`
   — boosted slots sampled >2× uniform rate.
2. `TestPERModeSamplesWithPriority::test_uniform_mode_unchanged` — old configs
   still emit unit IS weights.
3. `TestPERModeUpdatesPriorities::test_update_priorities_changes_sampling`
   — spiking one slot's priority shifts the empirical sampling distribution.
4. `TestPERModeISCorrectionWeight::test_is_weights_present_and_finite` —
   IS weights finite, positive, normalised to ≤ 1.
5. `TestCFSyntheticTransitionsGetMaxPriority::test_synthetic_transitions_get_top_priority_on_insert`
   — every CF / HER synthetic transition lands at `max_priority^α`.
6. `TestCFSyntheticTransitionsGetMaxPriority::test_per_stats_reports_buffer_state`
   — `get_per_stats()` exposes β, max_priority, sum-tree mass.
7. `TestCFSyntheticTransitionsGetMaxPriority::test_priority_mode_uniform_returns_empty_per_stats`
   — uniform-backed buffers emit `{}` (so logging short-circuits cleanly).
8. `TestInvalidPriorityMode::test_unknown_priority_mode_raises` — typos
   raise instead of silently falling through.

---

## CPU smoke test (already run, passed)

```
CUDA_VISIBLE_DEVICES="" python train.py --config configs/oracle_cf_per.yaml \
  env.name=FetchPickAndPlace-v4 \
  training.total_steps=2000 \
  training.warmup_steps=200 \
  training.log_interval=100 \
  training.eval_interval=2000 \
  logging.use_wandb=false
```

13 seconds wall, 2000 steps, no crashes. PERBuffer underlying confirmed via
inline inspection (see commit description); SAC `update_priorities` path
exercised every step.

---

## How to launch (after Phase 2 attempt 4 finishes ~12:30 PDT)

The three new configs slot into the existing Modal launcher exactly like
their non-PER counterparts. Assuming the existing `modal_app.py` train
entrypoint uses `--config` (it does — see commit `eb899be` Path A
relaunch script for the pattern):

```bash
# Single-seed verified_cf_per smoke on Modal (recommended FIRST)
modal run modal_app.py::train --config configs/verified_cf_per.yaml \
    --env-name FetchPickAndPlace-v4 --seed 42 --steps 200_000

# Three-seed verified_cf_per on Modal
for seed in 42 43 44; do
    modal run --detach modal_app.py::train \
        --config configs/verified_cf_per.yaml \
        --env-name FetchPickAndPlace-v4 \
        --seed $seed --steps 1_000_000
done

# Same pattern for vlm_cf_per and oracle_cf_per
```

**Expected wall time** (single-seed 1M steps, A100, by analogy to in-flight
runs): ~3-4 hours per seed. Cost ≈ $4-5/seed at current Modal pricing.

**Recommended launch order** (after Phase 2 attempt 4 reveals signal/no-signal):

1. **If Phase 2 attempt 4 (uniform-sampled Verified-CF) shows ≥ 0.05 lift
   over HER baseline at 500k steps**: launch `verified_cf_per.yaml` (3 seeds,
   1M steps) — primary headline experiment. Optionally `oracle_cf_per`
   as the upper-bound ablation.
2. **If Phase 2 attempt 4 shows no signal**: launch `oracle_cf_per.yaml`
   FIRST (cheap, no VLM cost, gives ceiling). If oracle+PER ≥ +0.10 over
   HER+PER, the PER stack is the missing piece and Verified-CF+PER is
   worth running. If oracle+PER also flat, kill Path C entirely.

**Compute budget** (worst case, all three configs × 3 seeds × 1M steps):
9 runs × ~$4 ≈ $36 + VLM costs (verified_cf_per and vlm_cf_per — keep
`cf_call_interval: 8` from the configs to stay under ~$5 of VLM spend per
seed).

---

## Ablations the new configs enable

| Comparison | Configs | Question |
|---|---|---|
| Uniform vs PER (Verified-CF) | `verified_cf.yaml` vs `verified_cf_per.yaml` | Does PER help on top of VLM-verified relabels? |
| Uniform vs PER (Oracle-CF) | `oracle_cf.yaml` vs `oracle_cf_per.yaml` | Sanity: does PER help in the *ideal* CF regime? |
| Uniform vs PER (VLM-CF) | `vlm_cf.yaml` vs `vlm_cf_per.yaml` | Does PER help even with un-verified CFs? |
| HER+PER vs HER+CF+PER | `her_per.yaml` vs `verified_cf_per.yaml` | What does CF add on top of the best non-VLM baseline? |

That's a clean 2×3 matrix (`{uniform, prioritized}` × `{oracle, verified, vlm}`)
on top of the HER+PER baseline already in `configs/her_per.yaml`.

---

## Risks / what might silently break

1. **Synthetic transitions could *flood* the buffer with max-priority entries.**
   With ~50-step Fetch episodes and `her_k=4`, every failed episode inserts
   ~200 transitions at max-priority. If max-priority is much larger than the
   median, PER will over-sample these and the SAC critic sees a
   non-stationary distribution. Mitigation: PER's IS-correction weights
   compensate exactly for this. The smoke test confirms weights stay
   normalised to ≤ 1.0. Monitor `buffer/per_max_priority` for runaway growth
   (if it exceeds ~1e3, something's wrong).
2. **`per_beta` annealing schedule from `base.yaml` is 500k steps.** For
   1M-step runs this is fine. For shorter runs (e.g. quick smoke), β will
   plateau at 1.0 partway through. Configs override is straightforward
   if needed.
3. **The `priority_mode` arg is informational, NOT enforcement.** If a future
   refactor passes a `UniformReplayBuffer` while setting
   `priority_mode='prioritized'`, sampling will still be uniform but the
   `get_per_stats()` call will be silently empty (no key checks). This is
   a known soft constraint; the test `test_priority_mode_uniform_returns_empty_per_stats`
   guards the inverse case.
4. **Oracle-CF + PER could underperform Oracle-CF + Uniform** if the CFs
   are *already* the strongest learning signal and PER's bias makes the
   critic spend too much time on them. This would be *useful negative
   evidence* — report it.
5. **VLM-CF + PER without verification** could amplify VLM hallucinations
   (high-priority + bad goal = repeated SGD on a corrupted target).
   `vlm_cf_per.yaml` keeps `cf_min_confidence: 0.5` and `cf_fallback_to_achieved: true`
   as guards, but if `verified_cf_per` lifts and `vlm_cf_per` does NOT, that
   gap *is* the verification value-add — write it up.

---

## DO NOT LAUNCH UNTIL Phase 2 attempt 4 finishes (~12:30 PDT)

Per the user's explicit instruction. This handoff exists so the launch
is a 30-second copy-paste once the decision is made.
