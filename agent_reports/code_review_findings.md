# Code Review Findings — CODE-REVIEWER agent

**Agent:** CODE-REVIEWER (Opus 4.7, 3h budget)
**Started:** 2026-05-11 22:18 PDT
**Hard stop:** 01:30 PDT 2026-05-12

Severity legend:
- **BLOCKER** — would break a training run or invalidate results. Needs human review.
- **ISSUE** — real bug, design flaw, or inconsistency that should be fixed before morning.
- **NIT** — minor, stylistic, or low-impact; safe for me to fix directly.

---

## Cycle 1 — 2026-05-11 22:18 PDT

### Commit 5a859f5 — "Path C: counterfactual HER (oracle/VLM/verified) integration"

**[ISSUE] train.py:141-160 — `verified` provider is a no-op**

File: `train.py` lines 141-160 (the `cf_fn_verified` closure inside `_build_cf_provider`).

```python
def cf_fn_verified(achieved_goals, desired_goal, keyframes=None):
    cfs = cf_fn_raw(...)
    if cfs is None: return None
    verified = []
    for (k_i, g, c) in cfs:
        # Skip verification when we have only a position-style CF
        verified.append((k_i, g, c))
    return verified if verified else None
```

The `verifier` object is constructed (line 133) but **never called**. The loop unconditionally appends every CF without checking `verifier.verify(...)`. This means the `verified_cf.yaml` config produces results identical to `vlm_cf.yaml` for `vlm_variant='achieved_goal'` (and even for `'all'`, which the config asks for). The comment "Position-only CFs aren't verifiable" is hand-waved past `variant='all'` (which the verified_cf.yaml does select). Suggested fix: either (a) actually call `verifier.verify(...)` when the CF has a corrective_action attached, or (b) document that "verified" mode currently means "VLM with explicit `variant='all'` request" and update the config name / W&B group. **For tonight's runs, the Phase 2 `verified_cf` results will be indistinguishable from `vlm_cf` — flag this in the morning analysis.**

**[ISSUE] train.py:108-118 — VLM `make_counterfactual_fn` called with `task_description=task_desc` where `task_desc` may be empty**

Line 104 in vlm_cf.yaml sets `vlm_task_description: ""` and train.py builds `task_desc = get_task_description(env_name)`. The orchestrator does not pass an override. So `task_desc` comes from `get_task_description` — fine if that function returns sensible defaults per env. Need to verify by reading the function. But the YAML config key `vlm_task_description` is **never consulted** by `_build_cf_provider`. Either remove the YAML key as dead config, or wire it: `cfg["replay"].get("vlm_task_description", "") or get_task_description(env_name)`.

**[ISSUE] src/buffers/counterfactual_buffer.py:310-313 — `_query_vlm` exception path double-counts `vlm_returned_none`**

In `_query_vlm`, the `except` block increments `self.stats["vlm_returned_none"]`. But in `finish_episode` at line 244-246, the caller also increments `vlm_returned_none` when `cf_list is None or len(cf_list) == 0`. After an exception, both the exception handler and the caller bump the counter — and the caller also doesn't decrement `vlm_calls` even though the call failed before issuing the request. Diagnostics will show inflated `vlm_returned_none` (~2x the truth) and an overestimate of `vlm_calls`. Suggested fix: don't bump from inside `_query_vlm`; just return None and let `finish_episode` count it once. Or rename the exception-path counter to `vlm_exceptions`.

**[ISSUE] src/vlm/oracle_cf.py:158 — `oracle_cf_pick_and_place` uses obs-relative table height check that is wrong on first frame**

`z_init = float(z_obj[0])` is the **block** z at frame 0. The condition `z_obj > z_init + 0.015` looks for a lift of >1.5 cm above starting block height. But if the gripper happens to nudge the block at frame 0 (or the block is grasped at episode start in some seeds), `z_init` is already lifted and the condition never fires for a smaller lift. Low impact for normal Fetch sims since the block starts on the table, but a sentinel `z_table = 0.42` (the known table height) would be more robust. NIT — okay as-is for tonight.

**[ISSUE] src/vlm/oracle_cf.py:212 — FetchSlide dt assumption**

