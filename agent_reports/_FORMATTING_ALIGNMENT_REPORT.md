# Formatting Alignment to NeurIPS 2025 Reference (CS 285)

**Date:** 2026-05-13, Opus 4.7
**Reference:** Xu et al., "Compliant Residual DAgger", NeurIPS 2025
(`agent_reports/reference_neurips_2025.pdf`)
**Target:** `agent_reports/paper_cs285/main.pdf`

## Summary of changes

1. **Citation style: author-year -> numeric.**
   - Before: `\PassOptionsToPackage{numbers, compress}{natbib}` had no effect because
     the `&` in `sort&compress` was missing and `square` wasn't requested. Render showed
     `(Andrychowicz et al., 2017)`-style.
   - After: `\PassOptionsToPackage{numbers,sort&compress,square}{natbib}` --
     citations render as `[1]`, `[14, 20, 29]`, exactly matching the reference paper's
     bracketed numeric style.
   - `\bibliographystyle{plainnat}` retained -- it produces a bbl compatible with
     both modes; natbib's `numbers` option does the numeric rendering at cite time.

2. **Figure / table placement: `[t]` -> `[!t]`.**
   - `main.tex` fig:main, tab:prompt-variants
   - `appendix.tex` fig:envs, tab:hparams
   - Matches the reference's strict top-of-page convention.

## Final state

- **Page count:** 12 pp (under the 13 pp CS 285 ceiling, same as before).
- **Citation style:** numeric, sort-compress, square brackets (e.g. `[14, 20, 29]`).
- **Bibliography list:** numbered `[1]` ... `[29]` on pp. 7-9.
- **Title block:** large bold centered title, centered author names, footer affiliation -- matches reference style.
- **Section headings:** numbered 1-6 plus unnumbered Contributions and References --
  matches reference's bold numbered style (default NeurIPS 2025).
- **Paragraph lead-ins:** 15 `\paragraph{Term.}` style headings already present,
  including one rhetorical-question lead ("Why multiplicative?") echoing the
  reference's punchy style. No additional question-form leads were added --
  the brief flagged this as optional and warned against forcing.

## What was preserved (CS 285 rubric)

- "Extended Abstract" heading retained (rubric-required, not standard NeurIPS
  "Abstract"; visually the heading is the only difference from the reference
  abstract block).
- All 7 rubric sections present.
- All Pass 1-3 / Winston / GPTZero / meta-cleanup content preserved verbatim.
- Contributions list with per-author breakdown retained.

## Tradeoffs

- The numeric-citation change shrinks the paper by ~0 lines but does compress the
  bibliography slightly (multi-cite groups now render as `[14, 20, 29]` instead of
  three full author-year strings). Net: same 12 pp.
- The reference's "Stanford University" affiliation footer is single-line; ours is
  two-line ("Department of EECS / UC Berkeley"). Left as-is for transparency on
  affiliation.

## Visual comparison (side by side)

| Page | Reference (NeurIPS 2025) | Ours (paper_cs285/main.pdf) |
|------|--------------------------|-----------------------------|
| 1 | "Abstract" centered, numeric cites `[20, 21, 22]` | "Extended Abstract" left-aligned (rubric), numeric cites `[3]`, `[22]` |
| 2 | Bold rhetorical-question paragraph leads, numeric cites | "Honest negative." + "Introduction" + numeric cites `[14, 20, 29]` etc. |
| 4 | Numbered section headings, figures `[!t]` | Numbered section headings, figures `[!t]` |
| 7 | Bibliography numbered `[1]` ... | Bibliography numbered `[1]` ... `[29]` |

## Files modified

- `agent_reports/paper_cs285/main.tex` (preamble, fig/table placement)
- `agent_reports/paper_cs285/appendix.tex` (fig/table placement)

No content edits. No edits to `paper/` (NeurIPS variant left untouched).
