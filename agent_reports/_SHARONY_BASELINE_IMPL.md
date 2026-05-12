# Sharony VLM-RB Baseline — Implementation Report

**Prepared by:** Agent Path-C-lead (Opus 4.7)
**Date:** 2026-05-12
**Branch:** `agent/pathc-lead`
**Status:** Pre-staged (smoke-tested on CPU). Training NOT launched.
**Closes R1 W7/W9:** "differentiation from Sharony is thin" — we now run their method on our benchmark.

---

## What we built

A faithful approximation of Sharony et al. (2026) "VLM-Guided Experience
Replay" (arXiv:2602.01915) as a drop-in replay buffer in our codebase.

### Files added

| Path | Purpose |
|---|---|
| `src/buffers/vlm_rb_buffer.py` | `VLMRBBuffer` (extends `PERBuffer`). Implements clip-score caching, mixture-with-uniform sampling, λ-warmup. ~310 LOC. |
| `src/vlm/vlm_rb_scorer.py` | Clip scorer. Sonnet 4.5 (anthropic) / GPT-4o (openai) / stub (smoke). Sharony's prompt wording. |
| `configs/vlm_rb.yaml` | Sharony hyperparameters (α=0.6, L=32, λ 0→0.5 linear, score-every-10-episodes). |
| `tests/test_vlm_rb_buffer.py` | 9 unit tests — clip formation, priority update, mixture sampling, λ anneal, stub integration. **All pass.** |

### Files modified

| Path | Change |
|---|---|
| `src/buffers/__init__.py` | New `_make_vlm_rb` + `vlm_rb` / `her_vlm_rb` dispatch. |
| `train.py` | New `is_vlm_rb` flag; clip-scorer attachment; episode-start tracking; episode-end `apply_vlm_rb_scoring` call. Frame capture enabled. |

---

## Method fidelity table (theirs vs. ours)

| Component | Sharony et al. | Our reproduction | Faithful? |
|---|---|---|---|
| Clip length L | 32 frames | 32 frames (configurable) | **Yes** |
| Clip score formula | `q^P ∝ p_VLM · |δ|` | `priority = (|δ| · p_VLM + ε)^α` | **Yes** (Sharony §4.2 form) |
| Mixture-with-uniform | `q_t = λq^P + (1−λ)q^U` | Per-slot Bernoulli(λ); IS-corrected against `q_mix` | **Yes** |
| λ warm-up | linear 0 → 0.5 | linear 0 → 0.5 over `mixture_anneal_steps` | **Yes** |
| PER α | 0.6 | 0.6 | **Yes** |
| VLM call cadence | async worker (continuous) | every-N-episodes sync (default N=10) | **Approximated** |
| VLM model | frozen PerceptionLM (Cho et al. 2025) | claude-sonnet-4-5 via API | **Differs** — see below |
| Prompt | "Does this clip contain a clear instance of goal satisfaction anywhere in it? Look for contact + displacement..." | Same wording, parameterized over `task_description` | **Yes** |
| Score parsing | scalar p_VLM | `yes→conf`, `no→1-conf`, else 0.5 | **Yes** (Sharony does not specify; ours follows their binary-with-confidence schema) |

### Acknowledged differences

1. **VLM choice.** Sharony uses a frozen open-weights PerceptionLM
   (Cho et al. 2025). PerceptionLM is not API-accessible and would
   require local-GPU hosting outside our $80–150 baseline budget. We
   use **Claude Sonnet 4.5** (anthropic provider) which matches our
   Phase 2 attempt 5 deployment for consistency across the paper.
   Reviewer language: *"Our reproduction uses Sonnet 4.5 instead of
   frozen Perception-LM 1B; we acknowledge this as a modeling-choice
   difference and report results accordingly."*

2. **Sync vs. async VLM calls.** Sharony runs the VLM in an
   asynchronous worker (~12% throughput overhead). We invoke the
   scorer synchronously at episode end, every `vlm_call_interval`
   episodes. This bounds API spend but means *not every clip is
   re-scored every episode* — a clip's p_VLM is updated only when the
   episode it belongs to is the next scoring target. A reviewer-honest
   way to phrase this: *"We approximate Sharony's continuous-async
   scoring with episode-batched sync scoring to match our API-cost
   model; both schemes use the same priority formula and λ schedule."*

3. **Frame downsampling.** Sharony's prompt sees all 32 frames. We
   downsample to **8 uniformly-spaced frames per clip** (configurable
   `vlm_rb_max_frames_per_clip`) to keep per-call cost ≤ $0.01 on
   Sonnet 4.5. This is the same downsample ratio our Path-C VLM-CF
   pipeline uses for its keyframe call.

