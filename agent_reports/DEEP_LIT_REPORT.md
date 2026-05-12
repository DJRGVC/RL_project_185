# Deep Literature Report — VLM-Verified Counterfactual Hindsight

*Author: DEEP-LIT-WRITER agent. Date: 2026-05-11.*

This report supplements `agent_reports/L2_bibliography.md` with an
adversarial scan of the 2024-2026 VLM-RL / hindsight / counterfactual /
prioritized-replay literature. Goal: find papers we should be citing —
especially THREATS that might scoop our contribution if a NeurIPS reviewer
found them and we didn't.

Tagging convention: **THREAT** (close scoop, must address head-on),
**STRENGTH** (cites our direction, lets us claim continuity with established
work), **NEUTRAL** (relevant context, cite in related work).

---

## TOP-5 THREATS (rebuttal-ready differentiation arguments)

### Threat 1: Sharony et al., "VLM-Guided Experience Replay" (arXiv 2602.01915, Feb 2026)

**The threat.** This is the single closest published paper. Frozen VLM
scores sub-trajectory clips for replay prioritization; reports 11-52%
higher success and 19-45% better sample efficiency on game-playing and
robotics (continuous + discrete domains). We already address this paper
in our Related Work and in `tab:differentiation` and acknowledge the
concurrent overlap.

**Differentiation argument (already in our paper, sharpen it):** We diverge
along five orthogonal axes summarized in our Table 1: (i) **failure-direction
localization vs. success scoring** — they ask "is this clip good?", we ask
"which timestep made this episode bad?", a strictly more informative
question for sparse-reward credit assignment; (ii) **single-timestep
granularity vs. 32-frame clips** — our signal pinpoints the actionable
transition, theirs averages across a window; (iii) **multiplicative
TD-weighting vs. uniform-mixture** — we preserve PER's IS-correction
structure and degenerate gracefully at $w_{\max}=1$, they require a
$\lambda$ warm-up schedule and break the IS interpretation; (iv) we ship a
**verified counterfactual hindsight** mechanism (Section 4.3) that is
entirely outside their scope; (v) we report **single-prompt cross-task
transfer evidence (12/12)**, which their per-benchmark $\lambda$ tuning
cannot achieve. Their stronger empirical results (deep ablations on
MiniGrid/OGBench) are a follow-up direction for us, not a methodological
threat.

### Threat 2: Glossop, Chen, Bhorkar, Shah, Levine — "CAST: Counterfactual Labels Improve Instruction Following in Vision-Language-Action Models" (arXiv 2508.13446, Aug 2025)

**The threat.** CAST uses a VLM to *generate counterfactual labels* for
trajectories in an existing robot dataset: given an observed scene, the
VLM proposes hypothetical instructions that the robot *could have*
executed at that state, and the system synthesizes plausible actions for
those instructions. CounterfactualVLA achieves +27% success rate on
visual navigation. Already cited as `glossop2025cast` in our refs.bib.

**Differentiation argument.** CAST is offline data augmentation for VLA
instruction-following on navigation; we are online experience-replay
prioritization for SAC+HER on continuous-control manipulation. Crucially,
CAST does *not verify* its counterfactual labels — it relies on VLM
plausibility, which is exactly the failure mode (teleport-collapse, 100%
on Opus 4.7) that motivates our simulator-fork verification. CAST also
operates in the language/instruction space; our verification operates in
physics-space (action sequences against MuJoCo dynamics). The two methods
are complementary: CAST augments before training, our scheme prioritizes
during training and verifies in simulator before relabel-admission.

### Threat 3: Ma et al., "Freshness-Aware Prioritized Experience Replay for LLM/VLM Reinforcement Learning" (arXiv 2604.16918, March/April 2026)

**The threat.** Closest published 2026 work on PER + foundation models.
Identifies priority staleness as the dominant failure mode of PER when
combined with rapidly-evolving LLM/VLM policies, and proposes age-decay
weights grounded in exponential ESS decay theory. Reports massive
gains (+46% NQ Search, +367% Sokoban Simple, +133% VLM FrozenLake).
Already cited as `ma2026freshness`.

**Differentiation argument.** Their setting is post-training of LLMs/VLMs
where the policy itself is a foundation model and trajectories are token
sequences; ours is SAC training of a small actor-critic where the VLM is
*exogenous* — a frozen oracle queried per failed episode. Their priority
modifier is endogenous (a function of policy age); ours is exogenous (a
function of causal influence as judged by an external VLM). We
already flag freshness as a limitation in our Discussion section and
defer to their work — this is the right cite. The two contributions are
orthogonal: their freshness correction could be combined with our
semantic boost in a future system.

