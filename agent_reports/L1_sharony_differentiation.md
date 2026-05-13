# L1 — Sharony et al. (VLM-RB) vs. Our Work: Differentiation Brief

**Prepared by:** Agent L1 (literature analyst)
**Date:** 2026-05-11
**Subject paper:** Sharony, Jurgenson, Krupnik, Di Castro, Mannor — "VLM-Guided Experience Replay" — arXiv:2602.01915 (Feb 2026)
**Project page:** https://esharony.me/projects/vlm-rb/ (code listed as "coming soon" — no GitHub release found as of 2026-05-11)

---

## Paper Summary

**One-line:** VLM-RB uses a frozen pre-trained Perception-LM-class VLM to score short **sub-trajectory clips** for **goal-satisfaction** (success) and uses those scores in a **mixture-with-uniform** prioritized replay scheme, with an additional **multiplicative TD-boost** on the continuous-control variant.

**Setup at a glance:**

| Item | Value (verbatim where possible) |
|------|---------------------------------|
| VLM | Frozen "PerceptionLM" (Cho et al. 2025, "Open-Access Data and Models for Detailed Visual Understanding"); specific size not stated on project page |
| Calling pattern | **Asynchronous worker** writes priorities back to buffer; **~12% throughput overhead** |
| Input | **Sub-trajectory clips of L = 32 frames** (resolves "temporal ambiguity") |
| Prompt direction | **Success-oriented.** MiniGrid: *"Does this clip contain a clear instance of goal satisfaction anywhere in it?"* OGBench: *"Is there at least one clear instance of goal satisfaction in these frames? Look for contact + displacement..."* Yes/No answer format. |
| Output | Scalar probability `p_VLM_i` per clip |
| Mixture formula | `q_t(i) = λ_t · q^P(i) + (1 − λ_t) · q^U(i)` |
| Continuous TD-blend | `q^P(i) ∝ p_VLM_i · |δ_i|` (multiplicative product, no exponent) |
| λ schedule | Linear warm-up `λ_0 = 0 → λ_max = 0.5`; horizon length not stated |
| Base RL algos | Discrete: DQN, IQN. Continuous: SAC, TD3. |
| Benchmarks | **MiniGrid DoorKey** (8×8, 12×12, 16×16) and **OGBench Scene Tasks 3/4/5** (UR5e manipulation). **No Fetch / Gymnasium-Robotics.** |
| Baselines | UER (uniform), PER, AER, ERO, ReLo |
| Headline result | 11–52% higher success rates; 19–45% better sample efficiency vs. UER/PER |
| Ablations | "Modified Game" semantic-alignment: standard vs. misleading-sprite vs. abstract-texture renders — performance collapses to UER baseline under misleading/abstract visuals |
| Oracle / privileged baseline | **None** |
| Code | Project page says "Code (coming soon)"; no GitHub repo found under eladsharony or tomjur as of 2026-05-11 |
| Venue | No conference/workshop disclosed |

**Claimed contributions (from abstract):**
1. First to put VLMs *inside the replay buffer prioritization loop*.
2. Frozen, no-fine-tuning recipe (zero-shot semantic priors).
3. Empirical gains across discrete + continuous, two algo families each.

---

## Method Comparison Table — Theirs vs. Ours

