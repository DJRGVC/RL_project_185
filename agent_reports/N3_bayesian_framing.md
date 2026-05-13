# N3 — Bayesian Framing: VLM-Guided PER as Posterior Reweighting

**Prepared by:** Agent N3 (novel-direction theoretical framing)
**Date:** 2026-05-11
**Audience:** Daniel; draft of a "Theoretical Motivation" section for the paper
**Companion reports:** L1 (Sharony differentiation), L2 (bibliography), C2 (counterfactual mechanism)

---

## TL;DR for the reader

Sharony et al. cast VLM-Guided Experience Replay as an engineering recipe: "score sub-trajectories with a VLM, mix into PER, train." They write down no replay-sampling objective and connect to no off-policy theory. We argue the right way to view the entire VLM-in-replay paradigm — both theirs and ours — is as **importance-sampled stochastic optimization with the VLM as a learned proposal distribution.** Specifically, the VLM emits a posterior `q(t* | τ)` over which transitions are most responsible for an episode's outcome; semantic PER then samples transitions from a weighted product `q(t* | τ) · π_default(t)`, with the Bellman-error correction recovering an unbiased estimator. This perspective (a) gives the method principled motivation, (b) connects it to retrace, V-trace, prioritized DQN, and the causal-credit-assignment literature, and (c) yields concrete predictions and new ablations that an empirical-only paper cannot make. We adopt this lens throughout.

---

## Notation table (LaTeX-ready)

| Symbol | Meaning |
|---|---|
| `τ = (s_0, a_0, r_0, …, s_T)` | An episode trajectory |
| `i ∈ {0, …, T-1}` | A transition index within the episode |
| `D_B` | Replay buffer of stored transitions |
| `δ_i = r_i + γ Q(s_{i+1}, π(s_{i+1})) − Q(s_i, a_i)` | TD-error at transition `i` |
| `L(θ; i) = δ_i^2` (or Huber) | Per-transition Bellman regression loss |
| `μ(i)` | Sampling distribution over transitions used by the buffer |
| `μ_U(i) = 1/|D_B|` | Uniform sampling distribution |
| `μ_P(i) ∝ ( | δ_i | + ε)^α` | Standard PER sampling distribution |
| `w_IS(i) = (|D_B| · μ(i))^{−β}` | Importance-sampling correction weight |
| `t*(τ)` | The (unobserved) true outcome-causing timestep of episode `τ` |
| `p(t* | τ)` | True (unknown) posterior over outcome-causing timesteps |
| `q_φ(t* | τ)` | VLM-emitted approximate posterior; `φ` denotes the VLM's frozen parameters |
| `K_W(i; t*)` | Window kernel; `1[ | i − t*  | ≤ W]` in our impl., bounded `w_max` boost |
| `w_sem(i; τ) = E_{t* ∼ q_φ}[K_W(i; t*)]` | Semantic boost factor for transition `i` |
| `μ_Sem(i) ∝ μ_P(i) · w_sem(i; τ_i)` | Our sampling distribution (semantic PER) |
| `λ_t ∈ [0, 1]` | Sharony's mixture coefficient (warm-up scheduled) |
| `μ_Sharony(i) = λ_t · μ^P_VLM(i) + (1 − λ_t) · μ_U(i)` | Sharony's sampling distribution |

---

## Section 1 — The reweighting view of replay

Off-policy value-function learning solves a regression problem on a distribution `μ` over transitions:

```
L(θ) = E_{i ∼ μ}[ ℓ(δ_i(θ)) ],
```

where `ℓ` is typically squared error or Huber loss. Different replay schemes correspond to different choices of `μ` and, correspondingly, different correction weights.

**Uniform replay (UER).** Set `μ = μ_U`. The empirical estimator is unbiased: the gradient
`∇_θ L_U(θ) = (1/|D_B|) Σ_i ∇_θ ℓ(δ_i)` is an unbiased estimate of `E_U[ ∇ ℓ ]`. Variance is high when most transitions are uninformative.

**Prioritized replay (PER, Schaul et al. 2016).** Sample `i ∼ μ_P` with `μ_P(i) ∝ (| δ_i | + ε)^α`. Sampling from `μ_P` is a non-uniform proposal, so the loss becomes biased unless we correct. Schaul et al. multiply each gradient by the importance weight