### Threat 4: Wu et al., "Large Reward Models: Generalizable Online Robot Reward Generation with Vision-Language Models" (arXiv 2603.16065, March 2026)

**The threat.** A foundation-VLM-based reward generator that produces
**per-timestep rewards** (process + completion + temporal-contrastive)
rather than trajectory-level evaluations, evaluated on long-horizon
manipulation benchmarks. Closest in spirit to what a reviewer might
imagine as "an alternative to your Semantic-PER": just use the VLM to
densify reward instead of to reshape replay priority.

**Differentiation argument.** Per-timestep VLM reward generation
fundamentally couples value-function learning to VLM calibration: if the
VLM is wrong on a timestep, the Q-target is wrong, and the policy
absorbs the error directly. Our scheme keeps the VLM as a *proposal
modifier* in importance sampling (Eq. 5 of our paper); the actual TD
target is recomputed against the env's true sparse reward at training
time, so VLM miscalibration only changes the *sampling distribution*,
not the *Q-target estimate*. This is mathematically analogous to V-trace
ratio truncation: a controlled bias for variance reduction, not a reward
hack. A reviewer asking "why not just shape reward?" can be answered:
because our objective remains uniform-replay of the unmodified sparse
MDP in the IS limit, and theirs does not.

### Threat 5: Hu, Van Durme, Andreas, Jhamtani — "ECHO: Sample-Efficient Online Learning in LM Agents via Hindsight Trajectory Rewriting" (arXiv 2510.10304, Oct 2025)

**The threat.** ECHO adapts HER to language-model agents: when a goal is
not achieved, the LM identifies subgoals that *were* achieved and rewrites
the trajectory as a synthetic positive demonstration for those subgoals.
Up to +80% over vanilla LM agents on web-style tasks. Already cited as
`hu2026echo`.

**Differentiation argument.** ECHO operates in language/instruction space
with no simulator or physics involved; the hindsight relabel is *language
re-interpretation* of an already-completed trajectory. Our counterfactual
hindsight is fundamentally different: the VLM proposes a *new* action
sequence that was *not* executed in the original trajectory, and the
simulator decides whether that proposal succeeds. ECHO cannot generate
truly novel trajectories; we can. ECHO's correctness rests on the LM
judge ("is the rewritten goal really achieved?"); ours rests on the
ground-truth simulator dynamics, which carry zero modeling error.

---

## External Context — Deep Search

Topic ordering matches the launch prompt.

### 1. VLM-Counterfactual / Hindsight / Vision-Language Approaches

- **Glossop et al. 2025, CAST** (arXiv 2508.13446) — STRENGTH/THREAT.
  VLM-generated counterfactual labels for VLA navigation datasets. See
  Threat #2 above. Already cited.
- **Feng et al. 2025, CoSo: Counterfactual Soft RL for VLM Agents**
  (arXiv 2505.03792, ICML 2025) — NEUTRAL. Token-level counterfactual
  credit assignment for VLM-agent fine-tuning. Operates on textual action
  spaces (Android, card games), not continuous control. Already cited.
- **Peng et al. 2025, Counterfactual VLA: Self-Reflective VLA**
  (arXiv 2512.24426, Dec 2025) — NEUTRAL. Driving domain. VLA model
  counterfactually reasons about its own plan before executing; no
  simulator verification. Different domain.
- **Lin et al. 2025, HiF-VLA: Hindsight, Insight, Foresight VLA**
  (arXiv 2512.09928, CVPR 2026) — NEUTRAL. Three-perspective temporal
  reasoning in a VLA model on LIBERO/CALVIN; not about replay or RL,
  about VLA architecture.
- **Cao et al. 2026, "When Vision Overrides Language"** (arXiv 2602.17659)
  — NEUTRAL. Evaluates counterfactual failures in VLAs, introduces
  LIBERO-CF benchmark. Related-work mention only.

### 2. Verified Counterfactual / Simulator-in-the-Loop Robotics

- **Patel et al. 2025, IKER: Iterative Keypoint Reward (Real-to-Sim-to-Real)**
  (arXiv 2502.08643, ICRA 2025) — STRENGTH. VLM generates Python-coded
  reward functions; real scene reconstructed in sim, RL policy trained
  in sim, deployed to real. Sim-as-verifier is a precedent for our
  approach; cite as evidence that "VLM proposes / simulator verifies"
  is an emerging pattern.
