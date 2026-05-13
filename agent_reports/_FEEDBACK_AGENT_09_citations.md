# Agent 09 — Citation Audit

Scope: `agent_reports/paper_cs285/main.tex` + `appendix.tex` against `refs.bib`.
Method: extracted all `\cite*{}` keys, diffed against bib entries, and
sanity-checked each citation's appropriateness for the claim it supports.

## Bibliography health

- Total entries in `refs.bib`: **38**
- Distinct entries cited in paper (main + appendix): **22**
- Orphan entries (in bib, not cited): **16**
- Broken citations (cited but missing from bib): **0** (clean BibTeX log,
  `main.blg` shows zero warnings)

## Must-add citations (claims without references)

These are claims a NeurIPS reviewer would flag as needing a citation.
Line numbers are from `main.tex` unless prefixed `app:`.

- **L40, L100, L322** — "Gymnasium-Robotics Fetch (Push / PickAndPlace / Slide)"
  is the central environment, named ~5 times, but never cited. Add
  `de_lazcano2024gymrobotics` (Gymnasium-Robotics) or fall back to
  Brockman et al. 2016 (OpenAI Gym). `plappert2018multigoal` is already
  cited but it documents the *prior* (gym/`-v1`) form; the `-v4` envs the
  paper actually runs are Gymnasium-Robotics.

- **L137-138, L288, L296** — repeated appeals to "MuJoCo dynamics"
  (the verifier's correctness argument is *load-bearing* on this) but
  MuJoCo is never cited. Add Todorov, Erez, Tassa 2012 (IROS) —
  `todorov2012mujoco`.

- **L244-245 (main) and app:72, app:97, app:237** — paper repeatedly
  calls its bias bound "V-trace-analogous" / "V-trace-style" / "V-trace
  specialization", but `espeholt2018impala` is an **orphan** in the bib.
  Cite it on first mention (L245).

- **app:72** "V-trace-style variance-reduction choice" and **app:237**
  "V-trace/Retrace specialization" — `munos2016retrace` is also an
  **orphan**. Cite at app:237 alongside V-trace.

- **L114, L118** — "Recent work uses foundation Vision-Language Models
  (VLMs) as 'oracles' inside the RL loop" — currently cited only with
  `rocamonde2024vlmreward,lee2025kagi` (reward shaping) and
  `sharony2026vlmrb` (replay). The bib has four highly relevant entries
  that are **orphaned** and should be folded in here for survey coverage:
  `venuto2024car` (Code-as-Reward), `wang2024rlvlmf` (RL-VLM-F),
  `chen2024promptable` (VLM promptable reps), `duan2025aha` (AHA — VLM
  for failure detection in manipulation — *especially* relevant given
  this paper's claim that the VLM localizes failure timesteps).

- **L168 (Related Work, relabel target)** — `zhao2018energy` (Energy-Based
  Hindsight Experience Prioritization, the canonical HER+priority paper)
  is in the bib but **orphaned**. EBP is the closest prior to Semantic
  PER's "non-uniform sampling of HER transitions" framing and was
  explicitly flagged in the agent-09 spec ("HER+EBP -> Zhao & Tresp
  2018"). This should be cited in the HER-extensions paragraph (L160-175)
  or at the multiplicative-form discussion.

- **L96-103, L106-111** — Temporal credit-assignment problem framing
  ("every standard TD-error signal decays exponentially") is built on
  but no foundational CA reference is given. `pignatelli2023survey`
  (Pignatelli et al. survey of TCA in deep RL) is in the bib and
  **orphaned** — a natural one-line cite here. `harutyunyan2019hca`
  (Hindsight Credit Assignment) and `mesnard2021cca` (Counterfactual
  Credit Assignment) are also orphans, and any one of them would fit
  L106-111 to legitimize the credit-assignment framing.

- **L130-139 (verified-CF intro)** — "asking instead for a corrective
  *action sequence* and executing it in a fork of the training simulator"
  — the "counterfactual data augmentation in sim" idea has direct prior
  art that the related-work paragraph misses:
  `urpi2024caiac` (CAIAC) is cited in §Related but **not at this
  positional claim**, and `arjonamedina2019rudder` (return decomposition)
  is an orphan that could anchor the "credit redistribution" framing.

- **L156 / L201** — "foundation-model-as-credit-oracle program of
  \citet{pignatelli2024calm}" — the citation is correct, but a stronger
  claim is that this paper *generalizes* CALM beyond text. Worth adding
  `mesnard2021cca` (counterfactual CA in model-free RL) since the
  paper's section heading is "Counterfactual Hindsight" yet does not
  cite the canonical "counterfactual credit assignment" paper.

- **L313 (and L139)** — "generator--verifier paradigm \citep{zha2025tango}"
  — `zha2025tango` is fine but it's an LM-reasoning paper. The broader
  "verifier-guided generation" lineage (e.g., Cobbe et al. 2021 GSM8K
  verifiers; Lightman et al. 2023 process reward models) is the actual
  origin of the paradigm in ML; Tango is a 2025 instance. A reviewer
  might call this anachronistic. *Not a must-fix, but flag.*

- **L329 (SAC config) and app:116** — "Adam, default $(\beta_1,\beta_2,
  \varepsilon)$" — Adam is uncited. Add Kingma & Ba 2015 (ICLR) at
  app:116 if you want to be belt-and-braces; typically not required.

- **L332, L389, L394, L397, app:188-193** — Statistical methodology
  invokes "Clopper--Pearson intervals" but uncited. Add Clopper & Pearson
  1934 (Biometrika). Minor; reviewers rarely demand it but neurips_2024
  style does benefit.

- **L332-334 / L387 / L394** — VLM model identifiers ("Claude Opus 4.7",
  "GPT-4o", "Sonnet 4.5") appear ~10 times across §Setup and §3.4.
  No technical-report citations. Adding OpenAI 2024 GPT-4o system card
  and Anthropic 2024-2026 model cards is *standard* for papers that
  benchmark closed VLMs. NeurIPS reviewers do request this.

## Wrong / questionable citations

- **L363-364**: "matching the PER@3M asymptote ($\sim$0.95,
  \citealp{plappert2018multigoal})". **Plappert et al. 2018 does not
  benchmark PER on Fetch** — they evaluate DDPG+HER (not SAC, not PER).
  Citing them for "PER@3M asymptote" is a category error. If the 3M PER
  number comes from the paper's own 36-run ablation (as suggested at
  L378 "drawn from a prior 36-run ablation suite"), the parenthetical
  should be removed or replaced with a self-reference. Currently it
  reads as if Plappert reported the number.

