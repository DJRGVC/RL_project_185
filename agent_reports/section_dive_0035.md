# Section dive 00:35 — §5.5 Real-Data Validation (33 -> 127 lines)

**Target:** §5.5 (`sec:exp:real`, lines 978-1102 of `agent_reports/paper/main.tex`).
Picked as the least-recently touched section in the last ~6 hours of paper iter
activity: figure-anchored, only 33 lines, untouched since initial draft, and
the natural home for two open reviewer concerns —
**W8/L2** ("3-VLM family robustness is really 2 vendors") and **W9**
(method-clarity / reproducibility for the real-data branch). All other
candidate sections (§4.1, §4.2, §4.3, §5.1, §5.2, §5.4, §5.6, abstract,
intro bullets, §2 AHA/Sharony paragraphs, §3 'why multiplicative', §6
limitations) were touched in the prior 7 commits. The expansion is purely
substantive (no copy-edit, no figure changes); body grew 3.8x from a single
"three findings" paragraph to a structured eight-paragraph treatment.

**Substantive additions:** (1) An *Episode collection* paragraph explaining
the SAC+HER checkpoint setup, seeds (50000-50102 / 60000-60051), stochastic
rollout sampling, qualitative failure modes (near-miss contact failures
vs. table-edge synthetic failures), and the localizer's mid-clip safety
rule never engaging on real data — directly addressing W9 reproducibility.
(2) An explicit **honest reframe** paragraph that downgrades the "3-VLM family"
claim to "two vendors" (Anthropic, OpenAI), notes the Opus 4.7 / Sonnet 4.5
shared-lineage caveat, and turns the Sonnet substitution into a diagnostic
*intra-vendor* probe (Sonnet behaves closer to GPT-4o on PickAndPlace, closer
to Opus on Push — the intra-vendor span covers most of the cross-vendor
range) — directly addressing R1's W8 and L2. (3) Three findings expanded
from one sentence each into full paragraphs with seed-level evidence:
task-conditioning of teleport-collapse with the Sonnet mid-air-waypoint
mechanism ($[x_{dg}, y_{dg}, 0.50]$); the 5 cm reject-teleport gate firing
on 60% of generations and the cross-vendor floor of 75% on Push; the
synthetic-to-real plausibility shift ($\pm 0.07$ on all four variants for
Opus) versus the action-axis sign-flip rate worsening from 0.50 to 0.70 on
real data — locating the largest remaining VLM-side error and motivating
two concrete fixes. (4) A *Caveats* paragraph naming the $n=10$ pilot
status, the OpenAI quota block as a real (not hypothetical) constraint on
the real-data sweep, and the judge-generator overlap as a potential
self-favoring bias with the Sonnet-vs-Opus internal-validity argument.
Pre-registers the open-weights VLM extension (LLaVA-NeXT, Qwen2.5-VL-7B)
via the existing `chen2024promptable` reference, no new bib entries.
Build clean (no overfull hboxes, no new warnings); visual gate **PASS**;
31 pages unchanged. Committed to `agent/pathc-lead` at 00:36 local.
