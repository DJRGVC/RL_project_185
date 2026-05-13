# Agent 07 — Adversarial NeurIPS Reviewer

**Paper:** "VLM-Verified Counterfactual Hindsight for Sparse-Reward Manipulation"
**Reviewer disposition:** hostile area chair, methodological-rigor lens.
**Recommendation in advance:** Reject — the paper's load-bearing claims are
empirically fragile, comparison-frame-dependent, and the differentiation from
Sharony et al. (2026) is more rhetorical than demonstrated.

---

## Summary

The authors recast VLM-guided prioritized experience replay as
importance-sampled posterior reweighting (Semantic PER), introduce a
simulator-verified counterfactual-hindsight channel that replaces a
language-only "achieved-goal" prompt with a "corrective action sequence"
verified in a forked simulator, and report that verified-CF ties their
unverified vlm_cf baseline at 500k steps across three Fetch tasks while
exceeding it on FetchSlide; a pre-registered Oracle-CF kill threshold on
FetchPickAndPlace was violated and the headline was pivoted accordingly.

---

## Strengths

- **S1. Pre-registration with an honored kill.** Section 4.4 reports a
  negative result on the originally-planned headline (Oracle-CF at 250k on
  PickAndPlace, $\Delta=-0.05$ vs. the $+0.10$ pre-registered threshold)
  and pivots transparently. This is rare and laudable; it is the single
  strongest signal that the paper is not p-hacked.
- **S2. The "teleport-collapse" diagnosis is sharp.** The 0/6 vs. 4/4
  contrast on (GPT-4o, `achieved_goal`) vs. (Opus, `achieved_goal`) is a
  judge-independent, predicate-decided result with disjoint
  Clopper–Pearson intervals. The framing of it as
  *prompt-architectural* rather than *model-specific* is a real, falsifiable
  hypothesis that the cross-vendor data largely supports.
- **S3. The generator–verifier construction is conceptually clean.** Asking
  for an action sequence rather than a hindsight goal and verifying in the
  exact training simulator is a sound move: it neutralizes the dominant
  failure mode "by construction" and preserves off-policy correctness by
  using the env's own sparse reward. The 17.6 ms / 0.4% overhead claim is
  credible.
- **S4. Honest discussion of the cold-start verifier-rejection regime.**
  The 100% rejection rate over the first ~80 calls on PickAndPlace seed 42
  is disclosed up front (§5) rather than buried, and is correctly framed
  as the asymmetric "throughput dial" failure mode of the verifier.
- **S5. The multiplicative-vs-additive distinction is the right axis.**
  Whether or not the empirical case is fully made, the theoretical
  observation that the additive Sharony mixture retargets the loss to a
  $\lambda$-weighted objective is correct and worth stating.

---

## Weaknesses (the meat)

### W1. **n = 3 seeds, with seed-spreads that swallow every headline claim.**
The paper's own numbers undermine its statistical confidence:

- The body explicitly reports HER@1M on FetchPickAndPlace as seeds
  $\{0.35, 0.45, 0.95\}$ (§4.4), a **60-point intra-condition spread**.
  With $n=3$ and that variance, the standard error is ~0.18 and the 95%
  $t$-interval is roughly $\pm 0.78$ — effectively spanning the entire
  $[0,1]$ outcome space.
- FetchPush verified-CF is reported as $0.85 \pm 0.14$ — the SE is
  comparable to the entire claimed gap over HER@250k for half the runs.
- FetchSlide verified-CF "wins" at $0.617 \pm 0.03$ vs. vlm_cf
  $0.55 \pm 0.13$. The two SE intervals **overlap**; the appendix's own
  declared "non-overlapping SE" decision rule (§B.3) is not met, yet the
  paper claims a Slide win in the abstract, intro, headline, and
  conclusion. This is a self-inconsistency.