- **L337-340** (horizon caveat): "canonical Fetch+HER horizon of 4.75M
  \citep{plappert2018multigoal}". Plappert reports DDPG+HER at this
  budget; ok to cite, but the paper here uses SAC+HER, so a sentence
  qualifier is warranted (this is appropriate-with-caveat).

- **L139, L313**: `zha2025tango` cited twice for "generator--verifier
  paradigm" — as noted above, Tango is LM-reasoning and a 2025 paper.
  The paradigm itself is older. Not technically *wrong* but reads
  weakly. Consider adding (or replacing one mention with) a more
  established verifier-guided-generation reference.

## Missing obvious references (reviewer red-flags)

1. **Gymnasium-Robotics** (de Lazcano, Lopez, Gonzalez-Duque, et al.
   2024) — environment source for `FetchPush-v4` / `FetchPickAndPlace-v4`
   / `FetchSlide-v4`. *Must add.*
2. **MuJoCo** (Todorov, Erez, Tassa 2012, IROS) — physics simulator the
   verifier load-bearingly depends on. *Must add.*
3. **V-trace / IMPALA** (Espeholt 2018) — paper explicitly invokes
   "V-trace-analogous" three times. Bib entry already exists
   (orphaned). *Must cite.*
4. **Retrace** (Munos 2016) — paper appendix says "V-trace/Retrace
   specialization". Bib entry exists (orphaned). *Must cite.*
5. **Energy-Based HER** (Zhao & Tresp 2018) — closest prior to
   Semantic-PER's HER-priority multiplicative form. Bib entry exists
   (orphaned). *Should cite.*
6. **AHA** (Duan et al. 2025, ICLR) — VLM for detecting and reasoning
   over robot-manipulation failures. The paper's central VLM use case
   is *failure-frame localization*; AHA is the most direct prior on this
   exact task. Bib entry exists (`duan2025aha`, orphaned). *Should cite*
   in either §Related or §3.2.
