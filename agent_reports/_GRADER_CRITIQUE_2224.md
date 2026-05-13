# BRUTAL 185/285 GRADER + NeurIPS REVIEWER CRITIQUE

**Target:** `agent_reports/paper_cs285/main.pdf` (45 pp.; CS 285 submission)
**Reference comparison:** `agent_reports/paper/main.pdf` (NeurIPS variant; has newer numbers)
**Reviewer:** Hostile CS 285 grader + NeurIPS area chair, 60-min review budget
**Date:** 2026-05-12 22:24

---

## TL;DR for the agent triage layer

The CS 285 paper has a **single catastrophic, score-killing problem**: the Extended Abstract — which the outline explicitly says is "primarily used for grading" — claims the headline result is **verified-CF** reaching 0.95 (Push) / 0.55 (Slide). But the body of the paper (§5.6 part C, lines 1626–1633) explicitly attributes those numbers to **VLM-CF**, not verified-CF. And the NeurIPS sister paper has the correct headline (verified-CF mean 0.606 across envs, **0.617 on Slide vs. vlm_cf 0.55**) that the CS 285 paper is *missing entirely*. The CS 285 paper presents data that is **30+ hours stale** relative to its sibling. A harsh grader who reads only the Extended Abstract will leave thinking the paper's headline is verified-CF, then find a §5.6 that says "PnP in flight" and doesn't actually evaluate verified-CF — and Figure 1 (the only training-curve figure) is captioned **"Pre-fix run, retained for transparency. ... not a valid evaluation of Semantic PER."** That caption alone is grounds for a "Fair (50-75%)" Completeness rating.

Below: §A drills into the Extended Abstract; §B rubric-axis ratings; §C reviewer-level concerns; §D figures; §E contradictions; §F honest-vs-spin; §G the 36-run aggregate. Final P0/P1/P2 list at the end.

---

## A. Extended Abstract (CS 285 graders' primary artifact)

The outline says graders **"will primarily use the extended abstract for grading."** Read it as if it were the entire paper. Here is what it says and what is wrong.

**Location:** `agent_reports/paper_cs285/main.tex` lines 34–107 (also pages 1–2 of the rendered PDF).

### A.1 The headline numbers contradict the body text (CRITICAL)

Line 70–74:
> *"(i) **vlm_cf headline.** At 500k SAC+HER+VLM-CF updates on FetchPush seed 0 the verified-CF agent reaches 0.95 success; on FetchSlide it reaches 0.55..."*

This is internally incoherent.
- The paragraph is labeled "**vlm_cf headline**" (good).
- The text says "**the verified-CF agent reaches 0.95 success**" (wrong — those numbers belong to vlm_cf per §5.6 lines 1626–1633).
- Verified-CF on Push is actually **0.85**, on Slide **0.617**, per the NeurIPS sister paper (`agent_reports/paper/main.tex` lines 1694–1696) which the CS 285 variant has not been updated to match.

A grader reads this and asks: "Is the headline VLM-CF or verified-CF? Which agent reached 0.95?" — and finds the answer is neither/both, because the bullet conflates them. **This is the single most damaging line in the document.**

**Worse:** The NeurIPS variant's clean positive finding — *verified-CF beats vlm_cf on Slide (0.617 vs 0.55)* — is **the strongest empirical claim in the whole project**, and the CS 285 paper does not state it anywhere. The Extended Abstract instead leads with a number that doesn't belong to verified-CF.

### A.2 The "Phase 1 kill verdict + 1M update" bullet is incoherent (CRITICAL)

Lines 74–78:
> *"(ii) **Pre-registered Phase 1 kill verdict + 1M update.** Our Phase 1 oracle-heuristic study triggered the pre-registered kill criterion (no separation by 300k updates); we honor the kill and re-allocate compute to Phase 2 (verified-CF), which crosses the criterion at 1M updates."*

Problems:
- "no separation by 300k updates" — but the body (line 1577) says the kill horizon was **250k**, not 300k. Off by 50k.
- "Phase 2 (verified-CF), which crosses the criterion at 1M updates" — what criterion? At what horizon? The body's §5.6(E) (lines 1673–1689) explicitly says the 1M run is a *post-hoc, not-pre-registered* observation and "*we do not retract the pre-registered kill verdict*." So the Extended Abstract is claiming the kill is overturned at 1M updates, while the body says it is **not** overturned. A grader will catch this contradiction in 90 seconds.
- Even more confusing: the bullet conflates Oracle-CF (the killed approach) with verified-CF (a *separate* mechanism), as if they were the same thing.

### A.3 The "Sharony reproduction" bullet inflates a not-yet-run experiment

Line 83–87:
> *"(iv) **Sharony reproduction.** A faithful re-implementation of the concurrent VLM-RB priority formula ... is pre-staged in our codebase for head-to-head comparison."*

"Pre-staged in our codebase" = unit tests pass on CPU; **no Modal runs launched**. The body (lines 1644–1671) is honest about this: "implemented, pending launch." But putting this bullet under "Headline findings" alongside actual training results misleads a grader into thinking a comparison was run. A NeurIPS reviewer would flag this as overstating a contribution.

### A.4 The "Honest negative result" paragraph is good — but undermines the headline

Lines 88–97 frame the verified-CF cold-start failure as an "honest negative result." This is well-written and reflects credit. BUT — combined with A.1 above — the Extended Abstract now reads:
- (i) verified-CF wins on Push/Slide (FALSE per body)
- (iv) verified-CF cold-start collapses 100% (TRUE per body)

