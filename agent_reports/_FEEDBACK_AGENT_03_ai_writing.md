# Agent 03 — AI-Writing Detector

Reviewed: `agent_reports/paper_cs285/main.tex` (557 lines), read-only.

## AI-voice score by section

- Abstract (lines 34-91): **4/10** — mostly direct and number-dense; some boilerplate verbs ("we argue", "we recast", "we close")
- §1 Introduction (lines 93-156): **5/10** — leans on the "four contributions" structure, "framing yields" / "this framing yields" boilerplate
- §2 Related Work (lines 157-206): **3/10** — terse, citation-dense, specific differentiation; mostly human-voice
- §3 Method (lines 208-316): **5/10** — strong technical writing, but "by construction" appears 3x, "instantiates the generator–verifier paradigm" repeats verbatim
- §5 Experiments (lines 318-460): **3/10** — number-dense, declarative, varied sentence rhythm; few AI tells
- §6 Discussion (lines 462-526): **6/10** — the conclusion paragraph is the most AI-flavored block in the paper; setup-payoff cadence
- §7 Contributions (lines 528-547): **2/10** — direct, factual, clearly human authorial voice
- **Overall: 4/10** — paper reads mostly as a competent researcher who edits with formal phrasing; the AI tells are concentrated in a small number of repeated boilerplate phrases (especially "by construction", "the framing yields", "instantiates the … paradigm"), the conclusion paragraph, and the four-contributions list cadence in §1.

Caveat: the paper is heavy on numbers and named entities, which is the strongest signal of human-authored research writing. AI-flavored phrasing is real but localized.

## Top-15 most AI-flavored passages

### Passage 1 (lines 511-526, §6 Conclusion)
- Quote: *"We re-frame VLM-guided experience replay as importance-sampled posterior reweighting, showing that the multiplicative form is the principled choice because it admits a clean IS-correction analysis, whereas the additive VLM-RB mixture implicitly retargets the loss. We introduce VLM-Verified Counterfactual Hindsight, which closes the dominant failure mode of language-only counterfactuals \emph{by construction}: …"*
- Tell: textbook AI conclusion cadence (we re-frame X / we introduce Y / we show Z); reuses "by construction" (3rd occurrence); "principled choice" is a vague intensifier; "the IS-posterior framing and the simulator-as-verifier guarantee stand independently of any single training outcome" is the kind of generic flourish AI tends to add at the end.
- Suggested rewrite: *"The multiplicative form of semantic PER admits a clean IS correction; the additive VLM-RB mixture does not. VLM-Verified Counterfactual Hindsight forces the VLM to emit an action sequence and accepts only sparse-reward-positive rollouts, so teleport-collapse cannot enter the buffer. At 500k steps verified-CF reaches 0.606 across three Fetch envs (0.85/0.35/0.617 on Push/PaP/Slide), ties VLM-CF in aggregate, and beats it on Slide (0.617 vs 0.55). The pre-registered Oracle-CF kill (PaP $\Delta=-0.05$ at 250k) bounds credit-assignment headroom on Fetch at this horizon; we honored it and report the result."*

### Passage 2 (lines 119-128, §1)
- Quote: *"This framing yields four contributions: \textbf{(1) An IS-posterior framing of VLM-guided replay} … We choose the multiplicative form because it admits a clean IS-correction analysis (the standard PER weight remains trajectory-conditionally well-defined); the additive mixture used by VLM-RB \citep{sharony2026vlmrb} implicitly retargets the loss to a $\lambda$-weighted objective."*
- Tell: "this framing yields N contributions" is canonical AI-paper scaffolding; "clean IS-correction analysis" is hedged-superlative-adjacent ("clean" used twice in paper).
- Suggested rewrite: *"This paper's contributions are four: (1) IS-posterior framing of VLM-guided replay (§3). The multiplicative form $\mu_P \cdot w_\text{sem}$ leaves PER's IS correction trajectory-conditionally well-defined; the additive VLM-RB mixture retargets the loss to a $\lambda$-weighted objective it does not correct for."*

