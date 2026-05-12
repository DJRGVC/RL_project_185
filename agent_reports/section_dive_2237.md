# Section Dive 22:37 — Deep Improvement to §4.1 (Semantic PER)

**Target.** Section 4.1, "Semantic PER with the Failure-Direction Signal,"
was the most underdeveloped methodological core in the paper: ~22 lines
of body relative to ~140 lines of theory-section framing in Section 3.
The bidirectional ablation variant was hand-waved, Oracle v3 was a single
paragraph buried inside a longer sentence, the sum-tree re-blending
mechanism (a real engineering insight from `A2_oracle_v3_bidirectional.md`)
was a single parenthetical, and the section lacked any formal statement of
the kernel or of the conditions under which the IS-correction story from
Section 3 extends. Although the paper's most-recent commit touched every
section equally (single 22:26 commit), §4.1 was the section whose
body-density most badly lagged its conceptual importance, so I targeted
it for the deep pass.

**What changed.** I restructured §4.1 from one prose paragraph plus a
trailing "and-also" paragraph into seven labeled sub-units: a one-paragraph
overview, a `Pipeline` paragraph (with the exact keyframe-to-timestep
mapping $\lfloor\hat k\cdot(T-1)/(K-1)\rfloor$), a boxed `Definition`
of the semantic kernel with explicit boundary cases and defaults, an
`Exact re-blending` paragraph (codifying the sibling float64 array trick
from `A2_oracle_v3_bidirectional.md`), a `Why this proposal-shaping family?`
paragraph citing four new proposal-shaping precedents already in
`refs.bib` (ReaPER, RPE-PER, Prioritized Generative Replay,
Krutsylo non-uniform-replay), a boxed `Assumption` listing the three
conditions under which the IS-correction interpretation of Section 3
extends from PER to Semantic PER (trajectory-only conditioning, bounded
priorities, finite second moment) with the policy-freshness loophole cross-
referenced to `ma2026freshness`, a formalized `Bidirectional variant`
paragraph that writes out $p_i=(|\delta_i|+\varepsilon)^\alpha\cdot
w^{\text{fail}}_i\cdot w^{\text{succ}}_i$ and explains why the variant
serves as a controlled comparison to VLM-RB's success-direction signal,
and a `Heuristic-Oracle upper envelope` paragraph that specifies Oracle
v3's three precedence phases (ballistic / contact-loss / argmin) with
their numeric thresholds and cites `sayar2023cebp` and `urpi2024caiac`
as the privileged-state precedents. The paper grew from 26 to 28 pages,
`bash build.sh` passes cleanly, and `python scripts/visual_quality_gate.py`
returns `PASS`. All citations resolve in the final pdflatex pass with no
natbib warnings; the four new citations were already in `refs.bib`.
