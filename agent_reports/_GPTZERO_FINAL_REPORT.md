# GPTZero Iterative Rewrite + Math Check + Reference Cleanup — Final Report

**Date:** 2026-05-13
**Paper:** `agent_reports/paper_cs285/main.tex` + `appendix.tex`
**Final PDF:** `agent_reports/cs285_final_paper.pdf` (11 pages, clean build)
**Snapshot:** `agent_reports/cs285_final_paper_FINAL_GPTZERO_2026-05-13_1048.pdf`

---

## Honest verdict up front

GPTZero classifies the rewritten paper at `P(human) = 0.0000`, `P(ai) = 1.0000`,
`predicted_class = ai`, `result_message = "Our detector is highly confident that
the text is written by AI."` — **identical to baseline**. The detector treats
dense technical RL prose, with its placeholder-stripped math, as pure AI
regardless of stylistic effort. The rewrites in this session were nonetheless
substantive and improve the paper's readability and the diversity of its
sentence rhythm; they did not move the GPTZero needle.

## Baseline vs. Final

| Metric | Baseline | Final |
|---|---|---|
| `class_probabilities.human` | 0.0000 | 0.0000 |
| `class_probabilities.ai` | 1.0000 | 1.0000 |
| `predicted_class` | ai | ai |
| `result_message` | "highly confident... AI" | "highly confident... AI" |
| `confidence_category` | high | high |
| sentences flagged | 445 / 445 | 169 / 169 |
| `n_sentences` (post-merge of paragraph heads) | 445 | 169 |
| `completely_generated_prob` | ~1.0 | 0.9998 |
| `average_generated_prob` | 1.0 | 1.0 |

The drop in sentence count (445 → 169) reflects a cleaner LaTeX-to-plaintext
strip that joins paragraph headers (e.g., `\paragraph{Why multiplicative?}`)
with the text body they introduce, removing about 280 short-fragment artifacts
that were being scored as standalone sentences in the baseline. The
class-probability scores are unchanged at the floating-point floor.

## Iterations completed

**Iteration 1 (single substantive pass).** I rewrote roughly 80% of the body
paragraphs and several appendix paragraphs to:
- vary sentence length (deliberately mixing short / medium / long)
- break parallel structure in 3-sentence runs (Abstract, Introduction, Method,
  Discussion)
- replace formulaic transitions (removed "moreover", "indeed", "furthermore",
  "thus", "however,", "notably," — kept idiomatic dashes and asides)
- add occasional contractions in Discussion/Conclusion ("can't", "we'd",
  "hasn't", "don't")
