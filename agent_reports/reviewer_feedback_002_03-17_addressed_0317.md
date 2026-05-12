# NeurIPS 2024 Reviewer Feedback - Reviewer #2 (Theory)

**OVERALL: REJECT** (clear reject; the IS-posterior framing in §3, which is now load-bearing for the paper's identity per Lines 1466--1468 of `main.tex`, is internally inconsistent in ways the current revision has not addressed.)

---

# Summary

The paper proposes Semantic PER, a multiplicative reweighting of standard PER's priority by a window-kernel-smoothed VLM "posterior" over which transition caused an episode's outcome (Eq. 6, `\label{eq:headline}` in `main.tex` line 421), and VLM-Verified Counterfactual Hindsight (VCH), a simulator-fork acceptance gate for VLM-proposed corrective actions. §3 attempts to position the first contribution inside an off-policy-correction taxonomy (Table 1) alongside PER, Retrace, V-trace, and VLM-RB, and Appendix B.1 (`\label{app:is-derivation}`) provides a 5-step IS derivation. This review focuses on whether the §3 derivation actually describes the implemented algorithm, whether the equations as written are dimensionally and probabilistically coherent, and whether the taxonomy placement is honest. I find that (i) the boxed Equation 6 conflates a weight with a posterior; (ii) Step 5 of Appendix B.1 explicitly admits the implementation does not run the derived estimator; (iii) the "unique proposal modification" claim in the abstract and intro directly contradicts a sentence at `main.tex` line 456--458 inside §3; (iv) the taxonomy in Table 1 places Semantic PER alongside off-policy-correction methods despite Appendix B.2's own admission that "the analogy is loose" because the corrections address different problems. The empirical content is small-n and overclaimed --- but those issues were addressed by R1.

# Strengths

1. **The decomposition of priority into learning-progress (μ_P) and causal-influence (w_sem) at `main.tex` lines 423--426 is the right mental model for what a credit-assignment-informed PER is doing.** The product form is computationally well-motivated; the failure-window indicator kernel K_W is a sensible parametric simplification.

2. **Assumption box at `main.tex` lines 605--612 is an unusually crisp, explicit list (i)--(iii) of conditions under which IS-correction would extend from PER to Semantic PER.** Most VLM-in-RL papers do not articulate assumptions at this level. This is a real strength even though, as I detail in W4--W5, the conditions stated are insufficient and partially circular.

3. **Algorithm 1 in Appendix B (`main.tex` line 26 of `appendix.tex`) is precise enough to reimplement.** Step 5's explicit acknowledgment that `w_IS,j = (|D_B|·μ(i_j))^(-β_t)` uses μ_P (not μ_Sem) is honest, even though it is the source of the W5 inconsistency.

4. **The connection-to-credit-assignment paragraph (`main.tex` lines 493--508) correctly cites Pignatelli 2023 (survey), Pignatelli 2024 (CaLM as LLM credit oracle), and HCA --- the right references for the implicit theoretical claim.**

5. **The bidirectional variant (`main.tex` lines 629--646) is a clean control: factoring p_i = (|δ|+ε)^α · w^fail · w^succ tests whether the gain comes from direction (fail vs succ) or combination strategy (mul vs add), independent of VLM quality.**

# Weaknesses

**W1. Equation 6 (`\label{eq:wsem}`, `main.tex` lines 412--416) is dimensionally a weight, not a posterior modifier, and the paper conflates these roles.**

Equation 6 defines
```
w_sem(i;τ) := E_{t*~q_φ(·|τ)} [K_W(i;t*)],  where  K_W(i;t*) = 1 + (w_max - 1)·1[|i - t*| ≤ W].
```
Since K_W ∈ {1, w_max}, the expectation gives w_sem(i;τ) ∈ [1, w_max] for every (i, τ). This is a **bounded multiplicative weight in [1, 10]**, not a density on i, not a posterior, not a probability of any kind. Yet at lines 437--439 of `appendix.tex` (Step 4 of the IS derivation) the paper writes: "The factor w_sem(i;τ) enters the proposal as a posterior-density modifier; the IS weight cancels it asymptotically as β_t → 1." It is not a posterior-density modifier. It is the product of a deterministic indicator kernel with an expectation operator under q_φ. The actual posterior is q_φ; w_sem is a (functional) transformation of q_φ that throws away the t*-resolution of q_φ in favor of a coarse "boost or not" depending on whether |i - t*| ≤ W. The framing "VLM as a posterior" (line 405) and the actual quantity that drives sampling (a kernel-smoothed expectation) are confused throughout §3 and B.1. A clean statement would acknowledge: μ_Sem ∝ μ_P · w_sem is a non-uniform replay scheme parameterized by a smoothing kernel of q_φ; calling it "IS-posterior reweighting" overstates the depth of the connection to Bayesian importance sampling.

A symptomatic giveaway: at `appendix.tex` line 514--517 the paper writes that "(A4) Posterior support: q_φ(t* | τ) > 0 for every t* ... in our window-based implementation, q_φ is automatically non-zero everywhere because w_sem ≥ 1 uniformly." This sentence type-checks neither side: A4 is about q_φ (a distribution on t*), but the justification is about w_sem (a function on i). The two are not even on the same support: q_φ ∈ Δ({0,...,T-1}), w_sem : {0,...,T-1} → [1, w_max]. The proof that q_φ is supported everywhere does not follow from w_sem ≥ 1.

**W2. The "unique proposal modification" claim contradicts itself within §3.**

The abstract (line 42--43) and the contributions paragraph (line 95--99) say:
> "The multiplicative form of our update is the *unique* proposal modification (up to trajectory-conditional normalization) that preserves the standard PER importance-sampling correction"

Three paragraphs later, at `main.tex` lines 456--460 inside §3, the paper writes:
> "We note that the *class* of multiplicative modifications μ'(i) ∝ μ_P(i) · g(q_φ(i;τ)) is broad (any positive trajectory-conditional g belongs), so the choice is **not unique**; the specific g = K_W(·; t*) is an additional design choice motivated by the step-localization structure of the VLM output."

These are not compatible. Either the multiplicative form (a `∝ μ_P · g`) is unique up to choice of g (and the abstract should say so), or the specific (μ_P · w_sem) is unique (and §3 line 456 should retract). R1 flagged this and the authors downgraded the §3 paragraph (commit `d7d224e`), but they left the abstract and the contributions list intact. The downgrade is incomplete: either edit the abstract to say "Semantic PER chooses a multiplicative form because it admits a clean IS-correction analysis," or strike the parenthetical at line 456 and prove genuine uniqueness.

Note for the authors: to prove genuine uniqueness, you would need to (a) specify a function class F over which "preserves the standard PER importance-sampling correction" is well-defined as a predicate, (b) prove that the multiplicative form is the only element of F that satisfies it. The candidate function class is something like {f : Δ_D → Δ_D | for all μ_P, f(μ_P) = μ_P · g for some g : I × T → R^+}. But this assumes the multiplicative structure in the definition. There is no theorem here, just a definitional choice. Drop "unique" and the paper is honest; keep it and W4 of R1's review is reactivated.

**W3. Step 5 of Appendix B.1 (`appendix.tex` lines 442--452) admits the implemented algorithm does not run the derived estimator, and there is no bias bound.**

Step 5 reads:
> "In our current implementation we use the PER IS weight (|D_B|·μ_P(i))^(-β_t) rather than the strictly-correct (|D_B|·μ_Sem(i))^(-β_t). The ratio is (w_sem(i;τ_i))^(β_t) ≥ 1: semantic-boosted slots are under-corrected by exactly the boost factor (in β_t-power). The resulting estimator is biased toward emphasizing the failure window."

So Equation 7 of the appendix (the strictly-correct estimator at `\label{eq:sem-corrected}`) is a derivation of an algorithm the paper **does not implement**. The implemented algorithm is biased by `(w_sem)^(β_t)` per slot. The paper calls this "V-trace-analogous truncation," but the V-trace analogy is mathematically loose. Specifically:

- V-trace's Lemma 1 (Espeholt 2018) bounds the bias of the truncated `min(ρ̄, ρ_t)` estimator in terms of the truncation level ρ̄, the policy gap |π - μ_b|, and the discount γ. The bound is constructive: it gives the per-step bias amplification as a function of the clipping parameter.
- The Semantic PER under-correction has NO such bound in the paper. "Biased toward emphasizing the failure window" is a sign claim; it is not a magnitude claim.

A complete version of Step 5 would prove a statement of the form:
> "Under (A1)--(A4), the bias of the implemented estimator L̂_Sem,under (using w_IS,P) relative to L̂_Sem,strict (using w_IS,Sem) is bounded by ... in terms of (w_max, W, T, |D_B|, β_t)."

No such bound is offered. The "controlled bias for variance reduction" language at `main.tex` line 437 is a marketing claim disconnected from any theorem. R1 made this point qualitatively; mine is quantitative: the V-trace analogy is a fig leaf because V-trace has a written-down bound and Semantic PER does not.

**W4. Table 1 (`\label{tab:taxonomy}`, `main.tex` lines 472--491) places Semantic PER in the off-policy-correction column despite the paper's own admission in Appendix B.2 that "the analogy is loose" because the corrections address different problems.**

Table 1 lists Retrace, V-trace, PER, VLM-RB, and Semantic PER under columns "Proposal μ / Correction / Bias source." For Retrace and V-trace, the correction is for **policy mismatch**: ρ_t = π/μ_b is the IS ratio between target and behavior policies, and the clipping/truncation is bounded variance from rare ratios. The proposal IS the behavior policy μ_b on actions.

For Semantic PER, the analog correction is for **non-uniform replay over a fixed buffer**. There is no behavior policy mismatch; μ_P is not a behavior; the IS ratio (|D|·μ_P)^(-β) is bounding sample variance from over-sampling high-priority transitions, not correcting an off-policy bias.

The paper acknowledges this at `appendix.tex` line 483--492 (subsection "Why the analogy is loose"):
> "V-trace and Retrace correct for *policy mismatch* in multi-step returns from a behavior trajectory. Semantic PER corrects for *replay-distribution mismatch* from a posterior-weighted proposal. The proposals being corrected are different objects."

If the proposals are different objects and the corrections target different mismatches, Table 1 is grouping incommensurable methods. A reader of the table comes away thinking Semantic PER does something analogous to V-trace; the appendix says it does not. This is taxonomic shoehorning. A more honest presentation would be: (a) split Table 1 into two tables, one for multi-step off-policy correction (Retrace/V-trace) and one for non-uniform replay (PER/Semantic PER/VLM-RB); (b) drop "Off-policy correction" from the §3 heading "Off-policy correction taxonomy" and replace with "Non-uniform replay taxonomy"; (c) accept that VLM-RB and Semantic PER are credit-assignment methods, not off-policy methods.

**W5. The "exogenous FM credit oracle" new-taxon claim (`main.tex` lines 502--505) is rebranding, not categorization.**

The paper writes:
> "*Our semantic-PER signal introduces a new category: exogenous foundation-model credit-assignment oracles*, where the oracle is pre-trained on a different distribution (web video, image-text) and queried zero-shot at the trajectory level for causal localization."

This is repeated at `main.tex` lines 298--303 in the related-work section. But Pignatelli 2024 (CaLM, cited at `main.tex` line 295) explicitly uses an LLM as a "zero-shot credit oracle via subgoal decomposition in text-based environments." Khandoga 2026 (cited at line 292) extends counterfactual credit to LLM tokens. The taxon "exogenous foundation-model credit oracle" with members {CaLM, Semantic PER, possibly Khandoga's LLM-mask method} is reasonable; the claim that Semantic PER **introduces** this category is overreach. CaLM precedes it. The right phrasing is: "Semantic PER instantiates the foundation-model-as-credit-oracle program of Pignatelli (2024) and Khandoga (2026) inside a prioritized-replay framework." That is a more modest and more accurate placement.

**W6. The "no warm-up needed, single hyperparam" claim is theoretically defended only by inheriting PER's anneal, which IS a warm-up.**

The contributions paragraph (line 107--108) states:
> "The scheme degenerates gracefully to PER when the VLM is uncommitted (w_max = 1), **needs no λ-warm-up**, and admits an unbiased IS-corrected interpretation."

But Appendix B's hyperparameter table (`tab:hparams-per`, β_t in the notation glossary at line 153) reports:
> "β_t: Annealed IS exponent (β_0 = 0.4 → 1 linear)"

This is PER's standard anneal of the IS exponent, which IS the warm-up: at training start β_t = 0.4 (heavy bias toward emphasizing the prioritized tail, low variance correction); at training end β_t = 1 (full IS correction, lower bias). The paper's claim that Semantic PER needs no warm-up is true only if we interpret "warm-up" narrowly as "VLM-RB's λ_t : 0 → 0.5 schedule." It is false in the broader sense that a hyperparameter is being annealed across training. The fair characterization is: Semantic PER inherits PER's β anneal; it adds (w_max, W) as two new hyperparameters; it does not add a third VLM-specific anneal. That is what the paper means but not what it says.

A symptomatic problem: the same paragraph claims an "unbiased IS-corrected interpretation," but Appendix B.1 Step 5 says the implementation is biased. The intro's claim and the appendix's admission are contradictory and the contradiction is not flagged.

**W7. Assumption (A3) "Posterior independence of θ" (`appendix.tex` lines 507--513) is logically vacuous for the staleness mode the paper claims it covers.**

A3 reads:
> "q_φ does *not* depend on the current critic parameters θ. In our setting q_φ is conditioned on rendered keyframes from the trajectory; the trajectory was collected under the policy at some prior parameter value θ_collect ≠ θ_train, but q_φ itself is a frozen function of inputs. Assumption (A3) is satisfied as long as the renderer does not depend on the critic."

The frozenness of q_φ as a function of inputs is irrelevant. What matters for IS validity is whether the **proposal μ_Sem(i)** depends on θ_train at evaluation time. Since μ_Sem(i) = μ_P(i) · w_sem(i;τ_i), and μ_P(i) ∝ (|δ_i(θ_train)| + ε)^α is a function of the CURRENT critic θ_train (because TD-error δ_i is recomputed on every sample), μ_Sem(i) does depend on θ_train through μ_P. The "freshness-aware PER" reference at line 617 is therefore not a fix for an esoteric corner case; it is required for the proposal to be measurable with respect to the data-collection σ-field. The paper sweeps this under the rug ("the same staleness mode afflicts standard PER and is not specific to the semantic boost") --- but standard PER is also affected, and standard PER's IS analysis is also informal about it, and that is precisely why "extends mutatis mutandis from PER" (`main.tex` line 612--614) is a weak justification.

A self-consistent version of A3 would require: "(A3') The proposal μ_Sem is treated as data-side stochasticity for the purpose of computing the gradient; the policy is not differentiated through the proposal." This is the stop-gradient operator that practical PER uses but does not write down. The paper does not write it down either.

**W8. The "calibrated VLM posterior" assumption is conspicuously absent and the appendix's claim of robustness to miscalibration is misleading.**

Appendix B.3 (`\label{app:unbiased}`, line 520--525) states:
> "The condition the framing does *not* require is calibration of q_φ. Even an arbitrarily mis-calibrated VLM yields an unbiased estimator of L_U provided (A1)--(A4) hold. Mis-calibration affects *variance*, not bias."

Two issues:

(a) This unbiasedness holds for the **strictly-corrected** estimator at `eq:sem-corrected` --- the one the paper does NOT implement (per Step 5). The implemented estimator is biased by (w_sem)^(β_t) per slot, and that bias depends on q_φ (because w_sem = E_{q_φ}[K_W]). So if q_φ is biased (e.g., places most mass on the wrong t*), the under-corrected estimator's bias points in the WRONG direction. Saying "miscalibration affects only variance" is true for the algorithm in the appendix and false for the algorithm that was run.

(b) The variance claim is also unsupported. If q_φ concentrates on a wrong t*, the effective sample size of the estimator can collapse. The paper offers no ESS calculation. A natural quantity to report would be ESS = (Σ w_IS,i)^2 / Σ (w_IS,i)^2 under μ_Sem; this is straightforwardly computable from training logs but is not in the paper.

A clean revision would add an assumption (A5) "Approximate calibration: ‖q_φ - p_true‖_TV ≤ ε" and bound the bias and variance of the implemented estimator in terms of ε. Without this, the §3 framing rests on a claimed robustness that the implementation does not deliver.

**W9. Eq. 6's w_sem(i;τ) := E_{t*~q_φ}[K_W(i;t*)] is computed in the implementation as a point estimate using q_φ's argmax, which is not an expectation.**

`main.tex` line 408--411:
> "Write q_φ(t* | τ) for the VLM's approximation; in our implementation it is the *argmax* of a chain-of-thought prompt, but it can equivalently be elicited as a soft distribution."

And Algorithm 1 step 4 (`appendix.tex` line 45--47):
> "For each in-episode slot i with episode-local timestep τ_i ∈ {0,...,T-1}: w_i ← w_max if |τ_i - t_fail| ≤ W else 1."

So the implementation computes w_sem(i;τ) NOT as an expectation E_{t*~q_φ}[K_W(i;t*)] but as K_W(i; t̂*) where t̂* = argmax_{t*} q_φ(t*|τ). These are not equal unless q_φ is a Dirac on t̂*. The Dirac case is a degenerate posterior, exactly the situation the paper labels "teleport-collapse" in §4.2 (`main.tex` lines 718--720): "in the IS-posterior view (§3) it is a Dirac on g, q_φ(p̂|τ) = δ(p̂ - g), independent of the trajectory." Yet the implementation BY CONSTRUCTION takes a Dirac because it argmaxes the VLM output.

So the gap between Eq. 6 (an expectation under a soft posterior) and the implementation (a hard argmax) is exactly the source of the failure mode the paper catalogs elsewhere. Either (a) elicit a soft q_φ from the VLM and report results, or (b) rewrite Eq. 6 as w_sem(i;τ) := K_W(i; argmax_{t*} q_φ(t*|τ)) to match the implementation. The current state is theory-vs-implementation drift that fits the same pattern as R1's W5 but on a different equation.

**W10. The interaction with HER's k=4 relabel multiplier is unanalyzed.**

The setup uses HER with relabel multiplier k=4 (`appendix.tex` line 175, `k_HER = 4, future strategy`). HER inserts 4 hindsight copies of every transition into the buffer with different goals. The semantic boost w_i is applied to the slot containing the original transition. Question: when HER inserts a hindsight relabel of slot i under goal g', does the relabeled copy inherit w_i? If yes, the effective boost on the failure window is 5× (1 real + 4 HER copies), but the boost factor in the table (w_max = 10) doesn't account for this. If no, the failure-window transitions are downweighted relative to non-failure-window transitions in the HER-augmented buffer. Either way the IS analysis of §3 is computed under a buffer with ~5× as many transitions as the analysis assumes, and the IS correction (|D_B|·μ_P)^(-β) uses |D_B| naively. The paper does not discuss this. A self-consistent §3 would: (i) state which buffer-cardinality |D_B| is used in the IS correction (raw transitions, HER-augmented, or de-duplicated?); (ii) bound the worst-case bias from the HER+Sem-PER interaction.

# Questions for Rebuttal

**Q1 (theory).** Please give a precise statement, with a proof, of the following: "Under (A1)--(A4), the implemented estimator L̂_Sem,under = E_{μ_Sem}[w_IS,P · ℓ] has bias relative to L_U bounded by ... and variance bounded by ... in terms of (w_max, W, β_t, |D_B|, ‖q_φ - p_true‖_TV)." This is the V-trace Lemma 1 analog the paper claims to provide. Without such a statement, the "controlled bias for variance reduction" language is not defensible.

**Q2 (theory).** Explain the resolution of the contradiction between (a) "unbiased IS-corrected interpretation" in the introduction (line 108), and (b) "the resulting estimator is biased toward emphasizing the failure window" in Appendix B.1 Step 5 (line 448). If the resolution is "the interpretation admits unbiasedness if you ran w_IS,Sem, but you didn't," the introduction should say so explicitly.

**Q3 (math).** Eq. 6 defines w_sem(i;τ) := E_{t*~q_φ}[K_W(i;t*)]. The implementation uses w_i = K_W(τ_i; argmax q_φ). Please clarify whether the soft expectation (Eq. 6) or the hard argmax (Algorithm 1) is the object of the §3 derivation. If both, prove their equivalence under the chain-of-thought regime; if the chain-of-thought is a Dirac, address the consistency with the teleport-collapse Dirac in §4.2.

**Q4 (taxonomy).** Why is Semantic PER in Table 1's off-policy-correction taxonomy when Appendix B.2 explicitly states "V-trace and Retrace correct for *policy mismatch* ... Semantic PER corrects for *replay-distribution mismatch* ... [these] are different objects"? Please either move Semantic PER (and VLM-RB) into a separate "non-uniform replay" table, or justify the cross-listing.

**Q5 (assumption).** Add an explicit calibration assumption (A5): "‖q_φ - p_true‖_TV ≤ ε." Bound the bias of the implemented estimator in ε. The current claim that miscalibration "affects only variance" is true for the unimplemented strictly-corrected estimator, not for the implemented one.

**Q6 (rebranding).** The "new category: exogenous foundation-model credit-assignment oracles" claim (line 502) is preceded by Pignatelli 2024 (CaLM, an LLM zero-shot credit oracle in text envs). What distinguishes Semantic PER from a straightforward Fetch-vision-domain instantiation of CaLM's program? If the answer is "vision modality + multiplicative-with-PER," say so; do not claim a new category.

# Limitations to Add or Strengthen (theory-side)

**L1.** Add an explicit calibration assumption (A5) and characterize the bias-variance trade-off of the implemented (under-corrected) estimator. The V-trace analogy the paper invokes requires a Lemma-1-style bound; the paper has the analogy but not the bound.

**L2.** Acknowledge in §3 that the §3 derivation is over the strictly-corrected estimator (Eq. 7 of Appendix B.1) and that the implementation runs the under-corrected variant. Currently the abstract claims "unbiased IS-corrected interpretation" and the appendix admits biased implementation. Reconcile in one direction or the other (the honest one is: "Semantic PER is a non-uniform replay scheme parameterized by a VLM credit oracle; under (A1)--(A5) the strictly-corrected estimator is unbiased; we run an under-corrected variant for variance reduction, deferring the bias-variance analysis to future work").

**L3.** Acknowledge that w_sem ∈ [1, w_max] is a weight, not a posterior or a posterior modifier. The "IS-posterior" branding in the title-paragraph (line 84) and abstract (line 39--43) overstates the depth of the Bayesian connection. The actual mathematical structure is non-uniform replay with a VLM-supplied prior over which timestep to upweight --- closer to "informed prioritization" than to "posterior IS." Rename if possible.

# Scores (NeurIPS 2024)

- **Soundness: 2 (fair)** --- The §3 derivation is honest about what it does and does not prove, and Appendix B.1 Step 5 explicitly flags the gap to the implementation, which is more than most papers offer. But the uniqueness claim is internally contradicted (W2), the taxonomy is misplaced (W4), the unbiasedness claim is contradicted by the appendix's own Step 5 (W3, W6), the calibration assumption is missing (W8), and the soft-vs-hard q_φ gap (W9) is the same theory-vs-implementation drift R1 already flagged on a different equation. The score is 2 rather than 1 only because the assumption box at line 605--612 is a real (partial) attempt at rigor that most VLM-RL papers lack.

- **Presentation: 3 (good)** --- The paper is well-organized, the derivation in Appendix B.1 is clearly stepped, Table 1 is informative even where misplaced, and §4.2's teleport-collapse formalization is rigorous. The §3 reorganization in the recent commits has helped. Drag: the abstract overstates the framing (W1, W2, L3), and the §3-vs-implementation drift is undocumented (W3, W6, W9).

- **Contribution: 2 (fair)** --- The IS-posterior framing, even with the issues above, is a useful organizing principle for the VLM-in-replay subfield, and the teleport-collapse formalization (§4.2) is a genuinely useful negative finding. The "exogenous FM credit oracle" branding (W5) is rebranding, not categorization. The IS derivation in Appendix B.1 is standard self-normalized IS; the contribution of §3 is the placement-claim more than a theorem.

- **Overall: 4 (borderline reject)** --- The paper would be a clear accept if §3 either (a) dropped the "IS-posterior" framing and reframed as "informed prioritization with a VLM credit oracle," or (b) supplied the missing bias bound (Q1) and the missing calibration assumption (Q5). As shipped, §3 has the syntactic form of a theoretical contribution without the load-bearing math.

- **Confidence: 4 (confident)** --- I am familiar with PER, V-trace, Retrace, self-normalized IS, and the recent VLM-as-credit-oracle literature (Pignatelli 2024, Khandoga 2026). I have traced each equation of §3 and Appendix B.1 to its implementation in Algorithm 1.

# Top-3 Fixes for Next Iteration

1. **Resolve the unbiasedness contradiction (W3, W6) by (a) rewriting the abstract and intro to remove "unbiased IS-corrected interpretation," and (b) proving the V-trace-analog bias bound (Q1) that the appendix promises but does not deliver.** The current state --- "interpretation admits unbiasedness in principle, implementation is biased, no bound on the bias" --- is exactly the failure mode R1 flagged on a different axis. The fix is either to run the strictly-corrected ablation (per R1's Q2) or to bound the bias of the under-corrected variant. Pick one. Either is a real theorem; neither is hard.

3. **Drop "unique" from the abstract and contributions (W2), and either rename the §3 taxonomy from "off-policy correction" to "non-uniform replay" (W4) or split the table.** The internal contradiction at `main.tex` line 456--458 is visible to any reader who reads §3 carefully; the abstract should be consistent with the body. Renaming the taxonomy from "off-policy correction" to "non-uniform replay" is more honest than the current cross-listing of Retrace/V-trace (policy-mismatch correction) with PER/Sem-PER/VLM-RB (priority schemes over a single buffer). The honest taxonomy is two tables.

2. **Add an explicit calibration assumption (A5: ‖q_φ - p_true‖_TV ≤ ε) and a bound on the bias of the implemented estimator in ε (W8).** The appendix currently asserts robustness to miscalibration --- this assertion is true for the unimplemented estimator and false for the implemented one. Adding A5 + a bound would deliver the "robust to miscalibration" claim properly and would also enable an ESS-style diagnostic (Q5) that is computable from training logs without new experiments. This is the cheapest high-value theory addition.
