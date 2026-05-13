# Pass 1/5 — P0 Data-Rigor Fixes (CS 285 paper)

**Date:** 2026-05-13
**Agent:** Opus 4.7
**Scope:** `agent_reports/paper_cs285/main.tex` + `appendix.tex` only
**Page count post-fix:** 11 pages (under 11pp ceiling; no change)
**Compile:** clean (zero undefined references, no new LaTeX warnings)

## Summary

All 6 fixes specified by the user brief were applied surgically against the verified W&B truth. Fix 6 (p_counterfactual in §6) was correctly absent from the CS 285 paper (confirmed via grep) and required no edit — only the Contributions list mentions `p_counterfactual` as work-done.

---

## Fix 1: HER@250k baseline reconciliation

### §5.1 (now correct everywhere)
- Push HER@250k: `0.617` (kept)
- PnP HER@250k: was `0.167` → **`0.183`** (W&B truth)
- Slide HER@250k: `0.183` (kept)

**main.tex:367 (before):**
```
(tied within noise), both above HER@250k ($0.167$).
```
**main.tex:367 (after):**
```
(tied within noise), both above HER@250k ($0.183$).
```

### §5.4 kill experiment (reconciled to §5.1 + W&B)

**main.tex:448-451 (before):**
```
$0.167\!\pm\!0.117$ vs.\ Oracle-CF $0.117\!\pm\!0.044$ ($\Delta\!=\!-0.05$,
\emph{below threshold}). On Push (post bug-fix, commit \texttt{ccb63d4}),
HER $0.550$ vs.\ Oracle-CF $0.383\!\pm\!0.109$. On Slide, HER $0.100$ vs.\
Oracle-CF $0.183$ ($\Delta\!=\!+0.083$, below threshold).
```
**main.tex:452-455 (after):**
```
$0.183\!\pm\!0.117$ vs.\ Oracle-CF $0.117\!\pm\!0.044$ ($\Delta\!=\!-0.066$,
\emph{below threshold}). On Push (post bug-fix, commit \texttt{ccb63d4}),
HER $0.617$ vs.\ Oracle-CF $0.383\!\pm\!0.109$. On Slide, HER $0.183$ vs.\
Oracle-CF $0.183$ ($\Delta\!=\!0.00$, below threshold).
```

Note: Slide HER (0.183) now equals Oracle-CF (0.183) — Δ = 0.00. The "below threshold" verdict still holds (kill rule was +0.10, and Δ=0.00 < +0.10), so the kill verdict is preserved. PnP Δ updated from `-0.05` to `-0.066` (= 0.117 - 0.183).

The HER SE of ±0.117 was preserved as-is — the user instruction was to reconcile means to W&B truth, not to recompute SE for baseline cells (only the 6 headline cells were flagged for SE recomputation in Fix 2).

## Fix 2: SE values recomputed from per-seed numbers (ddof=1, √n=√3)

Per Agent 04's per-seed audit:
- `verified_cf` Push (seeds 0.65, 0.90, 1.00): SE = 0.1041 → **0.10**
- `verified_cf` PnP (seeds 0.25, 0.30, 0.50): SE = 0.0764 → **0.076**
- `verified_cf` Slide (seeds 0.60, 0.65, 0.60): SE = 0.0167 → **0.017**
- `vlm_cf` Slide: SE = 0.150 → **0.15**

**main.tex:361 (before / after):**
```
- $0.85\!\pm\!0.14$
+ $0.85\!\pm\!0.10$
```
**main.tex:365 (before / after):**
```
- $0.35\!\pm\!0.10$
+ $0.35\!\pm\!0.076$
```
**main.tex:368 (before / after):**
```
- $0.617\!\pm\!0.03$ and \emph{vlm\_cf} reaches $0.55\!\pm\!0.13$
+ $0.617\!\pm\!0.017$ and \emph{vlm\_cf} reaches $0.55\!\pm\!0.15$
```

vlm_cf Push (±0.03) and PnP (±0.08) were left unchanged — Agent 04 confirms those round correctly from the W&B per-seed numbers.

## Fix 3: Clopper–Pearson "disjoint" → Fisher's exact

The 0/6 vs 4/4 CP intervals overlap (0.398–0.459), so "disjoint" is mathematically false. Replaced in both files.

**main.tex:397-398 (before):**
```
predicate) and the Clopper--Pearson intervals on the two cells are
disjoint at $\alpha\!=\!0.05$.
```
**main.tex:399-400 (after):**
```
predicate) and Fisher's exact test rejects equal-proportions at
$p\!<\!0.005$.
```

**appendix.tex:190-193 (before):**
```
is decided by Euclidean predicate (judge-independent) and the
Clopper--Pearson intervals on the two cells are disjoint at
$\alpha\!=\!0.05$.
```
**appendix.tex:190-192 (after):**
```
is decided by Euclidean predicate (judge-independent) and Fisher's
exact test rejects equal-proportions at $p\!<\!0.005$.
```

## Fix 4: Mixed-method delta attribution disambiguated

Each delta now attributed to its source method explicitly.

**Extended Abstract (main.tex:70-71, before):**
```
and \emph{exceeding} it on FetchSlide ($0.617$ vs.\ $0.55$;
$+0.45$ over PER@3M, $+0.43$ over HER@250k); Fig.~\ref{fig:headline}.
```
**(after):**
```
and \emph{exceeding} it on FetchSlide ($0.617$ vs.\ $0.55$, where
\emph{vlm\_cf} gains $+0.45$ over PER@3M and \emph{verified\_cf} gains
$+0.43$ over HER@250k); Fig.~\ref{fig:headline}.
```