- The pre-registered kill threshold ($\Delta \ge 0.10$) is itself
  $\sim 0.6\sigma$ at the observed variance — the kill decision was made
  on a statistic with no power to detect a true effect of the threshold
  magnitude. With $n=3$ I cannot tell whether Oracle-CF is actually
  $\Delta=-0.05$ or $+0.20$; the "headroom bound" claim
  (§5, §4.4) is not licensed by the data.

The paper acknowledges small-$n$ in passing ("we pre-register $n \ge 30$
replications") but proceeds to draw quantitative headline claims as
though the variance had been controlled. **n=3 is below the floor for
RL-with-stochastic-envs claims at NeurIPS 2024–26.** Agarwal et al.
(2021, "Deep RL at the edge of the statistical precipice") is the
relevant reference and is not cited.

### W2. **Comparison-frame asymmetries are doing the heavy lifting.**
Figure 1 (and the whole headline) explicitly mixes training horizons:
Uniform/PER at 3M, HER at 250k, vlm_cf/verified-CF at 500k, Oracle-CF at
250k or 1M. The authors flag this with an italic stamp and call it an
"efficiency claim," but the abstract and intro then read it as a
dominance claim ("exceeds it on FetchSlide … +0.45 over PER@3M, +0.43
over HER@250k"). Two specific concerns:

- (a) The fair comparator for vlm_cf@500k is HER@500k, not HER@250k or
  PER@3M. The paper's own §4.4 post-hoc HER@1M number on PickAndPlace
  is $0.583$ — **identical to Oracle-CF@1M ($0.583$)**, and well above
  vlm_cf@500k ($0.367$). The natural read is "HER catches up given equal
  budget"; the paper instead reports "vlm_cf reaches 63% of HER@1M at
  half the budget." Same numbers, opposite spin.
- (b) The PER@3M Slide number of $0.10$ is from a "prior 36-run ablation
  suite" not described in this paper. I cannot verify the protocol,
  hyperparameters, or seed counts of that suite from this manuscript;
  the +0.45 Slide gain over PER@3M therefore rests on a comparator
  whose provenance is outside the paper.
- (c) No HER@500k bars appear in Figure 1. This is the single most
  important missing comparator.

### W3. **Differentiation from Sharony 2026 is rhetorical, not empirical.**
The Related Work bills VLM-RB as "the closest published work" and the
introduction emphasizes the multiplicative-vs-additive distinction. But:

- **No head-to-head Sharony comparison is run.** The appendix says the
  reproduction "is pre-staged at `src/buffers/vlm_rb_buffer.py` for
  camera-ready head-to-head evaluation." A NeurIPS submission claiming
  to improve on a concurrent method should ship that head-to-head, not
  pre-stage it.
- The multiplicative-vs-additive bias-bound argument is non-trivial
  (Appendix B) but the bound $\le 1.98 C \|\ell\|_\infty$ at default
  parameters is **vacuous unless $C$ is given numerically**. The proof
  sketch leaves $C$ as "a constant depending on $|\mathcal{D}_B|$ and
  the PER normalization." For a 1M-slot buffer with PER normalizers,
  $C$ can easily be $\mathcal{O}(1)$ or $\mathcal{O}(10^{-3})$; the
  bound is uninformative without an explicit constant. The "full proof"
  is deferred to a GitHub URL — a NeurIPS proof should live in the
  appendix.
- The "Sharony retargets the loss to a $\lambda$-weighted objective"
  observation is correct but the practical consequence is not
  demonstrated. Does the loss retargeting hurt? On what? Show me an
  experiment.

### W4. **The IS-pairing bias-bound argument is informal.**
Appendix B is a "proof sketch" that elides several steps:

- The bound is derived for a "trajectory-conditional $w_{\text{sem}}$
  that factors and cancels in the normalized expectation," but the
  cancellation requires $w_{\text{sem}}$ to be independent of the
  sampled slot conditional on the trajectory — which is true for a fixed
  $q_\phi$ but **not** when $q_\phi$ is itself a function of the slot
  through the window kernel.
- The constant $C$ is unspecified.
- The "window-kernel structure confines support to $2W+1$ slots out of
  $T$" assumes a single $t^\star$; if $q_\phi$ has mass on multiple
  timesteps the support is larger and the bound loosens.
- The "V-trace specialization" is referenced but not derived.

For a paper whose principled-choice argument rests on this bound, the
proof must be tight, in-appendix, and with named constants.

### W5. **Reproducibility claims are gestural.**
The GitHub repo is referenced repeatedly (commit `0fa36fc`), with W&B
run IDs and `REPRODUCE.md` promised. But the manuscript itself:

- Defers full hyperparameter tables ("Full per-table breakdowns … at the
  GitHub repo") instead of putting them in the appendix.
- Defers the bias-bound proof to the repo.
- Defers per-seed eval traces to the repo.
- Defers the Sharony reproduction to the repo.

The NeurIPS reproducibility checklist asks the appendix to be
self-contained. As written, a reader without GitHub access cannot
reconstruct Semantic-PER, the verifier protocol, or the prompt-variant
texts. The hyperparameter table that *is* included (Table 4) is partial
(no VLM call hyperparameters, no exact prompt token counts, no judge
calibration data, no Sonnet 4.5 model version string).

### W6. **Cherry-picking concern: the Slide win is a single seed-cohort.**
Slide is the only environment where verified-CF claims a real gain. But:

- The standard-error overlap (W1) means I cannot rule out that the
  $0.617$ Slide number is a 3-seed lucky draw.
- HER@250k on Slide is reported as $0.183$ (§4.1) and as $0.100$ in the
  kill-experiment description (§4.4) — **two different numbers for what
  ought to be the same comparator**. (One is "from the kill experiment";
  the other is the figure baseline. Which is the truth? The paper does
  not say.)
- The "$+0.45$ over PER@3M" depends on the unaudited 36-run suite (W2c).
- Slide is also the environment with the smallest sample (Push and PnP
  appear with 1M ablation runs in §4.4; Slide does not get the same
  treatment).

If the Slide win evaporated under more seeds, the paper's empirical
contribution would reduce to "ties at 500k on Push and PnP, with
verifier-rejection cold-start cost," which is a much weaker claim than
the one in the abstract.

### W7. **VLM brittleness only partially addressed.**
The cross-vendor bake-off (Opus, GPT-4o, Sonnet) is real and useful, but:

- All three are commercial frontier closed-source models. There is no
  open-weights comparator (LLaVA, InternVL, Qwen-VL), so the
  "prompt-architectural, not model-specific" claim is restricted to
  models that share post-training conventions and RLHF lineage.
- The choice of *production* VLM is GPT-4o (Table 4), but the training
  runs use Opus 4.7 (per intro: "100% of Claude Opus 4.7 calls on
  FetchPush"). It is unclear which VLM actually produced the
  vlm_cf/verified-CF buffers. If verified-CF uses Opus and the
  bake-off shows Opus is the worst on `achieved_goal`, then the
  verified-CF result is downstream of the worst tested VLM — which is
  either a positive (robustness story) or a confound (the verifier may
  be compensating for a weak generator). The paper does not disentangle.
- The "12/12 cross-task pilot" is celebrated, but the appendix concedes
  "the 12/12 cross-task is not statistically distinguishable from an
  80% true rate." Then it should not be billed as 12/12 in the abstract.

### W8. **Asymptote / Plappert.**
Plappert et al. 2018 report HER on FetchPickAndPlace converging in the
4.75M-step regime. The paper's own §4.4 post-hoc 1M runs show HER
reaching $0.583$, **equal to Oracle-CF@1M**, on PickAndPlace. There is
**no evidence in this paper that verified-CF beats HER asymptotically**;
the empirical case is entirely a sample-efficiency claim in the regime
where HER has not yet converged. This is fine for what it is, but the
abstract's "verified-CF matches VLM-CF in aggregate, wins on Slide"
elides the question of whether either method matters past 1M steps. A
single 5M Slide run for HER would settle this.

### W9. **Author contributions raise eyebrows.**
The Contributions section reads like a single-author paper:
"Daniel Grant. Led the research direction … implemented and ran all
Phase 1/2 training experiments … authored the IS-posterior theoretical
framing and bias bound … produced all paper figures and the
manuscript." The other two authors are credited with "initial project
scoping," "prior pipeline development," and "the ablation infrastructure
underlying the Phase 1 / Phase 2 experiments." For a 3-person CS 285
final project this may be honest, but it raises questions about
internal review and second-eye verification of the load-bearing
analyses (bias bound, kill-experiment statistics, seed-overlap analysis).
NeurIPS does not require multiple authors, but the single-implementer
profile compounds the small-$n$ and missing head-to-head concerns.

### W10. **The "structurally inexpressible failure mode" claim is over-stated.**
The paper says "a four-vector action cannot teleport a 50 g block by
50 cm under MuJoCo dynamics; the failure mode is structurally
inexpressible." This is true for *teleport*. It is **not** true for
other forms of degenerate output: an all-zeros action sequence is a
no-op that the verifier will reject (good), but a sequence of small
random actions is *not* a counterfactual in any meaningful sense and
will also be rejected, contributing only to the cold-start regime.
The verifier closes the teleport loophole but does not guarantee
*useful* counterfactuals; it only guarantees that accepted CFs are
sparse-reward-positive. The framing conflates two things.

---

## Questions for authors

- **Q1.** Please report HER@500k on all three Fetch tasks alongside
  vlm_cf@500k and verified-CF@500k, ideally with $n \ge 5$ seeds and
  bootstrap CIs (Agarwal 2021 protocol). Does the verified-CF Slide
  win survive a fair-budget HER comparator?
- **Q2.** Resolve the $0.183$ vs. $0.100$ discrepancy for HER@250k on
  FetchSlide between §4.1 and §4.4.
- **Q3.** Which VLM (Opus, GPT-4o, Sonnet) was used to generate the
  vlm_cf and verified-CF buffers for the training runs in §4.1? If
  Opus, why was Opus chosen given its 100% teleport-collapse rate on
  `achieved_goal`? If GPT-4o, why is the cited rate "100% of Claude
  Opus 4.7 calls"?
- **Q4.** Please provide the explicit numerical value of the constant
  $C$ in the bias bound (Eq. 4) at your default settings, and a full
  proof in the appendix rather than a sketch with a GitHub link.
- **Q5.** What is the variance of the seed spread on FetchPush
  verified-CF ($\pm 0.14$) and FetchPickAndPlace verified-CF
  ($\pm 0.10$)? Bootstrap 95% CIs please, and a statement of whether
  the Slide win survives a Welch's $t$-test at $\alpha = 0.05$ against
  vlm_cf@500k.
- **Q6.** Where is the head-to-head with Sharony VLM-RB? If the
  reproduction code is "pre-staged," what is the holdup on running it
  before submission? A camera-ready promise is not a NeurIPS-grade
  comparison.
- **Q7.** Plappert et al. report HER convergence on FetchPickAndPlace
  near 4.75M steps with success ~ 1.0. Your post-hoc HER@1M is 0.583.
  Where does HER cross 0.9 in your setup? Please run one HER seed to
  5M on PickAndPlace (or cite a faithful replication).
- **Q8.** The "100% verifier-rejection over the first ~80 VLM calls"
  cold-start cost is asymmetric and unbounded (per the paper's own
  language). What is the expected total $ cost of the verified-CF
  channel for a 5M-step Fetch run, and is the cost-adjusted
  sample-efficiency claim still positive?
- **Q9.** The cross-task transfer "12/12 task-relevance" uses Opus 4.7
  as the *judge*. What is the judge calibration? Has any other
  evaluator (human, second VLM family) confirmed the 12/12 figure?
- **Q10.** Why no open-weights VLM (LLaVA, Qwen-VL, InternVL) in the
  bake-off? The "prompt-architectural, not model-specific" claim
  cannot hold cross-modality without an open-weights data point.

---

## Scores

- **Soundness:** 2 / 5
  *Theoretical bound is informal with an unnamed constant; empirical
  comparisons are at heterogeneous horizons; $n = 3$ throughout with
  variance that swallows the claimed effects.*
- **Presentation:** 4 / 5
  *Genuinely well-written. The teleport-collapse story is sharp, the
  pre-registration framing is clean, the limitations section is honest.
  Loses a point for the §4.1/§4.4 HER-Slide number inconsistency and
  the deferred-to-GitHub appendix material.*
- **Contribution:** 2 / 5
  *The IS-posterior framing and the verifier protocol are real
  conceptual contributions. The empirical evidence does not yet
  substantiate the claim that the contributions matter — no head-to-head
  with Sharony, no asymptotic comparison to HER, no fair-budget HER
  baseline.*
- **Confidence:** 4 / 5
  *I have read the manuscript end-to-end and verified the load-bearing
  numerical claims against the paper's own tables. I have not run the
  GitHub code.*
- **Verdict:** **Reject** (would be Borderline-Reject in a more
  forgiving venue).

---

## What would change my mind from Reject to Borderline?

- **B1.** Run HER@500k on all three Fetch envs with $n \ge 5$ seeds,
  report bootstrap 95% CIs (Agarwal 2021), and show that the Slide gain
  for verified-CF survives. If the Slide win is real at fair budget
  with adequate seeds, the empirical case is on its feet.
- **B2.** Resolve the §4.1 vs §4.4 HER-Slide numeric inconsistency in
  one direction. Pick a number, justify it, recompute the headline.
- **B3.** Either (a) move the bias-bound proof in-paper with a named
  numerical constant, or (b) downgrade "principled choice" language to
  "we observe empirically that ..." in the intro and method.
- **B4.** Run the staged Sharony VLM-RB reproduction on at least one
  Fetch env. Even a single-env, $n=3$ head-to-head would address W3.

## What would change my mind from Borderline to Accept?

- **A1.** $n \ge 5$ seeds across all (method, env) cells, with
  preregistered protocols and bootstrap CIs reported in the headline
  figure. Eliminate the heterogeneous-horizon comparison frame; report
  matched-budget bars first and label efficiency claims as secondary.
- **A2.** Full Sharony VLM-RB head-to-head on all three Fetch envs at
  matched horizons, ideally with an apples-to-apples MiniGrid or
  OGBench data point to land the cross-task claim in their setting.
- **A3.** Open-weights VLM in the bake-off (e.g., LLaVA-Next or
  InternVL) demonstrating that teleport-collapse is genuinely
  prompt-architectural across the open/closed boundary.
- **A4.** At least one task family beyond Fetch — the paper's own §5
  acknowledgement that Fetch is "HER-friendly" implies the headroom
  bound may not generalize. AntMaze or Adroit (pre-registered in the
  limitations) at even small-$n$ would substantially strengthen the
  contribution.
- **A5.** A full bias-bound proof with named constants, the V-trace
  specialization derivation, and a single-figure ablation comparing
  $w_{\text{IS},P}$ (under-corrected) vs $w_{\text{IS},\text{Sem}}$
  (strictly correct) to demonstrate the bias is actually negligible
  in practice.

---

*Reviewer 07 — adversarial methodological-rigor pass. The paper has a
nice idea, an honest negative result, and clean writing; it does not
yet have NeurIPS-grade empirical evidence to support its headline
claims.*
