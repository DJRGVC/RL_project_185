# Section Dive 1635 — Appendix F (Broader Impacts): substantive expansion

**Target.** `appendix.tex` `\subsection{Broader Impacts}` (`\label{app:impact}`),
inside `\section{Reproducibility Checklist}`. Chosen over §5.3/§5.4/§5.5 (all
recently deep-improved, 18-20 hr ago and data-dependent), Appendix B.2 (touched
13:35 with the two-regime degeneracy split, already substantive), and §1
contribution bullets (load-bearing, high risk of conflict with the abstract /
roadmap pass at 13:50). Appendix F was the only candidate from the
least-touched list that was both (a) untouched since the initial NeurIPS
appendix landed (`1de84cf`, 22:26 yesterday) and (b) genuinely thin — the
prior version was ~30 lines and largely duplicated §6's main-body
Broader-Impact paragraph (commit `c488c6b`). The §6 paragraph supplies
the high-level positive/negative/scope; Appendix F should supply the deeper
treatment a NeurIPS Broader-Impacts reader would want. No conflict with the
env-screenshots agent (operating on §5.1) or any in-flight paper_iter
(none in flight per `pgrep` at 16:34).

**Substantive changes.** Replaced the thin Broader-Impacts subsection with
six structured paragraphs that *complement* (do not duplicate) §6.
(1) Preamble explicitly forward-references §6 so the reader knows the
high-level structure is upstream and this appendix supplies depth.
(2) *Reproducibility-equity and foundation-model access asymmetry* — spells
out the closed-API access floor ($320 full sweep, $85/run) and three
structural mitigations: heuristic-Oracle fallback (zero API cost),
open-weights VLM shim layer in `src/vlm/` pre-registered for the camera-ready
follow-on, per-call cost reporting via `COST.md` in the release.
(3) *Net carbon accounting* — explicit env-step vs. VLM-call energy
arithmetic: 1.7×10³ calls × 8 kJ ≈ 14 MJ vs. 3.5 GPU-hr × 150 W ≈ 2000 MJ,
so VLM inference is ~10⁻² of the training-run energy at our call rate; the
sample-efficiency gain dominates. Documents the call-rate cross-over so
future work scaling up has a numeric basis for the trade-off.
(4) *Dual-use surface of the generator-verifier pattern* — physics-bounded
verifier in robotics vs. learned / partial / game-able verifiers in
program-synthesis, SMT, theorem-proving; explicitly surfaces the
Goodhart's-law failure mode this paper's setting does not exhibit, and asks
readers transplanting the pattern to non-physics domains to audit whether
the verifier is closed under the generator's output distribution.
(5) *Safety properties of training-time-only FM use* — the VLM is invoked
only offline on replay data; the deployed SAC actor carries no VLM weights
and makes no inference-time FM call, so VLM specification drift / API
deprecation / adversarial-prompt incidents after training cannot affect the
trained agent's runtime behavior. Compares favorably to VLM-as-policy and
VLM-as-reward lines (cites Rocamonde, Wu).
(6) *What this work is not* — explicit non-claims (N1) sim-to-real, (N2) FM
evaluation benchmark, (N3) multi-agent/HRI, (N4) autonomy. (7) *Personal data,
consent, content moderation* — NeurIPS Broader-Impacts required item.

**Verification.** Two pdflatex passes (exit 0). 44 pages (was 41), 1016273
bytes. Only warning is the pre-existing `tab:vlm_comparison` undefined ref
at main.tex:1537 (untouched by this edit). Visual gate via
`pdftotext -f 40 -l 44`: all paragraphs render with correct headings, all
cross-refs resolve (Appendix D.2 = compute, Appendix B.3 = Oracle v3, §5.3 /
§5.5 / §6 (vi)). Initial cross-ref to `app:oracle` was caught and fixed to
`app:oracle-v3` (correct label) before final compile. Commit `1cde9fe` on
`agent/pathc-lead`. No conflict with paper-iter schedule (compile completed
16:35, well before the 16:38 paper-iter slot). No data-dependent claims
touched; no `main.tex` change; no figure adds or bibliography touches.
