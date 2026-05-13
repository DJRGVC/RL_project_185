#!/usr/bin/env bash
# HER@1M on FetchPush + FetchSlide, 3 seeds each, local GPU.
# Run with: nohup bash scripts/run_her_1m_push_slide.sh > ~/.local/state/her_1m_push_slide.log 2>&1 &
# All 6 runs in parallel (each ~1.5-2GB VRAM on 5070 Ti 16GB — fits with PnP s999 still running).
set -uo pipefail
cd ~/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185
source .venv/bin/activate
mkdir -p ~/.local/state
log() { echo "[$(date '+%H:%M:%S')] $*"; }

log "→ launching 6 HER@1M runs (Push + Slide, 3 seeds each)"

for env in FetchPush-v4 FetchSlide-v4; do
    env_slug=$(echo "$env" | awk -F'-' '{print $1}' | sed 's/Fetch//' | tr '[:upper:]' '[:lower:]')
    for seed in 42 123 999; do
        run_name="path_c_her_1m_${env_slug}_s${seed}_seed${seed}"
        log "  → ${run_name}"
        WANDB_TAGS="path_c_her_1m,her_baseline_1m" \
        nohup python train.py \
            --config configs/her.yaml \
            env.name=${env} \
            training.seed=${seed} \
            training.total_steps=1000000 \
            training.eval_interval=10000 \
            training.save_interval=50000 \
            training.log_interval=1000 \
            logging.use_wandb=true \
            logging.run_name=${run_name} \
            > ~/.local/state/her_1m_${env_slug}_s${seed}.log 2>&1 &
        sleep 8  # stagger to avoid VRAM allocation race
    done
done

wait
log "✓ all 6 HER@1M Push+Slide runs done"
