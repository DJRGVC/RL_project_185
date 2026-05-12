# Wave B (B1 → B2 → B3) — PREPPED & WATCHER ARMED

**Prepped at:** 2026-05-12 16:36 PDT
**Watcher PID:** 258223 (`~/.local/state/waveB_launcher.pid`)
**Watcher log:** `~/.local/state/waveB_launcher.log`
**State file:** `~/.local/state/waveB_state.json`
**Lock file (idempotency):** `agent_reports/_WAVE_B_LAUNCHED.lock` (absent on launch; touched once the p-sweep drain clears)

## What this prep does

Three Modal entrypoints have been added to `modal_app.py`, plus a
sequential watcher at `scripts/launch_waveB_when_psweep_done.sh`. The
watcher is **already running in the background** and is currently
blocked on the p_counterfactual sweep (Phase 2 app
`ap-NWsFCh9kA9P0syU9JhIBAR` → then the 18-run p-sweep that auto-fires
when Phase 2 clears).

When the p-sweep fully drains (≈ 01:10 PDT tomorrow), the watcher
fires the three waves **sequentially** (NOT in parallel) and waits for
each to drain before launching the next, so we never exceed the Modal
10-GPU cap.

## Waves

### B1: HER+PER canonical baseline (Andrychowicz + Schaul)
- **9 runs** = 3 envs × 3 seeds × 500k steps
- Config: `configs/her_per.yaml` (pre-existing, smoke-tested)
- Buffer: `_make_per` → `PERBuffer`, wrapped in `HERBuffer` at train.py L364
- Run names: `path_c_her_per_{pp,push,slide}_s{42,123,999}_seed<seed>`
- W&B tag: `path_c_her_per_2026-05-13`
- Why: closes the "missing strongest non-VLM comparator" gap

### B2: Sharony VLM-RB head-to-head
- **9 runs** = 3 envs × 3 seeds × 500k steps
- Config: `configs/vlm_rb.yaml` (commit `ebce938`)
- Run names: `path_c_sharony_vlmrb_{pp,push,slide}_s{42,123,999}_seed<seed>`
- W&B tag: `path_c_sharony_vlmrb_2026-05-13`
- Why: closes R1 W7 "differentiation from Sharony only methodological"

### B3: 2×2 numeric × blind prompt ablation (PnP only)
- **12 runs** = 4 variants × 3 seeds × 500k steps on FetchPickAndPlace-v4
- Configs: `vlm_cf.yaml`, `vlm_cf_blind.yaml`, `vlm_cf_numeric.yaml`, `vlm_cf_blind_numeric.yaml`
- Run names: `path_c_2x2_{variant}_pp_s{42,123,999}_seed<seed>`
  where `variant ∈ {knowsgoal_visual, blind_visual, knowsgoal_numeric, blind_numeric}`
- W&B tag: `path_c_2x2_2026-05-13`
- Why: answers "does numeric trajectory + hidden desired_goal improve VLM CF quality?"

## Run-count totals

| Wave | Runs | Steps/run | Wall-clock (10-GPU cap, ~6 hr/run) | VLM cost | Modal GPU cost |
|------|------|-----------|------------------------------------|----------|----------------|
| B1   | 9    | 500k      | ~6 hr                              | $0       | ~$60–$80       |
| B2   | 9    | 500k      | ~6 hr                              | ~$80     | ~$60–$80       |
| B3   | 12   | 500k      | ~7–8 hr (2 micro-waves)            | ~$50     | ~$80           |
| **Total** | **30** | — | **~18–20 hr**                | **~$130**| **~$200–$240** |

Grand total spend ≈ **$310–$370** (matches the original budget).

## Sequencing & safety

1. Watcher polls `modal app list | grep ephemeral | grep semantic-p` every 5 min.
2. When zero ephemeral semantic-p apps remain → 60s settle → fire B1.
3. **DOES NOT touch** the running p-sweep watcher (PID 236126) or its lock.
4. Touches `_WAVE_B_LAUNCHED.lock` BEFORE firing B1 so a crashed/restarted
   watcher cannot re-fire.
5. After B1 fires, watcher waits for Modal to drain again, then fires B2.
6. After B2 drains, fires B3.
7. After B3 drains, writes `_WAVE_B_LAUNCHED.md` with all three app IDs.

## Smoke-test evidence

```
$ python -c "from train import load_config; cfg = load_config('configs/her_per.yaml', []); ..."
replay.type: her_per
per_alpha: 0.6
her_k: 4
buffer: PERBuffer

$ python -c "import modal_app; print(hasattr(modal_app, 'run_path_c_waveB_her_per'))"
True (and run_path_c_waveB_sharony / run_path_c_waveB_2x2 also True)

$ bash -n scripts/launch_waveB_when_psweep_done.sh
(no output — syntax OK)

$ ps -p 258223
258223  bash scripts/launch_waveB_when_psweep_done.sh   # ARMED
```

## Decision tree for the morning-after agent

After all 30 runs finish, a final agent should consume the W&B results
across the three tags and emit "headline figure v3" + recommendation:

### B1 outcome (HER+PER baseline)
- **If HER+PER SR ≥ our VLM-CF best on Push/Slide**: VLM-CF on flat-goal
  envs is not differentiated from canonical PER. Retract any
  "VLM-CF helps Push/Slide" claim from §5.
- **If HER+PER SR < VLM-CF best on PnP only**: VLM-CF differentiation
  is real and PnP-specific (consistent with the "VLM matters most where
  exploration is hardest" hypothesis).

### B2 outcome (Sharony VLM-RB head-to-head)
- **If VLM-CF beats Sharony on PnP by ≥0.05 SR**: our differentiation
  (forward CF goal-generation vs. Sharony's priority sampling) is real
  and load-bearing. Strengthen the R1 W7 response.
- **If they tie**: keep R1 W7 honest framing — "complementary mechanisms,
  comparable performance".
- **If Sharony wins**: pivot framing — Sharony's frozen VLM scorer is the
  stronger baseline, and our contribution is the forward-CF *capability*
  (interpretable counterfactuals) rather than absolute performance.

### B3 outcome (2x2 prompt ablation)
- **If "blind_numeric" wins**: prompt design matters — withholding
  desired_goal + adding numerical context is the optimal prompt regime.
  Promote this variant to production for §5.6(F).
- **If "knowsgoal_visual" (baseline) wins**: the VLM uses visual context
  best when it can also see the target — the numeric/blind axes don't
  carry additional signal. Keep the production config as-is.
- **Marginal effects (single-axis wins)**: report as design-axis ablation
  in §5.6(F) and pick the dominant axis (blind XOR numeric) for production.

## Files touched

- `modal_app.py` — added `_ENV_SLUGS`, `_waveB_common_overrides`, and
  three `@app.local_entrypoint()` functions
- `scripts/launch_waveB_when_psweep_done.sh` — NEW, sequential watcher
- `agent_reports/_WAVE_B_PREPPED.md` — THIS FILE
- `configs/her_per.yaml` — UNCHANGED (pre-existing, smoke-tested)
- All other configs UNCHANGED (per the "DON'T disturb in-flight" rule)

## Branch

`agent/pathc-lead`. Commit message:
"Modal queue manager for waves B1/B2/B3 (her_per + Sharony + 2x2)"