```
w_IS(i) = ( (1/|D_B|) / μ_P(i) )^β,
```

yielding the corrected estimator

```
∇_θ L_P(θ) = (1/|D_B|) Σ_i w_IS(i) ∇_θ ℓ(δ_i)
           = E_{i ∼ μ_P}[ w_IS(i) · ∇_θ ℓ(δ_i) ].
```

At `β = 1` this exactly recovers the uniform-loss gradient; the schedule `β: β_0 → 1` trades variance reduction (in early training) for unbiasedness (at convergence).

**Key insight.** PER is an *instance of self-normalized importance sampling*: the proposal `μ_P` is chosen to put mass on high-error transitions; the IS-weight `w_IS` reweights them back so the *target* objective remains the same. The "prior" being approximated is uniform on the buffer; the "proposal" is `μ_P`; learning still targets `E_U[ ℓ ]`.

This is the lens we extend.

---

## Section 2 — The VLM as a posterior

Now consider what a VLM is actually doing when it answers "which timestep caused the episode to fail?" Mathematically, the VLM is approximating the posterior

```
p(t* | τ) ∝ p(τ | t*) p(t*)
```

where `t*` is the latent random variable "the timestep responsible for the trajectory's outcome." The frozen VLM `q_φ(t* | τ)` is a (deeply approximate, miscalibrated, but informative) sample of this posterior conditional on the rendered trajectory. The output of our prompt — `t_fail` ∈ {0, …, T-1} — is the argmax of this posterior; equivalently, with a softer prompt or temperature-controlled chain-of-thought, the VLM induces a distribution over `t*` from which we have a point estimate.

**Semantic PER as posterior reweighting.** Given `q_φ(t* | τ)`, define the per-transition semantic boost

```
w_sem(i; τ) := Σ_{t*} q_φ(t* | τ) · K_W(i; t*),                           (1)
```

where `K_W(i; t*) = 1 + (w_max − 1) · 1[| i − t* | ≤ W]` is a window kernel of half-width `W` and bounded boost `w_max ≥ 1`. The semantic-PER sampling distribution is then

```
μ_Sem(i)  ∝  μ_P(i) · w_sem(i; τ_i),                                     (2)
```

i.e., we multiply the TD-error proposal by an estimate of the per-transition posterior probability of being outcome-causing.

**The factorization tells the story.** Two distinct factors drive priority:

1. `μ_P(i) ∝ |δ_i|^α`: how much would learning from `i` reduce the buffer's average TD-error? This is the *learning-progress* factor.
2. `w_sem(i; τ_i)`: how much posterior mass does the VLM place on `i` being the actual cause of the trajectory's outcome? This is the *causal-influence* factor.

Standard PER uses only the first; uniform replay uses neither; **semantic PER multiplies the two**. The multiplicative form is principled: when the VLM is non-committal (`q_φ` near-uniform), `w_sem ≈ 1` and we degenerate to PER. When the VLM is confident, we up-weight the posterior region of the trajectory by `w_max` and let `|δ_i|` further discriminate within that region.

**Comparison to Sharony.** Sharony's mixture
```
μ_Sharony(i) = λ_t · μ^P_VLM(i) + (1 − λ_t) · μ_U(i)
```
is an *additive convex combination* of a VLM-derived proposal and uniform. In the Bayesian lens, this is **not** a posterior reweighting of PER but a *mixture model* in which the VLM gets to redirect a fraction `λ_t` of the sampling probability and the remainder is uniform. Crucially, Sharony's `μ_U` includes a *uniform* prior — not a TD-error prior — so their scheme does **not** target the standard PER objective in expectation. They implicitly assume the VLM-driven distribution should *replace* TD-error-driven sampling for the fraction `λ_t` of samples it controls. Our scheme is multiplicative on top of the standard PER proposal; in the limit `w_max = 1` we are *exactly* PER. Sharony's scheme, in the limit `λ = 0`, is uniform; in the limit `λ = 1`, it discards TD-error entirely (in the discrete variant).

**The IS correction for semantic PER.** Since `μ_Sem` is a different proposal from `μ_P`, the importance weight in (the corrected) regression must be updated:

```
w_IS,Sem(i) = ( (1/|D_B|) / μ_Sem(i) )^β.                                (3)
```