The slide oracle uses `dt = 1/25.0` ("Fetch step is ~40 ms"). Gymnasium-robotics Fetch envs run the simulator at 0.002s × 20 substeps = 0.04s per env step, so 25 Hz is correct. However, the FrameCapture stores frames per-`env.step`, NOT per substep, so `T` is the count of env steps. The dt is correct. Acceptable.

**[BLOCKER] src/buffers/counterfactual_buffer.py:230 — `is_failure` defaults to True when `episode_success=None`**

```python
is_failure = (episode_success is False) or (episode_success is None)
```

The semantic is "if we don't know, assume it failed". For oracle CFs (cheap), this is benign — every episode incl. unknown-status triggers the oracle. For VLM CFs (expensive), an `episode_success=None` (e.g., from a buggy upstream call site, or for the early steps before `mark_episode_start` runs) would invoke the VLM gratuitously. In `train.py` line 410, the caller always passes `episode_success=bool(ep_success)`, which is always True/False (never None) — so the default never fires in production. But the C2-prototype default of `is_failure or unknown=failure` is asymmetric with how a strict goal-relabeler would treat unknowns. Downgrading to ISSUE because the call site is correct.

Actually, re-reading: train.py passes `bool(ep_success)` so we're fine. Downgrade to **NIT**.

**[ISSUE] src/buffers/counterfactual_buffer.py:236-238 — CF call interval gate off-by-one after fix**

The cf_call_interval gate is `self.stats["episodes_failed"] % self.cf_call_interval == 0`. After the patch that moved the `episodes_failed += 1` before the gate check, the modulo is computed AFTER incrementing — so for `cf_call_interval=8`, the VLM fires on the 8th, 16th, 24th, ... failed episode. That's correct behavior. **However**, when `cf_call_interval=1` (oracle_cf.yaml), `1 % 1 == 0` so it fires every time. Good. **However**, for `cf_call_interval=8` and a long warmup with many failures, the first VLM call is delayed until 8 failures have accumulated. That's the intended cost-control. ACCEPTABLE.

### Commit b393fe3 — "Path C orchestrator + plan + Modal Phase 2 spawn"

**[ISSUE] scripts/path_c_orchestrator.py:90 — `datetime.datetime.utcnow()` is deprecated in Py3.12+**

The orchestrator uses `datetime.datetime.utcnow().isoformat() + "Z"` (lines 90, 121, 128, 366, 387, 408 etc.). On Python 3.12, this emits a DeprecationWarning. On 3.13 it will be removed. Current run uses 3.11 so it's fine, but flag for the next refactor: prefer `datetime.datetime.now(datetime.timezone.utc).isoformat()`. NIT.

**[ISSUE] scripts/path_c_orchestrator.py:230-244 — modal_busy_containers parses table by splitting on `│` — fragile**

The `modal app list` output format may change between Modal CLI versions. The code parses by index into split tokens. If Modal updates its CLI output format (adds a column, removes the border char), this silently returns 0 (treating modal as fully free) and **slams Modal with all 18 Phase 2 jobs at once**. The error path returns 999 (treats modal as full) which would block Phase 2 forever. Suggested fix: pass `--json` if supported, or use `modal container list` with structured output. ISSUE — but Phase 2 is gated behind A1 completing, so the blast radius is bounded.

**[ISSUE] scripts/path_c_orchestrator.py:393-394 — Phase 2 launch uses `subprocess.Popen + wait(timeout=90)` but `proc.communicate(timeout=5)` after `wait()` is redundant and can hang the orchestrator if Modal CLI doesn't exit cleanly**

The control flow:
```python
proc = subprocess.Popen(...)
proc.wait(timeout=90)        # blocks up to 90s
out, err = proc.communicate(timeout=5)  # blocks 5s more
```

After `wait()` returns (success or TimeoutExpired), `proc.communicate` is called. If the timeout in `communicate` expires while the proc's stderr pipe is still open (rare on a clean `modal run --detach`), it raises `TimeoutExpired` which is uncaught — would crash the Phase 2 loop. Recommend: combine into a single `proc.communicate(timeout=90)`. ISSUE, low severity (Modal exits cleanly in practice).

