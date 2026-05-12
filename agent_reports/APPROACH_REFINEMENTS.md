# Approach Refinements — From Deep-Lit Findings

*Author: DEEP-LIT-WRITER agent. Date: 2026-05-11.*

Five concrete refinements suggested by Phase 1's external scan. Tagged
**WRITING-ONLY** (do tonight) or **NEW EXPERIMENT** (tomorrow's TODO).

---

## Refinement R1: Sharpen the "multiplicative is unique" theoretical claim

**Current claim (Section 3, after Eq. 5).**
"Within this framing the multiplicative form of our priority update is the
unique reweighting that preserves PER's IS-correction structure."

**The refinement.** This sentence is currently asserted without
justification. A reviewer who knows the PER paper will challenge it. The
key fact is: PER's IS-correction is
$w_{\text{IS}}(i) = (|\mathcal{D}_B|\cdot\mu_P(i))^{-\beta}$. Any
proposal modification $\mu_{\text{new}}(i) = f(\mu_P(i), w_{\text{sem}}(i))$
that wants the same IS-correction *interpretation* (the corrected loss
equals $\mathbb{E}_U[\ell]$ as $\beta \to 1$) must satisfy
$\mu_{\text{new}}(i) \propto \mu_P(i) \cdot w_{\text{sem}}(i)$ up to a
trajectory-conditional normalization. Sharony et al.'s
$\mu_{\text{new}}(i) = \lambda \mu_{\text{VLM}}(i) + (1-\lambda)\mu_U(i)$
is an *additive* mixture that does *not* recover $\mathbb{E}_U[\ell]$
under any single-$\beta$ IS correction — they would need a
$\lambda$-dependent correction or a redefined target, which they do not
publish.

**Phase-3 action.** Add one sentence after Eq. 6 of the form: "Eq. 6 is
the unique-up-to-normalization proposal modification that keeps the PER
IS-correction interpretation valid: any additive mixture
$\lambda \mu_q + (1-\lambda)\mu_P$ implicitly retargets the loss away
from the uniform-replay objective unless paired with a $\lambda$-dependent
correction." Cite Sharony et al.'s mixture as the contrasting case.

**Tag:** WRITING-ONLY.

**Citations needed (already in Phase 1 dump):** sharony2026vlmrb,
schaul2016per.

---

## Refinement R2: Reframe the "we don't modify reward, we modify replay" claim

**Current state.** Our paper explains the importance-sampling framing but
doesn't directly contrast against the "just use a VLM to shape reward"
alternative, which is the obvious reviewer question now that Large Reward
Models (Wu et al. 2026, arXiv 2603.16065) and IKER (Patel et al. ICRA
2025) exist. A reviewer will ask: *"Why bother with prioritization? Just
have the VLM emit a dense reward."*

**The refinement.** Make the argument explicit in Section 3
(Theoretical Motivation):

> Two natural placements for a VLM signal in off-policy RL are
> *reward-shaping* (modify the TD target $r_i + \gamma Q(s_{i+1}, \cdot)$)
> and *replay-shaping* (modify the proposal $\mu$). Reward-shaping
> (Wu et al. 2026; Patel et al. 2025; Rocamonde et al. 2024) couples
> Q-target accuracy to VLM calibration: any per-timestep VLM error
> propagates *bias* into the value function. Replay-shaping (this paper)
> leaves the TD target untouched; the env's true sparse reward is
> recomputed on every sampled transition. VLM miscalibration shows up
> as *variance* in the sampling distribution, corrected by the standard
> IS-weight $w_{IS}$, analogously to V-trace's truncation. We choose
> replay-shaping for this bias-vs-variance trade.

**Phase-3 action.** Add this as a new paragraph in Section 3, after the
off-policy correction taxonomy table.

**Tag:** WRITING-ONLY.

**Citations needed:** wu2026largerewardmodels (new), patel2025iker (new),
rocamonde2024vlmreward (already cited).

---

## Refinement R3: Position our verification mechanism against generator-verifier RL

**Current state.** Section 4.3 (Verified Counterfactual Hindsight) frames
the protocol mechanically but doesn't connect to the broader
*generator-verifier* paradigm that has become mainstream in 2025-2026 LLM
RL (RL Tango, Trust-but-Verify survey, ExecutableCounterfactuals).

**The refinement.** A NeurIPS reviewer in 2026 will read our Section 4.3
and think "this is a generator-verifier system where the VLM is the
generator, the simulator is the verifier." Naming this connection
elevates the contribution from "neat engineering" to "instantiation of a
recognized paradigm in a new domain." Add a one-paragraph framing:

> Our protocol instantiates the *generator-verifier* paradigm
> (Zha et al. 2025; Trust-but-Verify survey 2025) recently popular in
> LLM reasoning. The VLM is a learned generator emitting a candidate
> corrective action; the unmodified simulator (with the env's own sparse
> reward) is a *symbolic verifier* whose decisions are formally correct
> by construction. In contrast to LLM generator-verifier pipelines where
> the verifier is itself learned and may share generator failure modes,
> our verifier is the ground-truth dynamics — analogous to symbolic
> verifiers in program synthesis. This is what lets us assign
> confidence~1.0 to accepted relabels.

**Phase-3 action.** Insert as the second-to-last paragraph of Section 4.3,
just before the broader-impact framing.

**Tag:** WRITING-ONLY.

**Citations needed:** zha2025tango (new), survey (new, optional).

---

## Refinement R4: Add explicit "VLM scale ablation"-style discussion (writing only — defer the experiment)

**Pattern observed in Phase 1 lit.** Almost every 2025-2026 VLM-RL paper
runs a VLM-scale ablation (Sharony et al. compare with-VLM vs. without;
AHA compares fine-tuned vs. zero-shot; RL-VLM-F compares VLM families).
NeurIPS reviewers in this area now expect a "does it survive cheaper
VLMs?" ablation. Our paper has a partial version of this (Opus 4.7 vs.
GPT-4o vs. Sonnet 4.5 prompt-grid in Sections 5.3-5.4), but doesn't
*frame* it as a scale ablation. The data is there; we are under-selling it.

