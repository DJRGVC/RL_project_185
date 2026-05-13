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

YOUR TASKS (do TASK 0 FIRST, then TASK 1-14 surgically)

### TASK 0 — Analyze Matei's MetaWorld PR and integrate strategically (DO FIRST, ~15 min)

There is an OPEN PR #1 on `DJRGVC/RL_project_185` titled "Auxiliary MetaWorld study: replay-mechanism ablation" from `mateig:main` (Matei's fork). Opened 2026-05-13.

**What it contains** (per PR body):
- 60-run sweep: 3 MetaWorld tasks × 4 replay variants × 5 seeds, 130.5 L4-GPU-hours
- Finding: PER beats uniform in sparse-reward SAC on MetaWorld across all 3 tasks (+0.12-0.44 final-success, steps-to-0.8 ~halved). **Refutes pre-registered H3.**
- Demo content saturates easy tasks but not `sweep-into-v3`
- 3 figures + results table with bootstrap CIs
- Code trace for demo-replay==demo-priority implementation collapse at `src/replay.py:71`
- 5 new bib entries: vecerik2017ddpgfd, hester2018dqfd, rajeswaran2017dapg, nair2018overcomingexploration, yu2019metaworld
- 45,470 additions across 33 files (mostly the experiment dir + a few paper paragraphs)

**ACTIONS**

(a) Inspect the PR rigorously:
```bash
gh pr view 1 --repo DJRGVC/RL_project_185
gh pr diff 1 --repo DJRGVC/RL_project_185 --name-only
# Read the proposal + key result files:
gh pr diff 1 --repo DJRGVC/RL_project_185 -- experiments/metaworld_replay_ablation/proposal.md
gh pr diff 1 --repo DJRGVC/RL_project_185 -- experiments/metaworld_replay_ablation/results/manifest.json
gh pr diff 1 --repo DJRGVC/RL_project_185 -- experiments/metaworld_replay_ablation/results/efficiency.json
# Read the proposed paper additions:
gh pr diff 1 --repo DJRGVC/RL_project_185 -- agent_reports/paper/main.tex | head -200
gh pr diff 1 --repo DJRGVC/RL_project_185 -- agent_reports/paper/appendix.tex | head -200
```

(b) Verify rigor:
- Are the bootstrap CIs computed correctly?
- Does "PER beats uniform" match our existing 36-run aggregate (Push 0.95 vs 0.08)? It should — this is cross-benchmark corroboration.
- Is the "demo-replay == demo-priority" finding a real bug or a design choice?
- Are the 5 bib entries real (verify arxiv/doi)?

(c) Decide for the **CS 285 paper** (your editing scope):
- If the MetaWorld data substantively strengthens the narrative AND fits within the 11pp ceiling: integrate ONE PARAGRAPH (~0.4pp) in §6 Discussion as "Cross-benchmark corroboration on MetaWorld." Cite Matei's experiments/ directory.
- If integration would force overflow OR the data is orthogonal: SKIP for CS 285. Write a skip-note in `_PASS_3_FINAL_POLISH.md` explaining the decision.
- DO update Matei's contribution bullet to acknowledge the MetaWorld sweep (60-run, 130 GPU-h is substantial). The user's verbatim attribution covers his earlier alternative VLM-replay variant; this is additional substantial work. Add a clause: "...; later ran a 60-run MetaWorld replay-mechanism ablation reported in Appendix [if integrated] / [omitted for length]."

(d) Decide for the **NeurIPS paper** (`agent_reports/paper/main.tex`):
- The PR's proposed paper paragraphs target this paper directly. Merge intent vs cherry-pick:
  - **DO NOT use `gh pr merge`** — there are likely conflicts with our overnight edits.
  - INSTEAD: textually integrate Matei's proposed paragraphs into our current main.tex + appendix.tex via Edit tool, preserving our existing structure.
  - Copy in: the Related Work paragraph (Demonstration-augmented replay), the Discussion paragraph (Cross-benchmark corroboration on MetaWorld), the Appendix section (Auxiliary Study), the 5 new bib entries, the 3 figure PNGs (copy to `agent_reports/figs/`).
  - Note: the NeurIPS paper has no strict page ceiling (currently 49pp), so adding ~2pp of MetaWorld content is fine.

(e) Also: copy Matei's `experiments/metaworld_replay_ablation/` directory to our main branch (cp from the PR's branch via `git checkout origin/pr/1 -- experiments/` or equivalent). This preserves Matei's code so it's reproducible.

(f) Commit Matei's integration separately from the mechanical polish: "Integrate Matei's MetaWorld replay-mechanism ablation (PR #1, 60-run sweep, cross-benchmark corroboration)"

(g) Push the integration commit. Then proceed to TASK 1.

(h) Do NOT close PR #1 — Matei should review and close it himself. Just leave a comment on PR #1: `gh pr comment 1 --body "Integrated into agent/pathc-lead via commit <SHA>. Thank you for the cross-benchmark corroboration; the MetaWorld PER>Uniform finding strengthens the §6 Discussion and now appears in Appendix [X]. Closing manually after Daniel reviews."`

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
