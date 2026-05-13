# Section Dive 1735 — §2.1 HER closing connector: IS-pairing perspective

**Target.** `agent_reports/paper/main.tex` §2.1 "HER and goal-conditioned RL"
paragraph, specifically a new closing bridge added between the
relabel-verification-extensions sentence and the `\paragraph{Prioritized
replay and off-policy correction.}` break. Picked Option A from the
START-IMMEDIATELY logic over Option B (§3 setup) because the §2.1 HER
paragraph had no engagement at all with the IS-pairing principle that was
introduced into §2.2 at 21:38 (commit `0a3c139`), whereas §3 already
exercises that principle organically in its "Why multiplicative?
IS-correction analysis" paragraph at lines 489--525. Adding a fresh framing
slug to §3 risked stepping on the 21:38 PER iter's narrative; adding the
HER-side connector instead deepens the §2.1 $\to$ §2.2 $\to$ §3 arc into a
four-step structural sequence (HER preserves IS pairing trivially; PER
family preserves it multiplicatively; VLM-RB breaks it; Semantic PER
restores it). No conflict with paper_iter (no compile in flight per file
timestamps; 21:13/21:38 slots are not currently running). Picked over
Options C/D because §5.4 cross-task is data-dependent (HER@1M PnP runs
~50% done; numbers would change overnight) and B.2 V-trace was touched at
13:35 with the two-regime degeneracy split.

**Substantive changes.** One new ~13-line paragraph appended to the §2.1
HER paragraph (just before the `\paragraph{Prioritized replay\ldots}`
break). The paragraph (1) names that vanilla HER and all three HER
extension families (relabel-target, relabel-proposal, relabel-verification)
leave the replay-sampling distribution unchanged, so the IS pairing question
arises only trivially under HER with $w_\text{IS}=1$ and proposal $\mu_U$;
(2) frames HER's degree of freedom as the *buffer contents* with the sampler
fixed, contrasted with PER and VLM-RB whose degree of freedom is the
*sampler* with the contents fixed; (3) positions our Semantic PER as
exercising *both* degrees of freedom (verified-CF modifies contents;
multiplicative $w_\text{sem}$ modifies sampler with IS pairing kept
tractable); (4) names VLM-RB explicitly as the foil that modifies the
sampler but not the contents and whose pairing is not IS-corrected. No
new equations, no new citations (uses §3 and §4.1 cross-refs which already
exist), no figure changes. Forward-references `\S\ref{sec:method:sper}`
(§4.1) and `\S\ref{sec:theory}` (§3); both resolve cleanly under
`pdftotext -layout` extraction. Visual gate: page count went 44 $\to$ 45,
new paragraph renders correctly with all symbols (`µ_U`, `w_IS`,
`w_sem`) and the §4.1 / §3 cross-refs render as expected. Only build
warning is the pre-existing `tab:vlm_comparison` undef on p.~20
(unchanged). Commit on `agent/pathc-lead`. File size 1,018,494 bytes
(vs. 1,016,273 at 16:35 = +2.2 KB, consistent with one extra paragraph
of body text).
