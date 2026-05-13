#!/usr/bin/env bash
# HER@1M on FetchPickAndPlace-v4, 3 seeds, local GPU.
# Run with: nohup bash scripts/run_her_1m_pnp.sh > ~/.local/state/her_1m_pnp.log 2>&1 &
set -uo pipefail

cd ~/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185
source .venv/bin/activate

mkdir -p ~/.local/state
log() {
    echo "[$(date '+%H:%M:%S')] $*"
}

# 2 in parallel on the 5070 Ti (each ~5GB VRAM)
# Sequential 3rd to fit in VRAM safely
for seed in 42 123; do
    run_name="path_c_her_1m_pp_s${seed}_seed${seed}"
    log "→ launching ${run_name} in parallel"
    WANDB_TAGS="path_c_her_1m_pnp,her_baseline_1m" \
    nohup python train.py \
        --config configs/her.yaml \
        env.name=FetchPickAndPlace-v4 \
        training.seed=${seed} \
        training.total_steps=1000000 \
        training.eval_interval=10000 \
        training.save_interval=50000 \
        training.log_interval=1000 \
        logging.use_wandb=true \
        logging.run_name=${run_name} \
        > ~/.local/state/her_1m_pp_s${seed}.log 2>&1 &
    sleep 10  # stagger startup
done

# Wait for seeds 42 and 123 to finish
wait
log "✓ seeds 42 and 123 done"

# Now seed 999 sequential
seed=999
run_name="path_c_her_1m_pp_s${seed}_seed${seed}"
log "→ launching ${run_name}"
WANDB_TAGS="path_c_her_1m_pnp,her_baseline_1m" \
python train.py \
    --config configs/her.yaml \
    env.name=FetchPickAndPlace-v4 \
    training.seed=${seed} \
    training.total_steps=1000000 \
    training.eval_interval=10000 \
    training.save_interval=50000 \
    training.log_interval=1000 \
    logging.use_wandb=true \
    logging.run_name=${run_name} \
    >> ~/.local/state/her_1m_pp_s${seed}.log 2>&1
log "✓ seed 999 done"
log "HER 1M PnP relaunch DONE"
