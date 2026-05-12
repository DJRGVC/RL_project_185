# Ablation: VLM Model-Tier (Cost) Sweep

**Author**: Path-C ablation designer agent
**Created**: 2026-05-12 (overnight)
**Branch**: `agent/pathc-lead`
**Tag**: `path_c_ablation_vlmtier_2026-05-12`
**Status**: DESIGN ONLY — DO NOT LAUNCH TONIGHT.

## Why this ablation (and not another)

The `p_counterfactual` sweep (configs `cf_psweep_p{00,10,25,50,75}.yaml`, commit
`168518b`) already covers the CF/HER buffer-mix axis. The next most credible
reviewer hammer, given the paper's published Limitations and the existing
literature, is the **VLM model-tier** axis. Three converging reasons:

1. **Paper Limitation (v) names this exactly.** §6 admits: *"Our three-VLM-
   family robustness sweep (Opus 4.7, GPT-4o, Sonnet 4.5) does not yet cover
   open-weights VLMs (LLaVA-NeXT, Qwen2.5-VL, Pixtral); the relative magnitude
   of the prompt-architectural teleport failure on smaller open VLMs is open."*
   A reviewer who reads §6 will ask: *"OK, do you at least sweep the
   closed-VLM cost-tier axis you mention costs $500/run for?"*

2. **APPROACH_REFINEMENTS.md R4 + R8 are explicit asks.** R4
   ("VLM-scale ablation framing") notes our existing model comparison is *"under-
   sold"* — three families exist as a robustness check but were never plotted as
   a cost-vs-success curve. R8 ("Open-weights VLM swap") proposes a 1-hour
   open-weights pilot as the natural next step. This ablation does R4 directly
   on training-time performance, the only place a reviewer can't dismiss it as
   a one-shot prompt eval.

3. **Cost-effective deployment is a load-bearing claim.** §5.1 *"VLM API and
   cost"* explicitly quotes ≤$0.05/call and 10k calls/run. If a cheap VLM
   (gpt-4o-mini at ~$0.005) matches a premium one (Opus 4.7 at ~$0.15), the
   deployment cost drops 30x. If it does not match, the published 10k-call
   budget is at the wrong tier.

The four candidate ablations not picked, and why:

| Candidate | Why deferred |
|---|---|
| min_confidence sweep | Already gated by sim verification — second-order ablation. |
| verification-window length | Internal mechanism tuning; reviewers care less than cost. |
| failure-window K_W width | Touches §4.1 only; doesn't strengthen empirics. |
| n_seeds extension to 5–8 | Cheap, but does not introduce a new axis; safer as a follow-on once tier-effects are visible. |

## Hypothesis

> **H1 (cost-effective deployment).** Under the verified-CF pipeline (sim
> verification gate enabled, `reject_teleport_radius=0.05`, `vlm_variant=all`),
> the mean eval success at 250 k steps on FetchPickAndPlace satisfies
>
> $$\bigl|\mathrm{success}(\text{gpt-4o-mini}) - \mathrm{success}(\text{opus-4-7})\bigr| < 0.10$$
>
> across 3 seeds, with neither model strictly dominating outside the SE band.

**Underlying claim**: the simulator-verifier (Sec. 4.3 of the paper) is the
load-bearing component, not the VLM. Once a degenerate corrective action is
filtered by sim rollout, the VLM only contributes the seed proposal — a task
that small models can do because the prompt is *failure-localization +
corrective-position* (geometry-grounded), not open-ended reasoning.

**Pre-registered prediction (rank order, ascending model cost)**:
v0 (mini) ≈ v1 (gpt-4o) ≈ v2 (sonnet) ≈ v3 (opus), all within ±0.05 SE on PnP.

## Falsification criteria

Decision rule, applied at 250 k steps with mean across 3 seeds:

| Observation | Conclusion |
|---|---|
| All four tiers within ±0.10 success of each other | **H1 confirmed.** Recommend gpt-4o-mini as the production default; rewrite §5.1's cost paragraph to claim 30x cost reduction. |
| v3 (opus) beats v0 (mini) by ≥ 0.10 | **H1 falsified.** Mechanism is VLM-quality-bounded, not sim-verifier-bounded. Rewrite §4.3 to retract the *"generator-verifier asymmetry"* framing. |
| v2 (sonnet) ≈ v3 (opus) > v0 (mini) by ≥ 0.10 | **Partial H1.** Premium Anthropic is unnecessary, but cheap is not enough. Recommend sonnet as the deployment floor. |
| Bimodal: one or two seeds fail catastrophically in v0 only | **Reliability gap.** Cheap model has occasional pathological outputs the sim gate doesn't catch. Recommend confidence-threshold tightening, not model swap. |

