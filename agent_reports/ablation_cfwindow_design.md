# Ablation: `cf_window` Locality-Bound Sweep

**Author**: Path-C ablation designer agent
**Created**: 2026-05-12 (overnight, post-02:47 cf_window fix)
**Branch**: `agent/pathc-lead`
**Tag**: `path_c_ablation_cfwindow_2026-05-12`
**Status**: DESIGN ONLY — DO NOT LAUNCH TONIGHT.

## Why this ablation (and not another)

At 02:47 PDT 2026-05-12, commit `539211c` promoted the `cf_window` parameter
in `src/buffers/counterfactual_buffer.py` from *dead code* to a *real
constraint*: a counterfactual at frame K is now eligible to relabel a
transition at t only if `t <= K <= t + cf_window` (combined with the causal
condition K >= t). Twelve production configs — including every `cf_psweep_*`,
every `ablation_vlmtier_*`, `oracle_cf`, `verified_cf`, and `vlm_cf` — set
`cf_window: 4` as the default. None of those 12 was selected by an
empirical sweep.

A reviewer reading §4.3 (Verified Counterfactual Hindsight) and noticing
that the relabel locality bound is a free hyperparameter would ask exactly
one question: **why 4?** This ablation answers it directly.

Three converging reasons this is the highest-value remaining ablation:

1. **The 02:47 fix created the gap.** Twelve in-flight or queued configs
   now depend on a previously-dead parameter that has never been swept.
   Any "Path C beats HER by X" headline claim is contingent on the
   `cf_window: 4` default being approximately optimal — a claim with zero
   empirical support tonight.

2. **It targets a different mechanism than every existing ablation.** The
   four ablation axes already designed cover (i) CF/HER buffer mix
   (`p_counterfactual`, `cf_psweep_p*`), (ii) VLM generator quality
   (`ablation_vlmtier_v*`), (iii) state-vs-vlm CF provider (`oracle_cf`
   vs `verified_cf`), and (iv) the FetchPush midpoint-bug rerun. None
   targets the relabel credit horizon — the locality bound is orthogonal
   to all four.

3. **Single-env, oracle-provider, $0 API cost.** Twelve runs on one env
   with the hand-coded oracle CF, no VLM API call, no $ exposure. The
   fastest credible empirical answer to a real reviewer question on the
   shortest GPU budget of any remaining ablation.

The four candidate ablations not picked, and why:

| Candidate | Why deferred |
|---|---|
| n_seeds extension (n=3 → n=8) | Addresses R1 W2 (statistical power) but does not introduce a new axis. Re-running the headline at 8 seeds × 5 methods = 40 GPU-h is a heavier lift; better adjudicated after Phase 1 verdict + cfwindow verdict are in. |
| `min_confidence` sweep | The min_confidence gate is downstream of the verification gate; with oracle provider confidence is always 1.0, so the sweep is degenerate. With VLM provider it interacts with the verifier in ways that need vlmtier results first. |
| Failure-window K_W width (§4.1 semantic kernel) | The paper's pre-registered §6 Limitation (vii) names this sweep over W ∈ {1, 3, 5, 10}. It targets *Semantic PER*, not *CF-HER*; the two pipelines share no buffer code. Worth doing, but is a follow-on for the Semantic-PER track, not Path C. |

## Hypothesis

> **H1 (locality matters; default near-optimum).** Under the oracle-CF
> pipeline (`cf_provider=oracle`, `p_counterfactual=0.25`,
> `cf_call_interval=1`), the mean eval success at 250 k steps on
> FetchPickAndPlace satisfies, across 3 seeds,
>
> 1. v1 (cf_window=4) >= v0 (disabled) within +/-0.10 success (locality bound helps or is neutral),
> 2. v2 (cf_window=10) ≈ v1 within +/-0.05 SE (broadening to 10 does not improve),
> 3. v3 (cf_window=25) ≈ v0 within +/-0.05 SE (near-disabled approaches disabled).

**Underlying mechanism**: the oracle CF for PickAndPlace places the
corrective goal at the midpoint of `(block_pos[K], desired_goal)` at
some salient frame K (typically the grasp-failure frame in the late
trajectory). When `cf_window` is disabled, a transition at t=0 (the
reach phase) can be relabeled with a CF at K=40 (the drop phase),
giving the actor a long-horizon reward signal that washes out the
local HER credit. A tight locality bound restricts the CF's reach to
nearby transitions where the reward landscape is locally informative.

**Pre-registered prediction (rank order, ascending window width)**:
v1 (cf_window=4) ≈ v2 (cf_window=10) > v0 (disabled) ≈ v3 (cf_window=25).

## Falsification criteria

Decision rule, applied at 250 k steps with mean across 3 seeds:

| Observation | Conclusion |
|---|---|
| v0, v1, v2, v3 all within +/-0.05 success of each other | **H1 falsified (weak).** The locality bound is irrelevant on PnP; the 12 production configs are unaffected by the 02:47 fix in practice. Recommend keeping `cf_window: 4` as a conservative default but stop citing it as load-bearing. |
| v0 beats v1 by >=0.10 | **H1 falsified (strong).** The 02:47 fix was the wrong default. Recommend setting `cf_window: 0` (disabled) in 12 production configs and re-running affected experiments. |
| v1 ≈ v2 beats v0 and v3 by >=0.10 | **H1 confirmed.** The locality bound is real; the production default (4) is near the optimum. Add a one-sentence §4 footnote: "We set `cf_window` (relabel locality bound) to 4 based on the cfwindow sweep reported in Appendix X." |
| v2 strictly beats v1 by >=0.10 | **Partial H1 (relaxation).** Locality is real but the default is too tight. Recommend bumping production default to `cf_window: 10`; re-run any borderline OCF/VCF runs at the new default. |
| v0 ≈ v3 outperform v1 ≈ v2 by >=0.10 | **Reversed locality.** The CF helps most when it can relabel transitions arbitrarily far from K. This would be a surprising finding and would warrant a §4.3 paragraph on long-horizon CF credit assignment. |

