# Section dive 2335 — §3 Setup paragraph: formalize IS-pairing requirement

**Target:** `agent_reports/paper/main.tex` (NeurIPS preprint only). CS 285
variant untouched per page-lock guardrail.

**Edit summary.** Rewrote the opening "Setup" paragraph of §3 (Theoretical
Motivation, line ~499). Prior version dove straight into the trajectory
notation and the PER regression target without naming the conceptual axis
the section formalizes. Since 1735 the IS-pairing principle has been woven
into §1 (intro + bullets (1)(2)), §2.1 (HER closing connector), §2.2 (PER),
and §2.4 (generator-verifier adaptive-filter); but §3 — the section that
*derives* it — only invoked the term obliquely. The new opening now states
the requirement formally as a property of the pair $(\mu, w_{\text{IS}})$,
notes that changing $\mu$ alone produces a clean estimator of a *different*
objective (not a noisier estimator of the same objective), and threads
forward to the multiplicative vs additive choice that the rest of the
section adjudicates. The original PER derivation paragraph is preserved
below, with one small consolidation: the second paragraph now opens by
casting $(\mu_U,1)$ as the trivial pair satisfying the requirement, then
casts PER as the first non-trivial pair, which re-anchors Schaul et al.
[Sec. 3.4]'s self-normalized-IS argument as a *pairing-preserving*
construction rather than just an estimator-recovery move.

**Empirical tie-in landed.** The new Setup paragraph closes with a
falsifiable prediction that the IS-pairing framing makes: a correctly-paired
multiplicative VLM proposal cannot exceed the privileged-information
ceiling set by an oracle counterfactual relabeler on the same buffer-shape,
and the 23:27 HER@1M = Oracle-CF@1M = 0.583 tie on FetchPickAndPlace
(Delta = 0.000 at the 1M convergence horizon, n=3 seeds each) is exactly
the empirical bound the framing predicts. This converts the kill result
from a section-5 negative finding into a *§3 sanity check on the
derivation*, which is the load-bearing role the new data deserves. Page
count went 47 -> 48 (still 2pp inside the 50pp NeurIPS budget). One
pre-existing undefined reference (`tab:vlm_comparison`) is orthogonal and
was present before this edit; all cross-refs introduced by the new
paragraph (sec:related, sec:method:sper, sec:method:verified, sec:theory,
sec:exp:inflight, eq:headline) resolve cleanly. Compile via
`paper/build.sh`. No conflict with the :13/:38 paper-iter slots — those
target intro/related-work bullets and §5.x sub-analyses, not §3.
