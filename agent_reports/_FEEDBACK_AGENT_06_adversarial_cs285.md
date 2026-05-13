# Agent 06 — Adversarial CS 285 Grader

**Artifact under review:** `agent_reports/paper_cs285/main.tex` (+ `appendix.tex`), 11-page compiled PDF.
**Posture:** harshest plausible CS 285 grader. Quota of deductions, distrusts AI-aided writing, counts baselines literally, hates self-praise.
**Rubric:** 4 axes (Novelty / Scope / Analysis / Completeness), 100 pts max per axis. Final score = mean.

---

## TL;DR — Predicted scoring

| Axis | Best plausible | Worst-grader plausible | My central estimate |
|---|---:|---:|---:|
| Novelty | 92 | 70 | **80** |
| Scope | 90 | 72 | **82** |
| Analysis | 88 | 65 | **77** |
| Completeness | 94 | 78 | **86** |
| **Mean** | 91 | 71 | **~81 (high Good, not Excellent)** |

**Central thesis of this grader:** the paper reads as a workshop submission in voice but fails one Excellent-tier requirement: the headline claim — "Verified-CF matches VLM-CF and wins on Slide" — is supported by **n=3 seeds at 500k steps** without paired SE testing, without the canonical 4.75M-step horizon, and **without a head-to-head against the closest published work (VLM-RB), which the authors explicitly note is "pre-staged" but not run**. Several "contributions" are framing exercises layered on top of an honestly-killed experiment. A grader looking to mark down has rich material.

**Total predicted point losses (worst-realistic grader, summed before axis normalization):** **~52 points** across all four axes.

---

## Deductions by axis

### Novelty deductions (target axis cap: 100; estimated loss ~20)

- **L34–48 (Extended Abstract, Problem para) — overclaim "the multiplicative form is the principled choice"** [-3 pts, Novelty].
  This is asserted, not proven. The "principled" defense in §3.1 P1 is that PER's IS weight remains analyzable; the proof sketch (App B) shows a bounded bias under the *under-corrected* implementation, not that additive is unprincipled. "Principled" + italic *multiplicative* reads as marketing on first contact.

- **L193–196 "To our knowledge this paper is the first to use a VLM-localized failure timestep as a credit-assignment signal and to verify counterfactual relabels in the same simulator on which the policy trains"** [-3 pts, Novelty].
  Two clauses ANDed together — the conjunction is true by construction, but each clause has close precedent: Pignatelli et al. 2024 (FM-as-credit-oracle) and Chuck et al. 2025 / Lei et al. 2025 (verification-step counterfactual relabel). A skeptical grader reads "first to X *and* Y" as carving a niche by intersection and discounts the novelty claim.

- **L176–196 Differentiation from VLM-RB rests on a method we did not run** [-4 pts, Novelty].
  The "first" claim above is also undercut by the explicit admission in App E (L246–250): "A faithful VLM-RB reproduction ... is pre-staged ... for camera-ready head-to-head evaluation." Translation: we have not actually compared against the closest published work. A grader on the novelty axis will read this as "you redefined novelty as 'theirs is additive, ours is multiplicative' and let that adjective do the work."

- **L121–139 Contribution (1) reframes existing PER as IS-posterior reweighting** [-3 pts, Novelty].
  PER is *already* an importance-sampled estimator (Schaul 2016, §3.4 cited in the appendix). Calling the VLM weight a "posterior approximation $q_\phi(t^\star \mid \tau)$" and the product a "proposal" is a vocabulary swap. The accompanying bias bound (App B, Eq. 2) is a textbook application of bounded-likelihood-ratio IS — no new analysis technique.

- **L140–149 Contribution (3) "Empirical analysis: prompt design, VLM-family robustness, cross-task transfer"** [-2 pts, Novelty].
  Three loosely-related sweeps presented as a single named contribution. None is intrinsically novel; an adversarial grader will count this as "we ran ablations" rather than a contribution worth a bullet.

