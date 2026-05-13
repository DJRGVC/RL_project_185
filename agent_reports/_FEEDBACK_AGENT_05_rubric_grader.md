# Agent 05 — Strict Rubric Grader

**Artifact graded:** `/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/paper_cs285/main.tex` (rendered: `paper_cs285/main.pdf`, 11pp, ExtAbs fits page 1 cleanly, no undefined refs)
**Rubric source:** `agent_reports/_GRADER_REFERENCE.md` (verbatim 4-axis matrix from CS 285 outline)
**Grader stance:** Maximally harsh / worst-case-grader simulation. No charity reads.

---

## Final predicted grade: **89/100 (B+ / borderline A-)**

Breakdown by axis (each weighted 25% for the rubric, but Completeness gets a tilt down because of two unresolved hedges I flag below):

| Axis | Level | Numerical (out of 100) | Weight |
|---|---|---:|---:|
| Novelty | **Excellent (low end)** | 91 | 25% |
| Scope | **Good (high end)** | 88 | 25% |
| Analysis | **Excellent (low end)** | 91 | 25% |
| Completeness | **Good (mid)** | 85 | 25% |
| **Weighted total** | | **88.75** | 100% |

Rounded: **89/100, letter B+ on the strict reading, A- on a charitable reading.** The paper is one structural fix away from A/A- territory but currently has one lethal weakness (see "Single most lethal" below) that a strict grader will use to keep it out of unambiguous Excellent.

Translated to CS 285 grade bands: this paper would land in the **"Good to Excellent" boundary** — graders following the rubric verbatim will most often check "Good" on Scope and Completeness and "Excellent" on Novelty and Analysis, yielding a numerical mean in the upper-80s.

---

## Rubric axis ratings

### Novelty: **Excellent (low end of band)**

- **Evidence:**
  - Extended Abstract para 2: "we recast VLM-guided replay as a trajectory-conditional posterior $q_\phi(t^\star \mid \tau)$ over the failure-causing timestep" — this is a substantively original re-framing, not a re-implementation.
  - Extended Abstract para 2 (P2): "VLM-Verified Counterfactual Hindsight: we close the dominant failure mode of language-only counterfactuals (100% teleport-collapse of Opus 4.7 on FetchPush) by asking the VLM for a corrective action sequence rather than a hindsight goal, executing it in a simulator fork" — this is a structurally novel mechanism (generator-verifier paradigm instantiated in robot RL with a simulator-fork verifier).
  - §2 Related Work explicitly differentiates from concurrent VLM-RB [Sharony 2026] along two methodological axes (multiplicative vs additive; action-emitting verifier vs. success-scoring). The phrase "the multiplicative form is the principled choice" is a substantive thesis claim, not a label.
  - §3.3 introduces an explicit failure-mode name ("teleport-collapse") with a mathematical characterization ($q_\phi(\hat{p}\mid\tau)=\delta(\hat{p}-g)$) — this is a contribution at the framing level.

- **What's missing for highest-end Excellent (95+):**
  - The multiplicative-vs-additive argument is mathematically motivated but the paper does NOT empirically run VLM-RB at matched horizon and show "additive harms in regime X, multiplicative helps in regime X." The Sharony reproduction is "pre-staged" (appendix p.5–6) but not run. A strict grader will say "novel framing, but not yet empirically distinguished from the prior work it claims to supersede."
  - The IS-posterior framing reduces to "PER with a multiplicative weight" in implementation. The framing's novelty is real but a strict grader could mark it as "modifies existing" if they read it skeptically.

### Scope: **Good (high end of band; just below Excellent)**

- **Evidence:**
  - 3 environments × 3 seeds × ~6 methods (Uniform, PER, HER, Oracle-CF, vlm_cf, verified_cf) at multiple horizons (250k, 500k, 1M, 3M cited) = 21+ training runs documented.
  - 2 methodological contributions (Semantic PER + Verified-CF) implemented end-to-end.
  - 4 empirical sub-studies in §4: headline (§4.1), prompt design (§4.2), cross-task transfer (§4.3), pre-registered kill (§4.4).
  - Released GitHub repo with full code at `DJRGVC/RL_project_185`.
  - Bias-bound proof sketch in Appendix B.

