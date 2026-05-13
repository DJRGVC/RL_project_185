# CS 285 Final Project — Grader Reference

**Source:** Daniel's verbatim copy of the CS 185/285 Spring 2026 Final Project Outline (Sergey Levine)
**Last updated:** 2026-05-13 00:50 PDT
**Operational use:** every overnight agent should cross-reference this file before paper edits.

## Project context
- **Section**: CS 285 (graduate), **custom project route** (Daniel chose, not the 185 default)
- **Team size**: 3 students — Daniel Grant, Parshawn Gerafian, Matei Gardea (all CS 285 students at UC Berkeley)
- **No outside collaborators** — must verify no external contributors are listed
- **Lead author requirement**: not applicable (no outside collaborators)

## Deadlines (all 11:59 PM via Gradescope)
- Project Proposal: March 6, 2026 ✅ (submitted)
- Milestone Report: April 6, 2026 ✅ (submitted)
- **Final Report: May 13, 2026 — TODAY** ⚠️
- Worth 15% of final grade (out of 20% project total; proposal 2.5%, milestone 2.5%)

## What graders evaluate (the FULL rubric matrix, VERBATIM from outline)

**THE EXTENDED ABSTRACT IS THE PRIMARY GRADING ARTIFACT.** Direct quote:
> "We will primarily use the extended abstract for grading, and refer to your methods and experiments if we need to better understand the correctness of the solution."

The 1-page Extended Abstract must, on its own, convince graders that the project is **Excellent** across all 4 rubric axes.

### Four-axis rubric matrix (VERBATIM, all four columns)

| Axis | Poor (0-50%) | Fair (50-75%) | Good (75-90%) | **Excellent (90-100%)** |
|---|---|---|---|---|
| **Novelty** | Replicates existing work without new contributions or perspectives. | Applies existing work to a new environment without novel perspective. | Replicates existing work with some modifications. | **Substantively original implementation or perspectives.** |
| **Scope** | No implementation effort, e.g., running existing code on existing problem without in-depth analysis. | Relatively little implementation or analysis effort per group member. | Nearly ambitious enough for a workshop paper, with some missed opportunities. | **Similar scope to a conference workshop paper.** |
| **Analysis** | No comparison with baselines or ablations. Experiments do not evaluate the proposed problem. | Experiments are trivial/superficial/do not test the proposed setting. Inappropriate baselines or ablations. | Solid comparison with multiple baselines and some ablations. Experiments effectively test the problem setting. | **Compares with several baselines and ablations. Experiments are well thought-out and explain why the methods work or don't work.** |
| **Completeness** | No results due to incomplete implementation or training failure. Key elements are missing or not functional. | Implementation with significant issues. Experiments fail to effectively compare methods (e.g., all methods are identical). | Substantially complete. Experimental results differentiate between methods but may lack some discussion. | **All experiments are complete and results are discussed fully.** |

### Our target: Excellent on ALL 4 axes (target 100%)

| Axis | Evidence for Excellent | Status |
|---|---|---|
| **Novelty** | IS-posterior reweighting framing + multiplicative-vs-additive Sharony differentiation + Verified-CF sim-fork + two-regime degeneracy taxonomy + adaptive-filter insight (§2.4) | ✅ original substantive |
| **Scope** | 3 envs × n=3 seeds at multiple horizons + 2 methodological contributions + 4+ baselines + multiple ablations | ✅ workshop-paper scope IF main body trimmed to ~8pp |
| **Analysis** | Per-env mechanism explanations (§6 (ix) transitory cold-start; §5.5 policy-precision; §2.4 adaptive-filter); multiple baselines (HER, PER, Oracle-CF, Sharony, vlm_cf, verified_cf); ablations (p_counterfactual sweep, 2×2 prompt) | ✅ "WHY" explanations present |
| **Completeness** | All cited results must be done + discussed. NO "in flight" wording in final paper. | ⚠️ Wave B + matched-horizon HER@500k may not finish before submission — anything not done must be cut from claims |

## Required Sections (per outline)

| Section | Required content | Our paper |
|---|---|---|
| **Extended Abstract** | 1 page, "complete description of what you did and main findings" | Has it — must polish to be GRADER-PERFECT |
| Introduction | Context + key contributions | Has it — §1 contribution bullets just refined |
| Related Work | Differentiation from prior work | Has it — §2 with Sharony 2026 differentiation |
| Method | How the approach works | Has it — §3 + §4 |
| Experiments/Results | How conducted + results discussion | Has it — §5 |
| Discussion & Limitations | Summary + limits | Has it — §6 with 9 limitations |
| **Contributions** | One-line per member | Has placeholders — **Daniel must verify before submission** |

## Length and Format Guidance (VERBATIM from outline)

### Length
> "The full report should be about **8 pages** in length; we will not penalize shorter or longer reports, but please keep the length reasonable."

### Format
> "You should preferably use **LaTeX**, and you are welcome to use the **NeurIPS template**. The final report should be submitted as a **PDF to Gradescope**."

### Extended Abstract length
> "Your report should start with a **1-page extended abstract**"

### Required Sections (verbatim from outline)
- Extended Abstract (1 page)
- Introduction
- Related Work (can be brief)
- Method
- Experiments/Results
- Discussion & Limitations
- Contributions (one-line per team member)

