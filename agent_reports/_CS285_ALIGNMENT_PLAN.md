# CS 285 Final-Project Outline → Paper Alignment Plan

**Source outline:** `agent_reports/final_project_outline.pdf` (CS 185/285 Spring 2026, 4 pp.)
**Target paper:** `agent_reports/paper/main.tex` → `agent_reports/paper/main.pdf` (44 pp., NeurIPS preprint style)
**Branch:** `agent/pathc-lead`
**Date:** 2026-05-12

---

## Summary

**STATUS: DONE.** CS 285 paper variant built as a separate `paper_cs285/` directory; the original NeurIPS paper (`paper/`) is untouched. Final submission file is at `agent_reports/cs285_final_paper.pdf` (45 pages: 24 main + 21 appendix incl. references).

**Edits applied to `agent_reports/paper_cs285/main.tex` (NOT to `paper/main.tex`):**
1. **Extended Abstract** inserted as `\section*{Extended Abstract}` immediately after `\maketitle`, before the existing `\begin{abstract}` block. Covers: problem, two methodological contributions, four headline findings (incl. vlm_cf 500k Push 0.95 / Slide 0.55, Phase 1 kill verdict, prompt sweep, Sharony reproduction), honest verified-CF cold-start negative result, and a what's-in-this-report navigation paragraph. Renders to ~1.3 typeset pages.
2. **Contributions** section added with `% TODO: Daniel to revise per-member attribution` comment + placeholder bullets for Daniel Grant / Parshawn Gerafian / Matei Gardea. Renders on page 24 just before References.
3. **Title footnote** added: `\thanks{CS 285 Final Project, Spring 2026. UC Berkeley, Department of EECS.}` on the title — distinguishes this PDF from the NeurIPS variant on first glance.
4. **build.sh updated** to write to `../cs285_final_paper.pdf` instead of `../9pm_presentation.pdf` (so it doesn't clobber the NeurIPS paper's exported PDF).
5. Visual quality gate: `PASS: agent_reports/paper_cs285/main.pdf`.

**Daniel's remaining pre-submission items:**
- Revise the placeholder contribution attributions if any of them are inaccurate (search `paper_cs285/main.tex` for `% TODO: Daniel`).
- Optionally trim main body to ~8 pp. (not done; outline says no penalty for length).
- Confirm author-list completeness (no outside collaborators currently listed).

---

## 1. Outline summary (CS 285 final-report requirements)

The CS 185/285 final-project outline (Sergey Levine, Spring 2026) defines a **research-style workshop paper** as the final deliverable, worth 15% of the final grade (out of 20% project total). The outline is permissive on technical scope — "anything related to the content of the class" — but **strict on structure**: a one-page **Extended Abstract** must lead the report and is the primary grading artifact ("we will primarily use the extended abstract for grading"). The remaining required sections are Introduction, Related Work, Method, Experiments/Results, Discussion & Limitations, and a one-line-per-member **Contributions** statement. The recommended length is **~8 pages**, with no penalty for shorter/longer reports as long as length is "reasonable" — the appendix is implicitly tolerated.

Grading uses a four-tier rubric across four axes: **Novelty**, **Scope**, **Analysis**, and **Completeness**. The "Excellent (90–100%)" tier requires (i) "substantively original implementation or perspectives," (ii) "similar scope to a conference workshop paper," (iii) "compares with several baselines and ablations" with experiments that "explain why the methods work or don't work," and (iv) "all experiments are complete and results are discussed fully." The "Good (75–90%)" tier explicitly demands "**solid comparison with multiple baselines and some ablations**."

Format guidance: LaTeX preferred, NeurIPS template explicitly endorsed, PDF submission via Gradescope. The proposal and milestone components were already submitted on March 6 and April 6 respectively. Final report is due **May 13, 2026** (i.e., **tomorrow** as of the date stamp on this document).

Outside collaborators are permitted for CS285 students but must be explicitly listed with contribution attributions. Daniel's team appears to be three CS 285 students (Daniel Grant, Parshawn Gerafian, Matei Gardea) — no external collaborators in the current author block.

---

## 2. Gap analysis — present vs. required matrix

| Required component (CS 285)         | Present in `main.tex`?      | Status        | Notes                                                                                                                  |
|-------------------------------------|------------------------------|---------------|------------------------------------------------------------------------------------------------------------------------|
| **Extended Abstract (1 page)**      | NO — only NeurIPS `abstract` | **MISSING**   | Existing `\begin{abstract}` is the dense NeurIPS abstract (33 lines, ~3/4 page). Need a separate 1-page "what / main findings" extended abstract per outline.                                                       |
| **Introduction**                    | YES (line 68)                | OK            | Strong: 4-contribution roadmap, well-cited.                                                                            |
| **Related Work**                    | YES (line 179)               | OK            | Substantial — HER, PER lineage, VLM-in-RL, FM-credit-oracle. Outline says "can be brief" so length is acceptable.       |
| **Method**                          | YES (line 575)               | OK            | Three subsections (Semantic PER, Counterfactual prompting, Verified CF).                                                |
| **Experiments/Results**             | YES (line 998)               | OK            | Six subsections incl. headline ablation, prompt design, cross-task, real-data, kill experiment.                          |
| **Discussion & Limitations**        | YES (line 1660)              | OK            | Substantial (~220 lines) with Broader Impact + 9 limitations.                                                            |
| **Contributions (per team member)** | NO                           | **MISSING**   | Outline requires one-line per member. Currently only an author block with no per-member contribution split.              |
| **NeurIPS template**                | YES (`neurips_2024.sty`)     | OK            | Already uses `\usepackage[preprint]{neurips_2024}`.                                                                      |
| **PDF deliverable**                 | YES                          | OK            | `agent_reports/paper/main.pdf` builds cleanly (44 pp.).                                                                  |
| **Multiple baselines**              | YES                          | OK            | SAC+HER, PER, Semantic-PER, VLM-RB (Sharony), Oracle-CF, VLM-CF — all in §5.                                              |
| **Ablations**                       | YES                          | OK            | Prompt-design ablation (3 models × 2 prompt types), oracle-vs-VLM, real-vs-synthetic.                                    |
| **Length ≈ 8 pp.**                  | 44 pp. total (main + appx.)  | **NOTE**      | Main body alone is ~17 pp.; appendix adds ~27 pp. Outline does not penalize length but says "keep reasonable." See open Q3. |

