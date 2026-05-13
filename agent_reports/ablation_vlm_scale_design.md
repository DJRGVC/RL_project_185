# Ablation: VLM Model-Scale (Cost) Sweep — Wave C

**Author**: Path-C ablation designer agent
**Created**: 2026-05-13 (post-overnight)
**Branch**: `agent/pathc-lead`
**Tag**: `path_c_vlm_scale_2026-05-13`
**Status**: DESIGN ONLY — NOT FOR CS 285 TONIGHT. Queued for the NeurIPS
preprint timeline (~Tuesday 2026-05-19 launch window, after Wave B and
matched-horizon HER/PER @ 500k finish).

## Why this ablation (and not another)

The most-cited reviewer attack against any "VLM-in-RL" paper is
**"does this method only work with the most expensive frontier VLM?"**
R1's L2 already partially flags it ("two-family, not three-family"
robustness; Anthropic Opus and Sonnet share corpus and RLHF lineage),
and §5.1 of the paper commits to a `<= $0.05/call` cost claim — load-
bearing for the practical-deployment narrative — without a side-by-side
verification across a model-cost arc that includes a small frontier
Anthropic model.

Three converging reasons to pick this specifically over the candidates
listed below (D-F):

1. **Cost claim becomes empirical, not assumed.** §5.1 quotes
   `~$0.05/call` and `10k calls/run`. If the cheapest VLM here
   (gpt-4o-mini, `~$0.005/call`) matches the most expensive
   (claude-opus-4-7, `~$0.15/call`) within ±0.10 SR, the deployment
   cost drops 30x — a paper-strengthening practical claim with a clean
   positive-result outcome.

2. **Cleanly executable with existing infrastructure.** The five
   model identifiers are all already supported (`provider in {openai,
   anthropic}` dispatch in `src/vlm/counterfactual.py:494-496` plus
   `_call_openai/_call_anthropic`). No new training infrastructure or
   tokenizer plumbing is required; the swap is a single YAML key.

3. **Direct rebuttal handle.** A reviewer attack of the form *"your
   method only works with $20/run VLMs"* is defused by a 5-point
   cost-vs-SR plot. A null result (no tier dominates) is the strongest
   possible answer to that attack.

The five candidate ablations not chosen, with rationale:

| Candidate | Why deferred |
|---|---|
| B. n>=5 seeds extension only | Subsumed by Wave C: this ablation already runs n=5. |
| C. `verify_n_steps` sweep | Internal verifier tuning; reviewers care less than cost. |
| D. Failure-window W sweep | Touches §4.1 only; doesn't strengthen empirics broadly. |
| E. `cf_call_interval` 16 vs 32 sweep | Cuts API cost but is a pure efficiency engineering point; doesn't add a falsifiable claim. |
| F. Number of keyframes K sweep | Mechanism-internal; lower review impact than cost. |

Wave C extends the existing **250k verified-CF tier sweep**
(`configs/ablation_vlmtier_v{0..3}.yaml`, design doc
`agent_reports/ablation_vlmtier_design.md`) along three axes:

- **horizon**: 250k → 500k (paper-grade Wave B horizon)
- **seeds**: 3 → 5 (R1 W2: ≥5 seeds for any "significance" claim)
- **new tier**: adds **claude-haiku-4-5** as a 5th model (the missing
  mid-Anthropic point — the existing 4-tier sweep skips Haiku)
- **pipeline**: `vlm_cf` (UN-gated) rather than `verified_cf` — this
  is the harder test for the cost claim because the simulator gate is
  off, so VLM quality is no longer hidden behind a verifier
  acceptance rate

The two sweeps are complementary: vlmtier (250k, verified-CF) tests
"does the gate make the VLM irrelevant?"; vlm_scale (500k, plain
vlm_cf) tests "does VLM quality matter at the production operating
point that the paper actually claims?"

## Hypothesis

