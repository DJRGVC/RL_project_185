#!/usr/bin/env bash
# run_matched_horizon_500k.sh — Matched-horizon HER@500k + PER@500k baselines.
#
# Purpose:
#   Provide the canonical 500k-step comparators for vlm_cf@500k and
#   verified_cf@500k. Without these, the headline table reduces to
#   "vlm_cf vs HER@250k (1/2 training)" — an unfair comparison.
#
#   3 seeds × 3 envs × 2 methods = 18 runs total on the local GPU.
#
# Layout:
#   Wave 1: 9 HER@500k runs (3 envs × 3 seeds), all in parallel.
#   Wave 2 (after Wave 1 drains): 9 PER@500k runs, all in parallel.
#
#   Per-run VRAM ≈ 310 MB (matches the in-flight HER@1M procs). 9 parallel
#   ≈ 2.8 GB, well within free headroom on a 16 GB 5070 Ti once the
#   HER@1M wave finishes.
#
# Run names + tags:
#   HER:  path_c_her_500k_<env>_s<SEED>_seed<SEED>     tag: path_c_her_500k
#   PER:  path_c_per_500k_<env>_s<SEED>_seed<SEED>     tag: path_c_per_500k
#
# Usage (typically invoked by wait_for_her1m_finish_then_launch_500k.sh):
#   nohup bash scripts/run_matched_horizon_500k.sh \
#     > ~/.local/state/matched_500k_run.log 2>&1 &
set -uo pipefail

PROJECT_ROOT="/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185"
cd "${PROJECT_ROOT}"
source .venv/bin/activate
mkdir -p ~/.local/state

ENVS=(FetchPush-v4 FetchPickAndPlace-v4 FetchSlide-v4)
SEEDS=(42 123 999)

env_slug() {
    # FetchPush-v4 -> push ; FetchPickAndPlace-v4 -> pnp ; FetchSlide-v4 -> slide
    case "$1" in
        FetchPush-v4)          echo "push" ;;
        FetchPickAndPlace-v4)  echo "pnp" ;;
        FetchSlide-v4)         echo "slide" ;;
        *)                     echo "$1" | sed 's/Fetch//;s/-v4//' | tr '[:upper:]' '[:lower:]' ;;
    esac
}

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

launch_wave() {
    local method="$1"   # her | per
    local config="configs/${method}.yaml"
    local tag="path_c_${method}_500k"

    log "==> launching wave: ${method} (${tag}) — 9 runs in parallel"

    local pids=()
    for env in "${ENVS[@]}"; do
        slug=$(env_slug "${env}")
        for seed in "${SEEDS[@]}"; do
            run_name="path_c_${method}_500k_${slug}_s${seed}_seed${seed}"
            run_log="${HOME}/.local/state/matched_500k_${slug}_${method}_s${seed}.log"
            log "  -> ${run_name}  (log: ${run_log})"
            WANDB_TAGS="${tag},path_c_matched_horizon_500k" \
            nohup python train.py \
                --config "${config}" \
                env.name="${env}" \
                training.seed="${seed}" \
                training.total_steps=500000 \
                training.eval_interval=10000 \
                training.save_interval=50000 \
                training.log_interval=1000 \
                logging.use_wandb=true \
                logging.run_name="${run_name}" \
                > "${run_log}" 2>&1 &
            pids+=($!)
            sleep 8  # stagger to avoid VRAM allocation race
        done
    done

    log "    pids: ${pids[*]}"
    log "    waiting for ${method} wave to drain..."
    for pid in "${pids[@]}"; do
        wait "${pid}" || log "    pid ${pid} exited non-zero"
    done
    log "<== wave ${method} done"
}

log "######## MATCHED-HORIZON 500k BASELINES — 18 runs total ########"
launch_wave her
launch_wave per
log "######## ALL 18 MATCHED-HORIZON runs complete ########"
touch "${PROJECT_ROOT}/agent_reports/_MATCHED_500K_DONE.flag"