**Bottom line:** The two required *content* gaps are (1) Extended Abstract and (2) Contributions section. All other structural requirements are met. Length is the only soft concern, and the outline explicitly does not penalize.

---

## 3. Edits needed

### Major (content/structure)

**M1. Extended Abstract.** Insert a 1-page `\section*{Extended Abstract}` block right after `\maketitle`, before the existing `\begin{abstract}`. Content: a self-contained "what we did + main findings" summary suitable for grading — covers (a) the problem, (b) the two methodological contributions, (c) the three headline empirical findings, (d) the pre-registered null result. Length target: ~3/4 page typeset (NeurIPS column).

**M2. Contributions section.** Add `\section*{Contributions}` before `\bibliographystyle{plainnat}` with one bullet per author. Default content is a placeholder Daniel will need to revise — see open Q1.

### Minor (format/citation)

**m3. Cross-reference cleanup.** Add `\label` to the Extended Abstract if we want to refer to it; not required.

**m4. Optional: trim main body.** The CS 285 outline says "about 8 pages... we will not penalize shorter or longer reports, but please keep the length reasonable." Our main body is ~17 pp. The appendix (27 pp.) is universally accepted. If Daniel wants to be strictly conservative, candidate trim targets are:
- §3 Theoretical Motivation (lines 397–574) → move to appendix, leave 1-paragraph summary
- §4.2 Counterfactual Prompting subsection (lines 745–882) → can compress
- §5.1 Setup (lines 1001–1084) → can compress figure environment to half-column

We are **NOT** applying these trims in this pass — see open Q3.

---

## 4. Prioritized edit list (top 5)

| # | Edit                                       | LOC impact        | Risk | Priority |
|---|--------------------------------------------|-------------------|------|----------|
| 1 | Insert Extended Abstract (`\section*`)     | +35–45 lines      | Low  | **P0**   |
| 2 | Insert Contributions section               | +12 lines         | Low  | **P0**   |
| 3 | Verify build + check page numbering        | 0                 | Low  | **P1**   |
| 4 | Author-list / external-collab declaration  | 0–4 lines         | Low  | **P2** (open Q1) |
| 5 | Optional main-body trim to ≤10 pp.         | −400 to −600 lines | Med  | **P3** (open Q3) |

---

## 5. Open questions for Daniel

**Q1. Per-author contribution attributions.** The CS 285 outline requires "one-line (per team member) description of their contribution." I inserted placeholder bullets for Daniel Grant, Parshawn Gerafian, and Matei Gardea — these need to be **rewritten by Daniel before submission** to accurately reflect each member's actual contribution (theory, implementation, experiments, writing, etc.). Search for `% TODO(daniel): contributions` in `main.tex`.

**Q2. External collaborators?** The outline says CS 285 students with "outside collaborators... must be listed." Current author block has no externals. If there are unlisted collaborators (e.g., lab-mates, advisors providing input), declare them now per the outline's strict requirement.

**Q3. Main-body length policy.** Outline says ~8 pp. recommended but explicitly does *not* penalize longer. Three options:
- **(a) Keep as-is** (44 pp.): defensible under "we will not penalize... longer reports." Risk: graders might still skim. Reward: nothing to do.
- **(b) Move §3 theory to appendix**, leaving a 1-paragraph summary in the main body. Cuts ~180 lines from main, drops to ~14 pp. main + ~30 pp. appendix.
- **(c) Aggressive trim to ~10 pp. main body**, sweeping theory + prompt-design details to appendix. Cuts ~400+ lines, risky for cross-references and figure placement.

**My recommendation:** **(a) Keep as-is** for the submission deadline tomorrow. The graders explicitly said no penalty; the extended abstract now serves as the "skim layer." Defer (b)/(c) to a post-deadline cleanup.

---

## 6. Files touched in this pass

- `agent_reports/paper/main.tex` — inserted Extended Abstract + Contributions sections.
- `agent_reports/paper/main.pdf` — rebuilt via `bash build.sh` (post-edit).
- `agent_reports/_CS285_ALIGNMENT_PLAN.md` — this document.

Nothing in `agent_reports/paper/appendix.tex` was modified. No bibliography or figure files changed. No in-flight training touched. No new experiments launched.
