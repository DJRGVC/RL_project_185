# VLM-CF p_counterfactual sweep — PREPPED (auto-launch armed)

Generated 2026-05-12 by the Path-C lead agent. The sweep is queued behind the
running Phase 2 attempt 5 (Modal app `ap-NWsFCh9kA9P0syU9JhIBAR`) and will
fire automatically when Modal capacity frees.

## Question this sweep answers

The current Path C production default is HER+VLM-CF at `p_counterfactual=0.25`
(value inherited from the oracle-CF mix tuned in `configs/cf_psweep_p*.yaml`).
The mix means 1 in 4 HER relabels is replaced by a VLM-imagined corrective
goal; the other 3 are the standard achieved-future hindsight goal.

This sweep asks: **does pure VLM-imagined relabeling (`p=1.0`, no
achieved-future HER) beat the mix?** If the VLM is genuinely producing
high-quality counterfactual goals, the HER backstop is unnecessary; if HER's
hindsight guarantee is still load-bearing, the peak should sit near
`p ∈ {0.25, 0.50}`.

## Configs (6)

All in `configs/`, all *new* — none of the in-flight Phase 2 configs were
touched.

| File | p_counterfactual | Provider | Variant | cf_call_interval |
|---|---|---|---|---|
| `configs/vlm_cf_psweep_p00.yaml`  | 0.00 | anthropic / sonnet-4.5 | achieved_goal | 16 |
| `configs/vlm_cf_psweep_p10.yaml`  | 0.10 | anthropic / sonnet-4.5 | achieved_goal | 16 |
| `configs/vlm_cf_psweep_p25.yaml`  | 0.25 | anthropic / sonnet-4.5 | achieved_goal | 16 |
| `configs/vlm_cf_psweep_p50.yaml`  | 0.50 | anthropic / sonnet-4.5 | achieved_goal | 16 |
| `configs/vlm_cf_psweep_p75.yaml`  | 0.75 | anthropic / sonnet-4.5 | achieved_goal | 16 |
| `configs/vlm_cf_psweep_p100.yaml` | 1.00 | anthropic / sonnet-4.5 | achieved_goal | 16 |

All other fields (`cf_min_confidence=0.5`, `reject_teleport_radius_m=0.05`,
`vlm_keyframes=5`, `cf_window=4`, `cf_fallback_to_achieved=true`) match
`configs/vlm_cf.yaml` exactly so the sweep is ceteris-paribus on `p` only.

## Run grid

- Env: **FetchPickAndPlace-v4** (the env where the Path C VLM-CF mechanism
  has shown the largest delta over plain HER).
- Steps: **500,000** per run (matches Phase 2 attempt 5).
- Seeds: **42, 123, 999**.
- Total: **6 × 3 = 18 runs**.
- W&B run name format: `path_c_vlm_cf_psweep_p{NN}_pp_s{seed}_seed{seed}`
  where NN ∈ {00, 10, 25, 50, 75, 100}.
- W&B tags per run: `path_c_vlm_cf_psweep_2026-05-12`, `vlm_cf_psweep`,
  `p{NN}`, `pathc_lead`, `FetchPickAndPlace-v4`.

## Smoke test (p=1.0, CPU, 200 steps)

`configs/vlm_cf_psweep_p100.yaml` passed the smoke test:

- Config loads with `p_counterfactual=1.0`, `cf_provider=vlm`,
  `vlm_provider=anthropic`, `vlm_model=claude-sonnet-4-5`,
  `cf_call_interval=16`, `cf_min_confidence=0.5`,
  `reject_teleport_radius_m=0.05`, `vlm_variant=achieved_goal`.
- 200 SAC steps complete on CPU with no crashes (cf_call_interval bumped to
  999 to skip API calls during smoke).
- Unit-level buffer probe confirms p=1.0 semantics:
  - With valid CFs returned: 12 CF relabels + 8 fallback achieved-future
    relabels (where the locality/causal filter rejected the CF), no skips.
  - With cf_fn returning None: full fallback to achieved-future
    (20 synthetic relabels), buffer never empty.

