# Overnight Priority Queue — Daniel asleep, target morning bulletproof

**Updated:** 2026-05-13 00:15 PDT
**Active mandate:** "Act as a 185 grader. Identify what's wrong. Run/edit until bulletproof. Use as much usage as need be."

## STANDING DIRECTIVES FOR ALL OVERNIGHT AGENTS

1. **TWO papers exist** — never confuse them:
   - `agent_reports/paper/main.tex` → NeurIPS preprint (46 pages, has appendix)
   - `agent_reports/paper_cs285/main.tex` → CS 285 submission (45 pages, due TODAY)
2. **CS 285 paper must be ready for harsh-grader 100% by 06:00 PDT.** This is the operational deadline.
3. **Don't break in-flight training.** HER@1M PnP s999 + 6 new HER@1M Push/Slide runs on local GPU. p_counterfactual sweep on Modal.
4. **Push to GitHub after every commit** — both `agent/pathc-lead` and `main` (fast-forward).
5. **Use the watch dashboard** (`scripts/watch_runs.sh`) for status, not new agents.

## KNOWN GAPS (in priority order, work top-down)

### P0 — Blocker for CS 285 submission
- **CS 285 paper structure**: 45 pages is too long for class submission. Trim to ~10-15 pages main + appendix preserved. Reorganize for NeurIPS-style flow.
- **Per-member contributions** in 285 paper: placeholder bullets need Daniel's review (note in `% TODO`)
- **Extended Abstract polish**: graders' primary artifact. Must be flawless.

### P1 — Reviewer-grade weaknesses
- **Horizon mismatch in headline figure**: comparing HER@250k vs vlm_cf@500k vs PER@3M in same chart. Need explicit horizon annotations on every bar.
- **No matched-horizon HER baseline**: vlm_cf@500k vs HER@500k is the canonical fair comparison; we only have HER@250k and HER@1M (in flight)
- **Statistical claims**: df=2 SE intervals are not significance tests — already noted but could be sharpened
- **Sharony reproduction** still pending (Wave B B2, auto-fires after p-sweep)

### P2 — Polish
- **Consistent palette across all figures** — verify CB10 used everywhere
- **Bibliography completeness** — every claim must have citation
- **Cross-section coherence** — IS-pairing principle now threaded §1→§2→§3→§5→§6; verify

## RUNNING / QUEUED EXPERIMENTS

| Run | State | ETA finish PDT |
|---|---|---|
| HER@1M PnP s999 | 693k/1M | ~02:00 |
| HER@1M Push×3 + Slide×3 | freshly launched | ~03:30-04:00 |
| p_counterfactual sweep (10/18 active) | varied 25-73% | ~01:30-03:00 |
| Wave B (HER+PER, Sharony, 2×2) | watcher queued | fires post p-sweep |

## STOPPED FIRING SKIPS — every cron now does real work

Going forward, every cron (paper iter / section dive / status / figure / lit / code / ablation) fires a substantive agent. No more "skipping."