### HARD page targets (USER MANDATE 2026-05-13 02:15 PDT)

- **Main body: 8 pages** (matches outline "about 8 pages" target)
- **Appendix: ~5 pages MAX**
- **Total: ~13 pages** (current 42pp must be cut to ~13pp — 70% reduction)

### Current state
- CS 285 paper total: 42 pages (1.0 MB PDF) — **MUST CUT TO ~13 PAGES**
- Main body: 17 pages (cut to 8)
- Appendix: 25 pages (cut to ~5)

### Trim allocation (8 pages main body)

| Section | Target pages | What to keep |
|---|---:|---|
| Extended Abstract | 1.0 | Verified-CF mean 0.606 + Slide win 0.617 + IS-pairing principle + adaptive-filter; honest negative (transitory cold-start) |
| §1 Introduction | 1.0 | Problem framing + 4 contribution bullets (high level only) |
| §2 Related Work | 0.5 | Sharony differentiation (multiplicative vs additive IS-pairing) — concise |
| §3 Method | 1.5 | Semantic PER (IS-posterior) + Verified-CF (sim-fork); ONE equation each; details to appendix |
| §4 Experiments/Results | 2.5 | fig_headline_v4 + per-env numbers in prose + §5.6 (C)(D) integrated |
| §5 Discussion & Limitations | 1.0 | §6 (ix) transitory cold-start + 2-3 other limitations + future work |
| §6 Contributions | 0.5 | Per-member 1-line bullets |

### Appendix allocation (~5 pages)

ONLY the most essential supporting material. Cut ruthlessly. Suggested:
- A. Hyperparameter tables (0.5 pp)
- B. Bias-bound proof sketch (1 pp) — full proof at GitHub
- C. Per-env reproduction notes (1 pp)
- D. 2-3 supporting figures from §5.3-§5.5 if needed (1.5 pp)
- E. Broader impacts (1 pp)

### Hard guardrails — DO NOT cut

1. **Extended Abstract** (graders' primary artifact)
2. **fig_headline_v4** with horizon stamps
3. **Verified-CF empirical numbers** (Push 0.85, PnP 0.35, **Slide 0.617**, mean 0.606)
4. **vlm_cf empirical numbers** (Push 0.95, PnP 0.367, Slide 0.55, mean 0.622)
5. **§1 contribution bullets** (named contributions)
6. **§6 (ix) transitory cold-start framing**
7. **Per-member Contributions section**
8. **At least 2 baselines + 2 ablations cited** (for Analysis rubric Excellent)
9. **At least one "explain why the method works" passage** (Analysis rubric language)

### Cut targets (in priority order)

1. §3 long-form derivations → appendix
2. §5.3 / §5.4 / §5.5 sub-analyses → appendix summary or cut entirely
3. §6 (i)-(viii) limitations → keep 2-3 most important in main, cut rest
4. Appendix sections B.1, B.2, B.3 (V-trace specializations, two-regime taxonomy) → cut or 1-paragraph summary
5. Appendix D-G → cut or merge
6. Bib entries not cited in body → remove

## Anti-patterns to avoid (would cost points)

1. **Overclaiming**: e.g., "strictly more informative" without data (R1 W12 flag, already softened)
2. **Cross-horizon comparisons without explicit annotation**: "vlm_cf@500k beats HER@250k" is unfair without saying "at half the training"
3. **Missing baselines**: graders WILL ask "where's HER+PER?" — Wave B addresses this
4. **Internal contradictions**: Abstract vs §5.6 vs Conclusion — must agree on numbers
5. **Placeholder text**: any `% TODO` or `XXX` left in final version
6. **Orphan figures**: figures referenced but not present, or present but unreferenced
7. **Undefined refs**: `??` in compiled PDF
8. **Hyperbole**: "striking", "remarkable" should be replaced with concrete numbers

## What we have over a typical 285 project

- 65+ git commits across 24 hours of intensive work
- 46-page paper with extensive appendix (B.1/B.2/B.3 IS-machinery, C reproducibility, D ablations, E reproducibility checklist, F broader impacts, G additional tables)
- 21 W&B-tracked training runs (vlm_cf × 3 envs × 3 seeds + verified_cf × 3 envs × 3 seeds + Oracle-CF 1M × 3 seeds + HER@1M × 3 seeds + 36-run prior aggregate)
- 4 NeurIPS-grade figures (env screenshots, headline bars, learning curves, cross-task)
- Multiple ablation studies documented (p_counterfactual sweep, 2×2 prompt, prompt-design sweep)
- Public GitHub repo (DJRGVC/RL_project_185) with full code, README, reproducibility info
- Both reviewer feedback rounds (R1 + R2) addressed in commits

## Lethal failure modes (would tank score)

1. **Extended Abstract overlong** (>1 page typeset) — pinpoint the 4 most important findings and cut everything else
2. **Per-member contributions inaccurate** — Daniel must personally verify before Gradescope upload
3. **Compiled PDF has undefined references** (`??` in text) — always check after final compile
4. **Bibliography missing entries** — every \cite{} must resolve
5. **Author list wrong order** — verify on Gradescope's expected format
6. **External collaborators omitted** — N/A for us (no external)
7. **PDF doesn't compile or has missing fonts** — always test on a clean LaTeX install if possible
