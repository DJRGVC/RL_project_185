# Section dive 1235 — §6 Limitations bullet (ix): cold-start verifier-rejection regime

## What was done

Selected §6 Limitations (the original bullets (i)–(viii)) as the least-recently-touched
substantive section: bullets (vii) and (viii) were added in commits `da36b9f` and earlier
to address R1 W7/W11 granularity gaps, but the *body* of the original limitations list
had not been touched since the night of 05-11 (`d7d224e`). The pseudocode boxes
in the appendix and the §3 "Setup" derivation were also candidates, but the pseudocode is
already self-consistent (see Appendix B Step 5 honest disclosure) and the §3 setup is a
textbook IS warm-up. The strongest *substantive* improvement on the candidate list was
incorporating the live finding from the Phase 2 in-flight runs (`am_status_1345.md`,
`am_status_1255.md`): the verified-CF variant on FetchPickAndPlace, seed 42, is sitting at
100% verifier-rejection rate over the first ~80 VLM calls (steps 1.4k–2.8k of 100k). This
is a real cold-start failure mode of the simulator-as-verifier gate and was nowhere in the
paper — even §4.3's "calibration is a throughput dial" framing anticipated it only in
principle. R1's W6 ("The verifier mechanism is not actually evaluated as an RL method"),
read in light of this finding, sharpens to: "the verifier mechanism, when integrated into
SAC+HER, has a cold-start regime in which it can contribute zero." That is now disclosed.

## What the new bullet (ix) says

(ix) The verifier is a precision-over-recall instrument by construction: every accepted
relabel is sparse-reward-positive (ε_cal = 0 under A5), but acceptance is gated by the
joint event that the VLM proposes a corrective action *and* the action sequence crosses
the 5 cm goal threshold within N=50 verifier steps. Early in training, the snapshot state
σ itself is far from the goal, so this joint event has very low base rate. Our Phase 2
FetchPickAndPlace+verified-CF run, seed 42, hit a 100% verifier-rejection rate over the
first ~80 VLM calls of 100k — operationally indistinguishable from SAC+HER with extra
VLM-API overhead. The §4.3 "calibration is a throughput dial" framing anticipates this in
principle but understates the magnitude: at cold-start throughput can be zero, in which
case the verified-CF channel contributes nothing and the run reduces to a strictly costlier
HER. Practical mitigations (base-policy warm-up before enabling the verifier, longer
verifier horizon N, soft-acceptance relaxation r ≥ −ρ_r for some ρ_r < η) are
pre-registered for a follow-on study but not run here. Compile clean (no new
overfull/underfull issues), 38 pp total, no new bib entries. Committed to
`agent/pathc-lead` as a single addition between bullet (viii) and the Conclusion paragraph.