A grader cannot reconcile these two claims from the Extended Abstract alone. The NeurIPS variant resolves this by saying explicitly that the cold-start regime is *transitory* — but the CS 285 variant lacks this connector.

### A.5 Unexplained jargon (minor)

- "TD-bootstrapping" (line 42), "Bellman loss" (line 62), "multiplicative form / additive form" (line 51): assumed reader is mid-level RL — OK for CS 285 grader (a GSI).
- "$q_\phi(t^\star \mid \tau)$" (line 57) — a CS 285 GSI will know what a posterior is, but the symbol arrives without definition. Acceptable but not friendly.
- "IS-correction analysis" (line 59) — undefined. The IS bias bound is referenced (`Eq. ref{eq:bias-bound}`) but the equation is in the appendix; a grader scanning the Extended Abstract has no way to evaluate it.

### A.6 Length is fine (1.3 pp.)

Visually the Extended Abstract renders cleanly on pages 1–2 with normal margins. Defensible against the outline's 1-page recommendation under "we will not penalize longer reports."

**Bottom line on Extended Abstract:** This is the document the grader will read, and as written it is *incoherent on its headline finding*. A harsh grader could legitimately rate Completeness "Fair" on the Extended Abstract alone.

---

## B. CS 285 Rubric — Four Axes

Outline rubric: Novelty / Scope / Analysis / Completeness, each in {Poor (0-50%), Fair (50-75%), Good (75-90%), Excellent (90-100%)}.

### B.1 Novelty — **Good (75-90%)**, defensible

**Why not Excellent:** The two contributions (IS-posterior framing of Semantic PER; simulator-verified counterfactual hindsight) are both *substantively original* in framing. The IS-pairing argument against VLM-RB's additive mixture is a non-trivial theoretical positioning (§3, lines 472–648). The verified-CF mechanism is novel in its specific instantiation (action-output + sim-fork + sparse-reward gate; §4.3 lines 958–1071).

**Why a harsh grader might downgrade:**
- Both contributions are partially inherited: Semantic PER framing rests heavily on CaLM (Pignatelli 2024) and the ReaPER/RPE-PER/PGR multiplicative-PER family, which the paper acknowledges (lines 723–740). The novelty is the *vision-modality, prioritized-replay, multiplicative-VLM* combination — a specific instance, not a new top-level taxon.
- The "verified counterfactual" idea (generator-verifier, ground-truth simulator) is a clean engineering instantiation of zha2025tango. The novelty is the *application* to robot RL, not the paradigm.
- The honest reviewer-read is: this is a thoughtful synthesis with two well-placed implementations, not a discovery of a new mechanism. That's a solid "Good."

### B.2 Scope — **Good (75-90%)**

**Why Good and not Excellent:**
- Three Fetch environments, six experiments (headline ablation, prompt sweep, real-data, cross-task, kill experiment, Sharony repro), 36+ training runs, prompt-design 2×2×2 grid, two model vendors, three VLMs. That's the scale of a workshop paper.
- BUT: per the rubric, "Excellent" requires *"Similar scope to a conference workshop paper"* — which is exactly here. So why not bump? Because:
  - The Sharony VLM-RB reproduction is **not run** ("pending launch," line 1644). The single best head-to-head differentiation experiment is missing.
  - Verified-CF training-time results are **not in the CS 285 paper body** (NeurIPS variant has them; CS 285 says "PnP in flight" line 1635). The CS 285 grader sees an incomplete experiment suite.
  - The cross-task transfer pilot is n=12, which is openly flagged as a pilot (line 1761), not a powered sweep.
- Net: scope is solidly Good, would have been Excellent if Sharony VLM-RB had been launched + the verified-CF data folded in from NeurIPS variant.

### B.3 Analysis — **Good (75-90%)** with significant downgrade risk to **Fair**

The rubric "Good" requires *"Solid comparison with multiple baselines and some ablations. Experiments effectively test the problem setting."* The rubric "Excellent" requires *"Experiments are well thought-out and explain why the methods work or don't work."*

**For Good:** Yes, the paper has Uniform / PER / Semantic-PER (GPT-4o) / Semantic-PER (Oracle) on three envs (Fig. 1); two-vendor three-model prompt sweep (Table 1, Fig. 3); real-data validation (Fig. 5); cross-task transfer (Fig. 4); Oracle-CF kill experiment (§5.6 A). Plenty of baselines and ablations.

**Why downgrade risk to Fair:** The flagship figure (Fig. 1, `fig1_headline_success.pdf`) is captioned **"[Pre-fix run, retained for transparency.]"** with text saying *"The GPT-4o curve uses a known-buggy pipeline (all-variant prompt without the teleport gate), which silently admitted ~67% degenerate counterfactuals as relabels; see Section 5.7. The curve is therefore not a valid evaluation of Semantic PER."* (Line 1144).

This is honest, but a harsh grader reads it as: *"Your headline figure is invalid by your own admission."* The rubric "Fair" tier says *"Experiments are trivial/superficial/do not test the proposed setting. Inappropriate baselines or ablations."* — and a hostile reader could argue the headline ablation fails the "effectively test the problem setting" bar because the central curve is admitted to be buggy.

The **only** thing keeping Analysis at Good is that the Oracle headroom curve, PER baseline, and Uniform baseline in Fig. 1 are still valid (the bug is in the GPT-4o curve only) — and the prompt-design sweep (§5.2, Table 1) is genuinely solid.

**To rescue Analysis to Excellent:** the GPT-4o curve in Fig. 1 needs to be either (a) replaced with the post-fix Phase 2 verified-CF/vlm_cf data, or (b) the figure caption rewritten to clearly frame this as a "pre-fix vs. post-fix" comparison with a second panel showing post-fix results.

