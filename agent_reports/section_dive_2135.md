# Section Dive 2135 — §5.5 Real-Data: policy-precision bridge to verified-CF

**Target.** `agent_reports/paper/main.tex` §5.5 Real-Data Validation, a
new `\paragraph{Policy-precision dependence and the bridge to the verifier.}`
inserted between finding (iii) (action-axis sign-flip) and the existing
`\paragraph{Caveats.}` paragraph. Picked **Option C** from the
START-IMMEDIATELY logic over A/B/D because (a) §5.5 was 20+ hr stale and
contained no engagement with the verified-CF cold-start finding the §1
contribution bullet (3) at 23:30 and §6 (ix) at 22:30 both rely on,
leaving the two findings sitting in the paper as independent results
when in fact they are **two reflections of the same policy-precision-
dependent property** of the VLM credit-assignment oracle. Option B (§2.4
generator-verifier) was a close runner-up but would have stepped on the
recently-edited (22:30) §6 (ix) cold-start framing; Option D (§5.3
prompt analysis) is mid-stale (02:37 yesterday) but does not have a
natural conceptual addition pending real numbers; Option A (§2.3 FM-in-RL)
was edited at the post-Sharony pivot a couple of days ago and the
two-paradigm distinction is already named clearly in §2.3 lines 305--362
and §2.4 lines 364--391. No conflict with paper_iter (`pgrep -af paper_iter`
returned empty at 21:33 PDT). No in-flight training is touched: the new
text only references results already in the paper (§5.6 (D), §6 (ix), §4.2,
§4.3) and the §5.5 findings already on the page.

**Substantive changes.** One new ~28-line paragraph in §5.5 (`main.tex`
lines 1545--1586 in the updated file). The paragraph makes one paper-
strengthening conceptual claim: the two VLM-side error modes catalogued
in findings (i) and (iii) of §5.5---teleport-collapse persistence on real
data, and the worsening sign-flip rate on near-miss displacement
vectors---are **both policy-precision-dependent**, both run in a
direction that **degrades** the prompt-only pipeline as the policy
improves (because near-miss failures have smaller $\lVert g - \mathrm{ag}
\rVert$ and the achieved-goal CF approaches the desired goal in
expectation), and the verified-CF pipeline of §4.3 has the
**anti-correlated** dependence: snapshot state $\sigma$ sits closer to
the goal as the policy improves, so the verifier's joint-event base rate
rises toward one. This is the conceptual reason the cold-start verifier-
rejection regime of §6 (ix) is transitory, and it elevates §5.5 from a
standalone real-data ablation into a load-bearing prelude to §5.6 (D).
The paragraph closes by naming the two empirical anchors: Sonnet's
0/6 PickAndPlace teleport (a mid-air task admitting a non-trivial
waypoint) and verified-CF's 0.617 vs. vlm\_cf's 0.55 on FetchSlide
are two reflections of the same phenomenon under complementary
mechanisms. Cross-refs used: `sec:method:prompt` (§4.2),
`sec:method:verified` (§4.3), `sec:exp:inflight` (§5.6). All three are
defined elsewhere in main.tex and resolve cleanly in the rendered PDF
(verified `Section 4.2`, `Section 4.3`, `Section 5.6(D)` in pdftotext
output). No new equations, citations, or figures. Page count went
45 → 46; file size 121145 → ~124 KB (one paragraph added). Build clean
(2 pdflatex passes); only warning is the pre-existing `tab:vlm_comparison`
undef on p.~21, unchanged from the 17:35 baseline. Visual gate passed:
new paragraph renders correctly with all symbols (`q_φ`, `σ`, `∥g - ag∥`,
N=50, 5 cm) and bridges §5.5 → §5.6 (D) → §6 (ix) into the
conceptual sequence the §1 contribution bullet (3) already implies but
did not previously argue. Commit on `agent/pathc-lead`.
