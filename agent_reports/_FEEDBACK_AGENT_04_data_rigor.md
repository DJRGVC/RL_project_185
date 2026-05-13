# Agent 04 — Data Rigor Audit

Paper: `agent_reports/paper_cs285/main.tex` (556 lines) + `appendix.tex` (250 lines).
Verified against W&B data table supplied in tasking. Read-only.

Note on scope: the user brief referenced a §6 (vii) p_counterfactual claim at "line ~1700" — that paragraph does **not exist in this paper**. This 556-line `paper_cs285/main.tex` has no §6, no enumerated limitation list (vii), and no p_counterfactual claim in the body. The only mention of `p_counterfactual` is in the Contributions list (L536) describing work done. The "L1700 §6 (vii)" issue must be in the sibling `agent_reports/paper/main.tex` — out of scope here. **No STALE p-sweep claim found in this file.**

---

## Verified-correct claims (✓)

| File:Line | Claim | Verification |
|---|---|---|
| `main.tex:69` | verified-CF mean 0.606 across 3 envs | (0.85+0.35+0.617)/3 = 0.6057 ≈ 0.606 ✓ |
| `main.tex:69` | per-env (0.85 / 0.35 / 0.617) on Push/PnP/Slide | matches W&B means exactly ✓ |
| `main.tex:69-70` | vlm_cf mean 0.622, Δ = −0.016 | (0.95+0.367+0.55)/3 = 0.6223; 0.6057−0.6223 = −0.0166 ≈ −0.016 ✓ |
| `main.tex:71` | Slide: verified_cf 0.617 vs vlm_cf 0.55 | matches W&B ✓ |
| `main.tex:360` | vlm_cf Push 0.95±0.03 | mean 0.95 ✓; SE 0.05/√3 ≈ 0.029 ✓ |
| `main.tex:361` | verified_cf Push 0.85 | mean 0.85 ✓ (SE flagged below) |
| `main.tex:364-365` | vlm_cf PnP 0.367 | matches ✓ |
| `main.tex:365` | verified_cf PnP 0.35 | matches ✓ |
| `main.tex:367-368` | verified_cf Slide 0.617 | matches ✓ |
| `main.tex:368` | vlm_cf Slide 0.55 | matches ✓ |
| `main.tex:373-374` | aggregate means 0.606 / 0.622; Δ=−0.016 | recomputed ✓ (also restated in §6 L520) |
| `main.tex:454-456` | Oracle-CF@1M PnP mean 0.583 (n=3) | (0.30+0.90+0.55)/3 = 0.5833 ✓ |
| `main.tex:456` | HER@1M PnP mean 0.583, seeds 0.35/0.45/0.95 | matches W&B exactly ✓ |
| `main.tex:458` | vlm_cf@500k (0.367) = 63% of HER@1M asymptote | 0.367/0.583 = 0.629 ≈ 63% ✓ |
| `main.tex:458` | "half the budget" (500k vs 1M) | ✓ |
| `main.tex:363` | PER@3M Push ~0.95 | matches W&B (0.95) ✓ |
| `main.tex:369` | PER@3M Slide 0.10 | matches W&B (0.10) ✓ |
| `main.tex:370` | HER@250k Slide 0.183 | matches W&B Phase-1 number ✓ |
| `main.tex:363` | HER@250k Push 0.617 | matches W&B Phase-1 ✓ |
| `main.tex:419-420` | Opus 4/4 vs GPT-4o 0/6 teleport on achieved_goal | matches §3 of brief and table ✓ |
| `main.tex:438` | gate fires 12/20 position-emitting | self-consistent with appendix L178 (60%) ✓ |
| `appendix.tex:152` | snapshot round-trip 17.6 ms / 0.4% overhead | matches paper L304 ✓ |
| `main.tex:304` | per-verification CPU cost 17.6 ms | (self-consistent; not in W&B table but internally consistent) |

---

## ❌ WRONG / 🔄 STALE claims

### CRITICAL — HER@250k PnP value disagreement

The paper uses **two different values for HER@250k on FetchPickAndPlace** in two sections, and only one matches the verified W&B data:

- **`main.tex:366`** (Headline §5.1): "both above HER@250k (`0.167`)" — for PnP — does **NOT** match verified W&B (`0.183`). ❌ Off by −0.016.
- **`main.tex:448`** (Kill experiment §5.4): "HER `0.167`±0.117 vs. Oracle-CF 0.117±0.044 (Δ=−0.05)" — same wrong number.
- **Brief states**: "HER@250k (Phase 1): Push 0.617, PnP **0.183**, Slide 0.183 (per Plappert+DDPG comparison)".
- Either the kill-experiment PnP number is the correct one (and the W&B aggregate is the wrong reference), or 0.183 is correct and §5.1+§5.4 are stale. **Authors must reconcile.**

### CRITICAL — HER@250k Push disagreement between §5.1 and §5.4

- **`main.tex:363`** (Headline): "matching the PER@3M asymptote (~0.95)" *and* "substantially above HER@250k (0.617)" — uses **0.617** for HER Push@250k (matches verified W&B). ✓
- **`main.tex:450`** (Kill experiment): "On Push (post bug-fix, commit `ccb63d4`), HER `0.550` vs. Oracle-CF 0.383±0.109" — uses **0.550** for HER Push@250k. ❌ Inconsistent with both §5.1 and the W&B table.

### CRITICAL — HER@250k Slide disagreement between §5.1 and §5.4

- **`main.tex:370`** (Headline): "+0.43 over HER@250k (0.183)" — uses **0.183**, matches W&B. ✓
- **`main.tex:450-451`** (Kill experiment): "On Slide, HER `0.100` vs. Oracle-CF 0.183 (Δ=+0.083)" — uses **0.100** for HER Slide@250k. ❌ Conflicts with §5.1 and with W&B (`0.183`).
  - **Bonus problem**: if HER Slide = 0.183 (per verified data) and Oracle-CF Slide = 0.183, the Δ=+0.083 vanishes and the Slide row becomes a tie, not a +0.083 "below threshold" entry.

### Mixed-method "+0.45 / +0.43" attribution (`main.tex:369-370`)

> "verified_cf reaches 0.617±0.03 and vlm_cf reaches 0.55±0.13---a **+0.45 gain over PER@3M (0.10) and +0.43 over HER@250k (0.183)**"

- +0.45 = 0.55 − 0.10 → refers to **vlm_cf** (0.55)
- +0.43 = 0.617 − 0.183 → refers to **verified_cf** (0.617)

Each clause is internally correct but the two clauses describe **different methods** within the same sentence. This is misleading — a reader naturally attributes both deltas to the same method. Either pick one method for both deltas, or split into two sentences. The abstract's L71 repeats the same defect.

### `verified_cf` Push SE = 0.14 — number unverifiable from verified-data std

- **`main.tex:361`**: "`verified_cf` reaches 0.85±0.14"
- Per-seed: 0.65, 0.90, 1.00 → mean 0.85, sample-std (ddof=1) = 0.1803, SE = 0.1803/√3 ≈ **0.104**
- Paper says **0.14** — 35% larger than the standard SE calc.
- Possibilities: (a) using a different denominator, (b) bootstrap SE, (c) typo for 0.10 or 0.11. Either way, the convention should be uniform across all six (method, env) cells; flag for the authors to recompute uniformly.

### `verified_cf` Slide SE = 0.03 — too small

- **`main.tex:368`**: "verified_cf reaches 0.617±0.03"
- Per-seed: 0.60, 0.65, 0.60 → mean 0.6167, sample-std = 0.0289, SE = 0.0289/√3 ≈ **0.017**
- Paper says **0.03** — about 2× the standard SE. Again, possibly a different convention. **Apply uniformly.**

### `verified_cf` PnP SE = 0.10 — too large

- **`main.tex:365`**: "verified_cf reaches 0.35±0.10"
- Per-seed: 0.25, 0.30, 0.50 → mean 0.35, sample-std (ddof=1) ≈ 0.132, SE ≈ **0.076**
- Paper says **0.10** — 30% larger than the standard SE.

### `vlm_cf` SE values closer but still off

- L360 Push 0.95±**0.03** — SE recomputed 0.029. ✓ rounds OK.
- L365 PnP 0.367±**0.08** — SE recomputed 0.073. Mild rounding.
- L368 Slide 0.55±**0.13** — SE recomputed 0.150. Off by ~13%.