### B.4 Completeness — **Fair (50-75%)**, the weakest axis

The rubric "Good" requires *"Substantially complete. Experimental results differentiate between methods but may lack some discussion."* "Excellent" requires *"All experiments are complete and results are discussed fully."*

**Why this is Fair, not Good, in the CS 285 paper specifically:**
1. **§5.6(C) line 1610:** *"VLM-CF and verified-CF sweeps (Phase 2, attempt 5) — Push and Slide complete; PnP in flight."* — A core experiment is in flight at submission. The NeurIPS variant has the same section saying "all 9 runs complete." So the CS 285 paper *as submitted* is missing data the NeurIPS variant already has. **This is a submission-quality bug, not a project-quality bug.**
2. **§5.6(D)** says "Sharony VLM-RB baseline — implemented, pending launch."
3. **§5.6(E)** says "Mid-training trajectory of Oracle-CF at 1M steps — preliminary observation" — i.e., a different experiment is in flight.
4. **§5.6(F)** says "Prompt-design ablation matrix — pre-registered, in flight."
5. Figure 1 is captioned as a pre-fix run with a known bug.
6. There's an **undefined `tab:vlm_comparison` LaTeX reference** on page 20 (`build.log` line: *"LaTeX Warning: Reference 'tab:vlm_comparison' on page 20 undefined"*) — meaning a `??` shows up in the rendered PDF. **Show-stopper for a careful grader scanning the PDF.**

Four experiments listed as in-flight, plus a known-buggy headline figure, plus a broken reference. A harsh grader reading the outline's Completeness column ("*All experiments are complete and results are discussed fully*") will downgrade.

**To rescue Completeness to Good:** Fix the `tab:vlm_comparison` reference, fold the NeurIPS variant's Phase 2 verified-CF data into §5.6(C)/(D), and either run or remove Sharony VLM-RB.

---

## C. NeurIPS-Grade Reviewer Concerns

(Read this as if I am Reviewer 3.)

### C.1 Baseline fairness — moderate concern

- HER baseline trained to 250k steps. VLM-CF trained to 500k. Verified-CF trained to 500k. **The comparison horizons are not matched** in the Phase 2 section. A reviewer will ask: how does HER do at 500k? The paper handwaves this in the Conclusion section but does not give a number. The NeurIPS variant lines 1106–1116 invoke Plappert's asymptotes (HER+DDPG at 8M timesteps reaches ~0.99/0.95/0.75 on Push/PnP/Slide) — but the **CS 285 paper does not cite Plappert** (verified: `grep` returns nothing). So the CS 285 paper claims its 500k results "match the PER@3M asymptote" without a citation to substantiate the PER@3M number. A reviewer flags this as either uncited or unsupported.
- Comparing verified-CF (which is doing CF relabels) against HER (which is also doing relabels via the same `future` strategy with k=4) — the budget per relabel differs (verified-CF makes a VLM call + sim fork per failure, HER does not). Sample-efficiency-per-step is fair; sample-efficiency-per-wall-clock is wildly different. The paper does not table the wall-clock comparison.

### C.2 Statistical rigor — n=3 seeds

- n=3 is *defensible* for sparse-reward Fetch (RL standard, e.g. Plappert used n=5). But the paper claims "non-overlapping SE intervals as the threshold, consistent with a conservative two-sample test" (line 1126). With n=3 and t-distribution at df=2, the critical t is 4.30 — non-overlapping SE intervals correspond to a p≈0.05–0.10 test, NOT particularly conservative. The framing slightly oversells.
- On FetchSlide, the verified-CF claim "$0.617 \pm 0.03$ vs vlm_cf $0.55 \pm 0.13$" — the vlm_cf SE is large enough that the intervals overlap (0.42 to 0.68 for vlm_cf). The "verified-CF exceeds vlm_cf" claim is **within noise at n=3**. The NeurIPS variant lines 1700–1707 acknowledges this softly ("essentially tied in aggregate"), but the Extended Abstract is more bullish. A harsh reviewer would call this out.
- The 12/12 cross-task agreement at n=12 is sometimes described as "12/12 perfect agreement" — the paper does note (line 1764) that this is "not statistically distinguishable from an 80% true rate at n=12." Good catch by the authors.

### C.3 Reproducibility

- The repo URL is `https://github.com/d-grant-uc-berkeley/RL_project` at commit `0fa36fc` (line 2014) — anonymity issue if double-blind, but CS 285 is single-blind so fine.
- Hyperparameters are in `configs/` and Appendix lists them (line 2016). OK.
- Modal sweep is reproducible if you have a Modal account — but the Modal-specific commands `modal run modal_app.py::run_ablation` (appendix line 1641) are reproducible only with seed account access.
- The `path_c_overnight` W&B tag is referenced for verification — assumes a reviewer has access. Fine for non-anonymous submission.

### C.4 Comparison to prior work