| Dimension | Sharony et al. (VLM-RB) | Ours (proposed) |
|---|---|---|
| **Signal direction** | **Success / goal-satisfaction.** Prompt asks "is the goal satisfied?" Positive examples up-weighted. | **Failure-causing transitions.** Prompt asks the VLM to localize the *cause* of failure; transitions in a failure_window around the localized timestep are up-weighted. |
| **Granularity** | **Sub-trajectory clip (L = 32 frames).** Score is one scalar per clip; resolves "temporal ambiguity." | **Per-timestep window.** VLM identifies a *single failure-cause timestep*; surrounding window receives boost. Strictly finer than 32-frame clip scoring. |
| **Blending with TD-error** | **Mixture-with-uniform** at sampling time: `q_t = λ·q^P + (1−λ)·q^U`. For continuous control, additional `q^P ∝ p_VLM·|δ|` term. λ warm-ups 0 → 0.5. | **Pure multiplicative TD-weight:** `priority_i ← |δ_i| · failure_weight_i`. No mixture-with-uniform; failure_weight is bounded so non-failure transitions retain standard PER probability. |
| **VLM model** | Frozen **Perception-LM** (open-weights, Cho et al. 2025). Size unspecified; "1B" inferred. | **GPT-4o via API.** Frontier reasoning model; pays per call but no local GPU footprint. |
| **VLM cost model** | **Local frozen async worker** on training machine; ~12% throughput overhead. Inference compute amortized across episodes. | **API per-call** (paid). Trade-off: higher unit cost / call but stronger reasoning. We also provide a **heuristic Oracle** path (privileged sim state, zero VLM cost) to decouple "is the signal useful?" from "is the VLM accurate?" |
| **Observation type for VLM** | Renders video clips of agent's image observation (not clearly specified whether agent itself is image- or state-based). | Renders RGB from `mujoco_py` for VLM only; the SAC policy uses proprioceptive vector state. Cleanly separates VLM-as-evaluator from VLM-as-perception. |
| **Benchmark** | MiniGrid DoorKey + **OGBench** Scene 3/4/5. | **Gymnasium-Robotics Fetch** (Push, PickAndPlace, Slide) with SAC. No environment overlap with VLM-RB. |
| **Headroom / oracle analysis** | **None.** No privileged-state baseline; cannot answer "how much of the gap can a perfect failure-localizer close?" | **Yes.** Heuristic Oracle reads ground-truth object position; gives an upper-envelope curve so the VLM result can be reported as a fraction of "achievable" headroom. |
| **Direction of prioritization rationale** | "VLMs see semantic progress that TD-error misses." | "VLMs see *what went wrong* — a much rarer and more reward-sparse signal than progress. Failures are where credit assignment hurts most." |

---

## Concurrent / Prior Work on "VLM-in-Replay"

Per WebFetch of the project page, **VLM-RB explicitly claims novelty** in placing the VLM inside the replay buffer ("the replay buffer […] remains unexplored"). My corroborating searches turned up the following near-neighbors but **no direct prior work** combining VLMs with prioritization weights:

1. **VLM-Vac** (Mishra et al., arXiv:2409.14096, Sep 2024) — "Language-Guided Experience Replay" for smart vacuums. Uses GPT-4o + knowledge distillation; replay is for *continual learning* of an object classifier, not RL credit assignment. **Different problem** (perception KD), not RL prioritization. Sharony et al. do not cite it on the project page.
2. **ICAL — VLM Agents Generate Their Own Memories** (arXiv:2406.14596) — distills VLM experiences into "embodied programs of thought." Memory store, not replay-buffer prioritization. Not in Sharony's reference list per page extraction.
3. **Code-as-Reward** (Venuto et al., arXiv:2402.04764) — VLM generates *reward functions*, not replay priorities.
4. **Rocamonde et al. 2023** ("Vision-Language Models are Zero-Shot Reward Models") — cited by Sharony as related VLM-RL work; uses VLM as reward, not as replay scorer.
5. **Reliability-Adjusted PER (ReaPER, arXiv:2506.18482, 2025)** — pure TD-statistic, no VLM.
6. **Uncertainty-Prioritized ER (OpenReview, 2025)** — epistemic-uncertainty signal, no VLM.
7. **Prioritized Generative Replay (OpenReview 2025)** — generative augmentation, no VLM scorer.
8. **Freshness-Aware PER for LLM/VLM RL (arXiv:2604.16918)** — uses PER *for* training a VLM, opposite direction.

**Net:** Sharony et al. appear to be the first published VLM-as-replay-prioritizer. Our work is the *second*, but we attack a distinct dimension (failure direction, per-timestep window, oracle headroom) — see claims below.

---

## Our Differentiation Claims

Four claims our paper can credibly make, each with the evidence we'd need to ship.

### Claim 1 — Failure direction is fundamentally different from success direction (not a trivial sign-flip).

