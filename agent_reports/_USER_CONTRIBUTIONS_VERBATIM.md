# User-Provided Per-Member Contributions (CS 285 Final Paper)

**Provided by Daniel directly on 2026-05-13.**
**Operational rule:** the next agent that touches `paper_cs285/main.tex` `\section*{Contributions}` block MUST replace the placeholder text with the exact attributions below. **Do not interpret, summarize, or embellish.**

## EXACT REPLACEMENT TEXT

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
  combined with PER (this variant produced generally non-positive
  results and is reported as a negative finding); editing of the
  final submission document.
\item \textbf{Parshawn Gerafian.} Implementation and analysis for
  the milestone (first) checkpoint; feedback during the transition
  to the augmented final-paper direction.
\end{itemize}
```

## Plain-English Source (for reference / cross-check)

> Daniel: "give me credit for the counterfactual ideation and implementation, along with ablations regarding pnp/slide/p. Also did initial writing of the paper."
>
> Matei: "came up with our initial idea, and helped implement an alternative pointwise/pairwise vlm replay buffer based rescaling with per that ended up generally producing generally non-positive results … matei also helped with editing of our final submission document."
>
> Parshawn: "covered implementation and analysis for the first checkpoint, and gave helpful feedback as we transitioned into an augmented final paper idea."

## Important notes

- Author order in the title block (`Daniel Grant \quad Parshawn Gerafian \quad Matei Gardea`) stays as is — that order is set in the title block, not in the contributions ordering. Daniel-first reflects lead authorship per the contributions described above.
- The Contributions section ordering above (Daniel → Matei → Parshawn) reflects the natural narrative of the project (idea → impl → ablations), not seniority.
- Mention of "non-positive results" for Matei's variant is INTENTIONAL — it's an honest negative finding the paper acknowledges.