- **Sharony 2026 (VLM-RB):** Cited extensively, contrasted in Table 1 and §3. Implementation in code (`src/buffers/vlm_rb_buffer.py`) — but **no training-time numbers** comparing on Fetch. Reviewer will say: "you implemented their method but didn't run it." This is the biggest single missed-experiment in the paper.
- **HER+PER stacking:** The paper does not explicitly state whether HER and PER are stacked (i.e., HER relabels go into the PER buffer with priorities). Implicitly yes (Semantic PER multiplies on top of PER which is built on the HER buffer), but this is not made explicit anywhere I saw. A reviewer might ask whether the HER+PER stack itself has been studied (Andrychowicz HER paper used uniform replay, not PER; Zhao 2018 energy-based prioritized HER is a follow-up). The CS 285 paper does NOT cite Zhao 2018 (verified: missing from `refs.bib` — the NeurIPS variant has `@inproceedings{zhao2018energy}` which the CS 285 variant lacks). This is a missing baseline citation.
- **Plappert 2018 asymptotes:** Cited in NeurIPS variant lines 1108–1116; **completely missing from CS 285 variant** (the entire paragraph about HER+DDPG asymptotes was lost in the CS 285 build). When the CS 285 paper claims "this matches the PER@3M asymptote of 0.95" (line 1627), it has no reference to Plappert's published asymptote. A reviewer flags this.

### C.5 Claims relative to data

- Abstract claim: "evidence that a foundation-VLM credit-assignment oracle generalizes where a learned priority head would not" (line 128). The evidence is *n=12 cross-task* with no comparison run on a learned priority head. The claim is asymmetric: we observe VLM works, we *infer* a learned head would not. A reviewer would say "evidence for the first half, speculation on the second." The paper does flag this in the Limitations.
- "0% teleport-collapse, 0.79 plausibility, 0.83 goal-progress" (line 126) — accurate per Table 1 row `(GPT-4o, achieved_goal)`. OK.
- "12/12 cross-task annotations" — accurate per Fig. 4 and §5.3 (line 1407). Note 9/12 *tolerant keyframe agreement* (the harder metric) is the one labeled fairly in the body.

---

## D. Figure Consistency

Checked figures in `agent_reports/paper_cs285/main.tex` includegraphics calls and labels:
- **5 figures referenced via `\includegraphics`:** `fig_envs.pdf`, `fig1_headline_success.pdf`, `figN_c1v2_model_comparison.pdf`, `figN2_cross_task_transfer.pdf`, `figN_c1v2_real_vs_synthetic.pdf`. All exist in `agent_reports/paper_cs285/` (verified via `ls`).
- **5 figures referenced only via labels (boxed Definition figures):** `fig:kernel`, `fig:assumption`, `fig:teleport-def`, `fig:protocol` — these are `fbox` typeset boxes, not images. Acceptable.

### D.1 Inconsistent horizons in same chart (CRITICAL on Fig. 1)

`fig1_headline_success.pdf` shows Uniform/PER/Semantic-PER (GPT-4o)/Semantic-PER (Oracle) on three envs. From the rendered image:
- PER on FetchPush reaches ~0.95 — this is the **3M-step PER asymptote from the 36-run aggregate** (per discussion in §5.6 line 1627).
- Other bars appear to be at much shorter horizons (250k/500k for Semantic-PER).
- The figure does NOT annotate the horizon for each bar. A grader reading the figure will assume all bars are at the same horizon — they are not. This is **misleading by omission**.
- The figure caption (lines 1132–1146) does not mention this. It only notes the "pre-fix" bug.

### D.2 Inconsistent palette across figures

Comparing the four PNGs I rendered:
- `fig1_headline_success.png`: uses grey/dark-blue/orange/light-blue. CB-safe.
- `figN_c1v2_model_comparison.png`: uses blue/orange (Opus/GPT-4o).
- `figN2_cross_task_transfer.png`: uses dark-blue/orange/light-blue. The orange means *something different here* than in Fig. 1 (here it's "Task-relevant judge"; there it's "Semantic PER GPT-4o").
- `figN_c1v2_real_vs_synthetic.png`: uses grey/orange/blue.

The orange channel is overloaded across figures — orange = GPT-4o in Fig. 3, orange = Semantic-PER-GPT-4o in Fig. 1, orange = Task-relevant in Fig. 4, orange = C1v2-Opus in Fig. 5. A consistent paper would assign each axis a single color. **Per the user's memory entry on NeurIPS figure conventions, CB-safe palette is mandated — this is partially met but not consistent.**

### D.3 Missing/unclear captions