The chosen comparison is 250 k steps because (a) it matches the
`phase1_kill` budget reference (every OCF baseline runs to 250 k) and
(b) PnP saturates near 500 k, compressing tier-effects at the longer
horizon.

## What we expect (qualitative)

- **v0 (cf_window=0, disabled)**: ~0.40 success at 250 k. The CF still helps
  vs pure HER (the achieved-future fallback is intact), but long-horizon
  relabels add variance. Slightly below v1.
- **v1 (cf_window=4)**: ~0.50–0.55 success at 250 k. Production default;
  matches the phase1_kill OCF reference.
- **v2 (cf_window=10)**: ~0.50–0.55 success at 250 k. Indistinguishable
  from v1; the extra eligibility frames cover the few cases v1 over-tightens.
- **v3 (cf_window=25)**: ~0.40–0.45 success at 250 k. Approaches v0 because
  on T=50 episodes a window of 25 is half-episode, so eligibility is
  effectively unbounded for most t.

If the prediction holds, the paper gains an appendix table (cf_window
on the x-axis, final success on y) with a clear plateau between 4 and 10
and a drop-off at 0 and 25. This is a visually compelling argument that
the 02:47 fix was a real correction.

## Estimated compute cost

| Resource | Quantity | Total |
|---|---|---|
| GPU-hours (RTX 5070 Ti) | 4 cells × 1 env × 3 seeds × 0.5 h (250 k @ ~30 min) | **6 GPU-h** |
| VLM API $ | oracle provider, no API call | **$0** |

Local GPU only (no Modal). Twelve runs at three-way local parallelism = ~2 h
wall-clock. The orchestrator can pick this up as `phase3_ablation_cfwindow`
in the plan JSON; the schema extension is appended below.

## Priority for tomorrow

**P1.** This ablation should run *immediately after* `phase1_kill` and
`phase1_rerun_push` complete and *before* `phase2_vlm`, because (a) it
shares the oracle-CF pipeline that `phase1_kill` is validating and uses
the same code path the 02:47 fix touched, (b) the verdict is needed to
interpret all twelve `cf_window: 4` configs already in flight, and
(c) it has $0 API exposure unlike `phase2_vlm` and `phase3_ablation_vlmtier`.

Recommended sequencing (relative to existing plan):
1. **Phase 1 (HER + Oracle-CF kill)** — already in-flight, ETA 30 min/run × 18 runs.
2. **Phase 1 rerun_push** — corrected midpoint, 3 runs.
3. **cfwindow ablation (THIS)** — 12 runs × 30 min ≈ 6 GPU-h, $0.
4. **vlmtier ablation** — 12 runs × 30 min ≈ 6 GPU-h, ~$106.
5. **Phase 2 (VLM-CF + Verified-CF on Modal)** — only after cfwindow + vlmtier
   confirm `cf_window` and `vlm_model` defaults.

If morning-deadline pressure means only half of cfwindow fits, prioritize
v0 vs v1 (the disabled-vs-default bracket, which is the headline reviewer
question); v2 and v3 are interpolation points.

## Risks

1. **Floor effect at 250 k.** PnP at 250 k under oracle-CF typically hits
   ~0.50 success; if cell-to-cell variance is comparable to the floor of
   the metric (~0.05), 3 seeds may not resolve a 0.05-magnitude gap.
   Mitigation: report mean +/- SE explicitly and flag any borderline
   verdict as "underpowered" rather than "null."
2. **Seed-level pathology on FetchPickAndPlace.** Slide is known noisy
   (paper §5.1); PnP is less so but not noiseless. If one seed in any
   cell catastrophically fails, the 3-seed mean drops by 0.33. Budget
   contingency: 2 extra seeds (1234, 5678) for borderline cells = 4 more
   GPU-h.
3. **Oracle CF saturates the buffer at small windows.** With cf_window=0
   most transitions get the achieved-future fallback rather than the
   CF; the cell partially degenerates to HER. This is by design (it
   tests whether the locality bound matters) but should be sanity-checked
   in W&B via `buffer/cf_relabels_used` vs `buffer/achieved_relabels_used`
   on each run.
4. **No interaction with `p_counterfactual`.** This sweep fixes
   `p_counterfactual=0.25`. The cfwindow effect at different
   `p_counterfactual` values is a separate axis we do not cover. Note in
   the appendix that the interaction is unresolved.

## Mechanical reproduction

```bash
# Dry-run preview (no execution):
DRY_RUN=1 bash scripts/run_ablation_cfwindow.sh

# Actual launch (DO NOT do this tonight — no GPU capacity):
bash scripts/run_ablation_cfwindow.sh
```

Configs: `configs/ablation_cfwindow_v{0,1,2,3}.yaml`.
Run-name pattern: `path_c_ablation_cfwindow_pp_{w0,w4,w10,w25}_s{42,123,999}`.
W&B tag: `path_c_ablation_cfwindow_2026-05-12`.

## Plan JSON extension

Spec appended to `agent_reports/overnight_path_c_plan.json` as
`phase3_ablation_cfwindow` (parallel to existing `phase3_ablation_vlmtier`).
The orchestrator does not yet read `phase3_*`, but the spec is in the
canonical place for tomorrow's harness work.
