# Agent 10 — Mechanical Proofread

Source: `agent_reports/paper_cs285/main.tex` + `appendix.tex`
Rendered: `agent_reports/cs285_final_paper.pdf` (11 pages, 150 DPI inspection).
Build log: `agent_reports/paper_cs285/build.log` + `main.log`.

## CRITICAL: PDF is out of sync with main.tex

- `main.tex` modified 2026-05-12 23:33:10 (refers to `fig_headline_v5.pdf` on L345).
- `cs285_final_paper.pdf` last built 2026-05-12 23:27:17 (still embeds `fig_headline_v4.pdf` per `main.log` L595–597 and `build.log`).
- `fig_headline_v5.pdf` was written at 23:33:21 (after build).
- **Must rebuild before submission**; otherwise headline figure shown is the v4 version, not the v5 referenced in source.

## Build.log warnings

- L151–154 / L322–335: `Underfull \hbox (badness 10000)` in the Setup paragraph. Tight microtype "+20" expansion. Cosmetic but visible in render — the "Setup. We use Gymnasium-Robotics FetchPush-v4 …" line on p4 is loose.
- L156: `Underfull \vbox (badness 1314)` while \output is active on page 4.
- L157: `Underfull \vbox (badness 10000)` on page 5.
- L160–179 (appendix L19–20): five `Underfull \hbox (badness 10000)` warnings inside the verbatim-style prompt block. Visible on p8 — `\texttt{...}` cannot wrap a long monospace string cleanly. Consider line-breaking the prompt with explicit `\\`, switching to a `verbatim`/`lstlisting` environment, or shrinking the font further (already `\small`).
- L181–182: `Overfull \hbox (20.85347pt too wide)` at appendix lines 110–143 — the hyperparameters table (Table 2) overruns the text block by ~21pt; visible on p10 (text/figures clip into right margin). Must-fix.
- No undefined references, no undefined citations, no multiply-defined labels — clean otherwise.

## Typos

- **main.tex L373**: "Aggregating across the three envs, verified-CF reaches mean $0.606$ and vlm\_cf reaches $0.622$" — fine, but two lines later "Verified-CF \emph{exceeds} vlm\_cf on Slide" — author shifts capitalisation. See *Consistency*.
- **main.tex L450**: "On Push (post bug-fix, commit \texttt{ccb63d4})" — should this commit hash match the reproducibility hash `0fa36fc` used elsewhere (appendix L155, L241)? Two different SHAs in same paper is unusual; verify both are intentional.
- **appendix.tex L17**: `\texttt{...$\in\{0,\dots,K\!-\!1\}$, "reasoning": $s$\}.}` — the `$ ... $` math inside `\texttt{}` causes the multiple underfull-hbox warnings on p8 (visible: `2 f0 ; ... ; K −1 g$` rendered awkwardly). Math-in-monospace is the root cause; recommend rewriting the JSON template without math mode.

## Grammar