- Fig. 1 caption is heroically long (15 lines) but the *most important* fact — that the GPT-4o curve is buggy — is buried at line 1138. Should be the first sentence.
- Fig. 4 (cross-task) caption is OK but does not say n=4 per env in the caption (it's in the body, line 1404 — should be in the caption itself).
- Fig. 5 (real-vs-synthetic) caption mentions "75% → 0%" — but the figure shows bars of 30% and 0% on PickAndPlace `ag` column (per the rendered image). Caption number vs figure number mismatch.

### D.4 Orphaned figures (in `figs/` but not used)

35 figures in `agent_reports/figs/`. Used: 4 in CS 285 paper. **31 figures unused.** Not a grading concern (they're not in the paper directory), but:
- `fig_headline_v2.png`, `fig_headline_v3.png`, `fig_morning_headline.png` exist — suggests there were newer headline figures considered. If `fig_headline_v3.pdf` contains post-fix Phase 2 data, swapping it in is a high-leverage P0.

### D.5 No undefined refs to figures

All `\ref{fig:...}` resolve. The only undefined ref is `tab:vlm_comparison` (build.log line 1) — this is a **table** reference. Search showed line 1646 of `main.tex` says *"To sharpen the differentiation from \citet{sharony2026vlmrb} beyond the methodological comparison in Table~\ref{tab:vlm_comparison},"* — and that table is never defined. **The CS 285 paper has a `??` literally rendered in the PDF on page 20.** Confirmed by `grep -n "vlm_comparison"` — only one reference, no `\label`.

---

## E. Internal Contradictions

### E.1 Extended Abstract vs §5.6 vs Conclusion

| Where | Claim | Status |
|---|---|---|
| Ext. Abstract line 72 | "verified-CF agent reaches 0.95 on Push, 0.55 on Slide" | Wrong (those are vlm_cf numbers per §5.6) |
| Ext. Abstract line 77 | "Phase 2 (verified-CF), which crosses the criterion at 1M updates" | Contradicts §5.6(E) line 1681 ("we do not retract the pre-registered kill verdict") |
| §5.6(C) line 1626–1633 | vlm_cf reaches 0.95/0.55 | Self-consistent |
| §5.6(C) line 1635 | "FetchPickAndPlace: all 3 seeds are still in training at ~60% of the 500k budget" | **Stale**: NeurIPS variant says "all 9 runs complete" |
| §5.6(D) line 1644 | "Sharony VLM-RB baseline — implemented, pending launch" | Self-consistent with no-launch |
| Conclusion line 1915–1947 | Headline claims framed around "IS-posterior framing" + "verifier mechanism" + "12/12 cross-task" | Does NOT claim numerical headline (smart) but also doesn't *defend* a numerical headline |
| Ext. Abstract bullet (i) | "vlm_cf headline" | But Conclusion gives no numerical headline. **The Extended Abstract over-promises a numerical result the Conclusion doesn't deliver.** |

### E.2 Per-environment number consistency

- §5.6(A) line 1592–1593: Slide HER reached 0.100, Oracle-CF 0.183 — but the kill-experiment narrative says these are "below threshold" of +0.10. Actually +0.083 is below +0.10, so this is consistent. OK.
- §5.2 Table 1 lists GPT-4o achieved_goal plausibility 0.79. Ext. Abstract line 126 says 0.79. Consistent.
- Fig. 1 GPT-4o on Push appears to be ~0.17 in the rendered image; §5.6 line 1626 says vlm_cf on Push reaches 0.95 mean. **These are different runs at different horizons** — both correct individually, but Fig. 1 is misleading without the horizon labels (see D.1).

### E.3 Theory vs implementation

- §3 line 547: "In our current implementation we use the PER IS-weight $w_{IS,P}$ rather than the strictly-correct $w_{IS,Sem}$." Honest disclosure. OK.
- §3 line 510: "$w_{\text{sem}}(i;\tau) := \mathbb{E}_{t^\star\sim q_\phi}[K_W(i;t^\star)]$" defines expectation form, then line 528: "Hard elicitation (our implementation): a chain-of-thought prompt returns a single failure_frame_index... equivalent to setting $q_\phi$ to a Dirac." Honest, but a reviewer will say: you defined a posterior, then collapsed it to a point estimate, then claimed the posterior framing is your contribution. The "soft elicitation" is pre-registered for future work. **A NeurIPS reviewer would want the soft elicitation result before accepting the theory contribution as load-bearing.** Acceptable for a workshop paper / CS 285 final, less so for NeurIPS main track.

### E.4 The "1M update" Oracle-CF observation

- §5.6(E) lines 1673–1689 reports two seeds at 590k steps reaching 0.35/0.45 on PickAndPlace, suggesting Oracle-CF *would* clear the +0.10 threshold against HER@250k *if* HER hadn't moved. The paper then says "we do not have HER trained to 1M steps on the same task; without a matched comparator at 1M, we cannot determine whether the Oracle-CF–HER gap narrows, widens, or crosses the +0.10 threshold."
- This is **honest** but the Extended Abstract bullet (ii) claims "(verified-CF) crosses the criterion at 1M updates." Notice the swap: §5.6(E) is about **Oracle-CF** at 1M, not verified-CF. The Extended Abstract conflates them.

---

## F. Honest Negative Results — is the "cold-start" framing spin?

Re-read of the verified-CF cold-start framing.

### F.1 The framing in CS 285 main.tex

- Ext. Abstract lines 88–97 ("Honest negative result"): describes the 100% verifier-rejection rate over first ~80 VLM calls on PnP seed 42. Honest.
- §4.3 lines 1030–1051: explicitly states "calibration is a throughput dial." Honest.
- §6 (Discussion) Limitation (ix) lines 1890–1913: spells out the cold-start regime and pre-registers mitigations (base-policy warm-up, longer N, soft acceptance). Honest.
- Conclusion lines 1927–1933: "early in training — when the snapshot state sits far from the goal — the joint event ... can have near-zero base rate, reducing the channel to a strictly costlier HER until the underlying policy matures." Honest.

### F.2 Where the spin creeps in

The NeurIPS variant has *additional* claims that frame the cold-start as **transitory** and that verified-CF *eventually closes the gap* to vlm_cf (lines 1689–1715 of NeurIPS variant). The CS 285 paper **lacks these post-mature-policy results**, so the cold-start framing is the *last word* in the CS 285 paper on verified-CF training.

**This is actually the cleanest, most honest version of the story** — the CS 285 paper says "we tried verified-CF, it failed at cold-start, here's why" without the NeurIPS variant's claim that things eventually work. A harsh grader could read this either way:
- **Charitable:** This is a textbook "pre-registered falsification" honestly reported, which the outline rewards under Completeness ("results are discussed fully") and Analysis ("explain why the methods work or don't work").
- **Harsh:** The Extended Abstract bullet (i) still claims a positive result on Push/Slide that the body doesn't substantiate for verified-CF (only vlm_cf). The framing is **incoherent across abstraction levels**, not spin per se — but the result is the same: a grader is confused.

**Verdict:** The cold-start framing itself is honest and well-defended. The damage is from the *mismatch* between the Extended Abstract's positive bullet (i) and the body's negative finding. Fix the Extended Abstract and the framing is unimpeachable.

---

## G. The 36-Run Aggregate (Prior Existing Data)

This is the trickiest provenance question.

- §5.6(C) line 1627: "This matches the PER@3M asymptote of 0.95 and substantially exceeds HER@250k (0.617)."
- Where does "PER@3M asymptote of 0.95" come from? The CS 285 paper does NOT cite Plappert (verified). The number is **just stated**.
- Where does "HER@250k (0.617)" come from? **The kill experiment §5.6(A) line 1588 says HER on Push reached `0.550 ± 0.050`, not 0.617.** Where is the 0.617 number from? It is asserted, not derived.

Looking at the Contributions section (line 1965): "Parshawn Gerafian. Contributed to initial project scoping and the **prior 36-run ablation suite (PER / Semantic-PER with GPT-4o / Oracle-heuristic) that is referenced as foundational data in §5.1**."

But §5.1 (the Setup section, lines 1077–1140) is the env description — there is no foundational data discussed there. The 36-run aggregate is *implicit* in Fig. 1 (`fig1_headline_success.pdf`) which shows PER bars at much higher levels than the 250k HER numbers. The figure is a *mix* of:
- New 500k runs (Semantic PER GPT-4o, Semantic PER Oracle)
- Prior 36-run aggregate at longer horizons (PER, Uniform)

**The figure does not distinguish these.** A grader reading Fig. 1 sees four bars on each env and assumes they are comparable. They are not — the PER bar at 0.95 on Push is at 3M steps (per line 1627), while the Semantic-PER bars are at 500k (per line 1118 "All paper-grade training runs execute 500k environment steps").

**This is the biggest figure-honesty problem in the paper.** The 36-run aggregate's PER@3M result is *combined* with new 500k Semantic-PER results in the same chart, with no axis annotation telling the reader.

**Verdict:** The 36-run aggregate is *not clearly distinguished* from the new Phase 2 data. This is a significant transparency issue. A reviewer noticing this would flag the headline figure as misleading.

---

## H. Other Findings (rapid-fire)

- **Author / collaborator declaration:** The CS 285 outline (page 4) says outside collaborators must be listed. The Contributions section lists three students, no externals. If any external help was received (advisor, lab mate, GSI discussions during office hours that went beyond standard help), declaration is required. Daniel needs to verify.
- **Contributions section is placeholder-flagged:** Line 1952 has a literal `% TODO: Daniel to revise per-member attribution before submission` comment in the .tex. This comment is **not** visible in the rendered PDF (LaTeX comments are stripped) — but if Daniel forgets to revise, the placeholder attributions remain. Per the alignment plan §5 Q1.
- **Title footnote:** "CS 285 Final Project, Spring 2026" — correct.
- **Anonymity:** preprint NeurIPS style with full author names — appropriate for CS 285 (non-blind).
- **Page count:** 45 pp. (24 main + 21 appendix). Outline says "~8 pp." but "we will not penalize" longer. A grader who skims the Extended Abstract is OK; one who reads the full report may be fatigued. Per the alignment plan, Daniel chose option (a) "keep as-is." Defensible.

---

# PRIORITIZED FIX LIST

## P0 — Must fix before submission (~1h each, score-killing)

### P0.1 — Fix the Extended Abstract bullet (i) headline number contradiction
**File:** `agent_reports/paper_cs285/main.tex` lines 70–74.
**Current:** *"vlm_cf headline. At 500k SAC+HER+VLM-CF updates on FetchPush seed 0 the verified-CF agent reaches 0.95 success; on FetchSlide it reaches 0.55..."*
**Fix:** Choose ONE story line and commit:
- **Option A (recommended):** Use the NeurIPS variant's correct numbers — *"vlm_cf reaches mean 0.95±0.03 / 0.55±0.13 / 0.367±0.08 on Push/Slide/PnP at 500k; the simulator-verified counterfactual variant matches within Δ=0.02 in aggregate (0.606 vs 0.622), exceeding vlm_cf on Slide (0.617 vs 0.55) where prior baselines cluster near zero."* This requires pulling text from `agent_reports/paper/main.tex` lines 153–161.
- **Option B:** Drop the numerical headline entirely, keep only the framing — *"vlm_cf reaches a strong success rate on Push/Slide at 500k; full numbers in §5.6(C)."* Less impactful but avoids the contradiction.

### P0.2 — Update §5.6(C) with the completed Phase 2 verified-CF data
**File:** `agent_reports/paper_cs285/main.tex` lines 1610–1642 (the entire Part C block).
**Current:** Says PnP is "in flight at ~60% of budget."
**Fix:** Replace with the NeurIPS variant's lines 1656–1685 + add the Part (D) Verified-CF block (NeurIPS lines 1687–1715). Total: a new ~30-line block summarizing 18 completed runs. The numbers exist in the NeurIPS sister paper — copying them across is mechanical.

### P0.3 — Fix the undefined `tab:vlm_comparison` LaTeX reference
**File:** `agent_reports/paper_cs285/main.tex` line 1646.
**Current:** *"To sharpen the differentiation from \citet{sharony2026vlmrb} beyond the methodological comparison in Table~\ref{tab:vlm_comparison}, ..."*
**Fix:** Either (a) define the missing table (likely a side-by-side comparison Sharony / ours / Verified-CF), or (b) change `Table~\ref{tab:vlm_comparison}` to `Table~\ref{tab:differentiation}` (which is the existing table on line 456). Choice (b) is 1-minute, choice (a) is 30 minutes if a new table is added.

### P0.4 — Fix Extended Abstract bullet (ii): the kill verdict contradiction
**File:** `agent_reports/paper_cs285/main.tex` lines 74–78.
**Current:** Says "Phase 1 oracle-heuristic study triggered the pre-registered kill criterion (no separation by 300k updates); we honor the kill and re-allocate compute to Phase 2 (verified-CF), which crosses the criterion at 1M updates."
**Fix:** Correct the 300k → 250k typo, and remove the "1M updates crosses the criterion" claim because §5.6(E) explicitly says the kill verdict is NOT retracted at 1M. Replace with: *"(ii) Pre-registered Phase 1 kill verdict. Oracle-CF underperformed HER on FetchPickAndPlace by 0.05 success rate at the 250k decision horizon, well below our +0.10 threshold; the kill criterion fired and we pivoted the headline to the IS-posterior framing (§3, §4.1) and the simulator-verified counterfactual mechanism (§4.3)."*

### P0.5 — Fix Figure 1 caption (headline figure honesty)
**File:** `agent_reports/paper_cs285/main.tex` lines 1132–1146.
**Current:** Caption begins with "[Pre-fix run, retained for transparency.]" — a grader reading this immediately downgrades Completeness.
**Fix:** Either (a) replace Fig. 1 with `fig_headline_v3.pdf` (post-fix headline; check if it exists in `agent_reports/figs/`), or (b) rewrite the caption to lead with the *useful* signal: *"Headline ablation: PER, Oracle-localized Semantic PER, GPT-4o Semantic PER, Uniform on three Fetch envs at 500k steps. The GPT-4o curve uses the pre-fix all-variant prompt and is included for transparency on the pipeline bug discovery (see §5.7); the corrected (post-fix) results are the verified-CF and vlm_cf runs in §5.6(C)–(D), which exceed the GPT-4o curve here."* This re-frames the figure as a "before-fix vs. after-fix" demonstration rather than an admission of error.

---

## P1 — High-leverage polish (~30 min each)

### P1.1 — Annotate horizons in Fig. 1
**File:** `agent_reports/figs/fig1_headline_success.{pdf,png}` and the figure-generating script (find it via `grep -rn "fig1_headline_success" agent_reports/`).
**Action:** Add per-bar horizon labels (e.g., "3M steps" subscripts on PER bars, "500k" on Semantic-PER bars). If a single horizon is used, state it in the y-axis label or caption explicitly: *"Final success at 500k steps (PER, Uniform extrapolated from 3M-step asymptote)."* See §D.1 and §G above.

### P1.2 — Add Plappert 2018 citation to refs.bib
**File:** `agent_reports/paper_cs285/refs.bib`
**Action:** Copy the `@article{plappert2018multigoal,...}` entry from `agent_reports/paper/refs.bib` line 29. Then cite at the "PER@3M asymptote of 0.95" claim (line 1627 of `main.tex`) and in §5.1 setup paragraph as canonical baseline for Fetch asymptotic performance.

### P1.3 — Add zhao2018energy citation
**File:** `agent_reports/paper_cs285/refs.bib` and `agent_reports/paper_cs285/main.tex` §2 (Related Work).
**Action:** Copy `@inproceedings{zhao2018energy,...}` from the NeurIPS variant. Cite as a baseline for energy-based prioritized HER, in §2.1 HER discussion (around line 270).

### P1.4 — Resolve the placeholder Contributions attribution
**File:** `agent_reports/paper_cs285/main.tex` lines 1956–1971.
**Action:** The `% TODO: Daniel to revise` comment is still there. Daniel must replace the placeholder bullets with accurate attributions. NB: line 1965 attributes "the prior 36-run ablation suite" to Parshawn — this should be verified and the 36-run aggregate's provenance disclosed (see §G above). If Parshawn ran those experiments before the verified-CF work started, the attribution is correct; the figure caption then needs to acknowledge "PER baselines drawn from prior 36-run ablation suite at 3M steps."

### P1.5 — Add the Plappert HER+DDPG asymptote paragraph to §5.1
**File:** `agent_reports/paper_cs285/main.tex` after line 1116 (Evaluation protocol).
**Action:** Copy the paragraph from `agent_reports/paper/main.tex` lines 1106–1116 (begins "Canonical HER+DDPG asymptotes are approximately..."). This justifies the 500k-step horizon by referencing the published 8M-step asymptote and gives a grader a baseline reference. Two paragraphs of new text.

### P1.6 — Re-color the figures for palette consistency
**Files:** All `agent_reports/figs/fig*.{pdf,png}` generation scripts.
**Action:** Assign a consistent CB-safe palette across all figures:
- Uniform: grey
- PER: dark-blue
- Semantic-PER (Oracle): light-blue
- Semantic-PER (GPT-4o) / VLM-CF / Verified-CF: orange
- HER-only: black
Re-generate Fig. 3, 4, 5 with consistent labels. Per user memory entry on NeurIPS figure conventions.

### P1.7 — Add a head-to-head verified-CF vs vlm_cf table
**File:** `agent_reports/paper_cs285/main.tex` §5.6.
**Action:** Add a 3-row × 3-col table summarizing the 9-run Verified-CF and 9-run VLM-CF sweeps at 500k steps. This is the **single most-rescued exhibit** — it converts a "in-flight" claim to a completed comparison and is the figure a grader will use to validate the contribution. Source: NeurIPS variant lines 1687–1715.

### P1.8 — Fix Fig. 5 (real-vs-synthetic) caption numerical mismatch
**File:** `agent_reports/paper_cs285/main.tex` lines 1448–1461.
**Action:** Re-check the "75% → 0%" claim against the rendered figure bars. If the figure shows different rates than the caption says, fix the caption to match the figure.

### P1.9 — Tighten Extended Abstract bullet (iv) on Sharony
**File:** `agent_reports/paper_cs285/main.tex` lines 83–87.
**Current:** "A faithful re-implementation ... is pre-staged in our codebase for head-to-head comparison."
**Fix:** Reword to make clear no training-time numbers exist yet: *"(iv) **Sharony VLM-RB implementation.** We re-implement the concurrent VLM-RB priority formula (faithful to the original $\lambda$-schedule, clip length, with Sonnet 4.5 substituting for the non-API-accessible PerceptionLM) in our codebase. Head-to-head training results on Fetch are pending Modal queue release; the comparison is pre-registered for the camera-ready."* Honesty without overpromise.

### P1.10 — Add a one-sentence sample-efficiency framing
**File:** `agent_reports/paper_cs285/main.tex` Extended Abstract or §5.1.
**Action:** State explicitly that the 500k-step horizon is chosen because (a) Plappert's HER+DDPG converges by 8M, (b) prior 36-run aggregate shows PER@3M reaches 0.95 on Push, (c) we evaluate at 500k as a sample-efficiency comparison, not asymptotic comparison. One sentence in Ext. Abstract, one in §5.1.

---

## P2 — Nice-to-have (~15-30 min each)

### P2.1 — Add a (W, w_max) sensitivity sweep
The defaults W=5, w_max=10 are stated (line 689) but never ablated. A small ablation table (even 2-3 settings) would close a reviewer comment. Pre-registered in line 1875.

### P2.2 — Cross-judge sanity check on the prompt-design table
Use Sonnet 4.5 or GPT-4o as the judge for at least the load-bearing Opus vs GPT-4o `achieved_goal` row. Mitigates the judge-bias concern (§5.2 line 1325).

### P2.3 — Add unit-test pass-rate for the verified-CF gate
Line 998 says "A 4/4 smoke test ... confirms each design assertion." Just bump this to a few more synthetic episodes (10–20) to firm up the smoke test before the verifier runs.

### P2.4 — Move §3 (Theory) to appendix, leave 1-paragraph summary in body
Per alignment plan §3 m4. The theory section is 200+ lines in the main body; moving it to appendix would tighten the main body and align with the "~8 pp." outline guidance. Risk: cross-references. Reward: cleaner main body for grading.

### P2.5 — Add a "limitations honesty" framing paragraph at the top of §6
Currently §6 has 9 limitations stacked. Add a one-paragraph "what's missing and why" at the top to orient the grader.

### P2.6 — Add a verification budget line ("API cost / wall-clock")
The paper says VLM calls cost ≤$0.05 each (line 1133) but does not state total experiment dollar cost. A one-line "total API spend ~$X across all experiments" closes a reproducibility comment.

### P2.7 — Run the Sharony VLM-RB on at least 1 env / 1 seed
Even a smoke run on FetchPush at 100k steps with VLM-RB would convert §5.6(D) from "implemented, pending launch" to "pilot result available." This is the single P2 with the largest potential upside if Modal queue permits.

### P2.8 — Add a small heroic figure: "vlm_cf and verified-CF vs HER on Slide"
A 1-panel learning curve showing the +0.45 Slide gain (line 1632–1633) would be a visual headline. Currently the headline is buried in §5.6(C) prose. One Matplotlib figure, drop in §5.6.

### P2.9 — Tighten the "What this report contains" navigation paragraph
Lines 99–107 describe what's in the report. Trim by ~50% — graders skim navigation paragraphs. Move detail to appendix.

### P2.10 — Fix the "two-vendor three-model" framing
Lines 79–82 in Ext. Abstract and lines 1283–1286 in §5.2 both say "two-vendor three-model." This is honest (Opus and Sonnet are both Anthropic) but appears 6+ times in the paper — feels repetitive. Once in Ext. Abstract, once in §5.2 limitations, drop elsewhere.

---

## EXEC SUMMARY (for the agent assigning these tasks)

**If you can only do five things tonight, do P0.1–P0.5.** Those five fixes alone move the paper from a probable "Good" (75-90%) grade to a probable "Excellent" (90-100%) because they close the rubric's two weakest axes (Analysis and Completeness) without requiring new experiments.

**If you have an additional 2-3 hours:** Add P1.1, P1.2, P1.5, P1.7. These are the highest-leverage P1s for the harsh-grader concern about baseline citations and headline-figure honesty.

**The Sharony VLM-RB run (P2.7) is the single missed opportunity** — if it can be launched on Modal tonight even at a reduced scale (1 env, 1 seed, 250k steps), it converts the strongest reviewer complaint from a deficit to an asset.

**Do NOT:** Move §3 theory to appendix (P2.4) at the 11th hour — too risky for cross-references, low reward.

---

## A NOTE ON HONESTY

The CS 285 paper, taken as a whole, is *more* honest than most workshop papers I would grade. The "pre-fix run, retained for transparency" caption, the explicit kill-criterion violation in §5.6(A), the cold-start verifier-rejection regime in Limitation (ix), and the "we do not retract the pre-registered kill verdict" in §5.6(E) — these are all examples of strong scientific practice. **A grader who reads carefully will appreciate this and reward it.**

The problem is not honesty — the problem is that the Extended Abstract (which the grader reads first) does not reflect the body's honest version of the story. Fix P0.1 and P0.4 (the two Ext. Abstract bullets) and the project's honesty becomes a strength rather than a contradiction.

— end of critique —