## Auto-launch trigger

Watcher script: `scripts/launch_psweep_when_ready.sh`

Trigger: every 5 minutes, the watcher runs `modal app list` and checks
whether ANY ephemeral `semantic-p…` app (including the Phase 2 attempt 5
entrypoint `ap-NWsFCh9kA9P0syU9JhIBAR`) is still in flight. When that
filter yields zero rows, the watcher waits 60 s to settle, fires

```
modal run --detach modal_app.py::run_path_c_vlm_cf_psweep
```

captures the new entrypoint app ID into
`agent_reports/_PSWEEP_LAUNCHED.md`, and exits cleanly. A lock file
(`agent_reports/_PSWEEP_LAUNCHED.lock`) prevents re-fires if the watcher
is restarted by mistake.

### Watcher process

- PID file: `~/.local/state/psweep_launcher.pid`
- Log file: `~/.local/state/psweep_launcher.log`
- Started under `nohup` on 2026-05-12 ~14:23 PDT (survives terminal close).

## Expected ETA

500k SAC steps on Modal A10G ≈ 4–6 hr/run. With the 10-GPU concurrency
cap and 18 runs, the queue plays out in roughly two waves of ~5 hr each
→ **~03:00–07:00 PDT tomorrow** (morning analyst slot).

## Expected spend

- VLM API (Sonnet 4.5, cf_call_interval=16, ~1 call per 16 failed episodes):
  $180–$270 across the 18 runs (the p=0 run burns ~$0 because
  `p_counterfactual=0` short-circuits the VLM call; the p=1.0 run pays
  full price).
- Modal A10G GPU-hours: 18 × ~5 hr × $1.10/hr ≈ $100.
- Combined: roughly **$180–$270 total** (VLM API dominates).

## W&B filter URL

<https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_vlm_cf_psweep_2026-05-12>

## Decision rule for tomorrow

Compute the mean evaluation success rate at 500k steps across 3 seeds for
each p value, then apply:

- **If SR(p=1.0) ≥ SR(p=0.25) + 0.05** → *"pure VLM-CF" wins*. Switch the
  Path C default away from the p=0.25 hybrid; the achieved-future HER
  backstop is no longer carrying the result. Re-run the production
  configs at p=1.0 and update §5 of the paper draft to highlight this.
- **If peak SR lands at p ∈ {0.25, 0.50}** → *HER+VLM hybrid is the right
  default*. Keep the current production setting (the hindsight signal
  and the imagined-goal signal are complementary). This is the
  null-hypothesis outcome the current §5 narrative already supports.
- **If SR declines monotonically with p (p=0.0 > p=0.10 > … > p=1.0)** →
  *HER's hindsight guarantee dominates*. The VLM-imagined goals are
  net-harmful even at low weights. Retract the "VLM-CF helps PnP"
  claim from §5; pivot the paper toward the oracle-CF / verified-CF
  contrast instead.

## Files added by this prep

- `configs/vlm_cf_psweep_p{00,10,25,50,75,100}.yaml` — 6 new sweep configs.
- `modal_app.py` — added `run_path_c_vlm_cf_psweep()` local entrypoint;
  also added an optional `wandb_tags=` arg to `train_remote()`
  (backward-compatible — existing Phase 2 callers don't pass it and
  behave unchanged).
- `scripts/launch_psweep_when_ready.sh` — capacity-aware auto-launcher.
- `agent_reports/_VLM_CF_PSWEEP_PREPPED.md` — this file.
- (After fire) `agent_reports/_PSWEEP_LAUNCHED.md` — launch confirmation
  written by the watcher.

## Constraints honored

- DID NOT modify `configs/vlm_cf.yaml` (in-flight on Phase 2 attempt 5).
- DID NOT touch any in-flight Modal training (Phase 2 attempt 5 and the
  local Oracle-CF 1M PnP s999 run keep running undisturbed).
- DID NOT launch the sweep directly — only armed the watcher to fire when
  Phase 2 finishes.
- Used only existing W&B and Modal infrastructure (same secret, same
  team namespace, same image build).