**The refinement.** Rewrite the introduction/limitations to call our
existing GPT-4o vs. Opus 4.7 vs. Sonnet 4.5 evidence a *VLM-family
robustness ablation*, and explicitly say the failure mode is
prompt-architectural (we already do, but should highlight).

**Phase-3 action.**
1. In Section 5.3 final paragraph, add a sentence: "This functions as a
   VLM-family robustness ablation: the prompt-architectural fix
   transfers across at least three foundation-VLM families (Opus 4.7,
   GPT-4o, Sonnet 4.5)."
2. In Section 6 Limitations, add: "(v) we do not yet sweep over
   open-weights VLMs (LLaVA, Qwen-VL, Pixtral); the relative magnitude
   of the prompt-architectural failure on smaller VLMs is an open
   question."

**Tag:** WRITING-ONLY (the experiment is deferred).

---

## Refinement R5: Differentiate against AHA's failure-reasoning paradigm

**Current state.** AHA (Duan et al. ICLR 2025) is the closest *failure-
specific* VLM in robotics. We cite it as `duan2025aha` in the foundation-
models paragraph, but we do not draw the precise distinction. A reviewer
who knows AHA will ask: "Why isn't your system just AHA-driven
prioritization?"

**The refinement.** AHA's contributions are (a) a synthetic failure
dataset, (b) a fine-tuned VLM that produces failure *descriptions*, and
(c) downstream applications in Eureka (reward refinement) and PRoC3S
(planning). AHA does *not* localize a failure timestep within a
trajectory; AHA does *not* propose corrective actions; AHA's RL
integration is reward-refinement of LLM-generated reward code, not
replay prioritization.

**Phase-3 action.** Add to the foundation-models paragraph of Related
Work:

> AHA fine-tunes a VLM on synthetic robotic failures and produces
> natural-language failure explanations; AHA's RL integration refines
> LLM-generated reward functions (Eureka pipeline). Our work differs in
> three ways: (i) AHA describes failures whereas we localize them to a
> single timestep usable as a credit-assignment signal; (ii) AHA's RL
> contribution is reward-refinement whereas ours is replay-prioritization
> and hindsight-relabel-acceptance; (iii) AHA proposes no corrective
> actions, so its outputs cannot drive counterfactual relabels under our
> verification protocol. The two systems are complementary: an
> AHA-fine-tuned VLM could plausibly replace zero-shot GPT-4o inside our
> protocol.

**Tag:** WRITING-ONLY.

---

## Refinement R6 (NEW EXPERIMENT, not for tonight): Run the strictly-correct IS-weight ablation

Our paper currently uses $w_{IS,P}$ (PER's IS weight) rather than the
strictly-correct $w_{IS,\text{Sem}} = (|\mathcal{D}_B| \mu_{\text{Sem}})^{-\beta}$.
We frame this as "conservative under-correction" and analogous to V-trace
truncation. A reviewer will rightfully ask for the ablation.

**Action.** Tomorrow: a 50k-step run on FetchPush with the
$w_{IS,\text{Sem}}$ correction enabled. Predict: under-corrected variant
trains faster (higher effective semantic weighting); strictly-corrected
variant is more conservative but unbiased. Already flagged as Limitation
(i) in current draft.

**Tag:** NEW EXPERIMENT — flag for tomorrow's training pipeline (PATHC-LEAD).

---

## Refinement R7 (NEW EXPERIMENT, not for tonight): Generalization beyond Fetch

A reviewer will note our cross-task evidence is *within* the Fetch family
(Push, PickAndPlace, Slide all use the same gripper/object setup with
a 5cm threshold). To claim "VLM signal generalizes where any learned
priority head would not" robustly, we need at least one out-of-family
task. Suggested targets: Adroit (dexterous), robosuite, or one MiniGrid
task (matching Sharony et al.'s benchmark).

**Action.** A 12-episode cross-family pilot on Adroit Pen or robosuite
Lift, same single prompt template substitution. Estimated cost: 12 GPT-4o
calls @ $0.05 = $0.60; ~30 min compute.

**Tag:** NEW EXPERIMENT — flag for tomorrow.

---

## Refinement R8 (NEW EXPERIMENT, not for tonight): Open-weights VLM swap

Run the production prompt + verification protocol on at least one
open-weights VLM (suggest: LLaVA-NeXT or Qwen2.5-VL-7B). This would let
us claim the prompt-architectural fix transfers to open VLMs. Estimated
~1 hour of GPU.

**Tag:** NEW EXPERIMENT — flag for tomorrow.

---

## Phase-3 priority order

For the writing pass tonight:
1. R2 (reward-shaping vs. replay-shaping) — biggest payoff; goes into
   Section 3
2. R1 (multiplicative uniqueness) — sharpens the theory claim
3. R3 (generator-verifier framing) — elevates Section 4.3
4. R5 (AHA differentiation) — closes the most likely reviewer
   counter-question
5. R4 (VLM-scale robustness framing) — under-sold existing result

All five are writing-only and achievable in the 40-min budget.