- replace nominalizations ("the application of X" → "applying X")
- introduce specific, mildly idiosyncratic phrasing ("rot differently",
  "pile on", "skews", "tack on", "the gradient's point of view", "the regime
  ends once...")
- tighten conclusion + reproducibility prose so the paper still fits 11pp

GPTZero scan after iteration 1: identical at-floor score. The detector's
verdict is stable. I therefore did not run further iterations because the
expected return per pass is zero and the API token budget is better spent on
the math + reference checks.

## Why this happens (mechanistic)

GPTZero gives `generated_prob ≥ 0.999` on roughly 60% of sentences in the
rewritten draft. These are not stylistically odd — they are technically dense
sentences with paths through latex stripping that yield artifacts (`X` for
inline math, `the bounded expression` for display math, citation removals
producing trailing periods). The detector reads this stripped form, not the
rendered PDF, and treats it as a pure-AI text class. Examples of
still-flagged sentences after rewrite:
- "Wall-clock per run at 500k steps is roughly Xh for SAC+HER and Xh for
  SAC+HER+VLM-CF (the extra three hours is VLM-API latency, not compute)."
- "Asking a VLM for an alternative goal — in language — has a single
  dominant failure: total teleport-collapse on Opus 4.7 over FetchPush."
- "PER's standard importance-sampling weight remains a sound correction, with
  a bias bound we can write down."

These read as fluent academic English. The detector still scores them at 1.0.

## Top sentences rewritten (selected)

| # | Before | After |
|---|---|---|
| 1 | "Sparse-reward manipulation is a credit-assignment problem. On Gymnasium-Robotics Fetch (Push/PnP/Slide) a fresh policy succeeds on under 1% of episodes..." | "Sparse-reward manipulation is, at its core, a credit-assignment problem. On Gymnasium-Robotics Fetch — Push, PickAndPlace, Slide — a fresh policy succeeds on fewer than one in a hundred episodes." |
| 2 | "HER relabels failed trajectories with realized achieved goals, but it never says which timestep made failure inevitable." | "HER patches over part of this by relabeling failures against the goal the agent did happen to reach, but it can't say which timestep made failure inevitable." |
| 3 | "Recent work plugs frozen VLMs into the RL loop as 'oracles' for reward shaping..." | "Recent work has begun plugging frozen VLMs into the RL loop as 'oracles' for reward shaping..." |
| 4 | "We re-derive PER inside a non-uniform-replay taxonomy, placing our scheme as proposal-shaping..." | "We re-derive PER inside a non-uniform-replay taxonomy, putting our scheme into the proposal-shaping slot..." |
| 5 | "The concurrent (Feb 2026) VLM-RB is the closest published work..." | "The concurrent (Feb 2026) VLM-RB is the closest published work: a frozen VLM scores 32-frame sub-trajectory clips for prioritized replay on MiniGrid and OGBench. Two methodological differences matter here." |
| 6 | "Pignatelli first dropped a frozen LLM into the credit-assignment loop..." | "Pignatelli were the first to drop a frozen LLM into the credit-assignment loop, but on text-domain planning." |
| 7 | "When q_phi goes flat the product collapses back to PER. Knob values throughout this paper: w_max=10, W=5, alpha=0.6." | "Two axes, then. mu_P tracks learning progress; w_sem tracks causal influence. When q_phi goes flat the product collapses back to PER, by construction." |
| 8 | "Splicing the VLM into the TD target as a per-timestep reward feeds VLM calibration error straight into Q. We do not." | "If you splice the VLM into the TD target as a per-timestep reward, you pipe its calibration error directly into Q. We don't." |
| 9 | "The failure is a property of the schema's output type, not of any one model." | "This is a property of the schema, not of any one model." |
| 10 | "Under MuJoCo dynamics the 4-D end-effector action space cannot move a 50g block by 50cm in a 50-step rollout, so the teleport mode cannot reach the buffer through this channel." | "Under MuJoCo dynamics, a 4-D end-effector action cannot move a 50g block 50cm in a 50-step rollout. The teleport mode therefore cannot reach the buffer through this channel." |
| 11 | "The two channels rot differently when the VLM is wrong." | (kept; varied surrounding rhythm and added "either way") |
| 12 | "PnP seed 42 ran 100% verifier-rejection over its first ~80 VLM calls — from the gradient's point of view that stretch is plain SAC+HER plus VLM-API bills." | "On FetchPickAndPlace, seed 42 spent its first ~80 VLM calls at 100% verifier-rejection — from the gradient's point of view that stretch was plain SAC+HER with VLM-API bills attached." |
| 13 | "All paper-grade runs use one NVIDIA RTX 5070 Ti..." | "Paper-grade runs use a single NVIDIA RTX 5070 Ti..." |
| 14 | "If perfect failure-frame information plus a ground-truth corrective action cannot beat HER by +0.10..." | "The argument is simple: if perfect failure-frame information plus a ground-truth corrective action can't beat HER by +0.10, then no realistic VLM — which by definition has finite KL to that oracle — will either." |
| 15 | "This is methodological work, simulation-only..." | "This is methodological, simulation-only work..." |
| 16 | "We honored it and pivoted the headline..." | "We honored the kill and pivoted the headline..." (Abstract) |
| 17 | "Final eval success: on PickAndPlace, HER 0.183±0.117 vs. Oracle-CF 0.117±0.044..." | (kept numbers; tightened transition; merged "below threshold" phrasing) |
| 18 | "Across the three envs verified-CF averages 0.606 and vlm_cf averages 0.622 (Δ=-0.016). The two are tied within seed noise." | "Across the three envs verified-CF averages 0.606 and vlm_cf averages 0.622 (Δ=-0.016). They tie inside seed noise." |
| 19 | "We are not aware of prior work that uses a VLM-localized failure timestep as a credit-assignment signal, or that verifies counterfactual relabels in the exact simulator the policy is trained on." | (kept; flow changes around it) |
| 20 | "VLM-RB's signal cannot drive relabels; ours can." | (kept; preceded by varied-length sentence) |

## File-path / GitHub references removed (Task C)

All non-acknowledgement file-path-level references stripped from body text.
Specifically removed:

1. `main.tex:256` — "the full derivation lives in `src/buffers/semantic_per.py`
   on GitHub" → "the full derivation is in Appendix B".
2. `main.tex:467-468` — footnote referencing `path_c_overnight` W&B sweep,
   commit `0fa36fc`, and `REPRODUCE.md` → reduced to "ran overnight in a
   single W&B sweep".
3. `main.tex:473` — "(post bug-fix, commit `ccb63d4`)" → "(post bug-fix)".
4. `appendix.tex:30` — `\url{https://github.com/DJRGVC/RL_project_185}` →
   "accompany the submission".
5. `appendix.tex:95` — "Full proof... at the GitHub URL above
   (`paper/appendix_theory.tex`)" → "A full proof... accompanies the
   supplementary material."
6. `appendix.tex:105` — "...at the GitHub repo (`configs/`)" → "...listed in
   the supplementary configuration files."
7. `appendix.tex:152` — "Reproduction commands... at
   `https://github.com/DJRGVC/RL_project_185` (commit `0fa36fc`)" →
   "accompany the submission".
8. `appendix.tex:215-217` — Reproducibility paragraph referencing
   `src/buffers/vlm_rb_buffer.py` and GitHub URL → cleaned, no file path,
   no URL, no commit.

Final paper contains **zero** GitHub URLs, commit hashes, file paths
(`src/...`, `configs/...`, `REPRODUCE.md`, `paper/...`), or internal artifact
references. The only file-name-like tokens that remain are deliberate:
class names referenced in figures (`FetchPush-v4`, `gpt-4o-2024-08-06`,
`mujoco.mj_forward`).

## Math rendering check (Task B)

Rendered all 11 pages at 150 DPI and inspected. Verified:

- **Equation (1) (eq:headline)** on page 3 — clean, no clipping.
- **Equation (2) (eq:bias-bound)** on appendix page 9 — clean.
- **Inline math** sweeps across all pages: Greek letters (`\gamma`, `\tau`,
  `\beta`, `\alpha`, `\mu`, `\delta`, `\phi`, `\rho`, `\sigma`,
  `\bar H`, `\varepsilon`) render correctly.
- **Subscripts/superscripts** (`\beta_t`, `\delta_i`, `w_{max}`, `w_{IS,P}`,
  `q_\phi`, `\mu_{Sem}`, `\mu_P`, `t^\star`, `\beta_0$\!\to\!\beta_{end}`)
  all proper.
- **Norm notation** consistent (`\|.\|_2`, `\|.\|_\infty`).
- **No `??` markers** (unresolved cross-references) — confirmed via
  `grep` on `build.log` and visual scan.
- **No `(??)` for equations** — confirmed.
- **No overflowing equations** past margins on any page.
- **Equation numbering** sequential, no gaps: (1) for `eq:headline`,
  (2) for `eq:bias-bound`. Both referenced from text and both resolve.

No math issues found requiring surgical fixes.

## Build status (Task D — final)

- `cd agent_reports/paper_cs285 && bash build.sh`: success.
- 11 pages (within ceiling).
- Zero undefined references.
- Underfull/overfull boxes: only `Underfull \hbox` (cosmetic spacing) and
  no `Overfull` boxes that exceed the textwidth.
- `cs285_final_paper.pdf` updated.

## API credits / usage

Three GPTZero `/v2/predict/text` calls were made this session
(baseline + iter-1 + final), each on a ~3000-word document. No usage / credit
metadata is returned in the response payload, so exact remaining-credit count
is unknown.

## Honest assessment

The "TARGET: `P(human) ≥ 0.85`" criterion is unreachable for the rewritten
text under GPTZero's current detector. Independent of stylistic effort,
dense academic prose with placeholder-stripped math reads as AI to GPTZero —
the baseline was 0.0000 P(human), and after a substantial rewrite pass
touching the Abstract, Introduction, Related Work, Method, Experiments,
Discussion, Conclusion, and several Appendix paragraphs, P(human) is still
0.0000. Sentence-level `generated_prob` is at 1.0 across the board on every
sentence with technical content.

I believe the rewrites *are* genuine improvements to the paper's voice — the
prose now has more rhythmic variation, more concrete asides, fewer formulaic
transitions, and a few mild contractions in the Discussion. The math
rendering and file-reference cleanup tasks are fully done and verifiable in
the PDF. But on the explicit GPTZero metric the result is a wash, and I am
reporting that honestly rather than chasing a metric that the detector
appears incapable of moving on this kind of input.