**Why it's different:** In sparse-reward Fetch, *successful* transitions are the rare-but-reachable signal; *failure-causing* transitions are the **structurally different** rare event — they are the bottleneck for credit assignment because TD-error decays exponentially with distance from terminal reward. A success-prioritizer (VLM-RB) re-weights the **terminal end** of good episodes; a failure-prioritizer re-weights the **decision point** that turned a good rollout into a bad one. These overlap at most at episode boundaries.

**Evidence needed:**
- Plot the distribution of "boosted" transition indices within failed episodes (ours) vs. successful episodes (theirs): should be disjoint in time.
- Direct A/B in our env: run VLM-RB-style "success boost on Fetch" as a baseline and show our failure-boost beats it. **Action: add this baseline this week.**
- Theoretical sketch: in tabular SAC, show failure-boost reduces the variance of policy gradient on the *near-bottleneck* state, whereas success-boost reduces variance on the *terminal* state — different bias-variance trade-offs.

### Claim 2 — Per-timestep granularity is strictly finer than 32-frame clip scoring and matters when failure causes are localized.

**Why it's different:** A 32-frame clip score cannot distinguish *which* of 32 actions caused failure. Sharony et al. acknowledge clip-level scoring is needed to resolve "temporal ambiguity," but in fact they're trading specificity for VLM context. We instead **localize** within the window: the VLM is prompted to return the timestep index of the causal action.