- **What's missing for Excellent (90+):**
  - **Compute scope is below typical workshop paper.** Total project compute: ~220 GPU-hours + ~$80 VLM-API spend (Appendix C). A workshop paper at NeurIPS/CoRL on a robot-RL topic typically runs 1k+ GPU-hours and uses 5+ envs. 3 envs at 500k steps (vs. canonical 4.75M for Fetch+HER) is closer to a "long workshop submission" than a full workshop paper.
  - The "Sharony VLM-RB reproduction" is pre-staged but not run for camera-ready. A strict grader will note that the *headline comparison the paper sets up* (multiplicative vs. additive) is not yet a head-to-head experiment.
  - HER@500k matched-horizon baseline is implicit (only HER@250k and HER@1M are reported); the cross-horizon bars in Fig. 1 require the reader to do the matching mentally. The "Horizon caveat" paragraph in §4 acknowledges this but does not fix it.
  - **3-person team:** "Relatively little implementation or analysis effort per group member" is a Fair-level descriptor; the Contributions section shows Daniel did the lion's share (the research direction, all Phase 1/2 runs, IS-posterior framing, all paper figures, the manuscript), while Parshawn and Matei are credited only with "Contributed to..." prior infra and a 36-run ablation suite. A strict grader will read this as "1.5-person effort" and mark Scope down from Excellent to high-Good.

### Analysis: **Excellent (low end of band)**

- **Evidence:**
  - Multiple baselines explicitly compared in §4.1: Uniform, PER@3M, HER@250k, Oracle-CF, vlm_cf, verified_cf. That's 5+ baselines, comfortably above the rubric's "several" threshold for Excellent.
  - Ablations: p_counterfactual sweep referenced in Contributions, 2×2 prompt-variant grid (Table 1), 36-run prior ablation suite (Uniform/PER/Semantic-PER/Oracle).
  - **"Explains why methods work":** §4.1 closing paragraph asks "Why does verified-CF pay off on Slide?" and answers with the gripper-to-object-distance monotonicity argument — this is exactly the rubric's "explain why the methods work or don't work" language.
  - **"Explains why methods don't work":** §5 cold-start verifier-rejection paragraph (load-bearing limitation) names the asymmetric failure modes precisely (Semantic-PER = variance amplification, bounded; verified-CF = signal extinction, unbounded). This is a strong "honest negative explanation."
  - §3.3 teleport-collapse analysis: the paper names a failure mode, gives a mathematical characterization ($\delta(\hat{p}-g)$), and identifies it as architectural-not-model-specific via the GPT-4o $0/6$ vs. Opus $4/4$ contrast.
  - Pre-registered kill experiment (§4.4) with explicit threshold ($+0.10$) and honored verdict — methodologically rigorous.

- **What's missing for highest-end Excellent (95+):**
  - The headline aggregation ("verified-CF mean 0.606 vs. vlm_cf 0.622, $\Delta = -0.016$, tied within noise") is across $n=3$ seeds × 3 envs = 9 final-eval points. No formal hypothesis test is reported on the cross-method comparison; the "tied within noise" claim is by inspection. The Statistical Methodology paragraph (Appendix C) cites $t$-distribution with $n-1=2$ d.f., which is honest but very low power.
  - Sharony VLM-RB head-to-head is not in the paper; the paper's signature claim ("multiplicative is principled, additive is not") is supported analytically but not empirically. A strict grader's pencil will hover here.

### Completeness: **Good (mid band)**

- **Evidence:**
  - All cited numerical results have $n=3$ seeds: verified_cf reaches mean 0.606 (0.85/0.35/0.617), vlm_cf 0.622, HER@250k 0.617/0.167/0.183, Oracle-CF 0.117/0.383/0.183 — all populated.
  - Pre-registered kill verdict is honored and discussed in the paper, not hidden.
  - The Extended Abstract has a distinct "Honest negative and roadmap" paragraph naming the cold-start regime — strong sign of completeness rather than omission.
  - Bibliography compiles cleanly, no `??` in PDF, no LaTeX warnings.

