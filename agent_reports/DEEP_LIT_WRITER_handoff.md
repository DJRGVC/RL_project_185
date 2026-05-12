# DEEP-LIT-WRITER Handoff — Phase 1+2+3 Complete

*Agent: DEEP-LIT-WRITER (Opus 4.7). Date: 2026-05-11. Total budget used: ~2h.*

## Deliverables produced

1. `agent_reports/DEEP_LIT_REPORT.md` — adversarial scan of 2024-2026
   VLM-RL/hindsight/PER/counterfactual literature, with TOP-5 THREATS
   list and rebuttal arguments. ~40 papers reviewed.
2. `agent_reports/APPROACH_REFINEMENTS.md` — 8 concrete refinements
   (5 writing-only, 3 new-experiment) grounded in Phase 1 findings.
3. `agent_reports/paper/main.tex` — substantive prose rewrite:
   abstract, intro contribution bullets, related work, theory section,
   verified-CF section, limitations.
4. `agent_reports/paper/refs.bib` — 11 new citations added.
5. `agent_reports/9pm_presentation.pdf` — recompiled, visual quality
   gate **PASS**, 0 undefined citations, 26 pages total
   (~11 main + ~15 refs/appendix).

## (a) Top-5 threats identified, with rebuttal-ready differentiation

1. **Sharony et al., VLM-RB (arXiv 2602.01915, Feb 2026)** — closest
   published work. *Differentiation:* multiplicative (preserves PER IS-
   correction) vs.\ additive mixture (implicitly retargets to a
   $\lambda$-weighted objective); failure-direction localization vs.\
   success scoring; verified-CF mechanism entirely outside their scope.
   Now sharpened in paper Sections 1, 2 (new Sharony paragraph),
   3 (new "Why multiplicative?" subsection with uniqueness argument).
2. **CAST (Glossop et al., Aug 2025)** — VLM counterfactual labeling
   for VLA. *Differentiation:* CAST is offline data augmentation for
   navigation/instruction-following; ours is online replay
   prioritization for sparse-reward manipulation; CAST relies on VLM
   plausibility, ours verifies in simulator. Already cited; no edits
   required.
3. **Freshness-Aware PER (Ma et al., 2026)** — closest 2026 PER paper.
   *Differentiation:* their priority modifier is endogenous (policy
   age); ours is exogenous (VLM causal-influence). Two contributions
   are orthogonal — could be combined. Already cited in Limitations.
4. **Large Reward Models (Wu et al., March 2026)** — per-timestep VLM
   rewards. *Differentiation:* reward-shaping couples Q-target accuracy
   to VLM calibration (bias); replay-shaping leaves TD target alone
   (variance only). Now explicitly addressed in new "Why multiplicative?"
   subsection of paper Section 3 (Prediction P2).
5. **ECHO (Hu et al., Oct 2025)** — HER for LM agents.
   *Differentiation:* ECHO rewrites language goals on existing
   trajectories; we generate *new* trajectories via VLM-proposed
   actions verified by simulator. Already cited.

## (b) Sections rewritten in `agent_reports/paper/main.tex`

1. **Abstract** (lines 34-60). Reframed around two contributions
   (IS-posterior framing + verified counterfactual) with the
   "multiplicative is unique" claim foregrounded. Added explicit
   three-VLM-family (GPT-4o, Opus 4.7, Sonnet 4.5) framing.
2. **Introduction contribution bullets** (lines 83-129). All four
   bullets rewritten for specificity. Added explicit replay-vs-reward
   distinction (Bullet 2), generator-verifier framing (Bullet 3),
   three-family robustness framing (Bullet 4).
3. **Related Work: Foundation Models paragraph** (post-update).
   Added Wu et al. 2026, IKER, AHA differentiation (three orthogonal
   ways AHA differs), RLVR-F, AgentHER. AHA differentiation is
   particularly important because reviewers will ask "why isn't this
   just AHA-driven prioritization?"
4. **Related Work: New Generator-Verifier paragraph** (after Foundation
   Models). Names the paradigm; positions our simulator-as-verifier as
   a symbolic verifier in the program-synthesis sense.
5. **Related Work: Sharony differentiation paragraph**. Rewritten
   from apologetic-concurrent framing to assertive distinction: spells
   out the two methodological cores (multiplicative vs.\ additive;
   localization vs.\ scoring).