- **main.tex L78**: "(2) **VLM-Verified Counterfactual Hindsight**: we close the dominant failure mode of language-only counterfactuals (100\% teleport-collapse of Opus~4.7 on FetchPush) by **asking the VLM for** a \emph{corrective action sequence} rather than a hindsight goal, executing it in a simulator fork, and admitting only physics-consistent, reward-positive relabels into the buffer (confidence~1.0, zero modeling error)." — long sentence; "by asking ... executing ... and admitting" is fine parallelism but "executing it" has ambiguous referent ("the sequence" vs "the failure mode"). Consider "executing the proposed sequence …".
- **main.tex L109–111**: "the relabel target is constrained to the agent's actually-realized trajectory, so the most instructive transition (the one where failure became inevitable) receives no special treatment." — "actually-realized" is fine but unusual. Consider just "actual" or "realized".
- **main.tex L168**: "our verified-CF mechanism (\S\ref{sec:method:verified}) **is in the third family but verifies in the \emph{exact training simulator}** (zero modeling error) on an \emph{action sequence} rather than a hindsight goal." — works, but the closing "rather than a hindsight goal" hangs awkwardly given "verifies in" and "on an action sequence". Reads better as "… verifies an *action sequence* in the *exact training simulator* (zero modeling error) rather than a hindsight goal."
- **main.tex L191–193**: "VLM-RB-style success-scoring scheme: VLM-RB's signal is non-actionable for relabeling, ours is." — comma splice; should be a semicolon or a period.
- **main.tex L399–400**: "the three-model evidence is properly read as two-vendor (Opus/Sonnet share Anthropic lineage)." — slightly clipped; expected "is properly read as two-vendor evidence" (missing noun).
- **main.tex L444**: "18 SAC+HER and 18 Oracle-CF runs (3 envs $\times$ 3 seeds $\times$ 250k steps) executed overnight." — "executed overnight" reads as passive; for cleaner academic register either "were executed overnight" or "we executed overnight".
- **main.tex L494**: "Fetch is known to be ``HER-friendly'' because the achieved-future relabel is essentially a free signal whenever the gripper-to-object distance is monotone, which it typically is on Push and PickAndPlace." — "which it typically is" is colloquial; "which is typically true on …" reads more formally.
- **appendix.tex L168**: "Three findings transfer to production:" — there is no "production" in the paper; the runs are simulation experiments. Suggest "Three findings carry over from synthetic to real-failure data" or similar.
- **appendix.tex L180**: "Plausibility shifts only $\pm 0.07$ synthetic-to-real" — "shifts" with "$\pm$" is technically OK but awkward; "differs by only $\pm 0.07$" reads cleaner.

## Punctuation

