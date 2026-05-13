# APPENDIX-WRITER handoff

**Agent**: APPENDIX-WRITER
**Branch**: `agent/pathc-lead`
**Commit**: `1de84cf` ("Add comprehensive NeurIPS appendix (sections B-H, ~14 pages)")
**Date**: 2026-05-11
**Budget**: 3 h (well under)

## Deliverable

`agent_reports/paper/appendix.tex` (new, 957 lines, ~14 PDF pages of
appendix content).
`agent_reports/paper/main.tex` modified to `\input{appendix}` before
`\end{document}`.

PDF total: **25 pages** (10 main body + 15 appendix pages including
the pre-existing Appendix A).

## Sections written

| Section | Content |
|---|---|
| A | (pre-existing) Prompt Template and Implementation Details |
| **B.1** | Algorithm pseudocode --- Algorithm 1 (Semantic PER) and Algorithm 2 (Verified-CF), full step-by-step. |
| **B.2** | Notation glossary --- 30-entry tabular reference with first-use section citation. |
| **B.3** | Heuristic localizer (Oracle v3) --- extended geometric reasoning per env (Push contact-loss, PickPlace ballistic-vs-argmin precedence, Slide release-point detection). |
| **B.4** | Counterfactual prompt templates --- verbatim text for all 4 variants (narrative, action, achieved_goal, all), plus task-description substitutions. |
| **C.1** | IS-posterior derivation --- 5-step derivation from uniform-replay target to the strictly-correct Semantic-PER IS-corrected estimator (Eq.~\ref{eq:sem-corrected}); explicit treatment of the under-correction. |
| **C.2** | Connection to V-trace and Retrace --- specialization argument and analogy to truncation bias. |
| **C.3** | Conditions for unbiasedness --- A1--A4 (bounded boost, strict IS correction, posterior independence of $\theta$, posterior support). |
| **D.1** | Hyperparameter tables --- 5 tables: SAC, HER, PER, Semantic PER, VLM call parameters. |
| **D.2** | Compute used --- RTX 5070~Ti local + Modal A10G, breakdown by category, total $\approx\$320$ API + 210 GPU-h + 200 CPU-h. |
| **D.3** | Random seeds and statistical methodology --- bootstrap protocol, SE convention. |
| **D.4** | Evaluation protocol --- 20 eval eps, deterministic policy, success criterion. |
| **E.1** | Per-seed final success rates table (3 seeds x 3 envs x 4 methods). |
| **E.2** | Cross-task transfer details --- judge per-episode rationales. |
| **F.1** | NeurIPS 2024 reproducibility checklist --- 4 categories (models/datasets, algorithmic, code/data, compute) answered. |
| **F.2** | Broader Impacts --- positive/negative/scope paragraphs. |
| **F.3** | Compute infrastructure --- exact software versions for reproduction. |
| **G.1** | Teleport-collapse failure mode --- formal characterization, mitigations 1-4 evaluated. |
| **G.2** | Action sign-flip failure mode --- rates per (source, model, variant), recommended sign-check gate (Eq.~\ref{eq:sign-gate}). |
| **H** | Reproducibility commands --- verbatim CLI invocations to reproduce headline ablation, prompt eval, cross-task, verified-CF smoke. |

## Build status

`bash build.sh` runs clean. No fatal LaTeX errors. Warnings present
but harmless:
- 75 underfull/overfull-hbox notices in verbatim and table blocks
  (cosmetic; common in NeurIPS submissions; <30 pt overfull is fine).
- 3 undefined citations (`wu2026largerewardmodels`, `patel2025iker`,
  `zha2025tango`) introduced by parallel main.tex edits, NOT by the
  appendix. These need to be added to `refs.bib` by whoever added them
  to main.tex.

## Anything that needs follow-up

1. **Add missing refs**: `wu2026largerewardmodels`, `patel2025iker`,
   `zha2025tango` are cited in main.tex (the post-revision intro
   contributions paragraphs) but absent from `refs.bib`. The main
   paper has 3 undefined citations as a result. Fix by adding the
   three BibTeX entries (see L2 bibliography for templates).
2. **Per-seed table E.1 numbers**: Currently shows pre-fix pipeline-bug
   values for the GPT-4o column (cf.\ Section~\ref{sec:discussion} in
   the main paper). The data-collection agent running the overnight
   verified-CF sweep should replace these with corrected numbers in the
   morning. The rest of the table (Uniform, PER, Sem-PER Oracle) is
   final.
3. **Ablation placeholder in E.1.2**: Section E.1 has a paragraph
   reserved for the planned IS-correction ablation (strict
   $w_{\text{IS,Sem}}$ vs.\ the under-corrected $w_{\text{IS},P}$);
   the data isn't in yet. If the overnight sweep covers it the
   morning agent should fill in the numbers; otherwise the paragraph
   reads as a clear future-work statement.
4. **Algorithm rendering**: I used `\fbox{\parbox{...}}` rather than
   the `algorithm2e` or `algorithmic` packages because adding them
   would require modifying `neurips_2024.sty`. The rendering looks
   clean in the PDF but is not formally a numbered "algorithm
   environment". If the paper team prefers true algorithm-style
   numbering, swap in `\usepackage[ruled]{algorithm2e}` at the top of
   `appendix.tex` (no main.tex change needed; appendix is `\input` not
   `\include`).
5. **Optional: glossary cross-references**: The notation table
   (B.2) cites "first-use section" but some entries point to
   Algorithm~\ref{alg:...} rather than a numbered section. Minor;
   only fix if the paper team wants strict consistency.

## Constraints observed

- No VLM calls made.
- No training runs launched.
- All math in LaTeX (mathbf, mathcal, mathbb, mathrm).
- All Unicode in verbatim blocks replaced with ASCII equivalents (dx,
  dy, dz, in, ~=) to avoid utf8/inputenc errors.
- 14 pages of new appendix content; total appendix is 15 pages
  (B-H) plus the pre-existing 1-page A.
- Modified files committed on branch `agent/pathc-lead`.

## File map

- Created: `agent_reports/paper/appendix.tex`
- Modified: `agent_reports/paper/main.tex` (one line: `\input{appendix}`)
- Built: `agent_reports/paper/main.pdf` (25 pages, 451 KB)
- Committed: 1de84cf on branch agent/pathc-lead