7. **Counterfactual Credit Assignment** (Mesnard et al. 2021, ICML) —
   paper's headline contribution is literally called "Counterfactual
   Hindsight". Bib entry exists (`mesnard2021cca`, orphaned). Citing
   this would also fix the §Related-Work gap on "counterfactual
   relabeling" theory.
8. **Hindsight Credit Assignment** (Harutyunyan et al. 2019) — same
   §Related-Work gap; orphan in bib.
9. **OpenAI Gym / Brockman 2016** OR **Gymnasium / Towers 2023** — for
   the env framework.
10. **GPT-4o** technical report (OpenAI 2024) and **Claude Opus 4.7 /
    Sonnet 4.5** model cards (Anthropic 2024-2026) — three closed VLMs
    are the subject of a head-to-head sweep but none is technically
    cited.

Less critical but worth considering:
- **HER+MEP** (Maximum-Entropy Prioritization, Zhao et al. 2019) — the
  agent-09 spec specifically asked about HER variants. MEP is the other
  canonical HER+priority extension and is currently absent from the bib
  entirely.
- **DDPG** (Lillicrap et al. 2016) — only matters if the paper claims
  Plappert's results, which it does at L337-340 and L363-364. If those
  references stay, DDPG should be cited too.
- **PER+SAC** specifically — no canonical paper, but Wang et al. 2017
  "Sample Efficient Actor-Critic with Experience Replay" (ACER) is
  occasionally cited.

## Orphan bib entries (currently in `refs.bib`, not cited)

Listed with recommendation per entry:

| Key | Recommendation |
|---|---|
| `arjonamedina2019rudder` | **Cite** in §Related (credit redistribution lineage) or **cut** |
| `chen2024promptable` | **Cite** in §1 / §Related VLM-RL survey paragraph (L114) |
| `duan2025aha` | **Cite** (highly relevant — VLM failure reasoning for robot manipulation) |
| `espeholt2018impala` | **Cite** at L245 (paper says "V-trace-analogous") |
| `feng2025coso` | **Cite** in §Related (counterfactual + VLM-RL) or cut |
| `glossop2025cast` | **Cite** in §Related (counterfactual VLA) or cut |
| `harutyunyan2019hca` | **Cite** at L96-111 (TCA framing) or cut |
| `khandoga2026causalcredit` | **Cite** in §Related (causal CA lineage) or cut |
| `ma2026freshness` | **Cite** in §Related PER-2024-2026 paragraph (L173) or cut |
| `mesnard2021cca` | **Cite** (very relevant — paper claims "Counterfactual Hindsight") |
| `munos2016retrace` | **Cite** at app:237 ("V-trace/Retrace specialization") |
| `pignatelli2023survey` | **Cite** at §Intro CA framing or in §Related; otherwise cut |
| `venuto2024car` | **Cite** in VLM-as-reward sentence (L205) — sits alongside `rocamonde2024vlmreward` |
| `wang2024rlvlmf` | **Cite** in VLM-as-reward / VLM-feedback sentence (L205 or L114) |
| `wu2025rlvrworld` | **Cite** in §Related (RL + world models / verification) or cut |
| `zhao2018energy` | **Cite** at L168 (relabel-priority lineage, HER+EBP) |

**Strong recommendation: 11 of these 16 orphans should be promoted to
inline citations** (they will materially strengthen the paper). The
remaining 5 (e.g., `khandoga2026causalcredit`, `ma2026freshness`,
`wu2025rlvrworld`, `feng2025coso`, `glossop2025cast`) are weaker links
to the paper's narrative and can be cut to tighten the bib.

## Broken citations (cited, not in bib)

**None.** The BibTeX log is clean; every `\cite{...}` key resolves.

## Recommended additions to `refs.bib`

(Real references only — no fabrication.)

