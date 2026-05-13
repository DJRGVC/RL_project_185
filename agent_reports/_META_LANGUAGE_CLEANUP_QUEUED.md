# Meta-Language Cleanup — QUEUED to fire after GPTZero agent completes

**Wait condition:** the agent `abdd52ebfe96a5d2b` (GPTZero iterative + math check + GitHub-ref cleanup) must have written `_GPTZERO_FINAL_REPORT.md`.

**Trigger detection**: `agent_reports/_GPTZERO_FINAL_REPORT.md` exists AND `git log --oneline -1` shows a "GPTZero" or "math check" commit.

## Cleanup prompt to fire

META-LANGUAGE CLEANUP for CS 285 paper at /home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185. 45-min budget. Opus 4.7.

Daniel noticed AGENT-SPEAK ARTIFACTS in the paper (e.g., "paper-grade"). These are agent project-management words that leaked into the manuscript and should not appear in a real academic paper. Strip them surgically while preserving content + Pass 1-3 + Winston + GPTZero edits.

INVENTORY OF CONFIRMED ARTIFACTS (from baseline grep on 2026-05-13 10:35 PDT)

### 🔴 HIGH-PRIORITY REMOVE/REPLACE

(a) "**headline**" — 11 occurrences in main.tex+app. Pure meta-language for "main result/finding/figure." Context-appropriate replacements:
- "headline ablation" → "main ablation" / "primary ablation" / "the core ablation"
- "headline figure" → "Figure X" / "main figure" / specific noun ("the success-rate plot")
- "headline number" → "the [specific finding]"
- DO NOT use "main result" generically — pick a specific noun.

(b) "**production**" — 4 occurrences. Meta-language for "the version we use."
- "production VLM" → "the VLM we run" / "our deployed VLM" / "Sonnet 4.5 (our chosen VLM)"
- "production config" → "our chosen configuration" / "the configuration we adopt"

(c) "**pre-staged**" — 3 occurrences. Project-management speak.
- "pre-staged for camera-ready" → "deferred to camera-ready" / "left for future work"
- "pre-staged but not run" → "designed but not executed in time for this report"

(d) "**paper-grade**" — 2 occurrences (appendix). User explicitly flagged.
- "paper-grade evidence" → "publication-quality evidence" / "rigorous evidence" / drop the qualifier
- "paper-grade figure" → just "figure"

(e) "**submission**" — 4 occurrences. The paper is talking about itself.
- "for submission" → just remove the phrase if redundant
- "submission file" → "the manuscript" / "this report"

(f) "**P0/P1/P2**" — 2 occurrences. PM-priority notation, not academic.
- "P0 fixes" → "critical fixes" / specific terms
- "P1 polish" → "secondary improvements"

(g) "**verdict**" — 1 occurrence. Meta-language.
- "the kill verdict" → "the kill decision" / "the kill criterion outcome" / "the decision to abandon"

(g-bis) "**camera-ready**" — 4 occurrences. THIS IS WRONG FOR CS 285. There is no camera-ready for a CS 285 final report; this paper IS the final. The "camera-ready" phrasing is a fictional NeurIPS-submission narrative that leaked from agent context.
- main.tex:101 "VLM-RB head-to-head is pre-staged for camera-ready." → "VLM-RB head-to-head remains for future work." or "We do not run a direct VLM-RB comparison in this report."
- main.tex:285 "...to camera-ready." → "...to follow-up work." / "...to subsequent investigation."
- main.tex:551 "head-to-head deferred to camera-ready" → "head-to-head left for future work" / drop entirely
- appendix.tex:214-215 "head-to-head deferred to camera-ready" → same fix
- DO NOT use "camera-ready" anywhere in the CS 285 paper. There is no camera-ready stage.

(g-tris) Any other "preprint" / "extended preprint" / "manuscript" / "submission" meta-narrative — verify it makes sense in the CS 285 context. The Matei contribution bullet says "reported separately in the extended preprint" — this is acceptable as it refers to the actual longer NeurIPS variant we have at `paper/main.tex`. KEEP that one.

### 🟡 BORDERLINE — context-dependent

(h) "**pre-registered**" — 6 occurrences. Only legit if there's an actual pre-registration document (OSF, AsPredicted, etc.). For our project there is no such document; we just decided on a kill criterion upfront.
- "pre-registered kill criterion" → "the kill criterion we set upfront" / "the criterion specified before the runs"
- "pre-registered prediction" → "the prediction we stated upfront" / "the prediction the framework makes"
- ALTERNATIVELY: if Daniel wants to keep the rigor signal, add a sentence in Methods saying "our kill criterion + hypotheses were committed before any results were observed" — that justifies "pre-registered" usage. Recommend dropping the word and saying "stated in advance" since there's no formal preregistration.

(i) "**diff**" — 4 occurrences. Engineer-speak.
- "the diff between..." → "the difference between..." / "the comparison of..."
- "diff against..." → "compared against..."

(j) "**checkpoint**" — 2 occurrences. Mixed:
- "the milestone checkpoint" → "the milestone" / "the first checkpoint" (this is OK in CS-course context but slightly off in NeurIPS)
- "model checkpoint" → fine, standard RL term

### 🟢 KEEP (technical terms in RL)

- "rollout" (5) — standard RL term
- "post-hoc" (1) — standard academic

### 🟢 INLINE (i)/(ii)/(iii) format — KEEP AS-IS

**User decision 2026-05-13 10:45 PDT:** the inline `(i) \textbf{Title.} body text (ii) \textbf{Title.} body text` format in Ext Abs lines 72-93 and Discussion lines 540-547 is **standard NeurIPS style**. Many accepted NeurIPS papers (VAR 2024, etc.) use this exact pattern for Extended Abstract contribution lists and limitation enumerations. Keeping it preserves vertical space (critical for 1pp Ext Abs) and maintains paragraph flow.

**DO NOT convert to `\begin{enumerate}`.** The bold titles already provide visual structure inside the paragraph. The dense feel comes from content density, not format error.

### 🟢 KEEP / DO NOT touch §7 Contributions
The Contributions section uses some of these words (Daniel wrote them); leave unchanged.

WORKFLOW

(1) For each artifact category above, do targeted `grep -n` + replace per the rules. Use `Edit` tool with `replace_all: true` where safe.

(2) After all replacements, recompile: `cd agent_reports/paper_cs285 && bash build.sh`
- Verify 11pp ceiling preserved
- Verify build clean
- Visual check at 150 DPI on Abstract + §1 + §5 + Conclusion

(3) Final GPTZero re-scan (uses ~5-10 credits): submit the full plain-text body to verify the cleanup didn't hurt the human-score.

(4) Commit: "Meta-language cleanup: remove paper-grade, production, headline, P0/P1, pre-staged, etc."

(5) Push both branches via `git push origin agent/pathc-lead agent/pathc-lead:main`.

(6) Output `agent_reports/_META_LANGUAGE_CLEANUP_REPORT.md`:
- Per-pattern: count before / count after / decisions made
- Any borderline calls explained
- Final GPTZero score (should be ≥ prior)
- Total artifacts removed

CONSTRAINTS
- Opus 4.7. Use venv.
- **EDIT ONLY paper_cs285/main.tex + appendix.tex.**
- Preserve all numerical claims, equations, citations, contributions, section structure.
- Preserve 11pp ceiling.
- Preserve all Pass 1-3 + Winston + GPTZero + math-check + GitHub-cleanup edits.
- §7 Contributions UNTOUCHED.

START IMMEDIATELY.