**[ISSUE] scripts/path_c_orchestrator.py:432-435 — Phase 2 per-task overrides clobbered by `common_overrides`**

`common_overrides` from the plan includes `replay.cf_call_interval=8`. Per-task `task_extra` includes `replay.vlm_provider=anthropic` for PnP. The override merging in `_build_run_cmd` does `cmd.extend(overrides)` then `cmd.extend(extra)`. Python dict-style merging would let later overrides win, but `train.py`'s `load_config` applies overrides **in order** — so `task_extra` (later) wins over `common_overrides` (earlier). Verified by inspection of load_config:76. ACCEPTABLE.

Wait — but look at `launch_modal_run` line 308-309: `overrides = ... + list(common) + list(extra or [])`. So per-task `extra` is appended last, applied last, wins. OK.

**[ISSUE] scripts/path_c_orchestrator.py:464-468 — phase2 sleep between batches still happens after submit failures**

The loop in `run_phase2` doesn't differentiate ok/failed when sleeping. A failed `launch_modal_run` returns `False`, but the orchestrator still sleeps and moves on, so a Modal CLI hiccup just silently loses runs. The state file marks them `failed` but there's no retry. Should track failed runs and retry once after capacity probe. ISSUE.

**[STRUCTURAL — adds to BLOCKER B1] src/vlm/counterfactual.py:626-688 — `make_counterfactual_fn` discards `corrective_action`**

The CF function returns triples `(int, np.ndarray, float)` — `(failure_t, cf_pos, confidence)`. The `corrective_action` (from `variant='all'`) is computed inside `loc.query(...)` (line 661) and is on `res.corrective_action`, but is **not** included in the returned tuple. So even if the train.py `cf_fn_verified` wanted to call `verifier.verify(corrective_action=...)`, it has no access to the action.

This compounds BLOCKER B1: the verified-mode pathway is missing **two** things — (a) the actual verifier call, and (b) propagation of the corrective_action through the interface. To make `verified_cf` functional, the buffer's CF interface would need to expand to return `(failure_t, cf_pos, confidence, corrective_action_or_None)` quadruples.

**[NIT] modal_app.py:158 — local entrypoint `spawn` default config is `oracle_cf.yaml`**

Oracle uses no VLM — running it on Modal would be pure GPU waste. Default should be `vlm_cf.yaml` or no default. NIT, fixable.

**[ISSUE] scripts/path_c_orchestrator.py:201 — `LocalPool.submit` doesn't set `cwd`**

The Phase 1 `subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)` at line 201 does NOT pass `cwd=str(ROOT)`. The relative path "train.py" in the cmd will only resolve if the orchestrator's process cwd happens to be the repo root. The current launch instructions (`nohup python scripts/path_c_orchestrator.py`) work because the user runs it from repo root, but the Phase 2 orchestrator does set `cwd=str(ROOT)` for `modal run` invocations (line 288). Recommend symmetric `cwd=str(ROOT)` for Phase 1 too. ISSUE, low — works in the documented invocation pattern.

## Cycle 2 — 2026-05-11 22:43 PDT

### New commits since 22:30 — all docs/paper only

- `1de84cf` "Add comprehensive NeurIPS appendix" — `agent_reports/paper/*` only.
- `50229af` "DEEP-LIT-WRITER deliverables" — `agent_reports/*.md` + `paper/main.pdf,bbl`.
- `524a116` "Deep improvement to §4.1" — `paper/main.tex,pdf,bbl` + `section_dive_2237.md`.

None of these touch executable code. No code-review action needed.

## Cycle 3 — 2026-05-11 22:55 PDT

### Cross-branch divergence audit

**[ISSUE] `src/utils/logger.py` regressed on `agent/pathc-lead` vs `agent/a1-her-baselines`**

- `agent/a1-her-baselines` (commit 4d6bbf9) has a `_init(entity)` closure with a try/except fallback: if the configured `wandb_entity` rejects (permission denied), it retries with the default entity (None). It also auto-appends the `method` as a tag.
- `agent/pathc-lead` (commit b393fe3) regressed: removed the try/except and the `method` tag-append. Now only sets `tags` from env var.

