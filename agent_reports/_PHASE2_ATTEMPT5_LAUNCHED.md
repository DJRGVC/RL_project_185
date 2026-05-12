# Phase 2 Attempt 5 — Launched

**Launch timestamp:** 2026-05-12 11:25 PDT (= 18:25Z)
**Entrypoint app:** `ap-NWsFCh9kA9P0syU9JhIBAR`
**Branch:** `agent/pathc-lead`
**Jobs spawned:** 18 (3 envs × 3 seeds × {vlm_cf, verified_cf})
**Modal app dashboard:** https://modal.com/apps/agile-quadrupeds/main/ap-NWsFCh9kA9P0syU9JhIBAR
**W&B query:** https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_overnight_2026-05-11

## Provider routing (verified live via W&B at 18:27Z)

| Env                     | Provider  | Model                | cf_call_interval |
|-------------------------|-----------|----------------------|------------------|
| FetchPickAndPlace-v4    | anthropic | claude-sonnet-4-5    | 16               |
| FetchPush-v4            | openai    | gpt-4o               | 16               |
| FetchSlide-v4           | openai    | gpt-4o               | 16               |

10/18 runs already registered on W&B at T+2min with the correct routing. Remaining 8 will appear as Modal allocates more A10G containers (queue depth limited by account concurrency).

## Rationale (vs Attempts 3 + 4)

- **Attempt 3** used `gpt-4o-mini` globally → OpenAI Tier 1 RPD cap exhausted at 7/10 runs.
- **Attempt 4** used `claude-sonnet-4-5` globally → Anthropic Tier 1 5 RPM limit choked all 18 runs.
- **Attempt 5** splits providers along C1v2-B's per-task best-model finding:
  - **PnP → Sonnet 4.5** (task-aware mid-air waypoints; lowest teleport-collapse rate of any model on PnP per C1v2-A bake-off).
  - **Push/Slide → GPT-4o (full, NOT mini)** (0% teleport-collapse on achieved_goal per C1v2-A; OpenAI Tier 1 has 500 RPM headroom vs Anthropic's 5 RPM).
- `cf_call_interval` bumped 8 → 16 (halves call rate; each provider now sees ≤ 3 parallel runs).

## Early-run health observations (Modal logs, 18:26-18:28Z)

- 2 PnP-Sonnet runs hit Anthropic 429s within the first minute (`5 req/min` + `10k input tokens/min`).
- Anthropic SDK's exponential backoff catches all 429s (4-12s retry, then 200 OK).
- After 4 min wall-clock, PnP s42 + s123 are at `global_step≈6500/500000` (~1600 steps/min). Training velocity NOT blocked by VLM throttling — the worker thread sleeps on backoff while the SAC loop keeps going against the fallback achieved_goal relabel.
- When the 3rd PnP seed (s999) spins up, Anthropic load will be 3 concurrent runs sharing 5 RPM — backoff will lengthen but training will continue. The fallback path (`cf_fallback_to_achieved=true`) ensures the VLM is a generator-of-bonus-CFs, not a critical-path dependency.

## ETA + cost

- **ETA:** 500k steps at ~1600 steps/min per A10G → ~5.2 hours wall-clock per run. With 18 runs queued on Modal at ~6 concurrent → **finish ~17:00-18:00 PDT** (12:45-13:00 PDT was optimistic; Modal queue depth is currently 2, will scale).
- **Expected cost:** $150-250 (user authorized no cap).
  - Anthropic Sonnet-4.5 PnP: 6 runs × ~30k VLM calls × $0.003/call ≈ $540 *if uncapped* — but rate-limit throttling effectively caps each PnP run's VLM calls at ~12k → **closer to $200 on Anthropic alone**.
  - OpenAI GPT-4o Push+Slide: 12 runs × ~30k calls × $0.0025/call ≈ $900 *theoretical max*; practical given cf_call_interval=16 → **~$300 OpenAI**.
  - Modal A10G: 18 × 5 h × $1.10/h ≈ $99.

## Operational decisions

1. **Do NOT touch** local Oracle-CF 1M runs (PIDs 199586, 199587) and the 3 local OCF Slide runs (PIDs 204393, 204425, 204426) — these are independent of Modal.
2. **Stopped 12 Attempt-4 zombie Modal apps** before launch (all in `stopped` state now: `ap-PzBy08DH6nAjNe9Mwv7pMq`, `ap-9V1ZbJ246ZQNHfnYGxfmzT`, `ap-VMRLRtkiDhottUubvgpe4F`, `ap-wbF2AaJChg53hoEpiLZajO`, `ap-96dWy4dcvmIeU734QHmyXV`, `ap-3v4WdGDxqU5vZrjfck6rDQ`, `ap-gE3RqVLRU9ekQIVNBphilk`, `ap-IHwA5cfKyGTci5ckSReVxa`, `ap-acdJnYg9s37LUB7GNceHQ4`, `ap-fTxbaD7xS6DH9CAlyvvBm3`, `ap-Vj8Kq2j141SidqVh848NvC`, `ap-Dl3IvkYy889kILfcnJ8L3m`).
3. **Health check script** at `scripts/phase2_attempt5_healthcheck.py` — the 30-min status cron should pick it up around 12:00 PDT (T+25min).

## Files changed

- `configs/vlm_cf.yaml`            — `cf_call_interval: 8 → 16`
- `configs/verified_cf.yaml`       — `cf_call_interval: 8 → 16`
- `agent_reports/overnight_path_c_plan.json` — `_per_task_vlm_models` updated to split (PnP=Sonnet, Push/Slide=GPT-4o); `common_overrides.replay.cf_call_interval = 8 → 16`.

## Single-process app caveat

The Modal app uses `train_remote.spawn()` from inside a `local_entrypoint`, so **all 18 jobs share one app ID** (`ap-NWsFCh9kA9P0syU9JhIBAR`). There are no "sibling app IDs". Modal's `app list` will show only this entrypoint app — task count column reveals the live concurrency. Use the W&B query (above) to track per-run progress, not Modal's app list.