- **L260–280 Teleport-collapse "failure mode" framing** [-2 pts, Novelty].
  The phenomenon (VLM copying coordinates from the prompt) is well-known prompt-engineering folklore. Naming it "teleport-collapse" and dressing it as a Dirac on a goal distribution is rhetorically tidy but adds no analytical machinery beyond saying "don't show the VLM the answer." A grader who has read 2024–25 LLM-grounding papers will discount the framing.

- **L154–155 "Honest pre-registered negative result"** [-3 pts, Novelty].
  Negative results from killed experiments do not, on their own, supply novelty. The bullet is rhetorically clever — turning a failed Path C into a "headroom bound" — but a grader will note that the bound is task-family-specific (acknowledged at L495), demonstrated only via one ΔPickAndPlace = −0.05 cell at 250k steps, and not generalized.

### Scope deductions (target axis cap: 100; estimated loss ~18)

- **No Sharony VLM-RB head-to-head run** [-5 pts, Scope].
  App E (L246–250) admits the VLM-RB reproduction is "pre-staged ... for camera-ready head-to-head." That is the single comparison the paper most needs, and it is missing. A grader will dock heavily because the entire Related Work section pivots on "we differ from VLM-RB in two ways" — the reader has no quantitative ammunition for that claim.

- **n=3 seeds is the bare minimum for "workshop scope"** [-3 pts, Scope].
  Modern RL workshops effectively expect n=5 or paired statistics. L185–187 (App D) admits the test is `t` with 2 d.f. A skeptical grader will note that confidence intervals on n=3 are too wide to declare "ties within noise" credibly (e.g., verified_cf PickAndPlace = 0.35 ± 0.10 vs. vlm_cf 0.367 ± 0.08 — the SE bars overlap massively and the "tie" is statistically vacuous).

- **500k-step budget vs. canonical 4.75M Fetch horizon** [-3 pts, Scope].
  L336–341 acknowledges this (good), but the rhetorical framing "within-horizon comparisons are statistically meaningful" hides the bigger issue: NONE of the verified_cf bars reach the canonical horizon. A grader who wants to be rough will say "you didn't actually finish the training; you compared a partially-trained method to a fully-trained baseline and called the gap a contribution."

- **Cross-horizon bars in fig:headline mix 250k / 500k / 1M / 3M training budgets in one chart** [-3 pts, Scope].
  Even with the italic gray stamp under each bar (L350–353), the visual impression is that verified_cf "beats PER" on Push — but PER is at 3M and verified_cf is at 500k. The chart is honest in caption but misleading at glance. A "wants to mark down" grader will call this a fairness violation.

- **No paired-seed analysis or learning-curve figure in main body** [-2 pts, Scope].
  All comparisons are final-evaluation bars. A workshop paper would also show learning curves so the reader can see *when* verified_cf pulls ahead. The cold-start regime (§5 L465–485) deserves a curve, not just narrative — and the omission is suspicious given the regime is called "load-bearing."

- **No AntMaze / Adroit run despite §5 calling it out** [-2 pts, Scope].
  L495–497: "We pre-register an extension to harder task families." A grader views "pre-register" as a synonym for "did not run."

### Analysis deductions (target axis cap: 100; estimated loss ~23 — biggest hit)

- **Only one paired baseline + ours at 500k** [-5 pts, Analysis].
  The rubric Excellent column reads "Compares with several baselines and ablations." At 500k steps, the *paired* methods are: vlm_cf, verified_cf. Every other bar (Uniform, PER, HER, Oracle-CF) is at a different horizon. So the matched-horizon comparison reduces to "our two variants tied each other." A grader who counts literally will say: "you cited HER, PER, Uniform, Oracle-CF, VLM-RB, and Sharony — but you ran exactly two methods at your headline horizon."

- **Table 1 prompt analysis has n=2 cell** [-3 pts, Analysis].
  L421: ALL × Opus 4.7 row has n=2. The teleport-collapse rate is reported as "2/2 (100%)" — statistically meaningless, and adversely interacts with the bolded claim that "the failure is prompt-architectural, not model-specific." A grader will flag the n=2 cell as not even pretending to be evidence.

