# Sequential Edit Pipeline — CS 285 Paper

**Started:** 2026-05-13 morning
**Goal:** maximize CS 285 grade by applying the 10-agent review feedback in 5 surgical passes
**Hard constraint:** keep paper at ~11pp (under 8+5pp ceiling)
**Target:** rubric Excellent on all 4 axes; predicted grade 95+

## ⚠️ PIPELINE CONSOLIDATED TO 2 PASSES (user mandate 2026-05-13)

| # | Focus | Reads | Writes |
|---|---|---|---|
| **1** | P0 data-rigor BLOCKERS | Agent 04 (rigor) | `_PASS_1_DATA_FIXES.md` |
| **2** | Comprehensive sweep: citations, de-AI writing, rubric upgrades, story arc, visual polish, mechanical proofread | Agents 01, 02, 03, 05, 06, 07, 08, 09, 10 + Pass 1 handoff | `_PASS_2_COMPREHENSIVE.md` |

## Handoff convention

Each agent writes its handoff note at the end of its work. The next agent reads:
1. This file (pipeline state)
2. The relevant feedback agent file(s) for its angle
3. Previous pass's `_PASS_N_*.md` handoff note

## Standing constraints across all 5 passes

- **Edit `paper_cs285/main.tex` + `paper_cs285/appendix.tex` ONLY**
- **DO NOT touch `paper/main.tex`** (NeurIPS preprint, separate file)
- **Preserve 11pp page ceiling** (8 main + 3 appendix)
- **Preserve hard guardrails** per `_GRADER_REFERENCE.md`: Ext Abstract, fig_headline_v5, verified-CF numbers, §1 bullets, Contributions, all cited figures
- **Compile + visual gate after every commit**
- **Commit + push to both branches after every pass**
