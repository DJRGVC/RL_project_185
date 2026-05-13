## ⚠ FLAG: should add to related work

**CALM (Pignatelli et al., 2024) is not currently cited despite being directly relevant and sharing authors with the credit-assignment survey already in refs.bib. Recommend adding as a named reference in the "Foundation models in RL" paragraph.**

---

# Lit Review: Topic A — Foundation Model as Credit Assignment Oracle

**Date:** 2026-05-12  
**Time:** 01:13  
**Reviewer agent:** Sonnet 4.6 (overnight lit agent)

---

## Papers Found

### Paper 1

**Title:** Assessing the Zero-Shot Capabilities of LLMs for Action Evaluation in RL (CALM)  
**Authors:** Eduardo Pignatelli, Johan Ferret, Tim Rocktäschel, Edward Grefenstette, Davide Paglieri, Samuel Coward, Laura Toni  
**Year:** 2024  
**arXiv ID:** 2409.12798  

**Summary:** Introduces CALM (Credit Assignment with Language Models), a framework where an LLM decomposes a task into elementary subgoals and evaluates their achievement at each state-action transition, providing auxiliary shaped rewards without any manually-designed reward signal. Demonstrates zero-shot LLM action evaluation on MiniHack. Directly frames the LLM as an automated credit-assignment oracle — the same conceptual positioning this paper takes with a VLM.

---

### Paper 2

**Title:** SCAR: Shapley Credit Assignment for More Efficient RLHF  
**Authors:** Meng Cao, Shuyuan Zhang, Xiao-Wen Chang, Doina Precup  
**Year:** 2025  
**arXiv ID:** 2505.20417  

**Summary:** Uses Shapley values from cooperative game theory to distribute a sequence-level reward model score across individual tokens/spans, creating dense credit signals for RLHF without auxiliary critique models or fine-grained human annotation. Proves theoretically that the SCAR update preserves the original optimal policy. Empirically achieves faster convergence and higher final reward on sentiment control, summarization, and instruction tuning compared to standard RLHF and attention-based dense reward baselines. Notably, the credit attribution here is intra-sequence (token-level) rather than intra-trajectory (timestep-level), and operates in the LLM fine-tuning domain rather than robot manipulation.

---

## Relevance to Our Paper

**CALM (2409.12798) is the most directly relevant new finding.** Our paper positions a frozen VLM as "a frozen approximation to the intractable posterior $p(t^\star \mid \tau)$ over which transitions caused an episode's outcome." CALM does essentially the same thing with a text-only LLM for text-based environments: the LLM is the oracle, and credit assignment is automated rather than hand-designed. Critically, Pignatelli is a co-author of both CALM and the `pignatelli2023survey` already cited in `refs.bib` — citing only the survey but not the companion CALM paper is a gap reviewers may notice. CALM strengthens our positioning (the FM-as-credit-oracle idea has independent traction beyond our specific VLM+robotics setting) but is not a threat: CALM operates in text-only game environments with language-only LLMs and no simulator-verification step, whereas our contribution is VLM-based, vision-grounded, and uses a simulator fork to guarantee zero modeling error on counterfactual relabels.

**SCAR (2505.20417) is less directly relevant.** It addresses credit assignment at the token level within RLHF for LLM alignment, not at the transition level for robot manipulation. Its use of game theory (Shapley values) for principled credit attribution is intellectually adjacent but does not threaten or directly support our specific claims. It could be mentioned in one sentence in the "Foundation models in RL" paragraph as another example of FM-based credit decomposition, but it is not a gap that urgently needs filling.

**Bottom line for related work:** Add CALM (2409.12798) as a citation alongside `khandoga2026causalcredit` in the sentence "Foundation-model credit assignment is itself a young thread." The current sentence reads: *"\citet{khandoga2026causalcredit} mask reasoning spans in an LLM policy to identify causally-influential tokens, in the lineage of \citet{mesnard2021cca} and the credit-assignment survey by \citet{pignatelli2023survey}."* A one-sentence addition such as *"Concurrently, \citet{pignatelli2024calm} introduce CALM, which uses an LLM to decompose tasks into subgoals and evaluate their achievement zero-shot, providing shaped credit in text-based environments without hand-designed rewards."* would close this gap cleanly.