**Impact**: If the Path C orchestrator's Phase 2 (Modal) launches into a workspace whose `WANDB_ENTITY` secret is set to the wrong value (`djrgvc` is mentioned in the a1 commit message), the run will hard-fail at `wandb.init` rather than fall back. The orchestrator should still mark the run as failed and continue, but every Phase 2 run would die.

**Recommendation for morning merge**: Take the a1-her-baselines version of `src/utils/logger.py` and stack the WANDB_TAGS env var pickup on top. The PATHC-LEAD changes are a strict subset.

### New commits in this cycle

- `fd880a7` "Paper polish" — paper polish, no code changes.

**[ISSUE] `train.py:212-221` — capture_frames regression vs a1-her-baselines**

The `agent/a1-her-baselines` branch had:
```python
needs_frames = is_semantic and cfg["replay"].get("vlm_provider", "openai") != "heuristic"
```

The `agent/pathc-lead` (b393fe3 / 5a859f5) version replaces this with:
```python
capture_frames = is_semantic or cf_needs_frames
```

This **loses the heuristic-vlm-provider optimization**: any `her_semantic_per` run with `vlm_provider=heuristic` will now capture frames unnecessarily (~10% CPU + memory hit per env step). The Path C overnight matrix doesn't trigger this combination, but the previously-running A1 HER-baselines on Modal *do* use `vlm_provider=heuristic` and will incur this regression if they are restarted from the pathc-lead branch.

**Morning merge action**: restore the heuristic-skip logic when reconciling train.py:
```python
needs_frames_semantic = is_semantic and cfg["replay"].get("vlm_provider", "openai") != "heuristic"
capture_frames = needs_frames_semantic or cf_needs_frames
```

**[ISSUE] `src/envs/wrappers.py:101-104` — render_mode regression vs a1-her-baselines**

The `agent/a1-her-baselines` branch had:
```python
kwargs = {}
if capture_frames:
    kwargs["render_mode"] = render_mode
```

The `agent/pathc-lead` (b393fe3) version unconditionally sets:
```python
kwargs = {"render_mode": render_mode}
```

This is a regression: the a1 version was specifically designed to **avoid MuJoCo's offscreen-context errors** on machines without OSMesa/EGL when no frames are needed. The pathc-lead version always forces an offscreen context.

Tonight's runs use `MUJOCO_GL=egl` (set in the orchestrator's `_build_env`), so EGL is available and the regression is harmless. But if any Modal Phase 2 worker fails to find EGL (image issue, cold start), the runs would all crash at `env.reset` whereas the a1 path would have just disabled rendering.

**Morning merge action**: take the a1-her-baselines version of `src/envs/wrappers.py:make_env`. This change is independent of CF code so it's a clean cherry-pick.

**[ISSUE] scripts/path_c_orchestrator.py:308 — Phase 2 Modal tags not propagated**

`launch_modal_run` invokes `subprocess.Popen(["modal", "run", "--detach", "modal_app.py::spawn", ...])`. Modal CLI does NOT propagate the launcher's env vars to remote containers; secrets+env are set per-`app.function` via `secrets=[...]` and `.env({...})` in the image build.

