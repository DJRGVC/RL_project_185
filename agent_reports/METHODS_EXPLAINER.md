# Replay-Buffer Methods, a Visual Explainer

Companion markdown to `methods_explainer.pdf`. Same text content; copy/paste
freely into the paper or slides.

---

## 1. The problem we are trying to solve

A robot tries to do a task. It mostly fails. We want it to learn from those
failures. To do that, every step of every attempt gets stuffed into a big
bucket called the **replay buffer**, and stochastic gradient descent pulls
samples out and uses them to improve the policy.

Two things make this hard:

1. **Sparse reward.** The robot sees a 0 for almost every transition and only
   finds out whether it succeeded at the very last step.
2. **Credit assignment.** Even when the episode does finish with a 1, we have
   no idea *which* of the 50 transitions in that episode actually deserves
   credit.

This is the credit assignment problem, and it is what every method below is
attacking.

---

## 2. The family tree

```
                    Replay Buffer
                         |
        +----------------+----------------+
        |                                 |
   ON-POLICY                        OFF-POLICY (us)
                                          |
                              +-----------+-----------+
                              |           |           |
                           Uniform     Priority     Hindsight
                              |       (TD-based)   (relabel goals)
                              |           |           |
                             UER        PER          HER
                                          |           |
                                    +-----+-----+     +------+
                                    |           |            |
                              Semantic PER    OUR         CF-HER
                              (failure-       PATH A         |
                               window VLM)                Verified-CF
                                                          (OUR PATH C)
```

**One-line intuition for each:**

- **UER** — sample any transition with equal probability. Boring but unbiased.
- **PER** — sample transitions where the agent is most *surprised* (high TD-error). "Learn from your mistakes."
- **HER** — on failed episodes, relabel the goal to be wherever the agent actually ended up. "Pretend we meant it."
- **Semantic PER** (Path A) — VLM points to the failure timestep; boost a window around it on top of PER.
- **CF-HER** — VLM imagines a goal G* the trajectory should have aimed at; relabel and recompute reward.
- **Verified-CF** (Path C) — same as CF-HER, but only accept the VLM's proposal if a sim rollout actually reaches G*.

---

## 3. Side-by-side comparison

| Method | What it does | When it helps | When it hurts | Key knob | Published example |
|---|---|---|---|---|---|
| **UER** | Sample transitions uniformly. | Always safe baseline; cheap; unbiased. | Wastes capacity on transitions the agent already understands. | (none) | Mnih et al. 2015 (DQN/Atari) |
| **PER** | Sample with prob proportional to \|TD\|^α. | Dense rewards or any setting where TD-error is informative. | Sparse-reward tasks: TD-error ~0 everywhere until goal. | α, β | Schaul et al. 2016 |
| **HER** | Relabel goal = achieved state on failed episodes; recompute reward. | Goal-conditioned manipulation with sparse rewards. | Envs without achieved_goal; can confuse policy if relabel goal is unreachable from earlier states. | k, strategy | Andrychowicz et al. 2017 (Fetch) |
| **Semantic PER** | Multiply PER priority by VLM-derived failure-window weight. | Long-horizon tasks where one transition causes failure. | Tasks where VLM can't identify the failure frame. | W, w_max | This project; Sharony et al. 2026 |
| **CF-HER** | VLM proposes counterfactual goal G*; relabel and recompute reward. | Cases where policy was "close" and VLM can verbalize the near-miss. | If trajectory never reached G*, reward stays 0 — no winning transition is actually created. | p_counterfactual | This project, Path C v1 |
| **Verified-CF** | VLM proposes a corrective action; sim rolled out; accept only if env reward fires. | Whenever the simulator is forkable; turns the VLM into a generator of provably-valid transitions. | Needs forkable sim. VLM still has to produce coherent actions. | rollout horizon, accept threshold | This project, Path C v2 (agent N1) |

---

## 4. Pseudocode — the easy three

### UER

```python
i = uniform_random(0, len(buffer))
transition = buffer[i]
```

### PER