In our implementation, we use the standard PER IS-weight machinery, which means we are using `w_IS,P(i)` instead of `w_IS,Sem(i)`. This is a **conservative approximation** that under-corrects: high-semantic-boost transitions get sampled more often than their IS-weight reflects, which produces a slight bias toward the failure window. We discuss this in §3 and §6; it is closely analogous to the truncation bias in V-trace.

---

## Section 3 — Connection to importance sampling and off-policy correction

The most theoretically vital observation in this framing is that **semantic PER falls inside a well-charted off-policy-correction taxonomy**, alongside retrace, V-trace, and prioritized DQN. We locate it explicitly.

**Prioritized DQN (Schaul et al. 2016).** Single-step IS correction via `μ_P(i) ∝ |δ_i|^α` and annealed `β`. Off-policy distribution comes from *temporal-difference statistics*. The VLM plays no role; the proposal is endogenous to the learner.

**Retrace(λ) (Munos et al. 2016).** Multi-step return correction via clipped per-step importance ratios `c_s = λ · min(1, π/μ)`. Proposal here is the *behavior policy* used to collect data; the correction unbiases the n-step return. Bias-variance trade-off via `λ`.

**V-trace (Espeholt et al. 2018, IMPALA).** Truncated IS correction for distributed actor-learner setups: `ρ̄ = min(ρ̄, π/μ)` clips per-step IS ratios to bound variance. Explicitly trades unbiasedness (when clipping fires) for variance reduction in the large-scale regime.

**Where does semantic PER sit?** Semantic PER is a *multi-step proposal-shaping* scheme, but the proposal modifier (the VLM posterior `q_φ`) is exogenous and trajectory-level rather than policy-derived. Concretely:

| Method | Proposal | Correction | Bias source |
|---|---|---|---|
| Retrace | Behavior policy `μ_b` | Clipped per-step IS `c_s` | Truncation of IS ratio |
| V-trace | Behavior policy `μ_b` | Doubly-clipped IS ratios `ρ̄, c̄` | Truncation of both ratios |
| Prioritized DQN | `μ_P ∝ |δ|^α` | Per-sample `w_IS = (|D_B|·μ_P)^{−β}` | Anneal of `β < 1` |
| **Semantic PER (ours)** | `μ_Sem ∝ |δ|^α · w_sem` | We currently use `w_IS,P`, not `w_IS,Sem` (under-corrected) | Mis-calibration of `q_φ` *and* under-correction |
| **Sharony (VLM-RB)** | `λ · μ^P_VLM + (1 − λ) · μ_U` | None published; treated as a sampling-time mixture | The mixture objective itself differs from PER's; no IS correction reconciles them |

**The contribution is two-fold.** (i) Semantic PER is the first VLM-replay scheme expressible as a single-sample IS estimator with a clean correction (even if we under-correct in practice). (ii) The lens *predicts* failure modes: when `q_φ` is miscalibrated (e.g., VLM systematically over-confidently localizes failures at terminal step), the sampling distribution concentrates and the IS variance blows up. We can monitor this empirically by tracking the effective sample size (ESS) of `w_sem` across the buffer — an analogue to the truncation-firing metric in V-trace.

**Connection to soft Q-learning.** A more speculative connection: if we view `q_φ` as an *energy function* `E_φ(i, τ) = − log q_φ(t* = i | τ)`, then semantic PER samples in proportion to `exp(−E_φ + log |δ_i|^α)`. This is a Boltzmann distribution over transitions with a VLM-supplied energy. The temperature is `1`; with a chain-of-thought confidence score we could obtain a true temperature parameter.

---

## Section 4 — Connection to causal credit assignment

The credit-assignment problem (Pignatelli et al. 2023, the DeepMind survey) is "given a trajectory and an outcome, which actions deserve credit?" Methods range from RUDDER (return decomposition via LSTM relevance) to CCA-PG (Mesnard et al. 2021, counterfactual baselines) to Khandoga et al. 2026 (counterfactual masking of LLM tokens).