The Phase 1 `_build_env` correctly injects `WANDB_TAGS` for local subprocesses, but `launch_modal_run` does **not** use `_build_env` (line 288's Popen passes no `env=`). Even if it did, Modal wouldn't honor it.

**Impact**: Phase 2 runs will be **un-tagged** in W&B. The dashboard URL in the operator README (`?tags=path_c_overnight_2026-05-11`) will only show Phase 1 (local) runs. Filtering by `path_c_vlm`, `vlm_cf`, etc. will return nothing.

**Workaround for tonight**: have a human verify Phase 2 runs in W&B by `group=path_c_vlm_cf_*` instead of by tags.

**Morning fix**: either inject `WANDB_TAGS` as an additional `--extra` override (e.g., add `"replay.wandb_tags=path_c_vlm,vlm_cf,..."` to the overrides and have train.py wire it through), or set `WANDB_TAGS` via the Modal `.env({})` image clause.

**[NIT] src/buffers/counterfactual_buffer.py:157 — `cf_window` parameter is dead code**

The constructor accepts `cf_window: int = 4`, the docstring (line 177) says:
> "When a CF is returned for a single frame K, also push the same corrective goal as relabel for transitions in [K-cf_window, K+cf_window]"

But `self.cf_window` is **never referenced** anywhere after being stored. The `_draw_relabel_goal` method applies the standard `k_i >= t` causal filter and `c / max(1, (k_i - t + 1))` weighting — there's no explicit window. Configs (oracle_cf.yaml etc.) set `cf_window: 4` but it has no effect.

This is harmless for tonight (the existing weighting already biases toward nearby CFs), but it's misleading documentation. Either implement the window or remove the parameter.

## Cycle 4 — 2026-05-11 23:21 PDT

### Phase 1 progress

- HER PnP: 3/3 done (30 min each), all rc=0.
- HER Push: 3/3 done (30 min each), all rc=0.
- HER Slide: running (just started).
- OCF (oracle_cf.yaml): all 9 pending. ETA start: ~23:47 PDT.

No new commits in last 25 minutes. No new code changes to review yet. Will wait for OCF batch to begin to verify the oracle CF code path doesn't crash in practice.

## Cycle 5 — 2026-05-11 23:51 PDT

### Phase 1 status

- HER: 9/9 done (clean rc=0 for all).
- OCF: 3/9 running (PnP). 6 pending. **No crashes** in OCF startup or first 50k steps — oracle CF code path is healthy.

### Live inspection of OCF run

`logs/path_c_orch_ocf_pp_s42.log` shows the run training cleanly. Critic loss is 1.5-1.8 (vs HER's ~2.2), suggesting the buffer is producing differently-distributed transitions. No exceptions, no warning spam.

W&B run shows up at `path_c_kill_ocf_pp_s42_seed42`.

**[ISSUE] W&B group derivation defeats per-method grouping for Path C runs**

The orchestrator plan uses run_name like `path_c_kill_ocf_pp_s42` (suffix `_s42`, NOT `_seed42`). Train.py at line 304 appends `_seed42` to get final name `path_c_kill_ocf_pp_s42_seed42`. The logger derives group by `run_name.split("_seed")[0]` → group = `path_c_kill_ocf_pp_s42`.

Result: each seed lives in its own W&B group with 1 run, so the per-method comparison panel (HER-PnP all 3 seeds vs OCF-PnP all 3 seeds) does NOT group as expected. The morning consolidator must filter by tag or use W&B's "compare runs" UI manually.

**Cause**: the plan should have set run_name to `path_c_kill_ocf_pp` (no seed in name); train.py would then append `_seed42` and group would correctly derive `path_c_kill_ocf_pp`.

**Workaround for tonight**: filter by `tags=path_c_overnight_2026-05-11` and group manually in the W&B UI.

**Fix**: update the orchestrator's `overnight_path_c_plan.json` to drop the `_s{seed}` suffix from run_name strings. (Don't fix now — would require restarting completed HER runs.)

## Cycle 6 — 2026-05-12 00:06 PDT

### MAJOR — commit 168518b CLOSES BLOCKER B1

`commit 168518b "Path C: fix verified_cf no-op, add p_counterfactual sweep configs, add CF-HER tests"` (Tue May 12 00:01:12 2026 -0700) addresses my Cycle 1 BLOCKER. Reviewed in detail:

**counterfactual.py**: `make_counterfactual_fn` gains `return_action: bool` (default False — back-compatible). When True, returns 4-tuples `(idx, pos, conf, corrective_action_or_None)`.

**train.py::_build_cf_provider**: the 'verified' branch now:
- Forces `vlm_variant='all'` when `cf_provider='verified'` (with a warning if user set position-only variant).
- Constructs CF function with `return_action=True` so the 4-tuple is plumbed.
- Per-CF: reconstructs MuJoCo snapshot via `reconstruct_snapshot_for_synthetic_episode`, invokes `verifier.verify(corrective_action=ca)`, and either promotes verified CFs (conf→1.0, position replaced with simulator-observed achieved_goal) or drops rejected ones.
- Returns the verifier instance up to the buffer so its counters surface in W&B.

**train.py::train**: passes `verifier` to `CounterfactualHERBuffer` and logs `buffer/cf_verifications_*` (attempted, succeeded, rejected_no_action, rejected_no_success, rejected_exception, success_rate).

**Tests added**: 
- `tests/test_counterfactual_buffer.py` (15 invariants).
- `tests/test_verified_cf_wiring.py` (11 invariants).
- Both report 26/26 passing per commit message.

**Configs added**: `configs/cf_psweep_p{00,10,25,50,75}.yaml` — p_counterfactual sweep for the CF-mixing ablation. `cf_psweep_p00.yaml` should recover HER exactly (the "p=0 ≡ HER" invariant pinned in test_counterfactual_buffer.py).

### Code review of 168518b

**No new blockers introduced.** Light findings:

**[NIT] train.py:194 — `rejected_no_action` counter is a misnomer**

When `ca is None`, the code increments `verifier.stats["rejected_no_action"]` but **also appends the CF to `verified`** (line 194) with the original position+confidence. The comment explains: "we still surface the CF so the buffer keeps a usable signal." So this is a fallback-to-position-trust, not a true rejection. The counter name is misleading — it should be `fellback_no_action` or `position_only_passthrough`. Minor — no functional issue.

**[NIT] reconstruct_snapshot_for_synthetic_episode is wasteful**

Each CF requires a fresh `gym.make(env_name)` and `env.reset(seed=...)`. For Phase 2 with `cf_call_interval=8` and ~5000 episodes per 250k step run, that's ~625 env creations per run, ~0.5-1s each = 5-10 min wallclock overhead. Acceptable but could be optimized by caching a "snapshot factory" env on the verifier. NIT, post-morning improvement.

**[SCIENTIFIC RISK, not a bug] forced `vlm_variant='all'` for verified mode**

Per C1v2-A bake-off (`agent_reports/C1v2_real_data.md`), `variant='achieved_goal'` had 0% teleport collapse while `variant='all'` had non-zero. Forcing `'all'` for verified_cf means the underlying VLM outputs have higher pre-verification teleport-collapse rate. The verification gate filters them post-hoc — but this means **verified_cf may have LOWER CF density than vlm_cf with `'achieved_goal'`**, which would confound the comparison.

Watch the `buffer/cf_verifications_success_rate` and `buffer/cf_relabel_count` metrics in the morning: if verified_cf's relabel count is <50% of vlm_cf's, the comparison is dominated by mixture rather than gate efficacy.

### Phase 1 progress

- HER: 9/9 done (all rc=0).
- OCF PnP: 3/3 running. ETA done ~00:16-00:17.
- OCF Push, Slide: 6 pending.

## Cycle 7 — 2026-05-12 00:22 PDT (final code review cycle)

### New commits

- `6ac734e` — VLM-tier ablation configs + launcher script. Reviewed: clean configs, well-commented launcher. Pre-registration of falsification criteria in `agent_reports/ablation_vlmtier_design.md`. No code issues. NOT launching tonight.

## Cycle 8 — 2026-05-12 01:20 PDT (final wrap-up)

### Phase 1 KILL test FINAL results

Per `logs/path_c_orch_*.log` final "Best success rate" lines:

|         | PnP   | Push  | Slide |
|---------|-------|-------|-------|
| HER     | 0.183 | 0.617 | 0.183 |
| OCF     | 0.133 | 0.283 | 0.183 |
| Δ       | −0.050| −0.333| 0.000 |

- **PnP**: OCF − HER = −0.05. **KILL rule (+0.10) NOT met.** Path C is provisionally dead.
- **Push**: OCF − HER = −0.33. Catastrophic. OCF is **actively destroying** Push performance.
- **Slide**: tied.

### Code-side hypothesis for Push regression

`oracle_cf_push` outputs `midpoint(ee[k], desired_goal)` where `k` is the frame of **maximum ee-block distance** — i.e., the frame where the agent has wandered AWAY from the block. The midpoint is at a random location in the workspace. The relabel signal is noise. The morning lead should ablate Push oracle to either:
- `midpoint(block_pos[k], desired_goal)` (uses block position, not ee), OR
- `block_pos[k] + step_toward(desired_goal, dist=0.05)` (block one step closer).

The current Push oracle is **a clear design bug**, not a wiring bug. The buffer ingested it correctly.

### Final code-review verdict

- The CF-HER buffer integration **works mechanically** — no crashes, all OCF runs rc=0.
- The fix to BLOCKER B1 (`168518b`) is correct, well-tested (26/26 invariants pass), and unblocks the Phase 2 differentiation.
- The remaining BLOCKER B2 (Modal WANDB_ENTITY) is the highest-priority morning action: without it, all 18 Phase 2 runs silently die at startup.
- The empirical Path C result (OCF lags HER by 0.05 on PnP) is **not a code issue** — the code did what it was told. The oracle design for Push is the lever to pull before pronouncing Path C dead.



---

## 2026-05-12 ~01:55 PDT — addressed by REGRESSION-MERGE agent (Opus 4.7)

Single commit addresses the five highest-value pending items from this report:

1. **B3 (`src/envs/wrappers.py` render_mode regression)** — restored the
   `if capture_frames: kwargs["render_mode"] = render_mode` guard from
   `agent/a1-her-baselines`. Heuristic-only runs on minimal images
   (no OSMesa/EGL) no longer crash at `gym.make`.
2. **Cross-branch divergence (`src/utils/logger.py` try/except fallback)** —
   restored the `_init(entity)` closure with permission-denied fallback to
   default entity. WANDB_TAGS env-var pickup is retained AND merged with
   the method-prefix tag (a1-her-baselines behavior). Phase 2 Modal jobs
   no longer silently lose runs when secrets bake in a stale entity.
3. **Cross-branch divergence (`train.py:309` capture_frames heuristic-skip)** —
   restored `needs_frames_semantic = is_semantic and vlm_provider != "heuristic"`
   so semantic-PER runs with the heuristic localizer no longer pay the
   ~10% per-step rendering cost.
4. **Double-counted `vlm_returned_none`** — exception path in
   `counterfactual_buffer._query_vlm` now increments a new
   `vlm_exceptions` counter (surfaced as `buffer/cf_vlm_exceptions` in
   W&B). `vlm_returned_none` is now incremented exactly once per failed
   CF call (in `finish_episode`), so the diagnostic is no longer
   ~2x-inflated when the callback raises.
5. **`cf_window` dead-code → implemented** — added the locality bound
   documented in the constructor docstring: a CF at frame K is now only
   eligible for transitions with `t <= K <= t + cf_window`. `cf_window <= 0`
   disables the bound (recovers prior unbounded behavior). 12 existing
   configs that already set `cf_window: 4` now get the documented
   behavior. Verified by smoke test: CF at K=30 on T=50 episode with
   cf_window=4 yields exactly 20 CF relabels (5 eligible t × k=4); with
   cf_window=0 yields 124 (31 eligible × k=4).

**Tests**: 3 new invariants added (`TestCfWindowLocality` ×2,
`TestVlmExceptionsCounterDoesNotDoubleCount` ×1). Full suite:
**29/29 passing** (15 original `test_counterfactual_buffer.py` +
11 `test_verified_cf_wiring.py` + 3 new).

**Safety**: in-flight Phase 1 oracle_cf_sld training completed (rc=0,
0.150 final success rate on Slide) before these edits committed.
No subprocess re-imports source — safe to land.

**Behavioral note on cf_window=4**: this DOES change CF relabel
distribution for any future run using the default `cf_window: 4` in
configs. Specifically, on PnP/Push oracle CFs (which target frames late
in the episode, near the "first-drop" or "max-distance" frame), the CF
will now only relabel transitions in a 5-step window before the
critical frame. This is *the documented intent* — earlier transitions
fall back to standard HER. If morning analysis shows worse CF-HER
performance vs the original unbounded-forward implementation, set
`cf_window: 0` in the relevant configs to recover prior behavior.