**Pattern**: SE values are inconsistent. Either there are different conventions per cell, or the headline numbers have been transcribed from an older calculation. **Recompute all six method×env SEs uniformly from the W&B per-seed numbers using ddof=1 and √n.**

### Sonnet 4.5 "75% → 0% teleport on PickAndPlace" (`main.tex:437`)

- Brief states C1v2 real-data result: "Sonnet 4.5 `0/6 PnP teleport`, 4/4 plausible".
- Paper claims a `75% → 0%` shift. The "0%" is supported by `0/6`. The "75%" baseline — for which prompt variant or for `all` vs `achieved_goal`? Appendix L171 explicitly says "Opus teleports at 75% but Sonnet drops to 0%". So "75% → 0%" is comparing **Opus** to **Sonnet** at the same prompt variant — but the text reads like a within-Sonnet improvement.
- ⚠️ Phrasing-level data hygiene issue. The 0% Sonnet PnP figure is supported; the 75% is an Opus figure being shown next to it. Reader will plausibly mis-read. Recommend explicit rewording: "Sonnet 0% vs Opus 75% on PnP" or similar.

---

## ⚠️ UNSUPPORTED claims (no W&B backing in supplied data table)

| File:Line | Claim | Status |
|---|---|---|
| `main.tex:448` | "HER 0.167±0.117 vs. Oracle-CF 0.117±0.044" | Oracle-CF@250k PnP `0.117±0.044` is not in the supplied W&B verified table at all. Need source. |
| `main.tex:450` | "Oracle-CF 0.383±0.109" on Push@250k | not in supplied table. |
| `main.tex:450-451` | "HER 0.100 ... Oracle-CF 0.183" on Slide@250k | Oracle-CF Slide 0.183 is plausible but unverified here. HER 0.100 contradicts the table value (0.183). |
| `main.tex:301-302` | smoke-test final_distance 0.32 m, 0.16 m, 0.030 m | These are smoke-test ad-hoc numbers; not in the W&B table. Internal documentation-only — fine if reproducible from code, but they should be traceable to a logged artifact. |
| `main.tex:304` | "~1700 failed episodes / 100k steps" (in 0.4% overhead claim, appendix L152) | denominator for the 0.4% overhead. Not verified. |
| `appendix.tex:163-166` | "real failures near-misses with final-distance ∈[0.06,0.34] m on Push and median 0.27 m on PnP" | not in supplied W&B table. Should be in a manifest somewhere. |
| `main.tex:434` | cross-task pilot keyframe agreement Slide 4/4, Push 3/4, PnP 2/4 | not in supplied W&B table. |
| `appendix.tex:181` | "Opus 0.50 → 0.55, Sonnet 0.70" action sign-flip rate | not in supplied W&B table. |
| `appendix.tex:148-150` | "≈6h SAC+HER, ≈9h SAC+HER+VLM-CF" wall-clock; "220 GPU-hours"; "$80 VLM-API" | reasonable but unverified. |

These are not necessarily wrong — they may live in artifacts not summarized in the supplied W&B table. But any claim that is not in a verifiable artifact should be either cited to a specific repo path or removed before submission.

---

## Statistical reporting issues

1. **n=3, df=2 is properly disclosed.** `appendix.tex:184-189` correctly states: "each (method, env) cell uses n=3 seeds (42, 123, 999); reported metrics are mean ± SE computed across seeds using the t-distribution with n−1=2 d.f. Statistical comparison statements use **non-overlapping SE intervals** as the threshold". ✓ This is honest and conservative.

2. **No claim of "statistical significance" anywhere.** Searched main.tex + appendix.tex for `significan|preliminary|in.flight|forthcoming|provisional|tbd|todo` — zero hits. ✓ The paper avoids the trap.

3. **One residual hazard**: `main.tex:347` figure caption says "Within-horizon comparisons (same stamp) are statistically meaningful". This is softer than "significant" but borderline. Acceptable but the reviewer could ding it; consider "permit within-noise comparison" or similar.

