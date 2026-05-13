# Agent 02 — NeurIPS Style Emulation Audit

Auditor: Opus 4.7 (45-min budget). Paper read end-to-end (read-only). Reference
NeurIPS papers consulted via WebFetch + ar5iv mirrors.

## Reference papers consulted

- **arxiv:2404.02905 — Visual Autoregressive Modeling (NeurIPS 2024 Best Paper).**
  Opens its intro with a confident orienting sentence ("The advent of GPT
  series and other autoregressive (AR) large language models (LLMs) has
  heralded a new epoch..."). Abstract is a strict
  problem-approach-headline-result triplet ending on quantitative wins (FID
  18.65 -> 1.73, IS 80.4 -> 350.2). Contributions are a clean *numbered
  list of four items* placed at the end of the introduction. Figure captions
  begin with a one-sentence summary and then describe panels in order. Voice
  is declarative and confident but never adversarial.

- **arxiv:2410.04612 — REFUEL (NeurIPS 2024, multi-turn RLHF).**
  Abstract follows problem-approach-result. Opens intro with an
  achievement-acknowledge then pivot-to-limitation move ("Despite the
  impressive performance LLMs have demonstrated..., most LLMs struggle
  with planning..."). Contributions stated as a *short numbered list*,
  each line a single declarative sentence. Related work uses
  **bold-paragraph headers** (e.g. *"Other related policy optimization
  algorithms in RL."*) followed by 2-4 sentences each. Discussion is
  concise and limitation-honest.

- **arxiv:2406.10254 — "Towards Signal Processing in LLMs" (NeurIPS 2024).**
  Abstract opens with a direct first-person declarative ("This paper
  introduces the idea of applying signal processing inside a LLM."). No
  acronym overload, no methodological caveats in the abstract; the body
  carries the qualifications. Closing line is mildly aspirational, not
  promotional.

- **arxiv:2402.04588 — UltraLink (multilingual SFT, NeurIPS workshop).**
  Confirms the broad-context-then-pivot abstract style. Less directly
  relevant for an RL paper but useful as a baseline for "what a generic
  accepted NeurIPS abstract opening looks like."

**Common NeurIPS-accepted-paper patterns extracted from the four references:**

| Element | NeurIPS convention |
|---|---|
| Abstract opening | One-sentence problem framing; no "extended abstract" label |
| Abstract length | ~150-200 words, single paragraph |
| Intro contributions | Bullet/numbered list of 3-4 items, each ONE declarative sentence |
| Method | Equations + algorithm box + one orientation figure; minimal prose |
| Experiments | Open with headline figure/table, *then* per-section analysis |
| Related work | Bold-paragraph headers, 2-4 sentences each, no editorializing |
| Discussion | Short, limitation-honest, no re-pitching of results |
| Citations | Author-year style (`\citep`), no URLs in the bib |

---

## Section-by-section comparison

### Abstract (our lines 34-91, labelled "Extended Abstract")

**Our text (excerpt, lines 37-48):**
> *"\section*{Extended Abstract}* [...] Sparse-reward goal-conditioned
> manipulation is a temporal credit-assignment problem: in
> Gymnasium-Robotics Fetch (Push / PickAndPlace / Slide), a
> randomly-initialized policy succeeds in $<\!1\%$ of episodes [...]
> Concurrent VLM-RB \citep{sharony2026vlmrb} uses frozen VLMs as an
> *additive* priority bias; we argue the *multiplicative* form is the
> principled choice and pair it with a simulator-verified counterfactual
> channel."*

**NeurIPS convention:** Abstract is unlabeled (just produced by
`\maketitle`-adjacent abstract environment), single paragraph, ~150-200
words. The VAR paper packs problem + method + four headline numbers into
~180 words.

**Mismatch (load-bearing):**
1. **Title says "Extended Abstract" using `\section*`** -- NeurIPS papers
   use the unlabeled `\begin{abstract}...\end{abstract}` environment. The
   `neurips_2024.sty` package you've already loaded provides this; the
   reviewer's first signal that the paper is camera-ready-shaped is
   missing. The four `\paragraph{}` subheaders inside it
   (*Problem / Methodological contributions / Headline findings / Honest
   negative and roadmap*) are unprecedented in accepted NeurIPS papers --
   this reads as a "Findings"-conference structured abstract or a
   workshop-style extended abstract, not a NeurIPS one.
2. Abstract is **~520 words**, ~3x NeurIPS norm.
3. Tone has adversarial framing in the abstract itself ("we argue the
   *multiplicative* form is the principled choice"). NeurIPS abstracts
   usually leave the dialectic for the intro/related-work.

**Suggested rewrite (target ~200 words, single paragraph, no
`\paragraph{}` headers):**

> Sparse-reward goal-conditioned manipulation is a credit-assignment
> problem: a single terminal reward over a 50-step trajectory leaves the
> bulk of each episode invisible to TD learning. Hindsight Experience
> Replay (HER) relabels failures but provides no signal about which
> timestep caused failure. We re-frame Vision-Language-Model-guided
> experience replay as importance-sampled posterior reweighting and show
> that the multiplicative form (a per-transition semantic boost on top of
> a TD-error prior) admits a clean IS-correction analysis with a bounded
> bias, whereas the additive mixture used by concurrent work implicitly
> retargets the Bellman loss. To close the dominant failure mode of
> language-only counterfactual hindsight -- a 100% teleport-collapse rate
> in which the VLM copies the desired goal -- we introduce
> VLM-Verified Counterfactual Hindsight: the VLM proposes a corrective
> action sequence that is executed in a simulator fork, and only
> reward-positive, physics-consistent rollouts are admitted into the
> replay buffer. At 500k SAC steps on three Gymnasium-Robotics Fetch
> tasks, verified counterfactual hindsight reaches mean success 0.606
> (matching VLM-only counterfactuals at 0.622) and exceeds them on
> FetchSlide (0.617 vs.~0.55). A pre-registered Oracle-CF kill experiment
> bounds the credit-assignment headroom on Fetch at the 250k decision
> horizon; we honor the kill verdict transparently.

---

### Section 1 -- Introduction (our lines 93-156)

**Our text (lines 119-125):**
> *"This framing yields four contributions: \textbf{(1) An IS-posterior
> framing of VLM-guided replay} (\S\ref{sec:method})."*

**NeurIPS convention (VAR, REFUEL):** Contribution lists are short
numbered items, each *one declarative sentence*, no embedded
sub-explanations. From VAR: *"A new visual generative framework using a
multi-scale autoregressive paradigm with next-scale prediction, offering
new insights in autoregressive algorithm design for computer vision."*
That's it -- 27 words, one sentence, no parenthetical section refs in
the bullet text itself.

**Mismatch:**
- Each of our four contribution bullets is a *paragraph* (50-90 words)
  with embedded justification, mechanisms, and numbers. They read like
  mini-abstracts.
- The opening sentence (line 96, "The core difficulty of sparse-reward
  manipulation is temporal credit assignment...") is good -- declarative
  and topic-orienting, NeurIPS-shaped.
- No headline figure is referenced from the introduction. NeurIPS intros
  frequently end on a Fig.~1 pointer ("...as shown in Fig.~1.").

**Suggested rewrite of the contribution bullets:**

> Our contributions are:
> 1. We re-frame VLM-guided replay as importance-sampled posterior
>    reweighting over the failure-causing timestep, and prove a bounded
>    bias for the multiplicative form (Section~3.1).
> 2. We introduce VLM-Verified Counterfactual Hindsight, which closes the
>    teleport-collapse failure mode of language-only counterfactuals by
>    executing a VLM-proposed action sequence in a simulator fork
>    (Section~3.3).
> 3. A two-vendor three-model prompt-design sweep on real Fetch failures
>    isolates teleport-collapse as a prompt-architectural, not
>    model-specific, failure (Section~4.2).
> 4. We report a pre-registered Oracle-CF kill experiment that bounds the
>    credit-assignment headroom on Fetch at 250k steps, and we honor the
>    kill verdict (Section~4.4).

Move the technical justification of each contribution into the
corresponding method/experiment section, not the intro bullets.

---

### Section 2 -- Related Work (our lines 157-207)

**Our text (lines 160, 176, 198):** Uses `\paragraph{}` headers:
*HER, PER, and counterfactual augmentation.* / *Differentiation from
VLM-RB.* / *Foundation-model credit assignment.* This matches the
NeurIPS bold-paragraph-header convention (REFUEL does this).

**Mismatch (minor):**
- The "Differentiation from VLM-RB" paragraph (lines 176-196) is twice
  the length of the other two and reads as adversarial ("strictly more
  informative", "outside the scope of any VLM-RB-style success-scoring
  scheme"). NeurIPS accepted papers state differences crisply and let
  the empirics carry the punch:
- NeurIPS norm: name the contrast in one sentence, list the axes in 2-3
  sentences, move the empirical comparison out.

**Suggested rewrite (line 176, condense by ~40%):**

> *Differentiation from VLM-RB \citep{sharony2026vlmrb}.* VLM-RB scores
> 32-frame sub-trajectory clips with a frozen VLM and mixes the score
> additively with uniform sampling. We differ along two axes: (i) we ask
> the VLM to localize a single outcome-causing timestep rather than
> score a clip, and (ii) we combine multiplicatively with TD error
> rather than additively with the uniform proposal -- the
> multiplicative form preserves PER's IS-correction interpretation
> (Section~3.1). VLM-RB's signal is also non-actionable for relabel
> generation, whereas ours supplies the candidate that the simulator
> verifier checks.

---

### Section 3 -- Method (our lines 208-316)

**NeurIPS convention:** Method sections are *concise*: equations,
one algorithm box, one orientation figure, sparse prose. The VAR
method section weighs in at about half the length of our Section 3
despite proposing a wholly new generative paradigm.

**Mismatch:**
- **No algorithm box.** The verified-CF protocol (lines 287-294) is
  numbered prose ("(1) snapshot the MuJoCo state...; (2) fork a
  separate env..."). This should be an `algorithm` / `algorithmic`
  environment. NeurIPS papers with a procedural contribution almost
  always include one.
- **No orientation figure for the method.** Reviewers will look for a
  Figure~1 that depicts the verifier loop (snapshot -> VLM call ->
  fork rollout -> accept/reject). Currently Figure~1 is the headline
  bar chart in the experiments section. A method-orientation figure
  is the single most "NeurIPS-feeling" addition you could make.
- Lines 239-258 (the "Why multiplicative?" paragraph with P1/P2)
  embed an inequality with a hand-wave gesture to a code path and an
  appendix: *"(full derivation: GitHub
  \texttt{src/buffers/semantic\_per.py} + Appendix~\ref{app:methods})"*
  -- this is non-standard. NeurIPS papers cite the appendix
  (`Appendix~B`), never a GitHub path. Move the GitHub URL to a
  reproducibility section / footnote.
- The "Asymmetric failure modes" paragraph (lines 306-316) mixes
  method and discussion. Consider moving the asymmetry observation
  itself to the Discussion (Section 6), keeping only the
  generator-verifier correctness statement here.

**Suggested rewrite move:** add an `\begin{algorithm}` box for
Verified-CF, factor the verifier protocol into 6 short lines
(snapshot / fork / rollout / accept-if-positive / relabel / fall back
to HER), and add a single-panel orientation figure right after
Eq.~(1).

---

### Section 4 / 5 -- Experiments (our lines 318-460)

**Our text (line 357):** *"\subsection{Headline: Verified-CF matches
VLM-CF, wins on Slide}"*

**NeurIPS convention:** Headline tables/figures appear at the *top* of
the experiments section, followed by per-task analysis. The VAR paper
puts the main ImageNet table at the top of Section 4 with no preamble
beyond "Setup."

**Mismatch (small):**
- The "Setup" + "Horizon caveat" paragraphs (lines 321-341) are well
  placed.
- **But the headline figure caption (lines 346-354) is doing too much
  work.** It contains a *meta-instruction to the reader* about how to
  read the bars: *"Within-horizon comparisons (same stamp) are
  statistically meaningful; cross-horizon comparisons should be read
  as efficiency claims."* NeurIPS captions usually contain only:
  (a) one-sentence pointer to what the figure shows, (b) panel
  identifications, (c) statistical conventions (mean +/- SE,
  *n*=seeds). Reading guidance belongs in the body text.
- The subsection title *"Headline: Verified-CF matches VLM-CF, wins
  on Slide"* (line 357) reads as a slogan. NeurIPS subsection titles
  are descriptive ("Results on FetchPush/Pick/Slide") rather than
  result-y. Consider: *"Final-success comparison across three Fetch
  tasks."*
- **Bold-call-out within-paragraph leads** (`\textbf{FetchPush
  (500k).}` etc., lines 360, 364, 367) are unusual. The standard
  NeurIPS pattern is one `\paragraph{Push.}` or
  `\subsubsection{Push.}` per task, not inline bolded leads.

**Suggested rewrite of the headline-figure caption (line 346):**

> Figure 1: Final evaluation success on three Fetch tasks (mean +/- SE,
> n=3 seeds; individual seeds overlaid as dots). Training budgets vary
> by method (annotated below each bar); see Section 4.1 for the
> within- vs.~cross-horizon reading.

---

### Section 6 -- Discussion (our lines 462-526)

**Our text (line 511-526):** *"\paragraph{Conclusion.} We re-frame
VLM-guided experience replay as importance-sampled posterior
reweighting, showing that the multiplicative form is the principled
choice [...]."*

**NeurIPS convention:** Discussion is concise and limitation-honest.
The conclusion paragraph either does not exist or is two sentences
that don't re-pitch. REFUEL has no separate "Conclusion" paragraph at
all -- the Discussion section terminates on a limitation.

**Mismatch:**
- The Discussion is *strong* in voice and structure -- bold paragraph
  headers, asymmetric-failure-mode analysis, a kill-experiment honesty
  paragraph. This section is the most NeurIPS-shaped part of the
  paper.
- **But the Conclusion paragraph (lines 511-526) re-pitches the
  abstract.** It recites the IS-posterior framing, the verified-CF
  story, the 0.606 number, the kill experiment, and the standing of
  the guarantees. This is what an abstract is for. Recent NeurIPS
  papers either omit a conclusion paragraph or limit it to one
  forward-looking sentence.

**Suggested rewrite of the conclusion (replace lines 511-526):**

> *Conclusion.* The IS-posterior framing and the simulator-as-verifier
> guarantee stand independently of any single training outcome; the
> verified-CF mechanism is a drop-in replacement for HER's relabel
> step in any forkable simulator. Extension to non-resettable
> environments via a learned dynamics-model verifier is the natural
> next step.

---

### References / bib style

Cannot inspect `refs.bib` from this audit (read-only on `main.tex`),
but the bibliography style is correctly set:
*"\bibliographystyle{plainnat}"* (line 549) with
`numbers, compress` natbib options on line 3. This is
NeurIPS-canonical. **Action item for a future agent:** verify
`refs.bib` entries do not include URL fields for non-arxiv-only papers
-- NeurIPS bib convention omits URLs for venue-published work.

---

## Overall verdict

**Mostly NeurIPS, but the framing layer (abstract + intro contribution
bullets + method-section presentation) needs ~1 day of polish to read
like an accepted paper rather than a CS-285 final report.** The
intellectual content is at NeurIPS level; the *packaging* signals
"workshop submission" or "extended technical report" in three concrete
ways: (1) the labeled "Extended Abstract" with `\paragraph{}`
subheaders, (2) paragraph-length contribution bullets, and (3) the
missing method-orientation figure + algorithm box. Sections 2, 4, and
6 already match the convention closely.

The voice is, in places, slightly defensive/adversarial against
VLM-RB. Accepted NeurIPS papers tend to differentiate crisply once
and then let the experiments carry the contrast.

## Top-5 prioritized fixes (line-specific)

1. **Lines 34-91 -- replace the "Extended Abstract" structure with a
   single-paragraph `\begin{abstract}...\end{abstract}` of ~200
   words.** Drop the four `\paragraph{Problem/Methodological
   contributions/Headline findings/Honest negative and roadmap.}`
   subheaders. This is the single highest-signal "looks like a
   NeurIPS paper" fix.

2. **Lines 121-155 -- rewrite contribution bullets as one declarative
   sentence each.** Each current bullet is 50-90 words with embedded
   justification; NeurIPS norm is ~25-30 words, one sentence, with a
   section pointer. Move the justification into the corresponding
   method/experiment subsection.

3. **Section 3 (lines 208-316) -- add an `\begin{algorithm}` box for
   the Verified-CF protocol AND add a method-orientation Figure~1
   showing the snapshot/fork/rollout/accept-or-reject loop.** Currently
   the procedure is numbered prose, the only figure is in the
   experiments section, and the "GitHub `src/buffers/semantic_per.py`"
   reference on line 248 should become an appendix pointer with the
   URL in a footnote or reproducibility section.

4. **Lines 346-354 -- shorten the headline-figure caption and move
   the within-vs-cross-horizon reading guidance into the body text
   (line 357 vicinity).** NeurIPS captions don't include reader
   meta-instructions; they identify panels and statistics only.

5. **Lines 511-526 -- shorten the Conclusion paragraph from ~120
   words to ~30, and drop the abstract-rerun.** The Discussion
   section's "asymmetric failure modes" and "Oracle-CF kill bounds the
   headroom" paragraphs are the load-bearing prose here and should be
   the last thing the reviewer reads, not a re-pitch.

---

## Smaller stylistic notes (not in the top 5)

- Line 21: `\thanks{CS 285 Final Project, Spring 2026. UC Berkeley,
  Department of EECS.}` reveals the venue is a course, not NeurIPS.
  For a "looks like NeurIPS" emulation, drop the course attribution
  (move it to the acknowledgments / contributions section, which
  already exists at line 528).
- Lines 360, 364, 367, etc.: inline `\textbf{FetchPush (500k).}` leads
  are uncommon in NeurIPS. Use `\paragraph{FetchPush (500k).}`
  consistently (the rest of the paper already does this in the
  related-work and discussion sections).
- Line 248: `(full derivation: GitHub
  \texttt{src/buffers/semantic\_per.py} + Appendix~\ref{app:methods})`
  -- drop the GitHub path from the body, put it in a footnote or a
  reproducibility paragraph at the end of Section 1.
- Line 357: subsection title is a slogan ("Verified-CF matches VLM-CF,
  wins on Slide"). Convert to a descriptive title.
- Lines 528-547: The `\section*{Contributions}` (author contributions)
  section is unusual in NeurIPS papers, which use a
  `Contributions` paragraph in the Acknowledgments. NeurIPS 2024
  style guide does encourage author-contribution statements but they
  usually appear in a single short paragraph, not a bulleted list.