- **Duan et al. 2025, AHA: VLM for Detecting and Reasoning over Failures
  in Robotic Manipulation** (arXiv 2410.00371, ICLR 2025) — STRENGTH.
  Fine-tuned VLM for failure *description* (not localization, not action
  proposal). AHA generates explanations; our system localizes *and*
  proposes corrective actions, then verifies them. AHA's integration
  with Eureka/PRoC3S is reward-refinement; ours is replay-prioritization
  and hindsight-relabeling. Strong precedent for "VLM understands robot
  failure" that our work extends. Already cited.
- **Chuck et al. 2025, NCII/HInt: Null Counterfactual Factor Interactions**
  (arXiv 2505.03172, ICLR 2025) — STRENGTH/NEUTRAL. Uses a *learned*
  dynamics model to ask "would this still happen if cause-object were
  removed?"; we use the *true* simulator. Closest precedent for
  counterfactual-verified hindsight. Already cited.
- **ImaginationPolicy (Chain of Moving Oriented Keypoints)**
  (arXiv 2509.20841, 2025) — NEUTRAL. End-to-end manipulation policy
  using oriented keypoints. Different approach; mention only.
- **SimplerEnv (CoRL 2024)** — NEUTRAL. Sim env for evaluating real-world
  manipulation policies. Tooling reference, not threat.

### 3. Foundation-Model Credit Assignment / VLM-as-Oracle

- **Khandoga, Yuan, Sankarapu 2026, "Beyond Uniform Credit: Causal Credit
  Assignment for Policy Optimization"** (arXiv 2602.09331) — STRENGTH.
  Masking reasoning spans in an LLM policy to identify causally-influential
  tokens. Already cited. Precedent for "exogenous credit-assignment
  oracle."
- **Mesnard et al. 2021, CCA-PG: Counterfactual Credit Assignment in
  Model-Free RL** (ICML 2021) — STRENGTH. The progenitor of "counterfactual
  credit assignment" in RL. Already cited.
- **Pignatelli et al. 2023, A Survey of Temporal Credit Assignment**
  (arXiv 2312.01072) — STRENGTH. The survey our taxonomy positions
  against. Already cited.
- **TraCeS, "Trajectory Based Credit Assignment From Sparse Safety
  Feedback"** (arXiv 2504.12557, 2025) — NEUTRAL. Learns a safety summary
  vector to attribute safety to timesteps. Adjacent: assigns blame within
  trajectory. Worth a single-line cite in related work.
- **VAGEN: World-Model Reasoning for Multi-Turn VLM Agents** (NeurIPS
  2025) — NEUTRAL. Bi-level GAE for turn-aware credit in VLM agents.
  LM-agent setting; not Fetch.
- **Wang et al. 2024, RL-VLM-F: RL from VLM Foundation Model Feedback**
  (arXiv 2402.03681, ICML 2024) — STRENGTH. VLM gives pairwise
  preferences over agent observations, learned-reward model. Earlier
  precedent for "VLM-as-judge for RL"; should be cited.
- **VLP, "Vision-Language Preference Learning for Embodied Manipulation"**
  (EMNLP 2025) — NEUTRAL. VLM-based preference RL for manipulation.
  Worth a cite in related work.
- **Preference VLM** (arXiv 2502.01616, 2025) — NEUTRAL. Scalable
  preference-based RL with VLMs.

### 4. Prioritized Experience Replay (2024-2026)

- **Schaul et al. 2016, Prioritized Experience Replay** (ICLR 2016) —
  STRENGTH. Already cited.
- **Pleiss, Sutter, Schiffer 2025, ReaPER: Reliability-Adjusted PER**
  (arXiv 2506.18482, June 2025) — NEUTRAL/STRENGTH. Argues raw TD-error
  is unreliable because both predicted and target Q's are approximations;
  introduces reliability estimate. Conceptually compatible with our
  semantic boost — both modify the proposal $\mu$ with extra information
  beyond $|\delta|$. Should be cited.
- **Yamani et al. 2025, RPE-PER: Reward-Prediction-Error PER**
  (arXiv 2501.18093, Jan 2025) — STRENGTH. Prioritization by RPE rather
  than TD-error. Same proposal-shaping move our paper makes; the
  reweighting target differs. Should be cited.
- **Krutsylo 2025, Non-Uniform Memory Sampling in Experience Replay**
  (arXiv 2502.11305, Feb 2025) — NEUTRAL. Continual-learning setting,
  shows random non-uniform beats uniform. Worth a brief cite to
  contextualize "any non-uniform proposal beats uniform."
- **Wang, Frans, Abbeel, Levine, Efros 2025, Prioritized Generative
  Replay** (arXiv 2410.18082, ICLR 2025) — STRENGTH. Densifies past
  experience with a conditional diffusion model + relevance function
  (curiosity, value). Same proposal-shaping framing as ours, with a
  learned generative model rather than a frozen VLM. Cite to contextualize
  our approach within the "PER + auxiliary signal" family.