> **H1 (cost-effective deployment, ungated).** Under the production
> CF-HER pipeline (`p_counterfactual=0.25`, `cf_call_interval=16`,
> `vlm_variant=achieved_goal`, NO simulator gate), the mean eval
> success at 500 k steps on FetchPickAndPlace satisfies
>
> $$ \bigl|\,\mathrm{SR}(\text{model}_i) - \mathrm{SR}(\text{model}_j)\,\bigr| < 0.10 $$
>
> for every pair $(\text{model}_i, \text{model}_j)$ in the 5-tier set
> {gpt-4o-mini, gpt-4o, claude-haiku-4-5, claude-sonnet-4-5,
> claude-opus-4-7}, at $n = 5$ seeds, with no model strictly
> dominating outside the SE band.

**Underlying claim**: with the production-default prompt
(`achieved_goal` variant, the C1v2-A winner) the cost-vs-quality
arc on Fetch tasks is roughly flat because (a) the prompt template
constrains the output space to a 3-D position, (b) HER's vanilla
hindsight provides a `1 - p_counterfactual = 0.75` floor regardless
of VLM quality, and (c) at p=0.25 the counterfactual signal is
mixed with hindsight at 1:3, damping any per-VLM quality variance.

**Pre-registered prediction (rank order, ascending model cost)**:
- gpt-4o-mini ≈ claude-haiku-4-5 (the two ~$0.005-0.02 tier)
- gpt-4o ≈ claude-sonnet-4-5 (the two ~$0.03-0.05 tier)
- claude-opus-4-7 (premium anchor)

All five within ±0.05 of the production-default (sonnet-4-5) SE band
on PnP at 500k. Equivalent within H1 if max-min < 0.10.

## Expected results pattern

Concrete prediction per tier, hardened from §5.3 (prompt design),
§5.5 (real-data eval), and the C1v2 model-comparison table
(`agent_reports/C1v2_model_comparison.md`):

| Tier | Cost / call | Predicted SR @ 500k | Mechanism |
|---|---|---|---|
| **gpt-4o-mini** | $0.005 | 0.30 ± 0.07 | C1v2-A: 0% teleport collapse on achieved_goal. Achieves baseline quality. |
| **claude-haiku-4-5** | $0.02 | 0.33 ± 0.07 | Mid-tier Anthropic; expected to match gpt-4o-mini at slightly higher cost. (UNTESTED previously.) |
| **gpt-4o** | $0.05 | 0.35 ± 0.06 | C1v2: production OpenAI reference. |
| **claude-sonnet-4-5** | $0.03 | 0.37 ± 0.06 | Production default for PnP; C1v2-A: rescues teleport-collapse where GPT-4o falls back. |
| **claude-opus-4-7** | $0.15 | 0.37 ± 0.06 | Premium anchor; no expected gap vs sonnet (Opus's strength is text reasoning, not 3D-position recovery on a fixed prompt). |

If the prediction holds, the paper gains a single
**cost-on-log-x, SR-on-y figure with 5 points clustering at the same
y-band**: a visually compelling argument that VLM-cost is not the
load-bearing axis of the method at the production operating point.

## Falsification criteria

Decision rule applied at 500 k steps with mean across 5 seeds:

| Observation | Conclusion |
|---|---|
| All five tiers within ±0.10 SR of each other | **H1 confirmed.** Recommend **gpt-4o-mini or claude-haiku-4-5** as the production-default in a *cost-aware deployment*. Rewrite §5.1 cost paragraph to claim a 30x-cost-arc-with-equivalent-SR result. |
| Opus or sonnet beats mini or haiku by ≥ 0.10 SR | **H1 falsified.** Method is VLM-quality-bounded at the production operating point. Demote the practical-cost claim from §5.1; report the per-tier curve as the new method-design finding. |
| Bimodal: mini or haiku fail catastrophically on ≥ 2 seeds while others don't | **Reliability gap.** Cheap model has occasional pathological outputs that the no-gate pipeline cannot catch. Recommend keeping verifier gate on. (This would *strengthen* §4.3's case for the verifier — a positive paper result either way.) |
| Frontier OpenAI (gpt-4o) and frontier Anthropic (sonnet) diverge by ≥ 0.10 SR | **Family effect, not scale effect.** Reframe §5.1 to claim "any frontier within a single family suffices" — different from the universal-equivalence claim. |
| Haiku 4-5 underperforms gpt-4o-mini by ≥ 0.10 SR | **Per-family scaling differs.** Anthropic's mid-tier has worse vision-grounding on robotics than OpenAI's. Useful negative result; weakens the universal-equivalence framing. |