```python
p_i = (abs(TD_i) + eps) ** alpha
i ~ Categorical(p_i / sum_j p_j)
w_i = ((N * p_i / sum_j p_j) ** -beta) / max_w   # IS correction
loss = w_i * (Q(s_i, a_i) - target_i) ** 2
```

### HER

```python
for tau in failed_episodes:
    for t in range(len(tau)):
        t_prime = random_future(t, len(tau))
        new_goal = tau[t_prime].achieved_goal
        new_reward = env.compute_reward(tau[t].achieved_goal, new_goal)
        buffer.push(tau[t] with desired_goal=new_goal, reward=new_reward)
```

**Mental model:** UER is the bucket. PER is a smarter way to pull from the
bucket. HER is a way to *add more useful things to the bucket*. PER and HER
are orthogonal — most modern manipulation papers do both.

---

## 5. The novel three

All three add a vision-language model (VLM). They differ in *what they ask
the VLM to produce*, and how much they trust the answer.

### Semantic PER — "which timestep was the mistake?"

Show the VLM keyframes from the episode and ask it to point to the **critical
failure timestep t\***. Build a soft window of radius W around t* and multiply
each transition's PER priority by that window. Transitions near the mistake
get sampled much more often.

### Counterfactual HER — "what should the goal have been?"

Instead of asking the VLM about timesteps, ask it about goals. On a failed
episode the VLM proposes an imagined goal G*; we relabel desired_goal = G*
and recompute reward, exactly like HER.

**Honest weakness:** if the trajectory never actually reached G* (within the
success tolerance), the recomputed reward is still 0. We did not create a
winning transition — we just changed which losing transition the agent is
told to learn from.

### Verified-CF — "prove your counterfactual works"

The fix for CF-HER's weakness. Ask the VLM for a **corrective action
sequence**, snapshot the simulator at the failure timestep, roll out the
VLM's action in a forked sim, and accept only if the env's own reward fires.
The accepted transitions are guaranteed physically valid and to carry a real
reward of 1.

**Key property:** teleport is structurally inexpressible as a 4-D action, so
the dominant CF-HER failure mode (VLM proposes "teleport the block to the
target") is eliminated by construction.

---

## 6. Why each method beats the previous

- **UER → PER:** uniform wastes compute on already-understood transitions. PER concentrates on high TD-error. *Still wrong:* sparse rewards make TD-error ~0 everywhere.
- **PER → HER:** PER can't extract signal from unobserved rewards. HER manufactures successful transitions via goal relabeling. *Still wrong:* HER picks a goal but not a timestep.
- **HER → Semantic PER:** in long-horizon tasks, one or two transitions cause the failure. VLM identifies them; we boost those. *Still wrong:* VLMs are noisy — GPT-4o under-performs a privileged-state heuristic in our ablation.
- **Semantic PER → CF-HER:** Semantic PER reweights but does not change *what* transitions say. CF-HER swaps the goal so the reward changes too. *Still wrong:* nothing forces the imagined goal to have been reached.
- **CF-HER → Verified-CF:** lying synthetic transitions poison the value function. Verified-CF gates VLM proposals through the simulator. *Still wrong:* needs a forkable sim.

---

## 7. Empirical findings (Fetch, 250k–1M steps)

- **Path A (Oracle):** Semantic PER with the heuristic Oracle beats vanilla PER (0.417 vs 0.383 success, mean over 3 seeds, 1M steps).
- **Path A (GPT-4o):** swap the Oracle for a VLM and it drops below PER (0.31 vs 0.38). The mechanism works; the VLM is the bottleneck.
- **Path C v1 (CF-HER):** does not beat plain HER at 250k steps. Teleport-collapse on Push dominates.
- **Path C v2 (Verified-CF):** 4/4 smoke pass on sim-grounded verification; full training run launching now.

**Headline lesson:** adding a VLM is not automatic. It helps when the VLM has
a clear job, is calibrated against ground truth, and its outputs are
structurally constrained (window weights, not arbitrary coordinates). It
hurts when you ask it to invent physical-world facts without verifying them.
Verified-CF is the principled response.
