#!/usr/bin/env bash
# run_ablation_vlm_scale.sh — Wave C: VLM model-scale (cost) ablation.
#
# Design doc: agent_reports/ablation_vlm_scale_design.md
# Pre-registered hypothesis: at the production p=0.25 / vlm_cf operating
# point on FetchPickAndPlace, the mean eval success at 500k steps is
# statistically equivalent across the 5-tier cost curve (gpt-4o-mini,
# gpt-4o, haiku-4-5, sonnet-4-5, opus-4-7) within +/- 0.10 SR. Falsified
# if any frontier model beats the cheapest tier by >= 0.10 SR.
#
# Sweep grid: 5 models * 5 seeds * 1 env (PnP) * 500k steps = 25 runs.
# Compute: ~30 min/run on Modal A10G x 25 = ~12.5 GPU-h, ~$120 VLM API.
# Wall: ~6 hr at the established Modal 10-cap concurrency.
#
# IDEMPOTENT: refuses to relaunch if _VLM_SCALE_LAUNCHED.flag exists.
# Queues for AFTER Wave B + matched-horizon 500k baselines finish.
#
# Set DRY_RUN=1 to print the modal command without executing.
# DO NOT RUN until Wave B (her_per, sharony, 2x2) + matched-horizon
# HER@500k + PER@500k completes — Wave C consumes the same Modal A10G
# pool. See agent_reports/overnight_path_c_plan.json::phase_waveC_vlm_scale.

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

FLAG="agent_reports/_VLM_SCALE_LAUNCHED.flag"

if [[ -f "$FLAG" ]]; then
  echo "[run_ablation_vlm_scale] _VLM_SCALE_LAUNCHED.flag exists; refusing to relaunch."
  echo "  rm $FLAG to override."
  exit 0
fi

# Wave-C entrypoint on Modal. Defined in modal_app.py as the local
# entrypoint `run_path_c_vlm_scale_ablation`. It iterates the same
# 5-model * 5-seed grid this script tracks; the script is the canonical
# user-facing launcher.
CMD=(
  modal run --detach
  modal_app.py::run_path_c_vlm_scale_ablation
)

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  printf '[dry-run] %s\n' "${CMD[*]}"
  echo "[dry-run] Would write flag: $FLAG"
  exit 0
fi

echo "[run_ablation_vlm_scale] launching: ${CMD[*]}"
"${CMD[@]}"

# Mark launched so the script is idempotent.
date -u +"launched_at_utc=%Y-%m-%dT%H:%M:%SZ" > "$FLAG"
echo "[run_ablation_vlm_scale] launched and flagged at $FLAG"
echo "Track: https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_vlm_scale_2026-05-13"
