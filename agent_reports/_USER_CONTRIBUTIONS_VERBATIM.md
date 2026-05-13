# User-Provided Per-Member Contributions (CS 285 Final Paper)

**Provided by Daniel directly on 2026-05-13.**
**Operational rule:** the next agent that touches `paper_cs285/main.tex` `\section*{Contributions}` block MUST replace the placeholder text with the exact attributions below. **Do not interpret, summarize, or embellish.**

## EXACT REPLACEMENT TEXT (v2 — updated with Parshawn's milestone scope and Matei's MetaWorld study)

Replace the entire `\begin{itemize}...\end{itemize}` block inside `\section*{Contributions}` with the following LaTeX:

```latex
\begin{itemize}\itemsep0pt
\item \textbf{Daniel Grant.} Counterfactual ideation and
  implementation (\texttt{vlm\_cf} and \texttt{verified\_cf});
  ablations on FetchPickAndPlace, FetchSlide, and the
  $p_{\text{counterfactual}}$ sweep; initial writing of the
  manuscript.
\item \textbf{Matei Gardea.} Initial project idea; implementation
  of an alternative pointwise/pairwise VLM-replay-buffer rescaling
  combined with PER (a non-positive variant reported as a negative
  finding); auxiliary 60-run MetaWorld replay-mechanism ablation
  (cross-benchmark corroboration of PER\,$>$\,Uniform; cf.\
  Appendix\,[X]); editing of the final submission document.
\item \textbf{Parshawn Gerafian.} Implementation and analysis for
  the milestone checkpoint: designed and ran the 27-run
  Uniform/PER/Semantic-PER ablation across the three Fetch tasks
  (SAC, 1\,M training steps, 3 seeds per configuration on Modal
  A10G) that established the PER baselines used throughout the
  final paper. Identified the additive-blending failure mode
  ($0.7 \cdot \text{semantic} + 0.3 \cdot \text{TD}$ suppresses
  PER when the VLM is miscalibrated), which motivated the
  multiplicative IS-pairing framing now central to
  \S\ref{sec:method}. Provided feedback during the transition to
  the augmented final-paper direction.
\end{itemize}
```

Notes for Pass 3:
- If Matei's MetaWorld PR (PR #1) is NOT integrated due to 11pp ceiling, drop the "; auxiliary 60-run MetaWorld... (cf. Appendix [X])" clause from Matei's bullet.
- If Matei's MetaWorld PR IS integrated, replace `[X]` with the actual appendix label.

## Plain-English Source (for reference / cross-check)

> Daniel: "give me credit for the counterfactual ideation and implementation, along with ablations regarding pnp/slide/p. Also did initial writing of the paper."
>
> Matei: "came up with our initial idea, and helped implement an alternative pointwise/pairwise vlm replay buffer based rescaling with per that ended up generally producing generally non-positive results … matei also helped with editing of our final submission document."
>
> Parshawn: "covered implementation and analysis for the first checkpoint, and gave helpful feedback as we transitioned into an augmented final paper idea."

## Parshawn's milestone (paraphrased from Daniel's verbatim summary of the milestone document)

**Milestone title**: Semantic Failure Localization for Prioritized Experience Replay
**Authors** (milestone): Parshawn Gerafian, Matei Gardea, Daniel Grant

Milestone-stage hypothesis: a VLM can identify causal failure moments in failed Fetch episodes; Semantic PER (additive blend `0.7·semantic + 0.3·TD`) should improve over PER.

Milestone-stage experiments (Parshawn): 27-run ablation — Uniform, PER, Semantic PER × 3 Fetch envs × 1M training steps × 3 seeds, SAC, Modal A10G GPUs.

Milestone-stage findings:
- PER reaches 95% mean success on FetchPush; Uniform and Semantic PER plateau at 5-10%.
- PnP and Slide remain below 25% across all methods at this horizon.
- Semantic PER underperforms PER on Push/PnP because (1) additive blending `0.7·sem + 0.3·TD` suppresses PER's signal when the VLM is wrong, (2) GPT-4o cannot reliably localize failure in MuJoCo renders. Slide is competitive (simpler single-contact structure).
- Revision plan from milestone: **switch to multiplicative blending** (`final = TD × semantic_weight`) — this revision became the multiplicative IS-pairing principle that grounds §3 of the final paper.
- Additional milestone observations: semi-Markovian failure structure may favor video LLMs over keyframes; an "unknown" escape hatch for the VLM; keyframe selection-bias analysis as policy improves.

**Project-narrative point**: Parshawn's milestone finding that additive blending fails (when the VLM is miscalibrated) directly motivated the paper's central theoretical contribution — the multiplicative IS-pairing requirement. This is the conceptual bridge between Parshawn's milestone work and Daniel's final-paper theory and experiments. The contribution bullet above credits this explicitly.

## Important notes

- Author order in the title block (`Daniel Grant \quad Parshawn Gerafian \quad Matei Gardea`) stays as is — that order is set in the title block, not in the contributions ordering. Daniel-first reflects lead authorship per the contributions described above.
- The Contributions section ordering above (Daniel → Matei → Parshawn) reflects the natural narrative of the project (idea → impl → ablations), not seniority.
- Mention of "non-positive results" for Matei's variant is INTENTIONAL — it's an honest negative finding the paper acknowledges.