- **Ma et al. 2026, Freshness-Aware PER** — see Threat #3.
- **Saglam et al. 2022, Actor Prioritized Experience Replay**
  (arXiv 2209.00532) — NEUTRAL. Worth a cite if discussing actor-side
  prioritization.

### 5. Hindsight / Goal-Conditioned RL (2024-2026)

- **Andrychowicz et al. 2017, HER** — STRENGTH. Already cited.
- **Özgür et al. 2025, Next-Future: Single-step relabeling**
  (arXiv 2504.11247) — STRENGTH. Already cited. Sample-efficiency
  improvement to HER.
- **Sayar et al. 2023, CEBP: Contact-Energy-Based Hindsight Prioritization**
  (arXiv 2312.02677) — STRENGTH. Already cited. Privileged-state
  prioritization heuristic; precedent for our heuristic Oracle v3.
- **Lei et al. 2025, GCHR: Goal-Conditioned Hindsight Regularization**
  (arXiv 2508.06108) — STRENGTH. Already cited. Hindsight regularization
  for sample efficiency.
- **Ding et al. 2026, AgentHER: HER for LLM Agent Trajectories**
  (arXiv 2603.21357) — NEUTRAL/STRENGTH. Adapts HER to LM agents on
  WebArena/ToolBench; uses multi-judge VLM verification (5.9%→2.3% noise
  reduction). Worth citing as evidence that "language-only counterfactuals
  need verification" is a recognized issue (their fix: multi-judge; ours:
  simulator).
- **CAIAC: Causal Action Influence Aware Counterfactual Data
  Augmentation** (arXiv 2405.18917) — STRENGTH. Counterfactual data
  augmentation for offline goal-conditioned RL on Franka-Kitchen and
  Fetch-Push/Pick&Lift. Same family of methods; cite.
- **MRHER: Model-based Relay HER** (arXiv 2306.16061) — NEUTRAL.
  Model-based hindsight relabeling for sequential manipulation.

### 6. World Model / LLM Model-Based RL

- **Wu, Yin, Feng, Long 2025, RLVR-World: Training World Models with RL**
  (arXiv 2505.13934, NeurIPS 2025) — STRENGTH. World-model training with
  verifiable rewards on robot manipulation. Adjacent: they train the
  model; we use the actual sim. Worth a cite to position our "zero
  modeling error" claim.
- **Yu et al. 2026, RWML: Reinforcement World Model Learning for
  LLM-based Agents** (arXiv 2602.05842, Feb 2026) — NEUTRAL. Action-
  conditioned world models for LM agents (ALFWorld/τ²Bench). Token-state
  setting; not directly threatening.
- **LED-WM: Language-Conditioned World Model** (NeurIPS 2025,
  arXiv 2511.22904) — NEUTRAL. Reads environment descriptions for policy
  generalization. Adjacent.
- **Cortex 2.0: Grounding World Models in Industrial Deployment**
  (arXiv 2604.20246, 2026) — NEUTRAL. Imagined rollouts scored before
  action execution. Worth a brief cite in related work — strong
  industrial precedent for our "verify before commit" mantra.

### 7. Test-Time Verification / Verifier Language Models

- **Zha et al. 2025, RL Tango: Reinforcing Generator and Verifier
  Together** (arXiv 2505.15034, NeurIPS 2025) — NEUTRAL. Trains LM
  generator + verifier jointly via RL. LM reasoning setting; precedent
  for "generator-verifier" decomposition that we instantiate as
  (VLM, simulator). Worth a cite.
- **"Trust but Verify!" Survey on Test-Time Scaling**
  (arXiv 2508.16665, 2025) — NEUTRAL. Taxonomy of verifier designs;
  citable as evidence that "verify before accepting" is established.
- **Executable Counterfactuals for LLMs** (ICLR 2026,
  OpenReview Lm46gJA0q8) — STRENGTH. Counterfactual reasoning improves
  with RL. Concept-level support for our "verify counterfactuals"
  direction.

### 8. NeurIPS / ICML / ICLR / RSS / CoRL 2025-2026 VLM-RL Papers