- **Asymmetric n across Table 1 rows (n=2, 4, 4, 4, 4, 6, 6, 6, 6)** [-2 pts, Analysis].
  No explanation given for the asymmetry. Adversarial reading: synthetic episodes were re-used selectively after early runs, then GPT-4o got a fresh n=6. A grader will demand explanation; the table caption gives none.

- **"Strictly-dominating configuration" claim on L144 and L389** [-3 pts, Analysis].
  Strictly dominating in what partial order? GPT-4o has higher plausibility (0.79) on achieved_goal but LOWER goal-progress (0.83) than Opus (0.97). Strict dominance requires ≥ on all axes and > on one. With Opus winning goal-progress, the claim is technically false unless "strictly dominate" excludes the literal-goal-copying axis — but excluding the failure mode by definition is circular. A grader who reads carefully will catch this.

- **No ablation of the verifier itself** [-3 pts, Analysis].
  §3.3 introduces the simulator-verification gate. The natural ablation is: what happens if we admit *all* VLM-proposed counterfactuals without verifying? Or with a relaxed acceptance threshold $r \ge -\rho_r$ (L484 mentions this but says "not run")? Without that ablation, the "verifier is doing the work" claim is not isolated from "the VLM is doing the work."

- **No ablation of multiplicative-vs-additive within our own setup** [-3 pts, Analysis].
  The paper argues the multiplicative form is principled. The natural test: run our Semantic-PER additively and show it underperforms. Not present. A grader will say: "you argue against an architecture you didn't run, citing only a paper you also didn't reproduce."

- **p_counterfactual sweep mentioned in contributions (L535) but not shown** [-2 pts, Analysis].
  Daniel's contribution bullet credits him with "the p_counterfactual sweep" but this ablation is nowhere in the main body or appendix. A grader will note the discrepancy: claimed work not visible.

- **"Bias bound" Eq. 2 (App B) numerical example gives ~1.98·C·||ℓ||∞** [-2 pts, Analysis].
  The bound is technically valid but the worked example shows the bias multiplier is ~2× — not a tight bound, just a finite one. The TD-error magnitude ||ℓ||∞ in goal-conditioned sparse-reward settings can be on the order of 1/(1−γ) ≈ 50, so the realized bound is potentially huge. A grader will read this as a meaningless guarantee and dock for "analytical-looking but vacuous."

### Completeness deductions (target axis cap: 100; estimated loss ~14)

- **Sharony VLM-RB pre-staged but not run + Daniel claims it in contributions** [-4 pts, Completeness].
  L536–537 contributions bullet: "Sharony VLM-RB reproduction." L508 main body: "pre-staged in our codebase for camera-ready head-to-head evaluation." L246–250 appendix: same. This is the strongest deduction the grader can apply — a contribution-claim that contradicts the main body. Either Daniel ran it or he didn't. If he did, where's the bar? If he didn't, why is it in his contributions list?

- **Cold-start regime (load-bearing!) reported on a single seed** [-3 pts, Completeness].
  L473–476: "Our FetchPickAndPlace seed 42 hit a 100% verifier-rejection rate over the first ~80 VLM calls." Why only seed 42? Did seeds 123 and 999 not show this? The regime is labeled "load-bearing limitation" but the empirical evidence for it is n=1. A grader will deduct here AND on the Analysis axis.

- **"4/4 smoke test" (L298–304) is a unit test, not an experiment** [-2 pts, Completeness].
  Reporting a 4/4 smoke test in the main body as evidence the verifier works is a category error: smoke tests confirm code correctness, not method efficacy. A grader who wants to be unkind will say "you reported your CI green light as a result."