The chosen comparison is 250 k steps because (a) the in-flight HER kill is
running 250 k anyway, so we share the budget reference; (b) at 500 k the
trajectories saturate on PnP and tier-effects compress.

## What we expect (qualitative)

Concrete prediction by tier, hardened from §5.3 and §5.5 evidence:

- **v0 (gpt-4o-mini)**: ~70 % of v1's verified-CF accept rate (mini is more
  prone to off-by-one keyframe localization, but sim gate catches the bad
  actions). Final eval success: ~0.55 (matching v1 within SE).
- **v1 (gpt-4o)**: production reference. Final eval success: ~0.55–0.60.
- **v2 (claude-sonnet-4-5)**: marginally higher accept rate (Sonnet's PnP
  rescue from §5.5 transfers). Final eval success: ~0.55–0.60.
- **v3 (claude-opus-4-7)**: highest accept rate by a small margin, no
  measurable success delta because the gate has already filtered out the
  noise the smaller models would have produced.

If the prediction holds, the paper gains a figure (cost-$ on log-x,
final-success on y) with four points clustering near the same y-value: a
visually compelling argument that the verifier dominates the generator.

## Estimated compute cost

| Resource | Quantity | Total |
|---|---|---|
| GPU-hours (RTX 5070 Ti) | 4 tiers × 1 env × 3 seeds × 0.5 h (250 k @ ~30 min) | **6 GPU-h** |
| VLM API $ — gpt-4o-mini | 3 seeds × ~1.2 k failed-eps × 1/8 call-interval × $0.005 | $2.25 |
| VLM API $ — gpt-4o      | (same) × $0.05 | $22.50 |
| VLM API $ — sonnet-4-5  | (same) × $0.03 | $13.50 |
| VLM API $ — opus-4-7    | (same) × $0.15 | $67.50 |
| **VLM API $ total** | | **≈ $106** |

Local GPU only (no Modal), so the existing 5070 Ti orchestration path applies
directly. The orchestrator can pick up this ablation as `phase3_ablation` in
the plan JSON; the schema extension is appended below.

## Priority for tomorrow

**P1.** This ablation should run *after* the HER kill experiment completes
(phase 1 of the existing plan) and *before* the Phase-2 VLM-CF Modal launches,
because it (a) uses the same verified-CF pipeline Phase 2 launches at scale and
(b) tells Phase 2 which model to standardize on. If gpt-4o-mini wins, we save
~$80 on the Phase-2 sweep.

**Sequencing**:
1. Phase 1 (HER kill) — already in-flight, ETA 30 min/run × 18 runs.
2. **vlmtier ablation — 4 tiers × 3 seeds = 12 runs × 30 min ≈ 6 h** (THIS).
3. Phase 2 VLM-CF + verified-CF — only after vlmtier confirms model choice.

If Phase 1 morning-deadline pressure means we can only fit half of vlmtier,
prioritize v0 vs v3 (the cheap-vs-expensive bracket); v1 and v2 are
interpolation points.

## Mechanical reproduction

```bash
# Dry-run preview (no execution):
DRY_RUN=1 bash scripts/run_ablation_vlmtier.sh

# Actual launch (DO NOT do this tonight):
bash scripts/run_ablation_vlmtier.sh
```

Configs: `configs/ablation_vlmtier_v{0,1,2,3}.yaml`.
Run-name pattern: `path_c_ablation_vlmtier_pp_{gpt4omini,gpt4o,sonnet45,opus47}_s{42,123,999}`.
W&B tag: `path_c_ablation_vlmtier_2026-05-12`.

## Plan JSON extension

Spec appended to `agent_reports/overnight_path_c_plan.json` as
`phase3_ablation_vlmtier` (parallel to existing `phase1_kill` and
`phase2_vlm`). The orchestrator does not yet read `phase3_*`, but the spec is
in the canonical place for tomorrow's harness work.

## Risks

1. **API quota.** Opus 4.7 has a 50-RPM rate limit on our account; at
   1.2 k failed-eps / (8 call-interval) ≈ 150 calls/run, well within budget.
2. **gpt-4o-mini vision throughput.** Mini does ~3× the latency of full
   gpt-4o on vision; cf_call_interval=8 already throttles this. Smoke test
   first.
3. **Seed-level variance.** 3 seeds is the floor for SE bars; if v0 vs v3
   shows a borderline 0.08–0.12 gap, the ablation will need 5 seeds to
   resolve. Budget contingency: $50 + 4 GPU-h for the 2-seed extension.