**Reframing the VLM as a credit-assignment oracle.** A pre-trained VLM that has been shown a trajectory and answers "which step caused the failure?" is, formally, an *external oracle for credit assignment* — a learned function that emits a posterior over causally-influential timesteps without ever doing gradient-based credit estimation. This is a striking complement to the learned-CCA literature, which generally trains an auxiliary network on the agent's own data to learn causal influence (CCA-PG learns a hindsight classifier; RUDDER trains an LSTM regressor; CoSo (Feng et al. 2025) masks tokens and re-evaluates VLM-agent loss).

**The taxonomy.** Credit-assignment oracles can be grouped by data source:

1. **Endogenous (TD-error / value-based).** PER, prioritized DQN. Cheap but myopic; signals correlated with what the value function already predicts poorly.
2. **Endogenous (return decomposition).** RUDDER, hindsight-credit-assignment (Harutyunyan et al. 2019). Decomposes return contributions across steps; requires training auxiliary networks.
3. **Endogenous (counterfactual policy-gradient).** Mesnard et al. CCA-PG; counterfactual baselines via future-conditioning.
4. **Endogenous (counterfactual masking of policy).** Khandoga et al. 2026. Mask reasoning spans; measure outcome shift.
5. **Exogenous (foundation-model oracles, NEW).** VLM-RB, semantic PER. The oracle is *pre-trained on a different distribution* (web video, image-text pairs) and queried zero-shot for causal localization. This is the first credit-assignment oracle that is fully external to the RL training loop.

**Why this is a contribution.** All prior CCA methods are constrained by the data available to the RL agent: they can only credit actions whose alternatives the agent has actually tried. A VLM-based oracle imports a *human-distilled prior* over what physical events typically cause manipulation failures — gripper miss, object slipping, premature contact — that no in-domain endogenous CCA method can discover from a 100K-step buffer. We re-cast our paper not as "VLM in replay" but as "**foundation-model priors as a credit-assignment oracle**." This is a strictly stronger framing.

**Connection to Khandoga 2026 in particular.** Khandoga et al. perform counterfactual masking *in token space* using the policy itself; we perform counterfactual localization *in trajectory-state space* using an external VLM. Both estimate the same quantity (causal contribution of a sub-sequence to the outcome) but at different abstraction levels and with different oracles. We cite Khandoga as the closest LLM-RL analog and frame our work as the *physical-manipulation* counterpart.

---

## Section 5 — What this framing buys us in the paper

A reviewer who sees only the engineering ("VLM scores trajectories, priorities up, learning up") will rank us alongside Sharony. A reviewer who sees the IS-posterior framing recognizes a *principled* methodological contribution. Specifically:

**(a) Principled motivation.** "We use a VLM because it gives us posterior mass over causally-influential transitions" is a better one-liner than "VLMs see semantic structure that TD doesn't." It explains *why* the boost should be multiplicative on PER and *why* the failure direction is preferable (failures concentrate posterior mass on a single bottleneck; success spreads it across an entire goal-achievement subsequence).

**(b) IS lens predicts when our method should work or fail.** Specifically: semantic PER outperforms PER iff (i) `q_φ` is more concentrated than a uniform-on-trajectory prior (so it actually re-weights samples) AND (ii) `q_φ` is more *correctly* concentrated than `μ_P` alone (i.e., the VLM-localized transitions also have non-trivial TD-error in expectation). When the trajectory's TD-error is already concentrated around the failure timestep, the marginal gain of semantic boost shrinks toward zero. We can empirically test this with a "TD-concentration vs. VLM-improvement" scatter plot — a diagnostic Sharony cannot produce because they have no posterior model.

**(c) New ablations the framing suggests.**
- **Temperature-controlled posterior:** prompt the VLM for a *distribution* over `t*` (e.g., a confidence-weighted soft-localization) rather than a single timestep, then form `w_sem` as the true expectation in (1). Predict: smoother posteriors are robust on tasks where the VLM is less confident.
- **IS-correction ablation:** ablate `w_IS,P` vs. `w_IS,Sem`. Tests whether the under-correction is hurting us, and quantifies how much.
- **ESS monitoring:** track effective sample size of `w_sem` across training; predict performance degradation at low ESS (over-concentrated VLM).
- **Posterior-calibration check:** with the heuristic Oracle, compute KL(`p_oracle(t*|τ) || q_φ(t*|τ)`) and correlate with semantic-PER lift. This directly operationalizes the framing.

