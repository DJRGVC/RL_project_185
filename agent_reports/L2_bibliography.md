# L2 Bibliography Report — RL_project_185
**Author:** Agent L2 (research bibliography builder)
**Date:** 2026-05-11
**Deadline:** 20:50 PDT

---

## Path C Scoop Check — TOP-LINE FINDING

**No direct scoop found.** After targeted searches for "VLM counterfactual RL", "VLM hindsight relabeling", "VLM imagined goals RL", and "VLM-guided prioritized experience replay for manipulation", **no published paper** combines (a) a VLM critic, (b) failure-localized counterfactual relabeling, and (c) prioritized experience replay for sparse-reward manipulation in the exact way Path C proposes.

The closest neighbors — important to distinguish ourselves from in Related Work — are:

1. **Sharony et al. 2026 — "VLM-Guided Experience Replay" (arXiv 2602.01915):** Uses a frozen VLM to prioritize replay sub-trajectories. Closest competitor, but it scores trajectories rather than localizing failures and generating counterfactual goals. (See L1's deep-dive for details.)
2. **CAST (Glossop, Levine et al., arXiv 2508.13446):** Uses VLMs to generate counterfactual *language labels* for navigation VLA training — supervised imitation, NOT RL/PER, NOT manipulation.
3. **CoSo (Feng et al., arXiv 2505.03792, ICML 2025):** Counterfactual reasoning to identify causally-influential *tokens* in VLM agent outputs — not goals, not robotic manipulation.
4. **AgentHER (Ding 2026, arXiv 2603.21357):** HER for LLM agents on WebArena/ToolBench. LLM-guided relabeling but text-only agents.
5. **AHA (Duan et al., arXiv 2410.00371, ICLR 2025):** VLM failure detection/reasoning for manipulation — but feeds into reward-shaping / task planning, NOT into PER counterfactual relabeling.
6. **HInt / NCII (Chuck et al., arXiv 2505.03172, ICLR 2025):** Counterfactual *object-interaction* nulling for HER relabeling — uses a learned dynamics model, not a VLM, and uses interactions not failure localization.

**Path C remains well-positioned.** The combination of (i) VLM failure-localized counterfactual reasoning + (ii) prioritized experience replay + (iii) manipulation control with sparse rewards is novel relative to this corpus. Our differentiation story to write: "Sharony scores; CAST labels; CoSo masks tokens; AgentHER does text. Path C is the first to use a VLM as a *counterfactual oracle for failure localization in physical manipulation* and feed that into PER."

---

## Thread 1: Credit Assignment in Deep RL

### 1.1 Pignatelli et al. 2023 — Temporal Credit Assignment Survey (MUST CITE)
```bibtex
@article{pignatelli2023temporalcreditassignment,
  title={A Survey of Temporal Credit Assignment in Deep Reinforcement Learning},
  author={Pignatelli, Eduardo and Ferret, Johan and Geist, Matthieu and Mesnard, Thomas and van Hasselt, Hado and Pietquin, Olivier and Toni, Laura},
  journal={arXiv preprint arXiv:2312.01072},
  year={2023}
}
```
**Summary.** Comprehensive survey unifying credit-assignment methods under "learning the influence of an action over an outcome." Categorizes delayed feedback, transpositions, and insufficient action influence; proposes diagnostic protocols. Several authors are DeepMind affiliates (van Hasselt, Geist, Mesnard, Pietquin) — the brief's "DeepMind survey" attribution is essentially correct.
**Relevance.** Anchor citation for our Path C framing: counterfactual reasoning over failures is itself a credit-assignment mechanism. We frame VLM-counterfactual replay as a sample-level credit-assignment signal.
**Tag.** `credit-assignment`

### 1.2 Khandoga et al. 2026 — Causal Credit Assignment for Policy Optimization
```bibtex
@article{khandoga2026causalcreditassignment,
  title={Beyond Uniform Credit: Causal Credit Assignment for Policy Optimization},
  author={Khandoga, Mykola and Yuan, Rui and Sankarapu, Vinay Kumar},
  journal={arXiv preprint arXiv:2602.09331},
  year={2026}
}
```
**Summary.** Proposes counterfactual importance weighting for LLM RL: masks reasoning spans and measures probability drop to identify causally-influential tokens. No auxiliary model needed; importance estimated from the policy itself. Validated on GSM8K (Qwen, Llama).
**Relevance.** Provides the conceptual template we adapt: "mask the trajectory segment, see what would have happened" — except we use a VLM to do the masking-and-imagining in pixel/state space rather than token space.
**Tag.** `credit-assignment`

### 1.3 Mesnard et al. 2021 — Counterfactual Credit Assignment (foundational)
```bibtex
@inproceedings{mesnard2021counterfactual,
  title={Counterfactual Credit Assignment in Model-Free Reinforcement Learning},
  author={Mesnard, Thomas and Weber, Th\'eophane and Viola, Fabio and Thakoor, Shantanu and Saade, Alaa and Harutyunyan, Anna and Dabney, Will and Stepleton, Tom and Heess, Nicolas and Guez, Arthur and Toth, Eszter Vértes and Lakshminarayanan, Karthikeyan and Hassabis, Demis and Munos, Rémi},
  booktitle={ICML},
  year={2021}
}
```
**Summary.** Introduces CCA-PG and "future-conditional baselines" to subtract counterfactual contributions of future randomness from policy-gradient credit. Establishes the formal counterfactual-RL credit-assignment frame in model-free deep RL.
**Relevance.** Older but foundational — cite as the formal precursor for our "VLM as counterfactual oracle" framing.
**Tag.** `credit-assignment`

### 1.4 Arjona-Medina et al. 2019 — RUDDER (foundational)
```bibtex
@inproceedings{arjonamedina2019rudder,
  title={RUDDER: Return Decomposition for Delayed Rewards},
  author={Arjona-Medina, Jose A. and Gillhofer, Michael and Widrich, Michael and Unterthiner, Thomas and Brandstetter, Johannes and Hochreiter, Sepp},
  booktitle={NeurIPS},
  year={2019}
}
```
**Summary.** Return decomposition via LSTM contribution analysis transforms delayed-reward RL into regression and uses layer-wise relevance/integrated gradients to redistribute reward to causally-relevant steps. Exponential speedups on long-delay tasks.
**Relevance.** Core lineage for "redistribute credit to the moment that actually caused the failure" — the explicit conceptual ancestor for failure-localized PER weighting.
**Tag.** `credit-assignment`

---

## Thread 2: HER Variants + Goal-Conditioned RL SOTA

### 2.1 Özgür et al. 2025 — Next-Future (MUST CITE)
```bibtex
@article{ozgur2025nextfuture,
  title={Next-Future: Sample-Efficient Policy Learning for Robotic-Arm Tasks},
  author={\"{O}zg\"{u}r, Fikrican and Zurbr\"{u}gg, Ren\'e and Kumar, Suryansh},
  journal={arXiv preprint arXiv:2504.11247},
  year={2025}
}
```
**Summary.** Replaces HER's heuristic future-strategy with a principled single-step-transition reward formulation. Demonstrates sample-efficiency gains on 7/8 manipulation tasks and higher success on 6/8, with real-robot validation.
**Relevance.** A 2025 HER-replacement baseline that we MUST compare against. Their critique of HER's heuristic is the same gap Path C addresses, but they fix it via a single-step reward rule; we fix it via VLM-localized counterfactual goals.
**Tag.** `her-sota`

### 2.2 Sayar et al. 2023 — Contact Energy Hindsight (MUST CITE)
```bibtex
@article{sayar2023contactenergy,
  title={Contact Energy Based Hindsight Experience Prioritization},
  author={Sayar, Erdi and Bing, Zhenshan and D'Eramo, Carlo and Oguz, Ozgur S. and Knoll, Alois},
  journal={arXiv preprint arXiv:2312.02677},
  year={2023}
}
```
**Summary.** CEBP prioritizes replay samples using gripper-contact energy and object displacement — favoring contact-rich transitions which carry more learning signal. Real-robot Franka deployment included.
**Relevance.** Direct prior art for prioritized HER on manipulation. Argues prioritization should follow *information content* of transitions; we argue it should follow *causal failure-localization* — same family, different oracle (physical sensors vs. VLM).
**Tag.** `her-sota`

### 2.3 Chuck et al. 2025 — HInt / NCII (ICLR 2025)
```bibtex
@inproceedings{chuck2025nullcounterfactual,
  title={Null Counterfactual Factor Interactions for Goal-Conditioned Reinforcement Learning},
  author={Chuck, Caleb and Feng, Fan and Qi, Carl and Shi, Chang and Agarwal, Siddhant and Zhang, Amy and Niekum, Scott},
  booktitle={ICLR},
  year={2025}
}
```
**Summary.** Hindsight Relabeling using Interactions (HInt) combined with Null Counterfactual Interaction Inference (NCII). Defines interaction via the counterfactual "would the target object's dynamics change if the cause object were removed?" Achieves up to 4x sample-efficiency improvement.
**Relevance.** This is the closest published work to Path C in spirit — uses *counterfactual reasoning to drive hindsight relabeling*. Key differentiator: they use a learned dynamics model and per-object null counterfactuals; we use a VLM as the counterfactual oracle and operate on failure localization instead of object interactions.
**Tag.** `her-sota` / `credit-assignment`

### 2.4 GCHR — Lei et al. 2025 (Goal-Conditioned Hindsight Regularization)
```bibtex
@article{lei2025gchr,
  title={GCHR: Goal-Conditioned Hindsight Regularization for Sample-Efficient Reinforcement Learning},
  author={Lei, Xing and Yang, Wenyan and Ke, Kaiqiang and Yang, Shentao and Zhang, Xuetao and Pajarinen, Joni and Wang, Donglin},
  journal={arXiv preprint arXiv:2508.06108},
  year={2025}
}
```
**Summary.** Argues trajectory relabeling alone fails to fully exploit experience in off-policy GCRL. Adds Hindsight Goal-conditioned Regularization (HGR) and Hindsight Self-imitation Regularization (HSR) on top of HER. Improves over HER on navigation and manipulation benchmarks.
**Relevance.** Recent (Aug 2025) HER-extension to compare/cite as alternative to our approach. Same diagnosis ("HER under-uses experience"), different prescription.
**Tag.** `her-sota`

### 2.5 D-SPEAR — Zhang & Mason 2026 (Dual-Stream PER for Manipulation)
```bibtex
@inproceedings{zhang2026dspear,
  title={D-SPEAR: Dual-Stream Prioritized Experience Adaptive Replay for Stable Reinforcement Learning in Robotic Manipulation},
  author={Zhang, Yu and Mason, Karl},
  booktitle={IEEE ICCRE},
  year={2026},
  note={arXiv:2603.27346}
}
```
**Summary.** Decouples actor and critic sampling — critic uses prioritized replay for efficient value learning, actor uses low-error transitions for policy stability. Adaptive switching between uniform/prioritized via TD-error variation, plus Huber-based critic objective. Tested on robosuite Block-Lifting, Door-Opening.
**Relevance.** State-of-the-art PER variant for manipulation in 2026. Direct comparison target for the "PER baseline" in our ablation table.
**Tag.** `her-sota`

### 2.6 Act2Goal — Zhou et al. 2025 (World-Model + Hindsight Relabeling)
```bibtex
@article{zhou2025act2goal,
  title={Act2Goal: From World Model To General Goal-conditioned Policy},
  author={Zhou, Pengfei and Chen, Liliang and Chen, Shengcong and Chen, Di and Zhao, Wenzhi and Jin, Rongjun and Ren, Guanghui and Luo, Jianlan},
  journal={arXiv preprint arXiv:2512.23541},
  year={2025}
}
```
**Summary.** Integrates a goal-conditioned visual world model with multi-scale temporal hashing. Reward-free online adaptation via hindsight goal relabeling and LoRA fine-tuning. Improves real-robot success from 30%→90% on OOD tasks within minutes of interaction.
**Relevance.** December 2025 SOTA for goal-conditioned policies with on-the-fly HER-style adaptation. Demonstrates HER lineage is still actively winning in real-robot manipulation — important for our baseline-competitiveness narrative.
**Tag.** `her-sota`

### 2.7 Prioritized Generative Replay — Wang et al. 2024
```bibtex
@article{wang2024prioritizedgenerative,
  title={Prioritized Generative Replay},
  author={Wang, Renhao and Frans, Kevin and Abbeel, Pieter and Levine, Sergey and Efros, Alexei A.},
  journal={arXiv preprint arXiv:2410.18082},
  year={2024}
}
```
**Summary.** Replaces uniform replay with a conditional diffusion model that generates synthetic experience guided by relevance functions (curiosity or value). Reduces overfitting and enables higher UTD ratios.
**Relevance.** Cite as alternative replay-augmentation philosophy (generate-from-prior vs. relabel-with-VLM). Our work and theirs both attack "the buffer is the bottleneck"; we choose semantic relabeling, they choose generative densification.
**Tag.** `her-sota` / `vlm-in-rl` (borderline)

### 2.8 HER — Andrychowicz et al. 2017 (foundational baseline)
```bibtex
@inproceedings{andrychowicz2017her,
  title={Hindsight Experience Replay},
  author={Andrychowicz, Marcin and Wolski, Filip and Ray, Alex and Schneider, Jonas and Fong, Rachel and Welinder, Peter and McGrew, Bob and Tobin, Josh and Abbeel, Pieter and Zaremba, Wojciech},
  booktitle={NeurIPS},
  year={2017}
}
```
**Summary.** Original HER. Relabels failed trajectories with achieved states as goals so sparse-reward off-policy RL can learn from every episode.
**Relevance.** The reference point our entire bibliography orbits.
**Tag.** `her-sota`

---

## Thread 3: VLM / LLM / Foundation Models in RL

### 3.1 Sharony et al. 2026 — VLM-Guided Experience Replay (MUST CITE — brief; see L1 deep-dive)
```bibtex
@article{sharony2026vlmreplay,
  title={VLM-Guided Experience Replay},
  author={Sharony, Elad and Jurgenson, Tom and Krupnik, Orr and Di Castro, Dotan and Mannor, Shie},
  journal={arXiv preprint arXiv:2602.01915},
  year={2026}
}
```
**Summary.** Frozen pre-trained VLM as evaluator that ranks promising sub-trajectories for prioritized replay across gaming and robotics. 11-52% higher success, 19-45% sample-efficiency improvement.
**Relevance.** Closest published work to Path C and our most important comparison/differentiation. See L1's report for the deep-dive — Path C differs in (a) failure localization rather than success scoring and (b) counterfactual goal generation rather than trajectory ranking.
**Tag.** `vlm-in-rl`

### 3.2 Wu et al. 2026 — Large Reward Models (MUST CITE)
```bibtex
@article{wu2026largerewardmodels,
  title={Large Reward Models: Generalizable Online Robot Reward Generation with Vision-Language Models},
  author={Wu, Yanru and Yuan, Weiduo and Qi, Ang and Guizilini, Vitor and Mao, Jiageng and Wang, Yue},
  journal={arXiv preprint arXiv:2603.16065},
  year={2026}
}
```
**Summary.** Adapts foundation VLMs into online reward generators producing process, completion, and temporal-contrastive rewards from current visual observations. Trained on real trajectories + human-object interactions + simulation. Zero-shot to new envs; meaningful gains within 30 RL iterations.
**Relevance.** State-of-the-art VLM-as-reward in 2026. Cite as the "reward-model" axis of VLM-in-RL; Path C lives on the orthogonal "replay/credit" axis.
**Tag.** `vlm-in-rl`

### 3.3 Lee et al. 2025 — KAGI (MUST CITE)
```bibtex
@inproceedings{lee2025kagi,
  title={Affordance-Guided Reinforcement Learning via Visual Prompting},
  author={Lee, Olivia Y. and Xie, Annie and Fang, Kuan and Pertsch, Karl and Finn, Chelsea},
  booktitle={IROS},
  year={2025},
  note={arXiv:2407.10341}
}
```
**Summary.** KAGI uses VLM affordance keypoints to produce dense rewards for autonomous RL in real-world manipulation. Achieves task completion in 30K online steps with robustness to reduced training data.
**Relevance.** Chelsea Finn's group's flagship VLM-for-manipulation-RL paper. Cite as the affordance-guided reward-shaping branch of VLM-in-RL; Path C is replay-side rather than reward-side.
**Tag.** `vlm-in-rl`

### 3.4 Rocamonde et al. 2024 — VLMs as Zero-Shot Reward Models (ICLR 2024)
```bibtex
@inproceedings{rocamonde2024vlmrewardmodels,
  title={Vision-Language Models are Zero-Shot Reward Models for Reinforcement Learning},
  author={Rocamonde, Juan and Montesinos, Victoriano and Nava, Elvis and Perez, Ethan and Lindner, David},
  booktitle={ICLR},
  year={2024},
  note={arXiv:2310.12921}
}
```
**Summary.** CLIP-style VLMs deliver zero-shot reward signals from natural-language task specifications. MuJoCo humanoid learns kneel/splits/lotus from single-sentence prompts. Scale of VLM matters; failure modes track VLM spatial-reasoning limits.
**Relevance.** Foundational citation for "VLMs are reward models" — establishes the conceptual baseline upon which KAGI, MARVL, VLAC, and LRM all build.
**Tag.** `vlm-in-rl`

### 3.5 Venuto et al. 2024 — Code as Reward (VLM-CaR)
```bibtex
@inproceedings{venuto2024codeasreward,
  title={Code as Reward: Empowering Reinforcement Learning with VLMs},
  author={Venuto, David and Islam, Sami Nur and Klissarov, Martin and Precup, Doina and Yang, Sherry and Anand, Ankit},
  booktitle={ICML},
  year={2024},
  note={arXiv:2402.04764}
}
```
**Summary.** VLM-CaR generates dense reward *functions* via code generation rather than querying VLMs at every step, slashing inference cost while preserving task-decomposition benefits. Works in discrete and continuous control.
**Relevance.** Cite as evidence that VLM-in-RL is computationally viable when designed thoughtfully — supports our deployment claim that VLM-counterfactual queries can be batched or amortized.
**Tag.** `vlm-in-rl`

### 3.6 Chen et al. 2024 — VLM Promptable Representations
```bibtex
@article{chen2024promptablerepresentations,
  title={Vision-Language Models Provide Promptable Representations for Reinforcement Learning},
  author={Chen, William and Mees, Oier and Kumar, Aviral and Levine, Sergey},
  journal={arXiv preprint arXiv:2402.02651},
  year={2024}
}
```
**Summary.** Uses VLM embeddings (with task-context prompts and chain-of-thought) as features for RL policies. Outperforms generic image embeddings on Minecraft and Habitat navigation; CoT improves novel-scene generalization 1.5x.
**Relevance.** Cite as the "VLM-as-encoder" thread, distinguishing Path C's "VLM-as-counterfactual-reasoner" approach.
**Tag.** `vlm-in-rl`

### 3.7 Duan et al. 2024 — AHA (ICLR 2025)
```bibtex
@inproceedings{duan2025aha,
  title={AHA: A Vision-Language-Model for Detecting and Reasoning Over Failures in Robotic Manipulation},
  author={Duan, Jiafei and Pumacay, Wilbert and Kumar, Nishanth and Wang, Yi Ru and Tian, Shulin and Yuan, Wentao and Krishna, Ranjay and Fox, Dieter and Mandlekar, Ajay and Guo, Yijie},
  booktitle={ICLR},
  year={2025},
  note={arXiv:2410.00371}
}
```
**Summary.** Open-source VLM fine-tuned on FailGen-generated robot failure trajectories. Detects and explains manipulation failures via free-form reasoning; beats GPT-4o by 10.3%; integrates into RL/TAMP/zero-shot frameworks raising success by 21.4%.
**Relevance.** **Important comparison point.** AHA is the canonical "VLM identifies *why* manipulation failed" paper — exactly the capability Path C exploits. Our differentiation: AHA feeds VLM failure reasoning into reward shaping; we feed it into counterfactual replay relabeling.
**Tag.** `vlm-in-rl`

### 3.8 Feng et al. 2025 — CoSo (ICML 2025)
```bibtex
@inproceedings{feng2025coso,
  title={Towards Efficient Online Tuning of VLM Agents via Counterfactual Soft Reinforcement Learning},
  author={Feng, Lang and Tan, Weihao and Lyu, Zhiyi and Zheng, Longtao and Xu, Haiyang and Yan, Ming and Huang, Fei and An, Bo},
  booktitle={ICML},
  year={2025},
  note={arXiv:2505.03792}
}
```
**Summary.** CoSo uses counterfactual reasoning to identify causally-influential tokens in VLM agent outputs and prioritizes their exploration during fine-tuning. Tested on Android control, card games, embodied AI.
**Relevance.** Confirms VLM + counterfactual reasoning + RL is an emerging template — but applied at the *token* level for VLM-agent fine-tuning, not at the *trajectory* level for manipulation. Important Path C neighbor; we must distinguish.
**Tag.** `vlm-in-rl` / `credit-assignment`

### 3.9 Glossop et al. 2025 — CAST
```bibtex
@article{glossop2025cast,
  title={CAST: Counterfactual Labels Improve Instruction Following in Vision-Language-Action Models},
  author={Glossop, Catherine and Chen, William and Bhorkar, Arjun and Shah, Dhruv and Levine, Sergey},
  journal={arXiv preprint arXiv:2508.13446},
  year={2025}
}
```
**Summary.** VLM generates counterfactual language-action pairs (alternative instructions for executed trajectories) to augment VLA training data. +27% on navigation.
**Relevance.** Path-C-adjacent; uses VLMs for counterfactual labeling. But it's *imitation-learning data augmentation for VLAs*, not RL with PER. Our paper's framing should explicitly contrast.
**Tag.** `vlm-in-rl`

### 3.10 Hu et al. 2026 — ECHO (LM Hindsight Trajectory Rewriting)
```bibtex
@article{hu2026echo,
  title={Sample-Efficient Online Learning in LM Agents via Hindsight Trajectory Rewriting},
  author={Hu, Michael Y. and Van Durme, Benjamin and Andreas, Jacob and Jhamtani, Harsh},
  journal={arXiv preprint arXiv:2510.10304},
  year={2026}
}
```
**Summary.** ECHO has the LM itself generate optimized trajectories for *alternative goals* that could have been achieved from a failed attempt — language-model HER. Up to 80% gains on XMiniGrid and PeopleJoinQA, outperforms Reflexion and AWM.
**Relevance.** Direct conceptual analog to Path C in the LM-agent space. Cite as evidence that "LLM/VLM as counterfactual hindsight generator" is a maturing pattern; Path C ports the idea to physical manipulation with PER.
**Tag.** `vlm-in-rl` / `her-sota`

### 3.11 Ding 2026 — AgentHER
```bibtex
@article{ding2026agentHER,
  title={AgentHER: Hindsight Experience Replay for LLM Agent Trajectory Relabeling},
  author={Ding, Liang},
  journal={arXiv preprint arXiv:2603.21357},
  year={2026}
}
```
**Summary.** HER adapted to natural-language agent trajectories. LLM-guided relabeling with confidence gating and multi-judge verification (gpt-4o-mini + Qwen2.5-72B). +7-12% on WebArena/ToolBench.
**Relevance.** Another "LM as hindsight oracle" instance — confirms the recipe works for LM agents. Path C is the manipulation analog.
**Tag.** `vlm-in-rl` / `her-sota`

### 3.12 Singh et al. 2024 — LGR2 (Language-Guided Reward Relabeling)
```bibtex
@article{singh2024lgr2,
  title={LGR2: Language Guided Reward Relabeling for Accelerating Hierarchical Reinforcement Learning},
  author={Singh, Utsav and Bhattacharyya, Pramit and Namboodiri, Vinay P.},
  journal={arXiv preprint arXiv:2406.05881},
  year={2024}
}
```
**Summary.** LLM-generated reward functions for the high-level policy in HRL; integrates with HER goal relabeling. >55% success on hard tasks with real-robot transfer.
**Relevance.** Cite as another point on the "LLM/VLM + HER hybrid" map; uses LLM for *reward* generation while still applying classical HER goal relabeling.
**Tag.** `vlm-in-rl` / `her-sota`

### 3.13 Zhai et al. 2025 — VLAC (Vision-Language-Action-Critic)
```bibtex
@article{zhai2025vlac,
  title={A Vision-Language-Action-Critic Model for Robotic Real-World Reinforcement Learning},
  author={Zhai, Shaopeng and Zhang, Qi and Zhang, Tianyi and Huang, Fuxian and Zhang, Haoran and Zhou, Ming and Zhang, Shengzhe and Liu, Litao and Lin, Sixu and Pang, Jiangmiao},
  journal={arXiv preprint arXiv:2509.15937},
  year={2025}
}
```
**Summary.** Single InternVL-based model that alternately emits reward tokens and action tokens — unifying critic and policy. Human-in-the-loop protocol; 30%→90% success in 200 real-world episodes.
**Relevance.** Cite as the "VLM-as-critic" axis. Path C uses the VLM as a *counterfactual oracle*, not a continuous critic, which is computationally cheaper and more targeted.
**Tag.** `vlm-in-rl`

### 3.14 Zhou et al. 2026 — MARVL (Multi-Stage VLM-Guided Manipulation)
```bibtex
@article{zhou2026marvl,
  title={MARVL: Multi-Stage Guidance for Robotic Manipulation via Vision-Language Models},
  author={Zhou, Xunlan and Chen, Xuanlin and Zhang, Shaowei and Wan, ShengHua and Hu, Xiaohai and Yuan, Lei and Zhan, De-chuan},
  journal={arXiv preprint arXiv:2602.15872},
  year={2026}
}
```
**Summary.** Fine-tunes a VLM via Scene-View Decomposition and adds Task Direction Projection + Confidence-Thresholded Shaping to produce calibrated dense VLM rewards. Outperforms VLM-reward baselines on Meta-World sparse manipulation.
**Relevance.** Direct competitor on Meta-World benchmarks. Cite when comparing on sparse-reward manipulation results.
**Tag.** `vlm-in-rl`

### 3.15 Luu et al. 2025 — ERL-VLM
```bibtex
@article{luu2025erlvlm,
  title={Enhancing Rating-Based Reinforcement Learning to Effectively Leverage Feedback from Large Vision-Language Models},
  author={Luu, Tung M. and Lee, Younghwan and Lee, Donghoon and Kim, Sunho and Kim, Min Jun and Yoo, Chang D.},
  journal={arXiv preprint arXiv:2506.12822},
  year={2025}
}
```
**Summary.** Queries VLMs for absolute trajectory ratings (rather than pairwise comparisons), with stratified sampling and MAE loss to handle data imbalance and label noise. Beats baselines on 6/7 MetaWorld and ALFRED tasks; real-robot demonstrations.
**Relevance.** Cite for the "VLM-as-rating-source" branch. Path C uses the VLM more surgically (per-trajectory counterfactual queries on failures).
**Tag.** `vlm-in-rl`

### 3.16 Ma et al. 2026 — Freshness-Aware PER for LLM/VLM RL
```bibtex
@article{ma2026freshnessper,
  title={Freshness-Aware Prioritized Experience Replay for LLM/VLM Reinforcement Learning},
  author={Ma, Weiyu and Zeng, Yongcheng and Song, Yan and Cui, Xinyu and Zhao, Jian and Liu, Xuhui and Elhoseiny, Mohamed},
  journal={arXiv preprint arXiv:2604.16918},
  year={2026}
}
```
**Summary.** Identifies *priority staleness* as the failure mode of vanilla PER for billion-parameter LM/VLM training; adds an effective-sample-size-grounded exponential age decay. +46% NQ Search, +367% Sokoban, +133% VLM FrozenLake over on-policy.
**Relevance.** First serious PER methodology for LM/VLM-RL settings. Path C's PER weighting will need to address an analogous freshness concern as the policy improves and old failure-relabeled samples become stale; cite as methodological precedent.
**Tag.** `vlm-in-rl` / `her-sota`

### 3.17 Yong et al. 2026 — VLLR (Generalizable Dense Reward)
```bibtex
@article{yong2026vllr,
  title={Generalizable Dense Reward for Long-Horizon Robotic Tasks},
  author={Yong, Silong and Sheng, Stephen and Qi, Carl and Wang, Xiaojie and Sheehan, Evan and Shivaprasad, Anurag and Xie, Yaqi and Sycara, Katia and Dattatreya, Yesh},
  journal={arXiv preprint arXiv:2604.00055},
  year={2026}
}
```
**Summary.** Combines extrinsic VLM/LLM rewards for task-progress recognition with intrinsic self-certainty rewards. Up to 56% absolute success-rate improvement on CHORES; +5/+10% over SOTA on ID/OOD tasks.
**Relevance.** Cite for long-horizon dense-reward VLM methods. Reinforces the field-wide trend: VLMs are reshaping RL reward shaping in manipulation.
**Tag.** `vlm-in-rl`

---

## Synthesis Paragraph

The 2024-2026 literature converges on three orthogonal mechanisms for injecting foundation models into RL: (i) VLMs as **reward signals** (KAGI, Rocamonde et al., VLM-CaR, ERL-VLM, MARVL, VLLR, LRM, VLAC), (ii) VLMs as **representations or critics** (Promptable-Representations, VLAC), and (iii) LM/VLMs as **hindsight/counterfactual relabelers** — almost exclusively in the text-agent setting (ECHO, AgentHER, CAST, CoSo) with the partial exception of Sharony et al.'s VLM-Guided Experience Replay (trajectory-ranking) and Chuck et al.'s HInt/NCII (model-based counterfactual interactions). Classical credit-assignment work (Pignatelli's 2023 survey, RUDDER, Mesnard's CCA-PG) has matured into LLM-token-level causal credit assignment (Khandoga 2026), but the analogous step for *manipulation trajectories* — using a VLM to localize where a failure went wrong and synthesize a counterfactual goal for prioritized replay — is conspicuously missing. Meanwhile HER itself remains the active baseline: Next-Future, CEBP, GCHR, D-SPEAR, and Act2Goal all show that prioritization, relabeling, and dual-stream replay continue to deliver SOTA on sparse-reward manipulation. **Our work fits at the precise gap:** we treat a VLM as a counterfactual oracle for failure localization, and we plug that oracle into a prioritized experience replay scheme designed for sparse-reward physical manipulation — combining Thread 1's counterfactual credit-assignment formalism, Thread 2's HER lineage and its 2025-2026 prioritization advances, and Thread 3's emerging "foundation-model-as-reasoner-over-trajectories" pattern. The closest neighbors are Sharony (VLM ranks, doesn't relabel) and HInt (counterfactual interactions via dynamics models, not VLMs); neither closes the gap we target.

---

## Coverage check

- **Six MUST-CITE papers fetched and characterized:** Next-Future (2.1), CEBP (2.2), Credit-Assignment Survey (1.1), Sharony VLM-RB (3.1), Large Reward Models (3.2), KAGI (3.3). All confirmed.
- **17 total annotated entries** spanning the three threads.
- **Thread breakdown:** credit-assignment = 4 entries, her-sota = 8 entries (with overlap), vlm-in-rl = 11 entries (with overlap).
- **Path C scoop check:** clean — no direct competitor doing VLM-failure-localized counterfactual relabeling for manipulation PER. Closest neighbors are flagged at the top.
