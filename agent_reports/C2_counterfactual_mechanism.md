# C2 — Counterfactual VLM → SAC Mechanism Design

**Agent:** C2 (Path C theory)
**Branch:** `agent/c2-counterfactual-mechanism` (working inside isolated worktree on `main`)
**Deliverable:** Design + minimal prototype for *how* VLM counterfactuals
(produced by agent C1) feed into SAC training. **Not** a working
implementation; that's a 2–3 day follow-on if Daniel green-lights the path.

**TL;DR.** Of the three candidate mechanisms (counterfactual-HER relabeling,
dense reward shaping, exploration-head guidance), **counterfactual-HER
relabeling** is the strongest bet for a 5-day timeline. It is the most
theoretically grounded (subsumes standard HER as a special case), the
cheapest to implement (one new buffer class, ~250 LOC, drops into the
existing pipeline), the most novel relative to Sharony 2602.01915 (they
score *existing* transitions; we *generate* new ones from a VLM-imagined
target), and the most legible to a reviewer. The prototype stub lives at
`src/buffers/counterfactual_buffer.py` and is structured so
`p_counterfactual = 0` exactly recovers HER, giving us a clean ablation
axis. The chief risk is VLM 3D coordinate noise: if GPT-4o's
"corrective_position" is off by >5 cm, the synthetic reward stays sparse
and we've added zero-reward transitions toward a goal the policy never sees
again. Validation must include a confidence-thresholding ablation and a
"VLM vs oracle counterfactual" upper-bound experiment before any
full-scale Modal sweep.

---

## 1. Literature Survey

Path C lives at the intersection of three established areas. The relevant
prior work, briefly:

**Hindsight relabeling beyond achieved goals.** Standard HER (Andrychowicz
et al. 2017) relabels with goals from the *visited* trajectory. **Model-based
HER** (Yang et al. 2021) trains a forward dynamics model and rolls out
*virtual* future goals — relabels beyond what the agent actually achieved,
yielding measurably better sample efficiency. **DHER** (Fang et al. 2019)
relabels using achieved goals from *other* episodes. **Hindsight Task
Relabelling** (Packer et al. 2021) relabels meta-RL tasks with the achieved
*task* not the achieved goal. The throughline: HER is fundamentally a
counterfactual-reward generator, and the *choice of relabeling distribution*
determines which skills the policy generalizes toward. Our pitch — VLM as
the relabeling distribution — is a natural addition to this lineage. Whether
a VLM is a *better* distribution than a learned forward model is the open
empirical question.