- **main.tex L24**: "Daniel Grant \quad Parshawn Gerafian \quad Matei Gardea" — no terminal punctuation in author list (standard for NeurIPS — fine, just noting).
- **main.tex L70**: "\emph{exceeding} it on FetchSlide ($0.617$ vs.\ $0.55$;" — em-dash and `vs.\` look consistent throughout. OK.
- **main.tex L139**: "The mechanism instantiates the \emph{generator--verifier} paradigm" — uses `--` (en-dash) inside `\emph{}`. Renders correctly in PDF (en-dash) but typographically a true em-dash (`---`) is conventional in en-US prose; en-dash for ranges is fine here since "generator--verifier" is a coordinate compound. Consistent with rest of paper (L313 same usage). OK.
- **main.tex L262**: "A corrective signal admits four output types along two axes---\emph{output kind}" — em-dash here, good. But L398 "the failure is \emph{prompt-architectural}, not model-specific. The load-bearing" — period after `\emph{}` should be outside the emphasis. Currently `\emph{prompt-architectural},` puts the comma inside `\emph`, which is OK in LaTeX but flagged by some style guides.
- **main.tex L378**: "(see Contributions)." — "Contributions" is unlabeled section name; consider `\S\ref{sec:contributions}` for consistency with all other section refs.
- **main.tex L487**: "\paragraph{Oracle-CF kill bounds the headroom.}" — `\paragraph` body uses inline em-dashes nowhere; consistent.
- **appendix.tex L19**: `\{``failure\_frame\_index'': $i$, ``reasoning'': $s$\}.` — closing period inside the `\texttt{...}` group, after the `\}`. Trailing period inside monospace is intentional? In rendered PDF (p8) the period sits inside the code font, which looks odd. Consider moving the period outside the `\texttt{}` envelope.

## LaTeX issues

- **main.tex L41**: `<\!1\%$ of episodes` — `\!` (neg thinspace) inside math is fine. Used widely (L237, L246, L330, etc.) consistently. OK.
- **main.tex L131**: `\texttt{(GPT-4o, achieved\_goal)}` — inside text-mode parentheses, correct.
- **main.tex L229**: `[1 + (w_{\max}\!-\!1)\,\mathbb{1}[|i-t^\star|\le W]]` — outer `[ ]` is inside `\mathbb{E}_{...}[ ... ]` which already creates a bracket; double-bracket nesting renders correctly but visually is dense. Cosmetic.
- **main.tex L246**: `C(w_{\max}^{\beta_t}-1)((2W+1)/T)\|\ell\|_\infty` — exponent `\beta_t` appears later (Appendix L81, L86) with same notation. Consistent.
- **main.tex L274**: `q_\phi(\hat{p}\!\mid\!\tau)=\delta(\hat{p}-g)` — overloads `\delta` (also used for TD-error elsewhere, e.g., L216 `\delta_i`). Reader may briefly confuse with TD-error symbol; consider `\boldsymbol{\delta}(\cdot)` or note that this is the Dirac delta. Minor.
- **main.tex L301–302**: `\texttt{final\_distance} (0.32\,m, 0.16\,m); (iii) a hand-crafted close-goal action is verified with $\text{final\_distance}\!=\!0.030$\,m` — inconsistent typography: same field name as `\texttt{final\_distance}` then as `\text{final\_distance}` in math mode. Pick one.
- **main.tex L334**: `$\le\!\$0.05$/call` — the `\!` and `\$` work but `\$` inside math mode is a literal $ sign; the slash after `$` ends math mode. Renders OK in PDF (p4). OK.
- **main.tex L383**: subsection title "Prompt design (head-to-head)" — uses parens in a section header; in NeurIPS template subsection capitalization is title case; "design" lowercase is title-case "Prompt Design (Head-to-Head)" if going strict. Currently sentence-case used here AND in section "Cross-task transfer and real-data validation" (L427), "Pre-registered Oracle-CF kill experiment" (L441). Sentence-case consistent across all subsections — that's actually a choice, just verify it's intentional vs the title-case "Headline: Verified-CF matches VLM-CF, wins on Slide" (L357) which is also sentence-case-ish but capitalises "Verified-CF" and "VLM-CF". Internally consistent.
- **appendix.tex L17–19**: math (`$\in\{...\}$`, `$i$`, `$s$`) embedded in `\texttt{}` block causes Underfull warnings — see Typos/Build.log items.
- **appendix.tex L110–143 (Table 2)**: tabular `{l l l}` content has rows that overrun text width by 20.85pt → `Overfull \hbox`. Likely culprit is the "Twin-Q critic; tanh-squashed Gaussian actor" Notes column on the SAC row or "Adam, default $(\beta_1,\beta_2,\varepsilon)$" / "10k warm-up uniform-random". Must-fix for camera ready.

## Math / equation issues

- **main.tex L41**: Inline `$<\!1\%$` — the `\!` tightens but actually `\%` already has a thin space. Renders fine on p1.
- **main.tex L229**: `\mathbb{1}[|i-t^\star|\le W]` — double brackets `]` and `]` in `\mathbb{E}[...]` and the indicator's `[...]` are adjacent. Looks crowded; consider `\mathbf{1}\{|i-t^\star|\le W\}` (set-style) for clarity. Cosmetic.
- **main.tex L245–247**: bias bound `|\widehat{\mathcal{L}}_{\text{under}} - \mathcal{L}_U| \le C(w_{\max}^{\beta_t}-1)((2W+1)/T)\|\ell\|_\infty` is inline; the same equation appears as Eq.~(\ref{eq:bias-bound}) in Appendix B (numbered). Consistent statement, but inline-vs-display dual presentation is fine.
- **Eq. numbering**: Two equations total — (1) `eq:headline` and (2) `eq:bias-bound`. Eq.(1) is never referenced by `\ref{eq:headline}` anywhere in the text (search: only its definition). Either drop the label or add a forward reference like "Eq.~(\ref{eq:headline})" in text. Minor.
- **main.tex L271**: `\|\text{ag}_T-g\|_2\gg d_{\text{th}}\!=\!0.05$\,m` — the L2 subscript on `\|...\|_2` is fine; elsewhere (L326 `\|\text{ag}_t-g\|`) the norm has no subscript. Inconsistent norm notation. Pick one.
- **main.tex L300–302**: smoke test deltas: "(0.32\,m, 0.16\,m)" — two distances without symbols; further down "$\text{final\_distance}\!=\!0.030$\,m". Numbers `0.32`, `0.16`, `0.030` have inconsistent decimal places (2, 2, 3). Standardize to e.g. `0.320`, `0.160`, `0.030`.
- **main.tex L361, 365, 367**: bold-prefixed numerals `$0.95\!\pm\!0.03$`, `$0.85\!\pm\!0.14$`, etc. — consistent 2-decimal SE notation. Good.
- **main.tex L455**: "Oracle-CF mean $0.583$ ($n\!=\!3$) and HER mean $0.583$ ($n\!=\!3$; seeds $0.35/0.45/0.95$)" — the trailing "seeds 0.35/0.45/0.95" is ambiguous (means seed-id 0.35/0.45/0.95? or per-seed success rates 0.35, 0.45, 0.95?). Should clarify: e.g., "(seed successes: 0.35, 0.45, 0.95)".

## Table / figure issues

- **Table 1 (main.tex L411–425)**: tabular spec `{ll cccc}` — five columns of bullets (Variant, Model, $n$, Plausibility, Goal-progress, Teleport-collapse) = 6 columns total. Spec has `ll` + `cccc` = 6 columns. OK.
  - Last row L422: `$4/6\ (67\%)$` while L419 uses `$4/4$ (100\%)` outside math mode. Mixed math/text for the percentages. Make consistent.
  - L420 bolds the entire row label `\textbf{\textsc{achieved\_goal}}` and `\textbf{GPT-4o}` — works but visually heavy; this is the highlighted "best" row. OK if intentional.
  - L415–422 column "Teleport-collapse": four rows are `---` (narrative/action have no position output to teleport). Caption should note that `---` means "N/A" so the reader doesn't read it as "0 / N samples". Add to caption: "—: not applicable (variant emits no goal-position field)."
- **Table 2 (appendix.tex L103–143)**: Overfull hbox 20.85pt (see Build.log). On p10 render, the table extends past the right margin (visible). Must-fix.
  - Caption L106: "Headline hyperparameters. Full per-table breakdowns (SAC architecture, HER strategy, PER schedule, Semantic-PER, Verified-CF, VLM call) at the GitHub repo (\texttt{configs/})." — "per-table" is unusual; do you mean "per-component" or "complete"?
- **Figure 1 (main.tex L343–355)**: caption begins "**Final evaluation success rate across the three Fetch tasks (mean $\pm$ SE, $n\!=\!3$ seeds; individual seeds overlaid).**" — readable. Last sentence: "Within-horizon comparisons (same stamp) are statistically meaningful; cross-horizon comparisons should be read as efficiency claims." — minor: "(same stamp)" parenthetical interrupts flow; could move to end.
  - Figure caption mentions "italic gray stamp under each bar" — in the rendered PDF the horizon stamps are visible but the labelling "Uniform/PER at 3M" appears under all bars including HER (250k). Per-bar stamps are present.
  - Legend shows "HER reference (250k)" and "HER (250k)" — two entries with similar names? Confirm these are different series (one is per-task HER baseline, other is HER@250k reference dashed line). Visually distinguishable in render but legend names may confuse readers.
- **Figure 2 (appendix.tex L48–58)**: caption is clear. OK.

## Numeric / consistency issues

- **main.tex L71 + L369**: "$+0.45$ over PER@3M" — **likely numeric error**.
  - FetchSlide verified-CF = 0.617 (L367).
  - PER@3M on Slide = 0.10 (L370).
  - Actual delta = 0.617 − 0.10 = **0.517**, not 0.45.
  - HER@250k on Slide = 0.183. Delta = 0.617 − 0.183 = 0.434 ≈ **0.43** — matches "+0.43 over HER@250k".
  - So either the +0.45 number is wrong (should be ~+0.52), or the labels on the two deltas are swapped (i.e., +0.43 is over PER@3M and the +0.45 is over a different baseline). Must reconcile. This duplicates in the Extended Abstract (L71) — both copies need fixing.
- **main.tex L66–71** vs **L520–522**: "verified-CF agent reaches mean $0.606$ across the three Fetch envs ($0.85/0.35/0.617$)" — average of 0.85, 0.35, 0.617 = 0.6057 → rounds to 0.606. OK.
- **main.tex L373**: "vlm\_cf reaches $0.622$ ($\Delta\!=\!-0.016$)" — 0.606 − 0.622 = −0.016. OK.
- **main.tex L455**: "HER mean $0.583$ ($n\!=\!3$; seeds $0.35/0.45/0.95$)" — average of 0.35, 0.45, 0.95 = 1.75/3 ≈ 0.583. OK (assuming "seeds X/Y/Z" means per-seed success rates).
- **main.tex L304**: "per-verification CPU cost is 17.6\,ms (a $0.4\%$ overhead)." vs **appendix L152**: "Snapshot round-trip latency for the verifier is 17.6\,ms per call (a $0.4\%$ overhead at $\sim\!1700$ failed episodes / 100k steps)." — consistent. Good.
- **main.tex L457–458**: "vlm\_cf@500k ($0.367$) reaches 63\% of HER@1M's asymptote at half the budget." — 0.367/0.583 = 0.629 ≈ 63%. OK.
- **main.tex L86**: "100\% verifier-rejection over the first $\sim\!80$ VLM calls" — matches abstract / discussion. OK.
- **main.tex L304**: smoke-test final-distances `0.32\,m, 0.16\,m, 0.030\,m` — decimal-place inconsistency (see Math).
- **Push baseline**: L450 says "HER $0.550$" but L361 (extended abstract earlier) mentions HER@250k Push = $0.617$. Are these two different HER measurements? L370 says HER@250k=$0.617$ but in §4.4 the Oracle-CF kill table cites "HER $0.550$" on Push. Confirm two different HER runs or fix one — readers will catch this.
  - Looking again, L450 caveats "(post bug-fix, commit \texttt{ccb63d4})". So the 0.550 is a separate "post bug-fix" HER value; the 0.617 elsewhere is a different reference number. Worth a clarifying clause: e.g., "HER $0.550$ on Push (post bug-fix HER, single-seed; cf. the multi-seed $0.617$ reference in §4.1)" so readers don't double-take.
- **main.tex L21 thanks footnote**: "CS 285 Final Project, Spring 2026. UC Berkeley, Department of EECS." — title page footnote uses period after EECS. Fine.

## Consistency issues

- **Capitalisation: Verified-CF vs verified-CF**
  - Capital "Verified-CF" used in section titles (L357), appendix table label (L132), table caption (appendix L107), and at start of sentence.
  - Lowercase "verified-CF" used mid-sentence (L67, L84, L168, L279, L372, L379, L482, L505, L520, etc.).
  - Mostly consistent (sentence-case rule), but L66 "Verified-CF matches VLM-CF in aggregate" is mid-sentence after "(i)" — capitalisation OK as it's a list-item lead-in. Confirm rule is "capital iff sentence start or in heading", which is what's currently applied.
- **Hyphenation: `vlm_cf` vs `VLM-CF`**
  - `\emph{vlm\_cf}` is the code/buffer name (L67, L364, L373, etc.).
  - `VLM-CF` (capital, hyphen) used in prose (L66, L69, L74, L357, L521).
  - Internally consistent: prose VLM-CF, code `\emph{vlm\_cf}`. Good. But L373–374 mixes both in one paragraph ("vlm\_cf reaches $0.622$ … Verified-CF \emph{exceeds} vlm\_cf"); a reader may infer they're different things. Consider always-prose "VLM-CF" outside code blocks.
- **Model name spacing: `Opus 4.7` vs `Opus~4.7`**
  - `Opus~4.7` (non-breaking) at L60, L77, L132, L143, L277, L333.
  - `Opus 4.7` (regular space) at L143, L387, L409, L415, L417, L419, L421 (Table 1).
  - Table column is fine (space inside cell). But L143 vs L387 both regular text; inconsistent. Standardize to `Opus~4.7` (or `Claude Opus~4.7`) throughout.
- **`Sonnet~4.5` vs `Sonnet 4.5`**: L77, L147, L333, L437, L399 all use `Sonnet~4.5`. Consistent. Good.
- **`Claude Opus 4.7` vs `Opus 4.7`**: L132 "Claude Opus 4.7 calls", L143 "Claude Opus 4.7", L332 "Claude Opus 4.7", L409 "Claude Opus 4.7" — full name "Claude Opus 4.7" used when first introducing; later just "Opus 4.7" / "Opus~4.7". Standard practice. OK.
- **Number formatting**:
  - SE values: 2 decimals (`0.03`, `0.14`, `0.117`) — mostly. L448 has `0.117` (3 decimals); L361 has `0.03` (2 decimals); L365 has `0.08`, `0.10`. Mixed but OK if number of decimals tracks the SE magnitude.
  - Success rates: `0.617`, `0.183`, `0.367`, `0.95`, `0.85`, `0.35`, `0.55`, `0.622`, `0.606`. Mixed 2- and 3-decimal. Standardize to 3 decimals for the headline (so `0.95` → `0.950`, `0.55` → `0.550`).
  - Percentages: `100\%`, `75\%`, `67\%`, `60\%`, `5\%`, `63\%` — all integer percent, consistent. Good.
- **Currency**: `$\le\!\$0.05$/call` (L334), `\$80` (appendix L150) — consistent `$` rendering inside math.
- **Norm notation**: `\|\text{ag}_T-g\|_2` (L271) vs `\|\text{ag}_t-g\|` (L326, no subscript). Pick one (recommend explicit `\|\cdot\|_2`).
- **TeX-quotes**: `\`\`text''` used throughout (L113, L181, L494, appendix L19, L24, L25, L26, L201, L202, L203). All correctly use back-tick-pair opening and apostrophe-pair closing. **One exception**: appendix L201 `\emph{"strike direction off-axis"}` — uses straight ASCII quotes inside `\emph{}` rather than ``\`\` ... '' `` style. Replace with curly TeX quotes. Three quoted phrases in the same paragraph (L199–202) are all affected:
  - L200: `\emph{"gripper passes over block without making contact"}` — ASCII straight quotes
  - L201: `\emph{"gripper at block location but fails to close"}` — same
  - L202: `\emph{"strike direction off-axis"}` — same
  These will render as straight ASCII quotes in PDF (visible on p11 — confirmed). Must-fix to NeurIPS-style curly quotes.
- **Acronym definitions on first use**:
  - VLM: defined L113 "Vision-Language Models (VLMs)". Good.
  - HER: defined L42–43 in abstract ("Hindsight Experience Replay (HER)"). Good.
  - PER: defined L43 ("standard PER") in abstract but full name first appears L103 "Prioritized experience replay (PER)". Backwards order — abstract uses PER before defining it. Standard practice in extended abstracts that immediately precede an intro, but pedantically first-use should be defined in the abstract.
  - SAC: first appears L67 ("SAC+HER+verified-CF"), but defined only L327 "SAC \citep{haarnoja2018sac}". Define "Soft Actor-Critic (SAC)" on first abstract mention.
  - CF: never explicitly defined — "Oracle-CF", "VLM-CF", "verified-CF" appear from L66 onward; CF should be expanded to "counterfactual" on first use, e.g., "Oracle counterfactual (Oracle-CF)".
  - IS: "IS-correction" (L55), "IS-posterior" (L75, L90, etc.) — never spelled out. Add "importance-sampling (IS)" on first appearance.
  - TD: "TD-error" (L43, L44, L57) — never spelled out. Add "temporal-difference (TD)" on first use.
  - SE: "mean $\pm$ SE" — never spelled out. Add "standard error (SE)" on first appearance (L332 or earlier).
  - PnP: appendix L43 "Push/PnP drop-offs" — abbreviation for PickAndPlace; only place it appears. Either spell out "Push/PickAndPlace" or define "PnP" earlier.
- **Section reference style**: `\S\ref{...}` used throughout consistently. Good.
- **Author affiliations**: single-affiliation, all three authors. Consistent.

## Other observations

- **main.tex L21** `\thanks{CS 285 Final Project, ...}` is on the title; renders as footnote on p1 (visible). Good.
- **main.tex L457**: "vlm\_cf@500k" — uses `@` shorthand for "at N steps". This shorthand is introduced silently; first time it appears in L66 "HER@250k" / "PER@3M". Consider noting "@N denotes evaluation at N training steps" once.
- **main.tex L539**: "produced all paper figures and the manuscript." — Daniel Grant's contribution. Standard. OK.
- **main.tex L527**: "The IS-posterior framing and the simulator-as-verifier guarantee stand independently of any single training outcome." — strong closing statement; reads well.
- **No abstract section**: paper uses `\section*{Extended Abstract}` instead of `\begin{abstract}…\end{abstract}`. For NeurIPS template (`neurips_2024.sty`) the standard is the `abstract` environment. The current structure renders fine but breaks the template's expected layout (no italic / narrowed-margin abstract block). Verify this is intentional for the CS285 variant.
- **References**: bibliography appears clean (no `??` placeholders in PDF). All 22 citations resolved.

## Total: 64 issues found. 5 must-fix before submission.

**Must-fix (5):**
1. PDF/source out of sync — rebuild with `fig_headline_v5.pdf` (currently embeds v4).
2. Table 2 (appendix) `Overfull \hbox 20.85pt` — table extends beyond right margin.
3. Likely numeric error: "+0.45 over PER@3M" on Slide is inconsistent with 0.617 − 0.10 = 0.517 (appears in L71 abstract AND L369 main text — both copies need reconciling).
4. ASCII straight quotes in `\emph{"…"}` on appendix L200–202 (three phrases) must become curly TeX quotes.
5. Appendix prompt template (L17–19) embeds math (`$\in\{0,…,K-1\}$`, `$i$`, `$s$`) inside `\texttt{}` block — causes 5 Underfull warnings and visibly distorted typography on p8. Rewrite without math mode, or use `verbatim`/`lstlisting`.

**Should-fix (high value, ~10):**
- Define acronyms on first use: SAC, CF, IS, TD, SE, PER (in abstract).
- Norm notation: pick `\|\cdot\|_2` or `\|\cdot\|` and standardize (L271 vs L326).
- `final_distance` typography (`\texttt` vs `\text`) on L301–302.
- Mid-text comma splice (L191–193).
- Standardize success-rate decimal places (3 decimals throughout headline numbers).
- Clarify HER Push values: 0.617 (§4.1) vs 0.550 (§4.4) need a one-line cross-ref.
- `Opus~4.7` vs `Opus 4.7` spacing — pick non-breaking everywhere outside tables.
- Eq.~(1) `eq:headline` is never referenced — either reference it in prose or drop the label.
- Footnote `0.35/0.45/0.95` (L455) — clarify these are per-seed success rates, not seed IDs.
- Table 1 caption — add `—: N/A` legend for the four dash entries.

**Nice-to-haves (~49):**
All remaining items listed above (cosmetic, hyphenation, capitalisation, parenthetical phrasing, hbox/vbox underfulls, etc.).
