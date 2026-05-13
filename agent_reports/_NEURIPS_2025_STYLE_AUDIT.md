# NeurIPS 2025 Style Audit

Date: 2026-05-13
Auditor: Opus 4.7 agent
Scope: `agent_reports/paper_cs285/` (CS 285 final-project paper variant)

## Source

User-uploaded `agent_reports/styles.zip` (188 273 bytes), extracted to
`agent_reports/neurips_2025_ref/`.

### ZIP contents

```
Styles/neurips_2025.sty   13 023 B  (last revision: April 2025)
Styles/neurips_2025.tex   44 551 B  (example/instructions)
Styles/neurips_2025.pdf  171 133 B  (compiled instructions PDF)
```

The official `\ProvidesPackage` line confirms the file:
`neurips_2025 [2025/05/01 NeurIPS 2025 submission/camera-ready style file]`.

## Diff vs. our existing `neurips_2024.sty`

Total diff: 92 lines. Substantive changes (all isolated to the `.sty`; no
caller-side breakage):

| Change | 2024 | 2025 |
|---|---|---|
| Year / ordinal / location | 38th, 2024, Vancouver | 39th, 2025, San Diego |
| Footer track selection | hard-coded `(NeurIPS 2024).` | new `\@trackname` macro driven by track option |
| Track package options | none | `main` (default), `position`, `dandb`, `creativeai`, `sglblindworkshop`, `dblblindworkshop` |
| Anonymity switch | `\if@submission` | renamed to `\if@anonymous` (functionally equivalent) |
| Preprint footer string | `Preprint. Under review.` | `Preprint.` |
| `\workshoptitle{}` macro | absent | added (used only by workshop tracks) |
| `\PackageWarning` text | `neurips_2024` | `neurips_2025` |
| Geometry, fonts, headings, abstract, section spacing, bibliography style | unchanged | unchanged |

No breaking changes affect the `preprint` mode we use. The `[preprint]` option
is still accepted and behaves identically (skips the conference-notice block
in favour of the simpler footer).

## Compatibility verdict

Fully compatible. Our `main.tex` requires a one-line change:

```diff
- \usepackage[preprint]{neurips_2024}
+ \usepackage[preprint]{neurips_2025}
```

No commands, package options, environments, or geometry settings used by our
paper changed semantics between the two templates.

## Decision: switched to 2025 template

### Pre-switch baseline (neurips_2024.sty)
- Pages: **11**
- Build warnings: 25 (all benign existing `Underfull \hbox / \vbox`)
- Errors: 0

### Post-switch result (neurips_2025.sty)
- Pages: **11** (unchanged)
- Build warnings: 24 (one fewer; no new warning categories)
- Errors: 0
- Footer text in compiled PDF correctly displays `Preprint.` (the 2025 simplified string)
- All Pass 1-3 content (data, citations, contributions, polish) preserved verbatim

### Files changed
- `agent_reports/paper_cs285/main.tex` — single `\usepackage` line update
- `agent_reports/paper_cs285/neurips_2025.sty` — **added** (copied from `agent_reports/neurips_2025_ref/Styles/`)
- `agent_reports/paper_cs285/neurips_2024.sty` — **removed** (no longer referenced)

### Files untouched
- `agent_reports/paper_cs285/appendix.tex`
- `agent_reports/paper_cs285/refs.bib`
- `agent_reports/paper_cs285/build.sh`
- All figures and tables
- Sibling `agent_reports/paper/` (NeurIPS variant — not in scope; still on 2024 template)

## Rollback procedure (if ever needed)

```bash
cd agent_reports/paper_cs285/
git checkout HEAD~1 -- neurips_2024.sty main.tex
rm neurips_2025.sty
bash build.sh
```

## Notes for Daniel

- CS 285 final-project outline says only "you are welcome to use the NeurIPS
  template" — no year is mandated, so either would have been acceptable. The
  2025 template is now the more current choice and produces an identical
  11-page layout with one fewer underfull warning.
- The sibling `agent_reports/paper/` build (the standalone NeurIPS variant)
  still uses `neurips_2024.sty`. Migrating it is a trivial copy-and-edit if
  desired, but is **out of scope** for this audit (task constraint:
  CS 285 variant only).
- The 2025 template adds track-specific footer strings (Position / D&B /
  Creative AI / Workshop). For preprint mode these are inert — they only fire
  in `final` mode. No action needed unless the paper is later submitted to a
  specific NeurIPS track.
