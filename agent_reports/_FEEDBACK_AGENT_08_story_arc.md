# Agent 08 — Story-Arc Reviewer

Paper reviewed: `agent_reports/paper_cs285/main.tex` (commit on `agent/pathc-lead`).
Reviewer role: first-time reader with no prior project context, evaluating logical
flow, transitions, and claim/delivery consistency.

## Narrative map (as a first-time reader reconstructs it)

- **Hook (Ext. Abs. + §1 ¶1).** "How do you assign credit in a 50-step sparse-reward
  Fetch trajectory when the TD signal decays exponentially from a single terminal
  reward bit?" The hook is *credit assignment*, not VLMs.
- **Setup (§1 ¶1).** Standard PER cannot help because TD error is itself the
  bottleneck; HER relabels but cannot single out the failure-causing timestep.
- **Tension (Ext. Abs. + §1 ¶2).** Recent VLM-RB uses VLMs additively for
  prioritization, but (the paper claims) this implicitly retargets the Bellman
  loss; meanwhile direct VLM counterfactual goals collapse to teleports.
- **Insight (§1 contrib. (1), §3.1).** Cast VLM-guided replay as an
  IS-posterior $q_\phi(t^\star\mid\tau)$; multiplicative combination with PER
  preserves a clean IS-correction; additive does not.
- **Methods (§3.1–§3.3).** Semantic PER (multiplicative reweighting) +
  Verified-CF (ask for actions not goals, execute in simulator fork, accept
  only physics-consistent reward-positive relabels).
- **Climax (§5.1).** Verified-CF matches VLM-CF in aggregate at 500k
  ($0.606$ vs $0.622$) and wins on Slide ($+0.07$ vs VLM-CF, $+0.43$ vs
  HER@250k, $+0.45$ vs PER@3M).
- **Resolution (Conclusion).** Two independent contributions stand:
  IS-posterior framing + simulator-as-verifier guarantee.
- **Limitations (§6).** Cold-start verifier-rejection regime;
  pre-registered Oracle-CF kill bounds the headroom; small-$n$ everywhere;
  needs forkable simulator.

The arc is recognizable and roughly intact, but it has **three structural
fractures** flagged in detail below: the headline jumps between two different
methods, the kill verdict is simultaneously a "negative result" and a
"transparent post-hoc tie," and Semantic-PER is theorized in §3 but never
actually trained as a standalone method in §5.

## Section-to-section coherence

### Ext. Abstract → §1 Introduction
**Flow: weak.** The Ext. Abstract leads with two methodological contributions
*and the headline result*. §1 then re-introduces the same problem from
scratch ("The core difficulty of sparse-reward manipulation is temporal
credit assignment…") and re-states contributions (1)–(4) in slightly
different wording. A reader who took the Ext. Abstract seriously sees §1 as
redundant; a reader who skipped it sees §1 as the real intro.
*Specifically:* Ext. Abs. ¶3 already states the FetchSlide $0.617$ vs $0.55$
result; §1 never echoes a numeric headline, so the abstract is the only
place §1's contribution (3) is grounded.

### §1 → §2 Related Work
**Flow: good.** Contribution (1) "IS-posterior framing of VLM-guided replay"
lands cleanly on §2's three paragraphs (HER/PER lineage; explicit VLM-RB
differentiation; foundation-model credit assignment). The VLM-RB
"additive vs multiplicative" contrast appears in §1 ¶3 *and* §2 ¶2 *and*
§3.1 — this is on-message but borders on repetitive.

### §2 → §3 Method
**Flow: moderate.** §2 closes on "VLM-as-reward approaches … splice the VLM
signal into the TD target; we leave the env's true sparse reward intact in
the TD target." §3.1 then opens with the off-policy Bellman regression. The
transition is technically fine but the reader expects §3 to open with the
*verifier* (the more novel contribution) and instead gets the Semantic-PER
math. The contribution ordering in §1 (Semantic PER first, Verified-CF
second) is correct given §3's structure, but as a *story* the verifier is
the marquee piece — see "Buried lede" below.

### §3.1 → §3.2 → §3.3
**Flow: good locally but jarring at §3.2.** §3.1 is pure theory
(IS-posterior reweighting); §3.2 abruptly switches to an empirical taxonomy
of prompt output types and the teleport-collapse failure mode. There is no
bridging sentence explaining *why* a section on counterfactual prompting
appears in "Method." §3.3 then redeems §3.2 by showing the verifier closes
the teleport loophole. The cleanest re-org would be to retitle §3.2 as
"Motivation for action-level counterfactuals" or fold it into §3.3.

