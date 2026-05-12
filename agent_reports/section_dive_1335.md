# Section dive 1335 -- Appendix B.3 (Conditions for unbiasedness): formal regime split between $q_\phi$-degeneracy modes

## What was done

Selected Appendix B.3 (`app:unbiased`, "Conditions for unbiasedness") as the deep-improver
target. The "don't-touch" list at hand-off ruled out the headline §5.2 ablation, the recently
edited §5.6(C)(D)(E), §6 paragraph 1, §6(ix), the Conclusion, §4.1, §4.3, and the
Algorithm 1/2 pseudocode boxes. Remaining candidates were the Abstract, §1 contribution
bullets, §3 setup, §4.2 prompt design, and Appendix B/C/E. Appendix B.3 ranked highest:
(a) it carries the bias-bound theorem (Eq. bias-bound) cited from §3 main body, §4.3, the
Conclusion, and §6(ix) but never extended; (b) the hot finding at 14:45 -- Oracle-CF 1M
mean SR=0.60 with seeds s42=0.30 and s123=0.90, and vcf_pp_s42 at step 143k with 101/101
verifier rejections still 100% -- is exactly the regime that the existing (A5) bullet only
gestures at as "$\varepsilon_{cal} = 1$, VLM ignored." (A5) collapses two operationally
distinct failure modes (Semantic-PER miscalibration as variance amplification vs.
Verified-CF miscalibration as signal extinction) onto a single calibration scalar, which
is the slippage that makes §6(ix) read as a separate caveat rather than as a corollary of
the theory. The improvement formalizes the regime split.

## What the new paragraph does

Inserted a new paragraph "Two regimes of $q_\phi$-degeneracy: variance amplification vs.
signal extinction" at the end of Appendix B.3, before the §C heading. The paragraph (i)
decomposes the verifier-channel effective mass $m_\phi(\tau)=m_{gen}\cdot m_{ver}(\sigma)$
into a generator term and a snapshot-dependent acceptance term (new equation
`eq:verifier-mass`, set as an aligned block to avoid an overfull hbox at table-width); (ii)
identifies the cold-start regime as $m_{ver}(\sigma)\to 0$ uniformly over early-training
snapshots, citing both the s42 vcf_pp 143k rejection rate and the s42/s123 oracle-CF
variance from `am_status_1445.md`; (iii) shows that under this condition the verifier's
$\varepsilon_{cal}=0$ guarantee holds vacuously and Eq. bias-bound is satisfied trivially,
but at the cost that $\nu_{vcf}$ is the zero measure and the VCF channel contributes no TD
signal; (iv) contrasts this with Semantic PER, where the lower bound $w_{sem}\ge 1$ in (A1)
keeps $\mu_{Sem}$ full-support on $\mathcal{D}_B$ for arbitrary $q_\phi$-miscalibration and
the only effect is the bounded variance-amplification term in Eq. bias-bound; (v) closes
with the formal statement that "Semantic-PER $q_\phi$-degeneracy is variance amplification,
bounded; Verified-CF $q_\phi$-degeneracy is signal extinction, unbounded in the limit
$m_{ver}\to 0$." This is the analytical justification, internal to the IS framework, for
why the paper presents the two contributions as complementary rather than as parallel
applications of the same prior. Compile clean (Overfull hbox at line 650 fixed in v2 with
an aligned block, no new warnings, page count 38 -> 39, no new bib entries). Committed to
`agent/pathc-lead`.