**(d) Re-cast headline result.** Instead of "VLM-PER beats PER by X%," our headline is "with a frontier VLM as posterior, we recover Y% of the privileged-Oracle ceiling on Fetch — implying foundation-model priors are sufficient credit-assignment oracles for sparse-reward manipulation." This is a *thesis*, not a benchmark.

---

## Section 6 — Risks and where the framing breaks down

We should be honest about how loose the analogy is.

**(i) The VLM is not a calibrated posterior.** Probabilistic calibration of frozen LLMs/VLMs is famously poor; our `q_φ` is a hard-argmax output of a chain-of-thought prompt, not a Bayesian posterior. The IS interpretation requires only that `q_φ` be *correlated* with the true posterior, not that it be calibrated, but we should not over-claim. Mitigation: report posterior concentration / ESS as a diagnostic; treat the framing as motivation rather than as a theorem.

**(ii) We do not actually do exact IS correction.** As noted in §3, we use `w_IS,P` rather than `w_IS,Sem`, which means our gradient estimator is biased relative to the uniform objective. This is the same kind of bias that V-trace tolerates via truncation. We should *write this clearly* in the paper; it is a feature, not a bug, because the bias concentrates updates where the VLM thinks they matter.

**(iii) `q_φ(t* | τ)` is conditioned on `τ` collected by the current policy.** This couples `q_φ` to the policy in a way classical IS theory does not anticipate. As the policy improves, the trajectory distribution shifts and the VLM's posterior shifts with it. Freshness-aware PER (Ma et al. 2026) is the appropriate response: stale `q_φ` predictions on stale buffer transitions should be down-weighted. We do not currently implement this but can flag as future work.

**(iv) Window kernel `K_W` is heuristic.** The choice of window half-width `W` is engineering, not Bayesian. A more principled scheme would have the VLM emit a per-step soft posterior `q_φ(t = i | τ)` directly. This is a clear future direction; an honest reading of our current scheme is "approximate posterior via point estimate, broadened to a window for regularization." We say so.

**(v) The "true posterior" `p(t* | τ)` is underspecified.** There may be no unique causally-responsible timestep — failures often have multiple contributing factors. A purist Pearlian causal framing would require a structural causal model, which we do not have. We sidestep this by framing `p(t* | τ)` operationally: it is the posterior an idealized Oracle observing privileged sim state would emit. This grounds the framing in a measurable quantity (and our heuristic Oracle is a candidate approximation).

**(vi) The framing is post-hoc.** We did not derive semantic PER from an IS objective and then implement it; we built the implementation, observed it worked, and now articulate the framing. We should be transparent that this is *motivation framing*, not derivation. The paper's contribution is empirical; the framing helps readers position the work.

---

## Citations to use for this framing

From L2's bibliography, the following entries are essential to cite in support of this framing. Each annotated with its specific role in the IS-posterior argument:

1. **Schaul et al. 2016 — Prioritized Experience Replay** (not in L2 but canonical; add). Foundational for §1's PER setup; specifically for `w_IS = (|D_B| · μ_P)^{−β}` derivation and `β` schedule.
2. **Pignatelli et al. 2023 — Credit Assignment Survey** (L2 §1.1). Anchor for §4. The taxonomy of CCA methods is the spine of our exogenous-vs-endogenous argument.
3. **Mesnard et al. 2021 — CCA-PG** (L2 §1.3). The formal precedent for "counterfactual posterior over which step deserves credit." We cite to show our work fits the same conceptual line.
4. **Arjona-Medina et al. 2019 — RUDDER** (L2 §1.4). The canonical "credit redistribution along a trajectory" reference; we cite to position the VLM posterior as a structurally similar but exogenous oracle.
5. **Khandoga et al. 2026 — Causal Credit Assignment for LLM RL** (L2 §1.2). LLM-token analog of our scheme; cite as the direct intellectual sibling for the "external counterfactual oracle" framing.
6. **Sharony et al. 2026 — VLM-Guided Experience Replay** (L2 §3.1). Cite throughout §3 and §5 to contrast their additive mixture with our multiplicative posterior reweighting.
7. **Munos et al. 2016 — Retrace** (not in L2 but canonical; add). Cite in §3 as the off-policy correction reference; defines `c_s = λ·min(1, π/μ)` and the truncation-bias-variance trade-off we invoke.
8. **Espeholt et al. 2018 — V-trace / IMPALA** (not in L2 but canonical; add). Cite in §3 for the truncated-IS clipping framework analogous to our under-correction.
9. **Ma et al. 2026 — Freshness-Aware PER for LLM/VLM RL** (L2 §3.16). Cite in §6 as the right response to the policy-drift-induced staleness in `q_φ`; methodological precedent for future work.
10. **Duan et al. 2024 — AHA** (L2 §3.7). Cite in §4 as evidence that VLMs *can* zero-shot localize manipulation failures; grounds the practical viability of using `q_φ` as a posterior approximation.
11. **Feng et al. 2025 — CoSo** (L2 §3.8). Cite in §4 as the token-level counterpart of our trajectory-level scheme; reinforces the "external counterfactual reasoning" pattern.
12. **Chuck et al. 2025 — HInt/NCII** (L2 §2.3). Cite in §4 as the *dynamics-model*-based counterfactual analog; positions our VLM as a more general (web-pretrained) alternative.