6. **Section 3: New "Why multiplicative? Uniqueness, additive mixtures,
   and what this buys us" subsection** (post-taxonomy table). Two
   concrete predictions (P1 uniqueness, P2 replay-vs-reward) that the
   framing forces.
7. **Section 4.3: New "A generator-verifier framing" paragraph** (before
   the "model-based hindsight" paragraph). Explicitly names the LLM-RL
   paradigm and positions our simulator as a *symbolic* verifier.
8. **Section 5.3 Key Finding paragraph**. Added single sentence
   pointing forward to Sonnet 4.5 cross-family confirmation as
   "three-family robustness" evidence.
9. **Section 6 Limitations**. Added new limitations (v) open-weights
   VLMs not yet covered and (vi) simulator-as-verifier requires forkable
   env. Existing (iv) updated to call out MiniGrid head-to-head.

## (c) Citations added to `agent_reports/paper/refs.bib`

1. `pleiss2025reaper` — Reliability-Adjusted PER (proposal-shaping precedent)
2. `yamani2025rpeper` — Reward-Prediction-Error PER (same family)
3. `wang2025prioritizedgenerative` — Prioritized Generative Replay (ICLR 2025)
4. `wang2024rlvlmf` — RL-VLM-F (VLM-as-judge for RL, ICML 2024)
5. `wu2025rlvrworld` — RLVR-World (NeurIPS 2025; world-model RL)
6. `ding2026agentHER` — AgentHER (multi-judge verification precedent)
7. `zha2025tango` — RL Tango (generator-verifier paradigm; NeurIPS 2025)
8. `wu2026largerewardmodels` — Large Reward Models (per-timestep VLM
   reward, March 2026; this is Threat #4 — cited explicitly in
   differentiation argument)
9. `patel2025iker` — IKER (real-to-sim-to-real reward, ICRA 2025)
10. `urpi2024caiac` — CAIAC (counterfactual data augmentation for
    Fetch envs)
11. `krutsylo2025nonuniform` — Non-uniform memory sampling

## (d) Build verification

- LaTeX builds cleanly: 3-pass pdflatex + bibtex run via build.sh.
- 0 undefined citations after final pass.
- Visual quality gate (`scripts/visual_quality_gate.py`) — **PASS**.
- Total pages: 26 (11 main body + ~15 references/appendix).
- Compiled PDF lives at `agent_reports/9pm_presentation.pdf`.
- Page 4 cleanly shows new "Why multiplicative?" subsection.
- Page 3 cleanly shows new Foundation Models paragraph with AHA
  differentiation and new Sharony differentiation block.

## (e) What the next-iteration crons should prioritize

**For Reviewer #1 (00:19 PDT) and beyond:**

1. **Pull HER baseline numbers** as they finish overnight and replace
   the "in-flight" placeholder in Section 5.6. The PATHC-LEAD agent
   is set up to deliver these.
2. **Check for over-long lines** — there are a few overfull-hbox
   warnings (2.7pt and 29pt) in the new abstract and intro that the
   small crons can address with line-by-line wordsmithing.
3. **Verify Table 1 (Sharony differentiation table)** is still
   consistent with our new paragraph text — I did not modify the
   table itself but the prose around it has changed; a copy-edit pass
   should confirm consistency.
4. **Build out Figure 1 caption** — now that we have stronger framing
   around "VLM-family robustness," the headline figure caption could
   refer back to the prompt-grid evidence.
5. **Tighten the abstract** — at 26 lines it's still on the long side
   for NeurIPS. A subsequent cron could compress 2-3 sentences.
6. **NEW EXPERIMENT TODOs flagged for PATHC-LEAD tomorrow** (from
   `APPROACH_REFINEMENTS.md` R6/R7/R8):
   - Strictly-correct IS-weight $w_{IS,\text{Sem}}$ ablation
   - Cross-family transfer to Adroit or robosuite
   - Open-weights VLM swap (LLaVA-NeXT or Qwen2.5-VL)

## Final sanity-check summary

| Item | Status |
|---|---|
| Phase 1 lit dump | DONE (`DEEP_LIT_REPORT.md`, ~40 papers) |
| Phase 2 approach refinements | DONE (`APPROACH_REFINEMENTS.md`, 8 items) |
| Phase 3 writing pass | DONE (main.tex; abstract + intro + related work + theory + methods + limitations) |
| Refs.bib updated | DONE (11 new entries) |
| Paper compiles | YES |
| Visual quality gate | PASS |
| Undefined citations | 0 |
| Touched in-flight runs | NO |
| Other agents' reports modified | NO |
