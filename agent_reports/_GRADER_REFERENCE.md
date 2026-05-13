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

## What graders evaluate (the rubric)

**THE EXTENDED ABSTRACT IS THE PRIMARY GRADING ARTIFACT.** Direct quote:
> "We will primarily use the extended abstract for grading, and refer to your methods and experiments if we need to better understand the correctness of the solution."

The 1-page Extended Abstract must, on its own, convince graders that the project is excellent across all 4 rubric axes.

### Four-axis rubric — what "Excellent (90-100%)" means

| Axis | Excellent (90-100%) | Our status |
|---|---|---|
| **Novelty** | "Substantively original implementation or perspectives" | ✅ IS-posterior framing of Semantic PER + Verified CF via sim-fork + two-regime degeneracy taxonomy + generator-verifier dichotomy |
| **Scope** | "Similar scope to a conference workshop paper" | ✅ 46pp NeurIPS-style paper. CS 285 paper at 45pp — **but main body too long; needs trim to 8-12pp** |
| **Analysis** | "Compares with several baselines and ablations. Experiments are well thought-out and **explain why the methods work or don't work**" | ✅ HER + PER + Oracle-CF + Sharony repro + p_counterfactual sweep + 2×2 prompt ablation. ⚠️ "Why" explanation: §6 (ix) transitory cold-start, §5.5 policy-precision bridge — must be prominent in Extended Abstract |
| **Completeness** | "All experiments are complete and results are discussed fully" | ⚠️ At risk: HER@1M finishing overnight, p_counterfactual sweep finishing ~02:00, Wave B running until ~21:00 tmrw. **Anything cited must actually be complete by submission.** |

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

## Length guidance (verbatim from outline)
> "The full report should be about **8 pages** in length; we will not penalize shorter or longer reports, but please keep the length reasonable."

**Current state**: CS 285 paper is 45 pp (24 main + 21 appendix). Way over.

**Bulletproofing recommendation**:
- Main body: trim to **8-12 pages** (NeurIPS workshop-paper convention)
- Appendix: keep as-is (~21pp); appendix is universally tolerated by NeurIPS-style graders
- Final target: ~10pp main + 21pp appendix = 31pp total

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
