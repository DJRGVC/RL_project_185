#!/usr/bin/env bash
# run_ablation_vlmtier.sh — VLM model-tier (cost) ablation for Path C.
#
# Sweeps the VLM model used inside the verified-CF pipeline across four
# cost tiers, holding the production prompt + verification gate fixed.
# Pre-registered hypothesis: simulator-verification dominates over VLM-
# choice; the cheapest tier (gpt-4o-mini, ~$0.005/call) should match the
# premium tier (claude-opus-4-7, ~$0.15/call) within ±0.10 eval success
# at 250k steps. A gap >=0.10 falsifies the cost-effective-deployment
# claim.
#
# Pipeline layout (matches scripts/path_c_orchestrator.py conventions):
#   run_name : path_c_ablation_vlmtier_<env_slug>_<tier>_s<seed>
#   tag      : path_c_ablation_vlmtier_2026-05-12  (+ per-run model tag)
#
# Compute budget (250k steps, RTX 5070 Ti):
#   4 tiers × 1 env (PickAndPlace) × 3 seeds × ~30 min/run = ~6 GPU-hours.
#   VLM dollar cost: ≈ ($0.005 + $0.05 + $0.03 + $0.15) × 3 seeds × ~1.2k
#   failed-eps × 1/8 call-interval ≈ $100 total.
#
# Set DRY_RUN=1 to print the commands without executing them.
# DO NOT RUN tonight — no GPU/Modal capacity is reserved.

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

# Run only on the headline env. Slide and Push can be added in a v2 if
# v0 vs v3 disagrees on PnP. (The reviewer ask is "does cheap suffice?";
# answering on PnP is necessary; sweeping all three envs is sufficient
# but quadruples cost.)
ENVS=("FetchPickAndPlace-v4")
SEEDS=(42 123 999)

# Tier table: (config_suffix, model_label_for_tag)
TIERS=(
  "v0_mini:gpt4omini"
  "v1_gpt4o:gpt4o"
  "v2_sonnet:sonnet45"
  "v3_opus:opus47"
)

TAG_BASE="path_c_ablation_vlmtier_2026-05-12"

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
  for tier in "${TIERS[@]}"; do
    cfg_suffix="${tier%%:*}"
    model_tag="${tier##*:}"
    for seed in "${SEEDS[@]}"; do
      run_name="path_c_ablation_vlmtier_${env_slug}_${model_tag}_s${seed}"
      run_one "ablation_vlmtier_${cfg_suffix}" \
              "$env" "$seed" "$run_name" "${model_tag}"
    done
  done
done

echo "vlmtier ablation submitted: ${#ENVS[@]} env × 4 tiers × ${#SEEDS[@]} seeds = $(( ${#ENVS[@]} * 4 * ${#SEEDS[@]} )) runs"