- **Oracle-CF kill experiment has post-hoc 1M-step rerun on PickAndPlace only** [-2 pts, Completeness].
  L454–460: "Post-hoc 1M runs on PickAndPlace ... tie exactly." Why only PickAndPlace? If the 250k kill is task-specific, the 1M re-test should be on all three tasks. Reporting only the one that ties looks like cherry-picking the most charitable retraction.

- **Reproducibility checklist not in paper** [-2 pts, Completeness].
  App E (L240) says "reproducibility checklist ... released at GitHub." The standard expectation is the checklist is *in* the paper, not behind a URL. A grader will dock for "checklist offshored."

- **Bibliography has stale arXiv preprints from 2026 with format `2603.xxxxx`** [-1 pt, Completeness].
  L24 of refs: `arXiv:2603.21357` (AgentHER) — that ID format is suspicious for an arXiv paper. A skeptical grader will spot-check one of these and either find it doesn't exist or note that the arXiv ID is wrong-format. Also potentially looks AI-generated.

### Other deductions (cross-axis or unallocated)

- **Self-promotion vocabulary: "principled" ×4, "clean IS-correction" ×2, "strictly-dominating," "load-bearing," "substantively original" (implicit from the rubric file)** [-2 pts spread across Novelty/Analysis].
  L47, L54, L124, L513–514 all say "principled" or "admits a clean IS-correction." Repeated self-evaluation. A grader trained on NeurIPS reviewing norms will mentally subtract.

- **"Honest negative" phrasing repeated** [-1 pt, distributed].
  "Honest pre-registered negative result" (L151), "Honest negative and roadmap" (L83), "Pre-registered kill verdict, honored" (L72). Repeating "honest" three times reads as protesting too much.

- **Underfull/overfull boxes in the build log** [-1 pt, Completeness].
  L1: "Overfull \hbox (20.85347pt too wide) in paragraph at lines 110–143" (refs.bib). Multiple underfull \hbox at line 19–20 (probably the email line). Minor but suggests the LaTeX wasn't given a final polish pass.

- **Author affiliation block is generic ("Department of EECS")** [-0 pts, but: grader sees it as un-NeurIPS-y].

- **No PER asymptote citation page number for Plappert 2018** [-1 pt, Completeness].
  L363: "matching the PER@3M asymptote (~0.95,~\citealp{plappert2018multigoal})." A grader will want to verify the asymptote and finding it requires reading the entire Plappert benchmark paper. Page or figure number expected.

- **Contributions section is unequal** [-1 pt, soft-deduction, social].
  Daniel's bullet has ~8 clauses; Parshawn's and Matei's have 2 and 1 respectively. Adversarial reading: this is a Daniel-solo paper with two co-authors listed. CS 285 graders are sensitive to this (the rubric specifically calls for "1 line per member"); the imbalance signals either honest reporting or under-utilization.

---

## Top-10 most likely point losses

1. **No head-to-head with VLM-RB (Sharony 2026), the closest published work** [-5 pts] — Run the pre-staged reproduction overnight. Even n=1 seed on Push would partially close this; n=3 would close it fully.
2. **n=3 with overlapping SE bars and "ties" language** [-4 pts] — Add a paired-seed bootstrap; report 95% CIs explicitly; soften "tied" to "indistinguishable at n=3."
3. **Sharony VLM-RB reproduction claimed in contributions but not run** [-4 pts] — Either drop the bullet from Daniel's contributions, or run the reproduction.
4. **No verifier ablation (no-verify, soft-accept)** [-3 pts] — Run one seed with the gate disabled; report acceptance-rate-vs-success.
5. **No multiplicative-vs-additive ablation within our own framework** [-3 pts] — Run Semantic-PER additively at 250k on Push for one seed.
6. **"Strictly-dominating configuration" is partial-order-false** [-3 pts] — Replace "strictly-dominating" with "best non-degenerate" or list the explicit axes.
7. **Table 1 has n=2 cell and asymmetric n across rows** [-3 pts] — Either drop the n=2 row or top it up; add a footnote explaining n asymmetry.
8. **Cold-start regime evidence is n=1 (seed 42 only)** [-3 pts] — Report verifier-rejection trajectory on all 3 seeds; current single-seed claim is brittle.
9. **Cross-horizon bars in fig:headline mislead at glance** [-3 pts] — Either split into matched-horizon panels or add a visual cue (hatched fill) for non-matched bars.
10. **Bias bound (Eq. 2) is finite but vacuous in practice** [-2 pts] — Either compute the realized bound on a real run or move the proof entirely to appendix and stop calling it a "guarantee."

