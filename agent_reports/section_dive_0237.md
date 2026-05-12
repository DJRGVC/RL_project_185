# Section Dive — 0237 PDT — §5.3 Counterfactual Prompt Design

**Agent:** SECTION-DEEP-IMPROVER (Opus 4.7, 1M context).
**Budget:** 35 minutes. **Branch:** `agent/pathc-lead`. **Commit:** `7c4243a`.

## What was touched and why

Per the rotation logic, §5.3 (Counterfactual Prompt Design, lines 941–1002)
was the strongest remaining candidate: blame analysis showed only two
commits touched it (`1de84cfe` initial draft and `fd880a78` overflow polish
~4 hr ago), it sits well clear of the Oracle-CF-dependent KILL sections
(§4.1 / §5.2), and R2 had not landed by my fire time (only R1's addressed
file was present at `agent_reports/reviewer_feedback_001_00-19_addressed_0038.md`),
so I followed the default rotation rather than the R2-priority branch.

The pre-edit §5.3 was a one-paragraph "Key finding" containing the
"\emph{strictly dominates}" claim that R1 W12 had already flagged as
marketing tone (Opus's 0.97 goal-progress on \textsc{achieved\_goal} is
*higher* than GPT-4o's 0.83 on the same variant; the asserted "domination"
only survives after we discount Opus's number as a degenerate
goal-copy — a circular argument when stated without the mechanism). The
section also had no discussion of the dominant external-validity threats:
(i) same-vendor judge-candidate overlap (Opus is both the candidate model
and the judge), (ii) the underpowered sample size ($n\!=\!2$–$4$ on the
Opus rows), and (iii) the fact that the prompt-design experiment is a
*precondition* for the §3 IS-posterior framing rather than an independent
engineering ablation, since a position-copy-collapsed $q_\phi$ is by
construction $\tau$-independent and breaks the trajectory-conditional
structure of Eq.~\eqref{eq:headline}.

## What was added

Four new paragraphs (1f. paragraph headed by `\paragraph{...}`): (1)
*Mechanism of the position-copy attractor* — the $0/6$ vs $4/6$ GPT-4o
split between \textsc{achieved\_goal} and \textsc{all} as the
discriminating signature for a prompt-length-attentional-dilution
interpretation, with a falsifiable prediction (shortened action history
$\to$ monotonic teleport reduction). (2) *Judge-bias and inter-rater
reliability* — argues teleport-collapse is judge-independent (a Euclidean
predicate), the rubric constrains plausibility, and the §5.5 real-data
replication removes the same-vendor overlap; explicitly notes the
judge-bias direction is *adversarial* to our preferred conclusion, which
is the safer mis-specification. (3) *Statistical-power and
pre-registration framing* — Clopper–Pearson upper bounds give a $0/6$
consistent with true rate $\le 0.39$ and $4/4$ consistent with $\ge 0.40$,
so the $0/6$ vs $4/4$ contrast is the strongest single
binary-classification claim the table makes; the rest are within
standard-error noise. Pre-registers a 30-episode re-evaluation at $\le 5\%$
as the falsifier for camera-ready. (4) *Connection to the IS-posterior
framing* — the prompt-design experiment is a precondition for §3, not an
engineering ablation: degenerate position-copying produces a
$\tau$-independent $q_\phi$ that breaks Eq.~\eqref{eq:headline}'s
trajectory-conditional structure. Also softened "three-family robustness"
to "two-vendor" per R1 L2 and the "strictly dominates" line per R1 W12.

No new bib entries (two LLM-as-judge citations I initially drafted —
`zheng2023llmasjudge`, `wang2023largemodelsasjudges` — are absent from
`refs.bib` so I rewrote the prose citation-free; `rocamonde2024vlmreward`
was also removed where misapplied to a non-VLM attentional-bias claim).
Build clean (single `pdflatex` warning is the normal cross-reference
re-run hint resolved by build.sh's second pass), 33 → 34 pages, no
overfull/underfull boxes added.

Cron coordination: completed and committed at 02:37:35 PDT, ~25 s before
the 02:38 paper_iter cron window; `pgrep -af paper_iter` was empty at all
checkpoints.