- **What's missing for Excellent (90+):** (this axis carries the most risk)
  1. **Three "pre-registered but not run" items** that a strict grader will treat as incomplete:
     - "The strictly-correct IS-correction ablation" (§5 limitation (i)) — pre-registered, not run.
     - "$n \ge 30$ replications for the 12/12 cross-task" (§5 limitation (ii)) — pre-registered, not run.
     - "A faithful VLM-RB reproduction is pre-staged in our codebase for camera-ready head-to-head evaluation" (§5 closing of limitations) — pre-staged, not run.
     The rubric's Excellent says "All experiments are complete and results are discussed fully." The paper has three explicit "deferred to future" items. A strict grader marks this Good, not Excellent.
  2. **Cross-horizon comparisons** appear in Fig. 1 and §4.1 prose ("$+0.45$ over PER@3M, $+0.43$ over HER@250k"). The "Horizon caveat" paragraph is honest but the headline number ($0.617$ on Slide vs. $0.10$ on PER@3M) compares 500k vs. 3M, which is genuinely confounded. A strict grader will read this as "the headline result depends on a cross-horizon comparison."
  3. **The "Phase-1 Oracle-CF" experiment is killed** (§4.4) but the paper still leads with "headline pivoted to the IS-posterior framing." A grader who reads literally will note: "Path C was killed but the pivot is now to a *theoretical* framing whose multiplicative-vs-additive empirical claim is also not yet run." That's a structural concern about the completeness story.

---

## Extended Abstract specific notes

The Extended Abstract is the primary grading artifact (quote from outline). Walking through whether the Ext Abs *on its own* justifies each rubric level:

### Novelty — Ext Abs verdict: **Excellent**
Para 2 ("Methodological contributions") names two distinct contributions and gives one-sentence mechanism descriptions for each. The phrases "recast VLM-guided replay as a trajectory-conditional posterior," "the multiplicative form is the principled choice," "we close the dominant failure mode... by asking the VLM for a corrective action sequence rather than a hindsight goal," and "executing it in a simulator fork" are all substantively original. **This paragraph alone scores Excellent on Novelty.**

### Scope — Ext Abs verdict: **Good (boundary)**
Para 3 ("Headline findings") names 4 sub-results across 3 envs + 2-vendor 3-model prompt sweep + cross-task transfer + pre-registered kill. That's a lot of experimental surface area in 1 page. But: no compute totals, no run-count, no number-of-baselines tally appears in the Ext Abs. A grader scanning the Ext Abs alone will see "many findings" but cannot quantify scope without flipping to §4 / Appendix C. **Reads Good-with-Excellent-aspirations from the Ext Abs alone.**

### Analysis — Ext Abs verdict: **Excellent (low end)**
The Ext Abs explicitly names baselines ("PER@3M, HER@250k") in finding (i) and includes a "why" explanation ("the verified-CF channel exhibits a cold-start regime... in which it reduces to a strictly costlier HER"). Finding (iii) gives a contrastive analysis ($0/6$ vs $4/4$). **The Ext Abs hits the rubric's "explain why" requirement.**

### Completeness — Ext Abs verdict: **Good**
The "Honest negative and roadmap" paragraph is good (transparency signal). But it explicitly says "the two failure modes are asymmetric (Semantic-PER variance inflation is bounded; verified-CF write-throughput collapse is not)" — admitting one of the two contributions has an unbounded failure mode is a Completeness flag. A strict grader will not check "Excellent" on Completeness while the Ext Abs itself acknowledges an unbounded failure mode without a fix. **Reads Good, not Excellent.**

**Net Ext Abs prediction: 2 Excellent + 2 Good = approximately B+ / 88-89.**

---

## SINGLE most lethal weakness

### The lethal item: **The signature methodological claim (multiplicative > additive for VLM-guided replay) is never empirically tested in the paper.**

- **Why this is lethal:** The Ext Abs *closes* on the multiplicative-vs-additive distinction ("Concurrent VLM-RB uses frozen VLMs as an additive priority bias; we argue the multiplicative form is the principled choice"). This is the headline framing claim. Yet the Sharony VLM-RB reproduction is "pre-staged in our codebase for camera-ready head-to-head evaluation" (§5 limitations + Appendix E reproducibility). A strict grader reads this as: *the paper's thesis is asserted analytically but not demonstrated empirically against the comparison baseline it explicitly names.*

  This pulls the grade down on **two axes simultaneously**:
  1. **Analysis**: rubric Excellent requires "compares with several baselines and ablations." Sharony VLM-RB is the named-comparator baseline. Not running it is a Good-not-Excellent signal on this axis.
  2. **Completeness**: rubric Excellent requires "all experiments are complete." A pre-staged reproduction is, by the rubric's words, an incomplete experiment.