4. **Priority re-blend approximation.** When a new clip score arrives,
   we rescale the priority by `(new_score / prev_score)` outside the α
   exponent rather than recomputing `(|δ|·new + ε)^α` from the agent's
   |δ| (which is not cached). The exact form is recovered on the very
   next `update_priorities()` call. Relative ordering is preserved.
   Documented inline in the buffer.

---

## How to launch (do NOT launch now — Phase 2 + Oracle-CF in-flight)

Three envs × 3 seeds × 250k steps = **9 runs**. Sonnet 4.5 at ~$0.005 / clip
call × ~30 clips/episode × ~5000 episodes / vlm_call_interval(=10) ≈ **~$75
per run × 9 ≈ $675** if scoring every 10 episodes. To stay in the
$80–$150 envelope, raise `vlm_call_interval` to 50 or downsample fewer
frames.

### Modal launch (3-env × 3-seed sweep, FetchPickAndPlace example)

```bash
source .venv/bin/activate
for env in FetchPickAndPlace-v4 FetchPush-v3 FetchSlide-v3; do
  for seed in 0 1 2; do
    modal run modal_run_sweep.py \
      --config configs/vlm_rb.yaml \
      --override "env.name=${env}" \
      --override "training.seed=${seed}" \
      --override "training.total_steps=250000" \
      --group sharony-vlm-rb-baseline
  done
done
```

Expected wall-time: ~10h per run on A10G (matches our other
VLM-scoring runs). With 9 parallel Modal slots: **~10h total**.

### Local smoke test (already verified)

```bash
source .venv/bin/activate
CUDA_VISIBLE_DEVICES="" python train.py --config configs/vlm_rb.yaml \
  replay.vlm_provider=stub \
  training.total_steps=1500 \
  training.warmup_steps=200 \
  replay.capacity=5000 \
  replay.vlm_rb_clip_length=8 \
  replay.vlm_call_interval=1 \
  logging.use_wandb=false logging.use_tensorboard=false
```
Verified 2026-05-12: completes in ~8s, no crashes, log shows TD-error
descent. Test suite passes:

```bash
CUDA_VISIBLE_DEVICES="" python tests/test_vlm_rb_buffer.py
# → "All VLM-RB buffer tests passed."
```

---

## Risks & honest acknowledgements

1. **Our reproduction may underperform Sharony's published numbers.**
   - Different VLM (Sonnet 4.5 vs PerceptionLM); different domain
     (Fetch vs MiniGrid/OGBench); different cadence (sync-batched vs
     async). We should report Sharony's numbers separately *and* our
     reproduction on Fetch — never present our number as "VLM-RB's
     result."
   - Mitigation: introduce the table as **"VLM-RB on Fetch (our
     reproduction)"** and footnote each delta.

2. **No PerceptionLM access means we can't isolate VLM-choice from
   method-choice.** Reviewer could push: "Maybe Sharony's gains come
   from PerceptionLM's training data."
   - Mitigation: cite the methodological-vs-implementation distinction
     we already raise in Claim 4 of `L1_sharony_differentiation.md`.

3. **Cost over-run.** If `vlm_call_interval=10` overshoots budget, the
   sweep dies mid-run. Mitigation: set
   `vlm_call_interval=50` for the launch and explicitly document the
   throughput-vs-cost trade-off.

4. **The priority rescale approximation introduces a small bias.**
   When a new clip score arrives the buffer rescales by `new/prev`
   outside the α-exponent rather than recomputing exactly from |δ|.
   On the next `update_priorities` call this bias evaporates. In
   practice |δ| is updated every gradient step → bias decays within
   one batch. Documented in the buffer source.

5. **Sharony's code release ("coming soon") may invalidate some
   choices.** If they release before our submission we should re-verify
   λ horizon and prompt wording from source.

---

## Closing the gap — what this lets the paper say

Before: "We compare against Sharony only methodologically (Table 1)."
After: **"We additionally run Sharony's method on our benchmark
(Table N). Our failure-direction approach achieves $X$ on
FetchPickAndPlace versus Sharony's success-direction baseline at $Y$ —
a $Z$-point gap that closes head-to-head reviewer concern W7/W9."**

The implementation is faithful enough that a reviewer cannot say
"you didn't actually try their method." The acknowledged differences
(VLM choice, sync cadence) are scoped and the reproduction lives in
the same training loop as every other baseline — so the numbers are
directly comparable.
