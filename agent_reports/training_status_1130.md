# Training Status — 11:30 PDT 2026-05-12

## Phase 2 Attempt 5 — Spawn Status

**Total spawned: 2 / 18**

The Opus launch agent has NOT completed. `_PHASE2_ATTEMPT5_LAUNCHED.md` does NOT exist.

### Modal App Status
- Only 1 active Modal app: `ap-NWsFCh9kA9P0syU9JhIBAR` (created 11:25 PDT, 2 tasks, ephemeral/detached)
- All other apps from earlier attempts are `stopped`
- Expected 6-7 apps for full Phase 2 spawn — NOT reached

### W&B Runs (since 18:20Z / 11:20 PDT)

| Run | State | Provider | CI | Step | Relabel | None |
|-----|-------|----------|----|------|---------|------|
| path_c_vlm_cf_pp_s42_seed42 | running | anthropic | 16 | 4200 | 31 | 0 |
| path_c_vlm_cf_pp_s123_seed123 | running | anthropic | 16 | 5700 | 35 | 0 |

### Provider Routing
- PnP runs (s42, s123): prov=anthropic, model=claude-sonnet-4-5 — CORRECT
- Push runs: NOT spawned yet
- Slide runs: NOT spawned yet
- OpenAI-routed envs (Push/Slide, gpt-4o): cannot verify — runs don't exist

### Oracle-CF 1M Progress
- s42: step=4200 (4.2% of 100k? or ~0.4% of 1M — check scale)
- s123: step=5700 (~5.7% of 100k)
- At 11:25 user saw ~43% done — these two PnP runs are healthy and advancing
- Both runs: relabel>0, none=0 — VLM relabeling working correctly

## Anomalies

1. **Launch not complete**: Opus launcher still mid-flight at 11:30 PDT (5 min after 11:25 check). 16 of 18 runs unspawned.
2. **Single active app, 2 tasks only**: Consistent with only PnP s42+s123 being alive.
3. **No crashes/errors**: The 2 active runs are healthy (none=0, relabel>0).
4. **No Push or Slide runs visible**: Launcher has not yet dispatched those environments.

## Recommendation

Wait another ~3-5 min for Opus launcher to complete. Re-run status check to confirm full 18-run spawn and verify Push/Slide provider routing (should be openai/gpt-4o).
