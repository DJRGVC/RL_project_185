# Spacing hints — append to the in-flight formatting agent's task

**Source:** user comparison of `cs285_final_paper.pdf` p1 vs `reference_neurips_2025.pdf` p1 at 130 DPI.

The in-flight agent `a7825ce58ab798ef7` already covers citation style + figure placement. Add these spacing tweaks if not already done.

## Spacing-specific tweaks to apply

In `paper_cs285/main.tex` preamble (BEFORE `\begin{document}`):

```latex
% Compact list spacing — matches NeurIPS 2025 reference papers
\usepackage{enumitem}
\setlist{itemsep=0pt,topsep=2pt,parsep=0pt,partopsep=0pt}

% Slightly tighter inter-paragraph spacing (NeurIPS body defaults work but the
% reference paper feels denser; this gets close without breaking layout)
\setlength{\parskip}{0.2ex plus 0.1ex minus 0.05ex}

% Reduce section-heading vertical breathing
% (Use sparingly — NeurIPS template controls this; don't override too aggressively)
\usepackage{titlesec}
\titlespacing*{\section}{0pt}{1.5ex plus 0.5ex minus 0.2ex}{0.8ex plus 0.2ex}
\titlespacing*{\subsection}{0pt}{1.2ex plus 0.4ex minus 0.2ex}{0.6ex plus 0.2ex}
\titlespacing*{\paragraph}{0pt}{0.8ex plus 0.2ex minus 0.1ex}{0.5em}
```

## Caveats

- The NeurIPS 2025 `neurips_2025.sty` already sets reasonable defaults. Don't override aggressively — could fail submission compliance checks if any exist.
- `titlespacing*` requires `\usepackage{titlesec}` (not always in NeurIPS template; add it).
- `\setlist{...}` requires `\usepackage{enumitem}`.
- Test compile + verify ≤13pp ceiling after each spacing change.

## What NOT to do

- Don't change `\baselineskip` or `\linespread` — affects reading comprehension and may violate NeurIPS template.
- Don't compress figure spacing manually — let LaTeX handle it.
- Don't squish the abstract or title block — those are template-controlled and graders expect normal spacing there.

## How to verify

After all edits, render p1, p4, p7 of new PDF side-by-side with reference paper. Should look noticeably tighter without feeling cramped.