### §3 → §4
There is no §4 — §4 is "Experiments" labeled `\section{Experiments}` with
`\label{sec:exp}`, but the paper has no §3.4 transition paragraph, and §5
opens cold on "Setup." A one-sentence preview ("We test three predictions:
(a) verified-CF improves on HER at 500k, (b) teleport-collapse is
prompt-architectural, (c) Oracle-CF cannot beat HER at 250k") would help.

### §5.1 → §5.2 → §5.3 → §5.4 (within Experiments)
**Flow: fractured.** §5.1 reports the *headline* (Verified-CF training
outcome). §5.2 then jumps backward in the research process to *prompt
design* — work that logically *precedes* the headline runs. §5.3 continues
the prompt-design thread on real episodes. §5.4 then jumps to the *kill*
experiment, whose decision rule (Oracle-CF at 250k) is what motivated the
*pivot* to the headline in §5.1. The chronology of the project is:
Oracle-CF kill → prompt design → verified-CF runs → headline. The paper
reports them in the order: headline → prompt design → kill, which forces
the reader to repeatedly rebuild context. A reader reaching §5.4 may
reasonably ask "wait, this kill verdict came *before* the §5.1 numbers
existed — so what is being claimed?"

### §5 → §6
**Flow: moderate.** §6's "cold-start verifier-rejection regime" paragraph
maps cleanly to a weakness the §5.1 numbers implicitly contain
(PickAndPlace $0.35\pm0.10$, which is much weaker than Push). But §5 never
flags this PickAndPlace softness as a candidate weakness, so §6's
limitation feels like new material rather than a follow-up. The
"Oracle-CF kill bounds the headroom" paragraph in §6 is a *re-framing* of
§5.4 — fine, but the reader has already absorbed that framing.

### §6 → Conclusion (within §6)
**Flow: good.** Conclusion is a faithful compression of the contributions.

## Logic gaps found

1. **Gap: Semantic PER is theorized but never run.** §3.1 develops the
   multiplicative Semantic-PER proposal $\mu_P\cdot w_\text{sem}$ as a
   centerpiece. §5 contains zero training runs of "Semantic PER" as such
   — only `vlm_cf`, `verified_cf`, `oracle_cf`, and the HER/PER/Uniform
   baselines. The Contributions section even admits Parshawn ran "Semantic-PER
   with GPT-4o" in a prior 36-run suite, but the main text never reports
   those numbers. *The reader is invited to credit a theoretical contribution
   whose empirical version is absent from the experiments section.* The
   falsifiable prediction at the end of §3.1 ("Semantic PER tracks
   standard PER when the VLM is poorly calibrated and pulls ahead when it
   is reliable") is **never tested in §5**.

2. **Gap: Why is verified-CF "the same as" Semantic PER's framing?** §3.1
   builds the IS-posterior story; §3.3 introduces Verified-CF as if it
   were the same project. But Verified-CF *writes new trajectories into
   the buffer* — it is not a reweighting at all. The IS-correction
   analysis in §3.1 simply does not apply to Verified-CF, and the paper
   never says so. A reader expecting the bias bound in §3.1 to underwrite
   the headline result of §5.1 will be confused.

3. **Gap: Oracle-CF at 250k vs at 1M.** §5.4 reports the 250k kill
   ($\Delta=-0.05$) and then a 1M post-hoc tie ($0.583 = 0.583$). The
   verdict "Path C is killed" is justified by the 250k number, but the
   1M number says "headroom is exactly zero at convergence." The paper
   then claims VLM-CF@500k ($0.367$) reaches 63\% of HER@1M's asymptote
   — but this is an apples/oranges comparison (vlm_cf trained 500k,
   HER trained 1M). The reader cannot tell whether VLM-CF *would* tie
   HER at 1M. **Missing prediction.**

4. **Gap: "Teleport-collapse is prompt-architectural, not model-specific"
   vs Opus 4.7 4/4.** §1, §3.2, and §5.2 all assert
   "prompt-architectural, not model-specific" — but the table shows GPT-4o
   achieves $0/6$ on `achieved_goal` while Opus achieves $4/4$ on the
   *same* prompt. That is a model-specific effect on a fixed prompt; the
   prompt-architecture claim is really "architecture *and* model jointly
   determine teleport rate." The framing is overclaimed.

5. **Gap: Bias bound stated without derivation in main text.** §3.1
   states $|\hat{\mathcal L}_\text{under} - \mathcal L_U| \le
   C(w_\text{max}^{\beta_t}-1)((2W+1)/T)\|\ell\|_\infty$ and points the
   reader to "GitHub `src/buffers/semantic_per.py` + Appendix~\ref{app:methods}."
   For a NeurIPS-style paper this needs at least the assumptions and a
   one-line proof sketch in the main text; a GitHub pointer is not a
   citation a reviewer can verify.

6. **Gap: Verified-CF acceptance rates never quantified in §5.** §6
   reports "100% verifier-rejection rate over the first ~80 VLM calls"
   on PickAndPlace seed 42, but §5 never reports the *average*
   verifier-acceptance rate across the headline runs. Without this,
   the reader cannot judge how much of the §5.1 gain is "verified relabels
   actually entering the buffer" vs "the agent is just doing HER while
   the VLM idles."

## Buried lede check

- **Most important finding:** The simulator-as-verifier mechanism that
  *structurally precludes* the dominant failure mode of language-only
  counterfactuals (action-level prompting + MuJoCo execution +
  reward-positive admission).
- **Where it appears first:** Ext. Abstract ¶2 contribution (2),
  Introduction contribution (2) (§1), §3.3 in full.
- **Should it move?** *Yes — the headline of the headline.* The
  Verified-CF mechanism is the load-bearing novelty (the IS-posterior
  framing is theoretically clean but, as gap (1) above notes, has no
  matching empirical run). The Ext. Abstract leads with Semantic PER
  (contribution 1) before Verified-CF (contribution 2). Re-ordering to
  Verified-CF first — both in the Ext. Abstract bullet ordering and in
  §3 (move §3.3 in front of §3.1, with §3.1 as the theoretical
  framework that *also* covers verified-CF's relabeling channel) — would
  put the actually-demonstrated novelty in front. Currently the lede is
  not "buried" but it is "second-billed under a contribution the
  experiments don't directly support."

- **Secondary buried lede:** The FetchSlide $+0.45$ gain over PER@3M is
  the single most quantitatively striking result in the paper and
  appears in Ext. Abs. ¶3, §1 (oblique), §5.1, and Conclusion. It is
  *not* buried, but the framing "Verified-CF matches VLM-CF" in the
  §5.1 subsection title undersells the *Slide-specific* win. Consider
  retitling §5.1 to lead with the Slide result.

## Mismatched claim/delivery

- **§1 promises:** "An IS-posterior framing of VLM-guided replay" with
  a clean IS-correction analysis (contribution 1).
  **§5 delivers:** No training run of Semantic PER (the multiplicative
  proposal) as a standalone method. The headline runs are `vlm_cf` and
  `verified_cf`, both of which are *counterfactual-injection* methods,
  not Semantic-PER reweighting methods.
  **Mismatch:** The flagship theoretical contribution has no empirical
  validation in the main paper's experiments. Either §5 should add
  Semantic-PER curves, or §1's contribution (1) should be reframed as
  "a theoretical framework that *also* covers Verified-CF as a special
  case where $w_\text{sem}$ is replaced by a hard verifier gate."

- **§1 promises:** Cross-task transfer (contribution 3).
  **§5.3 delivers:** $12/12$ parse/task-relevance/plausibility on a
  *prompt* template, but *not* a cross-task transfer of the trained
  policy. Cross-task transfer of the *VLM annotation pipeline* is what
  was delivered; this is a weaker claim than "cross-task transfer" in
  the ML sense the abstract reader will assume.
  **Mismatch:** Mild but real. Rename to "cross-task prompt transfer" or
  "cross-task VLM-annotation transfer."

- **Ext. Abs. headline (i) promises:** "Verified-CF matches VLM-CF in
  aggregate, wins on Slide."
  **§5.1 delivers:** Aggregate $0.606$ vs $0.622$ (verified-CF is
  $-0.016$ lower) and Slide $0.617$ vs $0.55$. The aggregate "match"
  is honest; the Slide "win" is $+0.067$ with $n=3$ seeds and SE bars
  of $0.03$ vs $0.13$ — the gap is roughly $0.5\sigma$ of the wider
  bar. **Mismatch:** Calling this a "win" rather than "favors Verified-CF
  but is not statistically separable at $n=3$" is slightly overclaimed
  for a NeurIPS-style readership.

- **Ext. Abs. headline (ii) promises:** "Pre-registered kill verdict, honored."
  **§5.4 delivers:** The kill, then a 1M post-hoc tie that softens the
  kill, then a cross-horizon comparison that *re-licenses* VLM-CF as
  efficient.
  **Mismatch:** The Ext. Abs. frames the kill as a clean "honored"
  verdict; §5.4 actually walks the verdict halfway back. A reader will
  feel whiplash. Either the Ext. Abs. should add "(with caveats at
  1M)" or §5.4 should commit harder to the kill.

- **Conclusion drift check.** Conclusion says: (a) multiplicative
  IS-correction is the principled choice, (b) Verified-CF closes the
  failure mode by construction, (c) $0.606$ aggregate / Slide $0.617$,
  (d) Oracle-CF kill bounds the headroom, (e) framing and verifier
  stand independently of training outcome. Ext. Abstract says largely
  the same five things. **Conclusion is on-message with the abstract**;
  no drift between bookends. The drift, where it exists, is between
  §1's contributions and §5's actually-run experiments — not between
  abstract and conclusion.

## Narrative whiplash spots

1. **§3.1 → §3.2.** From IS-correction math to prompt-output taxonomy
   with no transition. The reader doesn't know that §3.2 is motivating
   §3.3.
2. **§5.1 → §5.2.** From training results to prompt-design experiments.
   §5.2 should arguably be in §3 (Method/motivation) or after §5.4.
3. **§5.4 mid-paragraph.** The pivot from "Path C is killed" to "Post-hoc
   1M runs … tie exactly" inside the same paragraph reverses the verdict
   in three sentences. Split into two paragraphs.

## Unresolved tensions

- **The "asymmetric failure modes" tension** (raised in §3.3 ¶4 and §6 ¶1)
  is the strongest analytical insight in the paper — Semantic-PER's
  miscalibration is bounded; Verified-CF's is unbounded in cold-start.
  But the paper never reconciles this with the *headline*: if Verified-CF
  has an unbounded cold-start failure mode, why is it the headline method?
  The answer (presumably: because in three of four headline runs it
  works) should be stated, not left for the reader.

- **The Sharony VLM-RB comparison** is asserted as "implicit retargeting"
  in §1, §2, §3.1 but no head-to-head run exists. §6 admits "A faithful
  VLM-RB reproduction is pre-staged in our codebase for camera-ready
  head-to-head evaluation." The reader is asked to accept the theoretical
  superiority of multiplicative over additive without an empirical
  comparison. This is a defensible move for a CS285 final but will be
  flagged by any external reviewer.

## Overall narrative quality: **6.5 / 10**

The paper has a real story (sparse-reward credit assignment →
VLM-as-posterior → verifier-by-construction → results), a clean
prose voice, and a transparent treatment of the kill verdict. The
arc is recognizable as a coherent piece of work.

The deductions:
- **−1.0** for the §3 theoretical contribution (IS-posterior /
  Semantic-PER) not being matched by a §5 experiment. This is the
  single biggest narrative weakness — the lede the paper *leads* with
  is not the contribution the data *supports*.
- **−0.8** for the §5 internal ordering (headline → prompt design →
  kill) reversing project chronology and forcing context-rebuilding.
- **−0.5** for the §3.1 → §3.2 transition being unmotivated.
- **−0.4** for the kill verdict being simultaneously "honored" and
  "tied at 1M" without committing to one frame.
- **−0.3** for "prompt-architectural, not model-specific" being mildly
  overclaimed when the data show a joint architecture × model effect.
- **−0.2** for the FetchSlide "+0.067 over VLM-CF" being called a
  "win" at $n=3$.
- **+0.7** credit for genuine analytic insight in the
  asymmetric-failure-modes paragraph and the IS-correction
  derivation; for the transparent Oracle-CF kill; and for the
  bias-bound formulation, which is a real piece of theory.

### Three concrete recommendations (highest-leverage edits, no rewriting required)

1. **Add a Semantic-PER training curve to §5** — even a single
   `semper_gpt4o@500k` run on FetchPickAndPlace would close the
   single biggest gap. If the run already exists in the Phase-1
   36-run suite (Contributions section suggests it does), surface
   the numbers in §5.1 or a new §5.5.
2. **Reorder §5 to chronology:** §5.4 (kill) → §5.2 (prompt design,
   which motivates the pivot) → §5.3 (real-data validation) →
   §5.1 (headline). Or, alternatively, add a 1-paragraph "research
   chronology" preface to §5.
3. **Add a bridge sentence at §3.1→§3.2** ("The IS-posterior view
   makes the design of $q_\phi$ the load-bearing engineering
   choice; we now examine the dominant failure mode of the most
   direct prompting scheme.").