## Compute cost estimate

| Resource | Quantity | Total |
|---|---|---|
| GPU-hours (Modal A10G, 500k @ ~30 min/run) | 5 models × 5 seeds × 1 env × 0.5 h | **12.5 GPU-h** |
| Modal $ @ ~$0.50 / A10G-h | 12.5 × 0.50 | $6.25 |
| VLM API $ — gpt-4o-mini  | 5 seeds × ~2.4 k failed-eps × 1/16 call-int × $0.005 | $3.75 |
| VLM API $ — gpt-4o       | (same) × $0.05  | $37.50 |
| VLM API $ — haiku-4-5    | (same) × $0.02  | $15.00 |
| VLM API $ — sonnet-4-5   | (same) × $0.03  | $22.50 |
| VLM API $ — opus-4-7     | (same) × $0.15  | $112.50 |
| **VLM API $ total**      | | **≈ $191** |
| **Grand total**          | | **≈ $197** |

Note: at the 16-call-interval and ~2.4k failed-eps/500k-run typical
of the production CF-HER buffer, the per-run call count is ~150 per
seed — well under the 50-RPM Anthropic Opus account limit.

Wall-clock estimate: 25 runs * ~30 min / run, throttled to Modal 10-
concurrency cap → **~3 batches × ~30 min = ~1.5 hr** if A10G pool is
clear. Allow a 6 hr budget against contention with Wave B
post-cleanup queue.

## Paper insertion plan

**Where this lands in main.tex**: a new sub-subsection of §5.5
("Real-Data Validation") OR a new §5.6 ("VLM Cost-Scale Sweep").
Recommendation: §5.6, because the cost claim is currently footnoted
in §5.1 ("VLM API and cost") and the sweep is its empirical
validation.

