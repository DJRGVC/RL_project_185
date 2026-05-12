#!/usr/bin/env bash
# run_ablation_cfwindow.sh — `cf_window` locality-bound ablation for Path C.
#
# Sweeps the CF-relabel locality bound `cf_window` across four cells,
# holding the oracle CF provider, p_counterfactual, and every SAC/HER
# hyperparameter fixed. The bound was promoted from dead code to a real
# constraint in commit 539211c at 02:47 PDT 2026-05-12; 12 production
# configs default to `cf_window: 4` without an empirical justification.
# This ablation answers the reviewer question "why 4?".
#
# Pipeline layout (matches scripts/path_c_orchestrator.py conventions):
#   run_name : path_c_ablation_cfwindow_<env_slug>_<wsuffix>_s<seed>
#   tag      : path_c_ablation_cfwindow_2026-05-12  (+ per-cell window tag)
#
# Compute budget (250 k steps, RTX 5070 Ti):
#   4 cells × 1 env (PickAndPlace) × 3 seeds × ~30 min/run = ~6 GPU-hours.
#   VLM dollar cost: $0  (oracle provider is hand-coded, no API call).
#
# Set DRY_RUN=1 to print the commands without executing them.
# DO NOT RUN tonight — no GPU/Modal capacity is reserved. The orchestrator
# is mid-flight on phase1_kill + phase1_rerun_push.

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

# Run only on the headline env. Push and Slide can be added in a v2 if
# v0 vs v1 disagrees on PnP. (The mechanism is buffer-side and env-
# agnostic; answering on PnP first is necessary; sweeping all three envs
# would quadruple cost for marginal robustness.)
ENVS=("FetchPickAndPlace-v4")
SEEDS=(42 123 999)

# Cell table: (config_suffix : window_tag : window_value_for_doc)
# The window_tag must be a valid W&B tag string (no spaces/equals).
CELLS=(
  "v0:w0:0"
  "v1:w4:4"
  "v2:w10:10"
  "v3:w25:25"
)

TAG_BASE="path_c_ablation_cfwindow_2026-05-12"

run_one () {
  local cfg="$1" env="$2" seed="$3" run_name="$4" extra_tag="$5"
  local logfile="logs/${run_name}/train.log"
  mkdir -p "logs/${run_name}"
  local cmd=(
    python train.py
    --config "configs/${cfg}.yaml"
    env.name="${env}"
    training.seed="${seed}"
    "training.total_steps=250000"
    "training.eval_interval=10000"
    "training.save_interval=50000"
    "training.log_interval=1000"
    "logging.use_wandb=true"
    "logging.run_name=${run_name}"
  )
  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    printf 'WANDB_TAGS=%s,%s,%s \\\n  %s\n' \
      "${TAG_BASE}" "${extra_tag}" "${env}" "${cmd[*]}"
  else
    WANDB_TAGS="${TAG_BASE},${extra_tag},${env}" \
      "${cmd[@]}" > "${logfile}" 2>&1
  fi
}

for env in "${ENVS[@]}"; do
  env_slug=$(echo "$env" | tr '[:upper:]' '[:lower:]' \
    | sed 's/fetch//;s/-v4//;s/pickandplace/pp/;s/push/push/;s/slide/sld/')
  for cell in "${CELLS[@]}"; do
    cfg_suffix="${cell%%:*}"
    rest="${cell#*:}"
    window_tag="${rest%%:*}"
    for seed in "${SEEDS[@]}"; do
      run_name="path_c_ablation_cfwindow_${env_slug}_${window_tag}_s${seed}"
      run_one "ablation_cfwindow_${cfg_suffix}" \
              "$env" "$seed" "$run_name" "${window_tag}"
    done
  done
done

echo "cfwindow ablation submitted: ${#ENVS[@]} env × ${#CELLS[@]} cells × ${#SEEDS[@]} seeds = $(( ${#ENVS[@]} * ${#CELLS[@]} * ${#SEEDS[@]} )) runs"