**Language/VLM feedback into RL updates.** Three flavors appear in 2024–25
literature. (i) **VLM-as-reward**: Rocamonde et al. 2023 ("VLMs are
Zero-Shot Reward Models"), Baumli et al. 2023 ("VLMs as a Source of
Rewards"), VLAC 2025 (Vision-Language-Action-Critic, takes (s, s′, task)
and outputs a progress delta). These replace the environment reward with a
VLM-derived dense signal. (ii) **VLM-as-priority/critic**: Sharony et al.
2602.01915 (the paper we're differentiating against) scores existing
trajectories with a VLM and multiplies that into PER priorities. (iii)
**VLM-as-goal-generator**: GoalLadder 2025 prompts a VLM to generate
intermediate subgoals from a language instruction. The counterfactual
mechanism we propose is most adjacent to (iii) but novel in that the
generated goal is *retrospective* (per-episode hindsight) rather than
*prospective* (per-task curriculum).

**Counterfactual credit assignment.** Mesnard et al. 2020 ("Counterfactual
Credit Assignment in Model-Free RL") introduced the formal idea of using
counterfactual baselines to reduce variance in policy-gradient updates;
recent agentic-LLM work (HCAPO, CCPO, C3 — 2026 arXiv) generates
"what-if-this-turn-had-been-different" continuations with an LLM critic to
localize credit in long horizons. These methods are all *training-signal*
modifications, not *data-augmentation* modifications. Our HER-counterfactual
proposal is closer to data augmentation (add new transitions to the buffer),
which is simpler to integrate with SAC than a new gradient estimator.

**The Sharony gap.** Sharony's mechanism multiplies the priority of
*observed* transitions by a VLM score. The trajectory data itself is
unchanged. Our mechanism *creates synthetic transitions* with a
VLM-imagined goal that the agent never visited. These are orthogonal
operations on the buffer — one re-weights, one extends — which means a
direct comparison is well-defined, and a combined variant
(`semantic_per × counterfactual_HER`) is a natural future axis.

---

## 2. Three Candidates — Comparison

| Axis | (i) CF-HER relabeling | (ii) CF reward shaping | (iii) CF-guided exploration |
|---|---|---|---|
| **Mechanism** | Generate synthetic transitions with `desired_goal := g_cf` and recompute sparse reward | Add dense bonus `r += -‖achieved - g_cf‖` to transitions near frame K | Train an auxiliary policy head to imitate the corrective direction at frame K |
| **Theoretical grounding** | Direct extension of HER. Counterfactual reward is recomputed honestly via `env.compute_reward`. Off-policy correctness preserved. | Reward shaping is a hack — alters the MDP unless designed as a potential-based shaping (Ng et al. 1999). Risk of policy distortion if VLM is biased. | Aux-head distillation has weak theoretical guarantees w/ SAC. Easy to harm the main policy if the VLM target is wrong. |
| **Implementation cost** | **Low.** One new buffer class extending HERBuffer. Drops into `make_buffer()` factory. ~250 LOC. Existing train.py already calls `replay.finish_episode(compute_reward)`. | Medium. Need to detect "near frame K" at sample time, modify reward in the batch (or at push time, but that risks double-counting on relabels). Tangled with HER if used together. | **High.** Need an auxiliary network, separate loss, weight scheduling, action-space matching between VLM output and SAC action distribution. Risk of breaking SAC's actor update. |
| **Expected effect (best case)** | Synthetic transitions teach the policy "if you were trying for g_cf, this (s,a) reaches it" — expands the conditional success distribution beyond visited states. Same compounding benefit as HER. | Dense gradient for the K-window steps, faster credit assignment locally. But only where the VLM says — narrow effect. | Direct policy bias toward the corrective action — fastest behavioral change if it works. |
| **Expected effect (worst case)** | If VLM g_cf is bad: synthetic transition with sparse zero reward toward an unvisited goal. Wasted slot but not actively harmful. | If VLM is biased: persistent reward bias pulls the policy off-optimal. Hard to detect because reward looks fine. **Actively harmful.** | If VLM is wrong: aux-head pulls actor toward bad actions, can collapse the policy. **Actively harmful.** |
| **VLM error budget** | Tolerant. Mix counterfactual relabels with achieved-future at `p_cf = 0.25` → 75% of the relabeling budget is the proven HER signal. Confidence threshold drops bad CFs. | Brittle. The shaping is added at every sample of those transitions; a wrong g_cf permanently warps the value function. | Brittle. Aux loss is computed every gradient step; a wrong target keeps pushing. |
| **Cost per failed episode** | 1 VLM call (same as agent C1's localization call — can be combined). | 1 VLM call. | 1 VLM call + recurring aux-loss compute. |
| **Novelty vs Sharony 2602.01915** | **High.** Sharony re-weights real transitions; we *create new* transitions with VLM-imagined goals. Different operation on the buffer. | Medium. Sharony's effect is also on the loss landscape (via priorities); ours is on the per-transition reward. Mechanically related but distinct knob. | High. Sharony does not touch the actor; this does. But the novelty is *because* it's risky. |
| **Ablatability** | **Clean.** `p_counterfactual ∈ {0, 0.25, 0.5, 1.0}` parameterizes the dial; `p=0` ≡ vanilla HER. | Awkward. Bonus magnitude must be co-tuned with sparse-reward scale. | Awkward. Need to disentangle aux-head effect from policy regularization. |
| **5-day feasibility** | **Yes.** Can prototype Day 1, smoke test Day 2, full sweep Days 3–4, write-up Day 5. | Yes but with caveats — shaped reward needs careful design; risk of running broken experiments. | No. Realistically a 2-week effort to get right. |

---

## 3. Recommendation + Justification

**Pick (i): Counterfactual-HER relabeling.** Three reasons:

1. **It subsumes its own ablation.** Setting `p_counterfactual = 0` recovers
   vanilla HER bit-for-bit. We can run `{p=0, p=0.25, p=0.5}` in a single
   Modal sweep and the ablation tells us exactly how much signal the VLM
   counterfactual contributes — no parallel codepath, no confound.

2. **The failure mode is graceful.** If the VLM returns garbage 3D
   coordinates, we add a zero-reward transition toward an unvisited goal.
   That slot is wasted, but the next sample call is unbiased — SAC continues
   training on the same distribution as before. Compare to reward shaping,
   where a wrong g_cf pulls the value function in the wrong direction
   *forever* until that transition is overwritten.

3. **It cleanly differentiates from Sharony.** Sharony re-weights existing
   transitions; we generate new transitions from a VLM-imagined goal. These
   are orthogonal axes on the replay buffer. The story for the paper is
   concrete: "Sharony asks the VLM *which transitions matter*; we ask the
   VLM *what the goal should have been*." That's a one-sentence delta.

The candidate I'd second-place is (iii) exploration guidance — it has the
highest ceiling if the VLM is reliable — but the realistic VLM-coordinate
error from agent C1's results (TBD, but likely 5–15 cm at first cut) makes
it too risky for a 5-day window. Save for a paper extension.

The candidate I'd avoid is (ii) reward shaping — it's the most natural-looking
choice and the most fragile. Reward shaping with a noisy oracle is a known
footgun (e.g., reward hacking literature, Skalse et al. 2022).

---

## 4. Prototype

File: `src/buffers/counterfactual_buffer.py` (~250 LOC, stub only).

**Interface contract with agent C1.** The VLM side must provide a callable
with signature:

```python
def localize_counterfactual(
    achieved_goals: np.ndarray,    # (T, goal_dim)
    desired_goal:   np.ndarray,    # (goal_dim,)
    keyframes:      Optional[List[PIL.Image]] = None,
) -> Optional[List[Tuple[int, np.ndarray, float]]]:
    """Returns list of (frame_index, corrective_goal_xyz, confidence) or None."""
```

This is intentionally close to C1's existing `localize_failure` so the two
can share a single VLM call per episode.

**Key class.** `CounterfactualHERBuffer(HERBuffer)` overrides `finish_episode`:

- On a failed episode, optionally calls the VLM (rate-limited by
  `cf_call_interval`).
- For each transition's `k` synthetic relabels, draws each *individually*
  as either CF-goal (prob. `p_counterfactual`) or achieved-future
  (prob. `1 - p_counterfactual`).
- Counterfactual draws are causally constrained: a CF at frame K is only
  used as the relabel goal for transitions with `t ≤ K`.
- Low-confidence CFs (`< min_confidence`) are dropped; falls back to HER.
- Failures of the VLM call (None return, exception) degrade gracefully to
  HER for that episode.
- Diagnostics dict (`get_stats()`) tracks `vlm_calls`,
  `cf_relabels_used`, `achieved_relabels_used`, `low_conf_dropped` for W&B.

**Wiring.** Add to `src/buffers/__init__.py::make_buffer`:

```python
elif rtype in ("cf_her",):
    base = _make_base_or_per(cfg)
    return CounterfactualHERBuffer(
        underlying_buffer=base,
        counterfactual_fn=load_counterfactual_fn(cfg),  # C1's callback
        p_counterfactual=cfg["replay"].get("p_counterfactual", 0.25),
        min_confidence=cfg["replay"].get("min_confidence", 0.5),
        cf_call_interval=cfg["replay"].get("cf_call_interval", 1),
        k=cfg["replay"].get("her_k", 4),
    )
```

And one line in `train.py` (after the existing `replay.finish_episode(...)`
call) to pass `episode_success` and pre-rendered keyframes if available.

**Stub status.** The prototype imports cleanly under the project venv. It
does not invoke a real VLM (C1's `counterfactual_fn` is what plugs in
there). It is *not* wired into `make_buffer` or `train.py` — that's the
follow-on integration work, deliberately deferred so this report is a
decision artifact, not a half-built feature.

---

## 5. Validation Plan — 2-3 Critical Experiments

Before any full Modal sweep, run these in order:

**Exp. 1 — Oracle counterfactual upper bound.** Replace the VLM with a
hand-coded oracle that produces a "perfect" counterfactual: at the
ballistic-release frame of a failed FetchSlide episode, return
`desired_goal` itself as the corrective goal (or a midpoint, scaled).
Run 3 seeds × 50k steps on FetchPickAndPlace + FetchSlide with
`p_counterfactual = 0.5`. **Decision rule:** if this oracle variant
does not beat vanilla HER by ≥ 0.1 success rate, the *mechanism itself*
is too weak to justify further VLM work — abandon Path C. If it does,
we have a measured ceiling for the real-VLM run.

**Exp. 2 — Real VLM with confidence sweep.** With agent C1's VLM
counterfactual generator, sweep `min_confidence ∈ {0.0, 0.4, 0.7}` and
`p_counterfactual ∈ {0.0, 0.25, 0.5}`. `p=0` is the HER baseline.
3 seeds × 100k steps on FetchPickAndPlace. **Decision rule:** the
`(p=0.25, conf=0.4)` cell needs to non-trivially exceed `(p=0, *)`,
*and* the gap to Exp. 1's oracle should be < 0.15 absolute. Larger gap
means the VLM is the bottleneck; report that as a contribution
("CF-HER is mechanism-correct but bottlenecked by VLM 3D grounding").

**Exp. 3 — Failure-mode characterization.** On the same runs as Exp. 2,
log per-episode: (a) the distance ‖g_cf − desired_goal‖, (b) the
fraction of synthetic transitions with reward = 0 vs reward > -1,
(c) the actor entropy on the CF-relabeled batch indices. This tells us
*why* the variant succeeds or fails: if (b) is near zero, the VLM is
proposing infeasible goals; if (c) is collapsing, the VLM is biasing
the actor toward an unhelpful action distribution.

If Exp. 1 fails outright we abandon. If Exp. 1 passes but Exp. 2 ties HER,
we still have a contribution (mechanism + ceiling + failure mode).

---

## 6. Risks

- **VLM 3D coordinate noise.** Most serious. GPT-4o's spatial grounding in
  pixel coords → world coords is the hard part for agent C1. If error is
  > 5 cm typically, the sparse Fetch reward (success at < 5 cm) means
  almost every CF-relabel gets reward 0 and is functionally equivalent to
  pushing a zero-reward transition with a random goal. Mitigation: Exp. 1
  oracle gives us a measured upper bound; the confidence threshold drops
  the worst VLM outputs; the `p_counterfactual = 0.25` mixing limits
  exposure.

- **Scope creep into agent C1's territory.** The boundary is clean: C1
  owns the callable; C2 owns the buffer. If the callable is delayed, this
  buffer can be tested with a *mock* counterfactual function (e.g., return
  the achieved goal at frame K+5 as a "fake CF") to verify the data flow.

- **Reward-recomputation correctness.** `env.unwrapped.compute_reward`
  takes `(achieved, desired, info)`. We feed it
  `(tr["next_achieved_goal"], g_cf, {})` — same as the existing HER
  buffer does. Validated by code-reading not by a runtime test in this
  report; the existing HER buffer is the reference.

- **VLM call cost.** 1 call per failed episode × ~200 failed episodes per
  run × 12 runs (sweep) ≈ 2,400 GPT-4o calls. At ~$0.03/call (small
  prompt + 3-4 images): ~$75 per full sweep. Affordable. Mitigation:
  `cf_call_interval > 1` halves cost trivially.

- **The Sharony comparison may be hard to make crisp.** If we run
  `semantic_per × cf_her` as the headline variant, the paper needs to
  argue that *both* axes matter independently. The ablation grid is
  `{vanilla, sharony-style, cf-her, both}` — 4 cells × 3 seeds × 3 envs
  = 36 runs, identical scale to the existing ablation. Tractable.

- **What if HER + PER already saturates Fetch.** If agent A1's HER
  baselines hit ~95% on all three envs, there's no room for CF-HER to
  show improvement. Mitigation: pivot to harder tasks
  (FetchPickAndPlaceDense, MetaWorld) or report the ceiling effect
  honestly.

---

## Appendix A — Files Created / Modified

- **Created:** `src/buffers/counterfactual_buffer.py` (250 LOC stub,
  imports cleanly under project venv).
- **Not modified:** `src/buffers/__init__.py`, `train.py`, configs/.
  Wiring is deferred to integration phase (Day 2 of the 5-day plan
  if Path C is green-lit).

## Appendix B — Open Questions for Daniel

1. Do we run Exp. 1 (oracle counterfactual) before C1 finishes the real
   VLM side? It's the cheapest way to kill Path C early if the
   mechanism itself is too weak. I recommend yes — it's a half-day of
   work and decides whether the next 4 days go into this or back into
   Path A.
2. Should the CF mechanism be exposed as a flag *on top of* HER + Semantic
   PER (so the combined variant is testable), or as a standalone replay
   type? Recommend the former: it's strictly more general and the
   ablation grid is cleaner.
3. Is the "VLM imagines goals" framing the headline contribution or a
   subcomponent? My read: it's the headline only if Exp. 2 beats vanilla
   HER. Otherwise it's a "mechanism characterization + negative result"
   subsection.