- **Fix recommendation (if there were time):**
  - Run Sharony VLM-RB at $n=3$ seeds × 1 env (PnP, where the kill verdict already constrains the headroom) at 500k steps. Even 1 env at 1 seed run as a "we ran the additive baseline once and it underperformed multiplicative by X" would close the loop.
  - **If no time**: in §4.1 and §5, add an explicit sentence saying "the multiplicative-vs-additive distinction is currently supported analytically (Eq. (1), §3.1) and not yet empirically distinguished; we pre-stage the Sharony VLM-RB reproduction for camera-ready" — this is already partially there but should be flagged more visibly as a *limitation* rather than buried as a future-work bullet.

---

## Sweep of edits to reach Excellent on all 4 axes

These are listed in order of grade impact per minute of effort. The user is in submission crunch — these are recommendations, NOT edits.

- **Edit 1 (Completeness, +2-3 grade pts): Add a one-sentence VLM-RB-comparison hedge to the Extended Abstract.** Currently the Ext Abs makes the multiplicative-vs-additive claim without flagging it as untested. A single sentence in the "Honest negative and roadmap" paragraph along the lines of: *"The multiplicative-vs-additive distinction is established analytically (Eq. 1); we pre-stage the head-to-head VLM-RB reproduction for camera-ready evaluation."* — this preempts the strict grader's main critique.

- **Edit 2 (Scope, +1-2 grade pts): In §4 setup or the horizon-caveat paragraph, add a sentence quantifying total compute and total run count.** Something like: *"Across all reported methods we executed 21 paper-grade training runs totaling ~220 GPU-hours."* This converts the Ext Abs reader's "many findings" intuition into a quantified scope claim that hits the workshop-paper-similar threshold.

- **Edit 3 (Analysis, +1 grade pt): Replace "tied within noise" with a confidence-interval statement.** E.g. *"verified-CF $0.606 \pm 0.08$ vs. vlm_cf $0.622 \pm 0.07$; 95% CIs overlap (Welch's $t$, $p = 0.X$)."* The numbers are likely already in the W&B logs; a 30-minute calculation upgrades a verbal-tie claim to a statistical-tie claim.

- **Edit 4 (Completeness, +1 grade pt): Move the three "pre-registered but not run" items out of the limitations enumeration and into a single dedicated "Pre-registered camera-ready experiments" paragraph.** This frames them as *planned-and-scoped* rather than *missing*. Same content, better framing for a strict-rubric grader.

- **Edit 5 (Novelty, +0.5 grade pt): Move the "first to use a VLM-localized failure timestep as a credit-assignment signal" claim from §2 into the Ext Abs (Methodological contributions paragraph).** This is a "to our knowledge first" claim and it belongs on page 1 if the grader is going to score Novelty primarily from the Ext Abs.

- **Edit 6 (Scope, +0.5 grade pt): Rebalance the Contributions section.** Currently Daniel did approximately 85% of the work per the bullets; Parshawn and Matei each get one "Contributed to..." sentence. A strict grader will read this as "scope is really 1-person scope, not 3-person." If Parshawn and Matei genuinely did more, surface it; if they did not, the contributions are accurate but Scope cannot read as full 3-person workshop scope.

---

## Bottom line

**Predicted strict-rubric grade: 89/100 (B+, with high-end-of-band readings landing at A-).**

The paper is structurally sound, has substantive original contributions, an honored pre-registered kill, and explicit "why methods work/don't work" explanations. It loses the unambiguous-Excellent grade because (1) the signature methodological claim is not yet empirically validated against the named comparator, (2) three pre-registered experiments are deferred to camera-ready, and (3) per-member scope is uneven across the 3-person team. The single highest-impact preemptive edit is adding one sentence to the Ext Abs flagging the VLM-RB reproduction as deferred-but-pre-staged, which preempts the strict grader's central critique.