---

## Best counter-argument if Daniel disputes

**For #1 (no VLM-RB head-to-head):**
> "VLM-RB on Fetch is out-of-distribution; their published results are on MiniGrid/OGBench. Reproducing without their PerceptionLM-1B model adds a substitution variable (Sonnet 4.5) that makes the comparison non-faithful anyway, so the qualitative differentiation argument (additive vs multiplicative) is the load-bearing claim, and the 250k Oracle-CF kill already bounds the headroom for ANY VLM-in-replay method including theirs."
> **Grader rebuttal:** The headroom-bounding argument is task-specific. Also: you didn't have to use their model; you could have run their priority formula with your VLM and ours, both at 250k. That's the apples-to-apples comparison.

**For #2 (n=3 stats):**
> "We explicitly report n=3 SE intervals and use the non-overlapping-SE conservative criterion (App D L188). The Clopper-Pearson on the 0/6 vs 4/4 prompt result IS rigorous; the headline 'tie' is qualified by Δ=-0.016."
> **Grader rebuttal:** Non-overlapping SE is not a 95% CI criterion (it's roughly 84%). The "tie" claim should be a Bayes factor or equivalence test, not a delta.

**For #3 (Sharony in contributions):**
> "Daniel built the reproduction infrastructure; the absence of run results doesn't negate the engineering contribution."
> **Grader rebuttal:** Then list "infrastructure" not "reproduction" — those are different deliverables. Current wording is misleading.

**For #6 ("strictly-dominating"):**
> "Strictly dominating in the goal-information-free sense: GPT-4o achieved_goal has 0% teleport and competitive plausibility, while Opus achieved_goal's higher goal-progress is achieved by goal-copying, which is the degenerate case we exclude."
> **Grader rebuttal:** Then say "non-degenerately dominating" or define a partial order in the table caption. "Strictly" is a strong word; carry the cost or change the word.

**For #8 (cold-start n=1):**
> "FetchPickAndPlace seed 42 is the exemplar; the other two seeds show qualitatively similar but less extreme rejection profiles, reported on the GitHub W&B dashboard."
> **Grader rebuttal:** Then put the all-three-seeds plot in the appendix. Offshoring to W&B is exactly the move the rubric file flags as a Completeness hit.

---

## Bottom-line scoring prediction

A typical "mark-down quota" CS 285 grader, applying the rubric strictly, lands at:

- **Novelty: 80–85** (Good, not Excellent — "modifications" with re-framing rather than "substantively original")
- **Scope: 82–87** (Good — workshop-paper-shaped, but the VLM-RB head-to-head gap holds it back)
- **Analysis: 75–82** (Good — multiple baselines cited, but the matched-horizon baseline set is thin; ablations are partial)
- **Completeness: 85–90** (Good→Excellent — all reported numbers are reported, but several contribution-bullets exceed the run set)

**Predicted mean: 80–86. The paper is solidly Good. To break into Excellent (90+) it needs the VLM-RB head-to-head, a verifier ablation, and a cold-start regime plot on all three seeds.**

The "honest negative" framing is genuinely the paper's strongest move on the Novelty axis and might pull a sympathetic grader up by 3–5 points. A hostile grader will not adjust.

---

## File paths referenced

- `/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/paper_cs285/main.tex` (556 lines)
- `/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/paper_cs285/appendix.tex` (250 lines)
- `/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/paper_cs285/main.pdf` (11 pages, 716 KB)
- `/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/_GRADER_REFERENCE.md` (rubric source)
