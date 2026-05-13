# Pass 3/3 prompt — QUEUED to fire as soon as Pass 2 commits

**Wait condition:** Pass 2 (agent `aac8bb825ca5bbd1c`) must have committed and pushed before this fires.

**Detection signal:** `agent_reports/_PASS_2_COMPREHENSIVE.md` exists on disk AND `git log --oneline -1` shows a "Pass 2" commit.

When triggered, fire the prompt below as an Opus 4.7 agent, 45-min budget.

---

## Pass 3 Prompt (final polishing)

PASS 3/3 — FINAL MECHANICAL POLISH for CS 285 paper at /home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185. 45-min budget. Opus 4.7.

You are the LAST pass before submission. Pass 1 (data rigor) and Pass 2 (comprehensive) already landed. Your job: catch every small mechanical issue without re-litigating content.

INPUTS (read in order)
1. `agent_reports/_GRADER_REFERENCE.md` — rubric + 11pp ceiling + hard guardrails (still apply)
2. `agent_reports/_PASS_1_DATA_FIXES.md` — Pass 1 changes
3. `agent_reports/_PASS_2_COMPREHENSIVE.md` — Pass 2 changes (must exist before you fire)
4. `agent_reports/_USER_CONTRIBUTIONS_VERBATIM.md` — Daniel's exact per-member attribution (MUST APPLY)
5. `agent_reports/_FEEDBACK_AGENT_10_proofread.md` — 64 mechanical issues catalogued
6. `agent_reports/paper_cs285/main.tex` — paper
7. `agent_reports/paper_cs285/build.log` — LaTeX warnings

YOUR TASKS (apply ALL surgically — small mechanical issues only, NO content rewrites)

### TASK 1 — Apply Daniel's verbatim per-member contributions (HIGHEST PRIORITY)
Read `agent_reports/_USER_CONTRIBUTIONS_VERBATIM.md`. Replace the `\begin{itemize}...\end{itemize}` block inside `\section*{Contributions}` with the EXACT LaTeX from that file. Do NOT interpret or embellish — paste verbatim.

### TASK 2 — Acronyms defined on first use (Agent 10)
For each of: CF (counterfactual), IS (importance sampling), TD (temporal difference), SE (standard error), SAC (soft actor-critic), PER (prioritized experience replay), HER (hindsight experience replay), VLM (vision-language model), CF-HER, MDP — verify they're defined on first use. Add definitions in parentheses if missing. Most-likely-missing: SAC, IS, TD, SE.

### TASK 3 — Quote/punctuation hygiene
- Replace ASCII straight quotes (`"..."`) with TeX quotes (`\`\`...''`) throughout paper_cs285/main.tex and appendix.tex
- Specifically: appendix.tex L200-202 has 3 `\emph{"..."}` instances (Agent 10 flagged)
- Em-dash vs en-dash: `--` for ranges, `---` for breaks — make consistent

### TASK 4 — Spacing consistency
- "Opus 4.7" vs "Opus~4.7" — pick ONE convention and apply globally (recommend `~` for non-breaking)
- "Sonnet 4.5" / "GPT-4o" / "Claude" — apply same convention
- Inter-symbol spacing in equations (`,` vs `,\,`)

### TASK 5 — Decimal place consistency in numbers
- Pick 3 decimal places (e.g., 0.617 not 0.62) and apply throughout the headline numbers
- Exception: percentages can use 2 decimal places (e.g., 0.95)

### TASK 6 — Norm notation
- Standardize on `\|\cdot\|_2` (not bare `\|\cdot\|`) for the L2 norm where ambiguous
- Specifically check the bias-bound section

### TASK 7 — Math-in-text-mode bugs
- Verify all `\beta`, `\mu`, `\sigma` references are in math mode (`$\beta$` not `\beta`)
- Agent 10 flagged appendix prompt template (L17-19) with math inside `\texttt{}` — confirm Pass 2 fixed it; if not, fix here using `$...$` or `\verb`

### TASK 8 — LaTeX warnings
- Read fresh `build.log` after recompiling
- Address any overfull/underfull hbox warnings ≥10pt by tweaking spacing
- Verify Table 2 in appendix (Agent 01 flagged 20.85pt overfull) was fixed in Pass 2 — if not, add `@{}` to tabular spec

### TASK 9 — Reference resolution
- Verify zero undefined `\ref{}` or `\cite{}` (any `??` in PDF)
- Verify every `\label{}` is actually referenced somewhere (remove orphan labels if any)

### TASK 10 — Remaining placeholders
- grep for `% TODO`, `\todo`, `XXX`, `???`, `TBD`, `FIXME` — should be ZERO remaining
- grep for `[NEEDS CITATION]`, `[CITATION NEEDED]` — should be ZERO

### TASK 11 — Misattributions (Agent 10 + intuition)
- Verify HER@250k Slide value is **consistently 0.183** throughout (Pass 1 fixed §5.4 from 0.100 → 0.183; double-check no other section still says 0.100)
- Verify HER@250k Push is **0.617** consistently
- Verify Sharony 2026 (`sharony2026vlmrb` or whichever bib key) is attributed correctly each cite — they didn't run Fetch, so don't claim Fetch numbers from them

### TASK 12 — Spelling + grammar pass
- Read every page of the rendered PDF inline (pdftoppm -r 150)
- Flag typos, doubled words ("the the"), subject-verb disagreement
- Verb-tense consistency (past vs present in results discussion — pick one)

### TASK 13 — Final compile + page count check
- Rebuild: `cd agent_reports/paper_cs285 && bash build.sh`
- Verify final page count is 11pp (or 12 if Pass 2 added a Sharony sentence — acceptable)
- Verify cs285_final_paper.pdf is current

### TASK 14 — Snapshot final + commit
- `cp agent_reports/cs285_final_paper.pdf agent_reports/cs285_final_paper_FINAL_2026-05-13_HHMM.pdf`
- Commit: "Pass 3/3: final mechanical polish (contributions verbatim, acronyms, quotes, spacing, decimals, LaTeX cleanup)"
- Push both branches: `git push origin agent/pathc-lead && git push origin agent/pathc-lead:main`

OUTPUT
Write `agent_reports/_PASS_3_FINAL_POLISH.md` with:
- Tasks completed (1-14 checklist)
- Issue counts: typos found, acronyms added, quotes converted, warnings cleared
- FINAL PDF page count
- Final visual verification: render p1 (Ext Abstract), p4 (Method), p11 (Contributions) inline
- Final verdict: **"READY FOR DANIEL TO SUBMIT TO GRADESCOPE"** or specific blockers if any

CONSTRAINTS
- Opus 4.7. Use venv.
- **EDIT ONLY paper_cs285/main.tex + appendix.tex + refs.bib.**
- NO content rewrites — surgical mechanical fixes only.
- Preserve Pass 1 and Pass 2 changes.
- Preserve hard guardrails per `_GRADER_REFERENCE.md`.
- The user's verbatim contributions text in `_USER_CONTRIBUTIONS_VERBATIM.md` is THE source of truth — paste verbatim, do not edit.

START IMMEDIATELY (this is the final pass).