**§5.1 (main.tex:368-371, before):**
```
$0.617\!\pm\!0.03$ and \emph{vlm\_cf} reaches $0.55\!\pm\!0.13$---a
$+0.45$ gain over PER@3M ($0.10$) and $+0.43$ over HER@250k ($0.183$),
on the task where prior baselines cluster near zero.
```
**(after):**
```
$0.617\!\pm\!0.017$ and \emph{vlm\_cf} reaches $0.55\!\pm\!0.15$---on the
task where prior baselines cluster near zero, \emph{vlm\_cf} gains
$+0.45$ over PER@3M ($0.10$) and \emph{verified\_cf} gains $+0.43$ over
HER@250k ($0.183$).
```

## Fix 5: "Sonnet 75% → 0% teleport" rephrased

The 75% baseline was Opus, not Sonnet; reader would mis-read as a within-Sonnet improvement.

**main.tex:437 (before):**
```
prompt-architectural fix transfers to a third VLM family
(Sonnet~4.5: 75\%~$\to$~0\% teleport on PickAndPlace) and that the 5\,cm
```
**main.tex:438-441 (after):**
```
prompt-architectural fix transfers to a third VLM family
(Sonnet~4.5 teleports on $0/6$ PickAndPlace episodes under
\textsc{achieved\_goal}, vs.\ Opus~4.7's $4/4$ on the same variant) and
that the 5\,cm
```

This aligns with the appendix L171 phrasing ("Opus teleports at 75% but Sonnet drops to 0%") which is already correctly attributed.

## Fix 6: p_counterfactual §6 stale claim — NOT PRESENT IN CS 285 PAPER

Confirmed via `grep -n "p_counterfactual\|p_{CF}\|p\\_CF" main.tex appendix.tex`:

Only one hit:
```
main.tex:540: $p_{\text{counterfactual}}$ sweep, baselines calibration, HER@1M
```

This is in the Contributions section as a "work done" note — not a stale data claim. No edit required. Agent 04's audit confirms this was a sibling-paper issue.

---

## Verification

### Page count
- **Before:** 11 pages
- **After:** 11 pages (no change — edits were micro and balanced)

### Compile
- `bash build.sh` produces `main.pdf` with zero undefined references and no new LaTeX warnings.
- Visual gate: pages 1, 4, 5, 7, 8, 11 inspected — all corrected numbers render cleanly.

### Sanity check on math
```
vCF Push   seeds [0.65, 0.90, 1.00]  -> mean 0.85,    SE 0.1041 (round 0.10)  ✓
vCF PnP    seeds [0.25, 0.30, 0.50]  -> mean 0.35,    SE 0.0764 (kept 0.076)  ✓
vCF Slide  seeds [0.60, 0.65, 0.60]  -> mean 0.617,   SE 0.0167 (kept 0.017)  ✓
```

---

## Concerns flagged for Pass 2

### Internal consistency caveats (data-side, not citation-side, but flagging for awareness)

1. **§5.4 PnP HER SE = ±0.117 was preserved as-is** even though the mean was changed from 0.167 → 0.183. The SE was not in the verified W&B table per Agent 04. If Pass 2+ finds a source-of-truth for the HER@250k per-seed values on PnP, the SE may need a refresh. This is a "MED" priority issue per Agent 04, not a blocker.

2. **§5.4 Oracle-CF @250k values** (`0.117±0.044` PnP, `0.383±0.109` Push, `0.183` Slide) remain unverified against the supplied W&B table. Agent 04 noted these as "[MED]" — needing artifact/run-ID. Pass 2 may want to either:
   - Add a footnote citing the originating sweep (commit/run-ID)
   - Or treat these as deferred to Pass 4 (rubric upgrades) if a verified source is identified.

3. **No "statistical significance" claims** were introduced; all numeric reporting uses mean ± SE language. The single borderline phrase ("Within-horizon comparisons (same stamp) are statistically meaningful" at main.tex:347 / figure caption) was flagged by Agent 04 as LOW priority and left intact this pass — Pass 4 (rubric upgrade) may want to tone this to "permit within-noise comparison" or similar. Did not touch this pass to stay surgical.

### Hard guardrails preserved

- Extended Abstract still 1 page (page 1).
- `fig_headline_v5` still present.
- Verified-CF numbers (Push 0.85, PnP 0.35, Slide 0.617, mean 0.606) intact.
- vlm_cf numbers (Push 0.95, PnP 0.367, Slide 0.55, mean 0.622) intact.
- §1 contribution bullets intact.
- §6 transitory cold-start (§5 here, "Cold-start verifier-rejection regime" paragraph) intact.
- Contributions section intact (per-member).
- Baselines (HER, PER, Oracle-CF, vlm_cf, verified_cf) all still cited.
- "Why method works" passage ("Why does verified-CF pay off on Slide?") intact.

---

## Hand-off note

**Pass 2 should focus on citations per `_FEEDBACK_AGENT_09_citations.md`.**

Specific items still pending after Pass 1:
- (MED) Add artifact citation / run-ID for §5.4 Oracle-CF @250k numbers (0.117±0.044, 0.383±0.109, 0.183).
- (LOW) Consider toning "statistically meaningful" in fig:headline caption (main.tex:347).
- (LOW) Consider folding the n=2 Opus 4.7 `\textsc{all}` row in Table 1 into a footnote.

No citation-related changes were made in Pass 1.