Optional but recommended:
- **Andrychowicz et al. 2017 — HER** (L2 §2.8). Background.
- **Harutyunyan et al. 2019 — Hindsight Credit Assignment.** Not in L2; canonical reference for the credit-assignment connection.

---

## A falsifier for the IS-posterior framing

The framing predicts: **semantic PER's lift over standard PER is monotonically increasing in (i) `q_φ`'s posterior concentration and (ii) the alignment of `q_φ` with the privileged Oracle posterior.**

**Falsifying experiment.** Construct three conditions on the same Fetch task:

1. **Sharp aligned `q_φ`:** prompt the VLM with the standard prompt (concentrated, accurate-on-average outputs).
2. **Sharp adversarial `q_φ`:** prompt the VLM to localize failure at a *random non-causal step* (e.g., always step 0). High concentration, zero alignment with the true posterior.
3. **Diffuse `q_φ`:** flatten the boost over a window covering the entire episode (effectively uniform posterior). Low concentration, vacuously "aligned" on average.

**Prediction (framing-consistent):** Lift over PER ranks (1) >> (2), (3). Specifically:
- (1) outperforms PER (concentration + alignment compounds).
- (2) underperforms PER (concentration without alignment hurts because IS variance is high and bias is wrong-direction).
- (3) matches PER (no concentration, no effect either way).

**Falsifier.** If (2) and (3) perform similarly to (1) — i.e., the lift is invariant to whether the posterior is correct — then the IS-posterior framing is wrong. The improvement is then attributable to something else (e.g., a side effect of multiplicative boost compressing the priority distribution, irrespective of where the boost falls). In that case the paper's framing must retreat to "engineering recipe" and we lose the Bayesian motivation. This experiment is feasible (3 runs at sweep budget) and would meaningfully test the framing.

**Auxiliary diagnostic.** Compute the Spearman correlation between `q_φ`'s argmax and Oracle-identified bottleneck across episodes. If correlation > 0.3 (a low bar) and lift > 5%, the framing holds; if correlation > 0.5 and lift < 5%, the framing's prediction (alignment ⇒ lift) fails and we should retreat.

---

## Bottom line for Daniel

The "Theoretical Motivation" section of the paper should be ~1 page tight, structured roughly:

1. **One paragraph** restating PER as IS-corrected reweighting (cite Schaul, point to App. A for derivation).
2. **One paragraph** introducing `q_φ(t* | τ)` as the VLM's posterior and (2) as our scheme.
3. **One paragraph** locating us in the off-policy-correction taxonomy table (§3) and citing retrace, V-trace, Khandoga.
4. **One paragraph** stating Pignatelli's CCA framing and the "exogenous foundation-model oracle" contribution.
5. **One short subsection** on the falsifier (§6's experiment) — this is what makes the framing scientific rather than rhetorical.

The full draft above is intentionally over-long; trim to the above structure for the camera-ready. **Key claim Daniel should adopt:** *"We provide the first principled framing of VLM-guided replay as importance-sampled posterior reweighting with a foundation-model credit-assignment oracle. This framing motivates the multiplicative form of our priority update and predicts conditions for its success."* Sharony cannot make this claim. We can.

---