- **Sharony et al. 2026 (Threat #1)** — see above.
- **Wu et al. 2026, Large Reward Models (Threat #4)** — see above.
- **Duan et al. AHA (ICLR 2025)** — already cited.
- **Chuck et al. NCII (ICLR 2025)** — already cited.
- **Plan-Seq-Learn** (ICLR 2024, arXiv 2405.01534) — NEUTRAL. LLM-guided
  RL for long-horizon manipulation. Already discussed in related-work
  context.
- **PRIMT: Preference-based RL with hierarchical neuro-symbolic VLM/LLM
  fusion** (NeurIPS 2025) — NEUTRAL. Worth a cite.
- **VAGEN** (NeurIPS 2025) — see above.
- **SimpleVLA-RL** (ICLR 2026, arXiv 2509.09674) — NEUTRAL. Outcome-reward
  RL for VLA models on LIBERO. Different scale (VLA fine-tuning, not SAC
  on Fetch).
- **VLABench** (ICCV 2025) — NEUTRAL. Benchmark for language-conditioned
  manipulation. Mention as future-eval target.
- **RoboCerebra** (arXiv 2506.06677) — NEUTRAL. Benchmark for long-horizon
  reasoning + manipulation.
- **ReWiND: Language-Guided Rewards Without New Demos** — STRENGTH.
  Generalizable reward learning from language. Worth a cite.
- **ThinkAct: VLA Reasoning via Hindsight** (NeurIPS 2025) — NEUTRAL.
  VLA reasoning extension.
- **Praxis-VLM** (NeurIPS 2025) — NEUTRAL.
- **RT-Trajectory: Hindsight Trajectory Sketches** (DeepMind) — STRENGTH.
  Hindsight trajectory representations for policy conditioning. Worth a
  brief cite.

### 9. Failure Detection / Keyframe Localization

- **AHA** (Duan et al., already covered) — STRENGTH.
- **Self-Refining VLM for Robotic Failure Detection** (arXiv 2602.12405)
  — NEUTRAL/STRENGTH. Recent extension of failure-VLM line.
- **Code-as-Monitor: Constraint-Aware Visual Programming for Reactive
  Failure Detection** (CVPR 2025) — NEUTRAL. Runtime monitoring; cite.
- **StepEval: VLM-Based Subgoal Evaluation** (arXiv 2509.19524, CoRL
  2025) — NEUTRAL. Per-subgoal VLM evaluation. Worth a brief mention.

---

## Summary of action items for Phase 2/3

Citations to add to `refs.bib`:
1. ReaPER (Pleiss et al. 2025) — proposal-shaping precedent
2. RPE-PER (Yamani et al. 2025) — proposal-shaping precedent
3. Prioritized Generative Replay (Wang et al. ICLR 2025) — same family
4. CAIAC (Urpí et al. 2024) — counterfactual data augmentation for
   goal-conditioned manipulation, *uses our Fetch envs*
5. RL-VLM-F (Wang et al. ICML 2024) — VLM-as-judge precedent
6. RLVR-World (Wu et al. NeurIPS 2025) — world-model RL with verifiable
   rewards
7. AgentHER (Ding et al. 2026) — multi-judge verification for LM-agent
   hindsight (precedent for "verification before relabel")
8. Cortex 2.0 — industrial "imagine + verify" precedent
9. RL Tango (Zha et al. NeurIPS 2025) — generator-verifier framework
10. ReWiND — language-guided rewards
11. PRIMT (NeurIPS 2025) — preference-based RL with VLM/LLM fusion
12. Large Reward Models (Wu et al. 2026) — Threat #4; per-timestep VLM
    reward generation, directly compared in differentiation
13. IKER (Patel et al. ICRA 2025) — real-to-sim-to-real precedent for
    sim-as-verifier
14. StepEval — VLM-based subgoal evaluation

Sections to sharpen in Phase 3:
- **Abstract**: too dense; reframe around "VLM-as-posterior" + simulator
  verification as the two-sentence pitch.
- **Introduction contribution bullets**: differentiate Threat #4 (Large
  Reward Models) explicitly — "we modify replay, not reward, to keep TD
  target faithful to the unmodified sparse MDP."
- **Related Work, Sharony paragraph**: stop apologizing about "concurrent";
  assert the methodological distinction confidently and add the verified-CF
  mechanism as a second clean axis of difference.
- **Theory section "what this buys us"**: make a concrete *prediction*
  that our framing forces — e.g., "the multiplicative form is the *unique*
  proposal-shaping that preserves PER's IS-correction interpretation; any
  additive mixture (Sharony et al.) implicitly redefines the target objective."
- **Method 4.3 (Verified Counterfactual)**: position against Wu et al.
  2026's per-timestep VLM rewards — the key claim is "we modify proposal,
  not target; reward is recomputed against true sim sparse reward;
  miscalibration costs variance, not bias."
- **Limitations**: add explicit comparison to Sharony et al.'s benchmark
  diversity (MiniGrid/OGBench) as the next-step generalization study.