4. **Clopper–Pearson disjoint @ α=0.05 (L398, L191-193)** — this is the 0/6 vs 4/4 contrast. With these counts, CP intervals are 0/6=[0, 0.459] and 4/4=[0.398, 1.000]. They are **NOT disjoint** at α=0.05 — they overlap at 0.398–0.459. ❌ This is a math error if "disjoint" means literally non-overlapping; if it means the two-sample Fisher exact p<0.05 it's true (Fisher exact p≈0.0048) but should not be phrased as "intervals disjoint". **Recommend changing to "Fisher exact p<0.005"** or recomputing what was meant.

5. **SE values are internally inconsistent** (see ❌ section above). The same data conventions need to be applied across all six headline cells.

6. **n=2 row in Table 1 (L421)** — Opus 4.7 \textsc{all} variant has n=2. The SE 0.10 / 0.12 from n=2 has df=1 and is barely meaningful; consider folding into a footnote or merging.

7. **Headline 12/12 result honesty.** `main.tex:504` correctly notes "the 12/12 cross-task is not statistically distinguishable from an 80% true rate". ✓ Excellent self-policing.

---

## Pre-submission must-fix list (priority order)

1. **[BLOCKER]** Reconcile HER@250k values across §5.1 and §5.4 for all three envs:
   - Push: §5.1 says 0.617, §5.4 says 0.550 → pick one, the W&B verified value is **0.617**.
   - PnP: §5.1 says 0.167, §5.4 says 0.167, W&B says **0.183** → confirm which is the correct artifact.
   - Slide: §5.1 says 0.183, §5.4 says 0.100, W&B says **0.183** → §5.1 wins.
   The kill-experiment §5.4 numbers (0.550, 0.167, 0.100) form an internally consistent set distinct from the W&B verified table — this suggests §5.4 is reading from an older or differently-aggregated source. **Identify which W&B sweep each number came from and align.**

2. **[BLOCKER]** Recompute all six headline SE values (Push/PnP/Slide × vlm_cf/verified_cf) uniformly from per-seed numbers using `np.std(seeds, ddof=1) / np.sqrt(3)`. The current SE values disagree with that recipe in 4 of 6 cells.

3. **[BLOCKER]** Fix the Clopper–Pearson "disjoint" claim (`main.tex:398`, `appendix.tex:191-193`). With 0/6 and 4/4, exact CP intervals **overlap**. Replace with "Fisher exact p<0.005" or compute correctly.

4. **[HIGH]** Disambiguate `+0.45 / +0.43` attribution on L70-71 (abstract) and L369-370 (§5.1). Each delta currently refers to a different method.

5. **[HIGH]** Reword L437 "Sonnet 4.5: 75% → 0% teleport on PickAndPlace" — the 75% is the Opus baseline, not a Sonnet baseline. Reader will mis-read.

6. **[MED]** Add explicit W&B run-IDs or artifact paths for the §5.4 Oracle-CF @250k numbers (0.117±0.044, 0.383±0.109) — they are not in the verified data table supplied to this audit.

7. **[MED]** Tone down `main.tex:347` "statistically meaningful" → "within-noise comparison" or similar. n=3 with overlapping SE shouldn't carry "meaningful" weight.

8. **[LOW]** Consider footnoting or merging the n=2 row in Table 1 (Opus 4.7 \textsc{all}); SE from n=2 is df=1.

9. **[LOW]** Mark any numbers in `appendix.tex` §C (real-data extended) that have no W&B artifact backing with a citation to the originating analysis notebook / commit.

---

## What was NOT found (and should have been if the brief was right)

- **No §6 (vii) p_counterfactual paragraph in this paper.** The paper has §6 = "Discussion and Limitations" (L462–509) with three `\paragraph{}` blocks (cold-start, kill-bounds, other limitations) but no (vii). No p=0.04–0.10 claim. No "weak" / "insensitive" phrasing. The brief's "L1700" appears to reference `agent_reports/paper/main.tex` (the sibling NeurIPS version), not `paper_cs285/main.tex`.
- **No "preliminary" / "in flight" / "forthcoming" / "TBD" tokens** anywhere in main or appendix. ✓ Clean.
- **No "statistical significance" claim.** ✓ Clean (one borderline phrase flagged at item 7 above).
