# Section dive 0135 -- Related Work (HER and PER paragraphs)

**Agent**: section-deep-improver (Opus 4.7, 1M context). 35-min budget. Branch `agent/pathc-lead`.

## Section selected and rationale

Picked **§2 Related Work** -- specifically the two least-recently-touched paragraphs
in the paper: §2.1 "HER and goal-conditioned RL" and §2.2 "Prioritized replay and
off-policy correction". Both paragraphs were last meaningfully touched in commit
`1de84cf` (the appendix-add, before the iter loop started), so they are by a wide
margin the least-recently-revised pieces of the paper. The §2.3-2.5 paragraphs
(Foundation Models, Generator-Verifier, VLM-RB differentiation) were all revised
in the last ~4 hours and were skipped per the prompt. §1 motivation is also old
but the contribution bullets were already revised; §3 theory body's "why
multiplicative" / uniqueness was touched at 00:38. §5.3 (Counterfactual Prompt
Design) body was effectively untouched since the appendix-add, but it depends on
the prompt-design data discussion that the iter loop will likely revisit; §6
limitations vii/viii were just added at 01:13. So Related Work HER+PER paragraphs
were the cleanest "least-recently-touched, no Oracle-CF/Phase-1 dependency"
target.

## What was changed

The HER paragraph was expanded from 12 lines to ~35 lines and now organizes the
2024-2026 HER-family literature along three orthogonal extension axes -- relabel
target, relabel proposal, and relabel verification -- placing our work explicitly
in the third (verification-stage) family. Added single-sentence distinctions for
each previously-listed method (Next-Future, CEBP, GCHR, HInt/NCII) and pulled in
two methods flagged by `DEEP_LIT_REPORT.md` but missing from §2: CAIAC (Urpí 2024,
counterfactual data augmentation on Fetch) and AgentHER (Ding 2026, multi-judge
VLM verification for LM-agent hindsight). Crucially, this directly addresses R1
W7's "differentiation is overstated/thin" critique by explicitly distinguishing
our verifier (exact training simulator, zero modeling error) from HInt/NCII's
(learned dynamics model) and from AgentHER's (multi-judge VLM committee).

The PER paragraph was expanded from 10 lines to ~40 lines and grounds the
IS-correction structure as the load-bearing property of PER (anticipating R1
W4/W5's theory critique) before listing the modern PER + auxiliary-signal family
(ReaPER, RPE-PER, Prioritized Generative Replay, Krutsylo non-uniform memory).
The new framing makes the multiplicative-vs-additive distinction with VLM-RB
look like the family's outlier choice rather than a hand-picked contrast, and
introduces the three-axis positioning of Semantic PER (exogenous /
trajectory-level / multiplicative) that §4.1 then expands. All new citations
already exist in `refs.bib`; no `refs.bib` edit. Compiles cleanly (no
Overfull/error lines; PDF stays at 32 pages; visual gate passes).

-- section-deep-improver, 2026-05-12
