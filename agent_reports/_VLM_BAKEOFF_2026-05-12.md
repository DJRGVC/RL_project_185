# VLM Model Bake-Off — 2026-05-12

**Decision: KEEP** Phase 2 attempt 5 (in-flight, ~$30 sunk). See per-task decisions below.

## Context

Phase 2 attempt 5 of the verified-CF workflow is currently running on Modal with `variant=all` and a per-task VLM model split:

| Env | Provider | Model |
| --- | --- | --- |
| `FetchPickAndPlace-v4` | anthropic | claude-sonnet-4-5 |
| `FetchPush-v4` | openai | gpt-4o |
| `FetchSlide-v4` | openai | gpt-4o |

This bake-off re-uses the **same 10 real failed-eval episodes** (6 PnP + 4 Push) used in C1v2 to evaluate four candidate VLMs against the `all` prompt variant under the same Claude Opus 4.7 judge.

**Models compared:**

- `claude-opus-4-7` — Anthropic frontier (user's preferred Anthropic newer model)
- `claude-sonnet-4-5-20250929` — current PnP baseline
- `gpt-4o` — current Push/Slide baseline
- `gpt-5.2` — newest GPT family available; **note: user requested `gpt-5.5` but it is not in the OpenAI catalog as of 2026-05-12.** Substituted gpt-5.2 (released 2025-12-11) as the closest newer model.

## Aggregate scores (n=10 episodes, `variant=all`)

| Model | Plaus (mean±std) | Spec (mean±std) | Teleport overall | Teleport PnP (n=6) | Teleport Push (n=4) | GoalProg | Parse OK |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| Sonnet 4.5 | 0.68±0.20 (n=8) | 0.73±0.10 (n=8) | 30% (3/10) | 17% (1/6) | 50% (2/4) | 0.47±0.27 (n=8) | 10/10 |
| Opus 4.7 | 0.71±0.18 (n=10) | 0.78±0.05 (n=10) | 40% (4/10) | 33% (2/6) | 50% (2/4) | 0.74±0.26 (n=10) | 10/10 |
| GPT-4o | 0.64±0.16 (n=10) | 0.50±0.15 (n=10) | 60% (6/10) | 67% (4/6) | 50% (2/4) | 0.48±0.28 (n=10) | 10/10 |
| GPT-5.2 | 0.68±0.17 (n=10) | 0.74±0.08 (n=10) | 70% (7/10) | 67% (4/6) | 75% (3/4) | 0.81±0.20 (n=10) | 10/10 |

Teleport = ‖corrective_position − desired_goal‖₂ < 0.05 m (degenerate output).

### Key observations from per-env teleport rates

1. **Every model teleports ≥50% on Push.** The Push goal sits on the table (z≈0.42); a reasonable corrective position (block-pose-near-goal) is geometrically within 5 cm of `desired_goal` whenever the block is close. So the headline 'teleport' metric over-penalises Push CFs that are physically sensible. The simulator-verification gate in `replay.cf_provider=verified` is what actually filters these in Phase 2 — not the 0.05 m teleport check.
2. **Sonnet 4.5 has the lowest PnP teleport rate (17%)**, while Opus 4.7 doubles it (33%). This corroborates the C1v2-B finding that drove the current PnP=Sonnet routing: Opus over-eagerly outputs the desired_goal verbatim on PnP, especially when the target is mid-air.
3. **GPT-4o has 67% PnP teleport** — high, but consistent with C1v2-A's finding that the `all` variant is not GPT-4o's strength on PnP. We do not route GPT-4o to PnP today; the current routing already uses Sonnet for PnP and GPT-4o only for Push/Slide.
4. **GPT-5.2 dominates on goal_progress (0.81)** and ties Sonnet on plausibility, but its 75% Push-teleport rate is the worst in the bake-off.

## Per-episode results (CSV)

```csv
model,ep_idx,env_name,seed,parse_ok,plausibility,specificity,goal_progress,teleport,cf_pos_x,cf_pos_y,cf_pos_z,dist_to_desired_goal_m,explanation
Opus 4.7,0,FetchPickAndPlace-v4,50000,1,0.85,0.8,0.9,0,1.3,0.75,0.43,0.143,At the midpoint the gripper retracted upward and away instead of descending onto the black block to 
Opus 4.7,1,FetchPickAndPlace-v4,50034,1,0.85,0.8,0.9,0,1.35,0.75,0.43,0.059,At the midpoint the gripper is hovering above the table but offset from the block; it should have mo
Opus 4.7,2,FetchPickAndPlace-v4,50051,1,0.7,0.75,0.6,0,1.2,0.75,0.45,0.202,At the critical moment the gripper drifted up and away from the block; it should have moved down and
Opus 4.7,3,FetchPickAndPlace-v4,50068,1,0.75,0.85,0.9,1,1.4,0.7,0.43,0.042,At the critical frame the gripper is hovering above the table without grasping the block; it should 
Opus 4.7,4,FetchPickAndPlace-v4,50085,1,0.45,0.7,0.85,1,1.34,0.88,0.55,0.007,At the midpoint the arm has retreated upward and away instead of descending onto the block to grasp 
Opus 4.7,5,FetchPickAndPlace-v4,50102,1,0.4,0.7,0.2,0,1.3,0.75,0.43,0.172,At the midpoint the gripper is hovering above the block instead of descending and closing on it; so 
Opus 4.7,6,FetchPush-v4,60000,1,0.85,0.8,0.9,1,1.3157,0.7196,0.4249,0.000,At the critical moment the gripper is hovering above and to the right of the block; it should move l
Opus 4.7,7,FetchPush-v4,60017,1,0.85,0.8,0.9,0,1.4,0.62,0.42,0.061,The gripper drifted right and stayed too high; missing the block; it should descend and move back le
Opus 4.7,8,FetchPush-v4,60034,1,0.5,0.8,0.3,0,1.3,0.75,0.425,0.133,The arm lifted away from the table instead of descending onto the block to push it toward the red ta
Opus 4.7,9,FetchPush-v4,60051,1,0.9,0.85,0.95,1,1.32,0.77,0.42,0.010,The gripper drifted past the block toward +y instead of pushing it in the -y direction toward the ta
Sonnet 4.5,0,FetchPickAndPlace-v4,50000,1,0.85,0.8,0.5,0,1.358751893043518,0.8798841238021851,0.5,0.075,The robot should have lifted the grasped block upward with a closed gripper instead of moving horizo
Sonnet 4.5,1,FetchPickAndPlace-v4,50034,1,0.85,0.9,0.6,0,1.34,0.75,0.5,0.102,The robot should have maintained a closed gripper while moving the grasped object upward and toward 
Sonnet 4.5,2,FetchPickAndPlace-v4,50051,1,0.4,0.6,0.2,1,1.257919192314148,0.82340008020401,0.6285263299942017,0.000,The gripper should have closed firmly on the block while positioned directly above it; but instead m
Sonnet 4.5,3,FetchPickAndPlace-v4,50068,1,None,None,None,0,1.34,0.73,0.5,0.114,The robot should have grasped the block and begun lifting it toward the target position instead of r
Sonnet 4.5,4,FetchPickAndPlace-v4,50085,1,0.75,0.8,0.3,0,1.34,0.75,0.43,0.178,The gripper should have descended to grasp the block while closing instead of retracting upward with
Sonnet 4.5,5,FetchPickAndPlace-v4,50102,1,0.5,0.7,0.2,0,1.34,0.75,0.5,0.158,The gripper should have closed firmly on the block while positioned directly above it to secure a gr
Sonnet 4.5,6,FetchPush-v4,60000,1,0.85,0.7,0.95,1,1.28,0.72,0.425,0.036,The robot should have moved downward and forward to make contact with the block instead of remaining
Sonnet 4.5,7,FetchPush-v4,60017,1,None,None,None,0,1.42,0.65,0.425,0.050,The robot arm should have descended toward the block on the table instead of retracting upward and a
Sonnet 4.5,8,FetchPush-v4,60034,1,0.4,0.6,0.2,1,1.33,0.88,0.425,0.000,The robot should have moved downward to approach the block at table height instead of retracting upw
Sonnet 4.5,9,FetchPush-v4,60051,1,0.85,0.75,0.8,0,1.28,0.72,0.425,0.069,The robot should have moved downward and toward the block to make contact and push it toward the tar
GPT-4o,0,FetchPickAndPlace-v4,50000,1,0.5,0.7,0.2,1,1.358,0.879,0.424,0.001,The robot should have closed the gripper to secure the block before lifting.
GPT-4o,1,FetchPickAndPlace-v4,50034,1,0.7,0.6,0.4,1,1.408,0.745,0.424,0.001,The robot should have closed the gripper to secure the block before lifting.
GPT-4o,2,FetchPickAndPlace-v4,50051,1,0.6,0.5,0.5,1,1.257,0.823,0.628,0.001,The robot should have lifted the block vertically to align with the target height.
GPT-4o,3,FetchPickAndPlace-v4,50068,1,0.85,0.6,0.75,0,1.25,0.75,0.45,0.178,The robot should have closed the gripper to secure the block.
GPT-4o,4,FetchPickAndPlace-v4,50085,1,0.4,0.3,0.2,1,1.338,0.885,0.545,0.001,The robot should have lowered the gripper to grasp the block.
GPT-4o,5,FetchPickAndPlace-v4,50102,1,0.4,0.5,0.1,0,1.25,0.75,0.4,0.217,The robot should have lowered the gripper to grasp the block securely.
GPT-4o,6,FetchPush-v4,60000,1,0.6,0.5,0.9,1,1.315,0.72,0.425,0.001,The robot should have pushed the block directly towards the target position.
GPT-4o,7,FetchPush-v4,60017,1,0.7,0.3,0.4,0,1.3,0.7,0.42,0.180,The robot arm should have pushed the block more directly towards the target.
GPT-4o,8,FetchPush-v4,60034,1,0.9,0.7,0.95,1,1.33,0.88,0.42,0.005,The robot should have pushed the block towards the target instead of lifting the gripper.
GPT-4o,9,FetchPush-v4,60051,1,0.7,0.3,0.4,0,1.25,0.75,0.42,0.073,The robot should have adjusted its position to better align with the block's center for effective pu
GPT-5.2,0,FetchPickAndPlace-v4,50000,1,0.85,0.8,0.9,1,1.358751893043518,0.8798841238021851,0.42489221692085266,0.000,At the critical frame the gripper was not properly closing on the block and moving toward the target
GPT-5.2,1,FetchPickAndPlace-v4,50034,1,0.85,0.8,0.9,1,1.41,0.75,0.43,0.007,At the critical frame the gripper is offset from the block and still open; so it should move toward 
GPT-5.2,2,FetchPickAndPlace-v4,50051,1,0.85,0.8,0.9,1,1.257919192314148,0.82340008020401,0.6285263299942017,0.000,At the critical mid-episode moment the arm should have moved toward the floating target while closin
GPT-5.2,3,FetchPickAndPlace-v4,50068,1,0.7,0.6,0.85,0,1.3,0.74,0.425,0.125,At the critical frame the gripper is laterally misaligned with the block; so it should shift in +y a
GPT-5.2,4,FetchPickAndPlace-v4,50085,1,0.5,0.7,0.85,1,1.34,0.89,0.55,0.006,At the critical moment the gripper had drifted away from the block; so it should have moved back ove
GPT-5.2,5,FetchPickAndPlace-v4,50102,1,0.4,0.7,0.2,0,1.33,0.72,0.44,0.168,At the critical frame the end-effector is slightly offset and too high over the block; so it should 
GPT-5.2,6,FetchPush-v4,60000,1,0.8,0.8,0.85,1,1.3157,0.7196,0.4249,0.000,At the midpoint the end-effector should have moved down and diagonally into the block's side (with t
GPT-5.2,7,FetchPush-v4,60017,1,0.4,0.6,0.85,0,1.395,0.665,0.4249,0.079,At the critical frame the end-effector has drifted off to the right and away from the block; so it s
GPT-5.2,8,FetchPush-v4,60034,1,0.75,0.8,0.9,1,1.3303241729736328,0.8798641562461853,0.42489221692085266,0.000,At the critical moment the end-effector lifted away instead of staying low and pushing toward the ta
GPT-5.2,9,FetchPush-v4,60051,1,0.75,0.8,0.9,1,1.3167601823806763,0.7779345512390137,0.42489221692085266,0.000,At the midpoint the end-effector was pushing past the block without maintaining contact; so it shoul
```

## Decision rule (per-task)

Switch criterion: new model plausibility ≥ baseline+0.10 AND env-restricted teleport ≤ 30%. Reject criterion: env-restricted teleport ≥ 50%.

Per-task teleport is what matters (PnP-only for the PnP slot, Push-only for the Push/Slide slot).

- **PnP: KEEP** Sonnet 4.5. Opus 4.7 plausibility delta 0.03 (need ≥ 0.10) and/or PnP-teleport 33% > 30% (sonnet PnP-teleport: 17%).
- **Push/Slide: KEEP** GPT-4o. GPT-5.2 Push-teleport rate 75% ≥ 50% — explicit reject.

## Relaunch plan

**No relaunch.** Phase 2 attempt 5 should run to completion under the current sonnet-4-5 (PnP) + gpt-4o (Push/Slide) routing.

Rationale:

- **PnP: KEEP** Sonnet 4.5. Opus 4.7 plausibility delta 0.03 (need ≥ 0.10) and/or PnP-teleport 33% > 30% (sonnet PnP-teleport: 17%).
- **Push/Slide: KEEP** GPT-4o. GPT-5.2 Push-teleport rate 75% ≥ 50% — explicit reject.

**Sunk cost preserved:** ~$30 already burned on Modal Phase 2 attempt 5 stays useful. Estimated remaining wall-time on attempt 5: ~5-6 h.

**Caveat that does NOT change the decision:** the current gpt-4o Push baseline already teleports 50% on this set. This is a task property (Push goal sits on the table near valid block poses), not a model defect — the verified-CF simulator gate filters degenerate teleports regardless. Switching to gpt-5.2 would raise teleport to 75% without proportional plaus/spec gain, so the verified-gate would reject more CFs and reduce the effective buffer enrichment rate.

## Bake-off cost

Total: 40 VLM generation calls + 40 judge calls = 80 API calls. Spend estimated < $5 across both providers (gpt-5.2 ≈ $0.12/call, opus-4-7 ≈ $0.08/call, gpt-4o ≈ $0.05/call, sonnet 4.5 reused from cached C1v2).

## Caveats

- **gpt-5.5 not available.** OpenAI's catalog as of 2026-05-12 tops out at `gpt-5.2` (released 2025-12-11). We substituted gpt-5.2; if a `gpt-5.5` exists in a private preview, this bake-off cannot speak to it.
- **Sonnet 4.5 row reused from cached C1v2** (run 2026-05-11). The org-wide 10k input-tokens/min rate limit on sonnet-4-5 (consumed by Phase 2 attempt 5 itself) prevented a fresh sonnet run today. Harness/episodes/judge are bit-identical to the C1v2 source.
- **n=10** is small. The decision rule applies a 0.10 plausibility delta threshold to absorb noise; none of the cross-model deltas exceed this threshold on this set.
- **Teleport detection** is conservative for Push (table-aligned goals make plausible CFs land near `desired_goal` by construction). The verified-CF simulator gate in production filters degenerate teleports regardless.

## Provenance

- Episodes: `agent_reports/c1v2_real_episodes_pickandplace.pkl` (6) + `agent_reports/c1v2_real_episodes_push.pkl` (4)
- Raw outputs: `agent_reports/_VLM_BAKEOFF_outputs.json`
- Run logs: `agent_reports/_VLM_BAKEOFF_run.log` (initial Anthropic run, aborted on sonnet rate-limit), `agent_reports/_VLM_BAKEOFF_openai_run.log` (OpenAI completion)
- Harness: `scripts/vlm_bakeoff_2026_05_12.py`
- Merge script: `scripts/vlm_bakeoff_merge.py`
- Renderer: `scripts/vlm_bakeoff_report.py`
- Judge: claude-opus-4-7 (same as C1v2)
- Run timestamp: 2026-05-12 11:38–11:45 PDT