**Evidence needed:**
- Ablation: replace our per-timestep localization with clip-uniform boost (same window length L) — should under-perform our localized variant.
- A "localization accuracy" metric on the Oracle (compare VLM-predicted failure timestep to Oracle's ground-truth bottleneck index).
- Qualitative: 3–5 figures showing VLM correctly localized failure timestep where clip-level would smear.

### Claim 3 — Pure multiplicative TD-weight is theoretically cleaner than mixture-with-uniform.

**Why it's different:** Sharony's mixture `λ·q^P + (1−λ)·q^U` introduces a hyperparameter λ that must be warm-up-scheduled (0 → 0.5) — without λ-warmup the VLM signal corrupts early training. Our `p_i = |δ_i| · w_i` (with `w_i ∈ [1, w_max]` and `w_i = 1` outside the failure window) **degenerates gracefully to PER** when no failure is localized — no warm-up needed, no λ to tune.

**Evidence needed:**
- Sweep over Sharony's λ_max ∈ {0.25, 0.5, 0.75} on our Fetch envs to show mixture is brittle; show our multiplicative scheme is monotone in w_max.
- Show our method runs from step 1 (no warm-up) and matches the warmed-up mixture.
- Discuss: multiplicative preserves PER's importance-sampling correction trivially; mixture requires re-derivation.

### Claim 4 — Oracle headroom analysis quantifies "how much of the gap is VLM-attributable."

**Why it's different:** VLM-RB has no privileged baseline, so its 11–52% gains conflate two things: (i) is failure/success-prioritization a good *idea*? and (ii) is the VLM a good *implementation* of it? Our heuristic Oracle (ground-truth sim state) isolates (i) from (ii). We can report: "GPT-4o closes X% of the Oracle-vs-uniform gap" — a metric Sharony et al. cannot.

**Evidence needed:**
- Three curves on each Fetch task: uniform PER, ours-with-GPT-4o, ours-with-Oracle. Headroom % = (GPT − PER) / (Oracle − PER).
- If GPT-4o achieves >70% headroom, claim "VLM is sufficient." If <30%, claim "the framework has headroom; bigger/better VLMs would help."
- The Oracle also serves as an **honest upper bound** for reviewers — a strong methodological move VLM-RB did not make.

---

## Related Work Paragraph (≈155 words, citation-ready)

> Most closely related to our work is **VLM-RB (Sharony et al., 2026)**, which independently and concurrently proposes using a frozen vision-language model to prioritize replay-buffer experiences. The two works differ along four orthogonal axes. First, VLM-RB up-weights transitions that the VLM judges to contain **goal-satisfaction**, whereas we up-weight transitions that the VLM identifies as the **cause of failure** — a sparser and arguably more credit-assignment-relevant signal in long-horizon sparse-reward control. Second, VLM-RB scores **32-frame sub-trajectory clips** as atomic units; we localize a **single failure timestep** and apply a bounded window, yielding finer credit attribution. Third, VLM-RB linearly mixes a VLM-priority distribution with uniform sampling (`q = λq^P + (1−λ)q^U`), requiring a warm-up schedule, while we apply a **multiplicative weight to the PER priority** (`p_i ∝ |δ_i|·w_i`), which degenerates gracefully to PER absent a VLM signal. Fourth, we introduce a **privileged-state Oracle** that decouples the value of failure-prioritization-as-a-principle from VLM accuracy as an implementation, allowing us to report **VLM-attributable headroom** — an analysis absent in VLM-RB. We evaluate on **Gymnasium-Robotics Fetch (Push, PickAndPlace, Slide)** with SAC; VLM-RB evaluates on **MiniGrid and OGBench Scene** with DQN/IQN/SAC/TD3, so the empirical scopes are disjoint.

---

## Remaining Questions (open items / risks)

1. **VLM-RB code release.** Project page says "coming soon" — if released before our submission, we should re-verify the priority formula and λ schedule directly from code (the project page lists ~12% throughput, λ_max = 0.5, L = 32, but exact warm-up steps and prompt phrasing for OGBench Task 5 should be checked from source).
2. **PerceptionLM size.** Project page does not state 1B vs. 7B; the verbal "1B" in our notes is currently an unverified inference. Need to either (a) confirm from the PDF body (Section 4 / experimental setup) once we get a cleaner extraction, or (b) cite as "PerceptionLM (Cho et al. 2025), specific size not disclosed."
3. **Is our success-vs-failure framing watertight?** A reviewer could argue "boosting failure transitions and boosting success transitions are dual under reward sign-flipping." We need Claim-1 evidence (qualitative + direct A/B) to defuse this.
4. **VLM-RB's continuous-control TD-boost (`p^VLM · |δ|`) is actually multiplicative inside a mixture.** Our story "they're additive, we're multiplicative" is partially incorrect — they're *multiplicative within q^P* and *additive between q^P and q^U*. Sharpen the differentiation: ours is multiplicative on `|δ|` *without* a uniform mixture component.
5. **Sharony cites no prior "VLM-in-replay" work — but neither did the WebSearch.** Worth one more pass on Google Scholar / Semantic Scholar to ensure no Oct–Dec 2025 workshop paper scoops us further.
6. **Did VLM-RB run an "Oracle-on-OGBench" baseline in the appendix?** Project page says no, but the full appendix (likely 8–15 pages) was not extractable from the PDF. Worth one more WebFetch on the PDF appendix region if time permits — if they *do* have an oracle, Claim 4 weakens.
7. **Modified-Game ablation = a free idea for us.** Their "misleading sprite" + "abstract texture" ablation is a clean way to show the VLM is doing semantic work, not pixel-statistical. We could replicate cheaply on Fetch (e.g., color-permuted block) to strengthen our paper.
8. **No venue declared.** If they target NeurIPS 2026 (June deadline), we are likely on the same review pool — emphasize differentiation in our intro/abstract.

---

## Sources

- Sharony et al., "VLM-Guided Experience Replay," arXiv:2602.01915, Feb 2026 — https://arxiv.org/abs/2602.01915
- Project page: https://esharony.me/projects/vlm-rb/
- Tom Jurgenson page (no code link): https://tomjur.github.io/
- VLM-Vac (Mishra et al., 2024) — arXiv:2409.14096
- ICAL (memory distillation) — arXiv:2406.14596
- Code-as-Reward (Venuto et al.) — arXiv:2402.04764
- Reliability-Adjusted PER (2025) — arXiv:2506.18482
- Uncertainty-Prioritized ER — OpenReview 2025 (aAxzDb0nlO)
- Prioritized Generative Replay — OpenReview 2025 (5IkDAfabuo)
