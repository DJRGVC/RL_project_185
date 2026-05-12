# Section dive 0336 — §3 main body (W5/W6/W9 honesty pass)

**Target.** §3 Theoretical Motivation main body — the "VLM as a posterior"
paragraph and the closing "Connection to causal credit assignment" paragraph,
plus the §1 contributions bullet (2) and §2 mirror paragraph. These three
loci were the last untouched body of §3 (recent iters hit the assumption
box, the taxonomy rename, the bias-bound equation, and Table 1's caption,
but not the running text between Eq. 6 and Table 1, nor the closing CaLM-positioning
paragraph). The pick targets three of R2's open weaknesses directly: **W5**
(the "exogenous FM credit oracle" new-category claim is rebranding because
CaLM precedes us); **W6** (the "needs no λ-warm-up" line in §1 ignores that
PER's β anneal is itself a warm-up); and **W9** (Eq. 6 is written as an
expectation but the implementation argmaxes the VLM's chain-of-thought
output, which is a Dirac). The diff is +65/-26 in main.tex spanning four
edits: §1 line ~94 (drop "exogenous … oracle" as a stand-alone claim, place
as "vision-modality instantiation of Pignatelli 2024's program"), §1 line
~106 (rewrite "needs no λ-warm-up" → "adds no VLM-specific schedule on top
of PER's standard β anneal (in contrast to VLM-RB's λ_t: 0→0.5 mixture
warm-up)"), §3 lines 408–456 (insert a "Soft versus hard elicitation of
q_φ" sub-paragraph that explicitly nests the hard-argmax implementation as
a Dirac special case of Eq. 6, references the bias bound in
Appendix~B.1 for the Dirac-collapse consequence, and pre-registers the soft
ablation), and §3 lines 510–532 + §2 mirror (rewrite both occurrences of
the "introduces a new category" claim as "first vision-modality,
prioritized-replay instantiation of CaLM's exogenous-FM-credit-oracle
program", explicitly crediting Pignatelli 2024 with establishing the program
and listing the two methodological additions — multiplicative-with-PER IS
structure and simulator-verified CF gate — that distinguish us from a pure
CaLM port).

**Verification and commit logistics.** Build passes on first try (35 pages,
no overfull/undefined-ref warnings; pre-existing underfull \vbox badness on
pages 2/9/16/25 is whitespace-budget noise and was present before this
iter). Rendered §3 spot-check confirms the "Soft versus hard elicitation"
paragraph reads cleanly and the new closing paragraph credits CaLM by name
in three places (intro line ~94, §2 line ~298, §3 line ~510). The fix is
deliberately phrased to leave R2's remaining open items (W1/W2/W4/W7/W8 +
the Q1 bias-bound itself, which lives in the appendix) intact for the next
iter to target; this dive is scoped to the §3 main-body W5/W6/W9 trio that
the recent iter's "R2 fixes" commit explicitly left to the next round.
Avoided: §4.1 / §5.2 (Oracle-CF rewrite watch — corrected Push data in,
morning re-frame will own those), and §3's appendix subsections B.1/B.2
(already touched). No paper_iter cron conflict — committed at 03:36, well
before the :38 boundary; pgrep clean at start of run. Committing to
`agent/pathc-lead` with the standard section-dive commit-message header.