### Passage 3 (lines 130-139, §1)
- Quote: *"A direct prompt for an alternative \emph{achieved goal} elicits a teleport-collapse failure mode in 100\% of Claude Opus 4.7 calls on FetchPush … We close this loophole \emph{by construction} by asking instead for a corrective \emph{action sequence} and executing it in a fork of the training simulator. A four-vector action cannot teleport a 50\,g block by 50\,cm under MuJoCo dynamics; the failure mode is structurally inexpressible. The mechanism instantiates the \emph{generator--verifier} paradigm \citep{zha2025tango} in robot RL."*
- Tell: "We close this loophole by construction" — 1st of 3 occurrences of "by construction"; "instantiates the … paradigm" repeats almost verbatim at line 313; "structurally inexpressible" is grandiose phrasing for "can't happen".
- Suggested rewrite: *"Direct prompts for an alternative achieved goal elicit teleport-collapse on 100\% of Opus 4.7 FetchPush calls. We ask instead for a 4-vector action sequence and execute it in a simulator fork; teleporting a 50 g block 50 cm with a 4-D end-effector action is physically impossible, so the failure mode cannot reach the buffer. This is a generator–verifier protocol with a simulator verifier."*

### Passage 4 (lines 282-296, §3.3)
- Quote: *"We close the teleport loophole by construction: ask the VLM for a corrective 4-vector action sequence rather than a hindsight goal, then verify execution in a simulator fork. … A four-vector action cannot teleport a 50\,g block by 50\,cm; the failure mode is structurally inexpressible."*
- Tell: 2nd "by construction"; sentence "the failure mode is structurally inexpressible" is recycled verbatim from §1. Repetition of phrasing across sections is a strong AI tell.
- Suggested rewrite: *"To close the teleport loophole, we ask for a 4-vector action sequence and verify execution in a simulator fork. Per episode: (1) snapshot MuJoCo state at the localized failure timestep K; (2) fork an env, write the snapshot, call \texttt{mj\_forward}; (3) roll out the VLM's action sequence for N=50 steps under the unmodified sparse reward; (4) accept iff $r_t \ge 0$ fires; (5) otherwise fall back to HER."* (just delete the closing "structurally inexpressible" sentence — it's a flourish, not information).

### Passage 5 (lines 306-316, §3.3 "Asymmetric failure modes" paragraph)
- Quote: *"The two contributions stack consistently but degrade asymmetrically: Semantic PER uses $q_\phi$ as a re-weighting prior and tolerates miscalibration as bounded variance amplification---calibration is a \emph{quality} dial. The verifier uses $q_\phi$ as a candidate-proposal prior and converts miscalibration into rejection-rate overhead rather than biased buffer writes---calibration is a \emph{throughput} dial."*
- Tell: too-perfect parallelism (quality dial / throughput dial) — the kind of rhetorical bow that AI loves; em-dashes connecting clauses in both halves. The information is good, the rhythm is the issue.
- Suggested rewrite: *"The two channels degrade differently. Semantic PER treats $q_\phi$ as a reweighting prior, so VLM miscalibration shows up as sampling-variance amplification (bounded; see §3.1). The verifier treats $q_\phi$ as a candidate proposal, so miscalibration shows up as rejection-rate overhead, not as biased buffer writes."* (break the parallelism; cut "quality dial / throughput dial".)

### Passage 6 (line 138 + lines 313-316, repeated phrase)
- Quote: *"The mechanism instantiates the \emph{generator--verifier} paradigm \citep{zha2025tango} in robot RL."* (line 138) and *"The protocol instantiates the generator--verifier paradigm \citep{zha2025tango} with a symbolic (simulator) verifier whose decisions are correct by construction…"* (line 313)
- Tell: same verb ("instantiates the … paradigm") with the same citation, two sections apart — a hallmark AI repetition pattern. Also "correct by construction" — 3rd "by construction".
- Suggested rewrite: keep one instance only (the §3.3 version is the more informative one). In §1 say *"This is a simulator-verified generator/verifier protocol (cf.\ \citealp{zha2025tango})."* and drop the duplicate.

### Passage 7 (lines 269-280, §3.2 teleport-collapse intro)
- Quote: *"the lowest-perplexity continuation when asked for a same-coordinate position is to copy it---a position-copy bias requiring no keyframe reasoning. We call this \textbf{teleport-collapse}: for a failed episode with $\|\text{ag}_T-g\|_2\gg d_{\text{th}}\!=\!0.05$\,m, the VLM emits $\hat{p}$ with $\|\hat{p}-g\|_2\le d_{\text{th}}$…"*
- Tell: "the lowest-perplexity continuation" is jargon-flavored hand-wave (lacks measurement); reads as AI explaining LM behavior in a vaguely authoritative tone.
- Suggested rewrite: *"When the prompt exposes \texttt{desired\_goal} as a literal triplet and asks for a corrective position in the same frame, the cheapest output is to copy it. We call this teleport-collapse: a failed episode with $\|\text{ag}_T - g\| \gg 0.05$ m gets a $\hat p$ within 5 cm of $g$, a Dirac $q_\phi(\hat p \mid \tau) = \delta(\hat p - g)$ that breaks HER's invariant."*

### Passage 8 (lines 239-258, §3.1 "Why multiplicative?")
- Quote: *"\textbf{(P1) IS-correction compatibility.} … \textbf{(P2) Replay-shaping vs.\ reward-shaping.} … The framing yields a falsifiable prediction: \emph{Semantic PER tracks standard PER when the VLM is poorly calibrated and pulls ahead when it is reliable; neither curve should diverge.}"*
- Tell: "The framing yields a falsifiable prediction" — generic AI scaffolding; also the (P1)/(P2) lockstep labelled-claim structure is fine in moderation but combined with the bolded sub-headers and the bow-tie ending it reads as ChatGPT-arguing-a-design-choice.
- Suggested rewrite: drop "The framing yields a falsifiable prediction:" entirely and just say *"Prediction: Semantic PER tracks PER under poorly-calibrated $q_\phi$ and pulls ahead when $q_\phi$ is reliable; the curves should not diverge."*

### Passage 9 (lines 372-382, §5.1 "Interpretation")
- Quote: *"\textbf{Interpretation.} Aggregating across the three envs, verified-CF reaches mean $0.606$ and vlm\_cf reaches $0.622$ ($\Delta\!=\!-0.016$); the two methods are essentially tied. Verified-CF \emph{exceeds} vlm\_cf on Slide, the task on which physics-consistent relabels are most valuable; vlm\_cf wins marginally on Push (near-saturated at this horizon). … \textbf{Why does verified-CF pay off on Slide?}"*
- Tell: "essentially tied", "the task on which … are most valuable" (post-hoc just-so explanation in a tone AI loves); the rhetorical "Why does verified-CF pay off on Slide?" self-Q&A is a classic AI tic.
- Suggested rewrite: *"Aggregate over the three envs: verified-CF mean 0.606, vlm\_cf 0.622 ($\Delta=-0.016$) — a tie within seed noise. Verified-CF beats vlm\_cf on Slide (0.617 vs 0.55) and loses on Push (0.85 vs 0.95, both near the horizon's ceiling). The Slide gap is consistent with HER's achieved-future relabel carrying little signal on free-flight pucks: the gripper-to-object distance is non-monotone, so a physics-consistent CF strike adds the positive TD target HER cannot."* (drop the rhetorical question.)

### Passage 10 (lines 50-63, Abstract "Methodological contributions")
- Quote: *"\textbf{(1) Semantic PER as importance-sampled posterior reweighting:} we recast VLM-guided replay as a trajectory-conditional posterior … \textbf{(2) VLM-Verified Counterfactual Hindsight:} we close the dominant failure mode of language-only counterfactuals (100\% teleport-collapse of Opus~4.7 on FetchPush) by asking the VLM for a \emph{corrective action sequence} rather than a hindsight goal, executing it in a simulator fork, and admitting only physics-consistent, reward-positive relabels into the buffer (confidence~1.0, zero modeling error)."*
- Tell: "we recast", "we close the dominant failure mode" — both have the AI flavor; "list of three" inside the (2) clause ("asking…, executing…, and admitting…"). The construction is competent, but the three-gerund tricolon is a tell.
- Suggested rewrite: *"(1) Semantic PER as posterior reweighting. We treat VLM-guided replay as a trajectory-conditional posterior $q_\phi(t^\star \mid \tau)$ over the failure-causing timestep and multiply the TD-error priority by $q_\phi$. The IS correction stays well-defined; VLM miscalibration becomes sampling-variance inflation, not Bellman-target corruption. (2) VLM-Verified Counterfactual Hindsight. We replace the language-only achieved-goal prompt (100\% teleport-collapse for Opus 4.7 on FetchPush) with a corrective action sequence executed in a forked MuJoCo env; only sparse-reward-positive rollouts enter the buffer."*

### Passage 11 (lines 96-102, §1 opening)
- Quote: *"The core difficulty of sparse-reward manipulation is temporal credit assignment: with only one reward bit at the end of a 50-step episode, every standard TD-error signal decays exponentially back from the terminal timestep, leaving the bulk of each trajectory effectively invisible to the optimizer."*
- Tell: "The core difficulty of X is Y" + "leaving the bulk … effectively invisible to the optimizer" — competent academic English but has a slight AI sheen ("effectively invisible" is a vague intensifier with "effectively" as the hedge). Not strongly AI but the chosen sentence rhythm (long subordinate-clause sentence opening a paper) is the default ChatGPT cadence.
- Suggested rewrite: *"Sparse-reward manipulation is a temporal credit-assignment problem. With one reward bit at the end of a 50-step episode, TD error decays geometrically from the terminal timestep and most of each trajectory contributes no signal."* (shorter, no hedge.)

### Passage 12 (lines 192-196, §2 Differentiation)
- Quote: *"To our knowledge this paper is the first to use a VLM-localized failure timestep as a credit-assignment signal and to verify counterfactual relabels in the same simulator on which the policy trains."*
- Tell: "To our knowledge this paper is the first to …" is one of the most common AI / paper-template phrases; combined with the "and" coordinating two claims this reads templated.
- Suggested rewrite: *"We are not aware of prior work that (a) uses a VLM-localized failure timestep as the credit-assignment signal or (b) verifies counterfactual relabels in the training simulator itself."*

### Passage 13 (lines 465-485, §6 "Cold-start verifier-rejection regime")
- Quote: *"\textbf{Why does the regime end?} As the policy improves and snapshots fall closer to the goal, $m_{\text{ver}}(\sigma)$ rises, the verifier admits relabels, and the small set of accepted CFs provides a low-variance, physics-consistent training signal."*
- Tell: 2nd rhetorical self-question ("Why does the regime end?") in the paper — paired with the "Why does verified-CF pay off on Slide?" question at line 380, this becomes a repeated AI tic.
- Suggested rewrite: drop the bolded question. Lead the sentence with the answer: *"The regime ends once the policy carries the gripper near the object on average: snapshots fall closer to the goal, $m_\text{ver}(\sigma)$ rises, and the small set of accepted CFs supplies a low-variance, physics-consistent training signal."*

### Passage 14 (lines 176-191, §2 "Differentiation from VLM-RB")
- Quote: *"The two systems differ along two methodological axes worth emphasizing. \textbf{First,} VLM-RB asks … we ask … \textbf{Second,} we ship a verified-counterfactual-hindsight mechanism …"*
- Tell: "two methodological axes worth emphasizing" is filler ("worth emphasizing" hedges with no information); the First/Second + bolded scaffolding is fine but combined with the "worth emphasizing" softener it feels AI-padded.
- Suggested rewrite: *"VLM-RB and Semantic PER differ on two axes. (1) Question. VLM-RB scores 32-frame sub-trajectory clips ("is this clip good?") and mixes the score additively with uniform sampling $\mu = \lambda \mu_\text{VLM} + (1-\lambda)\mu_U$; we ask which timestep was outcome-causing and combine multiplicatively with TD error, preserving PER's IS-correction interpretation (§3). (2) Counterfactual channel. We add a verified-CF mechanism (§3.3) outside the scope of any success-scoring scheme: VLM-RB's signal cannot drive relabels."*

### Passage 15 (lines 83-90, Abstract "Honest negative and roadmap")
- Quote: *"The verified-CF channel exhibits a cold-start regime (FetchPickAndPlace seed~42: 100\% verifier-rejection over the first $\sim\!80$ VLM calls) in which it reduces to a strictly costlier HER; the two failure modes are asymmetric (Semantic-PER variance inflation is bounded; verified-CF write-throughput collapse is not)."*
- Tell: "exhibits a … regime" — nominalization-flavored ("exhibits" + abstract noun); the parenthetical asymmetric-failure-modes summary again uses the "X is bounded; Y is not" tricolon-of-two parallelism. Content is great; rhythm is AI.
- Suggested rewrite: *"Verified-CF has a cold-start failure mode: on FetchPickAndPlace seed 42 the first ~80 VLM calls were 100\% rejected, so the agent ran as a costlier HER. Semantic PER degrades gracefully under miscalibrated $q_\phi$ (bounded variance inflation); verified-CF does not (write-throughput collapse is unbounded in the cold-start limit)."*

## Patterns to fix globally

- **"by construction"**: appears 3 times (lines 134, 285, 314) and once with "correct by construction". Pick one place to use it (probably §3.3) and rewrite the others. Each use signals AI-paper "watertight argument" framing.
- **"instantiates the … paradigm"**: identical phrase with same citation appears 2x (lines 138, 313). Collapse to one usage in §3.3; in §1 use a plainer "this is a generator–verifier protocol with a simulator verifier".
- **Rhetorical self-questions**: "Why does verified-CF pay off on Slide?" (line 380) and "Why does the regime end?" (line 476) within the same paper. One is rhetorical flourish; two is a tic. Cut both — lead with the answer.
- **"The framing yields …"**: appears at line 119 ("framing yields four contributions") and line 254 ("framing yields a falsifiable prediction"). Vary it; "Prediction:" or "Four contributions follow:" or just drop the framing-sentence entirely.
- **Hedged intensifiers without numbers**: "substantially above HER" (line 362), "essentially tied" (line 373), "marginally" (line 376), "effectively invisible" (line 100), "essentially a free signal" (line 494). Each could become specific or be cut. The paper has the numbers nearby — use them in the same clause ("0.85 vs 0.617 — 0.23 above HER@250k") instead of "substantially above".
- **Em-dash overuse**: triple em-dashes in single paragraphs at lines 39-42, 88-90 (abstract), 134-138, 261-264, 309-313, 477-485. Some are fine; the §6 cold-start paragraph has 4 em-dashes in one paragraph (lines 471, 477, 481, 484-485). Replace half with periods or colons.
- **Tricolons / lists of three**: "0.85 / 0.35 / 0.617" (fine, it's data), "Push / PickAndPlace / Slide" (fine, it's three envs), but also "parse / task-relevance / plausibility" (line 81, 432) appears twice and reads templated, and "snapshot…, fork…, roll out…, accept…, reject…" (lines 287-294, the per-episode protocol) is a five-step list ending in a tricolon-rhetoric flourish "structurally inexpressible". Keep the numbered protocol; cut the closing flourish.
- **"strictly-dominating" / "strictly more informative" / "strictly costlier" / "strictly-correct"**: "strictly" appears 4x across the paper (lines 144, 184, 88, 501). It is AI-flavored emphasis ("strictly" is the favored hedge for "really really"). Each use is defensible individually; collectively they pattern-match. Cut at least 2.
- **"load-bearing"**: lines 397, 465. Twice in one paper for a colloquial CS-Twitter idiom is fine but flag-worthy if the paper is otherwise formal.

## Most-improved-if-rewritten paragraphs

1. **§6 Conclusion (lines 511-526)**: highest leverage. It hits four AI tropes in one paragraph: "we re-frame … showing that … is the principled choice", "by construction", recap-of-numbers cadence, and the "stand independently of any single training outcome" flourish. Rewrite to lead with the strongest empirical claim and end on the kill-experiment honesty, no flourish. (See Passage 1 suggested rewrite.)

2. **§3.3 "Asymmetric failure modes" (lines 306-316)**: the quality-dial / throughput-dial parallelism is the single most AI-sounding sentence pair in the paper. Break the parallelism; cut the dial metaphor. (See Passage 5.)

3. **Abstract "Methodological contributions" (lines 50-63)**: dense and informative but the gerund-tricolon and "we recast / we close" verbs are textbook AI. Tightening here pays off because the abstract is what every reader sees first. (See Passage 10.)

4. **§1 lines 119-128**: replace "This framing yields four contributions" + four bolded items with a single-sentence problem statement followed by a less-templated contributions list. The four-numbered-contributions scaffolding is the most structurally AI thing in the paper.

5. **§3.2 teleport-collapse setup (lines 269-280)**: "the lowest-perplexity continuation" + "trajectory-independent Dirac" + "We call this teleport-collapse" — the diagnostic content is correct but the phrasing is in AI-pedagogical voice. Rewrite as a working-engineer description of what the model does. (See Passage 7.)

## What is NOT a problem (don't change)

- §2 Related Work (lines 157-206) is paragraph-level human-voice writing: each paragraph has a clear claim, citations cluster appropriately, sentence lengths vary. Leave it alone.
- §7 Contributions list (lines 528-547) reads as plainly-authored author statements. Do not touch.
- The numeric prose in §5 ("HER $0.167\pm 0.117$ vs.\ Oracle-CF $0.117 \pm 0.044$ ($\Delta=-0.05$, below threshold)") is the strongest evidence the paper is human-authored. Keep this register.
- Tables and figure captions are appropriately terse.
- Math display equations and the per-episode protocol (lines 287-294) read as engineer prose, not AI prose.

## Bottom line

The paper is broadly human-voiced (numbers, named seeds, dollar costs, commit hashes, specific failure modes) and the AI tells are concentrated in a small number of high-visibility passages: the conclusion paragraph, the §1 four-contributions scaffold, two rhetorical questions, three uses of "by construction", and two uses of "instantiates the … paradigm". An afternoon of targeted edits to those passages will bring the overall AI-voice score from ~4/10 to ~2/10 with no content change.

Highest-leverage edits, ranked:
1. Rewrite the conclusion paragraph (lines 511-526).
2. Kill the duplicate "instantiates the … paradigm" (line 138).
3. Cut 2 of 3 "by construction" uses.
4. Cut both rhetorical self-questions (lines 380, 476).
5. Break the quality-dial / throughput-dial parallelism (lines 306-316).