**Figure**: one PDF, NeurIPS style (no chart title, CB-safe palette,
sans-serif, vector). Cost on log-x ($0.005 → $0.15 → label "per-CF
call (USD)"), mean SR @ 500k on y with SE bars from n=5, one point
per tier, ordering left→right by cost. Annotate each point with
model name underneath. Color-code OpenAI vs Anthropic family. A
horizontal dashed line at the HER@500k baseline (from
`run_her_1m_*` already computed) for context.

**Table**: 5-row table in §5.6 with columns (Model, Family, Per-call
cost USD, Eval SR @ 500k mean ± SE, max-min gap vs frontier).

**Caption wording (target)**: "Across a ~30x cost arc spanning five
frontier and mid-tier VLMs (5 seeds each), final eval success on
FetchPickAndPlace at 500k steps is statistically equivalent
(max-min gap < 0.10 SR). The production-default
counterfactual-prompting pipeline does not require a premium VLM at
the p=0.25 operating point."

## Timing & sequencing

**Priority**: P2 for the NeurIPS preprint timeline (~Tuesday
2026-05-19 launch). NOT for the CS 285 paper submission tonight
2026-05-13.

**Sequencing constraints**:
1. **Wave B must finish first** (B1 her_per, B2 sharony, B3 2x2 —
   30 runs total, scheduled by
   `scripts/launch_waveB_when_psweep_done.sh`). Wave C consumes
   the same Modal A10G pool.
2. **Matched-horizon HER@500k + PER@500k must finish** (already
   queued, see `scripts/run_matched_horizon_500k.sh`) — this gives
   the dashed HER baseline for the cost figure.
3. **Earliest launch**: ~Tuesday 2026-05-19 morning, after the
   2026-05-13 → 2026-05-18 Wave B + matched-horizon window
   completes. Spec'd in `phase_waveC_vlm_scale` of the overnight
   plan JSON.

**Wall-clock budget for Wave C**: ~6 hours from launch to analysis,
including Modal contention buffer. Analysis (W&B query + figure
generation) is ~30 min once runs finish.

## Risks

1. **Opus 4.7 RPM cap**. At 50 RPM and ~150 calls/seed across 5
   seeds running concurrently in a Modal batch, peak instantaneous
   RPM is ~50 with 1-call-per-12-step pacing; tight but feasible.
   Contingency: lower Opus seeds to 3 if a cap is hit (sacrificing
   the n=5 claim for that single tier).
2. **Haiku 4.5 vision throughput**. Haiku's stated vision latency
   is ~1.5x that of Sonnet. Not a problem at cf_call_interval=16
   (one call per ~12 wall-clock seconds during early training).
3. **Stale gpt-4o snapshot**. The OpenAI `gpt-4o` alias has moved
   under us before. Pin to `gpt-4o-2024-08-06` (matches the §5.1
   citation in the paper) in a follow-up tightening if results
   come out odd.
4. **Seed-level variance**. If 5 seeds × 5 tiers shows a borderline
   0.08-0.12 gap, the ablation will need 8 seeds to resolve. Budget
   contingency: an additional $80 in VLM API + 5 GPU-h.

## Falsification: what result would INVALIDATE the design?

If **all** of the following hold simultaneously, the ablation
design itself is incorrect (not the hypothesis):

- All 5 tiers collapse to SR ≈ HER@500k baseline (≈ 0.58 on PnP)
  with no separation from baseline — meaning the CF mechanism is
  inert at p=0.25 regardless of VLM. This would invalidate the
  *framing* of the ablation (why study VLM choice if CF itself
  doesn't move SR?) and would be a Wave C *negative* result for
  the broader paper, not for the cost claim specifically.
- AND the within-tier variance exceeds the between-tier variance by
  3x — meaning seed noise dominates any VLM signal. This would
  invalidate the n=5 design choice; n=10+ would be needed.

In either of these cases, the cost-claim figure cannot be drawn
and the recommendation would be to **either** retract the cost
claim from §5.1 **or** restructure the ablation as a fixed-budget
experiment that holds *failed-episode count* constant rather than
training-step count.

## Mechanical reproduction (DO NOT RUN UNTIL ~2026-05-19)

```bash
# Dry-run preview (safe; no execution):
DRY_RUN=1 bash scripts/run_ablation_vlm_scale.sh

# Actual launch (DO NOT RUN until Wave B + matched-horizon @ 500k
# have completed):
bash scripts/run_ablation_vlm_scale.sh
```

The launcher is idempotent: it writes
`agent_reports/_VLM_SCALE_LAUNCHED.flag` on success and refuses to
relaunch while the flag exists. Delete the flag to permit a
retry.

Configs: `configs/ablation_vlm_scale_{gpt4omini,gpt4o,haiku45,sonnet45,opus47}.yaml`.
Run-name pattern: `path_c_vlm_scale_pp_{tier}_s{seed}_seed{seed}`.
W&B tag: `path_c_vlm_scale_2026-05-13`.

## Why claude-sonnet-3.5 and Gemini are NOT included

- **claude-3-5-sonnet-20241022**: deprecated Anthropic snapshot;
  vision is supported but the API is no longer the recommended
  endpoint and the model is excluded from current Anthropic pricing
  pages. Cleaner to anchor the legacy comparison via the existing
  vlmtier ablation than to mix versions here.
- **gemini-2.5-flash**: the project's VLM dispatch
  (`src/vlm/counterfactual.py:506-526`) supports only `openai` and
  `anthropic` providers. Adding a Google provider would require a
  new `_call_google` branch, a `google-generativeai` dependency, and
  a separate prompt-stability check on the Gemini multimodal API.
  Out of scope for Wave C; tracked as a follow-on in
  `APPROACH_REFINEMENTS.md` R8 ("Open-weights VLM swap") which
  proposes Pixtral / Qwen2.5-VL as the open-weights analog.

## Plan JSON extension

Spec appended to `agent_reports/overnight_path_c_plan.json` as
`phase_waveC_vlm_scale`. The orchestrator reads `phase_waveC_*` by
the same convention used for `phase_waveB_*`.
