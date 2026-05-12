#!/usr/bin/env bash
# run_corrected_push_ocf.sh — Re-run FetchPush Oracle-CF after the
# `oracle_cf_push` midpoint bugfix (commit ccb63d4, 2026-05-12).
#
# CONTEXT
#   The 2026-05-11 Path C KILL run showed OCF underperforming HER on
#   FetchPush by 0.33 success (HER 0.617, OCF 0.283). CODE-REVIEWER traced
#   the cause to a design bug in src/vlm/oracle_cf.py::oracle_cf_push: the
#   CF was midpoint(ee[k], goal) at the max-ee-block-divergence frame,
#   which placed the CF in an arbitrary workspace region whenever the
#   agent had lost the block. The fix (ccb63d4) uses midpoint(block[k],
#   goal) instead, anchoring the CF to a physically meaningful state.
#
#   This script re-runs the 3 OCF-Push seeds (42/123/999) at 250k steps
#   so the morning agent can re-evaluate the KILL verdict with corrected
#   Push numbers.
#
# PROVENANCE
#   W&B tags: path_c_kill_2026-05-11,oracle_cf_pushfix
#   Run names: path_c_kill_ocf_push_fix_s{42,123,999}
#   (Distinct from the original `path_c_kill_ocf_push_s*` runs so the
#    pre-fix and post-fix runs can be plotted side-by-side.)
#
# DEPENDENCIES
#   - Phase 1 ocf_sld batch (in flight at script-writing time) must finish
#     first. This script DOES NOT auto-detect; gate manually before
#     launching.
#
# Set DRY_RUN=1 to print commands without executing.

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

SEEDS=(42 123 999)
TAG_BASE="path_c_kill_2026-05-11,oracle_cf_pushfix"

run_one () {
  local seed="$1"
  local run_name="path_c_kill_ocf_push_fix_s${seed}"
  local logfile="logs/${run_name}/train.log"
  mkdir -p "logs/${run_name}"
  local cmd=(
    python train.py
    --config configs/oracle_cf.yaml
    env.name=FetchPush-v4
    training.seed="${seed}"
    training.total_steps=250000
    training.eval_interval=10000
    training.save_interval=50000
    training.log_interval=1000
    logging.use_wandb=true
    "logging.run_name=${run_name}"
  )
  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    printf 'WANDB_TAGS=%s \\\n  %s\n' "${TAG_BASE}" "${cmd[*]}"
  else
    WANDB_TAGS="${TAG_BASE}" "${cmd[@]}" > "${logfile}" 2>&1
  fi
}

# Sequential (not parallel) to be polite to GPU; each run is ~30 min on
# RTX 5070 Ti at 250k steps. Total ~90 min wallclock.
for seed in "${SEEDS[@]}"; do
  echo "[corrected_push_ocf] launching seed=${seed}"
  run_one "${seed}"
done

echo "corrected_push_ocf done: ${#SEEDS[@]} seeds at 250k steps."
echo "Filter in W&B: tags=path_c_kill_2026-05-11 AND tags=oracle_cf_pushfix"