```bibtex
@inproceedings{todorov2012mujoco,
  title={{MuJoCo}: A physics engine for model-based control},
  author={Todorov, Emanuel and Erez, Tom and Tassa, Yuval},
  booktitle={IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)},
  year={2012},
  doi={10.1109/IROS.2012.6386109}
}

@misc{delazcano2024gymnasium,
  title={Gymnasium-Robotics: A Standard Interface for Robot-Learning Environments},
  author={de Lazcano, Rodrigo and Andreas, Kallinteris and Jet, Tai and Seungjae Ryan, Lee and Jordan, Terry},
  year={2024},
  howpublished={\url{https://robotics.farama.org/}},
  note={Software, Farama Foundation}
}

@misc{brockman2016openaigym,
  title={{OpenAI Gym}},
  author={Brockman, Greg and Cheung, Vicki and Pettersson, Ludwig and Schneider, Jonas and Schulman, John and Tang, Jie and Zaremba, Wojciech},
  year={2016},
  eprint={1606.01540},
  archivePrefix={arXiv}
}

@inproceedings{kingma2015adam,
  title={{Adam}: A Method for Stochastic Optimization},
  author={Kingma, Diederik P. and Ba, Jimmy},
  booktitle={International Conference on Learning Representations (ICLR)},
  year={2015}
}

@inproceedings{lillicrap2016ddpg,
  title={Continuous control with deep reinforcement learning},
  author={Lillicrap, Timothy P. and Hunt, Jonathan J. and Pritzel, Alexander and Heess, Nicolas and Erez, Tom and Tassa, Yuval and Silver, David and Wierstra, Daan},
  booktitle={International Conference on Learning Representations (ICLR)},
  year={2016}
}

@inproceedings{zhao2019mep,
  title={Maximum Entropy-Regularized Multi-Goal Reinforcement Learning},
  author={Zhao, Rui and Sun, Xudong and Tresp, Volker},
  booktitle={International Conference on Machine Learning (ICML)},
  year={2019}
}

@article{precup2000eligibility,
  title={Eligibility traces for off-policy policy evaluation},
  author={Precup, Doina and Sutton, Richard S. and Singh, Satinder},
  journal={ICML},
  year={2000}
}

@article{clopper1934confidence,
  title={The use of confidence or fiducial limits illustrated in the case of the binomial},
  author={Clopper, C. J. and Pearson, E. S.},
  journal={Biometrika},
  volume={26},
  number={4},
  pages={404--413},
  year={1934}
}

@techreport{openai2024gpt4o,
  title={{GPT-4o} System Card},
  author={{OpenAI}},
  year={2024},
  institution={OpenAI},
  url={https://openai.com/index/gpt-4o-system-card/}
}

@techreport{anthropic2024claude,
  title={Claude 3 Model Card},
  author={{Anthropic}},
  year={2024},
  institution={Anthropic},
  url={https://www-cdn.anthropic.com/de8ba9b01c9ab7cbabf5c33b80b7bbc618857627/Model_Card_Claude_3.pdf}
}
```

## Priority rollup

**Must-fix before submission (factual / load-bearing):**
1. L363-364 "PER@3M asymptote (\citealp{plappert2018multigoal})" — wrong
   attribution; Plappert reports DDPG+HER, not PER.
2. Add Gymnasium-Robotics citation (env source, 5+ usages).
3. Add MuJoCo citation (verifier correctness load-bearing on it).
4. Promote `espeholt2018impala` from orphan to inline at L245
   ("V-trace-analogous").
5. Promote `munos2016retrace` at app:237 ("V-trace/Retrace
   specialization").

**Should-fix (strengthens scholarship, low cost):**
6. Promote `zhao2018energy` (EBP) at L168.
7. Promote `duan2025aha` (AHA) in §Related — directly competes with the
   paper's failure-localization claim.
8. Promote `mesnard2021cca` — the paper's headline is literally
   "Counterfactual Hindsight" and counterfactual-CA is uncited.
9. Promote `venuto2024car`, `wang2024rlvlmf`, `chen2024promptable` into
   the VLM-RL survey sentences at L114 and L205.

**Nice-to-have:**
10. Cite VLM technical reports (OpenAI GPT-4o, Anthropic Claude).
11. Cut the truly tangential orphans (`khandoga2026causalcredit`,
    `ma2026freshness`, `wu2025rlvrworld`, `feng2025coso`,
    `glossop2025cast`) or weave them into one §Related sentence each.
12. Add Adam and Clopper-Pearson citations for completeness.
