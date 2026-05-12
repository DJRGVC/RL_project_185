# Section Dive 2335 — §4.2 Counterfactual Prompting and Teleport-Collapse

**Target chosen.** §4.2 ("Counterfactual Prompting and the Teleport-Collapse
Failure Mode"). Skipped per the start-of-shift logic: §4.1 (22:29), §4.3
(22:30 DEEP-LIT-WRITER add but partial), §5.1/§5.3 (23:13), §5.6/abstract/
conclusion (22:38), and §3 ("why multiplicative" subsection 22:30). §4.2 had
not been touched since the original section was first drafted and was the
weakest-developed of the method-section subsections: 17 lines, no definition
box, no mechanistic account of *why* teleport-collapse occurs, and no
explicit connection to either the IS-posterior framing (§3) or the
generator–verifier framing that DEEP-LIT-WRITER added to §4.3. Given §4.2 is
the bedrock empirical observation justifying §4.3's existence, it deserved
substantive treatment, not just a stub.

**Improvement delivered.** The subsection is rewritten end-to-end (17 → ~85
lines) with five substantive additions, not a copy-edit. (1) A formal
**Definition (Teleport-collapse) box** as `\fbox{}` (Figure
\ref{fig:teleport-def}) that gives the literal predicate
$\|\hat{p}-g\|_2\!\le\!d_{\text{th}}$, an IS-posterior interpretation
($q_\phi=\delta(\hat{p}-g)$, connecting back to §3), an HER-invariant
violation argument, and a detectability note that explicitly motivates the
post-hoc rejection gate cited in §5.5 as defense-in-depth. (2) A
**2$\times$2 output-type design space** (output kind × goal-conditioning)
that organizes the four prompt variants as principled cells rather than an
unmotivated list, with each cell cited to its lineage paper (AHA for
narrative \citep{duan2025aha}, HER for achieved\_goal \citep{andrychowicz2017her}).
(3) A **mechanistic account** of *why* teleport-collapse occurs (in-context
goal triplet → position-copy bias; non-position variants are immune by
schema, not by model), explaining the prompt-architectural verdict
empirically rather than asserting it. (4) An **explicit bridge** to
§4.3's generator–verifier framing showing that the \textsc{action} output
type simultaneously (i) removes the numerical attractor and (ii) is what
the symbolic verifier can consume—so the two design choices co-design
rather than each standing alone. (5) A tightened **production
configuration** paragraph that distinguishes the position-emitting analysis
(adopts achieved\_goal+gate) from the verified-CF mechanism itself (uses
action). Compile: 0 overfull boxes, 29 pages, visual-quality-gate PASS.
No new figures, citations all from existing refs.bib (`duan2025aha`,
`andrychowicz2017her`, `zha2025tango`—all already in bibliography),
no overlap with concurrent paper-iter sections.
